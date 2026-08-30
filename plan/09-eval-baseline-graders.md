# Fase 9 — Graders, baseline y runner

**Pista:** B · **Depende de:** F0, F8 · **Duración objetivo:** 3 h · **TDD estricto: SÍ** · **CP1**

**Entrega:** graders deterministas, baseline congelado, runner que produce `experiments/*.json`.

> **Estos graders se escriben ANTES que el `CurriculumPlanner`.** Es TDD a escala de proyecto:
> primero defines cómo se mide el éxito, luego construyes lo que debe superarlo. Si se escriben
> después, medirán lo que el sistema hace en vez de lo que debería hacer.

---

## Tarea 9.1 — Grader de NSDQ

**Ficheros:** Crear `eval/graders/nsdq.py`; Test `packages/core/tests/eval/test_nsdq_grader.py`

**Interfaces producidas:**
```python
class CheckResult(BaseModel):
    name: str
    passed: bool
    points: int
    max_points: int
    detail: str

class CaseScore(BaseModel):
    case_id: str
    checks: list[CheckResult]
    points: int
    max_points: int          # siempre 10

def grade_case(decision: NextSessionDecision, case: dict, key: dict) -> CaseScore
def grade_all(decisions: dict[str, NextSessionDecision], cases, keys) -> NsdqReport
```

Las 6 comprobaciones y su puntuación están en `docs/05_evaluacion.md` §1. **Impleméntalas
exactamente como están escritas ahí.**

- [ ] **Paso 1: escribir el test que falla** — el grader se prueba con decisiones escritas a
      mano, no con salidas del sistema. Esto permite terminar CP1 sin que exista el planner.

```python
# packages/core/tests/eval/test_nsdq_grader.py
from datetime import date
from learning_manager.contracts import BlockKind, DeadlineStatus, NextSessionDecision, SessionBlock
from eval.graders.nsdq import grade_case

CASE = _load("eval/cases/nsdq/k8s-services-gap.json")
KEY = _load("eval/keys/k8s-services-gap.json")


def _decision(*blocks: SessionBlock, status=DeadlineStatus.ON_TRACK) -> NextSessionDecision:
    return NextSessionDecision(session_date=date(2026, 9, 5), blocks=list(blocks),
                               total_minutes=sum(b.minutes for b in blocks),
                               rationale="r", deadline_status=status)


def _b(kind: BlockKind, cid: str, minutes: int) -> SessionBlock:
    return SessionBlock(kind=kind, concept_id=cid, minutes=minutes, objective="o",
                        content="c", source_ids=["s1"])


def test_perfect_decision_scores_ten() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 20),
                                 _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)
    assert score.points == 10
    assert all(c.passed for c in score.checks)


def test_missing_the_target_gap_loses_exactly_two_points() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "deployments", 20),
                                 _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)
    check = next(c for c in score.checks if c.name == "targets_correct_gap")
    assert check.passed is False and check.points == 0


def test_reteaching_mastered_concept_loses_two_points() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "pods", 20),
                                 _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)
    assert next(c for c in score.checks if c.name == "no_redundant_mastery").points == 0


def test_reviewing_a_mastered_concept_does_not_lose_points() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 15),
                                 _b(BlockKind.REVIEW, "pods", 5),
                                 _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)
    assert next(c for c in score.checks if c.name == "no_redundant_mastery").passed


def test_prerequisite_violation_loses_two_points() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "ingress", 20),
                                 _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)
    assert next(c for c in score.checks if c.name == "respects_prerequisites").points == 0


def test_missing_due_review_loses_two_points() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 25)), CASE, KEY)
    assert next(c for c in score.checks if c.name == "includes_due_reviews").points == 0


def test_time_budget_tolerance_is_ten_percent() -> None:
    ok = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 22),
                              _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)   # 27 ≤ 27.5
    bad = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 25),
                               _b(BlockKind.REVIEW, "volumes", 5)), CASE, KEY)  # 30 > 27.5
    assert next(c for c in ok.checks if c.name == "fits_time_budget").passed
    assert not next(c for c in bad.checks if c.name == "fits_time_budget").passed


def test_wrong_deadline_status_loses_one_point() -> None:
    score = grade_case(_decision(_b(BlockKind.CONCEPT, "services", 20),
                                 _b(BlockKind.REVIEW, "volumes", 5),
                                 status=DeadlineStatus.INFEASIBLE), CASE, KEY)
    assert next(c for c in score.checks if c.name == "deadline_status_correct").points == 0


def test_grader_never_calls_an_llm() -> None:
    # Aserción estructural: el módulo no importa nada de providers.
    import eval.graders.nsdq as m
    src = Path(m.__file__).read_text()
    assert "providers" not in src and "llm" not in src.lower()


def test_grading_is_idempotent() -> None:
    d = _decision(_b(BlockKind.CONCEPT, "services", 20), _b(BlockKind.REVIEW, "volumes", 5))
    assert grade_case(d, CASE, KEY) == grade_case(d, CASE, KEY)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo** → `ModuleNotFoundError: eval.graders.nsdq`
- [ ] **Paso 3: implementar las 6 comprobaciones** exactamente como en `docs/05_evaluacion.md` §1
- [ ] **Paso 4: ejecutar** → 10 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(eval): add deterministic NSDQ grader"`

---

## Tarea 9.2 — Grader de fuentes

**Ficheros:** Crear `eval/graders/sources.py`; Test `tests/eval/test_sources_grader.py`

**Interfaces producidas:**
`grade_sources(lesson_claims: list[ClaimVerdict], case: dict, corpus_ids: set[str]) -> SourceReport`
con `source_support_rate`, `outdated_claim_rate`, `traceability`.

- [ ] **Paso 1: test que falla**

```python
def test_all_current_claims_cited_gives_perfect_scores() -> None:
    r = grade_sources(all_current_verdicts(), CASE, CORPUS_IDS)
    assert r.source_support_rate == 1.0 and r.outdated_claim_rate == 0.0 and r.traceability == 1.0


def test_emitting_an_outdated_claim_raises_the_outdated_rate() -> None:
    r = grade_sources([verdict("Data fetching uses getServerSideProps")], CASE, CORPUS_IDS)
    assert r.outdated_claim_rate == 1.0


def test_citing_a_source_id_that_is_not_in_the_corpus_lowers_traceability() -> None:
    r = grade_sources([verdict("x", source_id="inventado")], CASE, CORPUS_IDS)
    assert r.traceability == 0.0


def test_empty_lesson_is_reported_not_scored_as_perfect() -> None:
    # Una lección vacía NO puede puntuar 100 % de soporte de fuentes.
    r = grade_sources([], CASE, CORPUS_IDS)
    assert r.source_support_rate == 0.0
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar**
- [ ] **Paso 4: ejecutar** → 4 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(eval): add deterministic source verification grader"`

---

## Tarea 9.3 — Baseline congelado

**Ficheros:** Crear `eval/baseline/single_prompt.py`, `eval/baseline/prompt.md`;
Test `tests/eval/test_baseline.py`

**Interfaces producidas:** `run_baseline(case: dict, llm: LLMProvider) -> NextSessionDecision`

> **Recibe exactamente la misma entrada que la solución** (bases §4.1): misma meta, mismo
> learner model, mismo grafo, mismo `today`, mismas fuentes, mismo modelo, misma temperatura,
> mismo esquema de salida. Lo que NO tiene: estado persistente, verificador, bucle de
> reparación, scheduler, replanificación.

- [ ] **Paso 1: test que falla**

```python
def test_baseline_receives_the_same_input_as_the_agent() -> None:
    llm = FakeLLM(responses=[VALID_SESSION_JSON])
    run_baseline(CASE, llm)
    p = llm.last_user_prompt
    for field in ["services", "0.30", "2026-09-05", "25", "2026-09-20"]:
        assert field in p, f"el baseline no recibió {field}"


def test_baseline_has_no_verifier_and_returns_invalid_output_as_is() -> None:
    # Es el punto: el baseline NO repara. Si el modelo se equivoca, se ve.
    llm = FakeLLM(responses=[SESSION_WITH_PREREQ_VIOLATION_JSON])
    decision = run_baseline(CASE, llm)
    assert any(b.concept_id == "ingress" for b in decision.blocks)
    assert llm.calls == 1        # una sola llamada, sin reintentos


def test_baseline_prompt_is_frozen() -> None:
    # Un hash del prompt: si alguien lo toca después de congelar, el test lo detecta.
    assert sha256(Path("eval/baseline/prompt.md").read_bytes()).hexdigest() == FROZEN_HASH
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El prompt es una instrucción razonable y competente, no un
      hombre de paja: describe la tarea con claridad y pide el mismo JSON. Un baseline
      deliberadamente malo invalidaría la comparación.
- [ ] **Paso 4: ejecutar, calcular el hash y fijarlo en el test**
- [ ] **Paso 5: commit y CONGELAR**

```bash
git add eval/baseline && git commit -m "feat(eval): freeze single-prompt baseline

FROZEN before any optimization (hackathon rules §11)."
```

---

## Tarea 9.4 — Runner de evaluación

**Ficheros:** Crear `eval/runner.py`; Test `tests/eval/test_runner.py`

**Interfaces producidas:**
`python -m eval.runner --name <nombre> [--system agent|baseline|both] [--check-determinism]`
→ escribe `experiments/<nombre>.json`

Contenido del fichero de experimento:

```json
{
  "name": "iteration-02",
  "timestamp": "2026-08-31T04:12:00Z",
  "git_sha": "abc1234",
  "llm_mode": "replay",
  "model": "gemini-2.5-flash",
  "nsdq": {
    "agent":    {"score": 0.87, "points": 96, "max_points": 110},
    "baseline": {"score": 0.51, "points": 56, "max_points": 110}
  },
  "checks": {
    "targets_correct_gap":     {"agent": 11, "baseline": 8,  "max": 11},
    "no_redundant_mastery":    {"agent": 10, "baseline": 4,  "max": 11},
    "respects_prerequisites":  {"agent": 11, "baseline": 5,  "max": 11},
    "includes_due_reviews":    {"agent": 11, "baseline": 2,  "max": 11},
    "fits_time_budget":        {"agent": 10, "baseline": 7,  "max": 11},
    "deadline_status_correct": {"agent": 9,  "baseline": 3,  "max": 11}
  },
  "per_case": [{"case_id": "...", "agent": 10, "baseline": 6, "checks": [...]}],
  "sources": {"agent": {"source_support_rate": 0.94, "outdated_claim_rate": 0.03,
                        "traceability": 1.0},
              "baseline": {"source_support_rate": 0.41, "outdated_claim_rate": 0.22,
                           "traceability": 0.68}},
  "cost": {"agent_usd": 0.041, "baseline_usd": 0.009},
  "latency": {"agent_p50_ms": 1820, "baseline_p50_ms": 900},
  "reliability": {"repair_rate": 0.27, "fallback_rate": 0.0}
}
```

- [ ] **Paso 1: test que falla**

```python
def test_runner_writes_an_experiment_file_with_all_required_fields(tmp_path) -> None:
    run(name="t", out_dir=tmp_path, system="both")
    data = json.loads((tmp_path / "t.json").read_text())
    for field in ["name", "timestamp", "git_sha", "llm_mode", "model", "nsdq",
                  "checks", "per_case", "cost", "latency", "reliability"]:
        assert field in data


def test_check_determinism_passes_in_replay_mode(tmp_path) -> None:
    assert run(name="d1", out_dir=tmp_path, check_determinism=True) == 0


def test_check_determinism_fails_when_results_differ(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("eval.runner._plan", _nondeterministic_planner)
    assert run(name="d2", out_dir=tmp_path, check_determinism=True) != 0


def test_runner_refuses_to_overwrite_a_frozen_experiment(tmp_path) -> None:
    run(name="baseline", out_dir=tmp_path)
    with pytest.raises(ExperimentExistsError):
        run(name="baseline", out_dir=tmp_path)      # la evidencia no se pisa en silencio
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** `--check-determinism` ejecuta dos veces y compara el JSON
      completo salvo `timestamp`. Sobrescribir exige `--force` explícito.
- [ ] **Paso 4: ejecutar** → 4 passed
- [ ] **Paso 5: activar el paso de CI** — quitar `continue-on-error` del workflow de la F0
- [ ] **Paso 6: commit** → `git commit -m "feat(eval): add evaluation runner with determinism gate"`

---

## ✅ Criterio de salida — CP1

- [ ] Los graders puntúan correctamente decisiones escritas a mano, **sin que exista el planner**
- [ ] Los graders no importan nada de `providers/`
- [ ] Baseline congelado, con hash verificado por un test
- [ ] `python -m eval.runner --name smoke --system baseline` produce un JSON completo
- [ ] `--check-determinism` en verde en CI
- [ ] `make check` en verde
