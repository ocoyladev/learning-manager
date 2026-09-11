# Learning Manager

A persistent agent that takes a learner from a stated goal to verifiable mastery — and is
built to prove, with deterministic metrics, that it decides *what to study next* better than a
single-prompt LLM baseline.

Sole developer. The starting point was the Micro1 hackathon brief; the project continued as a
standalone agentic application and was not submitted.

> **Status:** in development. 13 of 16 planned phases are implemented on the track branches
> (`track/a-core`, `track/b-eval`, `track/c-ui`). Merging the tracks, end-to-end integration
> against recorded cassettes, the evaluation runs and the final deliverables are pending.

## Architecture

A headless Python core — five LLM agents plus a **deterministic scheduler and verifier** —
behind a FastAPI service, with a Next.js App Router UI and Telegram / WhatsApp channels.

```
Next.js (App Router)  ·  Telegram  ·  WhatsApp Cloud API
                    │
              FastAPI service  ──────────────  background worker
                    │                          (atomic claim on due reviews)
   ┌────────────────┼─────────────────┐
   ▼                ▼                 ▼
learner model   scheduler        verifier
(PostgreSQL)    (deterministic)  (repair loop + fallback)
                    │
              5 LLM agents (versioned prompts)
                    │
          record/replay provider layer → Gemini API
```

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · PostgreSQL 16 · Next.js 15 ·
TypeScript · Docker Compose · GitHub Actions · Gemini API · Telegram Bot API · WhatsApp Cloud
API.

## Engineering constraints, enforced mechanically

Not by convention — by tests and CI gates:

- **Record/replay provider layer.** Every LLM call goes through it, so evaluation is
  reproducible and the suite runs in CI with no API keys.
- **Frozen contracts.** A system-wide contracts module and a frozen OpenAPI spec; the API
  implements the spec rather than the spec documenting the API.
- **Temperature 0** across production and evaluation calls.
- **No `datetime.now()` in business logic**, guarded by a test — time is injected, so
  scheduling is testable and deterministic.
- **Strict TDD** in the domain, scheduler and verification layers; `mypy --strict` on the core.
- **CI determinism gate** alongside lint, typecheck and test.
- Spec-driven delivery across a versioned 16-phase plan, with JSONL agent-trajectory logging.

## Tracks

| Track | Content |
|---|---|
| **core** (`track/a-core`) | Learner model with PostgreSQL repositories, deterministic scheduler with deadline-feasibility checks, constraint verifier with repair loop and fallback, the five agents with versioned prompts, FastAPI endpoints implementing the frozen OpenAPI contract, background worker with an atomic claim on due reviews and a day-simulation mode |
| **eval** (`track/b-eval`) | Gemini provider with retries, record/replay cassettes and a cost meter, source retrieval with authority and version verification, a frozen evaluation corpus of 11 cases, deterministic graders, and a frozen single-prompt baseline |
| **ui** (`track/c-ui`) | Onboarding and diagnostic flow, daily-session dashboard with human controls over a generated typed API client, and console / Telegram / WhatsApp notification providers |

## Documents

| Path | What it is |
|---|---|
| `02_learning_manager_especificacion.md` | Product and system specification |
| `docs/03_decisiones_congeladas.md` | Frozen decisions |
| `docs/04_arquitectura.md` | Architecture |
| `docs/05_evaluacion.md` | Evaluation method: corpus, graders, baseline |
| `plan/00..15-*.md` | The 16-phase implementation plan |

## Running it

```bash
cp .env.example .env        # a Gemini API key is only needed for live calls
docker compose up -d        # PostgreSQL
make help                   # available targets
```

The test suite runs against recorded cassettes and needs no API key.

## License

MIT — see [LICENSE](LICENSE).
