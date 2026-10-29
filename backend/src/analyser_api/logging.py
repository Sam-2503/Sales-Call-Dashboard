"""Structured request logging, request IDs, and response security headers."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Mapping, MutableMapping
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
workspace_id_ctx: ContextVar[str | None] = ContextVar("workspace_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SENSITIVE_RE = re.compile(
    r"(?i)\b(authorization|token|access_token|jwt|transcript|body|file|audio_url)\s*=\s*([^\s&,)]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_QUERY_RE = re.compile(r"\?[^\s\"']+")


def set_workspace_id(workspace_id: str | None) -> None:
    workspace_id_ctx.set(workspace_id)


def set_job_id(job_id: str | None) -> None:
    job_id_ctx.set(job_id)


class RedactionFilter(logging.Filter):
    """Remove query strings, bearer tokens, and labelled sensitive values."""

    @staticmethod
    def _redact(value: str) -> str:
        value = _SENSITIVE_RE.sub(r"\1=[REDACTED]", value)
        value = _BEARER_RE.sub("Bearer [REDACTED]", value)
        return _QUERY_RE.sub("?[REDACTED]", value)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if isinstance(record.args, tuple):
            record.args = tuple(
                self._redact(value) if isinstance(value, str) else value for value in record.args
            )
        elif isinstance(record.args, Mapping):
            record.args = {
                key: self._redact(value) if isinstance(value, str) else value
                for key, value in record.args.items()
            }
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line with request/workspace/job correlation ids."""

    _RESERVED = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field, context in (
            ("request_id", request_id_ctx),
            ("workspace_id", workspace_id_ctx),
            ("job_id", job_id_ctx),
        ):
            value = getattr(record, field, None) or context.get()
            if value:
                payload[field] = str(value)
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str, separators=(",", ":"), sort_keys=True)


def configure_logging(level: str) -> None:
    """Install the JSON handler once and disable uvicorn's access logger."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    if not any(handler.name == "analyser-json" for handler in root.handlers):
        handler = logging.StreamHandler()
        handler.name = "analyser-json"
        handler.setFormatter(JsonFormatter())
        handler.addFilter(RedactionFilter())
        root.addHandler(handler)

    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False
    access.disabled = True

    # HTTP client logs include full URLs, and therefore signed query strings.
    for noisy in ("httpx", "httpx2", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _request_id(scope: Scope) -> str:
    headers = dict(scope.get("headers", []))
    raw = headers.get(b"x-request-id", b"")
    value = raw.decode("ascii", "ignore")
    return value if _REQUEST_ID_RE.fullmatch(value) else str(uuid4())


def _apply_security_headers(headers: MutableHeaders) -> None:
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["Referrer-Policy"] = "no-referrer"
    headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"


class RequestContextMiddleware:
    """Assign a request id, attach security headers, and emit one request log line."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = logging.getLogger("analyser_api.requests")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id(scope)
        state = scope.setdefault("state", {})
        if isinstance(state, dict):
            state["request_id"] = request_id

        request_token = request_id_ctx.set(request_id)
        workspace_id_ctx.set(None)
        job_id_ctx.set(None)
        started = time.perf_counter()
        status_code = 500

        async def send_with_context(message: MutableMapping[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                raw_headers = message.get("headers", [])
                headers = MutableHeaders(raw=raw_headers)
                headers["X-Request-ID"] = request_id
                _apply_security_headers(headers)
                message["headers"] = headers.raw
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            self.logger.info(
                "request method=%s path=%s status=%s duration_ms=%.1f",
                scope["method"],
                scope["path"],
                status_code,
                duration_ms,
            )
            request_id_ctx.reset(request_token)
            workspace_id_ctx.set(None)
            job_id_ctx.set(None)
