from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from analyser_api.app import create_app
from analyser_api.auth.tokens import issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call, Job, Workspace
from analyser_api.services.demo import _report
from analyser_api.services.reports import persist_report

pytestmark = pytest.mark.db


async def _seed(session_factory):
    async with session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        agent = Agent(workspace_id=workspace.id, name="Me")
        session.add(agent)
        await session.flush()
        call = Call(
            workspace_id=workspace.id,
            agent_id=agent.id,
            status="completed",
            consent_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        session.add(call)
        await session.flush()
        return workspace, call


@pytest.mark.asyncio
async def test_reanalysis_keeps_previous_report_and_respects_limit(
    database_url, db_session_factory, tmp_path: Path
) -> None:
    workspace, call = await _seed(db_session_factory)
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        max_reanalyses_per_call=1,
        daily_budget_usd=10,
        storage_dir=tmp_path,
    )
    from call_analyser.rubric import load_rubric

    await persist_report(
        db_session_factory,
        call.id,
        _report(load_rubric(settings.rubric_path), settings, score=70, outcome="advanced", index=0),
    )
    token = issue_token(workspace.id, settings)
    headers = {"Authorization": f"Bearer {token}"}
    app = create_app(settings)
    with TestClient(app) as client:
        before = client.get(f"/api/v1/calls/{call.id}/report", headers=headers)
        first = client.post(
            f"/api/v1/calls/{call.id}/reanalyse",
            json={"agent_speaker": "Agent"},
            headers=headers,
        )
        second = client.post(f"/api/v1/calls/{call.id}/reanalyse", json={}, headers=headers)
        during = client.get(f"/api/v1/calls/{call.id}/report", headers=headers)
    assert before.status_code == 200
    assert first.status_code == 202
    assert second.status_code == 409
    assert during.status_code == 200
    assert during.json() == before.json()
    async with db_session_factory() as session:
        updated = await session.get(Call, call.id)
        job = await session.scalar(
            select(Job).where(Job.call_id == call.id).order_by(Job.created_at.desc())
        )
    assert updated is not None
    assert updated.reanalysis_count == 1
    assert job is not None
    assert job.options == {"agent_speaker": "Agent"}
