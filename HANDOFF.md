# Learning Manager Project Handoff

Snapshot: 2026-08-31T12:46:23Z

This document is the operational entry point for the next agent. It records the implementation
state before this handoff-only documentation change. Verify live state again before mutating a
branch; GitHub connectivity was unavailable during the final handoff audit.

## Read first

1. `AGENTS.md`
2. `PLAN.md`
3. `docs/03_decisiones_congeladas.md`
4. `docs/04_arquitectura.md`
5. The phase plan for the branch being resumed

`packages/core/learning_manager/contracts.py` is frozen. `openapi.json` was extended once with
explicit human approval and is frozen again. Neither file may change without new human approval.

## Executive status

- Accepted roadmap progress: 3 of 16 phases complete (Phase 0, Phase 1, and Phase 6), or 18.75%.
- Current approved batch: 3 of 4 work packages accepted (shared API correction, Phase 1, and
  Phase 6), or 75%. Phase 10 is implemented but has unresolved review fixes and is not accepted.
- `master`, Track A, and Track B have passed their latest local and remote checks.
- Track A and Track B are intentionally not merged into `master`.
- Track C has four local commits plus an uncommitted review-fix set. Preserve that worktree.

## Repository state

Repository: `https://github.com/ocoyladev/learning-manager` (private; last verified earlier in
this session). Default branch: `master`.

| Branch | Local SHA | Upstream state at snapshot | Worktree |
|---|---|---|---|
| `master` | `1ddeface4508b0192f488919057ad358bad33999` | matched `origin/master`; clean | repository root |
| `track/a-core` | `1dbc02b1989dfacf56e7ad6486e6d44049f19501` | matched `origin/track/a-core`; clean | `.worktrees/track-a` |
| `track/b-eval` | `9491c509ece4714ad5ef1dda3696e17cf66a548f` | matched `origin/track/b-eval`; clean | `.worktrees/track-b` |
| `track/c-ui` | `29c867331d10f87ba468d2cf15dd7face42afbd3` | four commits ahead of `origin/track/c-ui`; dirty | `.worktrees/track-c` |

Last verified GitHub Actions runs:

- `master`: [CI 33345086974](https://github.com/ocoyladev/learning-manager/actions/runs/33345086974) — `core` and `web` succeeded.
- `track/a-core`: [CI 33355261061](https://github.com/ocoyladev/learning-manager/actions/runs/33355261061) — `core` and `web` succeeded.
- `track/b-eval`: [CI 33354550092](https://github.com/ocoyladev/learning-manager/actions/runs/33354550092) — `core` and `web` succeeded.
- `track/c-ui`: no run for the local commits because the branch has not been pushed.

## Completed work

### Phase 0 and shared API contract on `master`

Phase 0 is 36/36 checked. The repository has the frozen Pydantic contracts, project scaffold,
Compose stack, deterministic logging/trajectory support, FastAPI stub, generated stable OpenAPI,
secret guard, and GitHub CI.

The approved one-time API extension added typed deterministic endpoints for:

- goal sources;
- daily availability and pause state;
- recommendation rejection;
- session feedback;
- alternative explanations.

The change passed independent review after explicit-null and strict-scalar validation fixes.
Local `make check` passed with 34 tests before the merge, and remote `master` CI passed.

### Phase 1 on `track/a-core`

Phase plan: 20/20 checked. Main commits:

- `032bd8a` — pure learner-model transitions;
- `a904c6d` — deterministic prerequisite concept graph;
- `8469996` — seven-table PostgreSQL persistence and four repositories;
- `92a2e42` — learner identity, metadata, and foreign-key integrity fixes;
- `ea983ad` — exact nullable session-decision roundtrips;
- `1dbc02b` — completed phase checklist.

Independent review completed two fix rounds and ended with no findings. Final evidence:

- `make check`: 59 passed, 16 expected database skips;
- real PostgreSQL repository suite: 16 passed in isolated schemas;
- mypy, Ruff, formatting, scope, prohibited-pattern, and frozen-file checks passed.

The track-local PostgreSQL container/network used for verification was removed without deleting
its named volume.

### Phase 6 on `track/b-eval`

Phase plan: 20/20 checked. Main commits:

- `969d598` — FakeLLM and cost meter;
- `3e26308` — cassette record/replay provider;
- `4cbbfef` — Gemini provider and settings-driven factory;
- `0e5fd24` — p95 and fake/replay/live instrumentation coverage;
- `9491c50` — completed phase checklist.

Independent review ended ready to push. Final evidence:

- provider tests: 23 passed;
- `make check`: 57 passed;
- mypy, Ruff, formatting, scope, security, and frozen-file checks passed;
- official `google-genai` usage is isolated to `providers/llm/gemini.py`;
- no Phase 6 handoff artifact is tracked.

## Current work: Phase 10 on `track/c-ui`

The first implementation is split into four local commits:

- `1aabd3d` — generated API client and test tooling;
- `199314d` — onboarding and diagnostic experience;
- `66a5ac0` — daily session, dashboard, sources, and human controls;
- `29c8673` — component and Playwright coverage.

That committed head passed API generation, strict typecheck, lint, two component tests, one
Playwright journey on ports 3100/8011, production build, and root `make check` (34 tests).
Independent review nevertheless rejected it for the following real gaps:

1. Docker-built rewrites and server fetches targeted container-local `localhost:8000` instead
   of the Compose `api` service.
2. Multi-item diagnostics submitted one answer at a time and lost earlier answers.
3. Route pages converted every backend failure into a false 404.
4. The session-completion UI did not re-fetch the learner model or display assessment evidence,
   confidence/state/review changes.
5. Nullable session IDs fell back to an invented ID and errors were styled as success feedback.
6. Native form validation lacked accessible inline messages.
7. The E2E used a direct dashboard navigation, a date that will become stale, and did not exercise
   available feedback or human controls.

A review-fix agent implemented an uncommitted fix set but hit the shared model usage limit before
full verification and commit. Current dirty scope:

- 12 modified files under `apps/web/`;
- `apps/web/scripts/verify-docker-routing.mjs`;
- `DiagnosticFlow.test.tsx` and `TodaySession.test.tsx`.

The interrupted agent recorded two meaningful RED cases: early diagnostic submission and enabled
session controls without an ID. The nullable-session test became green; the diagnostic test had
just been corrected and was being rerun. Treat the entire dirty fix set as unverified.

## Resume Track C

1. Enter `.worktrees/track-c` and inspect `git status` and the complete diff. Preserve every
   current file; do not reset or recreate the worktree.
2. Finish the review fixes against the findings above. Confirm `package-lock.json` remains
   consistent; the current `package.json` change only adds a verification script.
3. Run the full gate from `apps/web/`:

   ```bash
   npm run generate:api
   npm run typecheck
   npm run lint
   npm test
   npm run test:e2e
   API_ORIGIN=http://api:8000 npm run build
   npm run verify:docker-routing
   ```

4. From the worktree root, run:

   ```bash
   make check
   git diff --check
   ```

5. Confirm only `apps/web/` changed; `contracts.py` and `openapi.json` must remain untouched.
   Confirm no `any`, `console.log`, TODO, build output, Playwright artifacts, or handwritten API
   payload contracts are tracked.
6. Commit the reviewed fix as `fix(web): complete typed learning workflow behavior`.
7. Regenerate the SDD review package and request a fresh independent review. Fix every Critical
   and Important finding before proceeding.
8. Only after a clean review: mark Phase 10 checkboxes, run the full gate again, push
   `track/c-ui`, and wait for both remote CI jobs.

Track C completion criterion: clean worktree, independently accepted review, all local commands
green, branch pushed, and GitHub `core` plus `web` jobs successful.

## Remaining roadmap

- Track A: Phases 2–5 — scheduler, verifier/repair, five agents, API/worker.
- Track B: Phases 7–9 — research/sources, frozen corpus/cases, evaluation/baseline/graders.
- Track C: complete Phase 10, then Phases 11–12 — Telegram and optional official WhatsApp.
- Sequential: Phases 13–15 — end-to-end integration, measured evaluation/changelog, submission
  deliverables and video.

Do not merge Track A, B, or C into `master` without a new explicit human integration decision.
Before any approved merge, rebase the track on current `master`, resolve only reviewed conflicts,
run the complete track gate, and require green CI.

## Environment notes

- Host ports 3000 and 8000 are occupied by unrelated containers. Port 8001 was also occupied at
  the last check. Preserve those processes; Track C uses 3100/8011.
- Activate the worktree virtual environment before committing so the `pre-commit` executable is
  available: `source .venv/bin/activate`.
- PostgreSQL integration tests require a real database. The proven approach starts only the
  track-local Compose `db` service and runs tests from a temporary Python container on the same
  Compose network.
- `.superpowers/sdd/` reports and ledgers are ignored handoff artifacts. Do not force-add them.
- `.codebase-memory/` exists and the main project was indexed earlier. `.codegraph/` is currently
  absent; follow `AGENTS.md` and ask before initializing it.
- The GitHub API became unreachable during the final audit. Re-run `gh auth status`, branch
  comparison, and CI queries when network access returns.
- Lightweight subagents hit a shared usage limit while finishing the Track C review fixes. Resume
  from the preserved worktree rather than repeating implementation.
