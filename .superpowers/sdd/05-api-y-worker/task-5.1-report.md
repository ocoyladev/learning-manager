# Phase 5.1 report — FastAPI routers

## Requirement mapping

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Frozen goal, diagnostic, research, source, planning, session, dashboard and simulation endpoints | `packages/core/learning_manager/api/app.py`, `api/routers/*.py` | `packages/core/tests/api/test_endpoints.py` |
| Exact frozen request and response payload models | Routers reuse the existing frozen-schema models from `api/stub.py` and `NextSessionDecision` from `contracts.py` | Happy-path, validation, and endpoint-availability tests |
| Phase 4 orchestration | `goals.py` invokes GoalManager, Diagnostician, Researcher, and CurriculumPlanner; `sessions.py` invokes Assessor | Full happy-path test |
| Deterministic, key-free defaults and dependency override | `api/deps.py` supplies deterministic LLM/knowledge providers and replaceable `ApiRuntime` | Dependency-override test |
| Explicit session date | `goals.py` requires `today: date` for next-session and passes it to CurriculumPlanner | `test_next_session_obeys_openapi_model_and_explicit_today` |
| Request-scoped trajectories | Middleware assigns UUID run IDs; agents receive run-specific trajectories from `ApiRuntime` | Dependency-override trajectory test |
| Missing resources | Goal and session lookup helpers return 404 rather than fixtures | Unknown-ID test |

## Verification

`make VENV_PYTHON=/home/ocoyla/personal/hackaton/.venv/bin/python check` passed: mypy, ruff,
format check, and pytest (116 passed, 16 skipped).
