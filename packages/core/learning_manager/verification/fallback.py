"""Deterministic safe session fallback."""

from __future__ import annotations

from datetime import date

from learning_manager.contracts import (
    BlockKind,
    LearnerModel,
    LearningGoal,
    NextSessionDecision,
    SessionBlock,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.scheduler.feasibility import deadline_status
from learning_manager.scheduler.spacing import REVIEW_MINUTES, due_reviews, prioritize_reviews


def deterministic_session(
    goal: LearningGoal,
    model: LearnerModel,
    graph: ConceptGraph,
    today: date,
    source_ids: list[str] | None = None,
) -> NextSessionDecision:
    supplied_source_ids = source_ids or []
    budget = goal.daily_minutes
    blocks: list[SessionBlock] = []
    due = prioritize_reviews(model, due_reviews(model, today), budget, graph)
    for cid in due:
        blocks.append(
            SessionBlock(
                kind=BlockKind.REVIEW if supplied_source_ids else BlockKind.RETRIEVAL,
                concept_id=cid,
                minutes=REVIEW_MINUTES,
                objective=f"Review {cid}",
                content=None,
                source_ids=supplied_source_ids[:1],
            )
        )
        budget -= REVIEW_MINUTES
    unlocked = [
        cid
        for cid in graph.unlocked(model)
        if model.concepts.get(cid) is None or model.concepts[cid].mastery < 0.85
    ]
    for cid in unlocked:
        if budget <= 0:
            break
        if not supplied_source_ids:
            break
        concept = next(c for c in graph.concepts if c.id == cid)
        minutes = min(budget, concept.estimated_minutes)
        blocks.append(
            SessionBlock(
                kind=BlockKind.CONCEPT,
                concept_id=cid,
                minutes=minutes,
                objective=f"Learn {concept.name}",
                content=None,
                source_ids=supplied_source_ids[:1],
            )
        )
        budget -= minutes
    if not blocks and graph.concepts:
        blocks.append(
            SessionBlock(
                kind=BlockKind.RETRIEVAL,
                concept_id=graph.concepts[0].id,
                minutes=min(REVIEW_MINUTES, goal.daily_minutes),
                objective="Retrieve prior knowledge",
                content=None,
            )
        )
    return NextSessionDecision(
        session_date=today,
        blocks=blocks,
        total_minutes=sum(b.minutes for b in blocks),
        rationale=(
            "Deterministic scheduler fallback prioritizes due reviews and the weakest "
            "unlocked concept."
        ),
        reviews_included=[b.concept_id for b in blocks if b.kind == BlockKind.REVIEW],
        deadline_status=deadline_status(goal, model, graph, today),
    )
