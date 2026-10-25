"""Speaker-role assignment after transcription."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from call_analyser.config import Settings
from call_analyser.errors import TranscriptionError
from call_analyser.llm import get_chat_model
from call_analyser.schemas import Transcript


class RoleAssignment(BaseModel):
    agent_speaker: str
    customer_speaker: str


def apply_roles(
    transcript: Transcript, assignment: RoleAssignment, agent_speaker: str | None = None
) -> Transcript:
    """Validate a role decision and assign unselected speakers to ``other``."""
    speakers = set(transcript.speakers)
    agent = agent_speaker or assignment.agent_speaker
    customer = assignment.customer_speaker
    if agent not in speakers or customer not in speakers or agent == customer:
        raise TranscriptionError("role assignment must identify distinct known speakers")
    if len(speakers) == 2 and {agent, customer} != speakers:
        raise TranscriptionError("two-speaker calls require one agent and one customer")
    roles: dict[str, Literal["agent", "customer", "other"]] = {
        speaker: "other" for speaker in speakers
    }
    roles[agent], roles[customer] = "agent", "customer"
    turns = [turn.model_copy(update={"role": roles[turn.speaker]}) for turn in transcript.turns]
    return transcript.model_copy(update={"turns": turns, "speaker_roles": roles})


async def assign_roles(
    transcript: Transcript,
    config: RunnableConfig,
    agent_speaker: str | None = None,
    settings: Settings | None = None,
) -> Transcript:
    """Use a short initial probe for a stable agent/customer assignment."""
    active = settings or Settings()
    if agent_speaker is not None:
        remaining = [speaker for speaker in transcript.speakers if speaker != agent_speaker]
        if not remaining:
            raise TranscriptionError("agent speaker override leaves no customer speaker")
        return apply_roles(
            transcript,
            RoleAssignment(agent_speaker=agent_speaker, customer_speaker=remaining[0]),
            agent_speaker,
        )
    probe = "\n".join(
        f"{turn.speaker}: {turn.text}"
        for turn in transcript.turns
        if turn.start_s < active.role_probe_seconds
    )
    model = get_chat_model("fast", active).with_structured_output(RoleAssignment)
    result = await model.ainvoke(
        [
            HumanMessage(
                content=f"Identify the sales agent and customer. Transcript data follows:\n{probe}"
            )
        ],
        config=config,
    )
    if not isinstance(result, RoleAssignment):
        raise TranscriptionError("role model returned invalid structured output")
    return apply_roles(transcript, result)
