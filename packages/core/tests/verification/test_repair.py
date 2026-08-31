from learning_manager.contracts import ConstraintViolation, ViolationCode
from learning_manager.verification.repair import run_with_repair


class Recorder:
    def __init__(self) -> None:
        self.steps: list[tuple[str, dict[str, object]]] = []

    def step(self, name: str, **fields: object) -> None:
        self.steps.append((name, fields))


def test_valid_first_attempt() -> None:
    out = run_with_repair(
        produce=lambda hint: "ok",
        validate=lambda value: [],
        repair_prompt=lambda value: "fix",
        fallback=lambda: "fb",
        trajectory=Recorder(),
    )
    assert out.value == "ok" and out.attempts == 1 and not out.used_fallback


def test_repair_then_success() -> None:
    bad = [ConstraintViolation(code=ViolationCode.EMPTY_SESSION, message="m")]
    out = run_with_repair(
        produce=lambda hint: "bad" if hint is None else "good",
        validate=lambda value: bad if value == "bad" else [],
        repair_prompt=lambda value: "EMPTY_SESSION",
        fallback=lambda: "fb",
        trajectory=Recorder(),
    )
    assert out.value == "good" and out.attempts == 2


def test_fallback_after_retries_is_logged() -> None:
    recorder = Recorder()
    bad = [ConstraintViolation(code=ViolationCode.EMPTY_SESSION, message="m")]
    out = run_with_repair(
        produce=lambda hint: "bad",
        validate=lambda value: bad,
        repair_prompt=lambda value: "fix",
        fallback=lambda: "safe",
        trajectory=recorder,
        max_retries=2,
    )
    assert out.value == "safe" and out.used_fallback and out.attempts == 3
    assert [name for name, _ in recorder.steps].count("validation") == 3
    assert "fallback" in [name for name, _ in recorder.steps]
