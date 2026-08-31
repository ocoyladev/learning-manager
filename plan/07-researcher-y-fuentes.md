# Fase 7 — Researcher y verificación de fuentes

**Pista:** B · **Depende de:** F0, F6 · **Duración objetivo:** 3 h · **TDD estricto: SÍ**

**Entrega:** búsqueda en vivo + juicio de autoridad/versión/fecha + contraste + `CorpusProvider`.

> Diferenciador 6 (§13). **El producto busca fuentes actuales en vivo para cualquier meta.**
> El corpus congelado es solo el fixture con el que se califica (`docs/05_evaluacion.md` §1).
> Ambos caminos implementan la MISMA interfaz `KnowledgeProvider`, así que el resto del sistema
> no distingue cuál está usando.

---

## Tarea 7.1 — Clasificación de autoridad y versión

**Ficheros:** Crear `providers/knowledge/authority.py`; Test `tests/providers/test_authority.py`

**Interfaces producidas:**
`classify_authority(url: str, title: str) -> AuthorityType`
`extract_version(text: str, title: str) -> str | None`
`extract_published_date(html: str) -> date | None`
`score_source(source: Source, today: date) -> float`

> Determinista y sin LLM: son reglas sobre dominio, ruta y patrones. Un LLM aquí sería más
> lento, más caro y no determinista para la misma decisión.

- [ ] **Paso 1: test que falla**

```python
@pytest.mark.parametrize(("url", "expected"), [
    ("https://kubernetes.io/docs/concepts/services-networking/service/", AuthorityType.OFFICIAL),
    ("https://docs.docker.com/engine/storage/volumes/",                  AuthorityType.OFFICIAL),
    ("https://nextjs.org/docs/app/building-your-application",            AuthorityType.OFFICIAL),
    ("https://stackoverflow.com/questions/12345",                        AuthorityType.FORUM),
    ("https://medium.com/@alguien/kubernetes-tutorial",                  AuthorityType.BLOG),
    ("https://dev.to/alguien/docker-101",                                AuthorityType.BLOG),
    ("https://random-tutorials.example.com/k8s",                         AuthorityType.UNKNOWN),
])
def test_authority_classification(url: str, expected: AuthorityType) -> None:
    assert classify_authority(url, "t") is expected


@pytest.mark.parametrize(("text", "expected"), [
    ("Next.js 15 introduces...", "15"),
    ("Kubernetes v1.31 documentation", "1.31"),
    ("Docker Compose V2", "2"),
    ("Sin versión aquí", None),
])
def test_version_extraction(text: str, expected: str | None) -> None:
    assert extract_version(text, "") == expected


def test_official_and_recent_scores_above_old_blog() -> None:
    official = Source(id="a", url="https://kubernetes.io/docs/x", title="t",
                      authority=AuthorityType.OFFICIAL, published_at=date(2026, 6, 1),
                      retrieved_at=date(2026, 8, 30))
    old_blog = Source(id="b", url="https://medium.com/x", title="t",
                      authority=AuthorityType.BLOG, published_at=date(2022, 1, 1),
                      retrieved_at=date(2026, 8, 30))
    assert score_source(official, date(2026, 8, 30)) > score_source(old_blog, date(2026, 8, 30))


def test_undated_source_is_penalised_not_discarded() -> None:
    undated = Source(id="c", url="https://kubernetes.io/docs/x", title="t",
                     authority=AuthorityType.OFFICIAL, retrieved_at=date(2026, 8, 30))
    dated = undated.model_copy(update={"id": "d", "published_at": date(2026, 6, 1)})
    s_undated = score_source(undated, date(2026, 8, 30))
    assert 0 < s_undated < score_source(dated, date(2026, 8, 30))
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** Lista de dominios oficiales explícita y comentada (no una
      heurística opaca). `score_source` = peso de autoridad × factor de frescura, con penalización
      por versión antigua respecto a la más nueva vista en el mismo tema.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(knowledge): add deterministic source authority scoring"`

---

## Tarea 7.2 — CorpusProvider

**Ficheros:** Crear `providers/knowledge/corpus.py`; Test `tests/providers/test_corpus.py`

**Interfaces producidas:** `CorpusProvider(corpus_path: Path)` — implementa `KnowledgeProvider`

Formato en disco (lo produce la F8):
```
corpus/<topic>/manifest.json      # list[Source] serializado
corpus/<topic>/<source_id>.md     # contenido en markdown
```

- [ ] **Paso 1: test que falla**

```python
def test_research_returns_sources_ranked_by_score(tmp_corpus) -> None:
    sources = CorpusProvider(tmp_corpus).research("kubernetes-services", k=3)
    assert len(sources) == 3
    assert sources[0].authority is AuthorityType.OFFICIAL


def test_research_is_deterministic(tmp_corpus) -> None:
    p = CorpusProvider(tmp_corpus)
    assert [s.id for s in p.research("kubernetes-services")] == \
           [s.id for s in p.research("kubernetes-services")]


def test_fetch_returns_the_markdown_content(tmp_corpus) -> None:
    assert "ClusterIP" in CorpusProvider(tmp_corpus).fetch("k8s_official_services")


def test_unknown_topic_raises_instead_of_returning_empty(tmp_corpus) -> None:
    with pytest.raises(TopicNotInCorpusError):
        CorpusProvider(tmp_corpus).research("tema-inexistente")
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar** — lectura de `manifest.json`, orden por `score_source` con
      desempate por `id` (para determinismo total).
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(knowledge): add frozen corpus provider"`

---

## Tarea 7.3 — LiveSearchProvider

**Ficheros:** Crear `providers/knowledge/live_search.py`, `providers/knowledge/notebooklm_stub.py`;
Test `tests/providers/test_live_search.py` (con `respx`)

**Interfaces producidas:** `LiveSearchProvider(...)` — implementa `KnowledgeProvider`

> Es el camino real del producto: cualquier meta, fuentes actuales. Se apoya en la búsqueda
> con grounding de Gemini para descubrir URLs, y luego **el juicio de autoridad/versión lo hace
> nuestro código** (Tarea 7.1), no el modelo — ese juicio es el diferenciador y no se delega.

- [ ] **Paso 1: test que falla**

```python
def test_discovered_urls_are_classified_by_our_own_rules(respx_mock) -> None:
    # El modelo devuelve URLs; la autoridad la decidimos nosotros.
    provider = LiveSearchProvider(llm=FakeLLM(responses=[json.dumps({
        "urls": ["https://kubernetes.io/docs/x", "https://medium.com/y"]})]))
    sources = provider.research("kubernetes services")
    by_url = {s.url: s for s in sources}
    assert by_url["https://kubernetes.io/docs/x"].authority is AuthorityType.OFFICIAL
    assert by_url["https://medium.com/y"].authority is AuthorityType.BLOG


def test_fetched_pages_are_converted_to_markdown_and_dated(respx_mock) -> None:
    respx_mock.get("https://kubernetes.io/docs/x").respond(
        html='<html><meta property="article:published_time" content="2026-06-01"><body><h1>T</h1><p>C</p></body></html>')
    s = LiveSearchProvider(...).research("kubernetes services")[0]
    assert s.published_at == date(2026, 6, 1)
    assert "# T" in LiveSearchProvider(...).fetch(s.id)


def test_notebooklm_stub_raises_not_implemented_with_the_reason() -> None:
    # spec §17: no se acopla a un MCP no oficial. La interfaz queda documentada.
    with pytest.raises(NotImplementedError, match="unofficial"):
        NotebookLMProvider().research("x")
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** Respetar `robots.txt`, `User-Agent` identificable, timeout 15 s,
      máximo 10 páginas por consulta. `notebooklm_stub.py` documenta la interfaz y **lanza**
      `NotImplementedError` explicando la decisión del §17 — no se implementa nada no oficial.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(knowledge): add live search provider and NotebookLM interface stub"`

---

## Tarea 7.4 — Verificación de afirmaciones

**Ficheros:** Crear `providers/knowledge/claim_check.py`;
Test `tests/providers/test_claim_check.py`

**Interfaces producidas:**
`check_claims(claims: list[str], sources: list[Source], provider, llm, today) -> list[ClaimVerdict]`
donde `ClaimVerdict(claim, verdict: Literal["supported","outdated","unsupported"], source_id, reason)`

> Es lo que la segunda métrica califica. El §29 de la especificación: preferir la fuente oficial
> más reciente y marcar como obsoleto lo que la contradiga.

- [ ] **Paso 1: test que falla**

```python
def test_claim_supported_by_current_official_source_is_supported() -> None:
    v = check_claims(["Route handlers live in app/api/*/route.ts"], SOURCES, provider,
                     FakeLLM(...), TODAY)[0]
    assert v.verdict == "supported" and v.source_id == "src_official_v15_route_handlers"


def test_claim_contradicted_by_a_newer_official_source_is_outdated() -> None:
    v = check_claims(["Data fetching uses getServerSideProps"], SOURCES, provider,
                     FakeLLM(...), TODAY)[0]
    assert v.verdict == "outdated"
    assert "App Router" in v.reason


def test_claim_with_no_supporting_source_is_unsupported() -> None:
    v = check_claims(["Next.js requires MongoDB"], SOURCES, provider, FakeLLM(...), TODAY)[0]
    assert v.verdict == "unsupported" and v.source_id is None


def test_official_source_wins_over_blog_on_conflict() -> None:
    # Blog de 2026 vs doc oficial de 2026 que lo contradice: gana la oficial.
    v = check_claims([CLAIM_IN_CONFLICT], [BLOG_2026, OFFICIAL_2026], provider,
                     FakeLLM(...), TODAY)[0]
    assert v.source_id == OFFICIAL_2026.id
```

- [ ] **Paso 2: ejecutar y confirmar el fallo**
- [ ] **Paso 3: implementar.** El LLM solo decide "¿esta fuente respalda o contradice esta
      afirmación?" por par (afirmación, fuente). **La resolución del conflicto es nuestra**:
      gana la de mayor `score_source`. Determinista dado el veredicto por par.
- [ ] **Paso 4: ejecutar** → verde
- [ ] **Paso 5: commit** → `git commit -m "feat(knowledge): add claim verification against ranked sources"`

---

## ✅ Criterio de salida

- [x] `CorpusProvider` y `LiveSearchProvider` implementan la misma interfaz y son intercambiables
- [x] La clasificación de autoridad es determinista y sin LLM
- [x] `NotebookLMProvider` documenta la interfaz y lanza `NotImplementedError` explicando §17
- [x] Ninguna llamada a red en la suite de tests
- [x] `make check` en verde
