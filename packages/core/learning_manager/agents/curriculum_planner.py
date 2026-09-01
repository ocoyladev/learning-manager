from __future__ import annotations

from datetime import date

from learning_manager.contracts import (
    ConstraintViolation,
    LearnerModel,
    LearningGoal,
    LLMProvider,
    NextSessionDecision,
    Source,
    ViolationCode,
)
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
        source_ids = [source.id for source in sources]
        base = (
            f"Goal={goal.model_dump()} model={model.model_dump()} "
            f"concepts={[concept.model_dump() for concept in graph.concepts]} "
            f"sources={source_ids} today={today}"
        )

        def produce(hint: str | None) -> NextSessionDecision:
            d = complete_json(
                self._llm,
                self._trajectory,
                "CurriculumPlanner",
                "",
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

        def validate(decision: NextSessionDecision) -> list[ConstraintViolation]:
            violations = validate_session(decision, goal, model, graph, today)
            for block in decision.blocks:
                for source_id in block.source_ids:
                    if source_id not in source_ids:
                        violations.append(
                            ConstraintViolation(
                                code=ViolationCode.UNSOURCED_CLAIM,
                                concept_id=block.concept_id,
                                message=(
                                    f"{block.concept_id} references unavailable source {source_id}"
                                ),
                            )
                        )
            return violations

        outcome = run_with_repair(
            produce=produce,
            validate=validate,
            repair_prompt=lambda vs: "; ".join(v.message for v in vs),
            fallback=lambda: deterministic_session(goal, model, graph, today, source_ids),
            trajectory=self._trajectory,
        )
        return outcome.value, outcome
