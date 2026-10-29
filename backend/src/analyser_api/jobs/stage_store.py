"""Per-call Postgres stage cache implementing the package's StageStore protocol."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.db.models import StageCache


class PostgresStageStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        call_id: UUID,
    ) -> None:
        self._session_factory = session_factory
        self._call_id = call_id

    async def get(self, key: str) -> dict[str, Any] | None:
        async with self._session_factory() as session:
            row = await session.get(StageCache, (self._call_id, key))
            return dict(row.value) if row is not None else None

    async def put(self, key: str, value: dict[str, Any]) -> None:
        async with self._session_factory() as session, session.begin():
            statement = insert(StageCache).values(
                call_id=self._call_id,
                key=key,
                stage="analysis",
                value=value,
                created_at=datetime.now(UTC),
            )
            statement = statement.on_conflict_do_update(
                index_elements=[StageCache.call_id, StageCache.key],
                set_={"value": value, "stage": "analysis", "created_at": datetime.now(UTC)},
            )
            await session.execute(statement)
