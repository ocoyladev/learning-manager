# ruff: noqa: E501,UP047
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from learning_manager.contracts import LLMProvider
from learning_manager.trajectory.logger import AgentTrajectory

T = TypeVar("T", bound=BaseModel)


def complete_json(
    llm: LLMProvider,
    trajectory: AgentTrajectory,
    agent: str,
    system: str,
    user: str,
    schema: type[T],
    hint: str | None = None,
) -> T:
    prompt = user if hint is None else f"{user}\n\nREPAIR:\n{hint}"
    prompt_names = {
        "GoalManager": "goal_manager.md",
        "CurriculumPlanner": "curriculum_planner.md",
        "Teacher": "teaching.md",
    }
    prompt_path = Path(__file__).with_name("prompts") / prompt_names.get(
        agent, f"{agent.lower()}.md"
    )
    system = prompt_path.read_text(encoding="utf-8")
    response = llm.complete(
        system=system,
        user=prompt,
        schema_name=schema.__name__,
        json_schema=schema.model_json_schema(),
        temperature=0.0,
    )
    trajectory.step(
        "llm_call", system=system, user=prompt, model=response.model, cache_hit=response.cache_hit
    )
    data: Any = response.parsed
    if data is None:
        data = json.loads(response.text)
    return schema.model_validate(data)
