"""Deterministic OpenAPI export used by the contract drift check."""

from __future__ import annotations

import json
from pathlib import Path

from analyser_api.app import create_app
from analyser_api.config import Settings

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "openapi.json"


def render_openapi() -> str:
    """Render the app schema without connecting to any external service."""
    schema = create_app(Settings()).openapi()
    return json.dumps(schema, sort_keys=True, indent=2) + "\n"
