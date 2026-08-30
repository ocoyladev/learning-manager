# Fase 2 — Scheduler determinista

**Pista:** A · **Depende de:** F0 · **Duración objetivo:** 1,5 h · **TDD estricto: SÍ**

**Entrega:** espaciado de repasos y viabilidad de deadline como **funciones puras sin LLM**.

> **Por qué esto NO es un agente.** Es aritmética de fechas sobre la heurística del §25. Un LLM
> aquí añadiría no determinismo y coste sin aportar juicio. Esta decisión es en sí misma una
> respuesta a la pregunta de control del §7.2 de la rúbrica ("¿qué decisiones de diseño
> ayudaron?") y hay que defenderla así en el vídeo: **LLM donde hay juicio, función pura donde
> no lo hay.**

---

## Tarea 2.1 — Espaciado de repasos

**Ficheros:**
- Crear: `packages/core/learning_manager/scheduler/spacing.py`
- Test: `packages/core/tests/scheduler/test_spacing.py`

**Interfaces producidas:**
`next_review_date(mastery: float, today: date, *, streak: int = 0) -> date`
`due_reviews(model: LearnerModel, today: date) -> list[str]`
`prioritize_reviews(model: LearnerModel, due: list[str], budget_minutes: int, graph: ConceptGraph) -> list[str]`

- [ ] **Paso 1: test que falla**

```python
# packages/core/tests/scheduler/test_spacing.py
from datetime import date
import pytest
from learning_manager.contracts import ConceptState, LearnerConceptState, LearnerModel
from learning_manager.scheduler.spacing import due_reviews, next_review_date, prioritize_reviews

TODAY = date(2026, 9, 5)


@pytest.mark.parametrize(
    ("mastery", "expected_days"),
    [(0.10, 1), (0.49, 1), (0.50, 2), (0.69, 2), (0.70, 4), (0.84, 4), (0.85, 7), (1.00, 7)],
)
def test_spacing_follows_the_frozen_heuristic(mastery: float, expected_days: int) -> None:
    # Tabla del §25 de la especificación. Congelada: cambiarla invalida el changelog.
    assert next_review_date(mastery, TODAY) == date(2026, 9, 5 + expected_days)


def test_streak_extends_the_interval() -> None:
    assert next_review_date(0.90, TODAY, streak=2) > next_review_date(0.90, TODAY, streak=0)


def test_streak_interval_is_capped() -> None:
    assert (next_review_date(1.0, TODAY, streak=99) - TODAY).days <= 30


def test_due_reviews_includes_today_and_past_only() -> None:
    model = LearnerModel(goal_id="g", concepts={
        "a": LearnerConceptState(concept_id="a", mastery=0.5, confidence=0.5,
                                 state=ConceptState.DEVELOPING, next_review=date(2026, 9, 4)),
        "b": LearnerConceptState(concept_id="b", mastery=0.5, confidence=0.5,
                                 state=ConceptState.DEVELOPING, next_review=date(2026, 9, 5)),
        "c": LearnerConceptState(concept_id="c", mastery=0.5, confidence=0.5,
                                 state=ConceptState.DEVELOPING, next_review=date(2026, 9, 6)),
        "d": LearnerConceptState(concept_id="d", mastery=0.5, confidence=0.5,
                                 state=ConceptState.DEVELOPING),
    })
    assert sorted(due_reviews(model, TODAY)) == ["a", "b"]


def test_review_storm_is_prioritized_by_weakness_within_budget() -> None:
    # Failure mode §47.10: cuatro repasos vencen con 25 min disponibles.
    model = LearnerModel(goal_id="g", concepts={
        cid: LearnerConceptState(concept_id=cid, mastery=m, confidence=0.6,
                                 state=ConceptState.REVIEW_DUE, next_review=TODAY)
        for cid, m in {"a": 0.20, "b": 0.80, "c": 0.45, "d": 0.60}.items()
    })
    ordered = prioritize_reviews(model, ["a", "b", "c", "d"], budget_minutes=10, graph=None)
    assert ordered[0] == "a"       # el más débil primero
    assert len(ordered) <= 2       # no desborda el presupuesto (5 min por repaso)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**

Run: `cd packages/core && pytest tests/scheduler -v` → `ModuleNotFoundError`

- [ ] **Paso 3: implementar**

```python
# packages/core/learning_manager/scheduler/spacing.py
"""Espaciado de repasos. Determinista, sin LLM, sin reloj del sistema.

Heurística del §25 de la especificación. Congelada: es la base del changelog.
No se afirma que sea un algoritmo pedagógico validado; es una heurística explícita
que puede evolucionar a FSRS/SM-2 fuera de la hackathon.
"""

from __future__ import annotations

from datetime import date, timedelta

from learning_manager.contracts import LearnerModel

REVIEW_MINUTES = 5
"""Presupuesto asumido por bloque de repaso."""

MAX_INTERVAL_DAYS = 30

_INTERVALS: tuple[tuple[float, int], ...] = (
    (0.50, 1),
    (0.70, 2),
    (0.85, 4),
    (1.01, 7),
)


def next_review_date(mastery: float, today: date, *, streak: int = 0) -> date:
    base = next(days for threshold, days in _INTERVALS if mastery < threshold)
    days = min(base * (2**streak), MAX_INTERVAL_DAYS)
    return today + timedelta(days=days)


def due_reviews(model: LearnerModel, today: date) -> list[str]:
    return [
        cid
        for cid, state in model.concepts.items()
        if state.next_review is not None and state.next_review <= today
    ]


def prioritize_reviews(
    model: LearnerModel, due: list[str], budget_minutes: int, graph: object | None = None
) -> list[str]:
    """Ordena por debilidad y recorta al presupuesto. Failure mode §47.10."""
    ordered = sorted(due, key=lambda cid: model.concepts[cid].mastery)
    capacity = max(0, budget_minutes // REVIEW_MINUTES)
    return ordered[:capacity]
```

- [ ] **Paso 4: ejecutar** → 12 passed (8 parametrizados + 4)
- [ ] **Paso 5: commit** → `git commit -m "feat(scheduler): add deterministic spaced review scheduling"`

---

## Tarea 2.2 — Viabilidad frente al deadline

**Ficheros:**
- Crear: `packages/core/learning_manager/scheduler/feasibility.py`
- Test: `packages/core/tests/scheduler/test_feasibility.py`

**Interfaces consumidas:** `ConceptGraph` (F1.2), `contracts.DeadlineStatus`.
**Interfaces producidas:**
`remaining_minutes(model, graph) -> int`
`available_minutes(goal, today) -> int`
`deadline_status(goal, model, graph, today) -> DeadlineStatus`

> Failure mode §47.2: deadline irreal. El sistema debe **decirlo**, no fingir que cabe.
> Es la comprobación 6 de NSDQ.

- [ ] **Paso 1: test que falla**

```python
# packages/core/tests/scheduler/test_feasibility.py
from datetime import date
from learning_manager.contracts import (
    Concept, ConceptState, DeadlineStatus, LearnerConceptState, LearnerModel, LearningGoal,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.scheduler.feasibility import (
    available_minutes, deadline_status, remaining_minutes,
)

TODAY = date(2026, 9, 5)
CONCEPTS = [
    Concept(id="pods", name="Pods", estimated_minutes=20),
    Concept(id="services", name="Services", prerequisites=["pods"], estimated_minutes=25),
    Concept(id="ingress", name="Ingress", prerequisites=["services"], estimated_minutes=25),
]
GRAPH = ConceptGraph(CONCEPTS)


def _goal(deadline: date, daily: int = 25) -> LearningGoal:
    return LearningGoal(id="g", title="t", purpose="p", deadline=deadline, daily_minutes=daily)


def _model(**mastery: float) -> LearnerModel:
    return LearnerModel(goal_id="g", concepts={
        cid: LearnerConceptState(concept_id=cid, mastery=m, confidence=0.8,
                                 state=ConceptState.DEVELOPING)
        for cid, m in mastery.items()})


def test_remaining_minutes_discounts_mastered_concepts() -> None:
    # pods dominado ⇒ solo quedan services (25) + ingress (25)
    assert remaining_minutes(_model(pods=0.95), GRAPH) == 50


def test_remaining_minutes_scales_partial_mastery() -> None:
    # pods 0.95 ≥ 0.85 ⇒ 0 · services 0.50 ⇒ ceil(25 * 0.5) = 13 · ingress 0.0 ⇒ 25
    assert remaining_minutes(_model(pods=0.95, services=0.50), GRAPH) == 38


def test_available_minutes_counts_days_until_deadline_inclusive() -> None:
    assert available_minutes(_goal(date(2026, 9, 8)), TODAY) == 4 * 25   # 5,6,7,8


def test_on_track_when_ample_time() -> None:
    assert deadline_status(_goal(date(2026, 10, 30)), _model(), GRAPH, TODAY) is DeadlineStatus.ON_TRACK


def test_at_risk_when_tight() -> None:
    # Necesita 70 min (20+25+25). Días 5,6,7 = 3 × 25 = 75 min disponibles.
    # Cabe, pero 75 < 70 × 1.20 = 84 ⇒ menos del 20 % de holgura.
    assert deadline_status(_goal(date(2026, 9, 7)), _model(), GRAPH, TODAY) is DeadlineStatus.AT_RISK


def test_infeasible_when_it_does_not_fit() -> None:
    # Failure mode §47.2: solo queda hoy (25 min) para 70 min de trabajo.
    assert deadline_status(_goal(date(2026, 9, 5)), _model(), GRAPH, TODAY) is DeadlineStatus.INFEASIBLE


def test_deadline_in_the_past_is_infeasible() -> None:
    assert deadline_status(_goal(date(2026, 9, 1)), _model(), GRAPH, TODAY) is DeadlineStatus.INFEASIBLE
```

> ⚠️ **Dos convenciones de las que dependen todos los números de arriba.** Impleméntalas así:
> 1. Un concepto con `mastery >= MASTERY_THRESHOLD` (0.85) aporta **0** minutos restantes,
>    no una fracción. Se considera terminado.
> 2. `available_minutes` cuenta los días **de forma inclusiva**: hoy y el día del deadline
>    ambos cuentan. Es decir `(deadline - today).days + 1`, con suelo en 0.

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar**

```python
# packages/core/learning_manager/scheduler/feasibility.py
"""Viabilidad del plan frente al deadline. Determinista."""

from __future__ import annotations

import math
from datetime import date

from learning_manager.contracts import MASTERY_THRESHOLD, DeadlineStatus, LearnerModel, LearningGoal
from learning_manager.domain.concept_graph import ConceptGraph

AT_RISK_SLACK = 0.20
"""Menos de este margen de holgura ⇒ at_risk en vez de on_track."""


def remaining_minutes(model: LearnerModel, graph: ConceptGraph) -> int:
    """Minutos de trabajo que quedan. Un concepto dominado aporta 0, no una fracción."""
    total = 0
    for concept in graph.concepts:
        state = model.concepts.get(concept.id)
        mastery = state.mastery if state else 0.0
        if mastery >= MASTERY_THRESHOLD:
            continue
        total += math.ceil(concept.estimated_minutes * (1.0 - mastery))
    return total


def available_minutes(goal: LearningGoal, today: date) -> int:
    """Días inclusivos: hoy cuenta y el día del deadline también."""
    days = (goal.deadline - today).days + 1
    return max(0, days) * goal.daily_minutes


def deadline_status(
    goal: LearningGoal, model: LearnerModel, graph: ConceptGraph, today: date
) -> DeadlineStatus:
    needed = remaining_minutes(model, graph)
    available = available_minutes(goal, today)
    if available < needed:
        return DeadlineStatus.INFEASIBLE
    if available < needed * (1 + AT_RISK_SLACK):
        return DeadlineStatus.AT_RISK
    return DeadlineStatus.ON_TRACK
```

- [ ] **Paso 4: ejecutar** → 7 passed. Los números de los tests están calculados con las dos
      convenciones de arriba; si alguno falla, el bug está en la implementación, no en el test.
      **No cambies un valor esperado para que pase**: verifica primero la aritmética a mano.
- [ ] **Paso 5: commit** → `git commit -m "feat(scheduler): add deadline feasibility assessment"`

---

## ✅ Criterio de salida

- [ ] Cobertura del 100 % en `scheduler/` (son funciones puras: no hay excusa)
- [ ] Ni un solo `datetime.now()` en el módulo — verificado con `grep -r "datetime.now" scheduler/`
- [ ] Ninguna importación de `providers/` ni de `agents/`
- [ ] `make check` en verde
