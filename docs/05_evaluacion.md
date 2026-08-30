# Diseño de evaluación — Learning Manager

> **CONGELADO.** Los casos, las claves de respuestas y el baseline no se tocan una vez escritos.
> Cambiarlos después de ver resultados invalida la comparación (§6.1 de las bases).
> Aquí se juegan **45 de los 100 puntos**: Measured Improvement (15), Reproducibility (15)
> y buena parte de Agent Solution & Engineering (30), porque cada decisión de diseño se
> justifica con una cifra salida de aquí.

---

## 1. Métrica primaria — NSDQ (Next-Session Decision Quality)

Mide **si el manager decide bien**, que es el diferenciador del producto.
No mide si la persona aprendió: eso no es demostrable en una hackathon (§31 lo admite).

### Entrada de un caso (`eval/cases/nsdq/k8s-services-gap.json`)

```json
{
  "case_id": "k8s-services-gap",
  "difficulty": "normal",
  "goal": {
    "id": "k8s-interview",
    "title": "Deploy an app on Kubernetes and answer fundamental interview questions",
    "purpose": "technical interview in 3 weeks",
    "deadline": "2026-09-20",
    "daily_minutes": 25,
    "preferred_formats": ["examples", "practice"]
  },
  "today": "2026-09-05",
  "concept_graph": [
    {"id": "pods",        "name": "Pods",        "prerequisites": [],            "estimated_minutes": 20},
    {"id": "deployments", "name": "Deployments", "prerequisites": ["pods"],      "estimated_minutes": 20},
    {"id": "services",    "name": "Services",    "prerequisites": ["pods"],      "estimated_minutes": 25},
    {"id": "ingress",     "name": "Ingress",     "prerequisites": ["services"],  "estimated_minutes": 25},
    {"id": "volumes",     "name": "Volumes",     "prerequisites": ["pods"],      "estimated_minutes": 20}
  ],
  "learner_model": {
    "pods":        {"mastery": 0.91, "confidence": 0.88, "state": "mastered",   "next_review": "2026-09-08"},
    "deployments": {"mastery": 0.84, "confidence": 0.80, "state": "developing", "next_review": "2026-09-09"},
    "services":    {"mastery": 0.30, "confidence": 0.70, "state": "weak",
                    "misconceptions": ["confunde ClusterIP con NodePort"]},
    "ingress":     {"mastery": 0.00, "confidence": 0.00, "state": "unseen"},
    "volumes":     {"mastery": 0.55, "confidence": 0.65, "state": "developing", "next_review": "2026-09-05"}
  }
}
```

### Clave de respuestas (`eval/keys/k8s-services-gap.json`)

```json
{
  "case_id": "k8s-services-gap",
  "must_target": ["services"],
  "must_not_teach_new": ["pods", "deployments"],
  "forbidden_before": {"ingress": ["services"]},
  "must_include_review": ["volumes"],
  "time_budget": 25,
  "time_tolerance": 0.10,
  "expected_deadline_status": "on_track",
  "notes": "services es el mastery más bajo con prerrequisito cubierto. volumes vence hoy. ingress está bloqueado."
}
```

### Las 6 comprobaciones (`eval/graders/nsdq.py`, **calificadas por código**)

| # | Comprobación | Regla exacta | Pts |
|---|---|---|---:|
| 1 | `targets_correct_gap` | Al menos un bloque `concept`/`practice` sobre cada id de `must_target` | 2 |
| 2 | `no_redundant_mastery` | Ningún bloque `concept`/`worked_example` sobre ids de `must_not_teach_new` (los bloques `review` sí se permiten) | 2 |
| 3 | `respects_prerequisites` | Para cada `k: [prereqs]` de `forbidden_before`, si aparece `k` entonces todos sus prereqs tienen `mastery >= 0.70` | 2 |
| 4 | `includes_due_reviews` | Todo id de `must_include_review` aparece en algún bloque | 2 |
| 5 | `fits_time_budget` | `sum(block.minutes)` dentro de `time_budget * (1 ± time_tolerance)` | 1 |
| 6 | `deadline_status_correct` | `decision.deadline_status == expected_deadline_status` | 1 |

**10 puntos por caso. 11 casos = 110 posibles. NSDQ = obtenidos / 110.**

Además se reporta el **desglose por comprobación**, porque es lo que convierte el changelog en
evidencia: "la Iteración 2 subió `respects_prerequisites` de 4/11 a 11/11".

### Regla anti-trampa

El grader es puro: recibe el JSON de salida y la clave, no llama a ningún LLM y no conoce
qué sistema la produjo. El **mismo** grader califica baseline y solución final.

---

## 2. Métrica secundaria — Verificación de fuentes

Mide el Diferenciador 6 (§13): ¿el sistema evita enseñar comportamiento obsoleto como actual?

`eval/cases/sources/*.json` marca afirmaciones sobre el corpus congelado:

```json
{
  "topic": "nextjs-app-router",
  "claims": [
    {"id": "c1", "text": "Data fetching uses getServerSideProps",
     "verdict": "outdated", "superseded_by": "src_official_v15_app_router",
     "correct": "Server Components fetch directly; getServerSideProps is Pages Router only"},
    {"id": "c2", "text": "Route handlers live in app/api/*/route.ts",
     "verdict": "current", "supported_by": "src_official_v15_route_handlers"}
  ]
}
```

| Métrica | Definición |
|---|---|
| `source_support_rate` | % de afirmaciones de la lección con `source_ids` no vacío que resuelve a un documento real del corpus |
| `outdated_claim_rate` | % de afirmaciones emitidas que la clave marca como `outdated`. **Menor es mejor** |
| `traceability` | % de `source_ids` citados que existen en `corpus/` |

También calificadas por código, contra la clave.

---

## 3. Métricas de apoyo (formato del §6.3)

| Métrica | Cómo se obtiene |
|---|---|
| Human time per task | Protocolo cronometrado: un humano prepara manualmente un plan de estudio para 3 de los casos. Se registra el tiempo y se documenta el procedimiento en `experiments/human_baseline.json` |
| Cost per task | `providers/llm/meter.py` agrega tokens × precio del modelo por ejecución |
| Latency | Medida por `eval/runner.py`, p50 y p95 |
| Retry rate | Cuántas decisiones necesitaron reparación — sale de las trayectorias |
| Fallback rate | Cuántas agotaron los reintentos y cayeron al scheduler puro |

---

## 4. Baseline congelado

`eval/baseline/single_prompt.py`. Recibe **exactamente** la misma entrada que la solución:
misma meta, mismo learner model, mismo grafo, mismo `today`, mismas fuentes del corpus, mismo
modelo Gemini, misma temperatura, mismo esquema JSON de salida.

Lo que **no** tiene: learner model persistente entre sesiones, verificador, bucle de reparación,
scheduler, replanificación.

Se congela y se commitea **antes** de optimizar nada (§11 de las bases). Cualquier diferencia de
recursos entre baseline y solución se documenta explícitamente en el README (§4.1).

---

## 5. Los 11 casos

| # | case_id | Qué prueba |
|---|---|---|
| 1 | `docker-cold-start` | Alumno sin conocimiento previo. ¿Empieza por la raíz del grafo? |
| 2 | `docker-mostly-known` | Alumno que ya domina casi todo. **¿Evita re-enseñar?** (failure mode §47.1) |
| 3 | `docker-volumes-weak` | Un gap claro entre conceptos dominados |
| 4 | `k8s-services-gap` | Gap + repaso vencido simultáneos |
| 5 | `k8s-prereq-trap` | El gap más grande está bloqueado por un prerrequisito. **¿Respeta el orden?** |
| 6 | `k8s-review-storm` | Cuatro repasos vencen el mismo día con 25 min. **¿Prioriza o desborda?** (§47.10) |
| 7 | `compose-tight-deadline` | Deadline irreal. ¿Marca `at_risk`/`infeasible` en vez de fingir? (§47.2) |
| 8 | `docker-repeated-failure` | Mismo concepto fallado dos veces. ¿Cambia de enfoque o repite? (§47.5) |
| 9 | `k8s-fast-learner` | Supera conceptos antes de lo previsto. ¿Comprime el plan? (§47.6) |
| 10 | `docker-availability-drop` | Los minutos diarios bajan de 40 a 10. ¿Replanifica? (§47.7) |
| 11 | `nextjs-version-drift` | **CASO DIFÍCIL (§6.2).** Corpus con fuentes contradictorias entre versiones. Prueba NSDQ *y* verificación de fuentes a la vez |

El caso 11 es el "caso desafiante" que exigen las bases y del que hay que explicar qué reveló.

---

## 6. Determinismo y reproducción

```bash
make eval-replay   # sin keys, sin red, sin coste → números idénticos siempre
make eval-live     # con GEMINI_API_KEY → regraba cassettes
```

Temperatura 0 en todas las llamadas. Todas las fechas provienen del campo `today` del caso,
nunca de `datetime.now()` — un test lo verifica congelando el reloj.

Cada ejecución escribe `experiments/<nombre>.json` con: NSDQ global, desglose por comprobación,
desglose por caso, métricas de fuentes, coste, latencia, tasa de reintentos, hash de git,
versión del modelo y timestamp. **Ninguna cifra del README puede afirmarse sin un fichero aquí.**
