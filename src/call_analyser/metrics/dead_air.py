"""Energy-based dead-air detection for audio files."""

from __future__ import annotations

from pathlib import Path

import librosa


def find_dead_air(
    audio_path: Path,
    *,
    threshold_db: float = -40.0,
    min_duration_s: float = 2.0,
) -> list[tuple[float, float]]:
    """Find contiguous low-energy stretches; boundaries have frame-level precision."""
    samples, sample_rate = librosa.load(str(audio_path), sr=None, mono=True)
    if len(samples) == 0:
        return []
    rms = librosa.feature.rms(y=samples, frame_length=2048, hop_length=512, center=False)[0]
    db = librosa.amplitude_to_db(rms, ref=1.0)
    silent = db <= threshold_db
    results: list[tuple[float, float]] = []
    start: int | None = None
    for index, is_silent in enumerate(silent):
        if is_silent and start is None:
            start = index
        if (not is_silent or index == len(silent) - 1) and start is not None:
            end = index + 1 if is_silent else index
            start_s = start * 512 / sample_rate
            end_s = min(len(samples) / sample_rate, end * 512 / sample_rate + 2048 / sample_rate)
            if end_s - start_s >= min_duration_s:
                results.append((start_s, end_s))
            start = None
    return results
