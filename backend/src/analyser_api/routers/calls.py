"""Streaming call upload and workspace-scoped call endpoints."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import mimetypes
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse, Response
from sqlalchemy import and_, or_, select

from analyser_api.auth.ratelimit import client_ip
from analyser_api.auth.tokens import issue_media_token, verify_media_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call, Job, JobEvent, Report
from analyser_api.deps import Database, Storage, Workspace, get_settings
from analyser_api.errors import APIError
from analyser_api.schemas.api import (
    AudioUrlResponse,
    CallListResponse,
    CallResponse,
    CallSummary,
    CallUploadResponse,
    JobActionResponse,
    JobEventResponse,
    JobResponse,
    ReanalyseRequest,
    ReportResponse,
)
from analyser_api.services.quotas import check_call_quota, check_reanalysis_quota
from call_analyser.errors import RubricError
from call_analyser.schemas.report import CallReport
from call_analyser.stages.follow_up import deterministic_next_steps

router = APIRouter(prefix="/api/v1", tags=["calls"])
MEDIA_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "webm": "audio/webm",
}


async def probe_audio(path: Path, timeout_s: float) -> tuple[float, str]:
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name",
            "-of",
            "json",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise APIError(
            "service_unavailable",
            message="Audio support is not installed. Install ffmpeg, then restart the backend.",
        ) from error
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout_s)
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise HTTPException(status_code=422, detail="invalid_audio") from error
    if process.returncode != 0:
        raise HTTPException(status_code=422, detail="invalid_audio")
    try:
        data = json.loads(stdout)
        format_data = data["format"]
        duration = float(format_data["duration"])
        format_name = str(format_data["format_name"]).split(",")[0]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=422, detail="invalid_audio") from error
    return duration, format_name


async def stream_upload(file: UploadFile, limit: int) -> tuple[Path, str, int]:
    digest = hashlib.sha256()
    size = 0
    with tempfile.NamedTemporaryFile(prefix="call-", suffix=".upload", delete=False) as temporary:
        path = Path(temporary.name)
        try:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail="file_too_large")
                digest.update(chunk)
                temporary.write(chunk)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    return path, digest.hexdigest(), size


@router.post("/calls", response_model=CallUploadResponse, status_code=202)
async def upload_call(
    request: Request,
    db: Database,
    workspace_id: Workspace,
    storage: Storage,
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(...)],
    consent: Annotated[bool, Form(...)],
    rubric_file: Annotated[UploadFile | None, File()] = None,
    title: Annotated[str | None, Form()] = None,
    agent_id: Annotated[UUID | None, Form()] = None,
) -> CallUploadResponse:
    if not consent:
        raise HTTPException(status_code=400, detail="consent_required")
    limiter = request.app.state.upload_limiter
    ip = client_ip(request, settings.trusted_proxy_count)
    if not limiter.allow(ip):
        raise APIError(
            "rate_limited",
            message="Too many uploads. Try again later.",
            headers={"Retry-After": str(limiter.retry_after(ip))},
        )
    await check_call_quota(db, workspace_id, settings)
    if agent_id is not None:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
        )
        if agent is None:
            raise HTTPException(status_code=404, detail="Not found")
    path, digest, size = await stream_upload(file, settings.max_upload_mb * 1024 * 1024)
    key: str | None = None
    try:
        duration, format_name = await probe_audio(path, settings.request_timeout_s)
        rubric_yaml: str | None = None
        if rubric_file is not None:
            rubric_bytes = await rubric_file.read(1_048_577)
            if len(rubric_bytes) > 1_048_576:
                raise HTTPException(status_code=413, detail="rubric_file_too_large")
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", suffix=".yaml", delete=False
                ) as rubric_temp:
                    rubric_temp.write(rubric_bytes)
                    rubric_path = Path(rubric_temp.name)
                from call_analyser.rubric import load_rubric

                load_rubric(rubric_path)
                rubric_yaml = rubric_bytes.decode("utf-8")
            except (UnicodeDecodeError, ValueError, RubricError) as error:
                raise HTTPException(status_code=422, detail="invalid_rubric") from error
            finally:
                if "rubric_path" in locals():
                    rubric_path.unlink(missing_ok=True)
        package_settings = settings.package
        if duration > package_settings.max_audio_minutes * 60:
            raise HTTPException(status_code=422, detail="audio_too_long")
        if duration < package_settings.min_duration_s:
            raise HTTPException(status_code=422, detail="audio_too_short")
        extension = next((ext for ext, mime in MEDIA_TYPES.items() if ext in format_name), "bin")
        call_id = uuid4()
        key = f"{workspace_id}/{call_id}/original.{extension}"
        await storage.put(key, path)
        call = Call(
            id=call_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            title=title,
            status="queued",
            audio_key=key,
            audio_mime=MEDIA_TYPES.get(extension, mimetypes.types_map.get(f".{extension}")),
            audio_sha256=digest,
            audio_bytes=size,
            duration_s=duration,
            original_filename=Path(file.filename or "recording").name[:255],
            consent_at=datetime.now(UTC),
        )
        db.add(call)
        job = Job(
            call_id=call_id,
            status="queued",
            max_attempts=settings.job_max_attempts,
            options={"rubric_yaml": rubric_yaml} if rubric_yaml is not None else {},
            available_at=datetime.now(UTC),
        )
        db.add(job)
        await db.commit()
        return CallUploadResponse(call_id=call_id, job_id=job.id, status="queued")
    except BaseException:
        await db.rollback()
        if key:
            await storage.delete(key)
        raise
    finally:
        path.unlink(missing_ok=True)


def _encode_cursor(created_at: datetime, call_id: UUID) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{call_id}".encode()).decode()


def _decode_cursor(value: str | None) -> tuple[datetime, UUID] | None:
    if not value:
        return None
    try:
        raw = base64.urlsafe_b64decode(value.encode()).decode()
        timestamp, _, call_id = raw.partition("|")
        return datetime.fromisoformat(timestamp), UUID(call_id)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=422, detail="validation_error") from None


@router.get("/calls", response_model=CallListResponse)
async def list_calls(
    workspace_id: Workspace,
    db: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    agent_id: UUID | None = None,
    status: str | None = None,
) -> CallListResponse:
    latest_job = (
        select(Job.id)
        .where(Job.call_id == Call.id)
        .order_by(Job.created_at.desc())
        .limit(1)
        .correlate(Call)
        .scalar_subquery()
    )
    query = (
        select(Call, Report, Job, Agent)
        .outerjoin(Report, Report.call_id == Call.id)
        .outerjoin(Job, Job.id == latest_job)
        .outerjoin(Agent, Agent.id == Call.agent_id)
        .where(Call.workspace_id == workspace_id)
    )
    if agent_id is not None:
        query = query.where(Call.agent_id == agent_id)
    if status is not None:
        query = query.where(Call.status == status)
    decoded = _decode_cursor(cursor)
    if decoded is not None:
        created_at, call_id = decoded
        query = query.where(
            or_(
                Call.created_at < created_at,
                and_(Call.created_at == created_at, Call.id < call_id),
            )
        )
    rows = list(
        await db.execute(query.order_by(Call.created_at.desc(), Call.id.desc()).limit(limit + 1))
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        CallSummary(
            id=call.id,
            title=call.title,
            status=call.status,
            created_at=call.created_at,
            duration_s=call.duration_s,
            overall_score=report.overall_score if report else None,
            outcome=report.outcome if report else None,
            report_status=report.report_status if report else None,
            percent=job.percent if job else None,
            has_audio=bool(call.audio_key),
            is_demo=call.is_demo,
            agent_id=call.agent_id,
            agent_name=agent.name if agent else None,
        )
        for call, report, job, agent in rows
    ]
    next_cursor = _encode_cursor(items[-1].created_at, items[-1].id) if has_more and items else None
    return CallListResponse(items=items, next_cursor=next_cursor)


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: UUID, workspace_id: Workspace, db: Database) -> CallResponse:
    row = (
        await db.execute(
            select(Call, Report, Job, Agent)
            .outerjoin(Report, Report.call_id == Call.id)
            .outerjoin(
                Job,
                Job.id
                == (
                    select(Job.id)
                    .where(Job.call_id == Call.id)
                    .order_by(Job.created_at.desc())
                    .limit(1)
                    .correlate(Call)
                    .scalar_subquery()
                ),
            )
            .outerjoin(Agent, Agent.id == Call.agent_id)
            .where(Call.id == call_id, Call.workspace_id == workspace_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    call, report, job, agent = row
    return CallResponse(
        id=call.id,
        title=call.title,
        status=call.status,
        created_at=call.created_at,
        duration_s=call.duration_s,
        overall_score=report.overall_score if report else None,
        outcome=report.outcome if report else None,
        report_status=report.report_status if report else None,
        percent=job.percent if job else None,
        has_audio=bool(call.audio_key),
        is_demo=call.is_demo,
        agent_id=call.agent_id,
        agent_name=agent.name if agent else None,
        original_filename=call.original_filename,
        consent_at=call.consent_at,
        audio_mime=call.audio_mime,
        audio_bytes=call.audio_bytes,
        reanalysis_count=call.reanalysis_count,
        completed_at=call.completed_at,
        job=JobResponse(
            id=job.id,
            call_id=job.call_id,
            status=job.status,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            percent=job.percent,
            current_stage=job.current_stage,
            error_code=job.error_code,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
        if job
        else None,
    )


async def _latest_job(call_id: UUID, workspace_id: UUID, db: Database) -> Job:
    job = await db.scalar(
        select(Job)
        .join(Call, Call.id == Job.call_id)
        .where(Job.call_id == call_id, Call.workspace_id == workspace_id)
        .order_by(Job.created_at.desc())
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Not found")
    return job


async def _queue_reanalysis(
    call_id: UUID,
    workspace_id: UUID,
    db: Database,
    settings: Settings,
    body: ReanalyseRequest,
) -> JobActionResponse:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    active_job = await db.scalar(
        select(Job).where(
            Job.call_id == call_id,
            Job.status.in_(("queued", "running")),
        )
    )
    if active_job is not None:
        raise HTTPException(status_code=409, detail="conflict")
    if call.status not in ("completed", "failed"):
        raise HTTPException(status_code=409, detail="conflict")
    if call.reanalysis_count >= settings.max_reanalyses_per_call:
        raise HTTPException(status_code=409, detail="conflict")
    await check_reanalysis_quota(db, settings)
    call.status = "queued"
    call.completed_at = None
    call.reanalysis_count += 1
    job = Job(
        call_id=call_id,
        status="queued",
        max_attempts=settings.job_max_attempts,
        options=body.model_dump(exclude_none=True),
        available_at=datetime.now(UTC),
    )
    db.add(job)
    await db.commit()
    return JobActionResponse(call_id=call_id, job_id=job.id, status="queued")


@router.post("/calls/{call_id}/reanalyse", response_model=JobActionResponse, status_code=202)
async def reanalyse_call(
    call_id: UUID,
    workspace_id: Workspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
    body: ReanalyseRequest | None = None,
) -> JobActionResponse:
    return await _queue_reanalysis(call_id, workspace_id, db, settings, body or ReanalyseRequest())


@router.post("/calls/{call_id}/reanalyze", response_model=JobActionResponse, status_code=202)
async def reanalyze_call(
    call_id: UUID,
    workspace_id: Workspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobActionResponse:
    return await _queue_reanalysis(call_id, workspace_id, db, settings, ReanalyseRequest())


@router.post("/calls/{call_id}/job/retry", response_model=JobActionResponse, status_code=202)
async def retry_call_job(call_id: UUID, workspace_id: Workspace, db: Database) -> JobActionResponse:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    job = await _latest_job(call_id, workspace_id, db)
    if job.status in ("queued", "running"):
        raise HTTPException(status_code=409, detail="analysis_in_progress")
    if job.status not in ("failed", "canceled"):
        raise HTTPException(status_code=409, detail="analysis_not_retryable")
    job.status = "queued"
    job.attempts = 0
    job.percent = 0
    job.current_stage = "queued"
    job.error_code = None
    job.error_message = None
    job.started_at = None
    job.finished_at = None
    job.available_at = datetime.now(UTC)
    call.status = "queued"
    call.completed_at = None
    await db.commit()
    return JobActionResponse(call_id=call_id, job_id=job.id, status="queued")


@router.post("/calls/{call_id}/job/cancel", response_model=JobActionResponse)
async def cancel_call_job(
    call_id: UUID, workspace_id: Workspace, db: Database
) -> JobActionResponse:
    job = await _latest_job(call_id, workspace_id, db)
    if job.status == "running":
        raise HTTPException(status_code=409, detail="analysis_already_running")
    if job.status != "queued":
        raise HTTPException(status_code=409, detail="analysis_not_active")
    now = datetime.now(UTC)
    job.status = "canceled"
    job.finished_at = now
    job.locked_by = None
    job.locked_at = None
    job.heartbeat_at = now
    job.current_stage = "canceled"
    job.error_code = "canceled"
    job.error_message = "analysis canceled by user"
    call = await db.get(Call, job.call_id)
    if call is not None:
        call.status = "canceled"
    db.add(
        JobEvent(
            job_id=job.id,
            stage="analysis",
            status="canceled",
            percent=job.percent,
            detail={"reason": "user_requested"},
        )
    )
    await db.commit()
    return JobActionResponse(call_id=call_id, job_id=job.id, status="canceled")


@router.get("/calls/{call_id}/job", response_model=JobResponse)
async def get_call_job(call_id: UUID, workspace_id: Workspace, db: Database) -> JobResponse:
    job = await _latest_job(call_id, workspace_id, db)
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
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get("/calls/{call_id}/job/events", response_model=list[JobEventResponse])
async def get_call_job_events(
    call_id: UUID, workspace_id: Workspace, db: Database
) -> list[JobEventResponse]:
    job = await _latest_job(call_id, workspace_id, db)
    events = await db.scalars(
        select(JobEvent).where(JobEvent.job_id == job.id).order_by(JobEvent.id.asc())
    )
    return [
        JobEventResponse(
            id=event.id,
            stage=event.stage,
            status=event.status,
            percent=event.percent,
            elapsed_s=event.elapsed_s,
            detail=event.detail,
            ts=event.ts,
        )
        for event in events
    ]


@router.get("/calls/{call_id}/report", response_model=ReportResponse)
async def get_call_report(call_id: UUID, workspace_id: Workspace, db: Database) -> JSONResponse:
    report = await db.scalar(
        select(Report)
        .join(Call, Call.id == Report.call_id)
        .where(Report.call_id == call_id, Call.workspace_id == workspace_id)
    )
    if report is None:
        raise HTTPException(status_code=409, detail="not_ready")
    payload = dict(report.report)
    parsed = CallReport.model_validate(payload)
    if parsed.status == "ok" and (
        parsed.next_steps is None or not parsed.next_steps.follow_up_message
    ):
        parsed.next_steps = deterministic_next_steps(parsed.customer_signals, parsed.missed_moments)
        payload = parsed.model_dump(mode="json")
        report.report = payload
        await db.commit()
    payload.pop("debug", None)
    return JSONResponse(
        payload,
        headers={"Cache-Control": "no-store"},
    )


@router.delete("/calls/{call_id}", status_code=204)
async def delete_call(
    call_id: UUID, workspace_id: Workspace, db: Database, storage: Storage
) -> None:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    if call.audio_key:
        await storage.delete(call.audio_key)
    await db.delete(call)
    await db.commit()


@router.get("/calls/{call_id}/audio-url", response_model=AudioUrlResponse)
async def audio_url(
    call_id: UUID,
    workspace_id: Workspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AudioUrlResponse:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None or not call.audio_key:
        raise HTTPException(status_code=404, detail="Not found")
    token = issue_media_token(workspace_id, call_id, settings)
    return AudioUrlResponse(url=f"/api/v1/media/audio?t={token}&call_id={call_id}")


@router.get("/media/audio")
async def media_audio(
    db: Database,
    storage: Storage,
    settings: Annotated[Settings, Depends(get_settings)],
    token: Annotated[str, Query(alias="t")],
    call_id: Annotated[UUID, Query(...)],
    range_header: Annotated[str | None, Header(alias="Range")] = None,
) -> Response:
    try:
        workspace_id = verify_media_token(token, call_id, settings)
    except Exception as error:
        raise HTTPException(status_code=401, detail="unauthorized") from error
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None or not call.audio_key:
        raise HTTPException(status_code=404, detail="Not found")
    total = await storage.size(call.audio_key)
    start, end = 0, total - 1
    if range_header:
        if not range_header.startswith("bytes="):
            raise HTTPException(status_code=416, detail="invalid_range")
        value = range_header[6:].split(",", 1)[0]
        left, _, right = value.partition("-")
        try:
            if left:
                start = int(left)
                end = int(right) if right else total - 1
            else:
                suffix = int(right)
                start = max(0, total - suffix)
            if start < 0 or end >= total or start > end:
                raise ValueError
        except ValueError as error:
            raise HTTPException(status_code=416, detail="invalid_range") from error
    body = await storage.open_range(call.audio_key, start, end)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(body)),
        "Cache-Control": "private, no-store",
    }
    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return Response(
        content=body,
        status_code=206 if range_header else 200,
        media_type=call.audio_mime or "application/octet-stream",
        headers=headers,
    )
