"""Public rubric and deployment limits."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from analyser_api.config import Settings
from analyser_api.db.models import Call
from analyser_api.deps import Database, OptionalWorkspace, get_rubric, get_settings
from call_analyser.schemas.rubric import Rubric

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/rubric", response_model=Rubric)
async def active_rubric(rubric: Annotated[Rubric, Depends(get_rubric)]) -> Rubric:
    return rubric


@router.get("/meta")
async def public_meta(
    workspace_id: OptionalWorkspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
    rubric: Annotated[Rubric, Depends(get_rubric)],
) -> dict[str, Any]:
    quota_remaining: int | None = None
    if workspace_id is not None:
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        used = await db.scalar(
            select(func.count(Call.id)).where(
                Call.workspace_id == workspace_id, Call.created_at >= start
            )
        )
        quota_remaining = max(0, settings.daily_calls_per_workspace - int(used or 0))
    return {
        "max_minutes": settings.package.max_audio_minutes,
        "max_upload_mb": settings.max_upload_mb,
        "allowed_audio_extensions": settings.allowed_audio_extensions,
        "retention_days": settings.retention_days,
        "max_reanalyses_per_call": settings.max_reanalyses_per_call,
        "demo_available": settings.demo_seed_calls > 0,
        "pipeline_version": settings.package.pipeline_version,
        "rubric": {"id": rubric.id, "version": rubric.version},
        "models": {
            "analysis": settings.package.analysis_model,
            "fast": settings.package.fast_model,
            "transcribe": settings.package.transcribe_model,
        },
        "quota_remaining": quota_remaining,
    }
