"""Deterministic rubric scoring and missed-finding selection."""

from __future__ import annotations

from call_analyser.config import Settings
from call_analyser.schemas.findings import MissedMoment, RubricResult
from call_analyser.schemas.report import Scorecard
from call_analyser.schemas.rubric import Rubric

SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE_WEIGHT = {"low": 0.5, "medium": 0.75, "high": 1.0}


def select_missed_moments(
    findings: list[MissedMoment], rubric: Rubric, settings: Settings | None = None
) -> list[MissedMoment]:
    """Rank and cap findings by severity, rubric weight, and confidence."""
    settings = settings or Settings()
    weights = {item.id: item.weight for item in rubric.items}
    ranked = sorted(
        findings,
        key=lambda finding: (
            -SEVERITY_WEIGHT[finding.severity]
            * weights.get(finding.rubric_item_id, 0)
            * CONFIDENCE_WEIGHT[finding.confidence],
            finding.id,
        ),
    )
    return ranked[: settings.max_missed_moments]


def _category_scores(results: list[RubricResult], rubric: Rubric) -> dict[str, float]:
    item_map = {item.id: item for item in rubric.items}
    category_values: dict[str, list[tuple[float, float]]] = {}
    for result in results:
        if result.status == "not_applicable" or result.rubric_item_id not in item_map:
            continue
        item = item_map[result.rubric_item_id]
        category_values.setdefault(item.category, []).append(
            (rubric.scoring[result.status], item.weight)
        )
    return {
        category: sum(value * weight for value, weight in values)
        / sum(weight for _, weight in values)
        for category, values in category_values.items()
    }


def score_rubric(results: list[RubricResult], rubric: Rubric) -> Scorecard:
    """Compute weighted category and overall scores, excluding not-applicable items."""
    category_scores = _category_scores(results, rubric)
    category_weights = {category.id: category.weight for category in rubric.categories}
    applicable_weight = sum(category_weights.get(category, 0) for category in category_scores)
    overall = (
        sum(score * category_weights[category] for category, score in category_scores.items())
        / applicable_weight
        * 100
        if applicable_weight
        else None
    )
    item_map = {item.id: item for item in rubric.items}
    critical_failures = [
        result.rubric_item_id
        for result in results
        if result.status == "missed"
        and result.rubric_item_id in item_map
        and item_map[result.rubric_item_id].critical
    ]
    return Scorecard(
        overall_score=overall,
        category_scores={category: score * 100 for category, score in category_scores.items()},
        critical_failures=critical_failures,
    )
