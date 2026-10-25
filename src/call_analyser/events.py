"""Runnable callbacks that emit user-facing progress events."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Literal
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler

from call_analyser.schemas.events import ProgressEvent

STAGE_WEIGHTS: dict[str, int] = {
    "ingest": 5,
    "transcribe": 20,
    "assign_roles": 5,
    "audio_metrics": 10,
    "rubric_results": 15,
    "missed_moments": 10,
    "customer_signals": 10,
    "grounding": 15,
    "next_steps": 5,
    "coaching": 5,
}

ProgressSink = Callable[[ProgressEvent], Awaitable[None]]


class ProgressCallbackHandler(AsyncCallbackHandler):
    """Emit ordered events only for explicitly registered stage names."""

    def __init__(self, sink: ProgressSink, registered_stages: set[str]) -> None:
        self.sink = sink
        self.registered_stages = registered_stages
        self.started: dict[UUID, tuple[str, float]] = {}

    async def _emit(
        self,
        stage: str,
        status: Literal["started", "finished", "failed", "cached"],
        elapsed_s: float,
        detail: str | None = None,
    ) -> None:
        await self.sink(
            ProgressEvent(
                stage=stage, status=status, ts=datetime.now(UTC), elapsed_s=elapsed_s, detail=detail
            )
        )

    async def on_chain_start(
        self,
        serialized: dict[str, Any] | None,
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        name = str((serialized or {}).get("name") or kwargs.get("name", ""))
        if name in self.registered_stages:
            self.started[run_id] = (name, monotonic())
            await self._emit(name, "started", 0)

    async def on_chain_end(self, outputs: dict[str, Any], *, run_id: UUID, **_: Any) -> None:
        started = self.started.pop(run_id, None)
        if started is not None:
            stage, started_at = started
            await self._emit(stage, "finished", monotonic() - started_at)

    async def on_chain_error(self, error: BaseException, *, run_id: UUID, **_: Any) -> None:
        started = self.started.pop(run_id, None)
        if started is not None:
            stage, started_at = started
            await self._emit(stage, "failed", monotonic() - started_at, str(error))
