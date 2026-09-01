from __future__ import annotations

from pydantic import BaseModel

from learning_manager.contracts import (
    ConstraintViolation,
    LearnerConceptState,
    LearnerModel,
    LLMProvider,
    SessionBlock,
    Source,
    ViolationCode,
)
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.repair import run_with_repair

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
        user = (
            f"Block={block.model_dump()} sources={[source.model_dump() for source in sources]} "
            f"state={model_state.model_dump()} formats={preferred_formats}"
        )
        allowed = {s.id for s in sources}

        def produce(hint: str | None) -> BlockDraft:
            return complete_json(self._llm, self._trajectory, "Teacher", "", user, BlockDraft, hint)

        def validate(result: BlockDraft) -> list[ConstraintViolation]:
            violations: list[ConstraintViolation] = []
            if not result.block.content:
                violations.append(
                    ConstraintViolation(
                        code=ViolationCode.EMPTY_SESSION,
                        message="Rendered teaching block must have content",
                    )
                )
            for source_id in result.block.source_ids:
                if source_id not in allowed:
                    violations.append(
                        ConstraintViolation(
                            code=ViolationCode.UNSOURCED_CLAIM,
                            concept_id=block.concept_id,
                            message=f"Rendered block references unavailable source {source_id}",
                        )
                    )
            return violations

        def fallback() -> BlockDraft:
            return BlockDraft(
                block=block.model_copy(update={"content": block.objective, "source_ids": []})
            )

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda violations: "; ".join(v.message for v in violations),
            fallback=fallback,
            trajectory=self._trajectory,
        )
        result = outcome.value
        if not isinstance(result, BlockDraft):
            raise ValueError("teaching repair produced an unexpected result")
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
