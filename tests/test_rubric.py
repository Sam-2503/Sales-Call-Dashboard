from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from call_analyser.errors import RubricError
from call_analyser.rubric import load_rubric, render_rubric

RUBRIC_PATH = Path("rubrics/sales_v1.yaml")


def test_placeholder_rubric_loads_with_two_items_per_category() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    assert len(rubric.categories) == 5
    assert len(rubric.items) == 10
    assert all(sum(item.category == category.id for item in rubric.items) == 2
               for category in rubric.categories)


def _write_rubric(tmp_path: Path, **changes: object) -> Path:
    base: dict[str, object] = {
        "id": "test",
        "version": "1",
        "name": "Test",
        "categories": [{"id": "opening", "name": "Opening", "weight": 1}],
        "items": [{
            "id": "item",
            "category": "opening",
            "title": "Title",
            "description": "Description",
            "good_looks_like": "Good",
        }],
    }
    base.update(changes)
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(base))
    return path


def test_loader_rejects_duplicate_item_ids(tmp_path: Path) -> None:
    data = yaml.safe_load(_write_rubric(tmp_path).read_text())
    data["items"].append(deepcopy(data["items"][0]))
    path = tmp_path / "duplicate.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(RubricError, match="unique"):
        load_rubric(path)


def test_loader_rejects_unknown_category_reference(tmp_path: Path) -> None:
    path = _write_rubric(tmp_path, items=[{
        "id": "item",
        "category": "missing",
        "title": "Title",
        "description": "Description",
        "good_looks_like": "Good",
    }])
    with pytest.raises(RubricError, match="unknown categories"):
        load_rubric(path)


def test_loader_rejects_category_weights_that_do_not_sum_to_one(tmp_path: Path) -> None:
    path = _write_rubric(tmp_path, categories=[
        {"id": "opening", "name": "Opening", "weight": 0.5},
    ])
    with pytest.raises(RubricError, match="sum"):
        load_rubric(path)


def test_loader_rejects_non_positive_item_weights(tmp_path: Path) -> None:
    path = _write_rubric(tmp_path, items=[{
        "id": "item",
        "category": "opening",
        "title": "Title",
        "description": "Description",
        "good_looks_like": "Good",
        "weight": 0,
    }])
    with pytest.raises(RubricError, match="greater than"):
        load_rubric(path)


def test_rendering_is_stable_and_contains_every_item() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    rendered = render_rubric(rubric)
    assert rendered == render_rubric(rubric)
    assert all(item.id in rendered for item in rubric.items)
    assert "Scoring: met=1, partial=0.5, missed=0" in rendered
