"""Transcription adapters."""

from transcription.fake import FakeTranscriber
from transcription.gemini import GeminiTranscriber

__all__ = ["FakeTranscriber", "GeminiTranscriber"]
