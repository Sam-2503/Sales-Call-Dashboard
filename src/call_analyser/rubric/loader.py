"""Load and render validated rubric YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from call_analyser.errors import RubricError
from call_analyser.schemas.rubric import Rubric


def load_rubric(path: str | Path) -> Rubric:
    """Load a rubric from YAML and raise a user-facing error for any invalid input."""
    source = Path(path)
    try:
        raw: Any = yaml.safe_load(source.read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise RubricError(f"could not read rubric {source}: {error}") from error
    if not isinstance(raw, dict):
        raise RubricError(f"rubric {source} must contain a YAML mapping")
    try:
        return Rubric.model_validate(raw)
    except ValidationError as error:
        raise RubricError(f"invalid rubric {source}: {error}") from error


def render_rubric(rubric: Rubric) -> str:
    """Render the complete rubric in stable order for model prompts."""
    lines = [
        f"Rubric: {rubric.name} (id={rubric.id}, version={rubric.version})",
        "Scoring: " + ", ".join(
            f"{status}={rubric.scoring[status]:g}"
            for status in ("met", "partial", "missed")
        ),
    ]
    for category in rubric.categories:
        lines.extend(
            [
                "",
                f"Category: {category.name} (id={category.id}, weight={category.weight:g})",
            ]
        )
        for item in (item for item in rubric.items if item.category == category.id):
            lines.extend(
                [
                    f"- {item.id}: {item.title} (weight={item.weight:g}, "
                    f"critical={'yes' if item.critical else 'no'})",
                    f"  Description: {item.description}",
                    f"  Good looks like: {item.good_looks_like}",
                    "  Common failures: "
                    + (", ".join(item.common_failures) if item.common_failures else "none"),
                ]
            )
            if item.applies_when:
                lines.append(f"  Applies when: {item.applies_when}")
            if item.source_refs:
                lines.append("  Source references: " + ", ".join(item.source_refs))
    return "\n".join(lines) + "\n"
