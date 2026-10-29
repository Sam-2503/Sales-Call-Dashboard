"""Progress accounting for package events that do not carry a percentage."""

from __future__ import annotations

from call_analyser.events import STAGE_WEIGHTS
from call_analyser.schemas.events import ProgressEvent

STAGE_ORDER: tuple[str, ...] = tuple(STAGE_WEIGHTS)
TOTAL_WEIGHT = sum(STAGE_WEIGHTS.values())


def percent_for(stage: str, status: str, current: int = 0) -> int:
    """Map a stage event to a monotonic percentage using the package weights."""
    before = 0
    for name in STAGE_ORDER:
        if name == stage:
            break
        before += STAGE_WEIGHTS[name]
    weight = STAGE_WEIGHTS.get(stage, 0)
    after = before + weight if status in ("finished", "cached") else before
    return int(max(current, min(100, round(after * 100 / TOTAL_WEIGHT))))


def event_detail(event: ProgressEvent) -> dict[str, object]:
    # Package failure details may contain model or transcript text.  Persist only
    # the fact that a failure happened, never its message.
    return {}
