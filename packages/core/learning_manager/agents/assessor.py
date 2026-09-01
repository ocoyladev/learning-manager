from __future__ import annotations
from datetime import date
from learning_manager.contracts import *
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.trajectory.logger import AgentTrajectory
from ._common import complete_json
from pydantic import BaseModel, Field

class ItemDraft(BaseModel): items: list[AssessmentItem] = Field(min_length=1)
class Assessor:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None: self._llm, self._trajectory = llm, trajectory
    def generate(self, concept: Concept, model_state: LearnerConceptState, n_items: int = 4) -> list[AssessmentItem]:
        return complete_json(self._llm, self._trajectory, "Assessor", "Create assessment questions.", f"Concept {concept.id}; state {model_state.model_dump()}; create {n_items} items.", ItemDraft).items
    def grade(self, items: list[AssessmentItem], answers: dict[str, str]) -> list[AssessmentResult]:
        out=[]
        for i in items:
            correct = answers.get(i.id) == i.expected
            out.append(AssessmentResult(concept_id=i.concept_id, score=float(correct), correct=int(correct), total=1, misconceptions=[] if correct else [i.explanation or "Answer indicates a misconception"], evidence=[i.id]))
        return out
    def retrieval_question(self, model: LearnerModel, graph: ConceptGraph, today: date) -> AssessmentItem:
        states = [
            model.concepts.get(
                concept.id,
                LearnerConceptState(
                    concept_id=concept.id,
                    mastery=0.0,
                    confidence=0.0,
                    state=ConceptState.UNSEEN,
                ),
            )
            for concept in graph.concepts
        ]
        state = min(states, key=lambda s: (s.mastery, -len(s.misconceptions)))
        return complete_json(self._llm, self._trajectory, "Assessor", "Create one retrieval question.", f"Concept {state.concept_id}; misconceptions: {state.misconceptions}; today: {today}", ItemDraft).items[0]
