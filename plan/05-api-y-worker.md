# Fase 5 — API, worker y simulación

**Pista:** A · **Depende de:** F1–F4 · **Duración objetivo:** 3 h · **TDD: tests de integración**

**Entrega:** FastAPI implementando `openapi.json`, worker de repasos, `simulate-day`.

---

## Tarea 5.1 — Routers FastAPI

**Ficheros:** Crear `api/app.py`, `api/routers/{goals,sessions,dashboard,simulation}.py`,
`api/deps.py`; Test `tests/api/test_endpoints.py`

**Interfaces consumidas:** los 5 agentes, los repositorios, el verificador.
**Restricción:** las rutas y los esquemas **deben coincidir exactamente** con el
`openapi.json` congelado en la F0. La Pista C ya construyó la UI contra él.

- [ ] **Paso 1: test que falla** — con `TestClient`, `LLM_MODE=fake` y Postgres de compose:

```python
def test_full_happy_path_through_the_api(client) -> None:
    r = client.post("/goals", json={"title": "Kubernetes", "purpose": "entrevista",
                                    "deadline": "2026-09-20", "daily_minutes": 25,
                                    "preferred_formats": ["practice"]})
    assert r.status_code == 201
    gid = r.json()["goal"]["id"]

    items = client.post(f"/goals/{gid}/diagnostic").json()["items"]
    assert len(items) >= 5

    answers = [{"item_id": i["id"], "answer": i["options"][0]} for i in items]
    model = client.post(f"/goals/{gid}/diagnostic/answers", json={"answers": answers}).json()
    assert model["learner_model"]["concepts"]

    session = client.get(f"/goals/{gid}/next-session", params={"today": "2026-09-05"}).json()
    assert session["blocks"] and session["total_minutes"] <= 28
    assert session["rationale"]

    dash = client.get(f"/goals/{gid}/dashboard").json()
    assert 0 <= dash["progress"] <= 1
    assert "why" in dash


def test_next_session_response_matches_the_frozen_openapi_schema(client) -> None:
    import json, jsonschema
    spec = json.load(open("openapi.json"))
    body = client.get("/goals/demo/next-session", params={"today": "2026-09-05"}).json()
    schema = spec["components"]["schemas"]["NextSessionDecision"]
    jsonschema.validate(body, {**schema, "components": spec["components"]})


def test_today_parameter_is_required_and_no_endpoint_uses_the_system_clock(client) -> None:
    with freeze_time("2030-01-01"):
        body = client.get("/goals/demo/next-session", params={"today": "2026-09-05"}).json()
    assert body["session_date"] == "2026-09-05"
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar** los 9 endpoints de la tabla de la F0 tarea 0.6. Inyección de
      dependencias en `api/deps.py` (provider de LLM según `LLM_MODE`, repositorios, logger de
      trayectoria por request con `run_id = uuid4()`).
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(api): implement frozen OpenAPI endpoints"`

---

## Tarea 5.2 — Worker y modo simulación

**Ficheros:** Crear `worker/tick.py`, `learning_manager/cli.py`;
Test `tests/worker/test_tick.py`

**Interfaces producidas:**
`tick(today: date, *, dry_run: bool) -> list[ScheduledEvent]`
CLI: `simulate-day --days N`, `record-cassettes`, `export-trajectories`, `build-corpus`

> **§45 de la especificación y regla R4 de las bases.** `SCHEDULER_MODE=simulation` por
> defecto: un juez reproduce `diagnóstico → lección → evaluación → adaptación → repaso vencido →
> pregunta proactiva` en minutos, sin esperar días y sin enviar nada a nadie.

- [ ] **Paso 1: test que falla**

```python
def test_tick_emits_a_retrieval_question_for_a_due_review() -> None:
    events = tick(today=date(2026, 9, 5), dry_run=True)
    assert any(e.kind == "retrieval_question" and e.concept_id == "volumes" for e in events)


def test_tick_never_sends_when_notify_live_is_false(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "false")
    sent = []
    events = tick(today=date(2026, 9, 5), dry_run=False, notifier=_Recording(sent))
    assert sent == []                      # regla R4: nada sale sin aprobación explícita
    assert events                          # pero el evento sí se registra


def test_simulate_day_advances_state_and_is_reproducible(tmp_path) -> None:
    a = simulate(days=5, seed=1)
    b = simulate(days=5, seed=1)
    assert a == b


def test_simulate_day_produces_the_full_demo_trajectory() -> None:
    events = simulate(days=5, seed=1)
    kinds = [e.kind for e in events]
    for expected in ["diagnostic", "lesson", "assessment", "adaptation",
                     "review_due", "retrieval_question", "reassessment"]:
        assert expected in kinds, f"falta {expected} en la trayectoria de demo"
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El worker hace polling sobre Postgres con
      `SELECT ... FOR UPDATE SKIP LOCKED`. En `simulation` avanza `today` en memoria. El envío
      real exige `NOTIFY_LIVE=true` **y** una confirmación interactiva.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(worker): add scheduler tick and simulation mode"`

---

## ✅ Criterio de salida

- [ ] Los 9 endpoints responden y validan contra `openapi.json` sin haberlo modificado
- [ ] `make simulate DAYS=5` produce los 7 tipos de evento de la trayectoria de demo
- [ ] Ninguna notificación sale con `NOTIFY_LIVE=false`
- [ ] `docker compose up` levanta todo y `/goals` responde
- [ ] `make check` en verde
