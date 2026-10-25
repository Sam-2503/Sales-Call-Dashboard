"""Gemini audio transcription, with deterministic response normalisation."""

from __future__ import annotations

import base64
import re
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel, Field

from config import Settings
from errors import TranscriptionError
from ingest import AudioAsset
from llm import get_chat_model
from persist import persisted
from prompts.registry import PromptRegistry
from schemas import Transcript, Turn, Word


class RawSegment(BaseModel):
    speaker: str = Field(min_length=1)
    start: str
    end: str
    text: str


class RawTranscript(BaseModel):
    segments: list[RawSegment]


def parse_timestamp(value: str) -> float:
    try:
        pieces = [float(piece) for piece in value.strip().split(":")]
        if len(pieces) == 1:
            return pieces[0]
        if len(pieces) == 2:
            return pieces[0] * 60 + pieces[1]
        if len(pieces) == 3:
            return pieces[0] * 3600 + pieces[1] * 60 + pieces[2]
    except ValueError as error:
        raise TranscriptionError(f"invalid timestamp: {value}") from error
    raise TranscriptionError(f"invalid timestamp: {value}")


def _words(text: str, speaker: str, start_s: float, end_s: float) -> list[Word]:
    values = re.findall(r"\S+", text)
    total = sum(max(len(value), 1) for value in values)
    cursor = start_s
    result: list[Word] = []
    for index, value in enumerate(values):
        share = (end_s - start_s) * len(value) / total
        next_cursor = end_s if index == len(values) - 1 else cursor + share
        result.append(Word(text=value, speaker=speaker, start_s=cursor, end_s=next_cursor))
        cursor = next_cursor
    return result


def parse_response(raw: RawTranscript, asset: AudioAsset, model: str) -> Transcript:
    """Validate timestamp quality, normalise speakers, and interpolate word timing."""
    parsed = [
        (segment, parse_timestamp(segment.start), parse_timestamp(segment.end))
        for segment in raw.segments
        if segment.text.strip()
    ]
    unordered = sum(left[1] > right[1] for left, right in zip(parsed, parsed[1:], strict=False))
    if parsed and unordered / len(parsed) > 0.05:
        raise TranscriptionError("too many out-of-order segments")
    parsed.sort(key=lambda item: item[1])
    speaker_names: dict[str, str] = {}
    turns: list[Turn] = []
    previous_end = 0.0
    for segment, start, end in parsed:
        if start > asset.duration_s + 2 or end > asset.duration_s + 2:
            raise TranscriptionError("segment timestamp exceeds audio duration")
        start, end = max(start, previous_end), min(end, asset.duration_s)
        if end <= start:
            continue
        key = segment.speaker.strip()
        speaker = speaker_names.setdefault(key, f"spk_{len(speaker_names) + 1}")
        words = _words(segment.text.strip(), speaker, start, end)
        turns.append(
            Turn(
                id=f"T{len(turns) + 1:03d}",
                speaker=speaker,
                role="other",
                start_s=start,
                end_s=end,
                text=segment.text.strip(),
                words=words,
            )
        )
        previous_end = end
    if not turns:
        raise TranscriptionError("transcript has no usable segments")
    if turns[-1].end_s < asset.duration_s * 0.8:
        raise TranscriptionError("transcript appears truncated before audio ends")
    speakers = list(speaker_names.values())
    return Transcript(
        turns=turns,
        speakers=speakers,
        speaker_roles={speaker: "other" for speaker in speakers},
        duration_s=asset.duration_s,
        language="en",
        source_model=model,
        timing="segment_interpolated",
    )


class GeminiTranscriber:
    def __init__(
        self, settings: Settings | None = None, prompts: PromptRegistry | None = None
    ) -> None:
        self.settings = settings or Settings()
        self.prompts = prompts or PromptRegistry()

    async def _call_model(self, asset: AudioAsset, config: RunnableConfig) -> RawTranscript:
        prompt = self.prompts.load("transcribe", "v1").render()
        content: list[str | dict[Any, Any]] = [
            {"type": "text", "text": prompt},
            {
                "type": "audio",
                "base64": base64.b64encode(asset.normalized_path.read_bytes()).decode(),
                "mime_type": "audio/wav",
            },
        ]
        model = get_chat_model("transcribe", self.settings).with_structured_output(RawTranscript)
        result = await model.ainvoke([HumanMessage(content=content)], config=config)
        if not isinstance(result, RawTranscript):
            raise TranscriptionError("Gemini did not return a valid structured transcript")
        return result

    async def transcribe(
        self, asset: AudioAsset, config: RunnableConfig | None = None
    ) -> Transcript:
        raw = await self._call_model(asset, config or {})
        return parse_response(raw, asset, self.settings.transcribe_model)


@chain
@persisted("transcribe")
async def transcribe(asset: AudioAsset, config: RunnableConfig) -> Transcript:
    """Default cached transcription stage."""
    return await GeminiTranscriber().transcribe(asset, config)
