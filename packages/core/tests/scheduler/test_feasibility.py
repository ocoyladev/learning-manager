from datetime import date

from learning_manager.contracts import (
    Concept,
    ConceptState,
    DeadlineStatus,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.scheduler.feasibility import (
    available_minutes,
    deadline_status,
    remaining_minutes,
)

TODAY = date(2026, 9, 5)
GRAPH = ConceptGraph(
    [
        Concept(id="pods", name="Pods", estimated_minutes=20),
        Concept(id="services", name="Services", prerequisites=["pods"], estimated_minutes=25),
        Concept(id="ingress", name="Ingress", prerequisites=["services"], estimated_minutes=25),
    ]
)


def _goal(deadline: date, daily: int = 25) -> LearningGoal:
    return LearningGoal(id="g", title="t", purpose="p", deadline=deadline, daily_minutes=daily)


def _model(**mastery: float) -> LearnerModel:
    return LearnerModel(
        goal_id="g",
        concepts={
            cid: LearnerConceptState(
                concept_id=cid, mastery=m, confidence=0.8, state=ConceptState.DEVELOPING
            )
            for cid, m in mastery.items()
        },
    )


def test_remaining_minutes_discounts_mastered_concepts() -> None:
    assert remaining_minutes(_model(pods=0.95), GRAPH) == 50


def test_remaining_minutes_scales_partial_mastery() -> None:
    assert remaining_minutes(_model(pods=0.95, services=0.50), GRAPH) == 38


def test_available_minutes_counts_days_until_deadline_inclusive() -> None:
    assert available_minutes(_goal(date(2026, 9, 8)), TODAY) == 4 * 25


def test_on_track_when_ample_time() -> None:
    assert (
        deadline_status(_goal(date(2026, 10, 30)), _model(), GRAPH, TODAY)
        is DeadlineStatus.ON_TRACK
    )


def test_at_risk_when_tight() -> None:
    assert (
        deadline_status(_goal(date(2026, 9, 7)), _model(), GRAPH, TODAY) is DeadlineStatus.AT_RISK
    )


def test_infeasible_when_it_does_not_fit() -> None:
    assert deadline_status(_goal(TODAY), _model(), GRAPH, TODAY) is DeadlineStatus.INFEASIBLE


def test_deadline_in_the_past_is_infeasible() -> None:
    assert (
        deadline_status(_goal(date(2026, 9, 1)), _model(), GRAPH, TODAY)
        is DeadlineStatus.INFEASIBLE
    )
