# ruff: noqa: E501
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from learning_manager.contracts import (
    AssessmentItem,
    Concept,
    ConceptState,
    ConstraintViolation,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    LLMProvider,
    ViolationCode,
)
from learning_manager.domain.learner_model import derive_state
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.repair import run_with_repair

from ._common import complete_json


class ItemDraft(BaseModel):
    items: list[AssessmentItem] = Field(min_length=1)


class DiagnosticGenerationError(ValueError):
    pass


class Diagnostician:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory
        self._concept_ids: list[str] = []

    def generate(
        self, goal: LearningGoal, concepts: list[Concept], n_items: int = 8
    ) -> list[AssessmentItem]:
        self._concept_ids = [c.id for c in concepts]
        user = (
            f"Goal {goal.title}; concepts: {self._concept_ids}; create {n_items} items "
            "covering every concept."
        )

        def produce(hint: str | None) -> ItemDraft:
            return complete_json(
                self._llm, self._trajectory, "Diagnostician", "", user, ItemDraft, hint
            )

        def validate(result: ItemDraft) -> list[ConstraintViolation]:
            returned_ids = {item.concept_id for item in result.items}
            unknown = returned_ids - set(self._concept_ids)
            missing = set(self._concept_ids) - returned_ids
            violations: list[ConstraintViolation] = []
            for concept_id in sorted(unknown):
                violations.append(
                    ConstraintViolation(
                        code=ViolationCode.UNKNOWN_CONCEPT,
                        concept_id=concept_id,
                        message=f"Diagnostic item references unknown concept {concept_id}",
                    )
                )
            for concept_id in sorted(missing):
                violations.append(
                    ConstraintViolation(
                        code=ViolationCode.EMPTY_SESSION,
                        concept_id=concept_id,
                        message=f"Diagnostic does not cover concept {concept_id}",
                    )
                )
            return violations

        def fail() -> ItemDraft:
            raise DiagnosticGenerationError(
                "diagnostic items did not cover every concept after repair"
            )

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda violations: "; ".join(v.message for v in violations),
            fallback=fail,
            trajectory=self._trajectory,
        )
        result = outcome.value
        if not isinstance(result, ItemDraft):
            raise DiagnosticGenerationError("diagnostic repair produced an unexpected result")
        return result.items

    def grade(
        self, items: list[AssessmentItem], answers: dict[str, str], today: date
    ) -> LearnerModel:
        by: dict[str, list[bool]] = {}
        for item in items:
            answer = answers.get(item.id)
            if answer is not None:
                by.setdefault(item.concept_id, []).append(answer == item.expected)
        states = {}
        for cid in self._concept_ids:
            vals = by.get(cid, [])
            if not vals:
                states[cid] = LearnerConceptState(
                    concept_id=cid, mastery=0.0, confidence=0.0, state=ConceptState.UNSEEN
                )
                continue
            mastery = sum(vals) / len(vals)
            states[cid] = LearnerConceptState(
                concept_id=cid,
                mastery=mastery,
                confidence=1.0,
                state=derive_state(mastery, 1.0, None, today),
                last_assessed=today,
            )
        self._trajectory.step("grading_result", states=states)
        return LearnerModel(goal_id="diagnostic", concepts=states)
