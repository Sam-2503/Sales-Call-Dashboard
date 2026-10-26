"""Application factory and Stage 0 health endpoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker

from analyser_api.config import Settings
from analyser_api.db.engine import create_engine
from analyser_api.deps import WorkspaceAuthError, workspace_auth_handler
from analyser_api.errors import unhandled_error_handler, validation_error_handler
from analyser_api.logging import RequestLogMiddleware
from analyser_api.routers import agents, calls, workspaces
from analyser_api.storage.factory import create_storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    active = settings or Settings()
    logging.basicConfig(level=active.log_level)
    app = FastAPI(title="Call Analyser API", version="0.1.0", lifespan=lifespan)
    app.state.settings = active
    app.state.engine = create_engine(active)
    app.state.session_factory = async_sessionmaker(app.state.engine, expire_on_commit=False)
    app.state.storage = create_storage(active)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    if active.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active.cors_origins,
            allow_methods=["*"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(workspaces.router)
    app.include_router(agents.router)
    app.include_router(calls.router)
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(WorkspaceAuthError, workspace_auth_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app


app = create_app()
