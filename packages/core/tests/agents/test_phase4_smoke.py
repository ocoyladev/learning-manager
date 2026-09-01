# ruff: noqa: E501,F403,F405,I001
import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from learning_manager.agents.assessor import Assessor
from learning_manager.agents.diagnostician import Diagnostician
from learning_manager.agents.teaching import Teacher
from learning_manager.agents.curriculum_planner import CurriculumPlanner
from learning_manager.agents.goal_manager import GoalManager, GoalPlanningError
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
    assert Researcher(Knowledge(), Fake({"source_ids": ["src"]}), trajectory).research("pods") == [
        _source()
    ]
    records = [
        json.loads(line) for line in (tmp_path / "Researcher.jsonl").read_text().splitlines()
    ]
    assert records[-1]["step"] == "result"


def test_researcher_uses_one_llm_call_for_a_valid_provider_source_selection(
    tmp_path: Path,
) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            assert topic == "pods"
            assert k == 3
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    fake = Fake({"source_ids": ["src"]})
    trajectory = tr(tmp_path, "Researcher")
    result = Researcher(Knowledge(), fake, trajectory).research("pods", k=3)

    assert result == [_source()]
    assert len(fake.calls) == 1
    assert fake.calls[0]["temperature"] == 0.0
    records = [
        json.loads(line) for line in (tmp_path / "Researcher.jsonl").read_text().splitlines()
    ]
    assert [record["step"] for record in records] == [
        "provider_retrieval",
        "llm_call",
        "llm_result",
        "validation",
        "result",
        "result",
    ]
    assert records[-1]["sources"] == [_source().model_dump(mode="json")]


def test_researcher_repairs_a_malformed_source_selection(tmp_path: Path) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    fake = SequencedFake([{"source_ids": "src"}, {"source_ids": ["src"]}])
    trajectory = tr(tmp_path, "Researcher")
    try:
        result = Researcher(Knowledge(), fake, trajectory).research("pods")
    except ValidationError:
        result = None

    assert result == [_source()]
    records = [
        json.loads(line) for line in (tmp_path / "Researcher.jsonl").read_text().splitlines()
    ]
    assert [record["step"] for record in records].count("validation") == 2
    assert any(record["step"] == "repair_prompt" for record in records)


def test_researcher_repairs_unknown_selected_source_ids(tmp_path: Path) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    fake = SequencedFake([{"source_ids": ["outside"]}, {"source_ids": ["src"]}])
    trajectory = tr(tmp_path, "Researcher")
    result = Researcher(Knowledge(), fake, trajectory).research("pods")

    assert result == [_source()]
    records = [
        json.loads(line) for line in (tmp_path / "Researcher.jsonl").read_text().splitlines()
    ]
    validation = next(record for record in records if record["step"] == "validation")
    assert validation["violations"][0]["code"] == "UNSOURCED_CLAIM"
    assert any(record["step"] == "repair_prompt" for record in records)


def test_researcher_falls_back_to_provider_sources_after_persistent_unknown_ids(
    tmp_path: Path,
) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    trajectory = tr(tmp_path, "Researcher")
    result = Researcher(
        Knowledge(), SequencedFake([{"source_ids": ["outside"]}]), trajectory
    ).research("pods")

    assert result == [_source()]
    records = [
        json.loads(line) for line in (tmp_path / "Researcher.jsonl").read_text().splitlines()
    ]
    assert [record["step"] for record in records].count("validation") == 3
    assert any(record["step"] == "fallback" for record in records)


def test_goal_manager_reports_a_cycle_after_exhausting_repair(tmp_path: Path) -> None:
    cyclic = {
        "title": "x",
        "success_criteria": ["demonstrate x"],
        "concepts": [
            {
                "id": f"c{i}",
                "name": f"C{i}",
                "prerequisites": ["c1"] if i == 0 else (["c0"] if i == 1 else []),
            }
            for i in range(5)
        ],
    }

    with pytest.raises(GoalPlanningError, match="cycle"):
        GoalManager(SequencedFake([cyclic]), tr(tmp_path, "GoalManager")).run(
            "goal", "purpose", date(2026, 9, 20), 25, ["text"]
        )


def test_planner_accepts_valid_first_attempt_and_uses_injected_today(tmp_path: Path) -> None:
    decision, outcome = CurriculumPlanner(
        Fake(_decision("pods")), tr(tmp_path, "CurriculumPlanner")
    ).next_session(_goal(), LearnerModel(goal_id="g"), _graph(), [_source()], date(2026, 9, 1))

    assert outcome.attempts == 1
    assert not outcome.used_fallback
    assert decision.session_date == date(2026, 9, 1)
    assert len(decision.rationale) > 20
    assert "pods" in decision.rationale


def test_planner_repairs_a_prerequisite_violation_on_second_attempt(tmp_path: Path) -> None:
    decision, outcome = CurriculumPlanner(
        SequencedFake([_decision("services"), _decision("pods")]),
        tr(tmp_path, "CurriculumPlanner"),
    ).next_session(_goal(), LearnerModel(goal_id="g"), _graph(), [_source()], date(2026, 9, 5))

    assert outcome.attempts == 2
    assert outcome.violations_per_attempt[0][0].code.value == "PREREQ_VIOLATION"
    assert (
        validate_session(decision, _goal(), LearnerModel(goal_id="g"), _graph(), date(2026, 9, 5))
        == []
    )


def test_diagnostician_assigns_mastery_to_all_covered_concepts_for_correct_answers(
    tmp_path: Path,
) -> None:
    items = [
        AssessmentItem(id="pods", concept_id="pods", question="?", expected="yes"),
        AssessmentItem(id="services", concept_id="services", question="?", expected="yes"),
    ]
    agent = Diagnostician(Fake({"items": [item.model_dump() for item in items]}), tr(tmp_path))
    agent.generate(_goal(), _graph().concepts)

    model = agent.grade(items, {item.id: item.expected for item in items}, date(2026, 9, 1))

    assert all(state.mastery >= 0.85 for state in model.concepts.values())


def test_assessor_only_records_misconceptions_for_wrong_answers(tmp_path: Path) -> None:
    items = [
        AssessmentItem(id="right", concept_id="pods", question="?", expected="yes"),
        AssessmentItem(
            id="wrong",
            concept_id="services",
            question="?",
            expected="yes",
            explanation="Services route traffic.",
        ),
    ]

    results = Assessor(Fake({}), tr(tmp_path)).grade(items, {"right": "yes", "wrong": "no"})

    assert results[0].misconceptions == []
    assert results[1].misconceptions == ["Services route traffic."]


def test_assessor_repairs_generated_items_that_target_another_concept(tmp_path: Path) -> None:
    wrong = AssessmentItem(id="wrong", concept_id="services", question="?", expected="yes")
    repaired = AssessmentItem(id="right", concept_id="pods", question="?", expected="yes")
    items = Assessor(
        SequencedFake([{"items": [wrong.model_dump()]}, {"items": [repaired.model_dump()]}]),
        tr(tmp_path),
    ).generate(
        Concept(id="pods", name="Pods"),
        LearnerConceptState(concept_id="pods", mastery=0, confidence=0, state=ConceptState.UNSEEN),
    )

    assert [item.concept_id for item in items] == ["pods"]


def test_teacher_falls_back_for_empty_content_and_unavailable_citations(tmp_path: Path) -> None:
    invalid_block = {
        "block": {
            "kind": "concept",
            "concept_id": "pods",
            "minutes": 5,
            "objective": "learn pods",
            "content": "",
            "source_ids": ["outside"],
        }
    }
    block = SessionBlock(
        kind=BlockKind.CONCEPT,
        concept_id="pods",
        minutes=5,
        objective="Learn pods",
    )

    result = Teacher(Fake(invalid_block), tr(tmp_path)).render(
        block, [_source()], LearnerModel(goal_id="g"), ["text"]
    )

    assert result.content
    assert set(result.source_ids) <= {"src"}


def test_every_llm_backed_agent_uses_its_versioned_system_prompt(tmp_path: Path) -> None:
    prompts = Path(__file__).parents[2] / "learning_manager" / "agents" / "prompts"
    concept = Concept(id="pods", name="Pods")
    assessment_item = AssessmentItem(id="pods", concept_id="pods", question="?", expected="yes")
    valid_goal = {
        "title": "x",
        "concepts": [{"id": f"c{i}", "name": f"C{i}"} for i in range(5)],
    }

    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    calls: list[tuple[Fake, str]] = []
    goal_fake = Fake(valid_goal)
    GoalManager(goal_fake, tr(tmp_path, "GoalManager")).run(
        "goal", "purpose", date(2026, 9, 20), 25, ["text"]
    )
    calls.append((goal_fake, "goal_manager.md"))
    diagnostician_fake = Fake({"items": [assessment_item.model_dump()]})
    Diagnostician(diagnostician_fake, tr(tmp_path, "Diagnostician")).generate(_goal(), [concept])
    calls.append((diagnostician_fake, "diagnostician.md"))
    researcher_fake = Fake({"source_ids": ["src"]})
    Researcher(Knowledge(), researcher_fake, tr(tmp_path, "Researcher")).research("pods")
    calls.append((researcher_fake, "researcher.md"))
    planner_fake = Fake(_decision("pods"))
    CurriculumPlanner(planner_fake, tr(tmp_path, "CurriculumPlanner")).next_session(
        _goal(), LearnerModel(goal_id="g"), _graph(), [_source()], date(2026, 9, 1)
    )
    calls.append((planner_fake, "curriculum_planner.md"))
    assessor_fake = Fake({"items": [assessment_item.model_dump()]})
    Assessor(assessor_fake, tr(tmp_path, "Assessor")).generate(
        concept,
        LearnerConceptState(concept_id="pods", mastery=0, confidence=0, state=ConceptState.UNSEEN),
    )
    calls.append((assessor_fake, "assessor.md"))
    teacher_fake = Fake(
        {
            "block": {
                "kind": "concept",
                "concept_id": "pods",
                "minutes": 5,
                "objective": "Learn pods",
                "content": "Learn from the source.",
                "source_ids": ["src"],
            }
        }
    )
    Teacher(teacher_fake, tr(tmp_path, "Teacher")).render(
        SessionBlock(kind=BlockKind.CONCEPT, concept_id="pods", minutes=5, objective="Learn pods"),
        [_source()],
        LearnerModel(goal_id="g"),
        ["text"],
    )
    calls.append((teacher_fake, "teaching.md"))

    for fake, prompt_name in calls:
        assert fake.calls
        assert fake.calls[0]["system"] == (prompts / prompt_name).read_text(encoding="utf-8")


def test_each_of_the_five_agents_records_a_call_and_final_result(tmp_path: Path) -> None:
    class Knowledge:
        def research(self, topic: str, *, k: int = 8) -> list[Source]:
            return [_source()]

        def fetch(self, source_id: str) -> str:
            return source_id

    goal_payload = {"title": "x", "concepts": [{"id": f"c{i}", "name": f"C{i}"} for i in range(5)]}
    assessment_item = AssessmentItem(id="pods", concept_id="pods", question="?", expected="yes")
    trajectories = {
        "GoalManager": tr(tmp_path, "GoalManager"),
        "Diagnostician": tr(tmp_path, "Diagnostician"),
        "Researcher": tr(tmp_path, "Researcher"),
        "CurriculumPlanner": tr(tmp_path, "CurriculumPlanner"),
        "Assessor": tr(tmp_path, "Assessor"),
    }
    GoalManager(Fake(goal_payload), trajectories["GoalManager"]).run(
        "goal", "purpose", date(2026, 9, 20), 25, ["text"]
    )
    Diagnostician(
        Fake({"items": [assessment_item.model_dump()]}), trajectories["Diagnostician"]
    ).generate(_goal(), [Concept(id="pods", name="Pods")])
    Researcher(Knowledge(), Fake({"source_ids": ["src"]}), trajectories["Researcher"]).research(
        "pods"
    )
    CurriculumPlanner(Fake(_decision("pods")), trajectories["CurriculumPlanner"]).next_session(
        _goal(), LearnerModel(goal_id="g"), _graph(), [_source()], date(2026, 9, 1)
    )
    Assessor(Fake({"items": [assessment_item.model_dump()]}), trajectories["Assessor"]).generate(
        Concept(id="pods", name="Pods"),
        LearnerConceptState(concept_id="pods", mastery=0, confidence=0, state=ConceptState.UNSEEN),
    )

    for agent in trajectories:
        records = [
            json.loads(line) for line in (tmp_path / f"{agent}.jsonl").read_text().splitlines()
        ]
        steps = {record["step"] for record in records}
        assert "llm_call" in steps, agent
        assert "result" in steps, agent
