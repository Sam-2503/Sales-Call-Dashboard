from pathlib import Path

from call_analyser.config import Settings
from call_analyser.schemas import Transcript
from call_analyser.stages.analysis import DraftEvidence, DraftRubricResult
from call_analyser.verification import confidence_bucket, verify_and_repair, verify_finding


def _transcript() -> Transcript:
    return Transcript.model_validate_json(
        Path("fixtures/synthetic_short_transcript.json").read_text()
    )


def _finding(
    turn_id: str = "T001",
    quote: str = "hello",
    role: str | None = None,
) -> DraftRubricResult:
    values: dict[str, object] = {
        "rubric_item_id": "opening_permission",
        "status": "met",
        "rationale": "supported",
        "evidence": DraftEvidence(turn_id=turn_id, quote=quote),
        "model_confidence": 0.8,
    }
    finding = DraftRubricResult.model_validate(values)
    if role is not None:
        return finding.model_copy(update={"role": role})
    return finding


def test_exact_and_normalized_quotes_verify_with_transcript_timestamps() -> None:
    transcript = _transcript()
    result = verify_finding(_finding(quote="Hi!"), transcript)
    assert result.verified
    assert result.evidence is not None
    turn = transcript.turns[0]
    assert result.evidence.start_s == turn.words[0].start_s
    assert result.evidence.end_s == turn.words[0].end_s
    assert result.evidence.quote == turn.words[0].text


def test_neighbor_search_finds_quote_and_fabricated_quote_fails() -> None:
    transcript = _transcript()
    neighbor = verify_finding(_finding(turn_id="T002", quote="Hi"), transcript)
    assert neighbor.verified
    fabricated = verify_finding(_finding(quote="words that were never spoken"), transcript)
    assert not fabricated.verified


def test_wrong_role_is_rejected() -> None:
    transcript = _transcript()
    finding = _finding(quote="Hi", role="customer")
    result = verify_finding(finding, transcript)
    assert not result.verified


def test_repair_success_and_failure_are_counted() -> None:
    transcript = _transcript()
    settings = Settings(repair_max_attempts=2)
    bad = _finding(quote="not present")

    def repair(_finding: object, _reason: str | None, _transcript: Transcript) -> DraftRubricResult:
        return _finding_object.model_copy(
            update={"evidence": DraftEvidence(turn_id="T001", quote="Hi")}
        )

    _finding_object = bad
    success = verify_and_repair([bad], transcript, repairer=repair, settings=settings)
    assert success.unverified_count == 0
    assert success.verified[0].evidence is not None
    failure = verify_and_repair([bad], transcript, repairer=lambda *_: None, settings=settings)
    assert failure.unverified_count == 1
    assert len(failure.dropped) == 1


def test_confidence_bucket_rules_are_deterministic() -> None:
    assert confidence_bucket(0, 97, 0.7) == "high"
    assert confidence_bucket(1, 100, 1) == "low"
    assert confidence_bucket(0, 95, 0.5) == "medium"
