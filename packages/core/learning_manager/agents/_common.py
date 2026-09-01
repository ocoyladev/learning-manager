from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel

from learning_manager.contracts import LLMProvider
from learning_manager.trajectory.logger import AgentTrajectory

T = TypeVar("T", bound=BaseModel)

def complete_json(llm: LLMProvider, trajectory: AgentTrajectory, agent: str, system: str, user: str, schema: type[T], hint: str | None = None) -> T:
    prompt = user if hint is None else f"{user}\n\nREPAIR:\n{hint}"
    response = llm.complete(system=system, user=prompt, schema_name=schema.__name__, json_schema=schema.model_json_schema(), temperature=0.0)
    trajectory.step("llm_call", system=system, user=prompt, model=response.model, cache_hit=response.cache_hit)
    data: Any = response.parsed
    if data is None:
        data = json.loads(response.text)
    return schema.model_validate(data)

