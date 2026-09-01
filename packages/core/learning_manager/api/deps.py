"""Deterministic, request-scoped dependencies for the FastAPI application."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import Request

from learning_manager.contracts import (
    AssessmentItem,
    AuthorityType,
    Concept,
    LearnerModel,
    LearningGoal,
    LLMResponse,
    NextSessionDecision,
    Source,
)
from learning_manager.trajectory.logger import AgentTrajectory, TrajectoryLogger


class DeterministicLLM:
    """Key-free default provider used for API replay and integration tests."""

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        del system, json_schema
        if temperature != 0.0:
            raise ValueError("LLM temperature must be zero")
        if schema_name == "GoalDraft":
            parsed: dict[str, object] = {
                "title": "Structured learning goal",
                "concepts": [
                    {
                        "id": f"foundation-{index}",
                        "name": f"Foundation {index}",
                        "prerequisites": [] if index == 1 else [f"foundation-{index - 1}"],
                        "importance": 1.0 - index / 10,
                        "estimated_minutes": 15,
                    }
                    for index in range(1, 6)
                ],
                "success_criteria": ["Explain the five core foundations."],
            }
        elif schema_name == "ItemDraft":
            concept_ids = re.findall(r"foundation-\d+", user)
            unique_ids = list(dict.fromkeys(concept_ids)) or ["foundation-1"]
            parsed = {
                "items": [
                    AssessmentItem(
                        id=f"diagnostic-{index}",
                        concept_id=concept_id,
                        question=f"What is {concept_id}?",
                        options=["Known", "Unknown"],
                        expected="Known",
                        explanation=f"Checks {concept_id}.",
                    ).model_dump(mode="json")
                    for index, concept_id in enumerate(unique_ids, start=1)
                ]
            }
        elif schema_name == "SourceSelection":
            parsed = {"source_ids": ["deterministic-source"]}
        elif schema_name == "NextSessionDecision":
            # The planner validates this and deliberately takes its deterministic fallback.
            parsed = {
                "session_date": "2000-01-01",
                "blocks": [],
                "total_minutes": 0,
                "rationale": "Use deterministic fallback.",
                "deadline_status": "on_track",
            }
        else:
            raise ValueError(f"unsupported deterministic schema: {schema_name}")
        return LLMResponse(text="", parsed=parsed, model="deterministic-api", cache_hit=True)


class DeterministicKnowledge:
    def research(self, topic: str, *, k: int = 8) -> list[Source]:
        del topic, k
        return [
            Source(
                id="deterministic-source",
                url="https://kubernetes.io/docs/concepts/overview/",
                title="Kubernetes Concepts",
                authority=AuthorityType.OFFICIAL,
                retrieved_at=date(2026, 8, 30),
            )
        ]

    def fetch(self, source_id: str) -> str:
        if source_id != "deterministic-source":
            raise KeyError(source_id)
        return "Deterministic offline Kubernetes source."


@dataclass
class ApiRuntime:
    """In-memory state and providers; replaceable through FastAPI dependency overrides."""

    llm: DeterministicLLM = field(default_factory=DeterministicLLM)
    knowledge: DeterministicKnowledge = field(default_factory=DeterministicKnowledge)
    trajectory_dir: Path = field(
        default_factory=lambda: Path(tempfile.gettempdir()) / "learning-manager-api-trajectories"
    )
    goals: dict[str, tuple[LearningGoal, list[Concept]]] = field(default_factory=dict)
    models: dict[str, LearnerModel] = field(default_factory=dict)
    diagnostics: dict[str, list[AssessmentItem]] = field(default_factory=dict)
    sources: dict[str, list[Source]] = field(default_factory=dict)
    sessions: dict[str, tuple[str, NextSessionDecision]] = field(default_factory=dict)
    paused: set[str] = field(default_factory=set)

    @classmethod
    def in_memory(cls, *, trajectory_dir: Path | None = None) -> ApiRuntime:
        return cls(
            trajectory_dir=trajectory_dir
            or Path(tempfile.gettempdir()) / "learning-manager-api-trajectories"
        )

    def trajectory(self, agent: str, run_id: str) -> AgentTrajectory:
        return TrajectoryLogger(self.trajectory_dir, run_id).for_agent(agent)


_runtime = ApiRuntime.in_memory()


def get_runtime() -> ApiRuntime:
    return _runtime


def request_run_id(request: Request) -> str:
    run_id = getattr(request.state, "run_id", None)
    if run_id is None:
        run_id = str(uuid4())
        request.state.run_id = run_id
    return run_id
