from datetime import date

import pytest
from pydantic import ValidationError

from learning_manager.contracts import (
    AuthorityType,
    BlockKind,
    Concept,
    ConceptState,
    ConstraintViolation,
    DeadlineStatus,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    LLMResponse,
    NextSessionDecision,
    SessionBlock,
    Source,
)


def test_learning_goal_rejects_absurd_daily_minutes() -> None:
    with pytest.raises(ValidationError):
        LearningGoal(id="g", title="t", purpose="p", deadline=date(2026, 9, 20), daily_minutes=0)


def test_next_session_total_minutes_must_match_blocks() -> None:
    block = SessionBlock(
        kind=BlockKind.CONCEPT,
        concept_id="services",
        minutes=10,
        objective="Understand ClusterIP",
    )
    with pytest.raises(ValidationError):
        NextSessionDecision(
            session_date=date(2026, 9, 5),
            blocks=[block],
            total_minutes=99,
            rationale="r",
            deadline_status=DeadlineStatus.ON_TRACK,
        )


def test_next_session_computes_total_when_consistent() -> None:
    blocks = [
        SessionBlock(kind=BlockKind.CONCEPT, concept_id="services", minutes=10, objective="o1"),
        SessionBlock(kind=BlockKind.REVIEW, concept_id="volumes", minutes=5, objective="o2"),
    ]
    decision = NextSessionDecision(
        session_date=date(2026, 9, 5),
        blocks=blocks,
        total_minutes=15,
        rationale="r",
        deadline_status=DeadlineStatus.ON_TRACK,
    )
    assert decision.total_minutes == 15


def test_mastery_is_bounded() -> None:
    with pytest.raises(ValidationError):
        LearnerConceptState(
            concept_id="pods",
            mastery=1.5,
            confidence=0.5,
            state=ConceptState.MASTERED,
        )


def test_source_requires_retrieved_at() -> None:
    with pytest.raises(ValidationError):
        Source(
            id="s1",
            url="https://kubernetes.io/docs/",
            title="Services",
            authority=AuthorityType.OFFICIAL,
        )


def test_source_optional_metadata_defaults_to_none() -> None:
    source = Source(
        id="s1",
        url="https://kubernetes.io/docs/",
        title="Services",
        authority=AuthorityType.OFFICIAL,
        retrieved_at=date(2026, 8, 30),
    )
    assert source.version is None and source.published_at is None


def test_public_contract_models_are_available() -> None:
    assert Concept(id="pods", name="Pods").id == "pods"
    assert LearnerModel(goal_id="g").goal_id == "g"
    assert LLMResponse(text="ok", model="fake").model == "fake"
    violation = ConstraintViolation(code="UNKNOWN_CONCEPT", message="unknown")
    assert violation.code.value == "UNKNOWN_CONCEPT"
