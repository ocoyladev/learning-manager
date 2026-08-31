"""Deterministic validation of curriculum session constraints."""

from __future__ import annotations

from datetime import date

from learning_manager.contracts import (
    MASTERY_THRESHOLD,
    ConstraintViolation,
    LearnerModel,
    LearningGoal,
    NextSessionDecision,
    ViolationCode,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.scheduler.spacing import due_reviews


def validate_session(
    decision: NextSessionDecision,
    goal: LearningGoal,
    model: LearnerModel,
    graph: ConceptGraph,
    today: date,
) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []
    concept_ids = {concept.id for concept in graph.concepts}
    for block in decision.blocks:
        if block.concept_id not in concept_ids:
            violations.append(
                ConstraintViolation(
                    code=ViolationCode.UNKNOWN_CONCEPT,
                    concept_id=block.concept_id,
                    message=f"{block.concept_id} no existe en el grafo",
                )
            )
            continue
        concept = next(c for c in graph.concepts if c.id == block.concept_id)
        if block.kind.value == "concept":
            state = model.concepts.get(block.concept_id)
            mastery = state.mastery if state else 0.0
            if mastery > MASTERY_THRESHOLD:
                violations.append(
                    ConstraintViolation(
                        code=ViolationCode.REDUNDANT_MASTERED,
                        concept_id=block.concept_id,
                        message=f"{block.concept_id} ya está dominado (mastery {mastery:.2f})",
                    )
                )
            for prerequisite in concept.prerequisites:
                prereq_state = model.concepts.get(prerequisite)
                prereq_mastery = prereq_state.mastery if prereq_state else 0.0
                if prereq_mastery < 0.70:
                    violations.append(
                        ConstraintViolation(
                            code=ViolationCode.PREREQ_VIOLATION,
                            concept_id=block.concept_id,
                            message=(
                                f"{block.concept_id} requiere {prerequisite}, cuyo mastery es "
                                f"{prereq_mastery:.2f} (< 0.70)"
                            ),
                        )
                    )
        if block.kind.value != "retrieval" and not block.source_ids:
            violations.append(
                ConstraintViolation(
                    code=ViolationCode.UNSOURCED_CLAIM,
                    concept_id=block.concept_id,
                    message=f"{block.concept_id} contiene afirmaciones sin fuentes",
                )
            )
    if not decision.blocks:
        violations.append(
            ConstraintViolation(
                code=ViolationCode.EMPTY_SESSION,
                message="la sesión debe contener al menos un bloque",
            )
        )
    if decision.total_minutes > goal.daily_minutes * 1.1:
        violations.append(
            ConstraintViolation(
                code=ViolationCode.TIME_BUDGET_EXCEEDED,
                message=(
                    f"la sesión suma {decision.total_minutes} minutos; el presupuesto es "
                    f"{goal.daily_minutes} ±10%"
                ),
            )
        )
    included = {block.concept_id for block in decision.blocks}
    for concept_id in due_reviews(model, today):
        if concept_id not in included:
            violations.append(
                ConstraintViolation(
                    code=ViolationCode.MISSING_DUE_REVIEW,
                    concept_id=concept_id,
                    message=f"falta el repaso vencido de {concept_id}",
                )
            )
    return violations
