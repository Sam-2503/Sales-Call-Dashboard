"""Workspace creation and self-service endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, func, select

from analyser_api.auth.ratelimit import client_ip
from analyser_api.auth.tokens import issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call
from analyser_api.db.models import Workspace as WorkspaceModel
from analyser_api.deps import Database, Storage, Workspace, get_settings
from analyser_api.errors import APIError
from analyser_api.schemas.api import WorkspaceInfo, WorkspaceResponse
from analyser_api.services.demo import seed_demo_workspace

router = APIRouter(prefix="/api/v1", tags=["workspaces"])


def _limit(request: Request, settings: Settings, kind: str) -> None:
    limiter = (
        request.app.state.workspace_limiter
        if kind == "workspace"
        else request.app.state.demo_limiter
    )
    key = f"{kind}:{client_ip(request, settings.trusted_proxy_count)}"
    if not limiter.allow(key):
        raise APIError(
            "rate_limited",
            message="Too many workspace requests. Try again later.",
            headers={"Retry-After": str(limiter.retry_after(key))},
        )


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    request: Request,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspaceResponse:
    _limit(request, settings, "workspace")
    workspace = WorkspaceModel()
    db.add(workspace)
    await db.flush()
    db.add(Agent(workspace_id=workspace.id, name="Me"))
    await db.commit()
    expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_ttl_days)
    return WorkspaceResponse(
        workspace_id=workspace.id,
        token=issue_token(workspace.id, settings),
        expires_at=expires_at,
    )


@router.post("/workspaces/demo", response_model=WorkspaceResponse, status_code=201)
async def create_demo_workspace(
    request: Request,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspaceResponse:
    del db
    _limit(request, settings, "demo")
    workspace_id, token = await seed_demo_workspace(
        request.app.state.session_factory,
        settings,
        calls=settings.demo_seed_calls,
        label=f"demo-{uuid4()}",
    )
    return WorkspaceResponse(
        workspace_id=workspace_id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_ttl_days),
    )


@router.get("/me", response_model=WorkspaceInfo)
async def get_workspace(
    workspace_id: Workspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspaceInfo:
    workspace = await db.get(WorkspaceModel, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = await db.scalar(
        select(func.count(Call.id)).where(
            Call.workspace_id == workspace_id, Call.created_at >= start_of_day
        )
    )
    today = int(calls_today or 0)
    return WorkspaceInfo(
        workspace_id=workspace.id,
        created_at=workspace.created_at,
        last_activity_at=workspace.last_activity_at,
        calls_today=today,
        quota_remaining=max(0, settings.daily_calls_per_workspace - today),
        is_demo=workspace.is_demo,
        label=workspace.label,
    )


@router.delete("/me", status_code=204)
async def delete_workspace(workspace_id: Workspace, db: Database, storage: Storage) -> Response:
    await storage.delete_prefix(str(workspace_id))
    await db.execute(delete(WorkspaceModel).where(WorkspaceModel.id == workspace_id))
    await db.commit()
    return Response(status_code=204)
