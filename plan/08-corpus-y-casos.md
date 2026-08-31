# Fase 8 — Corpus congelado, casos y claves de respuestas

**Pista:** B · **Depende de:** F0, F7 · **Duración objetivo:** 3 h · **CRÍTICA**

**Entrega:** `corpus/` con fuentes reales, 11 casos de evaluación, 11 claves de respuestas.

> ⛔ **Se congela al terminar.** Cambiar un caso o una clave después de ver resultados invalida
> la comparación (bases §6.1) y destruye la categoría de Measured Improvement.
> Léase `docs/05_evaluacion.md` entero antes de empezar.

---

## Tarea 8.1 — Construir el corpus

**Ficheros:** Crear `corpus/<topic>/manifest.json` + `corpus/<topic>/*.md` para 6 temas;
`learning_manager/cli.py::build_corpus`

**Temas** (decisión congelada: contenedores en profundidad + 1 caso React difícil):

| Tema | Fuentes objetivo | Trampa deliberada |
|---|---|---|
| `docker-fundamentals` | docs.docker.com | — |
| `docker-volumes-networking` | docs.docker.com | Un tutorial que usa `--link` (obsoleto) |
| `docker-compose` | docs.docker.com | Un post con sintaxis de Compose V1 (`version:`) |
| `k8s-workloads` | kubernetes.io | — |
| `k8s-services-networking` | kubernetes.io | Un post que confunde ClusterIP con NodePort |
| `nextjs-app-router` | nextjs.org | **Caso difícil:** `getServerSideProps` presentado como actual |

- [x] **Paso 1: implementar `build_corpus`** — recibe una lista de URLs por tema, descarga,
      convierte a markdown, extrae fecha y versión con las funciones de la F7.1, escribe
      `manifest.json` con `retrieved_at` y guarda el `.md`.
- [ ] **Paso 2: ejecutar sobre 5–8 URLs por tema** (≈ 40 documentos)

```bash
python -m learning_manager.cli build-corpus --topics-file eval/corpus_topics.yaml
```

- [ ] **Paso 3: verificar la calidad manualmente** — cada tema debe tener al menos:
      1 fuente oficial actual, 1 fuente oficial de versión anterior o guía de migración,
      1 fuente no oficial, y en los 3 temas trampa, la fuente obsoleta.
- [ ] **Paso 4: comprobar que se commitea**

```bash
du -sh corpus/                     # debe quedar por debajo de ~20 MB
git add corpus/ && git commit -m "data: freeze source corpus (40 docs, 6 topics)"
```

> Si el corpus supera los 20 MB, recorta el contenido de cada documento a las secciones
> relevantes. No uses Git LFS: complica la reproducción del juez.

- [ ] **Paso 5: registrar la fecha de captura** en `corpus/README.md` — es lo que hace
      auditable la afirmación "estas eran las fuentes actuales al momento de la captura".

---

## Tarea 8.2 — Los 11 casos de NSDQ

**Ficheros:** Crear `eval/cases/nsdq/*.json` (11 ficheros); Test `tests/eval/test_cases_valid.py`

La tabla de los 11 casos está en `docs/05_evaluacion.md` §5. El formato exacto de un caso está
en `docs/05_evaluacion.md` §1. **Cópialo literalmente, no lo reinventes.**

- [ ] **Paso 1: test que falla** — un test que valida los 11 casos estructuralmente:

```python
# packages/core/tests/eval/test_cases_valid.py
import json
from pathlib import Path
import pytest
from learning_manager.contracts import Concept, LearnerConceptState, LearningGoal
from learning_manager.domain.concept_graph import ConceptGraph

CASES = sorted(Path("eval/cases/nsdq").glob("*.json"))


def test_there_are_eleven_cases() -> None:
    assert len(CASES) == 11


def test_exactly_one_case_is_marked_hard() -> None:
    # Las bases §6.2 exigen al menos un caso desafiante.
    hard = [json.loads(p.read_text())["difficulty"] for p in CASES].count("hard")
    assert hard >= 1


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_case_is_structurally_valid(path: Path) -> None:
    case = json.loads(path.read_text())
    LearningGoal(**case["goal"])
    concepts = [Concept(**c) for c in case["concept_graph"]]
    graph = ConceptGraph(concepts)                       # rechaza ciclos y prereqs fantasma
    ids = {c.id for c in concepts}
    for cid, state in case["learner_model"].items():
        assert cid in ids, f"{cid} no existe en el grafo"
        LearnerConceptState(concept_id=cid, **state)


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_every_case_has_a_matching_key(path: Path) -> None:
    key = Path("eval/keys") / path.name
    assert key.exists(), f"falta la clave de respuestas para {path.stem}"
```

- [ ] **Paso 2: ejecutar y confirmar el fallo** (0 casos existen aún)
- [x] **Paso 3: escribir los 11 casos.** Cada uno debe aislar el comportamiento que dice su
      fila de la tabla. Ejemplos concretos de los dos más delicados:

`eval/cases/nsdq/k8s-review-storm.json` — 4 conceptos con `next_review` = `today` y solo
25 minutos. La clave exigirá que priorice los 2 más débiles y **difiera** los otros 2 en
`deferred_concepts`, no que los meta todos.

`eval/cases/nsdq/nextjs-version-drift.json` — `difficulty: "hard"`. Añade el campo
`corpus_topic: "nextjs-app-router"` para que el grader de fuentes lo use también.

- [ ] **Paso 4: ejecutar** → 25 passed (2 + 11 + 11 + 1)
- [ ] **Paso 5: commit** → `git commit -m "data: freeze 11 NSDQ evaluation cases"`

---

## Tarea 8.3 — Las 11 claves de respuestas

**Ficheros:** Crear `eval/keys/*.json`

El formato exacto está en `docs/05_evaluacion.md` §1. Campos obligatorios:
`case_id`, `must_target`, `must_not_teach_new`, `forbidden_before`, `must_include_review`,
`time_budget`, `time_tolerance`, `expected_deadline_status`, `notes`.

> **`notes` no es decorativo.** Explica por escrito por qué esa es la decisión correcta.
> Es lo que permite defender la clave ante un juez que pregunte si no la escribiste a
> conveniencia. Escríbela **antes** de ejecutar nada.

- [ ] **Paso 1: escribir las 11 claves razonando cada una a mano**, sin ejecutar el sistema
- [ ] **Paso 2: revisión cruzada** — pide a otro agente (o relee tú con distancia) que verifique
      cada clave contra su caso y señale ambigüedades. Una clave ambigua es un caso inútil.
- [ ] **Paso 3: verificar** que `test_every_case_has_a_matching_key` pasa
- [ ] **Paso 4: commit y CONGELAR**

```bash
git add eval/keys && git commit -m "data: freeze NSDQ answer keys

FROZEN. Modificar una clave tras ver resultados invalida la comparación (bases §6.1)."
```

---

## Tarea 8.4 — Casos de verificación de fuentes

**Ficheros:** Crear `eval/cases/sources/*.json` (uno por tema trampa: 3 ficheros)

Formato en `docs/05_evaluacion.md` §2. Cada afirmación lleva `verdict`
(`current` / `outdated` / `unsupported`), y si es `outdated`, el `superseded_by` y el texto
correcto.

- [ ] **Paso 1: escribir 8–12 afirmaciones por tema**, mezclando actuales, obsoletas y no
      respaldadas
- [ ] **Paso 2: verificar** que todo `superseded_by` y todo `supported_by` apunta a un
      `source_id` que existe realmente en `corpus/<topic>/manifest.json` — con un test:

```python
@pytest.mark.parametrize("path", sorted(Path("eval/cases/sources").glob("*.json")))
def test_every_referenced_source_exists_in_the_corpus(path: Path) -> None:
    case = json.loads(path.read_text())
    manifest = json.loads(Path(f"corpus/{case['topic']}/manifest.json").read_text())
    known = {s["id"] for s in manifest}
    for claim in case["claims"]:
        for field in ("supported_by", "superseded_by"):
            if claim.get(field):
                assert claim[field] in known, f"{claim['id']}.{field} → {claim[field]} no existe"
```

- [x] **Paso 3: commit** → `git commit -m "data: freeze source verification cases"`

---

## ✅ Criterio de salida — parte de CP1

- [ ] 6 temas en `corpus/`, ≈ 40 documentos, con las 3 trampas deliberadas
- [ ] 11 casos válidos estructuralmente, con al menos 1 marcado `hard`
- [ ] 11 claves de respuestas con `notes` razonadas
- [ ] 3 conjuntos de afirmaciones, todas referenciando fuentes que existen
- [ ] Todo commiteado y **declarado congelado en el mensaje de commit**
