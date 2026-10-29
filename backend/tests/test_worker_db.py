from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from analyser_api.config import Settings
from analyser_api.db.models import Call, Job, Report, Workspace
from analyser_api.jobs.queue import JobQueue
from analyser_api.jobs.runner import ScriptedRunner
from analyser_api.jobs.worker import JobWorker
from analyser_api.storage.local import LocalStorage

pytestmark = pytest.mark.db


def settings_for(database_url: str, storage_dir: Path) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="x" * 32,
        worker_enabled=False,
        worker_concurrency=1,
        worker_poll_interval_s=0.05,
        job_heartbeat_s=1,
        daily_budget_usd=10,
        storage_dir=storage_dir,
    )


async def _call_with_audio(session_factory, storage: LocalStorage) -> tuple[object, object]:
    key = f"{uuid4()}/call/original.wav"
    source = storage.root / key
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"not real audio, but the scripted runner ignores it")
    async with session_factory() as session, session.begin():
        workspace = Workspace()
        session.add(workspace)
        await session.flush()
        call = Call(
            workspace_id=workspace.id,
            consent_at=datetime.now(UTC),
            audio_key=key,
            status="queued",
        )
        session.add(call)
        await session.flush()
        job = Job(call_id=call.id, status="queued", max_attempts=2)
        session.add(job)
        await session.flush()
        return call, job


@pytest.mark.asyncio
async def test_worker_persists_report_and_succeeds_job(
    database_url, db_session_factory, tmp_path: Path
) -> None:
    storage = LocalStorage(tmp_path / "audio")
    settings = settings_for(database_url, storage.root)
    call, job = await _call_with_audio(db_session_factory, storage)
    worker = JobWorker(
        db_session_factory,
        ScriptedRunner(),
        storage,
        settings,
        worker_id="test-worker",
    )
    await worker.start()
    try:
        for _ in range(100):
            async with db_session_factory() as session:
                refreshed = await session.get(Call, call.id)
                if refreshed is not None and refreshed.status == "completed":
                    break
            await asyncio.sleep(0.05)
    finally:
        await worker.stop()
    async with db_session_factory() as session:
        refreshed_job = await session.get(Job, job.id)
        report = await session.get(Report, call.id)
    assert refreshed_job is not None
    assert refreshed_job.status == "succeeded"
    assert report is not None
    assert report.report_status == "insufficient_data"


@pytest.mark.asyncio
async def test_retry_backoff_and_attempt_limit(database_url, db_session_factory) -> None:
    workspace = Workspace()
    async with db_session_factory() as session, session.begin():
        session.add(workspace)
        await session.flush()
        call = Call(workspace_id=workspace.id, consent_at=datetime.now(UTC))
        session.add(call)
        await session.flush()
        job = Job(call_id=call.id, status="queued", max_attempts=2)
        session.add(job)
    queue = JobQueue(db_session_factory, worker_id="retry", max_attempts=2)
    claimed = await queue.claim_next()
    assert claimed is not None
    await queue.fail(claimed.id, code="transcription_failed", message="temporary", retryable=True)
    async with db_session_factory() as session:
        row = await session.get(Job, claimed.id)
    assert row is not None and row.status == "queued"
    assert row.available_at > datetime.now(UTC) + timedelta(seconds=10)
    async with db_session_factory() as session, session.begin():
        row = await session.get(Job, claimed.id)
        assert row is not None
        row.available_at = datetime.now(UTC) - timedelta(seconds=1)
    second = await queue.claim_next()
    assert second is not None
    await queue.fail(second.id, code="transcription_failed", message="temporary", retryable=True)
    async with db_session_factory() as session:
        row = await session.get(Job, claimed.id)
    assert row is not None and row.status == "failed"


@pytest.mark.asyncio
async def test_stale_worker_is_reclaimed_then_fails_after_attempts(
    database_url, db_session_factory
) -> None:
    workspace = Workspace()
    async with db_session_factory() as session, session.begin():
        session.add(workspace)
        await session.flush()
        call = Call(workspace_id=workspace.id, consent_at=datetime.now(UTC))
        session.add(call)
        await session.flush()
        job = Job(call_id=call.id, status="queued", max_attempts=2)
        session.add(job)
    queue = JobQueue(db_session_factory, worker_id="stale", max_attempts=2)
    first = await queue.claim_next()
    assert first is not None
    async with db_session_factory() as session, session.begin():
        row = await session.get(Job, first.id)
        assert row is not None
        row.heartbeat_at = datetime.now(UTC) - timedelta(minutes=2)
        row.locked_at = row.heartbeat_at
    assert await queue.reclaim_stale() == 1
    second = await queue.claim_next()
    assert second is not None
    async with db_session_factory() as session, session.begin():
        row = await session.get(Job, second.id)
        assert row is not None
        row.heartbeat_at = datetime.now(UTC) - timedelta(minutes=2)
        row.locked_at = row.heartbeat_at
    assert await queue.reclaim_stale() == 1
    async with db_session_factory() as session:
        row = await session.get(Job, second.id)
    assert row is not None
    assert row.status == "failed"
    assert row.error_code == "worker_lost"
