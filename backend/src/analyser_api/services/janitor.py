"""Retention and idle-workspace cleanup."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.config import Settings
from analyser_api.db.models import Call, Workspace
from analyser_api.storage.base import AudioStorage

logger = logging.getLogger("analyser_api.janitor")


class Janitor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        storage: AudioStorage,
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage
        self._settings = settings
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._loop(), name="analyser-janitor")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._settings.janitor_interval_s)
            except TimeoutError:
                try:
                    await self.run_once()
                except Exception as exc:  # pragma: no cover - retried next cycle
                    logger.error("janitor_failed error_type=%s", type(exc).__name__)

    async def run_once(self, *, now: datetime | None = None) -> None:
        current = now or datetime.now(UTC)
        call_cutoff = current - timedelta(days=self._settings.retention_days)
        workspace_cutoff = current - timedelta(days=self._settings.workspace_idle_days)
        demo_cutoff = current - timedelta(days=self._settings.demo_idle_days)
        async with self._session_factory() as session:
            old_call_prefixes = [
                (call.workspace_id, call.id)
                for call in await session.scalars(
                    select(Call).where(Call.is_demo.is_(False), Call.created_at < call_cutoff)
                )
            ]
            idle_workspaces: list[UUID] = list(
                await session.scalars(
                    select(Workspace.id).where(
                        Workspace.is_demo.is_(False),
                        Workspace.last_activity_at < workspace_cutoff,
                    )
                )
            )
            idle_demos: list[UUID] = list(
                await session.scalars(
                    select(Workspace.id).where(
                        Workspace.is_demo.is_(True),
                        Workspace.last_activity_at < demo_cutoff,
                    )
                )
            )
        for workspace_id, call_id in old_call_prefixes:
            await self._storage.delete_prefix(f"{workspace_id}/{call_id}")
        for workspace_id in (*idle_workspaces, *idle_demos):
            await self._storage.delete_prefix(str(workspace_id))
        async with self._session_factory() as session, session.begin():
            for _workspace_id, call_id in old_call_prefixes:
                await session.execute(delete(Call).where(Call.id == call_id))
            for workspace_id in (*idle_workspaces, *idle_demos):
                await session.execute(delete(Workspace).where(Workspace.id == workspace_id))
