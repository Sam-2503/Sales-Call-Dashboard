"""Timeline flags derived from deterministic metric events."""

from __future__ import annotations

from schemas.metrics import TimelineFlag
from schemas.transcript import Transcript


def build_flags(
    transcript: Transcript,
    *,
    long_monologue_s: float,
    slow_response_s: float,
    dead_air: list[tuple[float, float]] | None = None,
) -> list[TimelineFlag]:
    """Create dashboard flags; timing remains approximate for segment-timed transcripts."""
    flags: list[TimelineFlag] = []
    for turn in transcript.turns:
        if turn.end_s - turn.start_s > long_monologue_s:
            flags.append(
                TimelineFlag(
                    kind="long_monologue",
                    start_s=turn.start_s,
                    end_s=turn.end_s,
                    speaker=turn.speaker,
                    detail=f"Long monologue ({turn.end_s - turn.start_s:.1f}s).",
                )
            )
    turns = sorted(transcript.turns, key=lambda turn: turn.start_s)
    for previous, current in zip(turns, turns[1:], strict=True):
        if previous.role == "customer" and current.role == "agent":
            delay = max(0.0, current.words[0].start_s - previous.words[-1].end_s)
            if delay > slow_response_s:
                flags.append(
                    TimelineFlag(
                        kind="slow_response",
                        start_s=previous.end_s,
                        end_s=current.start_s,
                        speaker=current.speaker,
                        detail=f"Response delay ({delay:.1f}s; indicative).",
                    )
                )
    for start_s, end_s in dead_air or []:
        flags.append(
            TimelineFlag(
                kind="dead_air",
                start_s=start_s,
                end_s=end_s,
                detail="Low audio energy.",
            )
        )
    return sorted(flags, key=lambda flag: flag.start_s)
