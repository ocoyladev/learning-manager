from __future__ import annotations

from learning_manager.contracts import KnowledgeProvider, LLMProvider, Source
from learning_manager.trajectory.logger import AgentTrajectory


class Researcher:
    """Thin orchestration wrapper around the frozen knowledge-provider contract."""

    def __init__(
        self, knowledge: KnowledgeProvider, llm: LLMProvider, trajectory: AgentTrajectory
    ) -> None:
        self._knowledge = knowledge
        self._llm = llm
        self._trajectory = trajectory

    def research(self, topic: str, k: int = 8) -> list[Source]:
        sources = self._knowledge.research(topic, k=k)
        self._trajectory.step("research_result", topic=topic, sources=sources)
        return sources
