import json
from datetime import UTC, datetime, timedelta, timezone

from analyser_api.routers.jobs import format_sse, iso_z


def test_sse_event_has_id_and_json_data() -> None:
    rendered = format_sse(7, "progress", {"percent": 25, "stage": "transcribe"})
    assert rendered.startswith("id: 7\n")
    assert "event: progress\n" in rendered
    data = rendered.split("data: ", 1)[1].strip()
    assert json.loads(data) == {"percent": 25, "stage": "transcribe"}
    assert rendered.endswith("\n\n")


def test_sse_terminal_event_has_no_id() -> None:
    rendered = format_sse(None, "done", {"call_id": "abc"})
    assert not rendered.startswith("id:")
    assert "event: done\n" in rendered


def test_iso_z_is_utc() -> None:
    value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert iso_z(value) == "2026-01-01T21:34:05Z"
    assert iso_z(datetime(2026, 1, 2, 3, 4, 5)) == "2026-01-02T03:04:05Z"
    assert iso_z(datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)).endswith("Z")
