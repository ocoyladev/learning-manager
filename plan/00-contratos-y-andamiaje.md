# Fase 0 — Contratos y andamiaje

**Pista:** ninguna (SECUENCIAL, bloquea todo) · **Duración objetivo:** 2 h · **Checkpoint:** CP0

> ⛔ **Ninguna otra fase arranca hasta que esta esté commiteada en `main` y CI esté verde.**
> Todo el paralelismo de las siguientes 20 horas depende de que los contratos aquí definidos
> no cambien.

**Entrega:** `contracts.py` congelado · `docker compose up` con 4 servicios · CI en verde ·
`TrajectoryLogger` funcionando · `openapi.json` + stub server para la Pista C.

---

## Tarea 0.1 — Esqueleto del repositorio

**Ficheros:**
- Crear: `packages/core/pyproject.toml`, `packages/core/learning_manager/__init__.py`,
  `packages/core/tests/__init__.py`, `Makefile`, `.env.example`

- [x] **Paso 1: crear el árbol de directorios**

```bash
mkdir -p packages/core/learning_manager/{domain,scheduler,verification,trajectory,agents/prompts,persistence/migrations,api/routers,worker,providers/{llm,knowledge,notify}}
mkdir -p packages/core/tests/{domain,scheduler,verification,trajectory,agents,persistence,api,providers}
mkdir -p eval/{cases/nsdq,cases/sources,keys,baseline,graders} corpus fixtures/cassettes experiments trajectories
find packages/core/learning_manager packages/core/tests -type d -exec touch {}/__init__.py \;
```

- [x] **Paso 2: `packages/core/pyproject.toml`**

```toml
[project]
name = "learning-manager"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "pydantic>=2.9",
  "pydantic-settings>=2.5",
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy>=2.0",
  "psycopg[binary]>=3.2",
  "alembic>=1.14",
  "google-genai>=0.3",
  "httpx>=0.27",
  "typer>=0.13",
  "structlog>=24.4",
]

[project.optional-dependencies]
dev = ["pytest>=8.3", "pytest-cov>=6.0", "ruff>=0.8", "mypy>=1.13", "freezegun>=1.5", "respx>=0.21"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "T20"]   # T20 prohíbe print()

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [x] **Paso 3: `.env.example`** (se commitea; `.env` NO)

```bash
# ---- LLM ----
# replay = sin keys, determinista, POR DEFECTO. live = real. fake = solo tests.
LLM_MODE=replay
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash          # verificar el ID vigente antes de usar live
LLM_TEMPERATURE=0

# ---- Conocimiento ----
KNOWLEDGE_PROVIDER=corpus              # corpus | live
CORPUS_PATH=./corpus

# ---- Base de datos ----
DATABASE_URL=postgresql+psycopg://lm:lm@db:5432/learning_manager

# ---- Scheduler y notificaciones ----
SCHEDULER_MODE=simulation              # simulation | real  (base R4: simulation por defecto)
NOTIFY_PROVIDER=console                # console | telegram | whatsapp
NOTIFY_LIVE=false                      # true exige confirmación humana explícita
TELEGRAM_BOT_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=

# ---- Trazas ----
TRAJECTORY_DIR=./runs
```

- [x] **Paso 4: commit**

```bash
git add packages/core/pyproject.toml .env.example
git commit -m "chore: scaffold repository structure and dependencies"
```

---

## Tarea 0.2 — `contracts.py` (⛔ CONGELADO al terminar)

**Ficheros:**
- Crear: `packages/core/learning_manager/contracts.py`
- Test: `packages/core/tests/test_contracts.py`

**Interfaces producidas:** todo lo que consumen las 15 fases siguientes. Los nombres y tipos
de aquí son los que verán agentes que nunca leerán esta fase.

- [x] **Paso 1: escribir el test que falla**

```python
# packages/core/tests/test_contracts.py
from datetime import date
import pytest
from pydantic import ValidationError
from learning_manager.contracts import (
    BlockKind, ConceptState, DeadlineStatus, LearningGoal, Concept,
    LearnerConceptState, LearnerModel, SessionBlock, NextSessionDecision,
    Source, AuthorityType, ConstraintViolation, LLMResponse,
)


def test_learning_goal_rejects_absurd_daily_minutes() -> None:
    with pytest.raises(ValidationError):
        LearningGoal(id="g", title="t", purpose="p", deadline=date(2026, 9, 20), daily_minutes=0)


def test_next_session_total_minutes_must_match_blocks() -> None:
    block = SessionBlock(kind=BlockKind.CONCEPT, concept_id="services", minutes=10,
                         objective="Entender ClusterIP")
    with pytest.raises(ValidationError):
        NextSessionDecision(session_date=date(2026, 9, 5), blocks=[block], total_minutes=99,
                            rationale="r", deadline_status=DeadlineStatus.ON_TRACK)


def test_next_session_computes_total_when_consistent() -> None:
    blocks = [
        SessionBlock(kind=BlockKind.CONCEPT, concept_id="services", minutes=10, objective="o1"),
        SessionBlock(kind=BlockKind.REVIEW, concept_id="volumes", minutes=5, objective="o2"),
    ]
    d = NextSessionDecision(session_date=date(2026, 9, 5), blocks=blocks, total_minutes=15,
                            rationale="r", deadline_status=DeadlineStatus.ON_TRACK)
    assert d.total_minutes == 15


def test_mastery_is_bounded() -> None:
    with pytest.raises(ValidationError):
        LearnerConceptState(concept_id="pods", mastery=1.5, confidence=0.5,
                            state=ConceptState.MASTERED)


def test_source_requires_retrieved_at() -> None:
    s = Source(id="s1", url="https://kubernetes.io/docs/", title="Services",
               authority=AuthorityType.OFFICIAL, retrieved_at=date(2026, 8, 30))
    assert s.version is None and s.published_at is None
```

- [x] **Paso 2: ejecutar y confirmar el fallo**

Run: `cd packages/core && pytest tests/test_contracts.py -v`
Esperado: `ModuleNotFoundError: No module named 'learning_manager.contracts'`

- [x] **Paso 3: escribir `contracts.py`**

```python
"""Fuente única de verdad del sistema.

⛔ CONGELADO tras la Fase 0. Ningún agente puede modificar este fichero sin aprobación
humana explícita: tres pistas trabajan en paralelo confiando en estas firmas.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field, model_validator

# ─────────────────────────── Enumeraciones ───────────────────────────


class ConceptState(str, Enum):
    UNSEEN = "unseen"
    INTRODUCED = "introduced"
    WEAK = "weak"
    DEVELOPING = "developing"
    MASTERED = "mastered"
    REVIEW_DUE = "review_due"


class BlockKind(str, Enum):
    CONCEPT = "concept"
    WORKED_EXAMPLE = "worked_example"
    PRACTICE = "practice"
    RETRIEVAL = "retrieval"
    REVIEW = "review"


class AuthorityType(str, Enum):
    OFFICIAL = "official"
    VENDOR = "vendor"
    BOOK = "book"
    BLOG = "blog"
    TUTORIAL = "tutorial"
    FORUM = "forum"
    UNKNOWN = "unknown"


class DeadlineStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    INFEASIBLE = "infeasible"


class ViolationCode(str, Enum):
    PREREQ_VIOLATION = "PREREQ_VIOLATION"
    REDUNDANT_MASTERED = "REDUNDANT_MASTERED"
    TIME_BUDGET_EXCEEDED = "TIME_BUDGET_EXCEEDED"
    MISSING_DUE_REVIEW = "MISSING_DUE_REVIEW"
    UNKNOWN_CONCEPT = "UNKNOWN_CONCEPT"
    EMPTY_SESSION = "EMPTY_SESSION"
    UNSOURCED_CLAIM = "UNSOURCED_CLAIM"


# ─────────────────────────── Dominio ───────────────────────────

MASTERY_THRESHOLD = 0.85
"""Por encima de esto un concepto se considera dominado y no se re-enseña."""

PREREQ_THRESHOLD = 0.70
"""Mínimo de mastery de un prerrequisito para desbloquear el concepto siguiente."""


class LearningGoal(BaseModel):
    id: str
    title: str
    purpose: str
    deadline: date
    daily_minutes: int = Field(ge=5, le=240)
    preferred_formats: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class Concept(BaseModel):
    id: str
    name: str
    prerequisites: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    estimated_minutes: int = Field(default=15, ge=1, le=180)


class LearnerConceptState(BaseModel):
    concept_id: str
    mastery: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    state: ConceptState
    last_seen: date | None = None
    last_assessed: date | None = None
    next_review: date | None = None
    misconceptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class LearnerModel(BaseModel):
    goal_id: str
    concepts: dict[str, LearnerConceptState] = Field(default_factory=dict)
    updated_at: datetime | None = None


class SessionBlock(BaseModel):
    kind: BlockKind
    concept_id: str
    minutes: int = Field(ge=1, le=180)
    objective: str
    content: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class NextSessionDecision(BaseModel):
    """Salida del CurriculumPlanner. Es lo que NSDQ califica."""

    id: str | None = None
    """Lo asigna la capa de persistencia al guardar. None mientras vive en memoria."""

    session_date: date
    blocks: list[SessionBlock]
    total_minutes: int = Field(ge=0)
    rationale: str
    reviews_included: list[str] = Field(default_factory=list)
    deferred_concepts: list[str] = Field(default_factory=list)
    deadline_status: DeadlineStatus

    @model_validator(mode="after")
    def _total_matches_blocks(self) -> NextSessionDecision:
        expected = sum(b.minutes for b in self.blocks)
        if self.total_minutes != expected:
            raise ValueError(f"total_minutes={self.total_minutes} but blocks sum to {expected}")
        return self


class Source(BaseModel):
    id: str
    url: str
    title: str
    authority: AuthorityType
    version: str | None = None
    published_at: date | None = None
    retrieved_at: date
    content_path: str | None = None


class ConstraintViolation(BaseModel):
    code: ViolationCode
    message: str
    concept_id: str | None = None


class AssessmentItem(BaseModel):
    id: str
    concept_id: str
    question: str
    options: list[str] = Field(default_factory=list)
    expected: str
    explanation: str = ""


class AssessmentResult(BaseModel):
    concept_id: str
    score: float = Field(ge=0.0, le=1.0)
    correct: int
    total: int
    misconceptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


# ─────────────────────────── Providers ───────────────────────────


class LLMResponse(BaseModel):
    text: str
    parsed: dict[str, object] | None = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    cache_hit: bool = False


@runtime_checkable
class LLMProvider(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse: ...


@runtime_checkable
class KnowledgeProvider(Protocol):
    def research(self, topic: str, *, k: int = 8) -> list[Source]: ...
    def fetch(self, source_id: str) -> str: ...


class Reply(BaseModel):
    user_ref: str
    text: str
    received_at: datetime
    message_ref: str | None = None


@runtime_checkable
class NotificationProvider(Protocol):
    def send(
        self, *, user_ref: str, message: str, options: list[str] | None = None
    ) -> str: ...
    def poll_replies(self) -> list[Reply]: ...
```

- [x] **Paso 4: ejecutar y confirmar que pasa**

Run: `cd packages/core && pytest tests/test_contracts.py -v`
Esperado: 5 passed

- [x] **Paso 5: commit y marcar como congelado**

```bash
git add packages/core/learning_manager/contracts.py packages/core/tests/test_contracts.py
git commit -m "feat(contracts): freeze system-wide contracts

FROZEN. No agent may modify without explicit human approval."
```

---

## Tarea 0.3 — TrajectoryLogger

**Ficheros:**
- Crear: `packages/core/learning_manager/trajectory/logger.py`
- Test: `packages/core/tests/trajectory/test_logger.py`

**Interfaces consumidas:** ninguna. **Producidas:** `TrajectoryLogger.step()`, `.for_agent()`.

> Se escribe AHORA, no al final. Las trayectorias son un entregable obligatorio (§9.4) y
> reconstruirlas a posteriori es imposible.

- [x] **Paso 1: test que falla**

```python
# packages/core/tests/trajectory/test_logger.py
import json
from pathlib import Path
from learning_manager.trajectory.logger import TrajectoryLogger


def test_writes_one_json_object_per_line(tmp_path: Path) -> None:
    log = TrajectoryLogger(run_dir=tmp_path, run_id="run1")
    agent = log.for_agent("CurriculumPlanner")
    agent.step("llm_call", attempt=1, model="gemini-x")
    agent.step("validation", attempt=1, violations=[])

    lines = (tmp_path / "run1" / "CurriculumPlanner.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["agent"] == "CurriculumPlanner"
    assert first["step"] == "llm_call"
    assert first["attempt"] == 1
    assert "ts" in first


def test_separate_file_per_agent(tmp_path: Path) -> None:
    log = TrajectoryLogger(run_dir=tmp_path, run_id="run2")
    log.for_agent("Assessor").step("start")
    log.for_agent("Researcher").step("start")
    files = {p.name for p in (tmp_path / "run2").iterdir()}
    assert files == {"Assessor.jsonl", "Researcher.jsonl"}
```

- [x] **Paso 2: ejecutar y confirmar el fallo**

Run: `cd packages/core && pytest tests/trajectory -v` → `ModuleNotFoundError`

- [x] **Paso 3: implementar**

```python
# packages/core/learning_manager/trajectory/logger.py
"""Registro JSONL de trayectorias. Entregable §9.4 de la hackathon."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AgentTrajectory:
    def __init__(self, path: Path, agent: str) -> None:
        self._path = path
        self._agent = agent
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def step(self, step: str, **fields: Any) -> None:
        record: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "agent": self._agent,
            "step": step,
        }
        record.update(fields)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


class TrajectoryLogger:
    def __init__(self, run_dir: Path, run_id: str) -> None:
        self._dir = Path(run_dir) / run_id

    def for_agent(self, agent: str) -> AgentTrajectory:
        return AgentTrajectory(self._dir / f"{agent}.jsonl", agent)
```

- [x] **Paso 4: ejecutar** → `pytest tests/trajectory -v` → 2 passed
- [x] **Paso 5: commit** → `git commit -m "feat(trajectory): add JSONL agent trajectory logger"`

---

## Tarea 0.4 — Docker Compose y Makefile

**Ficheros:** Crear `docker-compose.yml`, `packages/core/Dockerfile`, `apps/web/Dockerfile`, `Makefile`

- [x] **Paso 1: `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: lm
      POSTGRES_PASSWORD: lm
      POSTGRES_DB: learning_manager
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lm -d learning_manager"]
      interval: 3s
      timeout: 3s
      retries: 20

  api:
    build: { context: ., dockerfile: packages/core/Dockerfile }
    env_file: [.env]
    environment:
      DATABASE_URL: postgresql+psycopg://lm:lm@db:5432/learning_manager
    depends_on:
      db: { condition: service_healthy }
    ports: ["8000:8000"]
    volumes:
      - ./corpus:/app/corpus:ro
      - ./fixtures:/app/fixtures:ro
      - ./runs:/app/runs
    command: uvicorn learning_manager.api.app:app --host 0.0.0.0 --port 8000

  worker:
    build: { context: ., dockerfile: packages/core/Dockerfile }
    env_file: [.env]
    environment:
      DATABASE_URL: postgresql+psycopg://lm:lm@db:5432/learning_manager
    depends_on:
      db: { condition: service_healthy }
    volumes:
      - ./corpus:/app/corpus:ro
      - ./fixtures:/app/fixtures:ro
      - ./runs:/app/runs
    command: python -m learning_manager.worker.tick

  web:
    build: { context: ./apps/web }
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [api]
    ports: ["3000:3000"]

volumes:
  pgdata:
```

- [x] **Paso 2: `packages/core/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY packages/core/pyproject.toml /app/packages/core/
RUN pip install --upgrade pip && pip install -e /app/packages/core
COPY packages/core /app/packages/core
COPY eval /app/eval
ENV PYTHONPATH=/app/packages/core
```

- [x] **Paso 3: `Makefile`**

```makefile
.PHONY: setup up down check test stub-api eval-replay eval-live record simulate trajectories

setup:
	python3.12 -m venv .venv && . .venv/bin/activate && pip install -e "packages/core[dev]"

up:
	docker compose up -d --build && docker compose ps

down:
	docker compose down

check:
	cd packages/core && ruff check . && ruff format --check . && mypy learning_manager && pytest

test:
	cd packages/core && pytest

stub-api:
	python -m learning_manager.api.stub --port 8001

eval-replay:
	LLM_MODE=replay python -m eval.runner --name $(or $(NAME),replay)

eval-live:
	LLM_MODE=live python -m eval.runner --name $(or $(NAME),live)

record:
	LLM_MODE=live python -m learning_manager.cli record-cassettes

simulate:
	python -m learning_manager.cli simulate-day --days $(or $(DAYS),5)

trajectories:
	python -m learning_manager.cli export-trajectories --out trajectories/
```

- [x] **Paso 4: verificar** → `docker compose config -q` sin errores; `make up` levanta `db` y `api` sanos
- [x] **Paso 5: commit** → `git commit -m "chore: add docker compose stack and Makefile"`

---

## Tarea 0.5 — CI en GitHub Actions

**Ficheros:** Crear `.github/workflows/ci.yml`

> Con tres agentes en paralelo, CI es lo único que detecta que una pista rompió a otra.

- [x] **Paso 1: escribir el workflow**

```yaml
name: CI
on: [push, pull_request]
jobs:
  core:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e "packages/core[dev]"
      - run: cd packages/core && ruff check .
      - run: cd packages/core && ruff format --check .
      - run: cd packages/core && mypy learning_manager
      - run: cd packages/core && pytest --cov=learning_manager --cov-report=term-missing
      - name: Evaluación determinista (sin keys)
        env: { LLM_MODE: replay }
        run: python -m eval.runner --name ci --check-determinism
      - name: Ningún secreto commiteado
        run: |
          ! git ls-files | grep -E '(^|/)\.env$' || (echo "ERROR: .env commiteado" && exit 1)
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "24" }
      - run: cd apps/web && npm ci && npm run lint && npx tsc --noEmit && npm run build
```

> `--check-determinism` ejecuta el runner dos veces y falla si los resultados difieren.
> Se implementa en la Fase 9; hasta entonces el paso puede marcarse `continue-on-error: true`.

- [x] **Paso 2: commit** → `git commit -m "ci: add lint, typecheck, test and determinism gate"`

---

## Tarea 0.6 — `openapi.json` congelado y stub server

**Ficheros:** Crear `openapi.json`, `packages/core/learning_manager/api/stub.py`

> Desbloquea a la Pista C: la UI se construye contra el stub sin esperar a la Fase 5.

- [x] **Paso 1: definir los endpoints congelados**

| Método | Ruta | Cuerpo | Devuelve |
|---|---|---|---|
| POST | `/goals` | `{title, purpose, deadline, daily_minutes, preferred_formats}` | `{goal: LearningGoal, concepts: Concept[]}` |
| GET | `/goals/{id}` | — | `{goal, concepts, learner_model}` |
| POST | `/goals/{id}/diagnostic` | — | `{items: AssessmentItem[]}` |
| POST | `/goals/{id}/diagnostic/answers` | `{answers: [{item_id, answer}]}` | `{learner_model: LearnerModel}` |
| POST | `/goals/{id}/research` | `{topic}` | `{sources: Source[]}` |
| GET | `/goals/{id}/next-session` | `?today=YYYY-MM-DD` | `NextSessionDecision` |
| POST | `/sessions/{id}/assess` | `{answers: [...]}` | `{results: AssessmentResult[], learner_model}` |
| GET | `/goals/{id}/dashboard` | — | `{progress, on_track, deadline_status, strong[], weak[], next_review, why, estimated_sessions, projected_completion}` |
| POST | `/goals/{id}/simulate-day` | `{days}` | `{events: [...]}` |

- [x] **Paso 2: generar `openapi.json`** desde modelos FastAPI vacíos con esas firmas y commitearlo
- [x] **Paso 3: `stub.py`** — sirve `openapi.json` y devuelve datos de ejemplo fijos para cada ruta
- [x] **Paso 4: verificar** → `make stub-api` y `curl localhost:8001/goals/demo/dashboard` responde
- [x] **Paso 5: commit** → `git commit -m "feat(api): freeze OpenAPI contract and add stub server"`

---

## Tarea 0.7 — Hook de pre-commit contra secretos

**Ficheros:** Crear `.pre-commit-config.yaml`

- [x] **Paso 1:**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
        args: ["--maxkb=2048"]
      - id: end-of-file-fixer
  - repo: local
    hooks:
      - id: no-env-file
        name: bloquear .env
        entry: bash -c 'git diff --cached --name-only | grep -qE "(^|/)\.env$" && { echo "ERROR: no commitear .env"; exit 1; } || exit 0'
        language: system
        pass_filenames: false
```

- [x] **Paso 2:** `pre-commit install` y commit

---

## ✅ Criterio de salida — CP0

- [x] `contracts.py` commiteado y sus tests pasan
- [x] `make check` en verde
- [x] `docker compose up` levanta `db`, `api`, `worker`, `web` sin errores
- [ ] CI verde en el primer push
- [x] `make stub-api` responde en `:8001`
- [x] `TrajectoryLogger` escribe JSONL correcto
- [x] `.env` bloqueado por el hook
- [ ] **Solo entonces:** crear `track/a-core`, `track/b-eval`, `track/c-ui` y lanzar las 3 pistas
