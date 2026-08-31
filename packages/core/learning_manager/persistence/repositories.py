"""Repositories translating SQLAlchemy rows to and from frozen contracts."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from learning_manager.contracts import (
    AuthorityType,
    Concept,
    ConceptState,
    LearnerConceptState,
    LearnerModel,
    LearningGoal,
    NextSessionDecision,
    Source,
)
from learning_manager.persistence.models import (
    ConceptRecord,
    LearnerConceptStateRecord,
    LearningGoalRecord,
    SessionRecord,
    SourceRecord,
)

SessionFactory = Callable[[], Session]


class _Repository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _commit(self, session: Session) -> None:
        session.commit()


class GoalRepository(_Repository):
    def save(self, goal: LearningGoal, concepts: Iterable[Concept]) -> None:
        concept_list = list(concepts)
        with self._session_factory() as session:
            row = session.get(LearningGoalRecord, goal.id)
            if row is None:
                row = LearningGoalRecord(id=goal.id)
                session.add(row)
            row.title = goal.title
            row.purpose = goal.purpose
            row.deadline = goal.deadline
            row.daily_minutes = goal.daily_minutes
            row.preferred_formats = list(goal.preferred_formats)
            row.success_criteria = list(goal.success_criteria)

            existing = session.scalars(
                select(ConceptRecord).where(ConceptRecord.goal_id == goal.id)
            ).all()
            incoming_ids = {concept.id for concept in concept_list}
            for existing_row in existing:
                if existing_row.id not in incoming_ids:
                    session.delete(existing_row)
            for position, concept in enumerate(concept_list):
                concept_row = session.get(ConceptRecord, (goal.id, concept.id))
                if concept_row is None:
                    concept_row = ConceptRecord(goal_id=goal.id, id=concept.id)
                    session.add(concept_row)
                concept_row.name = concept.name
                concept_row.position = position
                concept_row.prerequisites = list(concept.prerequisites)
                concept_row.importance = concept.importance
                concept_row.estimated_minutes = concept.estimated_minutes
            self._commit(session)

    def get(self, goal_id: str) -> tuple[LearningGoal, list[Concept]]:
        with self._session_factory() as session:
            row = session.get(LearningGoalRecord, goal_id)
            if row is None:
                raise KeyError(f"unknown learning goal: {goal_id}")
            goal = LearningGoal(
                id=row.id,
                title=row.title,
                purpose=row.purpose,
                deadline=row.deadline,
                daily_minutes=row.daily_minutes,
                preferred_formats=list(row.preferred_formats),
                success_criteria=list(row.success_criteria),
            )
            concept_rows = session.scalars(
                select(ConceptRecord)
                .where(ConceptRecord.goal_id == goal_id)
                .order_by(ConceptRecord.position)
            ).all()
            concepts = [
                Concept(
                    id=concept.id,
                    name=concept.name,
                    prerequisites=list(concept.prerequisites),
                    importance=concept.importance,
                    estimated_minutes=concept.estimated_minutes,
                )
                for concept in concept_rows
            ]
            return goal, concepts


class LearnerModelRepository(_Repository):
    def save(self, model: LearnerModel) -> None:
        with self._session_factory() as session:
            goal = session.get(LearningGoalRecord, model.goal_id)
            if goal is None:
                raise ValueError(f"cannot save learner model for unknown goal: {model.goal_id}")
            goal.updated_at = model.updated_at

            existing = session.scalars(
                select(LearnerConceptStateRecord).where(
                    LearnerConceptStateRecord.goal_id == model.goal_id
                )
            ).all()
            incoming_ids = set(model.concepts)
            for existing_row in existing:
                if existing_row.concept_id not in incoming_ids:
                    session.delete(existing_row)

            for state in model.concepts.values():
                row = session.get(LearnerConceptStateRecord, (model.goal_id, state.concept_id))
                if row is None:
                    row = LearnerConceptStateRecord(
                        goal_id=model.goal_id,
                        concept_id=state.concept_id,
                    )
                    session.add(row)
                row.mastery = state.mastery
                row.confidence = state.confidence
                row.state = state.state.value
                row.last_seen = state.last_seen
                row.last_assessed = state.last_assessed
                row.next_review = state.next_review
                row.misconceptions = list(state.misconceptions)
                row.evidence = list(state.evidence)
            self._commit(session)

    def get(self, goal_id: str) -> LearnerModel:
        with self._session_factory() as session:
            goal = session.get(LearningGoalRecord, goal_id)
            if goal is None:
                raise KeyError(f"unknown learning goal: {goal_id}")
            rows = session.scalars(
                select(LearnerConceptStateRecord)
                .where(LearnerConceptStateRecord.goal_id == goal_id)
                .order_by(LearnerConceptStateRecord.concept_id)
            ).all()
            concepts = {
                row.concept_id: LearnerConceptState(
                    concept_id=row.concept_id,
                    mastery=row.mastery,
                    confidence=row.confidence,
                    state=ConceptState(row.state),
                    last_seen=row.last_seen,
                    last_assessed=row.last_assessed,
                    next_review=row.next_review,
                    misconceptions=list(row.misconceptions),
                    evidence=list(row.evidence),
                )
                for row in rows
            }
            return LearnerModel(goal_id=goal_id, concepts=concepts, updated_at=goal.updated_at)


class SessionRepository(_Repository):
    @staticmethod
    def _resolve_goal_id(session: Session, decision: NextSessionDecision) -> str:
        concept_ids = {block.concept_id for block in decision.blocks}
        if not concept_ids:
            raise ValueError(
                "cannot save a session decision without a concept to identify its goal"
            )

        rows = session.execute(
            select(ConceptRecord.goal_id, ConceptRecord.id).where(ConceptRecord.id.in_(concept_ids))
        ).all()
        goal_ids_by_concept: dict[str, set[str]] = {
            concept_id: {
                cast(str, goal_id)
                for goal_id, row_concept_id in rows
                if cast(str, row_concept_id) == concept_id
            }
            for concept_id in concept_ids
        }
        candidate_goal_ids = set.intersection(*goal_ids_by_concept.values())
        if len(candidate_goal_ids) != 1:
            raise ValueError("session decision does not identify a unique existing goal")
        return candidate_goal_ids.pop()

    def save(self, decision: NextSessionDecision) -> str:
        session_id = decision.id or uuid4().hex
        blocks = [block.model_dump(mode="json") for block in decision.blocks]
        with self._session_factory() as session:
            goal_id = self._resolve_goal_id(session, decision)
            row = session.get(SessionRecord, session_id)
            if row is None:
                row = SessionRecord(id=session_id)
                session.add(row)
            row.goal_id = goal_id
            row.session_date = decision.session_date
            row.planned_minutes = decision.total_minutes
            row.blocks = cast(list[object], blocks)
            row.rationale = decision.rationale
            row.reviews_included = list(decision.reviews_included)
            row.deferred_concepts = list(decision.deferred_concepts)
            row.deadline_status = decision.deadline_status.value
            self._commit(session)
        return session_id

    def get(self, session_id: str) -> NextSessionDecision:
        with self._session_factory() as session:
            row = session.get(SessionRecord, session_id)
            if row is None:
                raise KeyError(f"unknown session: {session_id}")
            return NextSessionDecision.model_validate(
                {
                    "id": row.id,
                    "session_date": row.session_date,
                    "blocks": row.blocks,
                    "total_minutes": row.planned_minutes,
                    "rationale": row.rationale,
                    "reviews_included": row.reviews_included,
                    "deferred_concepts": row.deferred_concepts,
                    "deadline_status": row.deadline_status,
                }
            )


class SourceRepository(_Repository):
    def save_many(self, sources: Iterable[Source]) -> None:
        with self._session_factory() as session:
            for source in sources:
                row = session.get(SourceRecord, source.id)
                if row is None:
                    row = SourceRecord(id=source.id)
                    session.add(row)
                row.url = source.url
                row.title = source.title
                row.authority = source.authority.value
                row.version = source.version
                row.published_at = source.published_at
                row.retrieved_at = source.retrieved_at
                row.content_path = source.content_path
            self._commit(session)

    def by_ids(self, ids: Iterable[str]) -> list[Source]:
        requested_ids = list(ids)
        if not requested_ids:
            return []
        with self._session_factory() as session:
            rows = session.scalars(
                select(SourceRecord).where(SourceRecord.id.in_(requested_ids))
            ).all()
            by_id = {
                row.id: Source(
                    id=row.id,
                    url=row.url,
                    title=row.title,
                    authority=AuthorityType(row.authority),
                    version=row.version,
                    published_at=row.published_at,
                    retrieved_at=row.retrieved_at,
                    content_path=row.content_path,
                )
                for row in rows
            }
            return [by_id[source_id] for source_id in requested_ids if source_id in by_id]
