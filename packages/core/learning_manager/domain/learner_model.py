"""Pure learner-model state transitions."""

from __future__ import annotations

from datetime import date

from learning_manager.contracts import (
    MASTERY_THRESHOLD,
    AssessmentResult,
    ConceptState,
    LearnerConceptState,
)

LEARNING_RATE = 0.6
CONFIDENCE_GAIN = 0.15
MISCONCEPTION_CLEAR_SCORE = 0.9


def derive_state(
    mastery: float,
    confidence: float,
    next_review: date | None,
    today: date,
) -> ConceptState:
    """Derive the display state for a concept from its current estimates."""
    if next_review is not None and next_review <= today:
        return ConceptState.REVIEW_DUE
    if confidence == 0.0 and mastery == 0.0:
        return ConceptState.UNSEEN
    if mastery >= MASTERY_THRESHOLD:
        return ConceptState.MASTERED
    if mastery < 0.35:
        return ConceptState.WEAK
    if mastery < 0.50:
        return ConceptState.INTRODUCED
    return ConceptState.DEVELOPING


def apply_assessment(
    state: LearnerConceptState,
    result: AssessmentResult,
    today: date,
) -> LearnerConceptState:
    """Return a new state after incorporating one assessment result."""
    mastery = round(state.mastery * (1 - LEARNING_RATE) + result.score * LEARNING_RATE, 4)
    confidence = round(min(1.0, state.confidence + CONFIDENCE_GAIN), 4)

    if result.score >= MISCONCEPTION_CLEAR_SCORE:
        misconceptions: list[str] = []
    else:
        misconceptions = list(state.misconceptions)
        for misconception in result.misconceptions:
            if misconception not in misconceptions:
                misconceptions.append(misconception)

    return state.model_copy(
        update={
            "mastery": mastery,
            "confidence": confidence,
            "state": derive_state(mastery, confidence, state.next_review, today),
            "last_assessed": today,
            "last_seen": today,
            "misconceptions": misconceptions,
            "evidence": [*state.evidence, *result.evidence],
        }
    )
