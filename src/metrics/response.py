"""Response-delay metrics."""

from __future__ import annotations

from schemas.transcript import Transcript


def response_delays(transcript: Transcript) -> list[float]:
    """Return customer-to-agent delays, clamped at zero, in approximate seconds."""
    turns = sorted(transcript.turns, key=lambda turn: turn.start_s)
    return [
        max(0.0, current.words[0].start_s - previous.words[-1].end_s)
        for previous, current in zip(turns, turns[1:], strict=False)
        if previous.role == "customer" and current.role == "agent"
    ]


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def response_summary(transcript: Transcript) -> tuple[float | None, float | None]:
    delays = response_delays(transcript)
    return percentile(delays, 0.5), percentile(delays, 0.9)
