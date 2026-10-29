from fastapi.testclient import TestClient

from analyser_api.app import create_app
from analyser_api.config import Settings


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(
                _env_file=None,
                jwt_secret="x" * 32,
                worker_enabled=False,
                admin_token=None,
            )
        )
    )


def test_rubric_and_public_meta_need_no_token() -> None:
    with _client() as client:
        rubric = client.get("/api/v1/rubric")
        meta = client.get("/api/v1/meta")
    assert rubric.status_code == 200
    assert rubric.json()["id"] == "sales_v1"
    assert meta.status_code == 200
    assert meta.json()["quota_remaining"] is None
    assert meta.json()["rubric"]["id"] == "sales_v1"
    assert meta.json()["max_upload_mb"] == 25


def test_playbook_is_unavailable_without_an_index() -> None:
    with _client() as client:
        response = client.get("/api/v1/playbook")
    assert response.status_code == 200
    assert response.json() == {
        "available": False,
        "reason": "playbook index is not available",
    }


def test_admin_endpoints_are_absent_when_token_unset() -> None:
    with _client() as client:
        assert client.get("/api/v1/admin/stats").status_code == 404
        assert client.get("/api/v1/admin/feedback.jsonl").status_code == 404
