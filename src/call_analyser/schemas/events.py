"""Progress event contract shared by CLI and later backend adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProgressEvent(BaseModel):
    stage: str = Field(min_length=1)
    status: Literal["started", "finished", "failed", "cached"]
    ts: datetime
    elapsed_s: float = Field(ge=0)
    detail: str | None = None
