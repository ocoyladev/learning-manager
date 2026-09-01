from datetime import date
import json
from pathlib import Path

from learning_manager.agents.assessor import Assessor
from learning_manager.agents.diagnostician import Diagnostician
from learning_manager.agents.goal_manager import GoalManager
from learning_manager.agents.teaching import Teacher
from learning_manager.contracts import *
from learning_manager.trajectory.logger import AgentTrajectory

class Fake:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload, self.calls = payload, []
    def complete(self, **kwargs: object) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(text="", parsed=self.payload, model="fake")

def tr(tmp_path: Path, name: str = "agent") -> AgentTrajectory:
    return AgentTrajectory(tmp_path / f"{name}.jsonl", name)

def test_diagnostician_grading_is_deterministic_and_unanswered_unseen(tmp_path: Path) -> None:
    concepts = [Concept(id="a", name="A"), Concept(id="b", name="B")]
    items = [AssessmentItem(id="q", concept_id="a", question="?", expected="yes")]
    fake = Fake({"items": [item.model_dump() for item in items]})
    agent = Diagnostician(fake, tr(tmp_path))
    agent.generate(LearningGoal(id="g", title="x", purpose="p", deadline=date(2026, 9, 2), daily_minutes=5), concepts)
    model = agent.grade(items, {}, date(2026, 9, 1))
    assert model.concepts["b"].state is ConceptState.UNSEEN
    assert len(fake.calls) == 1 and fake.calls[0]["temperature"] == 0.0

def test_assessor_and_teacher_parse_typed_outputs_and_log(tmp_path: Path) -> None:
    item = AssessmentItem(id="q", concept_id="a", question="?", expected="yes")
    fake = Fake({"items": [item.model_dump()], "block": {"kind": "concept", "concept_id": "a", "minutes": 5, "objective": "learn", "content": "text", "source_ids": []}})
    assessor = Assessor(fake, tr(tmp_path, "assessor"))
    assessor.generate(Concept(id="a", name="A"), LearnerConceptState(concept_id="a", mastery=0, confidence=0, state=ConceptState.UNSEEN))
    source = Source(id="s", url="https://x", title="X", authority=AuthorityType.BOOK, retrieved_at=date(2026, 9, 1))
    out = Teacher(fake, tr(tmp_path, "teacher")).render(SessionBlock(kind=BlockKind.CONCEPT, concept_id="a", minutes=5, objective="learn"), [source], LearnerModel(goal_id="g"), ["text"])
    assert out.content and all(call["temperature"] == 0.0 for call in fake.calls)
    records = [json.loads(line) for line in (tmp_path / "teacher.jsonl").read_text().splitlines()]
    assert records[-1]["step"] == "result"
