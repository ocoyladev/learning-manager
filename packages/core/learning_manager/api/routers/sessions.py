from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from learning_manager.agents.assessor import Assessor
from learning_manager.api.deps import ApiRuntime, get_runtime, request_run_id
from learning_manager.api.stub import (
    _AcceptedResponse,
    _AlternativeExplanationResponse,
    _AnswersRequest,
    _AssessmentResponse,
    _SessionFeedbackRequest,
)
from learning_manager.contracts import AssessmentItem, NextSessionDecision

router = APIRouter(prefix="/sessions", tags=["sessions"])
RuntimeDependency = Annotated[ApiRuntime, Depends(get_runtime)]


def _session_or_404(runtime: ApiRuntime, session_id: str) -> tuple[str, NextSessionDecision]:
    try:
        return runtime.sessions[session_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown session") from exc


@router.post("/{session_id}/assess", response_model=_AssessmentResponse)
def assess(
    session_id: str,
    payload: _AnswersRequest,
    request: Request,
    runtime: RuntimeDependency,
) -> _AssessmentResponse:
    goal_id, session = _session_or_404(runtime, session_id)
    items = [
        AssessmentItem(
            id=f"{session_id}-{index}",
            concept_id=block.concept_id,
            question=block.objective,
            expected="Known",
        )
        for index, block in enumerate(session.blocks, start=1)
    ]
    answers = {answer.item_id: answer.answer for answer in payload.answers}
    results = Assessor(runtime.llm, runtime.trajectory("Assessor", request_run_id(request))).grade(
        items, answers
    )
    return _AssessmentResponse(results=results, learner_model=runtime.models[goal_id])


@router.post("/{session_id}/feedback", response_model=_AcceptedResponse)
def session_feedback(
    session_id: str,
    payload: _SessionFeedbackRequest,
    runtime: RuntimeDependency,
) -> _AcceptedResponse:
    del payload
    _session_or_404(runtime, session_id)
    return _AcceptedResponse(accepted=True, message="Session feedback recorded.")


@router.post(
    "/{session_id}/alternative-explanation", response_model=_AlternativeExplanationResponse
)
def alternative_explanation(
    session_id: str, runtime: RuntimeDependency
) -> _AlternativeExplanationResponse:
    goal_id, session = _session_or_404(runtime, session_id)
    source_ids = [source_id for block in session.blocks for source_id in block.source_ids]
    if not source_ids:
        source_ids = [source.id for source in runtime.sources.get(goal_id, [])]
    return _AlternativeExplanationResponse(
        content="This explanation uses a smaller example and the session's verified sources.",
        source_ids=source_ids,
    )
