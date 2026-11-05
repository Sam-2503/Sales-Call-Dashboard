"""Validated next-step and coaching contracts."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from call_analyser.config import Settings
from call_analyser.llm import ainvoke_structured, get_chat_model
from call_analyser.prompts.registry import PromptRegistry
from call_analyser.schemas.findings import CustomerSignals, MissedMoment
from call_analyser.schemas.report import Coaching, CoachingItem, NextSteps
from call_analyser.schemas.transcript import Transcript


class FollowUpDraft(BaseModel):
    follow_up_message: str = Field(min_length=1, max_length=1200)
    recommended_actions: list[str] = Field(default_factory=list, max_length=5)


async def llm_next_steps(
    transcript: Transcript,
    signals: CustomerSignals | None,
    findings: list[MissedMoment],
    config: RunnableConfig,
) -> NextSteps:
    """Write a call-specific follow-up email from verified report evidence."""
    prompt = PromptRegistry().load("follow_up", "v1").render(
        transcript="\n".join(
            f"{turn.id} {turn.role.upper()}: {turn.text}" for turn in transcript.turns
        ),
        signals=signals.model_dump_json() if signals else "None",
        findings=json.dumps([finding.model_dump(mode="json") for finding in findings]),
    )
    settings = Settings()
    model = config.get("configurable", {}).get("analysis_model") or get_chat_model(
        "analysis", settings
    )
    semaphore = config.get("configurable", {}).get("_stage_semaphore")

    async def invoke() -> BaseModel:
        return await ainvoke_structured(
            model, FollowUpDraft, [HumanMessage(content=prompt)], config
        )

    draft = await invoke() if semaphore is None else await _invoke_with_semaphore(invoke, semaphore)
    return NextSteps.model_validate(draft.model_dump())


async def _invoke_with_semaphore(
    invoke: Callable[[], Awaitable[BaseModel]], semaphore: asyncio.Semaphore
) -> BaseModel:
    async with semaphore:
        return await invoke()


def validate_coaching(coaching: Coaching, findings: list[MissedMoment]) -> Coaching:
    """Reject coaching references that do not point at existing findings."""
    known = {finding.id for finding in findings}
    unknown = {item.finding_id for item in coaching.top_fixes} - known
    if unknown:
        raise ValueError(f"coaching references unknown finding ids: {sorted(unknown)}")
    return coaching


def deterministic_next_steps(
    signals: CustomerSignals | None,
    findings: list[MissedMoment] | None = None,
) -> NextSteps:
    """Create a safe, evidence-backed follow-up message and actions."""
    unresolved = [
        objection.text
        for objection in (signals.objections if signals else [])
        if not objection.resolved
    ]
    commitments = signals.commitments if signals else []
    actions = [
        f"{commitment.party}: {commitment.what} by {commitment.due}"
        for commitment in commitments
    ]

    lines = ["Hi, thanks for your time today."]
    if commitments:
        lines.append(
            "As discussed, I’ll follow up on "
            + "; ".join(commitment.what for commitment in commitments)
            + "."
        )
    elif unresolved:
        lines.append(
            "I’m following up on your question about "
            + "; ".join(unresolved[:2])
            + ". I’d be happy to address any remaining concerns."
        )
    elif signals and signals.unanswered_questions:
        lines.append(
            "I’m following up on the question we left open: "
            + signals.unanswered_questions[0].quote
            + ". I’ll make sure you have a clear answer."
        )
    elif findings:
        finding = findings[0]
        detail = finding.better_alternative or finding.what_happened
        lines.append(
            "I’m following up on "
            + detail.rstrip(".")
            + ". I’d be happy to clarify this and answer any remaining questions."
        )
    else:
        lines.append(
            "I’m following up on our conversation. Please let me know if you have "
            "any questions or would like to continue the discussion."
        )
    lines.extend(["Would a short follow-up conversation be useful?", "", "Best,"])
    if signals is None:
        actions = []
    return NextSteps(
        follow_up_message="\n".join(lines),
        recommended_actions=actions,
    )


__all__ = [
    "Coaching",
    "CoachingItem",
    "FollowUpDraft",
    "NextSteps",
    "deterministic_next_steps",
    "llm_next_steps",
    "validate_coaching",
]
