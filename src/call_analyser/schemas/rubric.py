"""Sales-rubric contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RubricItem(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    good_looks_like: str = Field(min_length=1)
    weight: float = Field(default=1, gt=0)
    critical: bool = False
    scoring: dict[str, float] = Field(
        default_factory=lambda: {"met": 1, "partial": 0.5, "missed": 0}
    )


class RubricCategory(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    weight: float = Field(default=1, gt=0)
    items: list[RubricItem] = Field(min_length=1)


class Rubric(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    version: str = Field(min_length=1)
    categories: list[RubricCategory] = Field(min_length=1)

    @property
    def item_ids(self) -> set[str]:
        return {item.id for category in self.categories for item in category.items}

    @model_validator(mode="after")
    def unique_ids(self) -> Rubric:
        ids = [item.id for category in self.categories for item in category.items]
        if len(ids) != len(set(ids)):
            raise ValueError("rubric item ids must be unique")
        return self
