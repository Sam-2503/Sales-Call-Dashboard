"""Job detail and server-sent progress events."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from analyser_api.config import Settings
from analyser_api.db.models import Call, Job, JobEvent
from analyser_api.deps import Database, Workspace, get_settings
from analyser_api.schemas.api import JobResponse

router = APIRouter(prefix="/api/v1", tags=["jobs"])

TERMINAL_STATUSES = ("succeeded", "failed")


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def format_sse(event_id: int | None, event: str, data: dict[str, Any]) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.extend((f"event: {event}", f"data: {json.dumps(data, separators=(',', ':'))}"))
    return "\n".join(lines) + "\n\n"


async def workspace_job(job_id: UUID, workspace_id: UUID, db: AsyncSession) -> Job:
    job = await db.scalar(
        select(Job)
        .join(Call, Call.id == Job.call_id)
        .where(Job.id == job_id, Call.workspace_id == workspace_id)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Not found")
    return job


async def queue_position(job: Job, db: AsyncSession) -> int | None:
    if job.status != "queued":
        return None
    value = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(
            Job.status == "queued",
            (Job.available_at < job.available_at)
            | ((Job.available_at == job.available_at) & (Job.created_at < job.created_at)),
        )
    )
    return int(value or 0)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, workspace_id: Workspace, db: Database) -> JobResponse:
    job = await workspace_job(job_id, workspace_id, db)
    return JobResponse(
        id=job.id,
        call_id=job.call_id,
        status=job.status,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        percent=job.percent,
        current_stage=job.current_stage,
        error_code=job.error_code,
        error_message=job.error_message,
        queue_position=await queue_position(job, db),
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get("/jobs/{job_id}/events")
async def job_events(
    job_id: UUID,
    request: Request,
    workspace_id: Workspace,
    settings: Annotated[Settings, Depends(get_settings)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    async with request.app.state.session_factory() as session:
        job = await workspace_job(job_id, workspace_id, session)
        call_id = job.call_id
    try:
        cursor = max(0, int(last_event_id or 0))
    except ValueError:
        cursor = 0

    async def stream() -> AsyncIterator[str]:
        nonlocal cursor
        last_keepalive = time.monotonic()
        while True:
            if await request.is_disconnected():
                return
            async with request.app.state.session_factory() as session:
                events = list(
                    await session.scalars(
                        select(JobEvent)
                        .where(JobEvent.job_id == job_id, JobEvent.id > cursor)
                        .order_by(JobEvent.id.asc())
                    )
                )
                current = await session.get(Job, job_id)
            for event in events:
                cursor = event.id
                yield format_sse(
                    event.id,
                    "progress",
                    {
                        "job_id": str(job_id),
                        "stage": event.stage,
                        "status": event.status,
                        "percent": event.percent,
                        "elapsed_s": event.elapsed_s,
                        "ts": iso_z(event.ts),
                    },
                )
            if current is None:
                return
            if current.status in TERMINAL_STATUSES:
                if current.status == "succeeded":
                    yield format_sse(None, "done", {"call_id": str(call_id)})
                else:
                    yield format_sse(
                        None,
                        "error",
                        {
                            "error": {
                                "code": current.error_code or "internal_error",
                                "message": current.error_message or "Analysis failed.",
                            }
                        },
                    )
                return
            if time.monotonic() - last_keepalive >= settings.sse_keepalive_s:
                last_keepalive = time.monotonic()
                yield ": keep-alive\n\n"
            await asyncio.sleep(settings.sse_poll_s)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
