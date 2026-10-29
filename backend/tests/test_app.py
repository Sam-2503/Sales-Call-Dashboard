from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from analyser_api.app import create_app
from analyser_api.config import Settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(_env_file=None, jwt_secret="x" * 32, worker_enabled=False))
    with TestClient(app) as test_client:
        yield test_client


def test_health_does_not_log_query_string(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="analyser_api.requests"):
        response = client.get("/healthz?secret=should-not-be-logged")

    assert response.status_code == 200
    assert "secret" not in caplog.text
    assert "/healthz" in caplog.text


def test_request_id_is_echoed_and_security_headers_are_present(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["request_id"] == response.headers["x-request-id"]
    assert "Traceback" not in response.text


def test_healthz_does_not_need_a_database(client: TestClient) -> None:
    # create_app only constructs the engine; it never connects on /healthz.
    response = client.get("/healthz")
    assert response.json() == {"status": "ok"}


def test_create_app_works_with_dev_defaults() -> None:
    app = create_app(Settings(_env_file=None, worker_enabled=False))
    assert app.title == "Call Analyser API"
    assert app.state.settings.environment == "dev"
    # Dev convenience: a missing JWT secret is generated, never accepted in prod.
    assert app.state.settings.jwt_secret
