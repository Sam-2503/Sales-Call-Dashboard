"""Strict loading and rendering of versioned Markdown prompts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from typing import Any

import yaml


class PromptError(ValueError):
    """A prompt file or its supplied variables are invalid."""


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    input_variables: tuple[str, ...]
    body: str

    @property
    def prompt_id(self) -> str:
        return f"{self.name}@{self.version}+{hashlib.sha256(self.body.encode()).hexdigest()[:8]}"

    def render(self, **values: str) -> str:
        expected = set(self.input_variables)
        supplied = set(values)
        if expected != supplied:
            missing, extra = expected - supplied, supplied - expected
            raise PromptError(
                f"prompt variables mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        fields = {field for _, field, _, _ in Formatter().parse(self.body) if field}
        if fields != expected:
            raise PromptError("front matter input_variables must exactly match template fields")
        return self.body.format(**values)


class PromptRegistry:
    """File-backed registry; it does not read prompt files until requested."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).parent

    def load(self, stage: str, version: str = "v1") -> Prompt:
        path = self.root / stage / f"{version}.md"
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise PromptError(f"prompt not found: {path}") from error
        if not raw.startswith("---\n"):
            raise PromptError(f"prompt front matter missing: {path}")
        _, front_matter, body = raw.split("---\n", 2)
        data: dict[str, Any] = yaml.safe_load(front_matter) or {}
        required = {"name", "version", "input_variables"}
        if set(data) != required or not isinstance(data["input_variables"], list):
            raise PromptError(f"invalid front matter: {path}")
        return Prompt(
            name=str(data["name"]),
            version=str(data["version"]),
            input_variables=tuple(str(value) for value in data["input_variables"]),
            body=body,
        )
