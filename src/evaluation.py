"""Deterministic offline evaluation of public call reports."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from errors import PlaybookExtractionError
from schemas import CallReport


class EvaluationCase(BaseModel):
    """Expected properties for one report evaluation case."""

    id: str = Field(min_length=1)
    report: Path
    expected_rubric_statuses: dict[str, str] = Field(default_factory=dict)
    expected_missed_rubric_items: set[str] = Field(default_factory=set)
    expected_overall_score: float | None = Field(default=None, ge=0, le=100)


class CaseEvaluation(BaseModel):
    id: str
    rubric_status_accuracy: float
    missed_moment_recall: float
    evidence_validity: float
    score_absolute_error: float | None = None


class EvaluationSummary(BaseModel):
    """Aggregate metrics; all values are bounded and JSON-serializable."""

    n: int = Field(ge=0)
    rubric_status_accuracy: float = Field(ge=0, le=1)
    missed_moment_recall: float = Field(ge=0, le=1)
    evidence_validity: float = Field(ge=0, le=1)
    mean_score_absolute_error: float | None = Field(default=None, ge=0)
    cases: list[CaseEvaluation] = Field(default_factory=list)


def load_cases(path: str | Path) -> list[EvaluationCase]:
    """Load evaluation cases from a YAML list."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise PlaybookExtractionError(f"could not read evaluation cases: {error}") from error
    if not isinstance(raw, list):
        raise PlaybookExtractionError("evaluation cases must be a YAML list")
    try:
        return [EvaluationCase.model_validate(case) for case in raw]
    except ValueError as error:
        raise PlaybookExtractionError(f"invalid evaluation case: {error}") from error


def _load_report(case: EvaluationCase, base_path: Path) -> CallReport:
    report_path = case.report if case.report.is_absolute() else base_path / case.report
    try:
        return CallReport.model_validate_json(report_path.read_text())
    except (OSError, UnicodeError, ValueError) as error:
        raise PlaybookExtractionError(f"could not read report {report_path}: {error}") from error


def evaluate_cases(cases: list[EvaluationCase], base_path: str | Path = ".") -> EvaluationSummary:
    """Evaluate reports without model calls or mutation."""
    root = Path(base_path)
    results: list[CaseEvaluation] = []
    score_errors: list[float] = []
    for case in cases:
        report = _load_report(case, root)
        actual = {result.rubric_item_id: result.status for result in report.rubric_results}
        status_pairs = [
            actual[item_id] == expected
            for item_id, expected in case.expected_rubric_statuses.items()
            if item_id in actual
        ]
        status_accuracy = (
            sum(status_pairs) / len(case.expected_rubric_statuses)
            if case.expected_rubric_statuses
            else 1.0
        )
        expected_missed = case.expected_missed_rubric_items
        actual_missed = {finding.rubric_item_id for finding in report.missed_moments}
        recall = (
            len(expected_missed & actual_missed) / len(expected_missed)
            if expected_missed
            else 1.0
        )
        evidence_total = len(report.rubric_results) + len(report.missed_moments)
        evidence_validity = (
            sum(
                item.evidence is not None
                for item in [*report.rubric_results, *report.missed_moments]
            )
            / evidence_total
            if evidence_total
            else 1.0
        )
        score_error = (
            abs((report.scorecard.overall_score or 0) - case.expected_overall_score)
            if case.expected_overall_score is not None and report.scorecard
            else None
        )
        if score_error is not None:
            score_errors.append(score_error)
        results.append(
            CaseEvaluation(
                id=case.id,
                rubric_status_accuracy=status_accuracy,
                missed_moment_recall=recall,
                evidence_validity=evidence_validity,
                score_absolute_error=score_error,
            )
        )
    count = len(results)
    return EvaluationSummary(
        n=count,
        rubric_status_accuracy=sum(item.rubric_status_accuracy for item in results) / count
        if count
        else 0,
        missed_moment_recall=sum(item.missed_moment_recall for item in results) / count
        if count
        else 0,
        evidence_validity=sum(item.evidence_validity for item in results) / count if count else 0,
        mean_score_absolute_error=sum(score_errors) / len(score_errors) if score_errors else None,
        cases=results,
    )
