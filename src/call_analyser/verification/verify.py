"""Evidence verification and deterministic confidence derivation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from call_analyser.config import Settings
from call_analyser.schemas.findings import Evidence
from call_analyser.schemas.transcript import Transcript, Turn
from call_analyser.verification.matcher import MatchResult, match_quote


class HasEvidence(Protocol):
    """Minimal model-output shape accepted by the verifier."""

    model_confidence: float


@dataclass(frozen=True)
class FindingVerification:
    finding: Any
    evidence: Evidence | None
    verified: bool
    reason: str | None = None


@dataclass
class VerificationOutcome:
    verified: list[FindingVerification] = field(default_factory=list)
    dropped: list[dict[str, Any]] = field(default_factory=list)
    unverified_count: int = 0


def confidence_bucket(attempt: int, score: float, model_confidence: float) -> str:
    """Map evidence quality to a stable confidence bucket."""
    if attempt == 0 and score >= 97 and model_confidence >= 0.7:
        return "high"
    if attempt > 0 or score < 93 or model_confidence < 0.4:
        return "low"
    return "medium"


def _candidate(finding: Any) -> tuple[str, str, str | None] | None:
    evidence = getattr(finding, "evidence", None)
    if evidence is not None:
        return evidence.turn_id, evidence.quote, getattr(evidence, "role", None) or getattr(
            finding, "role", None
        )
    turn_id = getattr(finding, "turn_id", None)
    quote = getattr(finding, "quote", None)
    if turn_id and quote:
        return turn_id, quote, getattr(finding, "role", None)
    return None


def _evidence(
    turn: Turn,
    match: MatchResult,
    model_confidence: float,
    attempt: int,
) -> Evidence:
    words = turn.words[match.start_word : match.end_word]
    quote = " ".join(word.text for word in words)
    return Evidence(
        turn_id=turn.id,
        speaker=turn.speaker,
        role=turn.role,
        quote=quote,
        start_s=words[0].start_s,
        end_s=words[-1].end_s,
        match_score=match.score,
        attempt=attempt,
    )


def verify_finding(
    finding: Any,
    transcript: Transcript,
    *,
    attempt: int = 0,
    settings: Settings | None = None,
) -> FindingVerification:
    """Verify a finding's quote, preferring its turn and then nearby turns."""
    settings = settings or Settings()
    candidate = _candidate(finding)
    if candidate is None:
        return FindingVerification(finding, None, False, "finding has no quote and turn_id")
    turn_id, quote, claimed_role = candidate
    turns = transcript.turns
    index = next((index for index, turn in enumerate(turns) if turn.id == turn_id), None)
    if index is None:
        return FindingVerification(finding, None, False, f"unknown turn id: {turn_id}")
    indexes = [index] + [
        neighbor
        for distance in range(1, settings.verify_turn_radius + 1)
        for neighbor in (index - distance, index + distance)
        if 0 <= neighbor < len(turns)
    ]
    best: tuple[Turn, MatchResult] | None = None
    for candidate_index in indexes:
        turn = turns[candidate_index]
        if claimed_role is not None and turn.role != claimed_role:
            continue
        match = match_quote(turn, quote)
        if match and (best is None or match.score > best[1].score):
            best = (turn, match)
    if best is None or best[1].score < settings.verify_min_score:
        score = best[1].score if best else 0
        return FindingVerification(
            finding, None, False, f"quote did not verify (best score {score:.1f})"
        )
    return FindingVerification(
        finding,
        _evidence(best[0], best[1], float(getattr(finding, "model_confidence", 0)), attempt),
        True,
    )


def verify_and_repair(
    findings: list[Any],
    transcript: Transcript,
    *,
    repairer: Any | None = None,
    settings: Settings | None = None,
) -> VerificationOutcome:
    """Verify all findings; optionally retry rejected findings through a repairer."""
    settings = settings or Settings()
    outcome = VerificationOutcome()
    for finding in findings:
        result = verify_finding(finding, transcript, settings=settings)
        for attempt in range(1, settings.repair_max_attempts + 1):
            if result.verified or repairer is None:
                break
            repaired = repairer(finding, result.reason, transcript)
            if repaired is None:
                break
            result = verify_finding(repaired, transcript, attempt=attempt, settings=settings)
            finding = repaired
        if result.verified or (
            getattr(finding, "status", None) == "missed" and result.reason
        ):
            outcome.verified.append(result)
        else:
            outcome.unverified_count += 1
            outcome.dropped.append(
                {
                    "id": getattr(finding, "id", None),
                    "reason": result.reason,
                    "original": repr(finding),
                }
            )
    return outcome
