from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from learning_manager.contracts import LLMProvider
from learning_manager.trajectory.logger import AgentTrajectory


def complete_json[T: BaseModel](
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
        "Assessor": "assessor.md",
        "CurriculumPlanner": "curriculum_planner.md",
        "Diagnostician": "diagnostician.md",
        "GoalManager": "goal_manager.md",
        "Teacher": "teaching.md",
    }
    prompt_path = Path(__file__).with_name("prompts") / prompt_names[agent]
    system = prompt_path.read_text(encoding="utf-8")
    response = llm.complete(
        system=system,
        user=prompt,
        schema_name=schema.__name__,
        json_schema=schema.model_json_schema(),
        temperature=0.0,
    )
    trajectory.step(
        "llm_call",
        system=system,
        user=prompt,
        model=response.model,
        cache_hit=response.cache_hit,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        cost_usd=response.cost_usd,
        latency_ms=response.latency_ms,
    )
    data = response.parsed if response.parsed is not None else json.loads(response.text)
    result = schema.model_validate(data)
    trajectory.step("llm_result", result=result)
    return result
