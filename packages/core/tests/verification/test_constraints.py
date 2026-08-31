from datetime import date

from learning_manager.contracts import (
    BlockKind,
    Concept,
    ConceptState,
    DeadlineStatus,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    NextSessionDecision,
    SessionBlock,
    ViolationCode,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.verification.constraints import validate_session

TODAY = date(2026, 9, 5)
GRAPH = ConceptGraph(
    [
        Concept(id="pods", name="Pods"),
        Concept(id="services", name="Services", prerequisites=["pods"]),
        Concept(id="ingress", name="Ingress", prerequisites=["services"]),
    ]
)
GOAL = LearningGoal(id="g", title="t", purpose="p", deadline=date(2026, 9, 20), daily_minutes=25)


def model(**mastery: float) -> LearnerModel:
    return LearnerModel(
        goal_id="g",
        concepts={
            cid: LearnerConceptState(
                concept_id=cid, mastery=value, confidence=0.8, state=ConceptState.DEVELOPING
            )
            for cid, value in mastery.items()
        },
    )


def decision(*blocks: SessionBlock) -> NextSessionDecision:
    return NextSessionDecision(
        session_date=TODAY,
        blocks=list(blocks),
        total_minutes=sum(b.minutes for b in blocks),
        rationale="r",
        deadline_status=DeadlineStatus.ON_TRACK,
    )


def block(
    kind: BlockKind, cid: str, minutes: int, sources: list[str] | None = None
) -> SessionBlock:
    return SessionBlock(
        kind=kind,
        concept_id=cid,
        minutes=minutes,
        objective="o",
        content="c",
        source_ids=["s"] if sources is None else sources,
    )


def codes(value: NextSessionDecision, learner: LearnerModel) -> set[ViolationCode]:
    return {item.code for item in validate_session(value, GOAL, learner, GRAPH, TODAY)}


def test_all_constraint_codes() -> None:
    assert ViolationCode.PREREQ_VIOLATION in codes(
        decision(block(BlockKind.CONCEPT, "ingress", 10)), model(pods=0.9, services=0.3)
    )
    assert ViolationCode.REDUNDANT_MASTERED in codes(
        decision(block(BlockKind.CONCEPT, "pods", 10)), model(pods=0.95)
    )
    assert ViolationCode.TIME_BUDGET_EXCEEDED in codes(
        decision(block(BlockKind.CONCEPT, "pods", 30)), model()
    )
    assert ViolationCode.UNKNOWN_CONCEPT in codes(
        decision(block(BlockKind.CONCEPT, "unknown", 10)), model()
    )
    assert ViolationCode.EMPTY_SESSION in codes(decision(), model())
    assert ViolationCode.UNSOURCED_CLAIM in codes(
        decision(block(BlockKind.CONCEPT, "pods", 10, [])), model()
    )


def test_due_review_is_required() -> None:
    learner = model(pods=0.4)
    learner.concepts["pods"].next_review = TODAY
    assert ViolationCode.MISSING_DUE_REVIEW in codes(
        decision(block(BlockKind.RETRIEVAL, "services", 10)), learner
    )


def test_retrieval_without_sources_is_allowed() -> None:
    assert ViolationCode.UNSOURCED_CLAIM not in codes(
        decision(block(BlockKind.RETRIEVAL, "pods", 5, [])), model()
    )
