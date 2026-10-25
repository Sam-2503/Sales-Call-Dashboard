from _pytest.monkeypatch import MonkeyPatch

from call_analyser.config import Settings


def test_settings_read_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "7")
    assert Settings().llm_max_concurrency == 7
