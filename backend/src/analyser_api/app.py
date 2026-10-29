"""Application factory and Stage 0 HTTP foundation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from analyser_api.config import Settings
from analyser_api.db.engine import create_engine
from analyser_api.deps import WorkspaceAuthError, workspace_auth_handler
from analyser_api.errors import (
    APIError,
    api_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from analyser_api.logging import RequestContextMiddleware, configure_logging
from analyser_api.routers import agents, calls, workspaces
from analyser_api.storage.factory import create_storage

_OPERATION_IDS = {
    "create_workspace": "createWorkspace",
    "get_workspace": "getWorkspace",
    "delete_workspace": "deleteWorkspace",
    "list_agents": "listAgents",
    "create_agent": "createAgent",
    "update_agent": "updateAgent",
    "upload_call": "createCall",
    "list_calls": "listCalls",
    "get_call": "getCall",
    "delete_call": "deleteCall",
    "audio_url": "getCallAudioUrl",
    "media_audio": "getMediaAudio",
    "healthz": "healthz",
}


def _operation_id(route: APIRoute) -> str:
    if route.name in _OPERATION_IDS:
        return _OPERATION_IDS[route.name]
    parts = route.name.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    active = settings or Settings()
    configure_logging(active.log_level)

    app = FastAPI(
        title="Call Analyser API",
        version="0.1.0",
        lifespan=lifespan,
        generate_unique_id_function=_operation_id,
    )
    app.state.settings = active
    app.state.engine = create_engine(active)
    app.state.session_factory = async_sessionmaker(app.state.engine, expire_on_commit=False)
    app.state.storage = create_storage(active)

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    if active.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active.cors_origins,
            allow_methods=["*"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )
    # Added last so it is the outermost middleware and covers every response.
    app.add_middleware(RequestContextMiddleware)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(workspaces.router)
    app.include_router(agents.router)
    app.include_router(calls.router)

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(WorkspaceAuthError, workspace_auth_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app
