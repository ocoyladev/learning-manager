import random
from datetime import date

from learning_manager.contracts import (
    Concept,
    ConceptState,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.verification.constraints import validate_session
from learning_manager.verification.fallback import deterministic_session

TODAY = date(2026, 9, 5)
GRAPH = ConceptGraph(
    [
        Concept(id="pods", name="Pods"),
        Concept(id="services", name="Services", prerequisites=["pods"]),
        Concept(id="ingress", name="Ingress", prerequisites=["services"]),
    ]
)
GOAL = LearningGoal(id="g", title="t", purpose="p", deadline=date(2026, 9, 20), daily_minutes=25)


def random_model(rng: random.Random) -> LearnerModel:
    return LearnerModel(
        goal_id="g",
        concepts={
            cid: LearnerConceptState(
                concept_id=cid, mastery=rng.random(), confidence=0.8, state=ConceptState.DEVELOPING
            )
            for cid in ("pods", "services", "ingress")
        },
    )


def test_fallback_always_validates() -> None:
    rng = random.Random(1234)
    for _ in range(20):
        learner = random_model(rng)
        assert (
            validate_session(
                deterministic_session(GOAL, learner, GRAPH, TODAY), GOAL, learner, GRAPH, TODAY
            )
            == []
        )


def test_fallback_is_reproducible() -> None:
    learner = random_model(random.Random(7))
    assert deterministic_session(GOAL, learner, GRAPH, TODAY) == deterministic_session(
        GOAL, learner, GRAPH, TODAY
    )
