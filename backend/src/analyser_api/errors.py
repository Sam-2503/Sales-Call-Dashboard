"""Stable API error envelopes and exception handlers."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


def error_response(
    code: str, message: str, status_code: int, request_id: str | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id or str(uuid4()),
            }
        },
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del request, exc
    return error_response("validation_error", "Request validation failed.", 422)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del request, exc
    return error_response("internal_error", "An unexpected error occurred.", 500)


def http_error_detail(detail: Any) -> str:
    return detail if isinstance(detail, str) else "Request failed."
