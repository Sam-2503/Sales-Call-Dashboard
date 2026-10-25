"""Configurable, deterministic filler-word counting."""

from __future__ import annotations

import re
from collections import Counter

from call_analyser.schemas.transcript import Transcript

DEFAULT_FILLERS = ("um", "uh", "er", "ah", "you know", "i mean", "sort of", "kind of", "basically")


def count_fillers(
    transcript: Transcript, fillers: tuple[str, ...] = DEFAULT_FILLERS
) -> dict[str, int]:
    """Count configured fillers by role using normalized word sequences.

    ``like`` is intentionally excluded: it is common as an ordinary verb or
    preposition and cannot be classified reliably without semantic judgment.
    """
    phrases = [tuple(re.findall(r"[a-z]+", filler.lower())) for filler in fillers]
    counts: Counter[str] = Counter()
    for turn in transcript.turns:
        words = [word.text.lower() for word in turn.words]
        normalized = [re.sub(r"[^a-z']", "", word) for word in words]
        for phrase, _original in zip(phrases, fillers, strict=True):
            width = len(phrase)
            counts[turn.role] += sum(
                normalized[index : index + width] == list(phrase)
                for index in range(len(normalized) - width + 1)
            )
    return dict(counts)
