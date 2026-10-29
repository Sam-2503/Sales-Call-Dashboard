"""Durable worker loop and thread-backed worker for the FastAPI process."""

from __future__ import annotations

import asyncio
import tempfile
import threading
from collections.abc import Awaitable, Callable
from contextlib import suppress
from pathlib import Path
from uuid import UUID

from call_analyser.schemas.events import ProgressEvent
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.config import Settings
from analyser_api.db.engine import create_engine
from analyser_api.db.models import Call, Job
from analyser_api.errors import APIError
from analyser_api.jobs.events import event_detail, percent_for
from analyser_api.jobs.queue import JobQueue
from analyser_api.jobs.runner import PackageRunner, PipelineRunner, map_exception
from analyser_api.logging import set_job_id
from analyser_api.services.quotas import check_budget
from analyser_api.services.reports import persist_report
from analyser_api.storage.base import AudioStorage
from analyser_api.storage.factory import create_storage

ReadyCheck = Callable[[], Awaitable[bool]]


class JobWorker:
    """Run up to WORKER_CONCURRENCY jobs in the current event loop."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        runner: PipelineRunner,
        storage: AudioStorage,
        settings: Settings,
        *,
        worker_id: str | None = None,
        ready_check: ReadyCheck | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._runner = runner
        self._storage = storage
        self._settings = settings
        self._worker_id = worker_id or f"worker-{id(self)}"
        self._ready_check = ready_check
        self._queue = JobQueue(
            session_factory,
            worker_id=self._worker_id,
            stale_after_s=settings.job_stale_s,
            max_attempts=settings.job_max_attempts,
        )
        self._stop = asyncio.Event()
        self._tasks: list[asyncio.Task[None]] = []
        self._running: set[UUID] = set()

    async def start(self) -> None:
        if self._tasks:
            return
        self._stop.clear()
        await self._queue.reclaim_stale()
        self._tasks = [
            asyncio.create_task(self._loop(), name=f"analyser-worker-{index}")
            for index in range(self._settings.worker_concurrency)
        ]

    async def stop(self) -> None:
        self._stop.set()
        if not self._tasks:
            return
        done, pending = await asyncio.wait(self._tasks, timeout=self._settings.shutdown_grace_s)
        for task in pending:
            task.cancel()
        for task in pending:
            with suppress(asyncio.CancelledError):
                await task
        for task in done:
            with suppress(asyncio.CancelledError):
                await task
        self._tasks = []

    async def _loop(self) -> None:
        while not self._stop.is_set():
            if self._ready_check is not None and not await self._ready_check():
                await asyncio.sleep(self._settings.worker_poll_interval_s)
                continue
            job = await self._queue.claim_next()
            if job is None:
                await asyncio.sleep(self._settings.worker_poll_interval_s)
                continue
            self._running.add(job.id)
            try:
                await self._run_job(job)
            finally:
                self._running.discard(job.id)

    async def _run_job(self, job: Job) -> None:
        job_id = job.id
        set_job_id(str(job_id))
        heartbeat = asyncio.create_task(self._heartbeat(job_id))
        try:
            async with self._session_factory() as session:
                call = await session.get(Call, job.call_id)
                await check_budget(session, self._settings)
            if call is None or not call.audio_key:
                await self._queue.fail(
                    job_id,
                    code="invalid_audio",
                    message="The audio could not be found.",
                    retryable=False,
                )
                return
            with tempfile.TemporaryDirectory(prefix="analyser-job-") as directory:
                path = Path(directory) / f"audio{Path(call.audio_key).suffix}"
                await self._materialize(call.audio_key, path)
                percent = 0

                async def on_event(event: ProgressEvent) -> None:
                    nonlocal percent
                    percent = percent_for(event.stage, event.status, percent)
                    await self._queue.record_event(
                        job_id,
                        stage=event.stage,
                        status=event.status,
                        percent=percent,
                        elapsed_s=event.elapsed_s,
                        detail=event_detail(event),
                    )

                report = await self._runner.run(job, path, on_event)
                await persist_report(self._session_factory, job.call_id, report)
                await self._queue.succeed(job_id)
        except asyncio.CancelledError:
            await self._queue.release(job_id)
            raise
        except APIError as exc:
            await self._queue.fail(
                job_id,
                code=exc.code,
                message=exc.message,
                retryable=False,
            )
        except Exception as exc:
            code, message, retryable = map_exception(exc)
            await self._queue.fail(
                job_id,
                code=code,
                message=message,
                retryable=retryable,
            )
        finally:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat
            set_job_id(None)

    async def _materialize(self, key: str, path: Path) -> None:
        size = await self._storage.size(key)
        with path.open("wb") as stream:
            for start in range(0, size, 1024 * 1024):
                end = min(start + 1024 * 1024 - 1, size - 1)
                chunk = await self._storage.open_range(key, start, end)
                await asyncio.to_thread(stream.write, chunk)

    async def _heartbeat(self, job_id: UUID) -> None:
        while True:
            await asyncio.sleep(self._settings.job_heartbeat_s)
            await self._queue.heartbeat(job_id)


class ThreadedWorker:
    """Run the worker in a dedicated thread with its own loop and engine."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._thread_main, name="analyser-worker")
        self._thread.daemon = True

    async def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    async def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            await asyncio.to_thread(self._thread.join, self._settings.shutdown_grace_s + 5)

    def _thread_main(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        engine = create_engine(self._settings)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        storage = create_storage(self._settings)
        worker = JobWorker(
            session_factory,
            PackageRunner(self._settings, session_factory),
            storage,
            self._settings,
            worker_id=f"thread-{self._thread.ident}",
        )
        await worker.start()
        try:
            while not self._stop.is_set():
                await asyncio.sleep(0.2)
        finally:
            await worker.stop()
            await engine.dispose()
