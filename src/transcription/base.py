"""Transcription boundary."""

from typing import Protocol

from ingest import AudioAsset
from schemas import Transcript


class Transcriber(Protocol):
    async def transcribe(self, asset: AudioAsset) -> Transcript: ...
