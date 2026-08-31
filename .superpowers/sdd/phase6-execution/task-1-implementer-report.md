# Phase 6 Task 1 — Implementer Report

## Outcome

Phase 6 Task 1 is implemented on `track/b-eval` in three Conventional Commits. The provider
tests and the repository checks pass without API keys or network access.

## TDD evidence

- Fake/meter RED: `pytest tests/providers/test_fake.py tests/providers/test_meter.py` failed at
  collection because `fake.py` and `meter.py` did not exist.
- Fake/meter GREEN: 7 focused tests passed; the slice was committed as `969d598`.
- Cassette RED: `pytest tests/providers/test_cached.py` failed at collection because `cached.py`
  did not exist.
- Cassette GREEN: 7 focused tests passed, including live/replay, replay isolation, miss repair
  instructions, model/request key changes, special-character collision resistance, complete
  request auditability, and malformed cassette handling. The slice was committed as `3e26308`.
- Gemini/factory RED: `pytest tests/providers/test_gemini.py` failed at collection because
  `factory.py` did not exist.
- Gemini/factory GREEN: 6 focused tests passed, covering structured output, forced temperature,
  usage/latency capture, transient retry, non-transient fail-fast behavior, factory mode wiring,
  exactly-once meter/trajectory instrumentation, and missing-key configuration errors. The slice
  was committed as `6bf680f`.

## Verification evidence

- All provider tests: `20 passed`.
- Full `make check`: mypy clean (26 source files), Ruff clean, format check clean, `54 passed`.
- `git diff --check`: clean.
- Direct Google SDK scan: no `google.genai`/`genai.Client` usage outside `gemini.py`.
- Secret/logging scan: no print/console logging, TODO markers, or committed key values in
  production changes. Test fixtures use a non-functional sentinel only.
- Frozen interface scan: `contracts.py` and `openapi.json` are untouched.
- Worktree is clean after the report is added and included in the final task commit.

## Changed files

Production:

- `packages/core/learning_manager/providers/llm/fake.py` — deterministic finite/callable fake,
  JSON parsing, call and prompt observability, optional meter/trajectory instrumentation.
- `packages/core/learning_manager/providers/llm/meter.py` — immutable `CostSummary`, token/cost
  aggregation, cache-hit accounting, deterministic p50/p95 latency, and verified Gemini pricing.
- `packages/core/learning_manager/providers/llm/cached.py` — SHA-256 keyed atomic cassette
  record/replay, auditable requests, typed miss/malformed errors, and instrumentation.
- `packages/core/learning_manager/providers/llm/gemini.py` — official `google-genai` adapter with
  JSON structured output, 60-second timeout, usage metadata, monotonic latency, and bounded
  429/5xx exponential retries.
- `packages/core/learning_manager/providers/llm/factory.py` — settings-driven fake/replay/live
  construction, typed key configuration error, and concrete provider preservation.

Tests:

- `packages/core/tests/providers/test_fake.py`
- `packages/core/tests/providers/test_meter.py`
- `packages/core/tests/providers/test_cached.py`
- `packages/core/tests/providers/test_gemini.py`

## Deviations and residual concerns

- CodeGraph was not initialized in either the worktree or repository, so the mandated graph
  lookup was attempted and reported unavailable; existing interfaces were then read directly.
- The frozen contract has no configuration/settings class yet. `factory.py` therefore declares a
  private structural settings Protocol and uses conventional lowercase settings attributes with
  safe defaults, leaving the passed settings object authoritative whenever an attribute exists.
- Gemini SDK tests inject a fake client at the SDK boundary, so no `respx` route or real network is
  involved. Live calls use the installed official SDK only in `gemini.py`.
- The report is intentionally outside the provider/test ownership directories because the task
  explicitly requires this handoff artifact; no other out-of-track files were written.
