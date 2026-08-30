# Fase 6 — LLMProvider, cassettes y medidor de coste

**Pista:** B · **Depende de:** F0 · **Duración objetivo:** 2 h · **TDD estricto: SÍ**

**Entrega:** `GeminiProvider`, `CachedLLMProvider`, `FakeLLM`, medidor de tokens/coste/latencia.

> Es la pieza que hace todo lo demás posible: sin ella no hay evaluación determinista, no hay
> reproducción por el juez sin key, y no hay columna "Cost per task" en el §6.3.
> **La Pista A la necesita para la F4: constrúyela primero.**

---

## Tarea 6.1 — FakeLLM y el medidor

**Ficheros:** Crear `providers/llm/fake.py`, `providers/llm/meter.py`;
Test `tests/providers/test_meter.py`

**Interfaces producidas:**
`FakeLLM(responses: list[str] | Callable[[str], str])` — implementa `LLMProvider`, cuenta llamadas,
expone `last_user_prompt`.
`CostMeter.record(response: LLMResponse)`, `.totals() -> CostSummary`

- [ ] **Paso 1: test que falla**

```python
# packages/core/tests/providers/test_meter.py
from learning_manager.contracts import LLMResponse
from learning_manager.providers.llm.meter import PRICING, CostMeter


def test_meter_accumulates_tokens_cost_and_latency() -> None:
    m = CostMeter()
    m.record(LLMResponse(text="a", model="gemini-2.5-flash", input_tokens=1000,
                         output_tokens=500, latency_ms=120))
    m.record(LLMResponse(text="b", model="gemini-2.5-flash", input_tokens=2000,
                         output_tokens=100, latency_ms=80))
    t = m.totals()
    assert t.calls == 2
    assert t.input_tokens == 3000 and t.output_tokens == 600
    assert t.cost_usd > 0
    assert t.latency_p50_ms == 100


def test_cache_hits_are_counted_but_cost_nothing() -> None:
    m = CostMeter()
    m.record(LLMResponse(text="a", model="gemini-2.5-flash", input_tokens=1000,
                         output_tokens=500, latency_ms=1, cache_hit=True))
    t = m.totals()
    assert t.cache_hits == 1 and t.cost_usd == 0.0


def test_unknown_model_does_not_crash_and_reports_zero_cost() -> None:
    m = CostMeter()
    m.record(LLMResponse(text="a", model="modelo-inventado", input_tokens=10, output_tokens=10))
    assert m.totals().cost_usd == 0.0
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** `PRICING: dict[str, tuple[float, float]]` con precio por millón
      de tokens de entrada y salida. **Verifica los precios vigentes de Gemini antes de
      rellenarlos** y anota la fecha de consulta en un comentario; si no se conocen, deja el
      modelo fuera de `PRICING` (coste 0) y documéntalo en el README en vez de inventar cifras.
- [ ] **Paso 4: ejecutar** → 3 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(providers): add fake LLM and cost meter"`

---

## Tarea 6.2 — CachedLLMProvider (cassettes)

**Ficheros:** Crear `providers/llm/cached.py`; Test `tests/providers/test_cached.py`

**Interfaces producidas:** `CachedLLMProvider(inner: LLMProvider | None, cassette_dir: Path, mode: Literal["replay","live"])`

**Clave del cassette:** `sha256(model + system + user + schema_name + str(temperature))`.
Fichero: `fixtures/cassettes/<primeros 16 del hash>.json`, con la petición completa dentro para
poder auditarlo.

- [ ] **Paso 1: test que falla**

```python
def test_live_mode_records_and_replay_mode_reads(tmp_path) -> None:
    inner = FakeLLM(responses=['{"ok": true}'])
    live = CachedLLMProvider(inner=inner, cassette_dir=tmp_path, mode="live")
    first = live.complete(system="s", user="u", schema_name="X")
    assert first.cache_hit is False and inner.calls == 1

    replay = CachedLLMProvider(inner=None, cassette_dir=tmp_path, mode="replay")
    second = replay.complete(system="s", user="u", schema_name="X")
    assert second.cache_hit is True
    assert second.text == first.text


def test_replay_mode_raises_a_helpful_error_on_a_miss(tmp_path) -> None:
    replay = CachedLLMProvider(inner=None, cassette_dir=tmp_path, mode="replay")
    with pytest.raises(CassetteMissError) as exc:
        replay.complete(system="s", user="desconocido", schema_name="X")
    assert "make record" in str(exc.value)      # dice al usuario CÓMO arreglarlo


def test_key_changes_when_any_input_changes(tmp_path) -> None:
    p = CachedLLMProvider(inner=FakeLLM(responses=["a", "b"]), cassette_dir=tmp_path, mode="live")
    p.complete(system="s", user="u1", schema_name="X")
    p.complete(system="s", user="u2", schema_name="X")
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_cassette_file_is_human_readable_and_contains_the_request(tmp_path) -> None:
    p = CachedLLMProvider(inner=FakeLLM(responses=['{"ok":1}']), cassette_dir=tmp_path, mode="live")
    p.complete(system="sys", user="usr", schema_name="X")
    data = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert data["request"]["system"] == "sys" and data["request"]["user"] == "usr"
    assert "response" in data and "recorded_at" in data
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El mensaje de `CassetteMissError` debe decir literalmente qué
      ejecutar: `"Cassette no encontrado para <clave>. Ejecuta 'make record' con GEMINI_API_KEY,
      o usa LLM_MODE=live."`
- [ ] **Paso 4: ejecutar** → 4 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(providers): add cassette record/replay LLM provider"`

---

## Tarea 6.3 — GeminiProvider

**Ficheros:** Crear `providers/llm/gemini.py`, `providers/llm/factory.py`;
Test `tests/providers/test_gemini.py` (con `respx`, sin red real)

**Interfaces producidas:**
`GeminiProvider(api_key, model, timeout=60)` — implementa `LLMProvider`
`build_llm(settings, meter, trajectory) -> LLMProvider` — decide según `LLM_MODE`

- [ ] **Paso 1: test que falla**

```python
def test_json_schema_is_sent_as_structured_output(respx_mock) -> None:
    route = respx_mock.post(url__regex=r".*generateContent.*").respond(json=_fake_gemini_ok())
    GeminiProvider(api_key="k", model="gemini-2.5-flash").complete(
        system="s", user="u", schema_name="NextSessionDecision",
        json_schema={"type": "object", "properties": {}})
    body = json.loads(route.calls[0].request.content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["temperature"] == 0


def test_response_is_parsed_and_metered(respx_mock) -> None:
    respx_mock.post(url__regex=r".*generateContent.*").respond(json=_fake_gemini_ok())
    r = GeminiProvider(api_key="k", model="gemini-2.5-flash").complete(system="s", user="u")
    assert r.parsed is not None
    assert r.input_tokens > 0 and r.latency_ms >= 0


def test_transient_error_is_retried_then_succeeds(respx_mock) -> None:
    respx_mock.post(url__regex=r".*generateContent.*").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=_fake_gemini_ok())])
    r = GeminiProvider(api_key="k", model="gemini-2.5-flash").complete(system="s", user="u")
    assert r.text


def test_build_llm_respects_LLM_MODE(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODE", "replay")
    assert isinstance(build_llm(...), CachedLLMProvider)
    monkeypatch.setenv("LLM_MODE", "fake")
    assert isinstance(build_llm(...), FakeLLM)


def test_live_mode_without_api_key_fails_with_a_clear_message(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="GEMINI_API_KEY"):
        build_llm(...)
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar** con `google-genai`, `temperature=0`, salida JSON estructurada,
      3 reintentos con backoff exponencial en 429/5xx, y timeout de 60 s.
      **Antes de usar `live`, verifica el ID de modelo vigente y anótalo en `.env.example`.**
- [ ] **Paso 4: ejecutar** → 5 passed
- [ ] **Paso 5: commit** → `git commit -m "feat(providers): add Gemini LLM provider with retries"`

---

## ✅ Criterio de salida

- [ ] La suite completa corre con `LLM_MODE=fake` sin red ni keys
- [ ] Un cassette grabado en `live` se reproduce byte a byte en `replay`
- [ ] `CassetteMissError` dice cómo arreglarlo
- [ ] El medidor reporta coste, tokens y latencia p50/p95
- [ ] **Avisa a la Pista A**: la F4 ya puede arrancar
