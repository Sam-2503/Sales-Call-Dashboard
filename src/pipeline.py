"""Assembled call-analysis pipeline and fake-mode orchestration."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel

from config import Settings
from events import STAGE_WEIGHTS
from ingest import ingest
from metrics.compute import MetricsInput, compute_metrics
from playbook import PlaybookIndex, load_playbook_spec
from rubric import load_rubric
from schemas import (
    CallReport,
    CustomerSignals,
    Evidence,
    MissedMoment,
    ReportMeta,
    RubricResult,
)
from schemas.events import ProgressEvent
from schemas.report import DebugReport
from scoring import score_rubric
from stages.analysis import (
    AnalysisInput,
    CustomerSignalsDraft,
    DraftEvidence,
    DraftMissedMoment,
    DraftRubricResult,
    MissedMomentsDraft,
    RubricResultsDraft,
    customer_signals,
    missed_moments,
    rubric_results,
)
from stages.grounding import ground_findings
from transcription.fake import FakeTranscriber
from transcription.gemini import GeminiTranscriber


class AnalyseInput(BaseModel):
    audio_path: Path
    rubric_path: Path
    playbook_path: Path | None = None
    agent_speaker: str | None = None
    grounding: bool = True
    fake: bool = False


def _fake_transcript() -> Any:
    return FakeTranscriber().fixture


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


def _fake_drafts(transcript: Any, rubric: Any) -> tuple[
    RubricResultsDraft, MissedMomentsDraft, CustomerSignalsDraft
]:
    results = [
        DraftRubricResult(
            rubric_item_id=item.id,
            status="not_applicable",
            rationale="Synthetic fake-mode judgement.",
            model_confidence=1,
        )
        for item in rubric.items
    ]
    first = rubric.items[0]
    results[0] = DraftRubricResult(
        rubric_item_id=first.id,
        status="met",
        rationale="The synthetic call provides supporting evidence.",
        evidence=DraftEvidence(turn_id=transcript.turns[0].id, quote=transcript.turns[0].text),
        model_confidence=1,
    )
    missed = DraftMissedMoment(
        rubric_item_id=rubric.items[1].id,
        turn_id=transcript.turns[1].id,
        quote=transcript.turns[1].text,
        what_happened="The representative did not explore the stated concern.",
        severity="medium",
        model_confidence=0.9,
    )
    return (
        RubricResultsDraft(results=results),
        MissedMomentsDraft(moments=[missed]),
        CustomerSignalsDraft(outcome="advanced"),
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
    index = None
    if input.grounding and settings.playbook_grounding == "on":
        if input.playbook_path is None:
            raise ValueError("playbook_path is required when grounding is enabled")
        index = PlaybookIndex.open(load_playbook_spec(input.playbook_path), settings)
    asset = ingest(input.audio_path, settings)
    transcriber = (
        FakeTranscriber(_fake_transcript())
        if input.fake or settings.fake_mode
        else GeminiTranscriber(settings)
    )
    transcript = await transcriber.transcribe(asset)
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
    if input.fake or settings.fake_mode:
        rubric_draft, missed_draft, signals_draft = _fake_drafts(transcript, rubric)
    else:
        rubric_draft, missed_draft, signals_draft = await asyncio.gather(
            rubric_results.ainvoke(analysis_input, config),
            missed_moments.ainvoke(analysis_input, config),
            customer_signals.ainvoke(analysis_input, config),
        )
    rubric_results_public = _public_rubric_results(rubric_draft, rubric, transcript)
    missed_public = _public_missed(missed_draft, rubric, transcript)
    if index is not None and missed_public and not (input.fake or settings.fake_mode):
        from playbook.retriever import PlaybookRetriever

        missed_public = await ground_findings.ainvoke(
            missed_public,
            {**config, "configurable": {
                **config.get("configurable", {}),
                "retriever": PlaybookRetriever(index=index),
            }},
        )
    from stages.follow_up import deterministic_next_steps

    customer_signals_public = _public_signals(signals_draft, transcript)
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
        next_steps=deterministic_next_steps(customer_signals_public),
        debug=DebugReport(
            retrieved_passage_ids={
                finding.id: [ref.passage_id for ref in finding.playbook_refs]
                for finding in missed_public
            }
        ),
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
