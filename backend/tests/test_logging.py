import logging

from analyser_api.logging import RedactionFilter


def test_redaction_filter_removes_tokens_queries_and_transcripts() -> None:
    record = logging.LogRecord(
        "analyser_api.test",
        logging.INFO,
        __file__,
        1,
        "url=/media/audio?token=secret-token transcript=hello there",
        (),
        None,
    )

    assert RedactionFilter().filter(record) is True
    rendered = record.getMessage()
    assert "secret-token" not in rendered
    assert "hello there" not in rendered
    assert "?[REDACTED]" in rendered
    assert "transcript=[REDACTED]" in rendered
