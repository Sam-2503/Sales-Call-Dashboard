"""Playbook YAML specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from call_analyser.errors import PlaybookExtractionError
from call_analyser.schemas.playbook import PlaybookChapter


class PlaybookSpec(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    source_pdf: Path
    page_offset: int = 0
    skip_pages: list[str] = Field(default_factory=list)
    chapters: list[PlaybookChapter] | None = None
    language: str = "en"

    def skip_page_numbers(self) -> set[int]:
        pages: set[int] = set()
        for value in self.skip_pages:
            try:
                start, _, end = value.partition("-")
                first = int(start)
                last = int(end or start)
            except ValueError as error:
                raise PlaybookExtractionError(f"invalid skip page range: {value}") from error
            if first < 1 or first > last:
                raise PlaybookExtractionError(f"invalid skip page range: {value}")
            pages.update(range(first, last + 1))
        return pages


def load_playbook_spec(path: str | Path) -> PlaybookSpec:
    """Load a playbook spec, resolving its PDF relative to the YAML file."""
    source = Path(path)
    try:
        raw: Any = yaml.safe_load(source.read_text())
        spec = PlaybookSpec.model_validate(raw)
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError) as error:
        raise PlaybookExtractionError(f"invalid playbook spec {source}: {error}") from error
    if not spec.source_pdf.is_absolute():
        spec = spec.model_copy(update={"source_pdf": source.parent / spec.source_pdf})
    return spec
