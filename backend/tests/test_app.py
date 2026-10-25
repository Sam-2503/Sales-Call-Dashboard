from fastapi.testclient import TestClient

from analyser_api.app import create_app
from analyser_api.config import Settings


def test_health_does_not_log_query_string(caplog) -> None:
    client = TestClient(create_app(Settings()))
    with caplog.at_level("INFO", logger="analyser_api.requests"):
        response = client.get("/healthz?secret=should-not-be-logged")

    assert response.status_code == 200
    assert "secret" not in caplog.text
    assert "/healthz" in caplog.text
