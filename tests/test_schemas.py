import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from cli import app
from schemas import CallReport, Evidence, PlaybookRef, RubricResult, Transcript
from transcription.fake import FakeTranscriber


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


def test_full_synthetic_fixture_has_forty_turns() -> None:
    transcript = FakeTranscriber().fixture
    assert len(transcript.turns) == 40
    assert transcript.duration_s == 240


def test_hand_built_call_report_fixture_is_valid() -> None:
    report = CallReport.model_validate_json(Path("fixtures/synthetic_call_report.json").read_text())
    assert report.status == "insufficient_data"


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


def test_schema_export_is_deterministic(tmp_path: Path) -> None:
    runner = CliRunner()
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    assert runner.invoke(app, ["export-schema", "--output", str(first)]).exit_code == 0
    assert runner.invoke(app, ["export-schema", "--output", str(second)]).exit_code == 0
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["title"] == "CallReport"
