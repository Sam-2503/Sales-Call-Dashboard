from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from analyser_api.app import create_app
from analyser_api.auth.tokens import issue_media_token, issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call, Workspace

pytestmark = pytest.mark.db


async def _seed(session_factory):
    async with session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        agent = Agent(workspace_id=workspace.id, name="Me")
        session.add(agent)
        await session.flush()
        return workspace, agent


@pytest.mark.asyncio
async def test_upload_requires_consent_and_persists_audio(
    database_url, db_session_factory, tmp_path: Path, monkeypatch
) -> None:
    async def fake_probe(path, timeout):
        del path, timeout
        return 65.0, "wav"

    monkeypatch.setattr("analyser_api.routers.calls.probe_audio", fake_probe)
    workspace, _ = await _seed(db_session_factory)
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        daily_budget_usd=10,
        max_upload_mb=1,
        storage_dir=tmp_path / "audio",
    )
    token = issue_token(workspace.id, settings)
    headers = {"Authorization": f"Bearer {token}"}
    app = create_app(settings)
    with TestClient(app) as client:
        no_consent = client.post(
            "/api/v1/calls",
            files={"file": ("call.wav", b"RIFFfake", "audio/wav")},
            data={"consent": "false"},
            headers=headers,
        )
        too_large = client.post(
            "/api/v1/calls",
            files={"file": ("call.wav", b"x" * (1024 * 1024 + 1), "audio/wav")},
            data={"consent": "true"},
            headers=headers,
        )
        created = client.post(
            "/api/v1/calls",
            files={"file": ("call.wav", b"0123456789", "audio/wav")},
            data={"consent": "true", "title": "Uploaded"},
            headers=headers,
        )
        body = created.json()
        detail = client.get(f"/api/v1/calls/{body['call_id']}", headers=headers)
        media_token = issue_media_token(workspace.id, body["call_id"], settings)
        ranged = client.get(
            f"/api/v1/media/audio?t={media_token}&call_id={body['call_id']}",
            headers={"Range": "bytes=2-5"},
        )
        deleted = client.delete(f"/api/v1/calls/{body['call_id']}", headers=headers)
    assert no_consent.status_code == 400
    assert no_consent.json()["error"]["code"] == "consent_required"
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "file_too_large"
    assert created.status_code == 202
    assert detail.json()["has_audio"] is True
    assert ranged.status_code == 206
    assert ranged.content == b"2345"
    assert ranged.headers["content-range"].startswith("bytes 2-5/")
    assert deleted.status_code == 204
    async with db_session_factory() as session:
        assert await session.scalar(select(Call).where(Call.id == body["call_id"])) is None
