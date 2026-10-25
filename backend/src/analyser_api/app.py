"""Application factory and Stage 0 health endpoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from analyser_api.config import Settings
from analyser_api.errors import unhandled_error_handler, validation_error_handler
from analyser_api.logging import RequestLogMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    active = settings or Settings()
    logging.basicConfig(level=active.log_level)
    app = FastAPI(title="Call Analyser API", version="0.1.0", lifespan=lifespan)
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

    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app


app = create_app()
