from __future__ import annotations

from datetime import UTC, datetime

import pytest

from analyser_api.config import Settings
from analyser_api.db.models import Call, Report, Workspace
from analyser_api.errors import APIError
from analyser_api.services.quotas import check_budget, check_call_quota

pytestmark = pytest.mark.db


def settings_for(database_url: str, **overrides) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        **overrides,
    )


@pytest.mark.asyncio
async def test_workspace_quota_stops_at_the_limit(database_url, db_session_factory) -> None:
    settings = settings_for(database_url, daily_calls_per_workspace=2)
    async with db_session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        for _ in range(2):
            session.add(Call(workspace_id=workspace.id, consent_at=datetime.now(UTC)))
        workspace_id = workspace.id
    async with db_session_factory() as session:
        with pytest.raises(APIError) as raised:
            await check_call_quota(session, workspace_id, settings)
    assert raised.value.code == "quota_exceeded"
    assert raised.value.headers["Retry-After"]


@pytest.mark.asyncio
async def test_spend_budget_is_enforced(database_url, db_session_factory) -> None:
    settings = settings_for(database_url, daily_budget_usd=0.01)
    async with db_session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        call = Call(workspace_id=workspace.id, consent_at=datetime.now(UTC))
        session.add(call)
        await session.flush()
        session.add(
            Report(
                call_id=call.id,
                report={},
                report_status="ok",
                schema_version="1.0",
                pipeline_version="x",
                est_cost_usd=0.02,
            )
        )
    async with db_session_factory() as session:
        with pytest.raises(APIError) as raised:
            await check_budget(session, settings)
    assert raised.value.code == "budget_exceeded"
