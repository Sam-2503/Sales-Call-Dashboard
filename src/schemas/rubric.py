"""Sales-rubric contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RubricItem(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    category: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    good_looks_like: str = Field(min_length=1)
    common_failures: list[str] = Field(default_factory=list)
    weight: float = Field(default=1, gt=0)
    critical: bool = False
    applies_when: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class RubricCategory(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1)
    weight: float = Field(default=1, gt=0)


class Rubric(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    version: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scoring: dict[str, float] = Field(
        default_factory=lambda: {"met": 1.0, "partial": 0.5, "missed": 0.0}
    )
    categories: list[RubricCategory] = Field(min_length=1)
    items: list[RubricItem] = Field(min_length=1)

    @property
    def item_ids(self) -> set[str]:
        return {item.id for item in self.items}

    @model_validator(mode="after")
    def validate_references(self) -> Rubric:
        category_ids = [category.id for category in self.categories]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("rubric category ids must be unique")
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("rubric item ids must be unique")
        if invalid := {item.category for item in self.items} - set(category_ids):
            raise ValueError(f"rubric items reference unknown categories: {sorted(invalid)}")
        if abs(sum(category.weight for category in self.categories) - 1.0) > 1e-6:
            raise ValueError("rubric category weights must sum to 1")
        if set(self.scoring) != {"met", "partial", "missed"}:
            raise ValueError("rubric scoring must define exactly met, partial, and missed")
        return self
