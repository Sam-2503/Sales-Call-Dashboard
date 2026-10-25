"""Optional structured repair stage for rejected evidence."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel, Field

from llm import ainvoke_structured, get_chat_model


class RepairRequest(BaseModel):
    finding: str
    rejection_reason: str
    context: str


class RepairResponse(BaseModel):
    turn_id: str | None = Field(default=None, pattern=r"^T\d{3,}$")
    quote: str | None = None


class RepairInput(BaseModel):
    request: RepairRequest


@chain  # type: ignore[arg-type]
async def repair_evidence(input: RepairInput, config: RunnableConfig) -> RepairResponse:
    """Ask the analysis model for a corrected turn and quote, or null evidence."""
    model = get_chat_model("fast")
    prompt = (
        "Repair the evidence reference. Return null turn_id and quote if unsupported.\n"
        f"Finding: {input.request.finding}\n"
        f"Rejection: {input.request.rejection_reason}\n"
        f"Transcript context:\n{input.request.context}"
    )
    result = await ainvoke_structured(
        model, RepairResponse, [HumanMessage(content=prompt)], config
    )
    return RepairResponse.model_validate(result)
