from datetime import UTC, date, datetime

from learning_manager.contracts import ConceptState, LearnerConceptState, LearnerModel, Reply
from learning_manager.worker.tick import tick


class ScriptedNotifier:
    def __init__(self, text: str) -> None:
        self.text = text
        self.sent: list[tuple[str, str, list[str] | None]] = []

    def send(self, *, user_ref: str, message: str, options: list[str] | None = None) -> str:
        self.sent.append((user_ref, message, options))
        return "notification-1"

    def poll_replies(self) -> list[Reply]:
        return [Reply(user_ref="u1", text=self.text, received_at=datetime.now(UTC))]


class MemoryRepo:
    def __init__(self, model: LearnerModel) -> None:
        self.model = model

    def get(self, goal_id: str) -> LearnerModel:
        return self.model

    def save(self, model: LearnerModel) -> None:
        self.model = model


TODAY = date(2025, 1, 10)


def test_answer_updates_learner_model_and_reschedules() -> None:
    state = LearnerConceptState(
        concept_id="services",
        mastery=0.2,
        confidence=0.2,
        state=ConceptState.WEAK,
        next_review=TODAY,
        misconceptions=["ClusterIP is for external traffic"],
    )
    repo = MemoryRepo(LearnerModel(goal_id="g1", concepts={"services": state}))
    events = tick(today=TODAY, dry_run=False, notifier=ScriptedNotifier("ClusterIP"), repo=repo)
    after = repo.get("g1").concepts["services"]
    assert after.mastery > state.mastery
    assert after.next_review is not None and after.next_review > TODAY
    assert any(event.kind == "retrieval_question" for event in events)


def test_question_targets_recorded_misconception() -> None:
    state = LearnerConceptState(
        concept_id="services",
        mastery=0.2,
        confidence=0.2,
        state=ConceptState.WEAK,
        next_review=TODAY,
        misconceptions=["ClusterIP is for external traffic"],
    )
    events = tick(
        today=TODAY,
        dry_run=True,
        notifier=ScriptedNotifier("ClusterIP"),
        repo=MemoryRepo(LearnerModel(goal_id="g1", concepts={"services": state})),
    )
    question = next(event for event in events if event.kind == "retrieval_question")
    assert "ClusterIP" in question.message
