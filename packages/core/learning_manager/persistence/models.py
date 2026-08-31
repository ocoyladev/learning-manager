"""SQLAlchemy entities used only by the persistence adapter."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    preferred_language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")


class LearningGoalRecord(Base):
    __tablename__ = "learning_goals"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    purpose: Mapped[str] = mapped_column(String(2000), nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_formats: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    success_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConceptRecord(Base):
    __tablename__ = "concepts"

    goal_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_goals.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    importance: Mapped[float] = mapped_column(nullable=False, default=0.5)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)


class LearnerConceptStateRecord(Base):
    __tablename__ = "learner_concept_states"
    __table_args__ = (
        ForeignKeyConstraint(
            ["goal_id", "concept_id"],
            ["concepts.goal_id", "concepts.id"],
            ondelete="CASCADE",
        ),
    )

    goal_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    concept_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    mastery: Mapped[float] = mapped_column(nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    last_seen: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_assessed: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review: Mapped[date | None] = mapped_column(Date, nullable=True)
    misconceptions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class AssessmentAttemptRecord(Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["goal_id", "concept_id"],
            ["concepts.goal_id", "concepts.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    questions: Mapped[list[object]] = mapped_column(JSON, nullable=False, default=list)
    answers: Mapped[list[object]] = mapped_column(JSON, nullable=False, default=list)
    score: Mapped[float] = mapped_column(nullable=False)
    evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    goal_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("learning_goals.id", ondelete="CASCADE"), nullable=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    blocks: Mapped[list[object]] = mapped_column(JSON, nullable=False, default=list)
    rationale: Mapped[str] = mapped_column(String(4000), nullable=False)
    reviews_included: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    deferred_concepts: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    deadline_status: Mapped[str] = mapped_column(String(30), nullable=False)


class SourceRecord(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    url: Mapped[str] = mapped_column(String(4000), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authority: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[date] = mapped_column(Date, nullable=False)
    content_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
