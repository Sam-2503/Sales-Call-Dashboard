from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import CallReport, Evidence, PlaybookRef, RubricResult, Transcript


def evidence() -> Evidence:
    return Evidence(
        turn_id="T001",
        speaker="Rep",
        role="agent",
        quote="hello",
        start_s=0,
        end_s=1,
        match_score=100,
        attempt=0,
    )


def test_transcript_round_trips_synthetic_fixture() -> None:
    source = Path("fixtures/synthetic_short_transcript.json")
    transcript = Transcript.model_validate_json(source.read_text())
    assert Transcript.model_validate_json(transcript.model_dump_json()) == transcript


def test_required_evidence_and_times_are_validated() -> None:
    with pytest.raises(ValidationError, match="require evidence"):
        RubricResult(
            id="r",
            rubric_item_id="x",
            category="discovery",
            model_confidence=1,
            status="met",
            rationale="ok",
        )
    with pytest.raises(ValidationError, match="start_s"):
        Evidence(
            turn_id="T001",
            speaker="Rep",
            role="agent",
            quote="x",
            start_s=2,
            end_s=1,
            match_score=1,
            attempt=0,
        )


def test_excerpt_and_coaching_references_are_validated() -> None:
    with pytest.raises(ValidationError, match="MAX_EXCERPT_WORDS"):
        PlaybookRef(
            passage_id="p",
            book_title="b",
            chapter="c",
            page_start=1,
            page_end=1,
            excerpt="word " * 26,
        )
    with pytest.raises(ValidationError, match="unknown finding"):
        CallReport.model_validate(
            {
                "status": "ok",
                "meta": {"pipeline_version": "x"},
                "coaching": {
                    "top_fixes": [
                        {"finding_id": "missing", "explanation": "x", "practice_drill": "y"}
                    ]
                },
            }
        )
