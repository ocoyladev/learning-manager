# ruff: noqa: E501,F403,F405
from __future__ import annotations

from datetime import date

from learning_manager.contracts import *
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.scheduler.feasibility import deadline_status
from learning_manager.trajectory.logger import AgentTrajectory
from learning_manager.verification.constraints import validate_session
from learning_manager.verification.fallback import deterministic_session
from learning_manager.verification.repair import RepairOutcome, run_with_repair

from ._common import complete_json


class CurriculumPlanner:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None:
        self._llm, self._trajectory = llm, trajectory

    def next_session(
        self,
        goal: LearningGoal,
        model: LearnerModel,
        graph: ConceptGraph,
        sources: list[Source],
        today: date,
    ) -> tuple[NextSessionDecision, RepairOutcome]:
        base = f"Goal={goal.model_dump()} model={model.model_dump()} concepts={[c.model_dump() for c in graph.concepts]} sources={[s.id for s in sources]} today={today}"

        def produce(hint: str | None) -> NextSessionDecision:
            d = complete_json(
                self._llm,
                self._trajectory,
                "CurriculumPlanner",
                "Plan the next adaptive learning session.",
                base,
                NextSessionDecision,
                hint,
            )
            return d.model_copy(
                update={
                    "session_date": today,
                    "deadline_status": deadline_status(goal, model, graph, today),
                }
            )

        outcome = run_with_repair(
            produce=produce,
            validate=lambda d: validate_session(d, goal, model, graph, today),
            repair_prompt=lambda vs: "; ".join(v.message for v in vs),
            fallback=lambda: deterministic_session(goal, model, graph, today),
            trajectory=self._trajectory,
        )
        return outcome.value, outcome
