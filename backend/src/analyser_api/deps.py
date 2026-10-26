"""FastAPI dependencies for database sessions and workspace authentication."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, cast
from uuid import UUID

import jwt
from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from analyser_api.auth.tokens import verify_token
from analyser_api.config import Settings
from analyser_api.db.session import session_dependency
from analyser_api.errors import error_response


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in session_dependency(request.app.state.session_factory):
        yield session


async def current_workspace(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise WorkspaceAuthError()
    try:
        return verify_token(authorization[7:], settings)
    except (ValueError, jwt.InvalidTokenError) as error:
        raise WorkspaceAuthError() from error


class WorkspaceAuthError(Exception):
    pass


async def workspace_auth_handler(_: Request, __: Exception) -> JSONResponse:
    return error_response("unauthorized", "A valid workspace token is required.", 401)


Database = Annotated[AsyncSession, Depends(get_db)]
Workspace = Annotated[UUID, Depends(current_workspace)]
