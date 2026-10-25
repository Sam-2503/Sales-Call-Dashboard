import pytest
from langchain_core.documents import Document

from config import Settings
from rubric import load_rubric
from schemas import Evidence, MissedMoment, RubricResult
from scoring import score_rubric, select_missed_moments
from stages.grounding import GroundingResponse, ground_finding


class FakeGroundingModel:
    def with_structured_output(self, _schema: type[GroundingResponse]) -> "FakeGroundingModel":
        return self

    async def ainvoke(self, _messages: object, config: object = None) -> GroundingResponse:
        return GroundingResponse(
            why_it_hurt="It left the concern unresolved.",
            better_alternative="I hear the concern; may I ask one question?",
            cited_passage_ids=["p1", "invented"],
        )


class FakeRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, _query: str) -> list[Document]:
        self.calls += 1
        return [
            Document(
                page_content="Ask one question before presenting a solution. " * 20,
                metadata={
                    "passage_id": "p1",
                    "chapter": "Discovery",
                    "page_start": 3,
                    "page_end": 3,
                    "score": 0.9,
                },
            )
        ]


def _finding() -> MissedMoment:
    return MissedMoment(
        id="f1",
        rubric_item_id="opening_permission",
        category="opening",
        model_confidence=0.8,
        confidence="high",
        evidence=Evidence(
            turn_id="T001",
            speaker="Rep",
            role="agent",
            quote="Hi",
            start_s=0,
            end_s=1,
            match_score=100,
            attempt=0,
        ),
        what_happened="The rep did not ask permission.",
        severity="high",
    )


@pytest.mark.asyncio
async def test_grounding_allowlists_citations_and_caps_excerpts() -> None:
    retriever = FakeRetriever()
    result = await ground_finding(
        _finding(),
        retriever,
        title="Synthetic Playbook",
        model=FakeGroundingModel(),
        settings=Settings(max_excerpt_words=25),
    )
    assert result.grounded is True
    assert [ref.passage_id for ref in result.playbook_refs] == ["p1"]
    assert len(result.playbook_refs[0].excerpt.split()) <= 25
    assert retriever.calls == 1


@pytest.mark.asyncio
async def test_grounding_off_makes_no_retrieval_calls() -> None:
    retriever = FakeRetriever()
    result = await ground_finding(
        _finding(), retriever, grounding=False, model=FakeGroundingModel()
    )
    assert result.grounded is False
    assert retriever.calls == 0


def test_scoring_excludes_not_applicable_and_tracks_critical_failure() -> None:
    rubric = load_rubric("rubrics/sales_v1.yaml")
    results = [
        RubricResult(
            id="r1",
            rubric_item_id="opening_permission",
            category="opening",
            model_confidence=1,
            status="met",
            rationale="met",
            evidence=_finding().evidence,
        ),
        RubricResult(
            id="r2",
            rubric_item_id="compliance_consent",
            category="compliance",
            model_confidence=1,
            status="missed",
            rationale="missed",
        ),
        RubricResult(
            id="r3",
            rubric_item_id="opening_context",
            category="opening",
            model_confidence=1,
            status="not_applicable",
            rationale="not applicable",
        ),
    ]
    scorecard = score_rubric(results, rubric)
    assert scorecard.category_scores["opening"] == 100
    assert scorecard.critical_failures == ["compliance_consent"]


def test_selection_is_deterministic_and_capped() -> None:
    rubric = load_rubric("rubrics/sales_v1.yaml")
    findings = [
        _finding().model_copy(
            update={
                "id": f"f{index}",
                "severity": "low" if index else "critical",
            }
        )
        for index in range(3)
    ]
    selected = select_missed_moments(
        findings, rubric, Settings(max_missed_moments=2)
    )
    assert [finding.id for finding in selected] == ["f0", "f1"]
