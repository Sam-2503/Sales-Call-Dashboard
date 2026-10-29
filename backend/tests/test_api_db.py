from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from analyser_api.app import create_app
from analyser_api.auth.tokens import issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call, Feedback, Job, JobEvent, Workspace
from analyser_api.services.demo import _report
from analyser_api.services.reports import persist_report

pytestmark = pytest.mark.db


def api_settings(database_url: str, **overrides) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        storage_dir="/tmp/analyser-api-test-audio",
        **overrides,
    )


async def _workspace(session_factory, name: str = "Me") -> tuple[Workspace, Agent]:
    async with session_factory() as session, session.begin():
        workspace = Workspace(label=f"test-{uuid4()}")
        session.add(workspace)
        await session.flush()
        agent = Agent(workspace_id=workspace.id, name=name)
        session.add(agent)
        await session.flush()
        return workspace, agent


@pytest.mark.asyncio
async def test_tenant_isolation_for_agents(database_url, db_session_factory) -> None:
    workspace_a, agent_a = await _workspace(db_session_factory)
    workspace_b, agent_b = await _workspace(db_session_factory, "Other")
    token_a = issue_token(workspace_a.id, api_settings(database_url))
    token_b = issue_token(workspace_b.id, api_settings(database_url))
    app = create_app(api_settings(database_url))
    with TestClient(app) as client:
        listed = client.get("/api/v1/agents", headers={"Authorization": f"Bearer {token_a}"})
        crossed = client.patch(
            f"/api/v1/agents/{agent_b.id}",
            json={"name": "hijacked"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        own = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token_b}"})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [str(agent_a.id)]
    assert crossed.status_code == 404
    assert crossed.json()["error"]["code"] == "not_found"
    assert own.status_code == 200
    assert own.json()["workspace_id"] == str(workspace_b.id)


@pytest.mark.asyncio
async def test_call_list_report_and_feedback_are_workspace_scoped(
    database_url, db_session_factory
) -> None:
    workspace, agent = await _workspace(db_session_factory)
    call = Call(
        workspace_id=workspace.id,
        agent_id=agent.id,
        title="Scoped call",
        status="completed",
        consent_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    async with db_session_factory() as session, session.begin():
        session.add(call)
        await session.flush()
    from call_analyser.rubric import load_rubric

    report = _report(
        load_rubric(api_settings(database_url).rubric_path),
        api_settings(database_url),
        score=70,
        outcome="advanced",
        index=0,
    )
    await persist_report(db_session_factory, call.id, report)
    token = issue_token(workspace.id, api_settings(database_url))
    headers = {"Authorization": f"Bearer {token}"}
    app = create_app(api_settings(database_url))
    with TestClient(app) as client:
        listing = client.get("/api/v1/calls", headers=headers)
        detail = client.get(f"/api/v1/calls/{call.id}", headers=headers)
        report_response = client.get(f"/api/v1/calls/{call.id}/report", headers=headers)
        finding_id = (
            report.missed_moments[0].id if report.missed_moments else report.rubric_results[0].id
        )
        put = client.put(
            f"/api/v1/calls/{call.id}/feedback/{finding_id}",
            json={"finding_id": finding_id, "kind": "missed_moment", "verdict": "helpful"},
            headers=headers,
        )
        listed_feedback = client.get(f"/api/v1/calls/{call.id}/feedback", headers=headers)
        deleted = client.delete(f"/api/v1/calls/{call.id}/feedback/{finding_id}", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["items"][0]["id"] == str(call.id)
    assert detail.status_code == 200
    assert detail.json()["has_audio"] is False
    assert report_response.status_code == 200
    assert "debug" not in report_response.json()
    assert report_response.headers["cache-control"] == "no-store"
    assert put.status_code == 200
    assert listed_feedback.json()[0]["verdict"] == "helpful"
    assert deleted.status_code == 204
    async with db_session_factory() as session:
        assert await session.scalar(select(Feedback).where(Feedback.call_id == call.id)) is None


@pytest.mark.asyncio
async def test_global_job_endpoint_and_sse_replay(database_url, db_session_factory) -> None:
    workspace, agent = await _workspace(db_session_factory)
    call = Call(
        workspace_id=workspace.id,
        agent_id=agent.id,
        title="Job call",
        status="completed",
        consent_at=datetime.now(UTC),
    )
    async with db_session_factory() as session, session.begin():
        session.add(call)
        await session.flush()
        job = Job(call_id=call.id, status="succeeded", percent=100, error_code=None)
        session.add(job)
        await session.flush()
        session.add(
            JobEvent(
                job_id=job.id,
                stage="ingest",
                status="finished",
                percent=5,
                detail={},
            )
        )
    token = issue_token(workspace.id, api_settings(database_url))
    headers = {"Authorization": f"Bearer {token}"}
    app = create_app(api_settings(database_url))
    with TestClient(app) as client:
        status = client.get(f"/api/v1/jobs/{job.id}", headers=headers)
        with client.stream("GET", f"/api/v1/jobs/{job.id}/events", headers=headers) as stream:
            body = "".join(stream.iter_text())
    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"
    assert "id: 1" in body or "event: progress" in body
    assert "event: done" in body


@pytest.mark.asyncio
async def test_admin_requires_token_and_readiness_reports_dependencies(
    database_url, db_session_factory
) -> None:
    from call_analyser.config import Settings as PackageSettings

    settings = api_settings(
        database_url,
        admin_token="operator",
        package=PackageSettings(_env_file=None, fake_mode=True),
    )
    app = create_app(settings)
    with TestClient(app) as client:
        absent = client.get("/api/v1/admin/stats")
        denied = client.get("/api/v1/admin/stats", headers={"X-Admin-Token": "wrong"})
        allowed = client.get("/api/v1/admin/stats", headers={"X-Admin-Token": "operator"})
        ready = client.get("/readyz")
    assert absent.status_code == 404
    assert denied.status_code == 404
    assert allowed.status_code == 200
    assert allowed.json()["calls"] == {}
    assert ready.status_code == 200
    assert ready.json()["checks"]["database"] == "ok"
    assert ready.json()["checks"]["playbook"] == "skipped"
