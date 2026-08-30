# Fase 4 — Los cinco agentes

**Pista:** A · **Depende de:** F1, F2, F3, F6 · **Duración objetivo:** 4 h · **TDD: sí, con `FakeLLM`**

**Entrega:** `GoalManager`, `Diagnostician`, `Researcher`, `CurriculumPlanner`, `Assessor`.

> Cinco agentes, ni uno más. El §7.2 de la rúbrica dice que la cantidad no puntúa y el §9.4
> **cobra una trayectoria por cada agente**. Cada uno existe porque hay juicio genuino que una
> función pura no puede tomar.
>
> **Todos los tests de esta fase usan `FakeLLM`**, que devuelve respuestas fijas. Se prueba la
> orquestación, la validación y la reparación — no la calidad del modelo. Esa se mide en la F14.

---

## Patrón común (léelo antes de cada tarea)

Cada agente es una clase con esta forma. No inventes otra:

```python
class SomeAgent:
    def __init__(self, llm: LLMProvider, trajectory: AgentTrajectory) -> None: ...
    def run(self, ...) -> SomeContractModel: ...
```

Reglas para los cinco:
1. El prompt de sistema vive en `agents/prompts/<agent>.md`, **no** embebido en el `.py`.
   Así se puede versionar en el changelog: "Iteración 3: reescrito el prompt del planner".
2. Toda llamada pasa por `self._llm.complete(...)` con `temperature=0` y `json_schema` del
   modelo de `contracts`.
3. Toda llamada y todo resultado se registran en `self._trajectory`.
4. Si el agente produce algo validable, **debe** pasar por `run_with_repair`.
5. Ninguna fecha desde `datetime.now()`: siempre `today: date` por parámetro.

---

## Tarea 4.1 — GoalManager

**Ficheros:** Crear `agents/goal_manager.py`, `agents/prompts/goal_manager.md`;
Test `tests/agents/test_goal_manager.py`

**Interfaces producidas:** `GoalManager.run(raw_goal: str, purpose: str, deadline: date, daily_minutes: int, preferred_formats: list[str]) -> tuple[LearningGoal, list[Concept]]`

- [ ] **Paso 1: test que falla** — con `FakeLLM` devolviendo un grafo fijo, verificar que:
  - el `LearningGoal` sale con los campos del usuario intactos (el agente **no** inventa deadline);
  - los `Concept` forman un grafo válido (se construye `ConceptGraph` sin excepción);
  - si el LLM devuelve un grafo con un ciclo, el agente reintenta y, si persiste, lanza
    `GoalPlanningError` con mensaje accionable.

```python
def test_user_fields_are_never_overwritten_by_the_model(fake_llm_with_cycle_free_graph) -> None:
    goal, concepts = GoalManager(fake_llm_with_cycle_free_graph, _rec()).run(
        raw_goal="aprender kubernetes", purpose="entrevista",
        deadline=date(2026, 9, 20), daily_minutes=25, preferred_formats=["practice"])
    assert goal.deadline == date(2026, 9, 20)      # el modelo NO decide el deadline
    assert goal.daily_minutes == 25
    assert ConceptGraph(concepts)                   # grafo válido


def test_cyclic_graph_from_model_is_repaired_then_raises(fake_llm_always_cyclic) -> None:
    with pytest.raises(GoalPlanningError, match="cycle"):
        GoalManager(fake_llm_always_cyclic, _rec()).run(...)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El prompt pide: descomponer la meta en 8–15 conceptos con
      prerrequisitos, `importance` y `estimated_minutes`; y derivar `success_criteria`
      observables desde `purpose`. Validación: grafo acíclico, prerrequisitos existentes,
      entre 5 y 25 conceptos. Reparación con `run_with_repair`.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(agents): add GoalManager"`

---

## Tarea 4.2 — Diagnostician

**Ficheros:** Crear `agents/diagnostician.py`, `agents/prompts/diagnostician.md`;
Test `tests/agents/test_diagnostician.py`

**Interfaces producidas:**
`Diagnostician.generate(goal, concepts, n_items=8) -> list[AssessmentItem]`
`Diagnostician.grade(items, answers, today) -> LearnerModel`

> §9 de la especificación: no empezar por el capítulo 1, comprobar primero qué sabe.
> Failure mode §47.1: el alumno ya domina casi todo — el diagnóstico debe detectarlo.

- [ ] **Paso 1: test que falla**

```python
def test_diagnostic_covers_every_concept_at_least_once() -> None:
    items = Diagnostician(fake_llm, _rec()).generate(GOAL, CONCEPTS, n_items=8)
    assert {i.concept_id for i in items} >= {c.id for c in CONCEPTS}


def test_grading_produces_a_state_for_every_concept_including_unanswered() -> None:
    model = Diagnostician(fake_llm, _rec()).grade(items, answers={}, today=TODAY)
    assert set(model.concepts) == {c.id for c in CONCEPTS}
    assert all(s.state is ConceptState.UNSEEN for s in model.concepts.values())


def test_all_correct_answers_yield_mastered_states() -> None:
    model = Diagnostician(fake_llm, _rec()).grade(items, all_correct(items), TODAY)
    assert all(s.mastery >= 0.85 for s in model.concepts.values())


def test_grading_is_deterministic_and_does_not_call_the_llm() -> None:
    # La calificación de opción múltiple es comparación de cadenas: no necesita modelo.
    counting_llm = CountingFakeLLM()
    Diagnostician(counting_llm, _rec()).grade(items, all_correct(items), TODAY)
    assert counting_llm.calls == 0
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** `generate` usa el LLM. **`grade` NO usa el LLM**: compara
      `answer` con `item.expected`, agrega por concepto y construye el `LearnerModel` con
      `derive_state`. Los conceptos sin ítem quedan `UNSEEN` con mastery 0.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(agents): add Diagnostician with deterministic grading"`

---

## Tarea 4.3 — CurriculumPlanner (el que mide NSDQ)

**Ficheros:** Crear `agents/curriculum_planner.py`, `agents/prompts/curriculum_planner.md`;
Test `tests/agents/test_curriculum_planner.py`

**Interfaces producidas:**
`CurriculumPlanner.next_session(goal, model, graph, sources, today) -> tuple[NextSessionDecision, RepairOutcome]`

> **Es el agente que la métrica primaria califica.** Todo lo demás existe para que este decida
> bien. Su prompt es el artefacto que más se itera en el changelog.

- [ ] **Paso 1: test que falla**

```python
def test_returns_the_llm_decision_when_it_validates(fake_llm_valid_session) -> None:
    decision, outcome = CurriculumPlanner(fake_llm_valid_session, _rec()).next_session(
        GOAL, MODEL, GRAPH, SOURCES, TODAY)
    assert outcome.attempts == 1 and outcome.used_fallback is False
    assert validate_session(decision, GOAL, MODEL, GRAPH, TODAY) == []


def test_repairs_a_prerequisite_violation(fake_llm_bad_then_good) -> None:
    decision, outcome = CurriculumPlanner(fake_llm_bad_then_good, _rec()).next_session(
        GOAL, MODEL, GRAPH, SOURCES, TODAY)
    assert outcome.attempts == 2
    assert ViolationCode.PREREQ_VIOLATION in {v.code for v in outcome.violations_per_attempt[0]}
    assert validate_session(decision, GOAL, MODEL, GRAPH, TODAY) == []


def test_falls_back_when_the_model_never_produces_a_valid_session(fake_llm_always_bad) -> None:
    decision, outcome = CurriculumPlanner(fake_llm_always_bad, _rec()).next_session(
        GOAL, MODEL, GRAPH, SOURCES, TODAY)
    assert outcome.used_fallback is True
    assert validate_session(decision, GOAL, MODEL, GRAPH, TODAY) == []   # nunca inválido


def test_output_never_uses_the_system_clock(fake_llm_valid_session) -> None:
    with freeze_time("2030-01-01"):
        decision, _ = CurriculumPlanner(fake_llm_valid_session, _rec()).next_session(
            GOAL, MODEL, GRAPH, SOURCES, date(2026, 9, 5))
    assert decision.session_date == date(2026, 9, 5)


def test_rationale_is_non_empty_and_mentions_a_concept(fake_llm_valid_session) -> None:
    # El "por qué esta sesión" es lo que hace percibir la adaptación (spec §41).
    decision, _ = CurriculumPlanner(fake_llm_valid_session, _rec()).next_session(
        GOAL, MODEL, GRAPH, SOURCES, TODAY)
    assert len(decision.rationale) > 20
    assert any(c.id in decision.rationale or c.name in decision.rationale for c in CONCEPTS)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El prompt recibe: meta, deadline, `today`, minutos diarios,
      learner model completo, conceptos desbloqueados, repasos vencidos, misconceptions y
      `source_ids` disponibles. Exige devolver `NextSessionDecision` en JSON. `deadline_status`
      lo calcula **el código** con `feasibility.deadline_status`, no el modelo — sobrescribir
      lo que diga el LLM. Envolver todo en `run_with_repair` con
      `fallback=lambda: deterministic_session(...)`.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(agents): add CurriculumPlanner with verification loop"`

---

## Tarea 4.4 — Assessor

**Ficheros:** Crear `agents/assessor.py`, `agents/prompts/assessor.md`;
Test `tests/agents/test_assessor.py`

**Interfaces producidas:**
`Assessor.generate(concept, model_state, n_items=4) -> list[AssessmentItem]`
`Assessor.grade(items, answers) -> list[AssessmentResult]`
`Assessor.retrieval_question(model, graph, today) -> AssessmentItem`

> `retrieval_question` es el Diferenciador 5 (§12): la notificación proactiva **no** es
> "recuerda estudiar", sino una pregunta derivada de la evidencia más débil.

- [ ] **Paso 1: test que falla**

```python
def test_retrieval_question_targets_the_weakest_evidence() -> None:
    model = _model(pods=0.95, services=0.30, volumes=0.60)
    item = Assessor(fake_llm, _rec()).retrieval_question(model, GRAPH, TODAY)
    assert item.concept_id == "services"


def test_retrieval_question_prefers_a_recorded_misconception() -> None:
    model = _model_with_misconception("services", "confunde ClusterIP con NodePort")
    item = Assessor(fake_llm, _rec()).retrieval_question(model, GRAPH, TODAY)
    prompt = fake_llm.last_user_prompt
    assert "ClusterIP" in prompt      # la misconception concreta entra en el prompt


def test_grading_extracts_misconceptions_only_for_wrong_answers() -> None:
    results = Assessor(fake_llm, _rec()).grade(items, mixed_answers)
    wrong = [r for r in results if r.score < 1.0]
    assert all(r.misconceptions for r in wrong)
    assert all(not r.misconceptions for r in results if r.score == 1.0)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** Selección del concepto objetivo: **determinista** (menor mastery
      entre los ya vistos, desempate por misconception presente y por `last_assessed` más
      antiguo). Solo la redacción de la pregunta usa el LLM.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(agents): add Assessor with evidence-driven retrieval"`

---

## Tarea 4.5 — Teaching (materialización de la lección)

**Ficheros:** Crear `agents/teaching.py`, `agents/prompts/teaching.md`;
Test `tests/agents/test_teaching.py`

**Interfaces producidas:** `Teacher.render(block: SessionBlock, sources: list[Source], model_state, preferred_formats) -> SessionBlock`

> Rellena `content` de cada bloque. **No es un sexto agente**: es una capacidad del
> `CurriculumPlanner` y comparte su trayectoria. Formatos del MVP: texto conciso, ejemplo
> trabajado, ejercicio, pregunta de recuperación. **Sin vídeo ni podcast** (§23).

- [ ] **Paso 1: test que falla** — cada bloque devuelto tiene `content` no vacío y
      `source_ids` ⊆ ids de las fuentes recibidas (no puede citar lo que no se le dio).

```python
def test_rendered_block_cannot_cite_a_source_it_was_not_given() -> None:
    out = Teacher(fake_llm, _rec()).render(block, sources=[SRC_A], model_state=st,
                                           preferred_formats=["examples"])
    assert set(out.source_ids) <= {SRC_A.id}
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar** con filtrado duro de `source_ids` tras la respuesta del modelo.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(agents): add teaching block renderer"`

---

## ✅ Criterio de salida

- [ ] Los 5 agentes existen, cada uno con su prompt en `agents/prompts/`
- [ ] Todos los tests usan `FakeLLM`: la suite corre sin red y sin keys
- [ ] `CurriculumPlanner` nunca devuelve una sesión inválida, ni con un LLM que siempre falla
- [ ] Cada agente escribe su trayectoria
- [ ] `make check` en verde
