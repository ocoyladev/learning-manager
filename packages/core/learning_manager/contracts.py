"""Single source of truth for the system-wide contracts.

Frozen after Phase 0. Agents must not modify this file without explicit human approval:
three parallel tracks rely on these signatures.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field, model_validator


class ConceptState(str, Enum):  # noqa: UP042
    UNSEEN = "unseen"
    INTRODUCED = "introduced"
    WEAK = "weak"
    DEVELOPING = "developing"
    MASTERED = "mastered"
    REVIEW_DUE = "review_due"


class BlockKind(str, Enum):  # noqa: UP042
    CONCEPT = "concept"
    WORKED_EXAMPLE = "worked_example"
    PRACTICE = "practice"
    RETRIEVAL = "retrieval"
    REVIEW = "review"


class AuthorityType(str, Enum):  # noqa: UP042
    OFFICIAL = "official"
    VENDOR = "vendor"
    BOOK = "book"
    BLOG = "blog"
    TUTORIAL = "tutorial"
    FORUM = "forum"
    UNKNOWN = "unknown"


class DeadlineStatus(str, Enum):  # noqa: UP042
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    INFEASIBLE = "infeasible"


class ViolationCode(str, Enum):  # noqa: UP042
    PREREQ_VIOLATION = "PREREQ_VIOLATION"
    REDUNDANT_MASTERED = "REDUNDANT_MASTERED"
    TIME_BUDGET_EXCEEDED = "TIME_BUDGET_EXCEEDED"
    MISSING_DUE_REVIEW = "MISSING_DUE_REVIEW"
    UNKNOWN_CONCEPT = "UNKNOWN_CONCEPT"
    EMPTY_SESSION = "EMPTY_SESSION"
    UNSOURCED_CLAIM = "UNSOURCED_CLAIM"


MASTERY_THRESHOLD = 0.85
"""Above this value a concept is considered mastered and is not re-taught."""

PREREQ_THRESHOLD = 0.70
"""Minimum prerequisite mastery required to unlock the next concept."""


class LearningGoal(BaseModel):
    id: str
    title: str
    purpose: str
    deadline: date
    daily_minutes: int = Field(ge=5, le=240)
    preferred_formats: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class Concept(BaseModel):
    id: str
    name: str
    prerequisites: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    estimated_minutes: int = Field(default=15, ge=1, le=180)


class LearnerConceptState(BaseModel):
    concept_id: str
    mastery: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    state: ConceptState
    last_seen: date | None = None
    last_assessed: date | None = None
    next_review: date | None = None
    misconceptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class LearnerModel(BaseModel):
    goal_id: str
    concepts: dict[str, LearnerConceptState] = Field(default_factory=dict)
    updated_at: datetime | None = None


class SessionBlock(BaseModel):
    kind: BlockKind
    concept_id: str
    minutes: int = Field(ge=1, le=180)
    objective: str
    content: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class NextSessionDecision(BaseModel):
    """Output of CurriculumPlanner, scored by NSDQ."""

    id: str | None = None
    """Assigned by persistence when saved; remains None in memory."""

    session_date: date
    blocks: list[SessionBlock]
    total_minutes: int = Field(ge=0)
    rationale: str
    reviews_included: list[str] = Field(default_factory=list)
    deferred_concepts: list[str] = Field(default_factory=list)
    deadline_status: DeadlineStatus

    @model_validator(mode="after")
    def _total_matches_blocks(self) -> NextSessionDecision:
        expected = sum(block.minutes for block in self.blocks)
        if self.total_minutes != expected:
            raise ValueError(f"total_minutes={self.total_minutes} but blocks sum to {expected}")
        return self


class Source(BaseModel):
    id: str
    url: str
    title: str
    authority: AuthorityType
    version: str | None = None
    published_at: date | None = None
    retrieved_at: date
    content_path: str | None = None


class ConstraintViolation(BaseModel):
    code: ViolationCode
    message: str
    concept_id: str | None = None


class AssessmentItem(BaseModel):
    id: str
    concept_id: str
    question: str
    options: list[str] = Field(default_factory=list)
    expected: str
    explanation: str = ""


class AssessmentResult(BaseModel):
    concept_id: str
    score: float = Field(ge=0.0, le=1.0)
    correct: int
    total: int
    misconceptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class LLMResponse(BaseModel):
    text: str
    parsed: dict[str, object] | None = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    cache_hit: bool = False


@runtime_checkable
class LLMProvider(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse: ...


@runtime_checkable
class KnowledgeProvider(Protocol):
    def research(self, topic: str, *, k: int = 8) -> list[Source]: ...

    def fetch(self, source_id: str) -> str: ...


class Reply(BaseModel):
    user_ref: str
    text: str
    received_at: datetime
    message_ref: str | None = None


@runtime_checkable
class NotificationProvider(Protocol):
    def send(self, *, user_ref: str, message: str, options: list[str] | None = None) -> str: ...

    def poll_replies(self) -> list[Reply]: ...
