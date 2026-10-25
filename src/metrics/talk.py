"""Talk-time and monologue metrics over approximate transcript timings."""

from __future__ import annotations

from dataclasses import dataclass

from schemas.transcript import Transcript


@dataclass(frozen=True)
class TalkTime:
    by_role: dict[str, float]
    shares: dict[str, float]
    agent_customer_ratio: float | None


@dataclass(frozen=True)
class Monologue:
    duration_s: float
    start_s: float
    end_s: float
    turn_ids: list[str]


def talk_time(transcript: Transcript) -> TalkTime:
    """Sum turn-covered seconds by role; segment-interpolated values are approximate."""
    by_role: dict[str, float] = {}
    for turn in transcript.turns:
        by_role[turn.role] = by_role.get(turn.role, 0.0) + turn.end_s - turn.start_s
    total = sum(by_role.values())
    shares = {role: duration / total for role, duration in by_role.items()} if total else {}
    agent = by_role.get("agent", 0.0)
    customer = by_role.get("customer", 0.0)
    return TalkTime(
        by_role=by_role,
        shares=shares,
        agent_customer_ratio=agent / customer if customer else None,
    )


def longest_monologue(transcript: Transcript, gap_s: float = 2.0) -> Monologue | None:
    """Find the longest same-speaker run, merging adjacent turns across small gaps."""
    if not transcript.turns:
        return None
    turns = sorted(transcript.turns, key=lambda turn: turn.start_s)
    best: Monologue | None = None
    current = [turns[0]]
    for turn in turns[1:]:
        previous = current[-1]
        if turn.speaker == previous.speaker and turn.start_s - previous.end_s <= gap_s:
            current.append(turn)
            continue
        candidate = Monologue(
            current[-1].end_s - current[0].start_s,
            current[0].start_s,
            current[-1].end_s,
            [item.id for item in current],
        )
        if best is None or candidate.duration_s > best.duration_s:
            best = candidate
        current = [turn]
    candidate = Monologue(
        current[-1].end_s - current[0].start_s,
        current[0].start_s,
        current[-1].end_s,
        [item.id for item in current],
    )
    return candidate if best is None or candidate.duration_s > best.duration_s else best
