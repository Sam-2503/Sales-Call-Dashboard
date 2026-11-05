"""Pipeline adapters used by the durable worker."""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol, cast

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.config import Settings
from analyser_api.db.models import Job
from analyser_api.jobs.events import STAGE_ORDER
from analyser_api.jobs.stage_store import PostgresStageStore
from call_analyser.errors import (
    AudioValidationError,
    LLMBlockedError,
    StructuredOutputError,
    TranscriptionError,
)
from call_analyser.pipeline import AnalyseInput, stream_analysis
from call_analyser.schemas.events import ProgressEvent
from call_analyser.schemas.report import CallReport, ReportMeta

EventCallback = Callable[[ProgressEvent], Awaitable[None]]


class TransientRunnerError(Exception):
    """A deliberately retryable test failure."""


class PipelineRunner(Protocol):
    async def run(self, job: Job, audio_path: Path, on_event: EventCallback) -> CallReport: ...


class PackageRunner:
    """Run ``call_analyser.stream_analysis`` without touching HTTP concerns."""

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory

    async def run(self, job: Job, audio_path: Path, on_event: EventCallback) -> CallReport:
        if self._settings.package.fake_mode:
            return await ScriptedRunner().run(job, audio_path, on_event)
        agent_speaker = job.options.get("agent_speaker")
        rubric_path = Path(self._settings.rubric_path)
        rubric_temp: Path | None = None
        rubric_yaml = job.options.get("rubric_yaml")
        if isinstance(rubric_yaml, str):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as file:
                file.write(rubric_yaml)
                rubric_temp = Path(file.name)
            rubric_path = rubric_temp
        input_value = AnalyseInput(
            audio_path=audio_path,
            rubric_path=rubric_path,
            agent_speaker=str(agent_speaker) if agent_speaker else None,
        )
        config = {
            "configurable": {
                "stage_store": PostgresStageStore(self._session_factory, job.call_id),
            }
        }
        report: CallReport | None = None
        try:
            async for item in stream_analysis(input_value, cast(RunnableConfig, config)):
                if isinstance(item, ProgressEvent):
                    await on_event(item)
                else:
                    report = item
        finally:
            if rubric_temp is not None:
                rubric_temp.unlink(missing_ok=True)
        if report is None:
            raise RuntimeError("pipeline finished without a report")
        return report


class ScriptedRunner:
    """Deterministic runner for tests and local fake-mode workflows."""

    def __init__(
        self,
        mode: Literal["success", "slow", "transient", "permanent", "crash"] = "success",
        *,
        delay_s: float = 0.0,
    ) -> None:
        self.mode = mode
        self.delay_s = delay_s

    async def run(self, job: Job, audio_path: Path, on_event: EventCallback) -> CallReport:
        del job, audio_path
        for stage in STAGE_ORDER:
            await on_event(
                ProgressEvent(
                    stage=stage,
                    status="started",
                    ts=datetime.now(UTC),
                    elapsed_s=0,
                )
            )
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            await on_event(
                ProgressEvent(
                    stage=stage,
                    status="finished",
                    ts=datetime.now(UTC),
                    elapsed_s=self.delay_s,
                )
            )
        if self.mode == "transient":
            raise TransientRunnerError("temporary provider timeout")
        if self.mode == "permanent":
            raise AudioValidationError("audio is corrupt")
        if self.mode == "crash":
            raise RuntimeError("transcript text must never reach the API")
        return CallReport(
            status="insufficient_data",
            reason="scripted test report",
            meta=ReportMeta(pipeline_version="test"),
        )


def map_exception(exc: BaseException) -> tuple[str, str, bool]:
    """Map a package exception to a stable, non-sensitive job error."""
    if isinstance(exc, AudioValidationError):
        return "invalid_audio", "The audio could not be analysed.", False
    if isinstance(exc, TranscriptionError):
        return "transcription_failed", "Transcription failed.", True
    if isinstance(exc, LLMBlockedError):
        return "content_blocked", "The analysis provider blocked the content.", False
    if isinstance(exc, StructuredOutputError):
        return "analysis_failed", "The analysis response could not be validated.", True
    if isinstance(exc, (TimeoutError, ConnectionError, TransientRunnerError)):
        return "analysis_failed", "The analysis service is temporarily unavailable.", True
    return "internal_error", "The analysis failed.", False
