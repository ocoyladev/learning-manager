"""Deterministic FastAPI stub used by the UI during early development."""

from __future__ import annotations

import argparse
from datetime import date

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field, StrictBool, StrictInt, model_validator

from learning_manager.contracts import (
    AssessmentItem,
    AssessmentResult,
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

app = FastAPI(title="Learning Manager API", version="0.1.0")


class _GoalRequest(BaseModel):
    title: str
    purpose: str
    deadline: date
    daily_minutes: int = Field(ge=5, le=240)
    preferred_formats: list[str] = Field(default_factory=list)


class _GoalResponse(BaseModel):
    goal: LearningGoal
    concepts: list[Concept]


class _GoalDetailsResponse(_GoalResponse):
    learner_model: LearnerModel


class _DiagnosticResponse(BaseModel):
    items: list[AssessmentItem]


class _Answer(BaseModel):
    item_id: str
    answer: str


class _AnswersRequest(BaseModel):
    answers: list[_Answer]


class _LearnerResponse(BaseModel):
    learner_model: LearnerModel


class _ResearchRequest(BaseModel):
    topic: str


class _ResearchResponse(BaseModel):
    sources: list[Source]


class _GoalUpdateRequest(BaseModel):
    daily_minutes: StrictInt = Field(default=30, ge=5, le=240)
    paused: StrictBool = False

    @model_validator(mode="after")
    def require_update(self) -> _GoalUpdateRequest:
        if not self.model_fields_set:
            raise ValueError("At least one goal setting must be provided.")
        return self


class _GoalUpdateResponse(BaseModel):
    goal: LearningGoal
    paused: bool


class _RecommendationRejectionRequest(BaseModel):
    reason: str = Field(min_length=1)


class _SessionFeedbackRequest(BaseModel):
    appropriate: StrictBool
    reason: str | None = Field(default=None, min_length=1)


class _AcceptedResponse(BaseModel):
    accepted: bool
    message: str


class _AlternativeExplanationResponse(BaseModel):
    content: str
    source_ids: list[str]


class _AssessmentResponse(BaseModel):
    results: list[AssessmentResult]
    learner_model: LearnerModel


class _DashboardResponse(BaseModel):
    progress: float
    on_track: bool
    deadline_status: DeadlineStatus
    strong: list[str]
    weak: list[str]
    next_review: date | None
    why: str
    estimated_sessions: int
    projected_completion: date


class _SimulateDayRequest(BaseModel):
    days: int = Field(ge=1, le=365)


class _Event(BaseModel):
    day: int
    kind: str
    message: str


class _SimulateDayResponse(BaseModel):
    events: list[_Event]


def _concepts() -> list[Concept]:
    return [
        Concept(
            id="containers-basics",
            name="Container basics",
            prerequisites=[],
            importance=1.0,
            estimated_minutes=15,
        )
    ]


def _goal(goal_id: str, request: _GoalRequest | None = None) -> LearningGoal:
    if request is None:
        return LearningGoal(
            id=goal_id,
            title="Learn containers",
            purpose="Build reliable services",
            deadline=date(2026, 9, 20),
            daily_minutes=30,
            preferred_formats=["examples"],
        )
    return LearningGoal(id="demo", **request.model_dump())


def _learner_model(goal_id: str) -> LearnerModel:
    state = LearnerConceptState(
        concept_id="containers-basics",
        mastery=0.4,
        confidence=0.6,
        state=ConceptState.DEVELOPING,
        next_review=date(2026, 9, 1),
    )
    return LearnerModel(goal_id=goal_id, concepts={state.concept_id: state})


@app.post("/goals", response_model=_GoalResponse)
def create_goal(request: _GoalRequest) -> _GoalResponse:
    return _GoalResponse(goal=_goal("demo", request), concepts=_concepts())


@app.get("/goals/{goal_id}", response_model=_GoalDetailsResponse)
def get_goal(goal_id: str) -> _GoalDetailsResponse:
    return _GoalDetailsResponse(
        goal=_goal(goal_id), concepts=_concepts(), learner_model=_learner_model(goal_id)
    )


@app.post("/goals/{goal_id}/diagnostic", response_model=_DiagnosticResponse)
def diagnostic(goal_id: str) -> _DiagnosticResponse:
    del goal_id
    return _DiagnosticResponse(
        items=[
            AssessmentItem(
                id="diagnostic-1",
                concept_id="containers-basics",
                question="What does a container isolate?",
                options=["Process and dependencies", "An entire physical machine"],
                expected="Process and dependencies",
                explanation=(
                    "A container isolates a process and its dependencies while sharing "
                    "the host kernel."
                ),
            )
        ]
    )


@app.post("/goals/{goal_id}/diagnostic/answers", response_model=_LearnerResponse)
def diagnostic_answers(goal_id: str, request: _AnswersRequest) -> _LearnerResponse:
    del request
    return _LearnerResponse(learner_model=_learner_model(goal_id))


@app.post("/goals/{goal_id}/research", response_model=_ResearchResponse)
def research(goal_id: str, request: _ResearchRequest) -> _ResearchResponse:
    del goal_id, request
    return _research_response()


def _research_response() -> _ResearchResponse:
    return _ResearchResponse(
        sources=[
            Source(
                id="source-official",
                url="https://docs.docker.com/get-started/",
                title="Docker Get Started",
                authority=AuthorityType.OFFICIAL,
                retrieved_at=date(2026, 8, 30),
            )
        ]
    )


@app.get("/goals/{goal_id}/sources", response_model=_ResearchResponse)
def sources(goal_id: str) -> _ResearchResponse:
    del goal_id
    return _research_response()


@app.patch("/goals/{goal_id}", response_model=_GoalUpdateResponse)
def update_goal(goal_id: str, request: _GoalUpdateRequest) -> _GoalUpdateResponse:
    goal = _goal(goal_id)
    if "daily_minutes" in request.model_fields_set:
        goal = goal.model_copy(update={"daily_minutes": request.daily_minutes})
    return _GoalUpdateResponse(goal=goal, paused=request.paused)


@app.post(
    "/goals/{goal_id}/recommendations/reject",
    response_model=_AcceptedResponse,
)
def reject_recommendation(
    goal_id: str, request: _RecommendationRejectionRequest
) -> _AcceptedResponse:
    del goal_id, request
    return _AcceptedResponse(accepted=True, message="Recommendation rejected.")


@app.get("/goals/{goal_id}/next-session", response_model=NextSessionDecision)
def next_session(goal_id: str, today: date) -> NextSessionDecision:
    del goal_id
    block = SessionBlock(
        kind=BlockKind.CONCEPT,
        concept_id="containers-basics",
        minutes=15,
        objective="Explain container isolation",
        content=(
            "A container isolates a process and its dependencies while sharing the host kernel."
        ),
        source_ids=["source-official"],
    )
    return NextSessionDecision(
        id="session-demo",
        session_date=today,
        blocks=[block],
        total_minutes=15,
        rationale="Build the prerequisite foundation first.",
        deadline_status=DeadlineStatus.ON_TRACK,
    )


@app.post("/sessions/{session_id}/assess", response_model=_AssessmentResponse)
def assess(session_id: str, request: _AnswersRequest) -> _AssessmentResponse:
    del session_id, request
    return _AssessmentResponse(
        results=[
            AssessmentResult(
                concept_id="containers-basics",
                score=1.0,
                correct=1,
                total=1,
                evidence=["Correctly explained process and dependency isolation."],
            )
        ],
        learner_model=_learner_model("demo"),
    )


@app.post("/sessions/{session_id}/feedback", response_model=_AcceptedResponse)
def session_feedback(session_id: str, request: _SessionFeedbackRequest) -> _AcceptedResponse:
    del session_id, request
    return _AcceptedResponse(accepted=True, message="Session feedback recorded.")


@app.post(
    "/sessions/{session_id}/alternative-explanation",
    response_model=_AlternativeExplanationResponse,
)
def alternative_explanation(session_id: str) -> _AlternativeExplanationResponse:
    del session_id
    return _AlternativeExplanationResponse(
        content=(
            "A container packages an application and its dependencies while sharing "
            "the host kernel."
        ),
        source_ids=["source-official"],
    )


@app.get("/goals/{goal_id}/dashboard", response_model=_DashboardResponse)
def dashboard(goal_id: str) -> _DashboardResponse:
    del goal_id
    return _DashboardResponse(
        progress=0.4,
        on_track=True,
        deadline_status=DeadlineStatus.ON_TRACK,
        strong=[],
        weak=["containers-basics"],
        next_review=date(2026, 9, 1),
        why="Container basics is the weakest prerequisite.",
        estimated_sessions=4,
        projected_completion=date(2026, 9, 20),
    )


@app.post("/goals/{goal_id}/simulate-day", response_model=_SimulateDayResponse)
def simulate_day(goal_id: str, request: _SimulateDayRequest) -> _SimulateDayResponse:
    del goal_id
    return _SimulateDayResponse(
        events=[
            _Event(day=day, kind="notification", message="Review container basics.")
            for day in range(1, request.days + 1)
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic Learning Manager API stub")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
