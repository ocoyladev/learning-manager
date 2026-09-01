from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from learning_manager.contracts import (
    AssessmentItem,
    AssessmentResult,
    Concept,
    ConceptState,
    ConstraintViolation,
    LearnerConceptState,
    LearnerModel,
    LLMProvider,
    ViolationCode,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.repair import run_with_repair

from ._common import complete_json


class ItemDraft(BaseModel):
    items: list[AssessmentItem] = Field(min_length=1)


class AssessmentGenerationError(ValueError):
    pass


class Assessor:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory

    def generate(
        self, concept: Concept, model_state: LearnerConceptState, n_items: int = 4
    ) -> list[AssessmentItem]:
        user = f"Concept {concept.id}; state {model_state.model_dump()}; create {n_items} items."

        def produce(hint: str | None) -> ItemDraft:
            return complete_json(self._llm, self._trajectory, "Assessor", "", user, ItemDraft, hint)

        def validate(result: ItemDraft) -> list[ConstraintViolation]:
            if all(item.concept_id == concept.id for item in result.items):
                return []
            return [
                ConstraintViolation(
                    code=ViolationCode.UNKNOWN_CONCEPT,
                    concept_id=concept.id,
                    message=f"Every assessment item must target concept {concept.id}",
                )
            ]

        def fail() -> ItemDraft:
            raise AssessmentGenerationError("assessment items did not target the requested concept")

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda _: f"Every item must target concept {concept.id}",
            fallback=fail,
            trajectory=self._trajectory,
        )
        result = outcome.value
        if not isinstance(result, ItemDraft):
            raise AssessmentGenerationError("assessment repair produced an unexpected result")
        return result.items

    def grade(self, items: list[AssessmentItem], answers: dict[str, str]) -> list[AssessmentResult]:
        out: list[AssessmentResult] = []
        for i in items:
            correct = answers.get(i.id) == i.expected
            out.append(
                AssessmentResult(
                    concept_id=i.concept_id,
                    score=float(correct),
                    correct=int(correct),
                    total=1,
                    misconceptions=[]
                    if correct
                    else [i.explanation or "Answer indicates a misconception"],
                    evidence=[i.id],
                )
            )
        self._trajectory.step("grading_result", results=out)
        return out

    def retrieval_question(
        self, model: LearnerModel, graph: ConceptGraph, today: date
    ) -> AssessmentItem:
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
        seen_states = [
            state
            for state in states
            if (
                state.state is not ConceptState.UNSEEN
                or state.last_seen is not None
                or state.last_assessed is not None
            )
        ]
        candidates = seen_states or states
        state = min(
            candidates,
            key=lambda candidate: (
                candidate.mastery,
                0 if candidate.misconceptions else 1,
                candidate.last_assessed or date.min,
                candidate.concept_id,
            ),
        )
        item = complete_json(
            self._llm,
            self._trajectory,
            "Assessor",
            "",
            f"Concept {state.concept_id}; misconceptions: {state.misconceptions}; today: {today}",
            ItemDraft,
        ).items[0]
        target_item = item.model_copy(update={"concept_id": state.concept_id})
        self._trajectory.step("result", item=target_item)
        return target_item
