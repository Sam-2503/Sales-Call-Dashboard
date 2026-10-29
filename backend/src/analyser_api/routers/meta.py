"""Public rubric, playbook metadata, and deployment limits."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from call_analyser.schemas.rubric import Rubric
from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from analyser_api.config import Settings
from analyser_api.db.models import Call
from analyser_api.deps import Database, OptionalWorkspace, get_rubric, get_settings

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/rubric", response_model=Rubric)
async def active_rubric(rubric: Annotated[Rubric, Depends(get_rubric)]) -> Rubric:
    return rubric


def _manifest(settings: Settings) -> dict[str, Any] | None:
    path: Path = settings.package.chroma_path / settings.package.embedding_manifest_name
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


@router.get("/playbook")
async def playbook_metadata(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    if settings.package.playbook_grounding != "on":
        return {"available": False, "reason": "grounding is disabled"}
    manifest = _manifest(settings)
    if manifest is None:
        return {"available": False, "reason": "playbook index is not available"}
    return {
        "available": True,
        "title": manifest.get("book_title") or manifest.get("title"),
        "author": manifest.get("author"),
        "edition": manifest.get("edition"),
        "chunk_count": manifest.get("chunk_count") or len(manifest.get("chunks", []) or []),
    }


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
        "grounding": settings.package.playbook_grounding == "on",
        "demo_available": settings.demo_seed_calls > 0,
        "pipeline_version": settings.package.pipeline_version,
        "rubric": {"id": rubric.id, "version": rubric.version},
        "models": {
            "analysis": settings.package.analysis_model,
            "fast": settings.package.fast_model,
            "transcribe": settings.package.transcribe_model,
            "embedding": settings.package.embedding_model,
        },
        "quota_remaining": quota_remaining,
    }
