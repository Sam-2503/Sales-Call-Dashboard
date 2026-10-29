"""PostgreSQL-backed job queue using FOR UPDATE SKIP LOCKED."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.db.models import Call, Job, JobEvent, Report

CLAIM_SQL = text(
    """
    UPDATE jobs
       SET status = 'running',
           locked_by = :worker,
           locked_at = now(),
           heartbeat_at = now(),
           started_at = coalesce(started_at, now()),
           attempts = attempts + 1,
           error_code = NULL,
           error_message = NULL,
           current_stage = 'queued'
     WHERE id = (
           SELECT id
             FROM jobs
            WHERE status = 'queued'
              AND available_at <= now()
            ORDER BY available_at ASC, created_at ASC
              FOR UPDATE SKIP LOCKED
            LIMIT 1
     )
    RETURNING id
    """
)


class JobQueue:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        worker_id: str,
        stale_after_s: float = 60.0,
        max_attempts: int = 2,
    ) -> None:
        self._session_factory = session_factory
        self.worker_id = worker_id
        self._stale_after_s = stale_after_s
        self._max_attempts = max_attempts

    async def enqueue(self, call_id: UUID, *, options: dict[str, Any] | None = None) -> Job:
        async with self._session_factory() as session, session.begin():
            job = Job(
                call_id=call_id,
                status="queued",
                max_attempts=self._max_attempts,
                options=options or {},
                available_at=datetime.now(UTC),
            )
            session.add(job)
            await session.flush()
            return job

    async def claim_next(self) -> Job | None:
        async with self._session_factory() as session, session.begin():
            job_id = (
                await session.execute(CLAIM_SQL, {"worker": self.worker_id})
            ).scalar_one_or_none()
            if job_id is None:
                return None
            return await session.get(Job, job_id)

    async def heartbeat(self, job_id: UUID) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                update(Job)
                .where(Job.id == job_id, Job.status == "running")
                .values(heartbeat_at=datetime.now(UTC))
            )

    async def succeed(self, job_id: UUID) -> None:
        async with self._session_factory() as session, session.begin():
            job = await session.get(Job, job_id)
            if job is None:
                return
            now = datetime.now(UTC)
            job.status = "succeeded"
            job.percent = 100
            job.current_stage = "done"
            job.finished_at = now
            job.locked_by = None
            job.locked_at = None
            job.heartbeat_at = now
            call = await session.get(Call, job.call_id)
            if call is not None:
                call.status = "completed"
                call.completed_at = now

    async def fail(
        self,
        job_id: UUID,
        *,
        code: str,
        message: str,
        retryable: bool,
    ) -> bool:
        """Fail a job. Returns True when the job was requeued for a retry."""
        async with self._session_factory() as session, session.begin():
            job = await session.get(Job, job_id)
            if job is None:
                return False
            now = datetime.now(UTC)
            retry = retryable and job.attempts < job.max_attempts
            job.error_code = code
            job.error_message = message
            job.finished_at = None if retry else now
            job.locked_by = None
            job.locked_at = None
            job.heartbeat_at = now
            if retry:
                delay_s = min(300, 15 * (2 ** max(0, job.attempts - 1)))
                job.status = "queued"
                job.available_at = now + timedelta(seconds=delay_s)
                job.current_stage = "queued"
            else:
                job.status = "failed"
                job.current_stage = "failed"
            session.add(
                JobEvent(
                    job_id=job.id,
                    stage=job.current_stage or "analysis",
                    status="retrying" if retry else "failed",
                    percent=job.percent,
                    detail={"error_code": code},
                )
            )
            call = await session.get(Call, job.call_id)
            if call is not None:
                if retry:
                    call.status = "queued"
                else:
                    has_report = await session.scalar(
                        select(func.count())
                        .select_from(Report)
                        .where(Report.call_id == job.call_id)
                    )
                    call.status = "completed" if has_report else "failed"
            return retry

    async def release(self, job_id: UUID) -> None:
        async with self._session_factory() as session, session.begin():
            job = await session.get(Job, job_id)
            if job is None or job.status != "running":
                return
            job.status = "queued"
            job.available_at = datetime.now(UTC)
            job.locked_by = None
            job.locked_at = None
            job.heartbeat_at = None
            job.current_stage = "queued"
            call = await session.get(Call, job.call_id)
            if call is not None:
                call.status = "queued"

    async def reclaim_stale(self) -> int:
        async with self._session_factory() as session, session.begin():
            cutoff = datetime.now(UTC) - timedelta(seconds=self._stale_after_s)
            stale = await session.scalars(
                select(Job).where(
                    Job.status == "running",
                    or_(
                        and_(Job.heartbeat_at.is_(None), Job.locked_at <= cutoff),
                        and_(Job.heartbeat_at.is_not(None), Job.heartbeat_at <= cutoff),
                    ),
                )
            )
            count = 0
            for job in stale:
                count += 1
                job.locked_by = None
                job.locked_at = None
                job.heartbeat_at = None
                call = await session.get(Call, job.call_id)
                if job.attempts >= job.max_attempts:
                    job.status = "failed"
                    job.error_code = "worker_lost"
                    job.error_message = "worker heartbeat expired"
                    job.current_stage = "failed"
                    job.finished_at = datetime.now(UTC)
                    if call is not None:
                        reported = await session.scalar(
                            select(func.count())
                            .select_from(Report)
                            .where(Report.call_id == job.call_id)
                        )
                        call.status = "completed" if reported else "failed"
                else:
                    job.status = "queued"
                    job.available_at = datetime.now(UTC)
                    job.current_stage = "queued"
                    if call is not None:
                        call.status = "queued"
            return count

    async def position(self, job_id: UUID) -> int | None:
        async with self._session_factory() as session:
            job = await session.get(Job, job_id)
            if job is None or job.status != "queued":
                return None
            value = await session.scalar(
                select(func.count())
                .select_from(Job)
                .where(
                    Job.status == "queued",
                    or_(
                        Job.available_at < job.available_at,
                        (Job.available_at == job.available_at) & (Job.created_at < job.created_at),
                    ),
                )
            )
            return int(value or 0)

    async def record_event(
        self,
        job_id: UUID,
        *,
        stage: str,
        status: str,
        percent: int,
        elapsed_s: float | None = None,
        detail: dict[str, Any] | None = None,
    ) -> int:
        async with self._session_factory() as session, session.begin():
            job = await session.get(Job, job_id)
            if job is None:
                return percent
            monotonic = max(job.percent, min(100, percent))
            job.percent = monotonic
            job.current_stage = stage
            job.heartbeat_at = datetime.now(UTC)
            event = JobEvent(
                job_id=job.id,
                stage=stage,
                status=status,
                percent=monotonic,
                elapsed_s=elapsed_s,
                detail=detail or {},
            )
            session.add(event)
            await session.flush()
            return monotonic
