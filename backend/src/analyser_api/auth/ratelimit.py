"""Small in-memory token buckets for anonymous workspace creation."""

from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import Request


@dataclass
class _Window:
    started: float
    count: int


class RateLimiter:
    """A fixed-window limiter for cheap, per-process abuse protection."""

    def __init__(self, limit: int, window_s: float) -> None:
        self.limit = limit
        self.window_s = window_s
        self._windows: dict[str, _Window] = {}
        self._last_prune = 0.0

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        self._prune(now)
        window = self._windows.get(key)
        if window is None or now - window.started >= self.window_s:
            self._windows[key] = _Window(now, 1)
            return self.limit >= 1
        if window.count >= self.limit:
            return False
        window.count += 1
        return True

    def retry_after(self, key: str) -> int:
        window = self._windows.get(key)
        if window is None:
            return 1
        return max(1, int(self.window_s - (time.monotonic() - window.started)))

    def _prune(self, now: float) -> None:
        if now - self._last_prune < 60:
            return
        self._last_prune = now
        self._windows = {
            key: window
            for key, window in self._windows.items()
            if now - window.started < self.window_s
        }


def client_ip(request: Request, trusted_proxy_count: int) -> str:
    """Read the client address only from the trusted right-hand proxy hops."""
    if request.client is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and trusted_proxy_count > 0:
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        index = len(parts) - trusted_proxy_count
        if 0 <= index < len(parts):
            return parts[index]
    return request.client.host
