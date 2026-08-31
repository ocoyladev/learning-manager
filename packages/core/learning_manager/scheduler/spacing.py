"""Deterministic spaced-review scheduling without an LLM or system clock."""

from __future__ import annotations

from datetime import date, timedelta

from learning_manager.contracts import LearnerModel

REVIEW_MINUTES = 5
MAX_INTERVAL_DAYS = 30
_INTERVALS: tuple[tuple[float, int], ...] = ((0.50, 1), (0.70, 2), (0.85, 4), (1.01, 7))


def next_review_date(mastery: float, today: date, *, streak: int = 0) -> date:
    base = next(days for threshold, days in _INTERVALS if mastery < threshold)
    return today + timedelta(days=min(base * (2**streak), MAX_INTERVAL_DAYS))


def due_reviews(model: LearnerModel, today: date) -> list[str]:
    return [
        cid
        for cid, state in model.concepts.items()
        if state.next_review is not None and state.next_review <= today
    ]


def prioritize_reviews(
    model: LearnerModel, due: list[str], budget_minutes: int, graph: object | None = None
) -> list[str]:
    ordered = sorted(due, key=lambda cid: model.concepts[cid].mastery)
    return ordered[: max(0, budget_minutes) // REVIEW_MINUTES]
