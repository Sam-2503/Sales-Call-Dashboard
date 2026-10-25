"""Async SQLAlchemy engine construction."""

from __future__ import annotations

import asyncio

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from analyser_api.config import Settings
from analyser_api.db.dsn import asyncpg_dsn


def create_engine(settings: Settings) -> AsyncEngine:
    connect_args: dict[str, object] = {}
    if settings.db_pooler:
        connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    return create_async_engine(
        asyncpg_dsn(settings.database_url),
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )


async def connect_with_retry(engine: AsyncEngine, settings: Settings) -> AsyncConnection:
    """Open the first connection with bounded retries for sleeping databases."""

    last_error: Exception | None = None
    for attempt in range(settings.db_connect_retries + 1):
        try:
            return await engine.connect()
        except SQLAlchemyError as error:
            last_error = error
            if attempt == settings.db_connect_retries:
                raise
            await asyncio.sleep(0.5 * (2**attempt))
    raise RuntimeError("database connection failed") from last_error
