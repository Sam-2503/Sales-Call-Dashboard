from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from call_analyser.errors import AudioValidationError, PlaybookNotIndexedError, TranscriptionError
from call_analyser.schemas.events import ProgressEvent

from analyser_api.db.models import Job
from analyser_api.jobs.events import event_detail, percent_for
from analyser_api.jobs.runner import ScriptedRunner, TransientRunnerError, map_exception


def test_progress_is_weighted_and_monotonic() -> None:
    assert percent_for("ingest", "started") == 0
    assert percent_for("ingest", "finished") == 5
    assert percent_for("transcribe", "finished") == 25
    assert percent_for("coaching", "finished") == 100
    assert percent_for("ingest", "started", current=80) == 80


def test_job_errors_are_stable_and_sanitized() -> None:
    assert map_exception(AudioValidationError("transcript secret")) == (
        "invalid_audio",
        "The audio could not be analysed.",
        False,
    )
    assert map_exception(TranscriptionError("audio text"))[0] == "transcription_failed"
    assert map_exception(TranscriptionError("audio text"))[2] is True
    assert map_exception(PlaybookNotIndexedError("book text"))[0] == "playbook_unavailable"
    assert map_exception(RuntimeError("transcript secret")) == (
        "internal_error",
        "The analysis failed.",
        False,
    )


@pytest.mark.asyncio
async def test_scripted_runner_emits_ordered_events_and_returns_report() -> None:
    events: list[ProgressEvent] = []

    async def collect(event: ProgressEvent) -> None:
        events.append(event)

    job = Job(call_id=uuid4(), status="running")
    report = await ScriptedRunner().run(job, Path("/tmp/audio.wav"), collect)

    assert report.status == "insufficient_data"
    assert len(events) == 20
    assert [event.status for event in events[:2]] == ["started", "finished"]
    assert events[-1].stage == "coaching"


@pytest.mark.asyncio
async def test_scripted_runner_can_raise_retryable_failure() -> None:
    async def collect(event: ProgressEvent) -> None:
        del event

    job = Job(call_id=uuid4(), status="running")
    with pytest.raises(TransientRunnerError):
        await ScriptedRunner(mode="transient").run(job, Path("/tmp/audio.wav"), collect)


def test_event_detail_never_stores_failure_text() -> None:
    event = ProgressEvent(
        stage="ingest",
        status="failed",
        ts=datetime.now(UTC),
        elapsed_s=0.1,
        detail="do not expose transcript text",
    )
    assert event_detail(event) == {}
