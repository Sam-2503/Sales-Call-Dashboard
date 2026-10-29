import pytest
from sqlalchemy import func, select

from analyser_api.db.models import (
    Agent,
    Call,
    CallCategoryScore,
    CallItemResult,
    Feedback,
    Job,
    JobEvent,
    Report,
    ReportFinding,
    StageCache,
    Workspace,
)
from analyser_api.jobs.queue import JobQueue
from analyser_api.jobs.stage_store import PostgresStageStore

pytestmark = pytest.mark.db


@pytest.mark.asyncio
async def test_cascade_deletes_every_workspace_child(db_session_factory) -> None:
    async with db_session_factory() as session, session.begin():
        workspace = Workspace(label="cascade")
        session.add(workspace)
        await session.flush()
        agent = Agent(workspace_id=workspace.id, name="Me")
        session.add(agent)
        await session.flush()
        call = Call(
            workspace_id=workspace.id,
            agent_id=agent.id,
            consent_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )
        session.add(call)
        await session.flush()
        job = Job(call_id=call.id)
        session.add(job)
        await session.flush()
        session.add(JobEvent(job_id=job.id, stage="ingest", status="finished", percent=5))
        session.add(
            Report(
                call_id=call.id,
                report={},
                report_status="ok",
                schema_version="1.0",
                pipeline_version="x",
            )
        )
        session.add(CallCategoryScore(call_id=call.id, category_id="opening", score=80))
        session.add(
            CallItemResult(call_id=call.id, rubric_item_id="a", category_id="opening", status="met")
        )
        session.add(ReportFinding(call_id=call.id, finding_id="f", kind="missed_moment"))
        session.add(
            Feedback(
                call_id=call.id,
                workspace_id=workspace.id,
                finding_id="f",
                kind="missed_moment",
                verdict="helpful",
            )
        )
        session.add(StageCache(call_id=call.id, key="k", stage="transcribe", value={"x": 1}))
    async with db_session_factory() as session, session.begin():
        await session.delete(await session.get(Workspace, workspace.id))
    async with db_session_factory() as session:
        for model in (
            Agent,
            Call,
            Job,
            JobEvent,
            Report,
            CallCategoryScore,
            CallItemResult,
            ReportFinding,
            Feedback,
            StageCache,
        ):
            assert await session.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.asyncio
async def test_two_claimers_never_get_the_same_job(db_session_factory) -> None:
    from datetime import UTC, datetime

    from analyser_api.db.models import Call, Workspace

    async with db_session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        call = Call(workspace_id=workspace.id, consent_at=datetime.now(UTC))
        session.add(call)
        await session.flush()
        session.add(Job(call_id=call.id))
    first = JobQueue(db_session_factory, worker_id="a", max_attempts=2)
    second = JobQueue(db_session_factory, worker_id="b", max_attempts=2)
    claimed = await __import__("asyncio").gather(first.claim_next(), second.claim_next())
    assert sum(item is not None for item in claimed) == 1


@pytest.mark.asyncio
async def test_stage_store_round_trip_is_call_scoped(db_session_factory) -> None:
    from datetime import UTC, datetime

    from analyser_api.db.models import Call, Workspace

    async with db_session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        call = Call(workspace_id=workspace.id, consent_at=datetime.now(UTC))
        session.add(call)
        await session.flush()
    store = PostgresStageStore(db_session_factory, call.id)
    await store.put("transcribe", {"text": "x"})
    assert await store.get("transcribe") == {"text": "x"}
    assert await store.get("missing") is None
