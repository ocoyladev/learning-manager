from __future__ import annotations
from datetime import date
from learning_manager.contracts import AssessmentItem, Concept, LearnerModel, LearnerConceptState, ConceptState, LearningGoal, LLMProvider
from learning_manager.trajectory.logger import AgentTrajectory
from ._common import complete_json
from pydantic import BaseModel, Field

class ItemDraft(BaseModel): items: list[AssessmentItem] = Field(min_length=1)
class Diagnostician:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory
        self._concept_ids: list[str] = []
    def generate(self, goal: LearningGoal, concepts: list[Concept], n_items: int = 8) -> list[AssessmentItem]:
        self._concept_ids = [c.id for c in concepts]
        result = complete_json(self._llm, self._trajectory, "Diagnostician", "Create diagnostic multiple-choice questions.", f"Goal {goal.title}; concepts: {self._concept_ids}; create {n_items} items covering every concept.", ItemDraft)
        return result.items
    def grade(self, items: list[AssessmentItem], answers: dict[str, str], today: date) -> LearnerModel:
        by: dict[str, list[bool]] = {}
        for item in items: by.setdefault(item.concept_id, []).append(answers.get(item.id) == item.expected)
        states = {}
        for cid in self._concept_ids:
            vals = by.get(cid, [])
            if not vals:
                states[cid] = LearnerConceptState(concept_id=cid, mastery=0.0, confidence=0.0, state=ConceptState.UNSEEN)
                continue
            mastery = sum(vals) / len(vals)
            states[cid] = LearnerConceptState(concept_id=cid, mastery=mastery, confidence=1.0, state=ConceptState.MASTERED if mastery >= .85 else ConceptState.WEAK, last_assessed=today)
        self._trajectory.step("result", states=states)
        return LearnerModel(goal_id="diagnostic", concepts=states)
