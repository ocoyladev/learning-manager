# Fase 1 — Learner model y persistencia

**Pista:** A · **Depende de:** F0 · **Duración objetivo:** 2,5 h · **TDD estricto: SÍ**

**Entrega:** actualización pura del modelo del alumno + repositorios Postgres.

> El §11 de la especificación dice que el corazón del producto no es un historial de chat sino
> un modelo estructurado del alumno. Esta fase construye ese corazón, y es **pura**: sin IO,
> sin LLM, testeable exhaustivamente.

---

## Tarea 1.1 — Transición de estado de un concepto

**Ficheros:**
- Crear: `packages/core/learning_manager/domain/learner_model.py`
- Test: `packages/core/tests/domain/test_learner_model.py`

**Interfaces consumidas:** `contracts.LearnerConceptState`, `ConceptState`, `AssessmentResult`,
`MASTERY_THRESHOLD`.
**Interfaces producidas:**
`derive_state(mastery: float, confidence: float, next_review: date | None, today: date) -> ConceptState`
`apply_assessment(state: LearnerConceptState, result: AssessmentResult, today: date) -> LearnerConceptState`

- [x] **Paso 1: escribir el test que falla**

```python
# packages/core/tests/domain/test_learner_model.py
from datetime import date
from learning_manager.contracts import (
    AssessmentResult, ConceptState, LearnerConceptState,
)
from learning_manager.domain.learner_model import apply_assessment, derive_state

TODAY = date(2026, 9, 5)


def test_derive_state_unseen_when_never_assessed() -> None:
    assert derive_state(0.0, 0.0, None, TODAY) is ConceptState.UNSEEN


def test_derive_state_mastered_above_threshold() -> None:
    assert derive_state(0.90, 0.85, None, TODAY) is ConceptState.MASTERED


def test_derive_state_weak_below_half() -> None:
    assert derive_state(0.30, 0.70, None, TODAY) is ConceptState.WEAK


def test_derive_state_review_due_wins_over_mastered() -> None:
    # Un concepto dominado cuyo repaso vence HOY debe marcarse REVIEW_DUE:
    # es lo que permite al planner detectar el olvido (spec §12).
    assert derive_state(0.90, 0.85, date(2026, 9, 5), TODAY) is ConceptState.REVIEW_DUE


def test_apply_assessment_moves_mastery_toward_score() -> None:
    before = LearnerConceptState(concept_id="services", mastery=0.30, confidence=0.60,
                                 state=ConceptState.WEAK)
    result = AssessmentResult(concept_id="services", score=0.90, correct=9, total=10)
    after = apply_assessment(before, result, TODAY)
    assert 0.30 < after.mastery < 0.90          # media móvil, no salto directo
    assert after.confidence > before.confidence  # más evidencia ⇒ más confianza
    assert after.last_assessed == TODAY


def test_apply_assessment_accumulates_misconceptions_without_duplicates() -> None:
    before = LearnerConceptState(concept_id="services", mastery=0.30, confidence=0.60,
                                 state=ConceptState.WEAK,
                                 misconceptions=["confunde ClusterIP con NodePort"])
    result = AssessmentResult(concept_id="services", score=0.4, correct=4, total=10,
                              misconceptions=["confunde ClusterIP con NodePort",
                                              "cree que Ingress es un Service"])
    after = apply_assessment(before, result, TODAY)
    assert len(after.misconceptions) == 2


def test_apply_assessment_clears_resolved_misconceptions_on_high_score() -> None:
    before = LearnerConceptState(concept_id="services", mastery=0.60, confidence=0.70,
                                 state=ConceptState.DEVELOPING,
                                 misconceptions=["confunde ClusterIP con NodePort"])
    result = AssessmentResult(concept_id="services", score=1.0, correct=10, total=10)
    after = apply_assessment(before, result, TODAY)
    assert after.misconceptions == []


def test_apply_assessment_is_pure() -> None:
    before = LearnerConceptState(concept_id="pods", mastery=0.5, confidence=0.5,
                                 state=ConceptState.DEVELOPING)
    apply_assessment(before, AssessmentResult(concept_id="pods", score=1.0, correct=1, total=1),
                     TODAY)
    assert before.mastery == 0.5   # el original no se muta
```

- [x] **Paso 2: ejecutar y confirmar el fallo**

Run: `cd packages/core && pytest tests/domain/test_learner_model.py -v`
Esperado: `ModuleNotFoundError: No module named 'learning_manager.domain.learner_model'`

- [x] **Paso 3: implementar el mínimo**

```python
# packages/core/learning_manager/domain/learner_model.py
"""Actualización del modelo del alumno. Puro: sin IO, sin LLM, sin reloj del sistema."""

from __future__ import annotations

from datetime import date

from learning_manager.contracts import (
    MASTERY_THRESHOLD,
    AssessmentResult,
    ConceptState,
    LearnerConceptState,
)

LEARNING_RATE = 0.6
"""Peso de la evidencia nueva frente a la estimación previa. Media móvil exponencial."""

CONFIDENCE_GAIN = 0.15
MISCONCEPTION_CLEAR_SCORE = 0.9


def derive_state(
    mastery: float, confidence: float, next_review: date | None, today: date
) -> ConceptState:
    if next_review is not None and next_review <= today:
        return ConceptState.REVIEW_DUE
    if confidence == 0.0 and mastery == 0.0:
        return ConceptState.UNSEEN
    if mastery >= MASTERY_THRESHOLD:
        return ConceptState.MASTERED
    if mastery < 0.35:
        return ConceptState.WEAK
    if mastery < 0.50:
        return ConceptState.INTRODUCED
    return ConceptState.DEVELOPING


def apply_assessment(
    state: LearnerConceptState, result: AssessmentResult, today: date
) -> LearnerConceptState:
    mastery = round(
        state.mastery * (1 - LEARNING_RATE) + result.score * LEARNING_RATE, 4
    )
    confidence = round(min(1.0, state.confidence + CONFIDENCE_GAIN), 4)

    if result.score >= MISCONCEPTION_CLEAR_SCORE:
        misconceptions: list[str] = []
    else:
        seen = list(state.misconceptions)
        for m in result.misconceptions:
            if m not in seen:
                seen.append(m)
        misconceptions = seen

    evidence = [*state.evidence, *result.evidence]

    return state.model_copy(
        update={
            "mastery": mastery,
            "confidence": confidence,
            "state": derive_state(mastery, confidence, state.next_review, today),
            "last_assessed": today,
            "last_seen": today,
            "misconceptions": misconceptions,
            "evidence": evidence,
        }
    )
```

- [x] **Paso 4: ejecutar** → 8 passed
- [x] **Paso 5: commit** → `git commit -m "feat(domain): add pure learner model state transitions"`

---

## Tarea 1.2 — Grafo de conceptos

**Ficheros:**
- Crear: `packages/core/learning_manager/domain/concept_graph.py`
- Test: `packages/core/tests/domain/test_concept_graph.py`

**Interfaces producidas:**
`ConceptGraph(concepts: list[Concept])`, `.unlocked(model, today) -> list[str]`,
`.blocked_by(concept_id, model) -> list[str]`, `.topological_order() -> list[str]`,
`.detect_cycle() -> list[str] | None`

- [x] **Paso 1: test que falla**

```python
# packages/core/tests/domain/test_concept_graph.py
import pytest
from learning_manager.contracts import Concept, ConceptState, LearnerConceptState, LearnerModel
from learning_manager.domain.concept_graph import ConceptGraph, CyclicGraphError

CONCEPTS = [
    Concept(id="pods", name="Pods"),
    Concept(id="services", name="Services", prerequisites=["pods"]),
    Concept(id="ingress", name="Ingress", prerequisites=["services"]),
]


def _model(**mastery: float) -> LearnerModel:
    return LearnerModel(goal_id="g", concepts={
        cid: LearnerConceptState(concept_id=cid, mastery=m, confidence=0.8,
                                 state=ConceptState.DEVELOPING)
        for cid, m in mastery.items()
    })


def test_unlocked_includes_roots() -> None:
    g = ConceptGraph(CONCEPTS)
    assert "pods" in g.unlocked(_model())


def test_ingress_locked_while_services_is_weak() -> None:
    g = ConceptGraph(CONCEPTS)
    unlocked = g.unlocked(_model(pods=0.9, services=0.3))
    assert "services" in unlocked
    assert "ingress" not in unlocked


def test_ingress_unlocks_when_services_passes_threshold() -> None:
    g = ConceptGraph(CONCEPTS)
    assert "ingress" in g.unlocked(_model(pods=0.9, services=0.75))


def test_blocked_by_names_the_missing_prerequisites() -> None:
    g = ConceptGraph(CONCEPTS)
    assert g.blocked_by("ingress", _model(pods=0.9, services=0.3)) == ["services"]


def test_topological_order_respects_dependencies() -> None:
    order = ConceptGraph(CONCEPTS).topological_order()
    assert order.index("pods") < order.index("services") < order.index("ingress")


def test_cycle_is_rejected_at_construction() -> None:
    cyclic = [Concept(id="a", name="A", prerequisites=["b"]),
              Concept(id="b", name="B", prerequisites=["a"])]
    with pytest.raises(CyclicGraphError):
        ConceptGraph(cyclic)


def test_unknown_prerequisite_is_rejected() -> None:
    bad = [Concept(id="a", name="A", prerequisites=["ghost"])]
    with pytest.raises(ValueError, match="ghost"):
        ConceptGraph(bad)
```

- [x] **Paso 2: ejecutar y confirmar el fallo**
- [x] **Paso 3: implementar** `ConceptGraph` con validación en el constructor (ciclos y
      prerrequisitos inexistentes), `unlocked` usando `PREREQ_THRESHOLD` de `contracts`,
      y orden topológico por Kahn.
- [x] **Paso 4: ejecutar** → 7 passed
- [x] **Paso 5: commit** → `git commit -m "feat(domain): add concept graph with prerequisite gating"`

---

## Tarea 1.3 — Persistencia Postgres

**Ficheros:**
- Crear: `packages/core/learning_manager/persistence/models.py`,
  `packages/core/learning_manager/persistence/repositories.py`,
  `packages/core/learning_manager/persistence/migrations/001_initial.sql`
- Test: `packages/core/tests/persistence/test_repositories.py`

**Interfaces producidas:**
`GoalRepository.save(goal, concepts)`, `.get(goal_id) -> tuple[LearningGoal, list[Concept]]`
`LearnerModelRepository.get(goal_id) -> LearnerModel`, `.save(model)`
`SessionRepository.save(decision) -> str`, `.get(session_id) -> NextSessionDecision`
`SourceRepository.save_many(sources)`, `.by_ids(ids) -> list[Source]`

Tablas (del §37 de la especificación): `users`, `learning_goals`, `concepts`,
`learner_concept_states`, `assessment_attempts`, `sessions`, `sources`.

- [x] **Paso 1: test que falla** — usar Postgres real vía compose, no SQLite; el test se salta
      con `pytest.mark.skipif` si `DATABASE_URL` no apunta a un Postgres accesible.

```python
# packages/core/tests/persistence/test_repositories.py
import os
from datetime import date
import pytest
from learning_manager.contracts import Concept, ConceptState, LearnerConceptState, LearnerModel, LearningGoal
from learning_manager.persistence.repositories import GoalRepository, LearnerModelRepository

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="requiere Postgres (docker compose up db)"
)


def test_goal_roundtrip(session_factory) -> None:
    repo = GoalRepository(session_factory)
    goal = LearningGoal(id="g1", title="K8s", purpose="entrevista",
                        deadline=date(2026, 9, 20), daily_minutes=25)
    concepts = [Concept(id="pods", name="Pods"),
                Concept(id="services", name="Services", prerequisites=["pods"])]
    repo.save(goal, concepts)
    loaded_goal, loaded_concepts = repo.get("g1")
    assert loaded_goal == goal
    assert {c.id for c in loaded_concepts} == {"pods", "services"}
    assert next(c for c in loaded_concepts if c.id == "services").prerequisites == ["pods"]


def test_learner_model_upsert_is_idempotent(session_factory) -> None:
    repo = LearnerModelRepository(session_factory)
    model = LearnerModel(goal_id="g1", concepts={
        "pods": LearnerConceptState(concept_id="pods", mastery=0.5, confidence=0.5,
                                    state=ConceptState.DEVELOPING)})
    repo.save(model)
    repo.save(model)
    assert len(repo.get("g1").concepts) == 1
```

- [x] **Paso 2: ejecutar** → falla
- [x] **Paso 3: implementar** modelos SQLAlchemy 2 (`Mapped[...]`), migración SQL inicial,
      repositorios que traducen fila ⇄ modelo de `contracts` (nunca exponer entidades ORM
      fuera de `persistence/`), y un `conftest.py` que provee `session_factory` con rollback
      por test.
- [x] **Paso 4: ejecutar con `docker compose up -d db`** → 2 passed
- [x] **Paso 5: commit** → `git commit -m "feat(persistence): add Postgres repositories for goal and learner model"`

---

## ✅ Criterio de salida

- [x] `apply_assessment` y `derive_state` cubiertos al 100 % por tests
- [x] `ConceptGraph` rechaza ciclos y prerrequisitos inexistentes en construcción
- [x] Roundtrip de persistencia verde contra Postgres real
- [x] Ninguna función de esta fase llama a `datetime.now()`
- [x] `make check` en verde
