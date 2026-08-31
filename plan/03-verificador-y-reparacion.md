# Fase 3 — Verificador y bucle de reparación

**Pista:** A · **Depende de:** F0, F1, F2 · **Duración objetivo:** 2,5 h · **TDD estricto: SÍ**

**Entrega:** validación de restricciones + bucle de reparación con reintentos + fallback
determinista.

> **Esta es la fase que más puntos mueve.** Es el artefacto de ingeniería agentic central
> (categoría de 30 pts), genera trayectorias con reintentos visibles (§9.4), garantiza que el
> sistema nunca devuelve una sesión inválida (§7.3) y produce la cifra más contundente del
> changelog (§7.4).

---

## Tarea 3.1 — Validación de restricciones

**Ficheros:**
- Crear: `packages/core/learning_manager/verification/constraints.py`
- Test: `packages/core/tests/verification/test_constraints.py`

**Interfaces producidas:**
`validate_session(decision, goal, model, graph, today) -> list[ConstraintViolation]`

Los siete códigos están en `contracts.ViolationCode`. **Un test por código, ninguno se salta.**

- [ ] **Paso 1: test que falla**

```python
# packages/core/tests/verification/test_constraints.py
from datetime import date
from learning_manager.contracts import (
    BlockKind, Concept, ConceptState, DeadlineStatus, LearnerConceptState, LearnerModel,
    LearningGoal, NextSessionDecision, SessionBlock, ViolationCode,
)
from learning_manager.domain.concept_graph import ConceptGraph
from learning_manager.verification.constraints import validate_session

TODAY = date(2026, 9, 5)
GRAPH = ConceptGraph([
    Concept(id="pods", name="Pods", estimated_minutes=20),
    Concept(id="services", name="Services", prerequisites=["pods"], estimated_minutes=25),
    Concept(id="ingress", name="Ingress", prerequisites=["services"], estimated_minutes=25),
    Concept(id="volumes", name="Volumes", prerequisites=["pods"], estimated_minutes=20),
])
GOAL = LearningGoal(id="g", title="t", purpose="p", deadline=date(2026, 9, 20), daily_minutes=25)


def _model(next_review: dict[str, date] | None = None, **mastery: float) -> LearnerModel:
    nr = next_review or {}
    return LearnerModel(goal_id="g", concepts={
        cid: LearnerConceptState(concept_id=cid, mastery=m, confidence=0.8,
                                 state=ConceptState.DEVELOPING, next_review=nr.get(cid))
        for cid, m in mastery.items()})


def _decision(*blocks: SessionBlock) -> NextSessionDecision:
    return NextSessionDecision(
        session_date=TODAY, blocks=list(blocks), total_minutes=sum(b.minutes for b in blocks),
        rationale="r", deadline_status=DeadlineStatus.ON_TRACK)


def _block(kind: BlockKind, cid: str, minutes: int, sources: list[str] | None = None) -> SessionBlock:
    return SessionBlock(kind=kind, concept_id=cid, minutes=minutes, objective="o",
                        content="c", source_ids=sources or ["src1"])


def _codes(violations) -> set[ViolationCode]:
    return {v.code for v in violations}


def test_valid_session_produces_no_violations() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "services", 20),
                  _block(BlockKind.REVIEW, "volumes", 5))
    v = validate_session(d, GOAL, _model({"volumes": TODAY}, pods=0.9, services=0.3, volumes=0.55),
                         GRAPH, TODAY)
    assert v == []


def test_prereq_violation_when_prerequisite_is_weak() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "ingress", 25))
    v = validate_session(d, GOAL, _model(pods=0.9, services=0.3), GRAPH, TODAY)
    assert ViolationCode.PREREQ_VIOLATION in _codes(v)
    assert any(x.concept_id == "ingress" and "services" in x.message for x in v)


def test_redundant_mastered_when_teaching_something_already_known() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "pods", 20))
    v = validate_session(d, GOAL, _model(pods=0.95), GRAPH, TODAY)
    assert ViolationCode.REDUNDANT_MASTERED in _codes(v)


def test_review_block_on_mastered_concept_is_allowed() -> None:
    # Repasar lo dominado es correcto; RE-ENSEÑARLO no lo es.
    d = _decision(_block(BlockKind.REVIEW, "pods", 5))
    v = validate_session(d, GOAL, _model({"pods": TODAY}, pods=0.95), GRAPH, TODAY)
    assert ViolationCode.REDUNDANT_MASTERED not in _codes(v)


def test_time_budget_exceeded_beyond_tolerance() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "services", 40))
    v = validate_session(d, GOAL, _model(pods=0.9, services=0.3), GRAPH, TODAY)
    assert ViolationCode.TIME_BUDGET_EXCEEDED in _codes(v)


def test_time_budget_within_ten_percent_tolerance_is_ok() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "services", 27))   # 25 + 8 %
    v = validate_session(d, GOAL, _model(pods=0.9, services=0.3), GRAPH, TODAY)
    assert ViolationCode.TIME_BUDGET_EXCEEDED not in _codes(v)


def test_missing_due_review() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "services", 25))
    v = validate_session(d, GOAL, _model({"volumes": TODAY}, pods=0.9, services=0.3, volumes=0.55),
                         GRAPH, TODAY)
    assert ViolationCode.MISSING_DUE_REVIEW in _codes(v)


def test_unknown_concept() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "quantum", 25))
    v = validate_session(d, GOAL, _model(pods=0.9), GRAPH, TODAY)
    assert ViolationCode.UNKNOWN_CONCEPT in _codes(v)


def test_empty_session() -> None:
    d = NextSessionDecision(session_date=TODAY, blocks=[], total_minutes=0, rationale="r",
                            deadline_status=DeadlineStatus.ON_TRACK)
    assert ViolationCode.EMPTY_SESSION in _codes(validate_session(d, GOAL, _model(), GRAPH, TODAY))


def test_unsourced_claim_when_content_block_has_no_sources() -> None:
    d = _decision(_block(BlockKind.CONCEPT, "services", 25, sources=[]))
    v = validate_session(d, GOAL, _model(pods=0.9, services=0.3), GRAPH, TODAY)
    assert ViolationCode.UNSOURCED_CLAIM in _codes(v)


def test_retrieval_block_without_sources_is_allowed() -> None:
    # Una pregunta de recuperación no emite afirmaciones: no necesita fuente.
    d = _decision(_block(BlockKind.RETRIEVAL, "services", 25, sources=[]))
    v = validate_session(d, GOAL, _model(pods=0.9, services=0.3), GRAPH, TODAY)
    assert ViolationCode.UNSOURCED_CLAIM not in _codes(v)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo** → `pytest tests/verification -v`
- [ ] **Paso 3: implementar `validate_session`** — una función por código, agregadas en una
      lista. Usa `MASTERY_THRESHOLD` y `PREREQ_THRESHOLD` de `contracts`, `due_reviews` de
      `scheduler.spacing`. Los mensajes deben ser **accionables**, porque van literalmente al
      prompt de reparación: `"ingress requiere services, cuyo mastery es 0.30 (< 0.70)"`.
- [ ] **Paso 4: ejecutar** → 11 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(verification): add session constraint validation"`

---

## Tarea 3.2 — Bucle de reparación

**Ficheros:**
- Crear: `packages/core/learning_manager/verification/repair.py`
- Test: `packages/core/tests/verification/test_repair.py`

**Interfaces producidas:**
```python
class RepairOutcome(BaseModel):
    value: object
    attempts: int
    violations_per_attempt: list[list[ConstraintViolation]]
    used_fallback: bool

def run_with_repair(*, produce, validate, repair_prompt, fallback, trajectory, max_retries=2) -> RepairOutcome
```

- [ ] **Paso 1: test que falla**

```python
# packages/core/tests/verification/test_repair.py
from learning_manager.contracts import ConstraintViolation, ViolationCode
from learning_manager.verification.repair import run_with_repair


class _Recorder:
    def __init__(self) -> None:
        self.steps: list[tuple[str, dict]] = []

    def step(self, step: str, **fields: object) -> None:
        self.steps.append((step, dict(fields)))


def test_returns_immediately_when_first_attempt_is_valid() -> None:
    out = run_with_repair(produce=lambda hint: "ok", validate=lambda v: [],
                          repair_prompt=lambda vs: "fix", fallback=lambda: "fb",
                          trajectory=_Recorder())
    assert out.value == "ok" and out.attempts == 1 and out.used_fallback is False


def test_repairs_once_then_succeeds() -> None:
    calls: list[str | None] = []
    bad = [ConstraintViolation(code=ViolationCode.PREREQ_VIOLATION, message="m")]

    def produce(hint: str | None) -> str:
        calls.append(hint)
        return "bad" if hint is None else "good"

    out = run_with_repair(produce=produce, validate=lambda v: bad if v == "bad" else [],
                          repair_prompt=lambda vs: "PREREQ_VIOLATION: m",
                          fallback=lambda: "fb", trajectory=_Recorder())
    assert out.value == "good" and out.attempts == 2
    assert calls[1] is not None and "PREREQ_VIOLATION" in calls[1]


def test_falls_back_after_max_retries() -> None:
    bad = [ConstraintViolation(code=ViolationCode.EMPTY_SESSION, message="m")]
    out = run_with_repair(produce=lambda hint: "bad", validate=lambda v: bad,
                          repair_prompt=lambda vs: "fix", fallback=lambda: "deterministic",
                          trajectory=_Recorder(), max_retries=2)
    assert out.value == "deterministic" and out.used_fallback is True
    assert out.attempts == 3            # 1 inicial + 2 reintentos
    assert len(out.violations_per_attempt) == 3


def test_every_attempt_is_logged_to_the_trajectory() -> None:
    rec = _Recorder()
    bad = [ConstraintViolation(code=ViolationCode.EMPTY_SESSION, message="m")]
    run_with_repair(produce=lambda hint: "bad", validate=lambda v: bad,
                    repair_prompt=lambda vs: "fix", fallback=lambda: "fb",
                    trajectory=rec, max_retries=1)
    names = [s for s, _ in rec.steps]
    assert names.count("validation") == 2
    assert "repair_prompt" in names
    assert "fallback" in names
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar `run_with_repair`** — genérico sobre el tipo producido, registra
      `attempt`, `validation`, `repair_prompt`, `fallback` y `result` en la trayectoria.
- [ ] **Paso 4: ejecutar** → 4 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(verification): add repair loop with deterministic fallback"`

---

## Tarea 3.3 — Fallback determinista de sesión

**Ficheros:**
- Crear: `packages/core/learning_manager/verification/fallback.py`
- Test: `packages/core/tests/verification/test_fallback.py`

**Interfaces producidas:**
`deterministic_session(goal, model, graph, today) -> NextSessionDecision`

> Cuando el LLM agota los reintentos, el scheduler puro construye la sesión: repasos vencidos
> priorizados + el concepto desbloqueado con menor mastery, dentro del presupuesto.
> **Garantiza que el sistema nunca devuelve nada inválido.** Es la respuesta a §47.9
> (fallo del provider) y sostiene la puntuación de End-to-End Quality.

- [ ] **Paso 1: test que falla** — la aserción clave: la salida de `deterministic_session`
      **siempre** pasa `validate_session` sin violaciones, para 20 modelos generados
      aleatoriamente con semilla fija.

```python
# packages/core/tests/verification/test_fallback.py
import random
from datetime import date, timedelta
from learning_manager.verification.constraints import validate_session
from learning_manager.verification.fallback import deterministic_session
# ... GRAPH, GOAL como en test_constraints.py ...


def test_fallback_output_always_validates() -> None:
    rng = random.Random(1234)
    today = date(2026, 9, 5)
    for _ in range(20):
        model = _random_model(rng, today)
        decision = deterministic_session(GOAL, model, GRAPH, today)
        assert validate_session(decision, GOAL, model, GRAPH, today) == []


def test_fallback_is_reproducible() -> None:
    model = _random_model(random.Random(7), date(2026, 9, 5))
    a = deterministic_session(GOAL, model, GRAPH, date(2026, 9, 5))
    b = deterministic_session(GOAL, model, GRAPH, date(2026, 9, 5))
    assert a == b
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar** — repasos vencidos priorizados por `prioritize_reviews`, luego
      el concepto desbloqueado con menor mastery, recortando `minutes` para encajar en
      `daily_minutes`. `rationale` explica la elección en texto.
- [ ] **Paso 4: ejecutar** → 2 passed. **Si el test de propiedad falla, el bug está en el
      fallback o en el validador; no relajes el test.**
- [ ] **Paso 5: commit** → `git commit -m "feat(verification): add deterministic session fallback"`

---

## ✅ Criterio de salida

- [x] Los 7 códigos de `ViolationCode` tienen al menos un test que los dispara
- [x] `test_fallback_output_always_validates` verde con 20 modelos aleatorios
- [x] `run_with_repair` registra todos los intentos en la trayectoria
- [x] `make check` en verde
- [ ] **Anota la cifra de partida para el changelog:** cuántos de los 11 casos de NSDQ pasa el
      planner *sin* verificador (se mide en la F14; aquí solo se deja el gancho)
