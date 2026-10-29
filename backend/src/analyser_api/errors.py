"""Stable API error envelopes and exception handlers."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import cast
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger("analyser_api.errors")

MESSAGES: dict[str, str] = {
    "unauthorized": "A valid workspace token is required.",
    "not_found": "Not found.",
    "validation_error": "Request validation failed.",
    "consent_required": "Consent is required before uploading a call.",
    "file_too_large": "The uploaded file is too large.",
    "unsupported_media": "The uploaded file is not a supported audio format.",
    "invalid_audio": "The uploaded file is not valid audio.",
    "audio_too_long": "The call is longer than the configured maximum.",
    "audio_too_short": "The call is shorter than the configured minimum.",
    "quota_exceeded": "The call quota has been reached.",
    "budget_exceeded": "The daily analysis budget has been reached.",
    "rate_limited": "Too many requests. Try again later.",
    "not_ready": "The requested resource is not ready.",
    "conflict": "The request conflicts with the current state.",
    "playbook_unavailable": "The playbook index is unavailable.",
    "service_unavailable": "The service is temporarily unavailable.",
    "internal_error": "An unexpected error occurred.",
}

STATUS_BY_CODE: dict[str, int] = {
    "unauthorized": 401,
    "not_found": 404,
    "validation_error": 422,
    "consent_required": 400,
    "file_too_large": 413,
    "unsupported_media": 415,
    "invalid_audio": 422,
    "audio_too_long": 422,
    "audio_too_short": 422,
    "quota_exceeded": 429,
    "budget_exceeded": 429,
    "rate_limited": 429,
    "not_ready": 409,
    "conflict": 409,
    "playbook_unavailable": 503,
    "service_unavailable": 503,
    "internal_error": 500,
}

CODE_BY_STATUS: dict[int, str] = {
    400: "validation_error",
    401: "unauthorized",
    403: "not_found",
    404: "not_found",
    409: "conflict",
    413: "file_too_large",
    415: "unsupported_media",
    422: "validation_error",
    429: "rate_limited",
    503: "service_unavailable",
}


class APIError(Exception):
    """An error that is safe to expose to API clients."""

    def __init__(
        self,
        code: str,
        *,
        message: str | None = None,
        status_code: int | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message or MESSAGES.get(code, "Request failed."))
        self.code = code
        self.message = message or MESSAGES.get(code, "Request failed.")
        self.status_code = status_code or STATUS_BY_CODE.get(code, 500)
        self.headers = dict(headers or {})


def request_id_for(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) and value else str(uuid4())


def error_response(
    code: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    response_headers = dict(headers or {})
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id or str(uuid4()),
            }
        },
        headers=response_headers,
    )


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(APIError, exc)
    return error_response(
        error.code,
        error.message,
        error.status_code,
        request_id_for(request),
        headers=error.headers,
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del exc
    return error_response(
        "validation_error",
        MESSAGES["validation_error"],
        422,
        request_id_for(request),
    )


async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(HTTPException, exc)
    detail = error.detail if isinstance(error.detail, str) else ""
    code = detail if detail in STATUS_BY_CODE else CODE_BY_STATUS.get(error.status_code)
    if code is None:
        code = "internal_error" if error.status_code >= 500 else "validation_error"
    headers = dict(error.headers or {})
    if code == "unauthorized" and "WWW-Authenticate" not in headers:
        headers["WWW-Authenticate"] = "Bearer"
    return error_response(
        code,
        MESSAGES.get(code, "Request failed."),
        error.status_code,
        request_id_for(request),
        headers=headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never log exception text: package exceptions may contain transcript content.
    logger.error("unhandled_exception error_type=%s", type(exc).__name__)
    return error_response(
        "internal_error",
        MESSAGES["internal_error"],
        500,
        request_id_for(request),
    )
