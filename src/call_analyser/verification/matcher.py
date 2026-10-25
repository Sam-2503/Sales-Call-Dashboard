"""Fuzzy quote matching against timed transcript words."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz.fuzz import ratio

from call_analyser.schemas.transcript import Turn


@dataclass(frozen=True)
class NormalizedWord:
    text: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class MatchResult:
    start_word: int
    end_word: int
    score: float
    normalized_text: str


def normalize_words(text: str) -> tuple[str, list[NormalizedWord]]:
    """Normalize text while retaining character offsets for each normalized word."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    words: list[NormalizedWord] = []
    parts: list[str] = []
    for match in re.finditer(r"[^\W_]+(?:['’][^\W_]+)*", normalized, re.UNICODE):
        word = match.group().replace("’", "'")
        words.append(NormalizedWord(word, match.start(), match.end()))
        parts.append(word)
    return " ".join(parts), words


def match_quote(turn: Turn, quote: str) -> MatchResult | None:
    """Find the highest-scoring contiguous quote span in a turn."""
    target, target_words = normalize_words(quote)
    source, source_words = normalize_words(turn.text)
    if not target_words or not source_words:
        return None
    target_count = len(target_words)
    best: MatchResult | None = None
    for start in range(len(source_words)):
        for end in range(start + 1, min(len(source_words), start + target_count + 3) + 1):
            candidate = " ".join(word.text for word in source_words[start:end])
            score = float(ratio(target, candidate))
            result = MatchResult(start, end, score, candidate)
            if best is None or result.score > best.score:
                best = result
    return best
