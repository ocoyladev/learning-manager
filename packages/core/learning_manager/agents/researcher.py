from __future__ import annotations

from pydantic import BaseModel

from learning_manager.contracts import (
    ConstraintViolation,
    KnowledgeProvider,
    LLMProvider,
    Source,
    ViolationCode,
)
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.repair import run_with_repair

from ._common import complete_json


class SourceSelection(BaseModel):
    """LLM judgement restricted to IDs returned by the knowledge provider."""

    source_ids: list[str]


class Researcher:
    """Use the LLM to organize sources retrieved by the injected provider."""

    def __init__(
        self, knowledge: KnowledgeProvider, llm: LLMProvider, trajectory: AgentTrajectory
    ) -> None:
        self._knowledge = knowledge
        self._llm = llm
        self._trajectory = trajectory

    def research(self, topic: str, k: int = 8) -> list[Source]:
        sources = self._knowledge.research(topic, k=k)
        serialized_sources = [source.model_dump(mode="json") for source in sources]
        self._trajectory.step("provider_retrieval", topic=topic, sources=serialized_sources)
        user = f"Topic: {topic}\nCandidate sources: {serialized_sources}"
        available_ids = {source.id for source in sources}

        def produce(hint: str | None) -> SourceSelection:
            return complete_json(
                self._llm,
                self._trajectory,
                "Researcher",
                "",
                user,
                SourceSelection,
                hint,
            )

        def validate(selection: SourceSelection) -> list[ConstraintViolation]:
            unknown_ids = sorted(set(selection.source_ids) - available_ids)
            return [
                ConstraintViolation(
                    code=ViolationCode.UNSOURCED_CLAIM,
                    message=f"Selected source {source_id} was not returned by the provider",
                )
                for source_id in unknown_ids
            ]

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda violations: "; ".join(
                violation.message for violation in violations
            ),
            fallback=lambda: SourceSelection(source_ids=[source.id for source in sources]),
            trajectory=self._trajectory,
        )
        selection = outcome.value
        if not isinstance(selection, SourceSelection):
            raise ValueError("research repair produced an unexpected result")
        selected_ids = set(selection.source_ids)
        filtered = [source for source in sources if source.id in selected_ids]
        self._trajectory.step(
            "result",
            topic=topic,
            sources=[source.model_dump(mode="json") for source in filtered],
        )
        return filtered
