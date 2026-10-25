"""Transcription boundary."""

from typing import Protocol

from call_analyser.ingest import AudioAsset
from call_analyser.schemas import Transcript


class Transcriber(Protocol):
    async def transcribe(self, asset: AudioAsset) -> Transcript: ...
