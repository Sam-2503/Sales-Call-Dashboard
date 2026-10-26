"""Workspace creation and self-service endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select

from analyser_api.auth.tokens import issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call
from analyser_api.db.models import Workspace as WorkspaceModel
from analyser_api.deps import Database, Workspace, get_settings
from analyser_api.schemas.api import WorkspaceInfo, WorkspaceResponse

router = APIRouter(prefix="/api/v1", tags=["workspaces"])


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    db: Database, settings: Annotated[Settings, Depends(get_settings)]
) -> WorkspaceResponse:
    workspace = WorkspaceModel()
    db.add(workspace)
    await db.flush()
    db.add(Agent(workspace_id=workspace.id, name="Me"))
    await db.commit()
    expires_at = datetime.now(UTC) + timedelta(seconds=30 * 24 * 3600)
    return WorkspaceResponse(
        workspace_id=workspace.id,
        token=issue_token(workspace.id, settings),
        expires_at=expires_at,
    )


@router.get("/me", response_model=WorkspaceInfo)
async def get_workspace(workspace_id: Workspace, db: Database) -> WorkspaceInfo:
    workspace = await db.get(WorkspaceModel, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = await db.scalar(
        select(func.count(Call.id)).where(
            Call.workspace_id == workspace_id, Call.created_at >= start_of_day
        )
    )
    return WorkspaceInfo(
        workspace_id=workspace.id,
        created_at=workspace.created_at,
        last_activity_at=workspace.last_activity_at,
        calls_today=int(calls_today or 0),
    )


@router.delete("/me", status_code=204)
async def delete_workspace(workspace_id: Workspace, db: Database) -> Response:
    await db.execute(delete(WorkspaceModel).where(WorkspaceModel.id == workspace_id))
    await db.commit()
    return Response(status_code=204)
