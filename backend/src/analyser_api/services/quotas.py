"""Database-backed daily upload quotas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from analyser_api.config import Settings
from analyser_api.db.models import Call


async def check_call_quota(db: AsyncSession, workspace_id: UUID, settings: Settings) -> None:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    workspace_count = await db.scalar(
        select(func.count(Call.id)).where(
            Call.workspace_id == workspace_id, Call.created_at >= start
        )
    )
    global_count = await db.scalar(select(func.count(Call.id)).where(Call.created_at >= start))
    if (workspace_count or 0) >= settings.daily_calls_per_workspace or (
        global_count or 0
    ) >= settings.daily_calls_global:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily call upload limit reached.",
            headers={"Retry-After": "3600"},
        )
