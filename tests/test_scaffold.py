"""Stage 0 scaffold checks: settings, imports, CLI, and transcript redaction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

import call_analyser
from call_analyser.cli import app
from call_analyser.config import Settings
from call_analyser.logging import REDACTED_TRANSCRIPT, transcript_for_log


def test_package_imports_with_version() -> None:
    assert call_analyser.__version__ == "0.1.0"


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_max_concurrency == 4
    assert settings.max_audio_minutes == 5
    assert settings.dead_air_s == 3.0
    assert settings.log_transcripts is False


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "7")
    assert Settings(_env_file=None).llm_max_concurrency == 7


def test_settings_read_dotenv(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DEAD_AIR_S=4.5\n", encoding="utf-8")
    assert Settings(_env_file=env_file).dead_air_s == 4.5


def test_settings_reject_invalid_chunk_sizes() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_target_tokens=400, chunk_max_tokens=300)


def test_transcript_logging_is_redacted_by_default() -> None:
    assert transcript_for_log("customer secret") == REDACTED_TRANSCRIPT


def test_transcript_logging_requires_opt_in() -> None:
    assert transcript_for_log("customer secret", allow_transcripts=True) == "customer secret"


def test_cli_settings_excludes_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-key")
    result = CliRunner().invoke(app, ["settings"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "gemini_api_key" not in payload
    assert payload["dead_air_s"] == 3.0


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sales-call analysis" in result.stdout
