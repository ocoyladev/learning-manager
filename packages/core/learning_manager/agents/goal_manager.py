from __future__ import annotations
from datetime import date
from uuid import uuid4
from pydantic import BaseModel, Field
from learning_manager.contracts import Concept, LearningGoal, LLMProvider
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.trajectory.logger import AgentTrajectory
from ._common import complete_json

class GoalDraft(BaseModel):
    title: str
    concepts: list[Concept] = Field(min_length=5, max_length=25)
    success_criteria: list[str] = Field(default_factory=list)

class GoalPlanningError(ValueError): pass

class GoalManager:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None: self._llm, self._trajectory = llm, trajectory
    def run(self, raw_goal: str, purpose: str, deadline: date, daily_minutes: int, preferred_formats: list[str]) -> tuple[LearningGoal, list[Concept]]:
        system = "Decompose a learning goal into an acyclic prerequisite concept graph."
        user = f"Goal: {raw_goal}\nPurpose: {purpose}\nCreate 5-25 concepts with valid prerequisites and observable success criteria."
        hint: str | None = None
        for _ in range(3):
            try:
                draft = complete_json(self._llm, self._trajectory, "GoalManager", system, user, GoalDraft, hint)
                ConceptGraph(draft.concepts)
                goal = LearningGoal(id=str(uuid4()), title=raw_goal, purpose=purpose, deadline=deadline, daily_minutes=daily_minutes, preferred_formats=preferred_formats, success_criteria=draft.success_criteria)
                self._trajectory.step("result", goal=goal, concepts=draft.concepts)
                return goal, draft.concepts
            except Exception as exc:
                hint = f"The graph is invalid: {exc}. Return an acyclic graph with existing prerequisites."
        raise GoalPlanningError(f"concept graph validation failed (cycle or invalid prerequisites): {hint}")

