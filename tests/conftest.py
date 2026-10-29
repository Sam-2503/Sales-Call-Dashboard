"""Shared test configuration; live tests require an explicit API key."""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip network-backed tests unless the operator supplied a key."""
    if os.environ.get("GEMINI_API_KEY"):
        return
    skip = pytest.mark.skip(reason="GEMINI_API_KEY is not set")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
