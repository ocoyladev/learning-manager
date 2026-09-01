"""Deterministic scoring for next-session decisions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learning_manager.contracts import BlockKind, NextSessionDecision
from pydantic import BaseModel


class CheckResult(BaseModel):
    name: str
    passed: bool
    points: int
    max_points: int
    detail: str


class CaseScore(BaseModel):
    case_id: str
    checks: list[CheckResult]
    points: int
    max_points: int = 10


class NsdqReport(BaseModel):
    scores: list[CaseScore]
    points: int
    max_points: int
    score: float


def _check(name: str, passed: bool, points: int, detail: str) -> CheckResult:
    return CheckResult(name=name, passed=passed, points=points if passed else 0,
                       max_points=points, detail=detail)


def grade_case(decision: NextSessionDecision, case: dict[str, Any], key: dict[str, Any]) -> CaseScore:
    blocks = decision.blocks
    targeted = {b.concept_id for b in blocks if b.kind in {BlockKind.CONCEPT, BlockKind.PRACTICE}}
    taught = {b.concept_id for b in blocks if b.kind in {BlockKind.CONCEPT, BlockKind.WORKED_EXAMPLE}}
    present = {b.concept_id for b in blocks}
    checks = [
        _check("targets_correct_gap", set(key["must_target"]) <= targeted, 2,
               "All required target concepts are taught or practiced."),
        _check("no_redundant_mastery", not (taught & set(key["must_not_teach_new"])), 2,
               "Mastered concepts are not re-taught."),
        _check("respects_prerequisites", _prerequisites_ok(present, case, key), 2,
               "No blocked concept is introduced before its prerequisites."),
        _check("includes_due_reviews", set(key["must_include_review"]) <= present, 2,
               "All required reviews are present."),
        _check("fits_time_budget", _fits_budget(decision, key), 1,
               "Total minutes fit the configured tolerance."),
        _check("deadline_status_correct", decision.deadline_status.value == key["expected_deadline_status"], 1,
               "Deadline status matches the key."),
    ]
    return CaseScore(case_id=case["case_id"], checks=checks, points=sum(c.points for c in checks))


def _prerequisites_ok(present: set[str], case: dict[str, Any], key: dict[str, Any]) -> bool:
    states = case["learner_model"]
    return all(not (concept in present) or all(states.get(prereq, {}).get("mastery", 0.0) >= 0.70
               for prereq in prereqs) for concept, prereqs in key["forbidden_before"].items())


def _fits_budget(decision: NextSessionDecision, key: dict[str, Any]) -> bool:
    budget = key["time_budget"]
    tolerance = key["time_tolerance"]
    return budget * (1 - tolerance) <= decision.total_minutes <= budget * (1 + tolerance)


def grade_all(decisions: Mapping[str, NextSessionDecision], cases: Iterable[dict[str, Any]],
              keys: Mapping[str, dict[str, Any]]) -> NsdqReport:
    scores = [grade_case(decisions[case["case_id"]], case, keys[case["case_id"]]) for case in cases]
    maximum = sum(score.max_points for score in scores)
    points = sum(score.points for score in scores)
    return NsdqReport(scores=scores, points=points, max_points=maximum,
                      score=points / maximum if maximum else 0.0)
