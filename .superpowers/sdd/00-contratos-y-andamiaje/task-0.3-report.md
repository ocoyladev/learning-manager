# Task 0.3 Report: JSONL Trajectory Logging

## RED evidence

Added `packages/core/tests/trajectory/test_logger.py` with the two brief-specified tests before creating the logger module.

Command:

```text
cd packages/core && ../../.venv/bin/pytest tests/trajectory -v
```

Result: collection failed with the expected missing-module error:

```text
ModuleNotFoundError: No module named 'learning_manager.trajectory.logger'
```

## GREEN evidence

Implemented `packages/core/learning_manager/trajectory/logger.py` with `TrajectoryLogger.for_agent()` returning `AgentTrajectory`, and `AgentTrajectory.step()` appending one JSON object per line with UTC metadata.

Focused command:

```text
cd packages/core && ../../.venv/bin/pytest tests/trajectory -v
```

Result: `2 passed`.

## Verification

Commands were run in the requested order after focused GREEN:

1. `cd packages/core && ../../.venv/bin/mypy --strict learning_manager` — passed (`18 source files`).
2. `cd packages/core && ../../.venv/bin/ruff check .` — passed (`All checks passed!`).
3. `cd packages/core && ../../.venv/bin/ruff format --check .` — passed (`29 files already formatted`).
4. `cd packages/core && ../../.venv/bin/pytest -q` — passed (`9 passed`).

`git diff --check` also passed.

## Concerns

Running strict mypy over both source and tests (`mypy --strict learning_manager tests`) reports one pre-existing error in `tests/test_contracts.py:72`: missing named argument `retrieved_at` for `Source`. This task does not modify that test or the frozen contracts module.
