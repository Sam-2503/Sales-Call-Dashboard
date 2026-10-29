"""FastAPI dependencies for database sessions and workspace authentication."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast
from uuid import UUID

import jwt
from call_analyser.schemas.rubric import Rubric
from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from analyser_api.auth.tokens import verify_token
from analyser_api.config import Settings
from analyser_api.db.models import Workspace as WorkspaceModel
from analyser_api.db.session import session_dependency
from analyser_api.errors import error_response, request_id_for
from analyser_api.logging import set_workspace_id
from analyser_api.storage.base import AudioStorage


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_storage(request: Request) -> AudioStorage:
    return cast(AudioStorage, request.app.state.storage)


def get_rubric(request: Request) -> Rubric:
    return cast(Rubric, request.app.state.rubric)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in session_dependency(request.app.state.session_factory):
        yield session


async def current_workspace(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise WorkspaceAuthError()
    try:
        workspace_id = verify_token(authorization[7:], settings)
    except (ValueError, jwt.InvalidTokenError) as error:
        raise WorkspaceAuthError() from error
    workspace = await db.get(WorkspaceModel, workspace_id)
    if workspace is None:
        raise WorkspaceAuthError()
    now = datetime.now(UTC)
    if now - workspace.last_activity_at >= timedelta(minutes=5):
        workspace.last_activity_at = now
        await db.commit()
    set_workspace_id(str(workspace_id))
    return workspace_id


class WorkspaceAuthError(Exception):
    pass


async def optional_workspace(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> UUID | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return verify_token(authorization[7:], settings)
    except (ValueError, jwt.InvalidTokenError):
        return None


async def workspace_auth_handler(request: Request, _: Exception) -> JSONResponse:
    return error_response(
        "unauthorized",
        "A valid workspace token is required.",
        401,
        request_id_for(request),
        headers={"WWW-Authenticate": "Bearer"},
    )


Database = Annotated[AsyncSession, Depends(get_db)]
Workspace = Annotated[UUID, Depends(current_workspace)]
OptionalWorkspace = Annotated[UUID | None, Depends(optional_workspace)]
Storage = Annotated[AudioStorage, Depends(get_storage)]
