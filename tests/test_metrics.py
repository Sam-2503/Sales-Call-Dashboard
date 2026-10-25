from pathlib import Path

import numpy as np
import soundfile as sf

from metrics.dead_air import find_dead_air
from metrics.fillers import count_fillers
from metrics.response import response_summary
from metrics.talk import longest_monologue, talk_time
from schemas.transcript import Transcript, Turn, Word


def _turn(
    number: int, speaker: str, role: str, start: float, end: float, text: str
) -> Turn:
    tokens = text.split()
    width = (end - start) / len(tokens)
    words = [
        Word(
            text=token,
            start_s=start + index * width,
            end_s=start + (index + 1) * width,
            speaker=speaker,
        )
        for index, token in enumerate(tokens)
    ]
    return Turn(
        id=f"T{number:03d}",
        speaker=speaker,
        role=role,  # type: ignore[arg-type]
        start_s=start,
        end_s=end,
        text=text,
        words=words,
    )


def _transcript() -> Transcript:
    turns = [
        _turn(1, "a", "agent", 0, 4, "um hello there"),
        _turn(2, "c", "customer", 5, 7, "you know yes"),
        _turn(3, "a", "agent", 10, 14, "kind of great"),
    ]
    return Transcript(
        turns=turns,
        speakers=["a", "c"],
        speaker_roles={"a": "agent", "c": "customer"},
        duration_s=14,
    )


def test_talk_time_and_monologue() -> None:
    metrics = talk_time(_transcript())
    assert metrics.by_role == {"agent": 8, "customer": 2}
    assert metrics.shares["agent"] == 0.8
    assert metrics.agent_customer_ratio == 4
    monologue = longest_monologue(_transcript(), gap_s=2)
    assert monologue is not None
    assert monologue.duration_s == 4
    assert monologue.turn_ids == ["T001"]


def test_fillers_and_indicative_response_percentiles() -> None:
    transcript = _transcript()
    assert count_fillers(transcript) == {"agent": 2, "customer": 1}
    median, p90 = response_summary(transcript)
    # Customer ends at 7 and agent starts at 10, so this response is 3 seconds.
    assert median == 3
    assert p90 == 3


def test_dead_air_detects_synthesized_silence(tmp_path: Path) -> None:
    sample_rate = 16_000
    audio = np.concatenate(
        [
            np.full(sample_rate, 0.2, dtype=np.float32),
            np.zeros(sample_rate * 3, dtype=np.float32),
            np.full(sample_rate, 0.2, dtype=np.float32),
        ]
    )
    path = tmp_path / "silence.wav"
    sf.write(path, audio, sample_rate)
    stretches = find_dead_air(path, min_duration_s=2)
    assert len(stretches) == 1
    start, end = stretches[0]
    assert 0.8 <= start <= 1.2
    assert 3.8 <= end <= 4.2
