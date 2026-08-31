"""Deterministic feasibility assessment against a learning deadline."""

from __future__ import annotations

import math
from datetime import date

from learning_manager.contracts import MASTERY_THRESHOLD, DeadlineStatus, LearnerModel, LearningGoal
from learning_manager.domain.concept_graph import ConceptGraph

AT_RISK_SLACK = 0.20


def remaining_minutes(model: LearnerModel, graph: ConceptGraph) -> int:
    total = 0
    for concept in graph.concepts:
        state = model.concepts.get(concept.id)
        mastery = state.mastery if state else 0.0
        if mastery < MASTERY_THRESHOLD:
            total += math.ceil(concept.estimated_minutes * (1.0 - mastery))
    return total


def available_minutes(goal: LearningGoal, today: date) -> int:
    return max(0, (goal.deadline - today).days + 1) * goal.daily_minutes


def deadline_status(
    goal: LearningGoal, model: LearnerModel, graph: ConceptGraph, today: date
) -> DeadlineStatus:
    needed = remaining_minutes(model, graph)
    available = available_minutes(goal, today)
    if available < needed:
        return DeadlineStatus.INFEASIBLE
    if available < needed * (1 + AT_RISK_SLACK):
        return DeadlineStatus.AT_RISK
    return DeadlineStatus.ON_TRACK
