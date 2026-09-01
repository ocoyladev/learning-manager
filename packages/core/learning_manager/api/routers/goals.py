from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from learning_manager.agents.curriculum_planner import CurriculumPlanner
from learning_manager.agents.diagnostician import Diagnostician
from learning_manager.agents.goal_manager import GoalManager
from learning_manager.agents.researcher import Researcher
from learning_manager.api.deps import ApiRuntime, get_runtime, request_run_id
from learning_manager.api.stub import (
    _AcceptedResponse,
    _AnswersRequest,
    _DiagnosticResponse,
    _GoalDetailsResponse,
    _GoalRequest,
    _GoalResponse,
    _GoalUpdateRequest,
    _GoalUpdateResponse,
    _LearnerResponse,
    _RecommendationRejectionRequest,
    _ResearchRequest,
    _ResearchResponse,
)
from learning_manager.contracts import Concept, LearnerModel, LearningGoal, NextSessionDecision
from learning_manager.domain.concept_graph import ConceptGraph

router = APIRouter(prefix="/goals", tags=["goals"])
RuntimeDependency = Annotated[ApiRuntime, Depends(get_runtime)]


def _goal_or_404(runtime: ApiRuntime, goal_id: str) -> tuple[LearningGoal, list[Concept]]:
    try:
        return runtime.goals[goal_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown goal") from exc


@router.post("", response_model=_GoalResponse)
def create_goal(
    payload: _GoalRequest,
    request: Request,
    runtime: RuntimeDependency,
) -> _GoalResponse:
    goal, concepts = GoalManager(
        runtime.llm, runtime.trajectory("GoalManager", request_run_id(request))
    ).run(
        payload.title,
        payload.purpose,
        payload.deadline,
        payload.daily_minutes,
        payload.preferred_formats,
    )
    runtime.goals[goal.id] = (goal, concepts)
    runtime.models[goal.id] = LearnerModel(goal_id=goal.id)
    return _GoalResponse(goal=goal, concepts=concepts)


@router.get("/{goal_id}", response_model=_GoalDetailsResponse)
def get_goal(goal_id: str, runtime: RuntimeDependency) -> _GoalDetailsResponse:
    goal, concepts = _goal_or_404(runtime, goal_id)
    return _GoalDetailsResponse(goal=goal, concepts=concepts, learner_model=runtime.models[goal_id])


@router.patch("/{goal_id}", response_model=_GoalUpdateResponse)
def update_goal(
    goal_id: str, payload: _GoalUpdateRequest, runtime: RuntimeDependency
) -> _GoalUpdateResponse:
    goal, concepts = _goal_or_404(runtime, goal_id)
    if "daily_minutes" in payload.model_fields_set:
        goal = goal.model_copy(update={"daily_minutes": payload.daily_minutes})
        runtime.goals[goal_id] = (goal, concepts)
    if payload.paused:
        runtime.paused.add(goal_id)
    else:
        runtime.paused.discard(goal_id)
    return _GoalUpdateResponse(goal=goal, paused=goal_id in runtime.paused)


@router.post("/{goal_id}/diagnostic", response_model=_DiagnosticResponse)
def diagnostic(goal_id: str, request: Request, runtime: RuntimeDependency) -> _DiagnosticResponse:
    goal, concepts = _goal_or_404(runtime, goal_id)
    items = Diagnostician(
        runtime.llm, runtime.trajectory("Diagnostician", request_run_id(request))
    ).generate(goal, concepts, n_items=5)
    runtime.diagnostics[goal_id] = items
    return _DiagnosticResponse(items=items)


@router.post("/{goal_id}/diagnostic/answers", response_model=_LearnerResponse)
def diagnostic_answers(
    goal_id: str, payload: _AnswersRequest, request: Request, runtime: RuntimeDependency
) -> _LearnerResponse:
    _goal_or_404(runtime, goal_id)
    items = runtime.diagnostics.get(goal_id)
    if items is None:
        raise HTTPException(status_code=409, detail="Diagnostic has not been generated")
    agent = Diagnostician(runtime.llm, runtime.trajectory("Diagnostician", request_run_id(request)))
    agent._concept_ids = [item.concept_id for item in items]
    answers = {answer.item_id: answer.answer for answer in payload.answers}
    model = agent.grade(items, answers, today=date(1970, 1, 1)).model_copy(
        update={"goal_id": goal_id}
    )
    runtime.models[goal_id] = model
    return _LearnerResponse(learner_model=model)


@router.post("/{goal_id}/research", response_model=_ResearchResponse)
def research(
    goal_id: str,
    payload: _ResearchRequest,
    request: Request,
    runtime: RuntimeDependency,
) -> _ResearchResponse:
    _goal_or_404(runtime, goal_id)
    sources = Researcher(
        runtime.knowledge, runtime.llm, runtime.trajectory("Researcher", request_run_id(request))
    ).research(payload.topic)
    runtime.sources[goal_id] = sources
    return _ResearchResponse(sources=sources)


@router.get("/{goal_id}/sources", response_model=_ResearchResponse)
def sources(goal_id: str, runtime: RuntimeDependency) -> _ResearchResponse:
    _goal_or_404(runtime, goal_id)
    return _ResearchResponse(sources=runtime.sources.get(goal_id, []))


@router.post("/{goal_id}/recommendations/reject", response_model=_AcceptedResponse)
def reject_recommendation(
    goal_id: str,
    payload: _RecommendationRejectionRequest,
    runtime: RuntimeDependency,
) -> _AcceptedResponse:
    del payload
    _goal_or_404(runtime, goal_id)
    return _AcceptedResponse(accepted=True, message="Recommendation rejected.")


@router.get("/{goal_id}/next-session", response_model=NextSessionDecision)
def next_session(
    goal_id: str,
    today: date,
    request: Request,
    runtime: RuntimeDependency,
) -> NextSessionDecision:
    goal, concepts = _goal_or_404(runtime, goal_id)
    decision, _ = CurriculumPlanner(
        runtime.llm, runtime.trajectory("CurriculumPlanner", request_run_id(request))
    ).next_session(
        goal,
        runtime.models[goal_id],
        ConceptGraph(concepts),
        runtime.sources.get(goal_id, []),
        today,
    )
    session_id = decision.id or uuid4().hex
    decision = decision.model_copy(update={"id": session_id})
    runtime.sessions[session_id] = (goal_id, decision)
    return decision
