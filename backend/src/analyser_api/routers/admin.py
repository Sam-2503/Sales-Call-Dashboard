"""Operator-only metrics and feedback export."""

from __future__ import annotations

import hmac
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, text

from analyser_api.config import Settings
from analyser_api.db.models import Call, Feedback, Report, ReportFinding
from analyser_api.deps import Database, get_settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    if not settings.admin_token or not token:
        raise HTTPException(status_code=404, detail="Not found")
    if not hmac.compare_digest(token, settings.admin_token):
        raise HTTPException(status_code=404, detail="Not found")


Admin = Annotated[None, Depends(require_admin)]


@router.get("/stats")
async def admin_stats(_: Admin, db: Database) -> dict[str, Any]:
    counts = {
        status: int(count)
        for status, count in (
            await db.execute(select(Call.status, func.count(Call.id)).group_by(Call.status))
        ).all()
    }
    durations = await db.execute(
        text(
            """
            SELECT percentile_cont(0.5) WITHIN GROUP (
                       ORDER BY EXTRACT(EPOCH FROM (finished_at - started_at))
                   ) AS median_s,
                   percentile_cont(0.95) WITHIN GROUP (
                       ORDER BY EXTRACT(EPOCH FROM (finished_at - started_at))
                   ) AS p95_s
              FROM jobs
             WHERE status = 'succeeded'
               AND started_at IS NOT NULL
               AND finished_at IS NOT NULL
            """
        )
    )
    row = durations.first()
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    avg_cost = await db.scalar(select(func.avg(Report.est_cost_usd)))
    today_spend = await db.scalar(
        select(func.coalesce(func.sum(Report.est_cost_usd), 0)).where(Report.created_at >= start)
    )
    return {
        "calls": counts,
        "job_duration_s": {
            "median": float(row.median_s) if row and row.median_s is not None else None,
            "p95": float(row.p95_s) if row and row.p95_s is not None else None,
        },
        "average_cost_per_report_usd": float(avg_cost) if avg_cost is not None else None,
        "today_spend_usd": float(today_spend or 0),
    }


@router.get("/feedback.jsonl")
async def feedback_jsonl(
    _: Admin,
    request: Request,
) -> StreamingResponse:
    async def rows() -> AsyncIterator[str]:
        async with request.app.state.session_factory() as session:
            result = await session.execute(
                select(Feedback, Report, ReportFinding)
                .join(Call, Call.id == Feedback.call_id)
                .join(Report, Report.call_id == Feedback.call_id)
                .outerjoin(
                    ReportFinding,
                    (ReportFinding.call_id == Feedback.call_id)
                    & (ReportFinding.finding_id == Feedback.finding_id),
                )
                .where(Call.is_demo.is_(False))
                .order_by(Feedback.created_at.asc())
            )
            for feedback, report, finding in result:
                body: dict[str, Any] = {
                    "feedback_id": str(feedback.id),
                    "call_id": str(feedback.call_id),
                    "finding_id": feedback.finding_id,
                    "kind": feedback.kind,
                    "verdict": feedback.verdict,
                    "comment": feedback.comment,
                    "finding_present": finding is not None,
                    "rubric_version": report.report.get("meta", {}).get("rubric_version"),
                    "models": report.report.get("meta", {}).get("models", {}),
                    "prompt_ids": report.report.get("meta", {}).get("prompt_ids", {}),
                    "created_at": feedback.created_at.isoformat(),
                }
                yield json.dumps(body, separators=(",", ":")) + "\n"

    return StreamingResponse(rows(), media_type="application/x-ndjson")
