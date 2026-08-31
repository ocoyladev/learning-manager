from datetime import date

import pytest

from learning_manager.contracts import ConceptState, LearnerConceptState, LearnerModel
from learning_manager.scheduler.spacing import due_reviews, next_review_date, prioritize_reviews

TODAY = date(2026, 9, 5)


@pytest.mark.parametrize(
    "mastery, expected_days",
    [(0.10, 1), (0.49, 1), (0.50, 2), (0.69, 2), (0.70, 4), (0.84, 4), (0.85, 7), (1.00, 7)],
)
def test_spacing_follows_the_frozen_heuristic(mastery: float, expected_days: int) -> None:
    assert next_review_date(mastery, TODAY) == date(2026, 9, 5 + expected_days)


def test_streak_extends_the_interval() -> None:
    assert next_review_date(0.90, TODAY, streak=2) > next_review_date(0.90, TODAY, streak=0)


def test_streak_interval_is_capped() -> None:
    assert (next_review_date(1.0, TODAY, streak=99) - TODAY).days <= 30


def test_due_reviews_includes_today_and_past_only() -> None:
    model = LearnerModel(
        goal_id="g",
        concepts={
            "a": LearnerConceptState(
                concept_id="a",
                mastery=0.5,
                confidence=0.5,
                state=ConceptState.DEVELOPING,
                next_review=date(2026, 9, 4),
            ),
            "b": LearnerConceptState(
                concept_id="b",
                mastery=0.5,
                confidence=0.5,
                state=ConceptState.DEVELOPING,
                next_review=TODAY,
            ),
            "c": LearnerConceptState(
                concept_id="c",
                mastery=0.5,
                confidence=0.5,
                state=ConceptState.DEVELOPING,
                next_review=date(2026, 9, 6),
            ),
            "d": LearnerConceptState(
                concept_id="d", mastery=0.5, confidence=0.5, state=ConceptState.DEVELOPING
            ),
        },
    )
    assert sorted(due_reviews(model, TODAY)) == ["a", "b"]


def test_review_storm_is_prioritized_by_weakness_within_budget() -> None:
    model = LearnerModel(
        goal_id="g",
        concepts={
            cid: LearnerConceptState(
                concept_id=cid,
                mastery=m,
                confidence=0.6,
                state=ConceptState.REVIEW_DUE,
                next_review=TODAY,
            )
            for cid, m in {"a": 0.20, "b": 0.80, "c": 0.45, "d": 0.60}.items()
        },
    )
    ordered = prioritize_reviews(model, ["a", "b", "c", "d"], budget_minutes=10, graph=None)
    assert ordered[0] == "a"
    assert len(ordered) <= 2
