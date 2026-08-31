"""Bounded repair loop for agent-produced decisions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from learning_manager.contracts import ConstraintViolation


class RepairOutcome(BaseModel):
    value: Any
    attempts: int
    violations_per_attempt: list[list[ConstraintViolation]]
    used_fallback: bool


def run_with_repair(
    *,
    produce: Callable[[str | None], Any],
    validate: Callable[[Any], list[ConstraintViolation]],
    repair_prompt: Callable[[list[ConstraintViolation]], str],
    fallback: Callable[[], Any],
    trajectory: Any,
    max_retries: int = 2,
) -> RepairOutcome:
    violations_per_attempt: list[list[ConstraintViolation]] = []
    hint: str | None = None
    for attempt in range(1, max_retries + 2):
        value = produce(hint)
        violations = validate(value)
        violations_per_attempt.append(violations)
        trajectory.step(
            "validation", attempt=attempt, violations=[v.model_dump() for v in violations]
        )
        if not violations:
            trajectory.step("result", attempt=attempt, value=value)
            return RepairOutcome(
                value=value,
                attempts=attempt,
                violations_per_attempt=violations_per_attempt,
                used_fallback=False,
            )
        if attempt <= max_retries:
            hint = repair_prompt(violations)
            trajectory.step("repair_prompt", attempt=attempt + 1, user=hint)
    value = fallback()
    trajectory.step("fallback", attempt=len(violations_per_attempt) + 1, value=value)
    trajectory.step("result", attempt=len(violations_per_attempt) + 1, value=value)
    return RepairOutcome(
        value=value,
        attempts=len(violations_per_attempt),
        violations_per_attempt=violations_per_attempt,
        used_fallback=True,
    )
