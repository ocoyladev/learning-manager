from __future__ import annotations

from pydantic import BaseModel

from learning_manager.contracts import KnowledgeProvider, LLMProvider, Source
from learning_manager.trajectory.logger import AgentTrajectory

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
        selection = complete_json(
            self._llm,
            self._trajectory,
            "Researcher",
            "",
            f"Topic: {topic}\nCandidate sources: {serialized_sources}",
            SourceSelection,
        )
        selected_ids = set(selection.source_ids)
        filtered = [source for source in sources if source.id in selected_ids]
        self._trajectory.step(
            "result",
            topic=topic,
            sources=[source.model_dump(mode="json") for source in filtered],
        )
        return filtered
