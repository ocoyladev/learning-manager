from datetime import UTC, date, datetime

from sqlalchemy import inspect

from learning_manager.contracts import (
    AuthorityType,
    BlockKind,
    Concept,
    ConceptState,
    DeadlineStatus,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    NextSessionDecision,
    SessionBlock,
    Source,
)
from learning_manager.persistence.repositories import (
    GoalRepository,
    LearnerModelRepository,
    SessionRepository,
    SourceRepository,
)


def test_initial_schema_contains_all_required_tables(session_factory) -> None:
    with session_factory() as session:
        tables = set(inspect(session.bind).get_table_names())

    assert tables == {
        "users",
        "learning_goals",
        "concepts",
        "learner_concept_states",
        "assessment_attempts",
        "sessions",
        "sources",
    }


def test_goal_roundtrip_preserves_goal_and_prerequisites(session_factory) -> None:
    repo = GoalRepository(session_factory)
    goal = LearningGoal(
        id="goal-roundtrip",
        title="Kubernetes",
        purpose="interview",
        deadline=date(2026, 9, 20),
        daily_minutes=25,
        preferred_formats=["worked examples", "practice"],
        success_criteria=["explain Services", "configure Ingress"],
    )
    concepts = [
        Concept(id="pods", name="Pods", importance=0.8, estimated_minutes=20),
        Concept(id="services", name="Services", prerequisites=["pods"], importance=0.9),
    ]

    repo.save(goal, concepts)
    loaded_goal, loaded_concepts = repo.get(goal.id)

    assert loaded_goal == goal
    assert loaded_concepts == concepts


def test_goal_save_is_idempotent(session_factory) -> None:
    repo = GoalRepository(session_factory)
    goal = LearningGoal(
        id="goal-idempotent",
        title="Kubernetes",
        purpose="interview",
        deadline=date(2026, 9, 20),
        daily_minutes=25,
    )
    concepts = [Concept(id="pods", name="Pods")]

    repo.save(goal, concepts)
    repo.save(goal, concepts)

    assert repo.get(goal.id) == (goal, concepts)


def test_goal_roundtrip_preserves_concept_order(session_factory) -> None:
    repo = GoalRepository(session_factory)
    goal = LearningGoal(
        id="goal-order",
        title="Kubernetes",
        purpose="interview",
        deadline=date(2026, 9, 20),
        daily_minutes=25,
    )
    concepts = [Concept(id="z-last", name="Last"), Concept(id="a-first", name="First")]

    repo.save(goal, concepts)

    assert repo.get(goal.id)[1] == concepts


def test_learner_model_upsert_preserves_optional_and_list_fields(session_factory) -> None:
    repo = LearnerModelRepository(session_factory)
    model = LearnerModel(
        goal_id="learner-roundtrip",
        concepts={
            "services": LearnerConceptState(
                concept_id="services",
                mastery=0.5,
                confidence=0.5,
                state=ConceptState.DEVELOPING,
                last_seen=date(2026, 9, 1),
                last_assessed=date(2026, 9, 2),
                next_review=date(2026, 9, 4),
                misconceptions=["confuses ClusterIP with NodePort"],
                evidence=["assessment:attempt-1"],
            )
        },
        updated_at=datetime(2026, 9, 5, 12, tzinfo=UTC),
    )

    repo.save(model)

    assert repo.get(model.goal_id) == model


def test_learner_model_upsert_is_idempotent(session_factory) -> None:
    repo = LearnerModelRepository(session_factory)
    state = LearnerConceptState(
        concept_id="pods", mastery=0.5, confidence=0.5, state=ConceptState.DEVELOPING
    )
    model = LearnerModel(goal_id="learner-idempotent", concepts={"pods": state})

    repo.save(model)
    repo.save(model)

    assert repo.get(model.goal_id).concepts == {"pods": state}


def test_learner_model_save_replaces_removed_states(session_factory) -> None:
    repo = LearnerModelRepository(session_factory)
    model = LearnerModel(
        goal_id="learner-replace",
        concepts={
            "pods": LearnerConceptState(
                concept_id="pods", mastery=0.5, confidence=0.5, state=ConceptState.DEVELOPING
            ),
            "services": LearnerConceptState(
                concept_id="services", mastery=0.4, confidence=0.5, state=ConceptState.INTRODUCED
            ),
        },
    )
    repo.save(model)
    replacement = model.model_copy(update={"concepts": {"pods": model.concepts["pods"]}})

    repo.save(replacement)

    assert repo.get(model.goal_id) == replacement


def test_session_roundtrip_preserves_nested_blocks_and_metadata(session_factory) -> None:
    repo = SessionRepository(session_factory)
    decision = NextSessionDecision(
        session_date=date(2026, 9, 5),
        blocks=[
            SessionBlock(
                kind=BlockKind.RETRIEVAL,
                concept_id="services",
                minutes=10,
                objective="Recall service types",
                content="ClusterIP is internal.",
                source_ids=["source-k8s"],
            ),
            SessionBlock(
                kind=BlockKind.PRACTICE,
                concept_id="services",
                minutes=15,
                objective="Choose a service type",
            ),
        ],
        total_minutes=25,
        rationale="Weakest evidence first",
        reviews_included=["services"],
        deferred_concepts=["ingress"],
        deadline_status=DeadlineStatus.ON_TRACK,
    )

    session_id = repo.save(decision)
    loaded = repo.get(session_id)

    assert loaded.id == session_id
    assert loaded == decision.model_copy(update={"id": session_id})


def test_source_upsert_preserves_metadata_and_by_ids_order(session_factory) -> None:
    repo = SourceRepository(session_factory)
    sources = [
        Source(
            id="source-official",
            url="https://kubernetes.io/docs/concepts/services-networking/service/",
            title="Service",
            authority=AuthorityType.OFFICIAL,
            version="v1.34",
            published_at=date(2026, 1, 1),
            retrieved_at=date(2026, 9, 5),
            content_path="corpus/service.md",
        ),
        Source(
            id="source-book",
            url="https://example.com/book",
            title="Kubernetes book",
            authority=AuthorityType.BOOK,
            retrieved_at=date(2026, 9, 5),
        ),
    ]

    repo.save_many(sources)
    repo.save_many(sources)

    assert repo.by_ids(["source-book", "missing", "source-official"]) == [sources[1], sources[0]]
