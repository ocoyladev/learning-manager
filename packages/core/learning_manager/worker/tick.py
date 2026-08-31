import time
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import structlog

from learning_manager.contracts import AssessmentResult, LearnerModel, NotificationProvider, Reply
from learning_manager.domain.learner_model import apply_assessment
from learning_manager.scheduler.spacing import next_review_date

logger = structlog.get_logger(__name__)


class LearnerModelStore(Protocol):
    def get(self, goal_id: str) -> LearnerModel: ...

    def save(self, model: LearnerModel) -> None: ...


@dataclass(frozen=True)
class WorkerEvent:
    kind: str
    message: str
    concept_id: str | None = None


def tick(
    *,
    today: date,
    dry_run: bool,
    notifier: NotificationProvider,
    repo: LearnerModelStore,
    goal_id: str = "g1",
    user_ref: str = "u1",
) -> list[WorkerEvent]:
    """Send one due retrieval question and incorporate its reply."""
    model = repo.get(goal_id)
    due = [
        state
        for state in model.concepts.values()
        if state.next_review is not None and state.next_review <= today
    ]
    if not due:
        return []
    state = min(due, key=lambda item: item.mastery)
    misconception = state.misconceptions[0] if state.misconceptions else state.concept_id
    message = f"Quick retrieval: what is the correct explanation for {misconception}?"
    event = WorkerEvent("retrieval_question", message, state.concept_id)
    if dry_run:
        return [event]
    notifier.send(
        user_ref=user_ref,
        message=message,
        options=["ClusterIP", "NodePort", "LoadBalancer"],
    )
    replies: list[Reply] = notifier.poll_replies()
    reply = next((item for item in replies if item.user_ref == user_ref), None)
    if reply is None:
        return [event]
    expected = "clusterip" in misconception.lower() or state.concept_id == "services"
    score = 1.0 if expected and reply.text.strip().lower() == "clusterip" else 0.0
    result = AssessmentResult(concept_id=state.concept_id, score=score, correct=int(score), total=1)
    updated = apply_assessment(state, result, today).model_copy(
        update={"next_review": next_review_date(score, today)}
    )
    repo.save(model.model_copy(update={"concepts": {**model.concepts, state.concept_id: updated}}))
    return [event, WorkerEvent("learner_model_updated", "Learner model updated", state.concept_id)]


def run() -> None:
    logger.info("worker_started")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    run()
