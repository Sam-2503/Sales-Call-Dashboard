"""Application factory and Stage 0 HTTP foundation."""

from __future__ import annotations

import asyncio
import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from call_analyser.playbook import PlaybookIndex, load_playbook_spec
from call_analyser.rubric import load_rubric
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from analyser_api.auth.ratelimit import RateLimiter
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
from analyser_api.jobs.runner import PackageRunner
from analyser_api.jobs.worker import JobWorker, ThreadedWorker
from analyser_api.logging import RequestContextMiddleware, configure_logging
from analyser_api.routers import admin, agents, calls, feedback, jobs, meta, trends, workspaces
from analyser_api.services.janitor import Janitor
from analyser_api.services.playbook_artifact import sync as sync_playbook
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
    "get_job": "getJob",
    "job_events": "streamJobEvents",
    "trend_scores": "getTrendScores",
    "weak_spots": "getWeakSpots",
    "benchmarks": "getBenchmarks",
    "active_rubric": "getRubric",
    "playbook_metadata": "getPlaybook",
    "public_meta": "getMeta",
    "admin_stats": "getAdminStats",
    "feedback_jsonl": "getAdminFeedback",
    "healthz": "healthz",
    "readyz": "readyz",
}


def _operation_id(route: APIRoute) -> str:
    if route.name in _OPERATION_IDS:
        return _OPERATION_IDS[route.name]
    parts = route.name.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    worker = app.state.worker
    settings = app.state.settings
    if settings.playbook_artifact_prefix:
        try:
            await asyncio.to_thread(sync_playbook, settings)
            app.state.playbook_ready = True
        except Exception as exc:
            app.state.playbook_ready = False
            logging.getLogger("analyser_api.startup").error(
                "playbook_sync_failed error_type=%s", type(exc).__name__
            )
    await app.state.janitor.start()
    if worker is not None and app.state.playbook_ready:
        await worker.start()
    try:
        yield
    finally:
        if worker is not None:
            await worker.stop()
        await app.state.janitor.stop()
        await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    active = settings or Settings()
    if active.environment == "dev" and not active.jwt_secret:
        # Dev convenience only; restarting invalidates previously issued tokens.
        active.jwt_secret = secrets.token_urlsafe(32)
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
    app.state.rubric = load_rubric(active.rubric_path)
    app.state.playbook_ready = True
    app.state.workspace_limiter = RateLimiter(active.workspace_rate_limit_per_hour, 3600)
    app.state.demo_limiter = RateLimiter(active.demo_workspaces_per_ip_per_day, 86400)
    app.state.upload_limiter = RateLimiter(active.upload_rate_limit_per_hour, 3600)
    app.state.janitor = Janitor(app.state.session_factory, app.state.storage, active)
    app.state.worker = None
    if active.worker_enabled and active.worker_mode != "off":
        if active.worker_mode == "thread":
            app.state.worker = ThreadedWorker(active)
        else:
            app.state.worker = JobWorker(
                app.state.session_factory,
                PackageRunner(active, app.state.session_factory),
                app.state.storage,
                active,
            )

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

    @app.get("/readyz", tags=["meta"])
    async def readyz() -> JSONResponse:
        checks: dict[str, str] = {}
        try:
            async with app.state.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "failed"
        checks["rubric"] = "ok" if app.state.rubric is not None else "failed"
        try:
            await app.state.storage.healthcheck()
            checks["storage"] = "ok"
        except Exception:
            checks["storage"] = "failed"
        package = active.package
        if package.fake_mode or package.playbook_grounding != "on":
            checks["playbook"] = "skipped"
        elif active.playbook_path is None or not app.state.playbook_ready:
            checks["playbook"] = "failed"
        else:
            try:
                PlaybookIndex.open(load_playbook_spec(active.playbook_path), package)
                checks["playbook"] = "ok"
            except Exception:
                checks["playbook"] = "failed"
        ready = all(value != "failed" for value in checks.values())
        return JSONResponse(
            {"status": "ok" if ready else "not_ready", "checks": checks},
            status_code=200 if ready else 503,
        )

    app.include_router(workspaces.router)
    app.include_router(agents.router)
    app.include_router(calls.router)
    app.include_router(feedback.router)
    app.include_router(jobs.router)
    app.include_router(trends.router)
    app.include_router(meta.router)
    app.include_router(admin.router)

    static_dir = active.static_dir
    if static_dir is not None and Path(static_dir).is_dir():
        index_file = Path(static_dir) / "index.html"

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(index_file, headers={"Cache-Control": "no-cache"})

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str) -> FileResponse:
            if path.startswith(("api/", "healthz", "readyz")):
                raise HTTPException(status_code=404, detail="Not found")
            candidate = Path(static_dir) / path
            if candidate.is_file():
                headers = {"Cache-Control": "no-cache"}
                if path.startswith("assets/"):
                    headers = {"Cache-Control": "public, max-age=31536000, immutable"}
                return FileResponse(candidate, headers=headers)
            return FileResponse(index_file, headers={"Cache-Control": "no-cache"})

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(WorkspaceAuthError, workspace_auth_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app
