from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from analyser_api.db.models import Base

pytestmark = pytest.mark.db


@pytest.mark.asyncio
async def test_migration_applies_and_matches_models(database_url, db_engine) -> None:
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    config = Config(str(Path("alembic.ini")))
    config.set_main_option("sqlalchemy.url", database_url)
    await asyncio.to_thread(command.upgrade, config, "head")
    await asyncio.to_thread(command.check, config)
    async with db_engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
    assert {
        "workspaces",
        "agents",
        "calls",
        "jobs",
        "job_events",
        "reports",
        "call_category_scores",
        "call_item_results",
        "report_findings",
        "feedback",
        "stage_cache",
    } <= tables
