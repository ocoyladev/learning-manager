# ruff: noqa: E501,E701,F403,F405,I001
from __future__ import annotations

from pydantic import BaseModel

from learning_manager.contracts import *
from learning_manager.trajectory.logger import AgentTrajectory

from ._common import complete_json


class BlockDraft(BaseModel):
    block: SessionBlock


class Teacher:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory

    def render(
        self,
        block: SessionBlock,
        sources: list[Source],
        model_state: LearnerConceptState | LearnerModel,
        preferred_formats: list[str],
    ) -> SessionBlock:
        result = complete_json(
            self._llm,
            self._trajectory,
            "Teacher",
            "Render concise educational content for the supplied block.",
            f"Block={block.model_dump()} sources={[s.model_dump() for s in sources]} state={model_state.model_dump()} formats={preferred_formats}",
            BlockDraft,
        )
        allowed = {s.id for s in sources}
        out = result.block.model_copy(
            update={
                "content": result.block.content or block.objective,
                "source_ids": [x for x in result.block.source_ids if x in allowed],
                "concept_id": block.concept_id,
                "kind": block.kind,
                "minutes": block.minutes,
                "objective": block.objective,
            }
        )
        self._trajectory.step("result", block=out)
        return out
