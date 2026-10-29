from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from analyser_api.app import create_app
from analyser_api.config import Settings
from analyser_api.db.models import Call, Workspace
from analyser_api.services.demo import seed_demo_workspace

pytestmark = pytest.mark.db


def settings_for(database_url: str, storage_dir: Path) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        demo_seed_calls=5,
        storage_dir=storage_dir,
    )


@pytest.mark.asyncio
async def test_demo_seed_is_idempotent_and_trends_are_available(
    database_url, db_session_factory, tmp_path: Path
) -> None:
    settings = settings_for(database_url, tmp_path)
    first_id, token = await seed_demo_workspace(
        db_session_factory, settings, calls=5, label="demo-test", reuse=True
    )
    second_id, _ = await seed_demo_workspace(
        db_session_factory, settings, calls=9, label="demo-test", reuse=True
    )
    assert second_id == first_id
    async with db_session_factory() as session:
        workspace = await session.get(Workspace, first_id)
        count = await session.scalar(
            select(func.count(Call.id)).where(Call.workspace_id == first_id)
        )
        call = await session.scalar(select(Call).where(Call.workspace_id == first_id).limit(1))
    assert workspace is not None and workspace.is_demo is True
    assert int(count or 0) == 5
    assert call is not None
    headers = {"Authorization": f"Bearer {token}"}
    app = create_app(settings)
    with TestClient(app) as client:
        scores = client.get("/api/v1/trends/scores", headers=headers)
        weak = client.get("/api/v1/trends/weak-spots", headers=headers)
        bench = client.get(f"/api/v1/benchmarks?call_id={call.id}", headers=headers)
    assert scores.status_code == 200
    assert scores.json()["n"] == 5
    assert len(scores.json()["points"]) == 5
    assert weak.status_code == 200
    assert weak.json()["available"] is True
    assert weak.json()["n_calls"] == 5
    assert bench.status_code == 200
    assert bench.json()["call_id"] == str(call.id)
    assert bench.json()["overall"]["call"] is not None
    assert bench.json()["n"]["agent"] >= 1
    assert bench.json()["n"]["team"] >= 2
