# ruff: noqa: E501
from __future__ import annotations

from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field

from learning_manager.contracts import (
    Concept,
    ConstraintViolation,
    LearningGoal,
    LLMProvider,
    ViolationCode,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.repair import run_with_repair

from ._common import complete_json


class GoalDraft(BaseModel):
    title: str
    concepts: list[Concept] = Field(min_length=5, max_length=25)
    success_criteria: list[str] = Field(default_factory=list)


class GoalPlanningError(ValueError):
    pass


class GoalManager:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory

    def run(
        self,
        raw_goal: str,
        purpose: str,
        deadline: date,
        daily_minutes: int,
        preferred_formats: list[str],
    ) -> tuple[LearningGoal, list[Concept]]:
        user = (
            f"Goal: {raw_goal}\nPurpose: {purpose}\n"
            "Create 5-25 concepts with valid prerequisites and observable success criteria."
        )

        def produce(hint: str | None) -> GoalDraft:
            return complete_json(
                self._llm, self._trajectory, "GoalManager", "", user, GoalDraft, hint
            )

        def validate(draft: GoalDraft) -> list[ConstraintViolation]:
            try:
                ConceptGraph(draft.concepts)
            except ValueError as exc:
                return [
                    ConstraintViolation(
                        code=ViolationCode.EMPTY_SESSION,
                        message=f"Concept graph validation failed: {exc}",
                    )
                ]
            return []

        def fail() -> GoalDraft:
            raise GoalPlanningError(
                "concept graph validation failed after repair: cycle or invalid prerequisites"
            )

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda violations: "; ".join(v.message for v in violations),
            fallback=fail,
            trajectory=self._trajectory,
        )
        draft = outcome.value
        if not isinstance(draft, GoalDraft):
            raise GoalPlanningError("goal repair produced an unexpected result")
        goal = LearningGoal(
            id=str(uuid4()),
            title=raw_goal,
            purpose=purpose,
            deadline=deadline,
            daily_minutes=daily_minutes,
            preferred_formats=preferred_formats,
            success_criteria=draft.success_criteria,
        )
        self._trajectory.step("result", goal=goal, concepts=draft.concepts)
        return goal, draft.concepts
