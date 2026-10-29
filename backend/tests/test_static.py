from pathlib import Path

from fastapi.testclient import TestClient

from analyser_api.app import create_app
from analyser_api.config import Settings


def test_spa_serves_index_and_assets_without_shadowing_api(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    app = create_app(
        Settings(_env_file=None, jwt_secret="x" * 32, static_dir=tmp_path, worker_enabled=False)
    )
    with TestClient(app) as client:
        root = client.get("/")
        deep_link = client.get("/dashboard/calls")
        asset = client.get("/assets/app.js")
        api = client.get("/api/v1/does-not-exist")

    assert root.status_code == 200
    assert root.text == "<html>app</html>"
    assert root.headers["cache-control"] == "no-cache"
    assert deep_link.status_code == 200
    assert asset.headers["cache-control"].startswith("public, max-age=31536000")
    assert api.status_code == 404
    assert api.json()["error"]["code"] == "not_found"
