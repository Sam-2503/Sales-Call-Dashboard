"""The deterministic Stage 4 metrics chain."""

from __future__ import annotations

from pathlib import Path

from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel

from config import Settings
from metrics.dead_air import find_dead_air
from metrics.fillers import count_fillers
from metrics.flags import build_flags
from metrics.response import response_summary
from metrics.talk import longest_monologue, talk_time
from schemas.metrics import AudioMetrics
from schemas.transcript import Transcript


class MetricsInput(BaseModel):
    transcript: Transcript
    audio_path: Path | None = None


@chain  # type: ignore[arg-type]
async def compute_metrics(input: MetricsInput, config: RunnableConfig) -> AudioMetrics:
    """Compute deterministic metrics without persistence or model calls."""
    settings = Settings()
    transcript = input.transcript
    times = talk_time(transcript)
    monologue = longest_monologue(transcript, settings.monologue_gap_s)
    fillers = count_fillers(transcript)
    agent_words = sum(len(turn.words) for turn in transcript.turns if turn.role == "agent")
    customer_words = sum(len(turn.words) for turn in transcript.turns if turn.role == "customer")
    duration_minutes = transcript.duration_s / 60
    dead_air = (
        find_dead_air(
            input.audio_path,
            threshold_db=settings.silence_db,
            min_duration_s=settings.dead_air_threshold_s,
        )
        if input.audio_path is not None
        else []
    )
    median_delay, p90_delay = response_summary(transcript)
    flags = build_flags(
        transcript,
        long_monologue_s=settings.long_monologue_s,
        slow_response_s=settings.slow_response_s,
        dead_air=dead_air,
    )
    return AudioMetrics(
        duration_s=transcript.duration_s,
        timing_resolution=transcript.timing,
        agent_talk_ratio=times.shares.get("agent"),
        customer_talk_ratio=times.shares.get("customer"),
        agent_customer_talk_ratio=times.agent_customer_ratio,
        agent_words_per_minute=agent_words / duration_minutes if duration_minutes else None,
        customer_words_per_minute=customer_words / duration_minutes if duration_minutes else None,
        filler_count=fillers.get("agent", 0) + fillers.get("customer", 0),
        filler_rate_agent=fillers.get("agent", 0) / agent_words * 100 if agent_words else None,
        filler_rate_customer=(
            fillers.get("customer", 0) / customer_words * 100 if customer_words else None
        ),
        longest_monologue_s=monologue.duration_s if monologue else None,
        longest_monologue_start_s=monologue.start_s if monologue else None,
        longest_monologue_end_s=monologue.end_s if monologue else None,
        longest_monologue_turn_ids=monologue.turn_ids if monologue else [],
        response_delay_median_s=median_delay,
        response_delay_p90_s=p90_delay,
        silence_ratio=(
            sum(end - start for start, end in dead_air) / transcript.duration_s
            if transcript.duration_s
            else None
        ),
        timeline_flags=flags,
    )
