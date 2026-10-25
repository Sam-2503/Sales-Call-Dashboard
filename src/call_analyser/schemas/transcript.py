"""Transcript contracts with timing expressed exclusively as float seconds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TimedText(BaseModel):
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)

    @model_validator(mode="after")
    def ordered_time(self) -> TimedText:
        if self.start_s >= self.end_s:
            raise ValueError("start_s must be less than end_s")
        return self


class Word(TimedText):
    text: str = Field(min_length=1)
    speaker: str = Field(min_length=1)


class Turn(TimedText):
    id: str = Field(pattern=r"^T\d{3,}$")
    speaker: str = Field(min_length=1)
    role: Literal["agent", "customer", "other"] = "other"
    text: str = Field(min_length=1)
    words: list[Word] = Field(min_length=1)


class Transcript(BaseModel):
    turns: list[Turn] = Field(default_factory=list)
    speakers: list[str] = Field(default_factory=list)
    speaker_roles: dict[str, Literal["agent", "customer", "other"]] = Field(default_factory=dict)
    duration_s: float = Field(ge=0)
    language: str = "en"
    source_model: str = "unknown"
    timing: Literal["segment_interpolated", "word"] = "segment_interpolated"

    @model_validator(mode="after")
    def consistent_speakers(self) -> Transcript:
        turn_speakers = {turn.speaker for turn in self.turns}
        if not turn_speakers.issubset(set(self.speakers)):
            raise ValueError("every turn speaker must be declared in speakers")
        if not turn_speakers.issubset(set(self.speaker_roles)):
            raise ValueError("every turn speaker must have a role")
        return self
