"""Database-backed daily upload, spend, and global quota checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from analyser_api.config import Settings
from analyser_api.db.models import Call, Job, Report
from analyser_api.errors import APIError


def _start_of_day() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _retry_after() -> str:
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return str(max(1, int((tomorrow - now).total_seconds())))


async def check_budget(db: AsyncSession, settings: Settings) -> None:
    start = _start_of_day()
    spent = await db.scalar(
        select(func.coalesce(func.sum(Report.est_cost_usd), 0)).where(Report.created_at >= start)
    )
    if float(spent or 0) >= settings.daily_budget_usd:
        raise APIError(
            "budget_exceeded",
            message="The daily analysis budget has been reached.",
            headers={"Retry-After": _retry_after()},
        )


async def check_reanalysis_quota(db: AsyncSession, settings: Settings) -> None:
    start = _start_of_day()
    global_jobs = await db.scalar(select(func.count(Job.id)).where(Job.created_at >= start))
    if (global_jobs or 0) >= settings.daily_calls_global:
        raise APIError(
            "quota_exceeded",
            message="The daily analysis limit for this service has been reached.",
            headers={"Retry-After": _retry_after()},
        )
    await check_budget(db, settings)


async def check_call_quota(db: AsyncSession, workspace_id: UUID, settings: Settings) -> None:
    start = _start_of_day()
    workspace_count = await db.scalar(
        select(func.count(Call.id)).where(
            Call.workspace_id == workspace_id, Call.created_at >= start
        )
    )
    global_count = await db.scalar(select(func.count(Call.id)).where(Call.created_at >= start))
    if (workspace_count or 0) >= settings.daily_calls_per_workspace:
        raise APIError(
            "quota_exceeded",
            message="The daily call limit for this workspace has been reached.",
            headers={"Retry-After": _retry_after()},
        )
    if (global_count or 0) >= settings.daily_calls_global:
        raise APIError(
            "quota_exceeded",
            message="The daily call limit for this service has been reached.",
            headers={"Retry-After": _retry_after()},
        )
    await check_budget(db, settings)
