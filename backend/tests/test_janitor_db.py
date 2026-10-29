from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from analyser_api.config import Settings
from analyser_api.db.models import Call, Workspace
from analyser_api.services.janitor import Janitor
from analyser_api.storage.local import LocalStorage

pytestmark = pytest.mark.db


@pytest.mark.asyncio
async def test_janitor_deletes_old_calls_and_idle_workspaces(
    database_url, db_session_factory, tmp_path: Path
) -> None:
    now = datetime.now(UTC)
    storage = LocalStorage(tmp_path / "audio")
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        retention_days=30,
        workspace_idle_days=60,
        demo_idle_days=3,
        storage_dir=storage.root,
    )
    call_id = uuid4()
    workspace_id = uuid4()
    key = f"{workspace_id}/{call_id}/original.wav"
    audio_path = storage.root / key
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"audio")
    async with db_session_factory() as session, session.begin():
        session.add(
            Workspace(
                id=workspace_id,
                is_demo=False,
                last_activity_at=now - timedelta(days=70),
            )
        )
        await session.flush()
        session.add(
            Call(
                id=call_id,
                workspace_id=workspace_id,
                consent_at=now - timedelta(days=40),
                created_at=now - timedelta(days=40),
                audio_key=key,
            )
        )
    await Janitor(db_session_factory, storage, settings).run_once(now=now)
    async with db_session_factory() as session:
        assert await session.scalar(select(func.count(Call.id))) == 0
        assert await session.scalar(select(func.count(Workspace.id))) == 0
    assert not audio_path.exists()


@pytest.mark.asyncio
async def test_janitor_spares_recent_calls_and_active_demos(
    database_url, db_session_factory, tmp_path: Path
) -> None:
    now = datetime.now(UTC)
    storage = LocalStorage(tmp_path / "audio")
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        storage_dir=storage.root,
    )
    recent_ws = Workspace(label="recent")
    demo_ws = Workspace(label="demo", is_demo=True, last_activity_at=now)
    async with db_session_factory() as session, session.begin():
        session.add_all((recent_ws, demo_ws))
        await session.flush()
        session.add(
            Call(
                workspace_id=recent_ws.id,
                consent_at=now,
                created_at=now,
            )
        )
        session.add(
            Call(
                workspace_id=demo_ws.id,
                consent_at=now,
                created_at=now - timedelta(days=40),
                is_demo=True,
            )
        )
    await Janitor(db_session_factory, storage, settings).run_once(now=now)
    async with db_session_factory() as session:
        assert await session.scalar(select(func.count(Call.id))) == 2
        assert await session.scalar(select(func.count(Workspace.id))) == 2
