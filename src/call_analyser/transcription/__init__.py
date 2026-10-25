"""Transcription adapters."""

from call_analyser.transcription.fake import FakeTranscriber
from call_analyser.transcription.gemini import GeminiTranscriber

__all__ = ["FakeTranscriber", "GeminiTranscriber"]
