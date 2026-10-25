"""Validated next-step and coaching contracts."""

from __future__ import annotations

from schemas.findings import CustomerSignals, MissedMoment
from schemas.report import Coaching, CoachingItem, NextSteps


def validate_coaching(coaching: Coaching, findings: list[MissedMoment]) -> Coaching:
    """Reject coaching references that do not point at existing findings."""
    known = {finding.id for finding in findings}
    unknown = {item.finding_id for item in coaching.top_fixes} - known
    if unknown:
        raise ValueError(f"coaching references unknown finding ids: {sorted(unknown)}")
    return coaching


def deterministic_next_steps(signals: CustomerSignals | None) -> NextSteps:
    """Create only deterministic actions from verified customer commitments."""
    if signals is None:
        return NextSteps()
    actions = [
        f"{commitment.party}: {commitment.what} by {commitment.due}"
        for commitment in signals.commitments
    ]
    return NextSteps(recommended_actions=actions)


__all__ = ["Coaching", "CoachingItem", "NextSteps", "deterministic_next_steps", "validate_coaching"]
