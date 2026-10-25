"""Network-free transcriber for tests and local fake-mode operation."""

from call_analyser.ingest import AudioAsset
from call_analyser.schemas import Transcript


class FakeTranscriber:
    def __init__(self, transcript: Transcript) -> None:
        self.fixture = transcript

    async def transcribe(self, asset: AudioAsset) -> Transcript:
        return self.fixture.model_copy(
            deep=True, update={"duration_s": asset.duration_s, "source_model": "fake"}
        )
