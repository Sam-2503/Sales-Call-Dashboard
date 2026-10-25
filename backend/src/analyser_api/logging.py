"""Request logging with query-string and sensitive-value redaction."""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send


class RequestLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = logging.getLogger("analyser_api.requests")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        status_code = 500

        async def capture(message: MutableMapping[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        await self.app(scope, receive, capture)
        self.logger.info(
            "request method=%s path=%s status=%s",
            scope["method"],
            scope["path"],
            status_code,
        )
