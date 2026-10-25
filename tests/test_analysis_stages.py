from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from call_analyser.rubric import load_rubric
from call_analyser.schemas import Transcript
from call_analyser.stages import AnalysisInput, customer_signals, missed_moments, rubric_results
from call_analyser.stages.analysis import (
    CustomerSignalsDraft,
    DraftRubricResult,
    MissedMomentsDraft,
    RubricResultsDraft,
    render_transcript,
)


class FakeStructuredModel:
    def __init__(self, responses: dict[type[BaseModel], BaseModel]) -> None:
        self.responses = responses

    def with_structured_output(self, schema: type[BaseModel]) -> "FakeStructuredModel":
        self.schema = schema
        return self

    async def ainvoke(self, _messages: Any, config: Any = None) -> BaseModel:
        return self.responses[self.schema]


def _input() -> AnalysisInput:
    transcript = Transcript.model_validate_json(
        Path("fixtures/synthetic_short_transcript.json").read_text()
    )
    return AnalysisInput(transcript=transcript, rubric=load_rubric("rubrics/sales_v1.yaml"))


def test_transcript_rendering_is_stable_and_includes_turn_ids() -> None:
    rendered = render_transcript(_input().transcript)
    assert rendered.startswith("T001 [")
    assert "AGENT:" in rendered or "OTHER:" in rendered
    assert "\n" in rendered


@pytest.mark.asyncio
async def test_rubric_stage_rejects_unknown_item_and_accepts_scripted_output() -> None:
    input_value = _input()
    valid = RubricResultsDraft(
        results=[
            DraftRubricResult(
                rubric_item_id=item.id,
                status="not_applicable",
                rationale="No supporting evidence in this fixture.",
                model_confidence=0.5,
            )
            for item in input_value.rubric.items
        ]
    )
    model = FakeStructuredModel({RubricResultsDraft: valid})
    result = await rubric_results.ainvoke(
        input_value, {"configurable": {"analysis_model": model}}
    )
    assert len(result.results) == len(input_value.rubric.items)

    invalid = valid.model_copy(
        update={
            "results": [
                valid.results[0].model_copy(update={"rubric_item_id": "missing"})
            ]
        }
    )
    with pytest.raises(ValueError, match="unknown"):
        await rubric_results.ainvoke(
            input_value,
            {
                "configurable": {
                    "analysis_model": FakeStructuredModel({RubricResultsDraft: invalid})
                }
            },
        )


@pytest.mark.asyncio
async def test_missed_moments_validates_turn_ids() -> None:
    invalid = MissedMomentsDraft(
        moments=[
            {
                "rubric_item_id": "opening_permission",
                "turn_id": "T999",
                "quote": "not present",
                "what_happened": "Unsupported",
                "severity": "low",
                "model_confidence": 0.2,
            }
        ]
    )
    with pytest.raises(ValueError, match="unknown"):
        await missed_moments.ainvoke(
            _input(),
            {
                "configurable": {
                    "analysis_model": FakeStructuredModel({MissedMomentsDraft: invalid})
                }
            },
        )


@pytest.mark.asyncio
async def test_customer_signals_scripted_output_is_structured() -> None:
    result = CustomerSignalsDraft(
        sentiment_arc=[
            {"turn_id": "T001", "quote": "hello", "sentiment": "neutral"}
        ],
        outcome="unclear",
    )
    output = await customer_signals.ainvoke(
        _input(),
        {"configurable": {"analysis_model": FakeStructuredModel({CustomerSignalsDraft: result})}},
    )
    assert output.outcome == "unclear"
