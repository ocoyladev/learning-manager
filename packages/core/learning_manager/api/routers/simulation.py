from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from learning_manager.api.deps import ApiRuntime, get_runtime
from learning_manager.api.stub import _Event, _SimulateDayRequest, _SimulateDayResponse

router = APIRouter(prefix="/goals", tags=["simulation"])
RuntimeDependency = Annotated[ApiRuntime, Depends(get_runtime)]


@router.post("/{goal_id}/simulate-day", response_model=_SimulateDayResponse)
def simulate_day(
    goal_id: str,
    payload: _SimulateDayRequest,
    runtime: RuntimeDependency,
) -> _SimulateDayResponse:
    if goal_id not in runtime.goals:
        raise HTTPException(status_code=404, detail="Unknown goal")
    return _SimulateDayResponse(
        events=[
            _Event(day=day, kind="notification", message="Review your scheduled concept.")
            for day in range(1, payload.days + 1)
        ]
    )
