"""Stage 7 LLM judgement stages with minimal, unverified outputs."""

from __future__ import annotations

import asyncio
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel, Field

from config import Settings
from llm import ainvoke_structured, get_chat_model
from prompts.registry import PromptRegistry
from rubric import render_rubric
from schemas.rubric import Rubric
from schemas.transcript import Transcript


class DraftEvidence(BaseModel):
    turn_id: str = Field(pattern=r"^T\d{3,}$")
    quote: str = Field(min_length=1, max_length=500)


class DraftRubricResult(BaseModel):
    rubric_item_id: str
    status: Literal["met", "partial", "missed", "not_applicable"]
    rationale: str = Field(min_length=1)
    evidence: DraftEvidence | None = None
    model_confidence: float = Field(ge=0, le=1)


class RubricResultsDraft(BaseModel):
    results: list[DraftRubricResult]


class DraftMissedMoment(BaseModel):
    rubric_item_id: str
    turn_id: str
    quote: str = Field(min_length=1, max_length=500)
    what_happened: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    model_confidence: float = Field(ge=0, le=1)


class MissedMomentsDraft(BaseModel):
    moments: list[DraftMissedMoment] = Field(max_length=12)


class DraftSentimentPoint(BaseModel):
    turn_id: str
    quote: str = Field(min_length=1, max_length=500)
    sentiment: Literal["positive", "neutral", "negative", "mixed"]


class DraftObjection(BaseModel):
    text: str = Field(min_length=1)
    raised_turn_id: str
    raised_quote: str = Field(min_length=1, max_length=500)
    resolved: bool
    resolution_turn_id: str | None = None
    resolution_quote: str | None = Field(default=None, max_length=500)


class DraftCommitment(BaseModel):
    party: str = Field(min_length=1)
    what: str = Field(min_length=1)
    due: str = Field(min_length=1)
    turn_id: str
    quote: str = Field(min_length=1, max_length=500)


class CustomerSignalsDraft(BaseModel):
    sentiment_arc: list[DraftSentimentPoint] = Field(default_factory=list, max_length=12)
    objections: list[DraftObjection] = Field(default_factory=list)
    unanswered_questions: list[DraftEvidence] = Field(default_factory=list)
    buying_signals: list[DraftEvidence] = Field(default_factory=list)
    commitments: list[DraftCommitment] = Field(default_factory=list)
    outcome: Literal["advanced", "stalled", "lost", "unclear"] = "unclear"


class AnalysisInput(BaseModel):
    transcript: Transcript
    rubric: Rubric


def render_transcript(transcript: Transcript) -> str:
    """Render one auditable, timestamped line per turn for model prompts."""
    return "\n".join(
        f"{turn.id} [{turn.start_s // 60:02.0f}:{turn.start_s % 60:04.1f}-"
        f"{turn.end_s // 60:02.0f}:{turn.end_s % 60:04.1f}] "
        f"{turn.role.upper()}: {turn.text}"
        for turn in transcript.turns
    )


def _prompt(stage: str, input_value: AnalysisInput) -> str:
    registry = PromptRegistry()
    return registry.load(stage, "v1").render(
        rubric=render_rubric(input_value.rubric),
        transcript=render_transcript(input_value.transcript),
    )


def _validate_turns_and_items(
    input_value: AnalysisInput,
    turn_ids: list[str],
    item_ids: list[str],
) -> None:
    known_turns = {turn.id for turn in input_value.transcript.turns}
    unknown_turns = set(turn_ids) - known_turns
    unknown_items = set(item_ids) - input_value.rubric.item_ids
    if unknown_turns or unknown_items:
        raise ValueError(
            f"model referenced unknown ids: turns={sorted(unknown_turns)}, "
            f"rubric_items={sorted(unknown_items)}"
        )


async def _invoke(
    stage: str,
    schema: type[BaseModel],
    input_value: AnalysisInput,
    config: RunnableConfig,
    semaphore: asyncio.Semaphore | None = None,
) -> BaseModel:
    active = Settings()
    model = config.get("configurable", {}).get("analysis_model") or get_chat_model(
        "analysis", active
    )
    async def call() -> BaseModel:
        return await ainvoke_structured(
            model, schema, [HumanMessage(content=_prompt(stage, input_value))], config
        )
    active_semaphore = semaphore or config.get("configurable", {}).get("_stage_semaphore")
    if active_semaphore is None:
        return await call()
    async with active_semaphore:
        return await call()


@chain  # type: ignore[arg-type]
async def rubric_results(input: AnalysisInput, config: RunnableConfig) -> RubricResultsDraft:
    """Judge every rubric item against the whole transcript."""
    result = await _invoke("rubric_results", RubricResultsDraft, input, config)
    draft = RubricResultsDraft.model_validate(result)
    _validate_turns_and_items(
        input,
        [item.evidence.turn_id for item in draft.results if item.evidence],
        [item.rubric_item_id for item in draft.results],
    )
    if {item.rubric_item_id for item in draft.results} - input.rubric.item_ids:
        raise ValueError("rubric results contain unknown rubric item ids")
    if {item.rubric_item_id for item in draft.results} != input.rubric.item_ids:
        raise ValueError("rubric results must contain exactly one result for every rubric item")
    return draft


@chain  # type: ignore[arg-type]
async def missed_moments(input: AnalysisInput, config: RunnableConfig) -> MissedMomentsDraft:
    """Locate missed opportunities without generating advice or timestamps."""
    result = await _invoke("missed_moments", MissedMomentsDraft, input, config)
    draft = MissedMomentsDraft.model_validate(result)
    _validate_turns_and_items(
        input,
        [item.turn_id for item in draft.moments],
        [item.rubric_item_id for item in draft.moments],
    )
    return draft


@chain  # type: ignore[arg-type]
async def customer_signals(input: AnalysisInput, config: RunnableConfig) -> CustomerSignalsDraft:
    """Extract customer signals while retaining only model-supplied turn references."""
    result = await _invoke("customer_signals", CustomerSignalsDraft, input, config)
    draft = CustomerSignalsDraft.model_validate(result)
    turn_ids = [
        point.turn_id for point in draft.sentiment_arc
    ] + [item.turn_id for item in draft.unanswered_questions]
    turn_ids += [item.turn_id for item in draft.buying_signals]
    turn_ids += [item.turn_id for item in draft.commitments]
    turn_ids += [item.raised_turn_id for item in draft.objections]
    turn_ids += [
        item.resolution_turn_id for item in draft.objections if item.resolution_turn_id
    ]
    _validate_turns_and_items(input, turn_ids, [])
    return draft


async def run_analysis_stages(
    input_value: AnalysisInput, config: RunnableConfig
) -> tuple[RubricResultsDraft, MissedMomentsDraft, CustomerSignalsDraft]:
    """Run the independent judgement stages concurrently under one semaphore."""
    semaphore = asyncio.Semaphore(Settings().llm_max_concurrency)
    return await asyncio.gather(
        rubric_results.ainvoke(input_value, {**config, "configurable": {
            **config.get("configurable", {}), "_stage_semaphore": semaphore
        }}),
        missed_moments.ainvoke(input_value, {**config, "configurable": {
            **config.get("configurable", {}), "_stage_semaphore": semaphore
        }}),
        customer_signals.ainvoke(input_value, {**config, "configurable": {
            **config.get("configurable", {}), "_stage_semaphore": semaphore
        }}),
    )
