from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from learning_manager.api.deps import ApiRuntime, get_runtime
from learning_manager.api.stub import _DashboardResponse
from learning_manager.contracts import ConceptState, DeadlineStatus

router = APIRouter(prefix="/goals", tags=["dashboard"])
RuntimeDependency = Annotated[ApiRuntime, Depends(get_runtime)]


@router.get("/{goal_id}/dashboard", response_model=_DashboardResponse)
def dashboard(goal_id: str, runtime: RuntimeDependency) -> _DashboardResponse:
    try:
        goal, concepts = runtime.goals[goal_id]
        model = runtime.models[goal_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown goal") from exc
    states = model.concepts
    progress = sum(state.mastery for state in states.values()) / len(states) if states else 0.0
    strong = [concept_id for concept_id, state in states.items() if state.mastery >= 0.85]
    weak = [
        concept.id
        for concept in concepts
        if concept.id not in states or states[concept.id].state is not ConceptState.MASTERED
    ]
    next_review = min(
        (state.next_review for state in states.values() if state.next_review is not None),
        default=None,
    )
    return _DashboardResponse(
        progress=progress,
        on_track=True,
        deadline_status=DeadlineStatus.ON_TRACK,
        strong=strong,
        weak=weak,
        next_review=next_review,
        why="The next session targets the weakest unlocked concept.",
        estimated_sessions=max(0, len(concepts) - len(strong)),
        projected_completion=goal.deadline,
    )
