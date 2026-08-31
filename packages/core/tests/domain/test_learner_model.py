from datetime import date

from learning_manager.contracts import (
    AssessmentResult,
    ConceptState,
    LearnerConceptState,
)
from learning_manager.domain.learner_model import apply_assessment, derive_state

TODAY = date(2026, 9, 5)


def test_derive_state_unseen_when_never_assessed() -> None:
    assert derive_state(0.0, 0.0, None, TODAY) is ConceptState.UNSEEN


def test_derive_state_mastered_at_threshold() -> None:
    assert derive_state(0.85, 0.85, None, TODAY) is ConceptState.MASTERED


def test_derive_state_weak_below_threshold() -> None:
    assert derive_state(0.30, 0.70, None, TODAY) is ConceptState.WEAK


def test_derive_state_introduced_between_weak_and_half() -> None:
    assert derive_state(0.35, 0.70, None, TODAY) is ConceptState.INTRODUCED
    assert derive_state(0.49, 0.70, None, TODAY) is ConceptState.INTRODUCED


def test_derive_state_developing_at_half() -> None:
    assert derive_state(0.50, 0.70, None, TODAY) is ConceptState.DEVELOPING


def test_derive_state_review_due_precedes_all_other_states() -> None:
    assert derive_state(0.90, 0.85, TODAY, TODAY) is ConceptState.REVIEW_DUE
    assert derive_state(0.90, 0.85, date(2026, 9, 1), TODAY) is ConceptState.REVIEW_DUE


def test_derive_state_future_review_does_not_make_review_due() -> None:
    assert derive_state(0.30, 0.70, date(2026, 9, 6), TODAY) is ConceptState.WEAK


def test_apply_assessment_moves_mastery_toward_score_exponentially() -> None:
    before = LearnerConceptState(
        concept_id="services", mastery=0.30, confidence=0.60, state=ConceptState.WEAK
    )
    result = AssessmentResult(concept_id="services", score=0.90, correct=9, total=10)

    after = apply_assessment(before, result, TODAY)

    assert after.mastery == 0.66
    assert before.mastery < after.mastery < result.score


def test_apply_assessment_caps_confidence_at_one() -> None:
    before = LearnerConceptState(
        concept_id="services", mastery=0.8, confidence=0.95, state=ConceptState.DEVELOPING
    )

    after = apply_assessment(
        before,
        AssessmentResult(concept_id="services", score=0.9, correct=9, total=10),
        TODAY,
    )

    assert after.confidence == 1.0


def test_apply_assessment_sets_assessed_and_seen_dates() -> None:
    before = LearnerConceptState(
        concept_id="services",
        mastery=0.30,
        confidence=0.60,
        state=ConceptState.WEAK,
        last_seen=date(2026, 9, 1),
    )

    after = apply_assessment(
        before,
        AssessmentResult(concept_id="services", score=0.9, correct=9, total=10),
        TODAY,
    )

    assert after.last_assessed == TODAY
    assert after.last_seen == TODAY


def test_apply_assessment_accumulates_evidence() -> None:
    before = LearnerConceptState(
        concept_id="services",
        mastery=0.30,
        confidence=0.60,
        state=ConceptState.WEAK,
        evidence=["attempt-1"],
    )
    result = AssessmentResult(
        concept_id="services", score=0.4, correct=4, total=10, evidence=["attempt-2"]
    )

    after = apply_assessment(before, result, TODAY)

    assert after.evidence == ["attempt-1", "attempt-2"]


def test_apply_assessment_accumulates_misconceptions_without_duplicates() -> None:
    before = LearnerConceptState(
        concept_id="services",
        mastery=0.30,
        confidence=0.60,
        state=ConceptState.WEAK,
        misconceptions=["confuses ClusterIP with NodePort"],
    )
    result = AssessmentResult(
        concept_id="services",
        score=0.4,
        correct=4,
        total=10,
        misconceptions=[
            "confuses ClusterIP with NodePort",
            "believes Ingress is a Service",
        ],
    )

    after = apply_assessment(before, result, TODAY)

    assert after.misconceptions == [
        "confuses ClusterIP with NodePort",
        "believes Ingress is a Service",
    ]


def test_apply_assessment_clears_resolved_misconceptions_on_high_score() -> None:
    before = LearnerConceptState(
        concept_id="services",
        mastery=0.60,
        confidence=0.70,
        state=ConceptState.DEVELOPING,
        misconceptions=["confuses ClusterIP with NodePort"],
    )
    result = AssessmentResult(concept_id="services", score=0.9, correct=9, total=10)

    after = apply_assessment(before, result, TODAY)

    assert after.misconceptions == []


def test_apply_assessment_preserves_next_review() -> None:
    review_date = date(2026, 9, 8)
    before = LearnerConceptState(
        concept_id="services",
        mastery=0.30,
        confidence=0.60,
        state=ConceptState.WEAK,
        next_review=review_date,
    )

    after = apply_assessment(
        before,
        AssessmentResult(concept_id="services", score=0.9, correct=9, total=10),
        TODAY,
    )

    assert after.next_review == review_date


def test_apply_assessment_is_pure_and_does_not_mutate_inputs() -> None:
    before = LearnerConceptState(
        concept_id="pods",
        mastery=0.5,
        confidence=0.5,
        state=ConceptState.DEVELOPING,
        misconceptions=["old misconception"],
        evidence=["old evidence"],
    )
    result = AssessmentResult(
        concept_id="pods",
        score=1.0,
        correct=1,
        total=1,
        misconceptions=["new misconception"],
        evidence=["new evidence"],
    )

    apply_assessment(before, result, TODAY)

    assert before.mastery == 0.5
    assert before.misconceptions == ["old misconception"]
    assert before.evidence == ["old evidence"]
    assert result.misconceptions == ["new misconception"]
    assert result.evidence == ["new evidence"]
