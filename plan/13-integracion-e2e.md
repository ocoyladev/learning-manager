# Fase 13 — Integración end-to-end

**Pista:** ninguna (SECUENCIAL) · **Depende de:** todas · **Duración objetivo:** 4 h · **CP4**

**Entrega:** las tres pistas unidas, trayectoria real completa, cassettes grabados.

---

## Tarea 13.1 — Merge de las tres pistas

- [ ] `git checkout main`, luego merge de `track/a-core`, `track/b-eval`, `track/c-ui` en ese orden
- [ ] Resolver conflictos. **Si aparece un conflicto en `contracts.py` u `openapi.json`, algo se
      hizo mal: revísalo con el humano antes de resolverlo a mano.**
- [ ] `make check` en verde con las tres pistas juntas
- [ ] `docker compose up --build` levanta los 4 servicios sanos
- [ ] Commit → `chore: integrate core, evaluation and UI tracks`

---

## Tarea 13.2 — Trayectoria completa real

**Ficheros:** Test `tests/test_end_to_end.py`

Los 10 criterios del §48 de la especificación, en un solo test:

- [ ] **Paso 1: escribir el test que falla**

```python
def test_full_goal_to_mastery_trajectory(client, tmp_path) -> None:
    # 1. Goal intake
    gid = client.post("/goals", json={"title": "Kubernetes fundamentals",
                                      "purpose": "entrevista técnica",
                                      "deadline": "2026-09-26", "daily_minutes": 25,
                                      "preferred_formats": ["examples", "practice"]}
                      ).json()["goal"]["id"]

    # 2. Diagnostic
    items = client.post(f"/goals/{gid}/diagnostic").json()["items"]
    model = client.post(f"/goals/{gid}/diagnostic/answers",
                        json={"answers": _partially_correct(items)}).json()["learner_model"]
    assert any(s["state"] == "weak" for s in model["concepts"].values())

    # 3. Verified source acquisition
    sources = client.post(f"/goals/{gid}/research", json={"topic": "k8s-services-networking"}
                          ).json()["sources"]
    assert any(s["authority"] == "official" for s in sources)

    # 4-5. Initial curriculum + one lesson
    s1 = client.get(f"/goals/{gid}/next-session", params={"today": "2026-09-05"}).json()
    assert s1["blocks"] and s1["rationale"]
    weak_concept = _weakest(model)
    assert any(b["concept_id"] == weak_concept for b in s1["blocks"])

    # 6-7. Assessment + learner-state update
    after = client.post(f"/sessions/{s1['id']}/assess",
                        json={"answers": _all_correct(s1)}).json()["learner_model"]
    assert after["concepts"][weak_concept]["mastery"] > model["concepts"][weak_concept]["mastery"]

    # 8. Curriculum adaptation
    s2 = client.get(f"/goals/{gid}/next-session", params={"today": "2026-09-06"}).json()
    assert not any(b["concept_id"] == weak_concept and b["kind"] == "concept"
                   for b in s2["blocks"]), "reenseña un concepto ya superado"

    # 9. Scheduled / proactive review
    events = client.post(f"/goals/{gid}/simulate-day", json={"days": 4}).json()["events"]
    assert any(e["kind"] == "retrieval_question" for e in events)

    # 10. Reassessment
    assert any(e["kind"] == "reassessment" for e in events)


def test_every_agent_produced_a_trajectory(tmp_path) -> None:
    run_dir = _latest_run_dir()
    produced = {p.stem for p in run_dir.glob("*.jsonl")}
    assert produced >= {"GoalManager", "Diagnostician", "Researcher",
                        "CurriculumPlanner", "Assessor"}


def test_no_session_in_the_whole_trajectory_was_ever_invalid(tmp_path) -> None:
    # Aunque haya habido reparaciones, ninguna sesión ENTREGADA puede tener violaciones.
    for decision in _all_delivered_sessions(_latest_run_dir()):
        assert validate_session(decision, ...) == []
```

- [ ] **Paso 2: ejecutar y arreglar lo que salga.** Este test es el que revela los desajustes
      entre pistas. Es normal que falle varias veces.
- [ ] **Paso 3: verde con `LLM_MODE=fake`** primero, luego con `replay`
- [ ] **Paso 4: commit** → `test: add full goal-to-mastery end-to-end trajectory`

---

## Tarea 13.3 — Grabar los cassettes

**Requiere `GEMINI_API_KEY`. Es el momento de más gasto de API del proyecto: hazlo una vez y bien.**

- [ ] **Paso 1: verificar el ID de modelo vigente** y fijarlo en `.env` y `.env.example`
- [ ] **Paso 2: grabar el happy path**

```bash
LLM_MODE=live make record
```

- [ ] **Paso 3: grabar la evaluación completa** (agente + baseline sobre los 11 casos)

```bash
LLM_MODE=live python -m eval.runner --name live-recording --system both
```

- [ ] **Paso 4: verificar que replay reproduce lo mismo**

```bash
make eval-replay NAME=replay-check
python -m eval.compare experiments/live-recording.json experiments/replay-check.json
# debe reportar diferencia cero en nsdq y en checks
```

- [ ] **Paso 5: medir el tamaño** — `du -sh fixtures/cassettes/`. Si supera ~50 MB, recorta los
      campos de petición a un hash y guarda el prompt completo solo de una llamada por agente
      (suficiente para las trayectorias)
- [ ] **Paso 6: commit** → `data: record LLM cassettes for deterministic replay`

---

## Tarea 13.4 — Verificación desde entorno limpio

> Regla 10 de las bases. **Hazlo de verdad, no lo asumas.**

- [ ] **Paso 1:** clonar el repo en un directorio nuevo

```bash
git clone . /tmp/lm-clean && cd /tmp/lm-clean
cp .env.example .env          # SIN rellenar ninguna key
docker compose up -d --build
```

- [ ] **Paso 2:** verificar que todo funciona sin ninguna credencial
  - `http://localhost:3000` carga el onboarding
  - crear una meta funciona (modo replay)
  - `make eval-replay` produce los mismos números que en tu máquina
- [ ] **Paso 3:** cronometrar y anotar el tiempo total y el tamaño de descarga — van a
      `REPRODUCTION.md` como "runtime aproximado"
- [ ] **Paso 4:** si algo falla, arreglarlo **ahora**. Es exactamente lo que hará un juez
- [ ] **Paso 5: commit** → `fix: ensure clean-environment reproduction works without credentials`

---

## ✅ Criterio de salida — CP4

- [ ] Los 10 criterios del §48 pasan en un solo test
- [ ] Las 5 trayectorias se generan
- [ ] Ninguna sesión entregada fue inválida
- [ ] `replay` reproduce `live` con diferencia cero
- [ ] Un clon limpio sin keys funciona end-to-end
