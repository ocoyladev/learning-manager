# Phase 4 fix round 4 report

## Requirement mapping

| Requirement | Implementation and focused coverage |
| --- | --- |
| Planner fallback validity | `curriculum_planner.py` validates source IDs; `fallback.py` receives only planner-supplied IDs and uses retrieval when none are available. `test_phase4_smoke.py::test_planner_fallback_is_valid_for_due_review_and_uses_supplied_source`. |
| Validation and repair | `repair.py` handles typed parse/validation errors; `goal_manager.py`, `diagnostician.py`, `assessor.py`, and `teaching.py` use the shared loop. The diagnostic coverage and cyclic graph cases are covered in `test_phase4_smoke.py`. |
| Assessor retrieval policy | `assessor.py` prioritizes seen state, mastery, misconception evidence, oldest assessment, then concept ID; it rewrites the returned target ID. Covered by `test_retrieval_prefers_seen_then_misconception_then_oldest_and_forces_target`. |
| Trajectories | `_common.py` records model/cache/token/cost/latency metadata and parsed results. Deterministic grade/research steps are recorded in `diagnostician.py`, `assessor.py`, and `researcher.py`. Teacher uses the supplied planner trajectory object. |
| Diagnostic grading | `diagnostician.py` now derives states with `domain.learner_model.derive_state` and leaves unanswered concepts unseen. |
| Acceptance tests | `test_phase4_smoke.py` supplements smoke coverage with planner fallback/source, diagnostic repair, retrieval ordering/target enforcement, GoalManager repair/metadata, and Researcher trajectory cases. |

## Verification

- Focused agents/verification suite: 16 passed.
- Full gate: `make check` passes (96 passed, 16 skipped; one existing FastAPI/httpx deprecation warning).
- `git diff --check` passes; `contracts.py` and `openapi.json` are unchanged from `eda1a9c`.

## Commit

Recorded after final verification in the Phase 4 Track A branch.

## Remaining concern

The FastAPI test client emits an upstream Starlette deprecation warning for the installed `httpx`; it does not affect the Phase 4 behavior or gate status.
