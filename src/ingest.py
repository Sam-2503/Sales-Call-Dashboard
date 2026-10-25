"""Deterministic, local audio validation and normalisation."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import soundfile as sf
from pydantic import BaseModel, Field

from config import Settings
from errors import AudioValidationError

SUPPORTED_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


class AudioAsset(BaseModel):
    original_path: Path
    normalized_path: Path
    sha256: str
    duration_s: float = Field(gt=0)
    mime_type: str = "audio/wav"


def _duration_ffprobe(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError) as error:
        raise AudioValidationError(f"could not inspect audio with ffprobe: {path}") from error


def ingest(path: Path, settings: Settings | None = None) -> AudioAsset:
    """Validate input, hash original bytes, and produce a 16kHz mono WAV asset."""
    active = settings or Settings()
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise AudioValidationError(
            "audio must be an existing wav, mp3, m4a, ogg, flac, or webm file"
        )
    if path.stat().st_size > active.max_audio_bytes:
        raise AudioValidationError("audio exceeds MAX_AUDIO_BYTES")
    try:
        duration = _duration_ffprobe(path)
    except AudioValidationError:
        if path.suffix.lower() != ".wav":
            raise
        try:
            info = sf.info(path)
            duration = float(info.duration)
        except RuntimeError as error:
            raise AudioValidationError("audio is corrupt or unsupported") from error
    if duration < active.min_duration_s:
        raise AudioValidationError("audio is shorter than MIN_DURATION_S")
    if duration > active.max_audio_minutes * 60:
        raise AudioValidationError(
            "audio exceeds MAX_AUDIO_MINUTES; chunking is not supported in v1"
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    active.work_dir.mkdir(parents=True, exist_ok=True)
    output = active.work_dir / f"{digest}.wav"
    if not output.exists():
        if shutil.which("ffmpeg"):
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(path), "-ar", "16000", "-ac", "1", str(output)],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as error:
                raise AudioValidationError("ffmpeg could not normalize audio") from error
        elif path.suffix.lower() == ".wav":
            try:
                samples, rate = sf.read(path, always_2d=True)
                mono = samples.mean(axis=1)
                if rate != 16000:
                    raise AudioValidationError("ffmpeg is required to resample this WAV file")
                sf.write(output, mono, 16000, subtype="PCM_16")
            except RuntimeError as error:
                raise AudioValidationError("audio is corrupt or unsupported") from error
        else:
            raise AudioValidationError("ffmpeg is required to normalize this audio format")
    if output.stat().st_size > active.transcribe_inline_max_mb * 1024 * 1024:
        raise AudioValidationError("normalised audio exceeds TRANSCRIBE_INLINE_MAX_MB")
    return AudioAsset(
        original_path=path, normalized_path=output, sha256=digest, duration_s=duration
    )
