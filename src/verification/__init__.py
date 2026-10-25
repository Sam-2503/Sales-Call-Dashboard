"""Evidence verification and repair."""

from verification.matcher import MatchResult, match_quote, normalize_words
from verification.verify import (
    FindingVerification,
    VerificationOutcome,
    confidence_bucket,
    verify_and_repair,
    verify_finding,
)

__all__ = [
    "FindingVerification",
    "MatchResult",
    "VerificationOutcome",
    "confidence_bucket",
    "match_quote",
    "normalize_words",
    "verify_and_repair",
    "verify_finding",
]
