"""Transcript-safe logging helpers."""

from __future__ import annotations

import logging

REDACTED_TRANSCRIPT = "[transcript redacted]"


def transcript_for_log(text: str, *, allow_transcripts: bool = False) -> str:
    """Return text only after the explicit transcript logging opt-in."""
    return text if allow_transcripts else REDACTED_TRANSCRIPT


def get_logger(name: str, *, level: str = "INFO") -> logging.Logger:
    """Return a configured package logger without modifying the root logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())
    return logger
