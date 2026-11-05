"""Groq Whisper transcription with deterministic response normalisation."""

from __future__ import annotations

import re
from typing import Any

import httpx
from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel

from call_analyser.config import Settings
from call_analyser.errors import TranscriptionError
from call_analyser.ingest import AudioAsset
from call_analyser.persist import persisted
from call_analyser.schemas import Transcript, Turn, Word


class RawSegment(BaseModel):
    speaker: str = "speaker"
    start: float
    end: float
    text: str


class RawTranscript(BaseModel):
    segments: list[RawSegment]


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


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _normalise_response(payload: dict[str, Any], duration_s: float) -> RawTranscript:
    raw_segments = payload.get("segments")
    if not isinstance(raw_segments, list):
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise TranscriptionError("Groq returned no transcript segments")
        raw_segments = [{"start": 0, "end": duration_s, "text": text}]

    segments: list[RawSegment] = []
    cursor = 0.0
    has_speaker_labels = any(
        isinstance(item, dict) and item.get("speaker") is not None for item in raw_segments
    )
    for index, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        start = _number(item.get("start"), cursor)
        end = _number(item.get("end"), duration_s if len(raw_segments) == 1 else start)
        speaker = str(item.get("speaker") or "speaker")
        if not has_speaker_labels and len(raw_segments) > 1:
            # Whisper does not diarize. Keep alternating turns distinguishable so
            # the role stage can run, while retaining the transcript as approximate.
            speaker = f"speaker_{index % 2 + 1}"
        segments.append(
            RawSegment(
                speaker=speaker,
                start=start,
                end=end,
                text=text,
            )
        )
        cursor = max(cursor, end)
    if not segments:
        raise TranscriptionError("Groq returned no usable transcript segments")
    return RawTranscript(segments=segments)


def parse_response(raw: RawTranscript, asset: AudioAsset, model: str) -> Transcript:
    parsed = sorted(
        (
            (
                segment,
                max(0.0, segment.start),
                max(0.0, segment.end),
            )
            for segment in raw.segments
            if segment.text.strip()
        ),
        key=lambda item: (item[1], item[2]),
    )
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
        turns.append(
            Turn(
                id=f"T{len(turns) + 1:03d}",
                speaker=speaker,
                role="other",
                start_s=start,
                end_s=end,
                text=segment.text.strip(),
                words=_words(segment.text.strip(), speaker, start, end),
            )
        )
        previous_end = end
    if not turns:
        raise TranscriptionError("transcript has no usable segments")
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


class GroqTranscriber:
    """Call Groq's Whisper transcription endpoint."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    async def transcribe(
        self, asset: AudioAsset, config: RunnableConfig | None = None
    ) -> Transcript:
        del config
        if not self.settings.groq_api_key:
            raise TranscriptionError("GROQ_API_KEY is not configured")
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_s) as client:
                with asset.normalized_path.open("rb") as audio:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                        data={
                            "model": self.settings.transcribe_model,
                            "language": "en",
                            "response_format": "verbose_json",
                            "timestamp_granularities[]": "segment",
                        },
                        files={"file": (asset.normalized_path.name, audio, "audio/wav")},
                    )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise TranscriptionError("Groq speech-to-text request failed") from error
        if not isinstance(payload, dict):
            raise TranscriptionError("Groq speech-to-text returned an invalid response")
        return parse_response(
            _normalise_response(payload, asset.duration_s), asset, self.settings.transcribe_model
        )


@chain
@persisted("transcribe")
async def transcribe(asset: AudioAsset, config: RunnableConfig) -> Transcript:
    return await GroqTranscriber().transcribe(asset, config)
