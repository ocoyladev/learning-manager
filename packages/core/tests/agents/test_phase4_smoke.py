# ruff: noqa: E501,F403,F405,I001
import json
from datetime import date
from pathlib import Path

from learning_manager.agents.assessor import Assessor
from learning_manager.agents.diagnostician import Diagnostician
from learning_manager.agents.teaching import Teacher
from learning_manager.agents.curriculum_planner import CurriculumPlanner
from learning_manager.agents.goal_manager import GoalManager
from learning_manager.agents.researcher import Researcher
from learning_manager.contracts import (
    AssessmentItem,
    AuthorityType,
    BlockKind,
    Concept,
    ConceptState,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    LLMResponse,
    SessionBlock,
    Source,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.verification.constraints import validate_session
from learning_manager.trajectory.logger import AgentTrajectory


class Fake:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload, self.calls = payload, []

    def complete(self, **kwargs: object) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(text="", parsed=self.payload, model="fake")


class SequencedFake(Fake):
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        super().__init__(payloads[0])
        self._payloads = payloads

    def complete(self, **kwargs: object) -> LLMResponse:
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self._payloads) - 1)
        return LLMResponse(
            text="",
            parsed=self._payloads[index],
            model="fake-model",
            input_tokens=11,
            output_tokens=7,
            cost_usd=0.02,
            latency_ms=15,
            cache_hit=True,
        )


def tr(tmp_path: Path, name: str = "agent") -> AgentTrajectory:
    return AgentTrajectory(tmp_path / f"{name}.jsonl", name)


def test_diagnostician_grading_is_deterministic_and_unanswered_unseen(tmp_path: Path) -> None:
    concepts = [Concept(id="a", name="A"), Concept(id="b", name="B")]
    items = [AssessmentItem(id="q", concept_id="a", question="?", expected="yes")]
    covered_items = [
        *items,
        AssessmentItem(id="q-b", concept_id="b", question="?", expected="yes"),
    ]
    fake = Fake({"items": [item.model_dump() for item in covered_items]})
    agent = Diagnostician(fake, tr(tmp_path))
    agent.generate(
        LearningGoal(id="g", title="x", purpose="p", deadline=date(2026, 9, 2), daily_minutes=5),
        concepts,
    )
    model = agent.grade(items, {}, date(2026, 9, 1))
    assert model.concepts["b"].state is ConceptState.UNSEEN
    assert len(fake.calls) == 1 and fake.calls[0]["temperature"] == 0.0


def test_assessor_and_teacher_parse_typed_outputs_and_log(tmp_path: Path) -> None:
    item = AssessmentItem(id="q", concept_id="a", question="?", expected="yes")
    fake = Fake(
        {
            "items": [item.model_dump()],
            "block": {
                "kind": "concept",
                "concept_id": "a",
                "minutes": 5,
                "objective": "learn",
                "content": "text",
                "source_ids": [],
            },
        }
    )
    assessor = Assessor(fake, tr(tmp_path, "assessor"))
    assessor.generate(
        Concept(id="a", name="A"),
        LearnerConceptState(concept_id="a", mastery=0, confidence=0, state=ConceptState.UNSEEN),
    )
    source = Source(
        id="s",
        url="https://x",
        title="X",
        authority=AuthorityType.BOOK,
        retrieved_at=date(2026, 9, 1),
    )
    out = Teacher(fake, tr(tmp_path, "teacher")).render(
        SessionBlock(kind=BlockKind.CONCEPT, concept_id="a", minutes=5, objective="learn"),
        [source],
        LearnerModel(goal_id="g"),
        ["text"],
    )
    assert out.content and all(call["temperature"] == 0.0 for call in fake.calls)
    records = [json.loads(line) for line in (tmp_path / "teacher.jsonl").read_text().splitlines()]
    assert records[-1]["step"] == "result"


def test_retrieval_handles_concept_absent_from_learner_model(tmp_path: Path) -> None:
    item = AssessmentItem(id="q", concept_id="a", question="?", expected="yes")
    fake = Fake({"items": [item.model_dump()]})
    out = Assessor(fake, tr(tmp_path)).retrieval_question(
        LearnerModel(goal_id="g"),
        __import__("learning_manager.domain.concept_graph", fromlist=["ConceptGraph"]).ConceptGraph(
            [Concept(id="a", name="A")]
        ),
        date(2026, 9, 1),
    )
    assert out.concept_id == "a"


def _goal() -> LearningGoal:
    return LearningGoal(
        id="g", title="Kubernetes", purpose="practice", deadline=date(2026, 9, 20), daily_minutes=25
    )


def _graph() -> ConceptGraph:
    return ConceptGraph(
        [
            Concept(id="pods", name="Pods"),
            Concept(id="services", name="Services", prerequisites=["pods"]),
        ]
    )


def _source() -> Source:
    return Source(
        id="src",
        url="https://example.test",
        title="Source",
        authority=AuthorityType.OFFICIAL,
        retrieved_at=date(2026, 9, 1),
    )


def _decision(concept_id: str, source_id: str = "src") -> dict[str, object]:
    return {
        "session_date": "2026-09-05",
        "blocks": [
            {
                "kind": "concept",
                "concept_id": concept_id,
                "minutes": 25,
                "objective": "Study",
                "source_ids": [source_id],
            }
        ],
        "total_minutes": 25,
        "rationale": f"Practice {concept_id} based on current evidence.",
        "deadline_status": "on_track",
    }


def test_planner_fallback_is_valid_for_due_review_and_uses_supplied_source(tmp_path: Path) -> None:
    model = LearnerModel(
        goal_id="g",
        concepts={
            "pods": LearnerConceptState(
                concept_id="pods",
                mastery=0.4,
                confidence=0.5,
                state=ConceptState.REVIEW_DUE,
                next_review=date(2026, 9, 5),
            )
        },
    )
    planner = CurriculumPlanner(
        SequencedFake([_decision("missing", "outside")]), tr(tmp_path, "CurriculumPlanner")
    )
    decision, outcome = planner.next_session(
        _goal(), model, _graph(), [_source()], date(2026, 9, 5)
    )
    assert outcome.used_fallback
    assert validate_session(decision, _goal(), model, _graph(), date(2026, 9, 5)) == []
    assert {source_id for block in decision.blocks for source_id in block.source_ids} <= {"src"}


def test_diagnostician_repairs_items_that_do_not_cover_every_concept(tmp_path: Path) -> None:
    item_a = AssessmentItem(id="a", concept_id="pods", question="?", expected="yes")
    item_b = AssessmentItem(id="b", concept_id="services", question="?", expected="yes")
    fake = SequencedFake(
        [{"items": [item_a.model_dump()]}, {"items": [item_a.model_dump(), item_b.model_dump()]}]
    )
    items = Diagnostician(fake, tr(tmp_path, "Diagnostician")).generate(_goal(), _graph().concepts)
    assert {item.concept_id for item in items} == {"pods", "services"}
    assert len(fake.calls) == 2


def test_retrieval_prefers_seen_then_misconception_then_oldest_and_forces_target(
    tmp_path: Path,
) -> None:
    graph = _graph()
    model = LearnerModel(
        goal_id="g",
        concepts={
            "pods": LearnerConceptState(
                concept_id="pods",
                mastery=0.2,
                confidence=0.5,
                state=ConceptState.WEAK,
                last_assessed=date(2026, 9, 4),
            ),
            "services": LearnerConceptState(
                concept_id="services",
                mastery=0.2,
                confidence=0.5,
                state=ConceptState.WEAK,
                last_assessed=date(2026, 9, 1),
                misconceptions=["ClusterIP"],
            ),
        },
    )
    wrong_target = AssessmentItem(id="q", concept_id="pods", question="?", expected="yes")
    fake = SequencedFake([{"items": [wrong_target.model_dump()]}])
    item = Assessor(fake, tr(tmp_path, "Assessor")).retrieval_question(
        model, graph, date(2026, 9, 5)
    )
    assert item.concept_id == "services"
    assert "ClusterIP" in str(fake.calls[0]["user"])


def test_goal_manager_retries_invalid_graph_and_records_llm_metadata(tmp_path: Path) -> None:
    cyclic = {
        "title": "x",
        "success_criteria": [],
        "concepts": [
            {
                "id": f"c{i}",
                "name": f"C{i}",
                "prerequisites": ["c1"] if i == 0 else (["c0"] if i == 1 else []),
            }
            for i in range(5)
        ],
    }
    valid = {**cyclic, "concepts": [{"id": f"c{i}", "name": f"C{i}"} for i in range(5)]}
    trajectory = tr(tmp_path, "GoalManager")
    goal, concepts = GoalManager(SequencedFake([cyclic, valid]), trajectory).run(
        "goal", "purpose", date(2026, 9, 20), 25, ["text"]
    )
    assert goal.deadline == date(2026, 9, 20) and len(concepts) == 5
    records = [
        json.loads(line) for line in (tmp_path / "GoalManager.jsonl").read_text().splitlines()
    ]
    assert records[0]["input_tokens"] == 11 and records[0]["latency_ms"] == 15


def test_researcher_records_deterministic_research_result(tmp_path: Path) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    trajectory = tr(tmp_path, "Researcher")
    assert Researcher(Knowledge(), Fake({}), trajectory).research("pods") == [_source()]
    assert json.loads((tmp_path / "Researcher.jsonl").read_text())["step"] == "research_result"
