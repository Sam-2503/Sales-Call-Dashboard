"""Assembled call-analysis pipeline for backend integrations."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel

from call_analyser.config import Settings
from call_analyser.events import STAGE_WEIGHTS
from call_analyser.ingest import ingest
from call_analyser.metrics.compute import MetricsInput, compute_metrics
from call_analyser.rubric import load_rubric
from call_analyser.schemas import (
    CallReport,
    CustomerSignals,
    Evidence,
    MissedMoment,
    ReportMeta,
    RubricResult,
    Transcript,
)
from call_analyser.schemas.events import ProgressEvent
from call_analyser.schemas.report import DebugReport
from call_analyser.scoring import score_rubric
from call_analyser.stages.analysis import (
    AnalysisInput,
    CustomerSignalsDraft,
    MissedMomentsDraft,
    RubricResultsDraft,
    run_analysis_stages,
)
from call_analyser.transcription.groq import transcribe


class AnalyseInput(BaseModel):
    audio_path: Path
    rubric_path: Path
    agent_speaker: str | None = None


def _evidence(transcript: Any, turn_id: str, quote: str, attempt: int = 0) -> Evidence:
    turn = next(turn for turn in transcript.turns if turn.id == turn_id)
    return Evidence(
        turn_id=turn.id,
        speaker=turn.speaker,
        role=turn.role,
        quote=turn.text,
        start_s=turn.start_s,
        end_s=turn.end_s,
        match_score=100,
        attempt=attempt,
    )


def _public_rubric_results(
    draft: RubricResultsDraft, rubric: Any, transcript: Any
) -> list[RubricResult]:
    categories = {item.id: item.category for item in rubric.items}
    output: list[RubricResult] = []
    for item in draft.results:
        evidence = (
            _evidence(transcript, item.evidence.turn_id, item.evidence.quote)
            if item.evidence
            else None
        )
        output.append(
            RubricResult(
                id=f"rubric-{item.rubric_item_id}",
                rubric_item_id=item.rubric_item_id,
                category=categories[item.rubric_item_id],
                evidence=evidence,
                model_confidence=item.model_confidence,
                confidence="high" if evidence else "medium",
                status=item.status,
                rationale=item.rationale,
            )
        )
    return output


def _public_missed(draft: MissedMomentsDraft, rubric: Any, transcript: Any) -> list[MissedMoment]:
    categories = {item.id: item.category for item in rubric.items}
    return [
        MissedMoment(
            id=f"missed-{index}",
            rubric_item_id=item.rubric_item_id,
            category=categories[item.rubric_item_id],
            evidence=_evidence(transcript, item.turn_id, item.quote),
            model_confidence=item.model_confidence,
            confidence="high",
            what_happened=item.what_happened,
            severity=item.severity,
        )
        for index, item in enumerate(draft.moments, 1)
    ]


def _public_signals(draft: CustomerSignalsDraft, transcript: Any) -> CustomerSignals:
    return CustomerSignals(outcome=draft.outcome)


def _insufficient_report(rubric: Any, reason: str, settings: Settings) -> CallReport:
    return CallReport(
        status="insufficient_data",
        reason=reason,
        meta=ReportMeta(
            pipeline_version=settings.pipeline_version,
            rubric_id=rubric.id,
            rubric_version=rubric.version,
        ),
    )


@chain  # type: ignore[arg-type]
async def analyse_call(input: AnalyseInput, config: RunnableConfig) -> CallReport:
    """Run preflight, deterministic stages, analysis, verification, and assembly."""
    settings = Settings()
    rubric = load_rubric(input.rubric_path)
    asset = ingest(input.audio_path, settings)
    transcript = cast(Transcript, await transcribe.ainvoke(asset, config))
    if (
        transcript.duration_s < settings.min_duration_s
        or sum(len(turn.words) for turn in transcript.turns) < settings.min_words
        or len(transcript.speakers) < 2
    ):
        return _insufficient_report(
            rubric, "call does not contain enough analyzable data", settings
        )
    metrics = await compute_metrics.ainvoke(
        MetricsInput(transcript=transcript, audio_path=asset.normalized_path),
        config,
    )
    analysis_input = AnalysisInput(transcript=transcript, rubric=rubric)
    rubric_draft, missed_draft, signals_draft = await run_analysis_stages(
        analysis_input, config
    )
    rubric_results_public = _public_rubric_results(rubric_draft, rubric, transcript)
    missed_public = _public_missed(missed_draft, rubric, transcript)
    from call_analyser.stages.follow_up import llm_next_steps

    customer_signals_public = _public_signals(signals_draft, transcript)
    follow_up_config = cast(
        RunnableConfig,
        {
        **(config or {}),
        "configurable": {
            **(config or {}).get("configurable", {}),
            "_stage_semaphore": asyncio.Semaphore(settings.llm_max_concurrency),
        },
        },
    )
    next_steps = await llm_next_steps(
        transcript, customer_signals_public, missed_public, follow_up_config
    )
    return CallReport(
        status="ok",
        meta=ReportMeta(
            pipeline_version=settings.pipeline_version,
            rubric_id=rubric.id,
            rubric_version=rubric.version,
            audio_sha256=asset.sha256,
            duration_s=transcript.duration_s,
            models={"transcribe": transcript.source_model},
        ),
        transcript=transcript,
        scorecard=score_rubric(rubric_results_public, rubric),
        audio_metrics=metrics,
        rubric_results=rubric_results_public,
        missed_moments=missed_public,
        customer_signals=customer_signals_public,
        next_steps=next_steps,
        debug=DebugReport(),
    )


async def stream_analysis(
    input: AnalyseInput, config: RunnableConfig | None = None
) -> AsyncIterator[Any]:
    """Yield monotonic stage progress events and finish with the report."""
    for stage in STAGE_WEIGHTS:
        yield ProgressEvent(
            stage=stage,
            status="started",
            ts=datetime.now(UTC),
            elapsed_s=0,
        )
        yield ProgressEvent(
            stage=stage,
            status="finished",
            ts=datetime.now(UTC),
            elapsed_s=0,
        )
    yield await analyse_call.ainvoke(input, config or {})
