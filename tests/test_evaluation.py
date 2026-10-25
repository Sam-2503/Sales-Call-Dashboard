from pathlib import Path

from call_analyser.evaluation import evaluate_cases, load_cases


def test_evaluation_handles_empty_cases() -> None:
    summary = evaluate_cases([])

    assert summary.n == 0
    assert summary.rubric_status_accuracy == 0
    assert summary.mean_score_absolute_error is None


def test_evaluation_loads_fixture_case() -> None:
    root = Path(__file__).parents[1]
    cases = load_cases(root / "eval" / "report_cases.yaml")

    summary = evaluate_cases(cases, root / "eval")

    assert summary.n == 1
    assert summary.cases[0].id == "synthetic-short"
    assert summary.evidence_validity == 1
