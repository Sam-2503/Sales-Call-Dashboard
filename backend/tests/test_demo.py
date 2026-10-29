from call_analyser.rubric import load_rubric

from analyser_api.config import Settings
from analyser_api.services.demo import _report


def test_demo_report_is_valid_and_has_trends_data() -> None:
    settings = Settings(_env_file=None)
    rubric = load_rubric(settings.rubric_path)
    report = _report(rubric, settings, score=72, outcome="advanced", index=0)

    assert report.status == "ok"
    assert report.scorecard is not None
    assert report.scorecard.overall_score is not None
    assert set(report.scorecard.category_scores) == {category.id for category in rubric.categories}
    assert len(report.rubric_results) == len(rubric.items)
    assert all(result.id for result in report.rubric_results)
    assert report.meta.rubric_id == rubric.id
    assert report.meta.usage["est_cost_usd"] == 0
