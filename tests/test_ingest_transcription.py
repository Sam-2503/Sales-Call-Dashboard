from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from call_analyser.config import Settings
from call_analyser.errors import AudioValidationError, TranscriptionError
from call_analyser.ingest import AudioAsset, ingest
from call_analyser.schemas import Transcript
from call_analyser.transcription.gemini import RawSegment, RawTranscript, parse_response
from call_analyser.transcription.roles import RoleAssignment, apply_roles


def wav(path: Path, seconds: float) -> None:
    sf.write(path, np.zeros(int(16000 * seconds)), 16000)


def settings(tmp_path: Path, **updates: object) -> Settings:
    values: dict[str, object] = {
        "work_dir": tmp_path / "work",
        "min_duration_s": 0,
        "max_audio_minutes": 5,
    }
    values.update(updates)
    return Settings.model_validate(values)


def test_ingest_normalises_generated_wav(tmp_path: Path) -> None:
    source = tmp_path / "call.wav"
    wav(source, 1)
    asset = ingest(source, settings(tmp_path))
    assert asset.duration_s == pytest.approx(1)
    assert sf.info(asset.normalized_path).samplerate == 16000


def test_ingest_rejects_long_and_corrupt_audio(tmp_path: Path) -> None:
    source = tmp_path / "long.wav"
    wav(source, 2)
    with pytest.raises(AudioValidationError, match="MAX_AUDIO_MINUTES"):
        ingest(source, settings(tmp_path, max_audio_minutes=0.01))
    corrupt = tmp_path / "corrupt.wav"
    corrupt.write_bytes(b"no audio")
    with pytest.raises(AudioValidationError):
        ingest(corrupt, settings(tmp_path))


def asset(tmp_path: Path, duration_s: float = 20) -> AudioAsset:
    path = tmp_path / "normal.wav"
    wav(path, 20)
    return AudioAsset(
        original_path=path, normalized_path=path, sha256="a" * 64, duration_s=duration_s
    )


def test_parse_normalises_order_overlap_and_timestamps(tmp_path: Path) -> None:
    ordered_tail = [
        RawSegment(speaker="B", start=str(15 + index), end=str(16 + index), text="tail")
        for index in range(18)
    ]
    raw = RawTranscript(
        segments=[
            RawSegment(speaker="B", start="00:05", end="00:10", text="second segment"),
            RawSegment(speaker="A", start="0", end="00:06", text="first segment"),
            RawSegment(speaker="B", start="0:00:10", end="15", text="third segment"),
            *ordered_tail,
        ]
    )
    transcript = parse_response(raw, asset(tmp_path, 40), "fake")
    assert [turn.speaker for turn in transcript.turns[:3]] == ["spk_1", "spk_2", "spk_2"]
    assert transcript.turns[1].start_s == 6
    assert transcript.turns[0].words[0].start_s == transcript.turns[0].start_s
    assert transcript.turns[0].words[-1].end_s == transcript.turns[0].end_s


def test_parse_rejects_out_of_range_timestamp(tmp_path: Path) -> None:
    raw = RawTranscript(
        segments=[RawSegment(speaker="A", start="00:00", end="00:30", text="too late")]
    )
    with pytest.raises(TranscriptionError, match="exceeds"):
        parse_response(raw, asset(tmp_path), "fake")


def test_role_assignment_rejects_unknown_and_sets_extras_other() -> None:
    transcript = Transcript.model_validate_json(
        Path("fixtures/synthetic_short_transcript.json").read_text()
    )
    assigned = apply_roles(
        transcript, RoleAssignment(agent_speaker="Rep", customer_speaker="Prospect")
    )
    assert assigned.speaker_roles == {"Rep": "agent", "Prospect": "customer"}
    with pytest.raises(TranscriptionError):
        apply_roles(transcript, RoleAssignment(agent_speaker="Nobody", customer_speaker="Prospect"))
