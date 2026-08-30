# Arquitectura — Learning Manager

> Deriva de `02_learning_manager_especificacion.md` §36 y de `03_decisiones_congeladas.md`.
> **Los agentes ejecutores no pueden cambiar límites de módulo ni firmas sin aprobación humana.**

---

## 1. Vista de servicios (`docker compose up`)

```
┌──────────────────────────────────────────────────────────────┐
│ web        Next.js 15 · :3000   dashboard, onboarding, sesión │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP (OpenAPI congelado en Fase 0)
┌───────────────────────────▼──────────────────────────────────┐
│ api        FastAPI · :8000                                   │
│            orquesta las 5 capacidades + verificador          │
└───────┬───────────────────────────────────┬──────────────────┘
        │                                   │
┌───────▼─────────┐               ┌─────────▼──────────────────┐
│ db  Postgres 16 │               │ worker                     │
│     :5432       │◄──────────────┤ tick del scheduler,        │
│     learner     │               │ repasos vencidos,          │
│     state       │               │ notificaciones proactivas  │
└─────────────────┘               └─────────┬──────────────────┘
                                            │
                        ┌───────────────────┴───────────────┐
                        ▼                                   ▼
                 Console / Telegram                   WhatsApp Cloud
                 (reproducible)                       (opcional, env-gated)
```

Cuatro servicios. Sin Redis: el `worker` hace polling sobre Postgres con `SELECT ... FOR UPDATE
SKIP LOCKED`, suficiente a esta escala y una pieza móvil menos que puede fallar en la demo.

---

## 2. Estructura del repositorio

```
learning-manager/
├── AGENTS.md                      # instrucciones para CUALQUIER agente ejecutor
├── CLAUDE.md                      # → AGENTS.md
├── PLAN.md                        # índice maestro, cronograma, checkpoints, línea de corte
├── plan/                          # 00..15, una fase por fichero, ejecutables por separado
├── docs/                          # 01..05 documentos congelados
├── .claude/{agents,skills}/       # adaptadores Claude Code
├── .cursor/rules/                 # adaptadores Cursor
│
├── packages/core/                 # ── TODO lo que la rúbrica califica ──
│   ├── pyproject.toml
│   ├── learning_manager/
│   │   ├── contracts.py           # ⛔ CONGELADO EN FASE 0 — fuente única de verdad
│   │   ├── config.py              # settings por entorno
│   │   ├── domain/                # concept_graph.py, learner_model.py  (puro, sin IO)
│   │   ├── scheduler/             # spacing.py, feasibility.py          (puro, sin LLM)
│   │   ├── verification/          # constraints.py, repair.py           (puro + bucle)
│   │   ├── trajectory/            # logger.py                           (JSONL)
│   │   ├── providers/
│   │   │   ├── llm/               # gemini.py, cached.py, fake.py, meter.py
│   │   │   ├── knowledge/         # live_search.py, corpus.py, notebooklm_stub.py
│   │   │   └── notify/            # console.py, telegram.py, whatsapp.py
│   │   ├── agents/                # goal_manager.py, diagnostician.py, researcher.py,
│   │   │                          # curriculum_planner.py, assessor.py   (+ prompts/)
│   │   ├── persistence/           # models.py, repositories.py, migrations/
│   │   ├── api/                   # app.py, routers/, schemas.py
│   │   ├── worker/                # tick.py
│   │   └── cli.py                 # simulate-day, record-cassettes, build-corpus
│   └── tests/                     # espeja learning_manager/ 1:1
│
├── apps/web/                      # Next.js — solo presentación, cero lógica de negocio
│
├── eval/                          # ── la evidencia ──
│   ├── cases/nsdq/*.json          # 11 entradas congeladas
│   ├── cases/sources/*.json       # afirmaciones marcadas del corpus
│   ├── keys/*.json                # claves de respuestas escritas a mano
│   ├── baseline/single_prompt.py  # baseline congelado
│   ├── graders/                   # nsdq.py, sources.py  (deterministas)
│   └── runner.py                  # → experiments/<nombre>.json
│
├── corpus/                        # snapshot congelado de fuentes reales + metadatos
├── fixtures/cassettes/            # respuestas LLM grabadas
├── experiments/                   # baseline.json, iteration-01..04.json, final.json
├── trajectories/                  # una por agente (entregable §9.4)
├── docker-compose.yml · Makefile · .env.example
└── README.md · REPRODUCTION.md · CHANGELOG_IMPROVEMENT.md   (inglés, para los jueces)
```

**Regla de propiedad para trabajo en paralelo:** cada pista posee directorios disjuntos.
Ningún agente edita fuera de los suyos. `contracts.py` es de solo lectura tras la Fase 0.

---

## 3. Flujo del bucle central (§7 de la especificación)

```
POST /goals                     GoalManager      → LearningGoal + ConceptGraph
  ↓
POST /goals/{id}/diagnostic     Diagnostician    → preguntas → respuestas → LearnerModel inicial
  ↓
POST /goals/{id}/research       Researcher       → Source[] verificadas (autoridad/versión/fecha)
  ↓
GET  /goals/{id}/next-session   CurriculumPlanner→ NextSessionDecision
  │                                  ↓
  │                             verifier.validate()
  │                                  ├─ ok        → devolver
  │                                  ├─ violación → repair prompt → reintento (máx 2)
  │                                  └─ agotado   → fallback: scheduler puro decide
  ↓
POST /sessions/{id}/assess      Assessor         → puntuación + misconceptions
  ↓
                                learner_model.update()   (puro)
  ↓
                                scheduler.next_review()  (puro)
  ↓
worker tick / POST /simulate-day
  ↓
notify: pregunta de recuperación derivada de la evidencia MÁS DÉBIL, no un recordatorio genérico
  ↓
respuesta → assess → learner_model → replan
```

---

## 4. El bucle de verificación y reparación

Es el núcleo de ingeniería agentic del proyecto. Toda salida de agente lo atraviesa.

```
salida del LLM (JSON)
   ↓
1. validación de esquema      Pydantic
   ↓
2. validación de restricciones  verifier.validate_session()
      PREREQ_VIOLATION        introduce un concepto con prerrequisito no cubierto
      REDUNDANT_MASTERED      dedica tiempo nuevo a un concepto con mastery > 0.85
      TIME_BUDGET_EXCEEDED    suma de bloques fuera de daily_minutes ±10 %
      MISSING_DUE_REVIEW      omite un concepto con next_review <= hoy
      UNKNOWN_CONCEPT         referencia un concept_id que no existe en el grafo
      EMPTY_SESSION           cero bloques
      UNSOURCED_CLAIM         bloque de contenido sin source_ids
   ↓
3. si hay violaciones → prompt de reparación con los códigos y mensajes CONCRETOS → reintento
   ↓
4. máximo 2 reintentos; si persiste → fallback determinista (el scheduler puro elige la sesión)
   ↓
5. cada intento queda registrado en la trayectoria con su violación
```

Por qué importa para la rúbrica: produce trayectorias con reintentos visibles (§9.4), convierte
"añadimos verificación" en una cifra medible del changelog (§7.4), y garantiza que el sistema
nunca devuelve una sesión inválida aunque el modelo falle (§7.3).

---

## 5. Frontera de determinismo

| Capa | Determinista | Motivo |
|---|:--:|---|
| `scheduler/` | ✔ | Aritmética de fechas. Testeable exhaustivamente |
| `verification/constraints.py` | ✔ | Reglas duras. Debe poder confiarse ciegamente |
| `domain/` | ✔ | Sin IO, sin LLM |
| `eval/graders/` | ✔ | **Si la calificación no es determinista, la evidencia no vale nada** |
| `agents/` | ✖ | Juicio genuino. Temperatura 0 + cassettes para reproducir |
| `providers/knowledge/live_search.py` | ✖ | Red. Por eso la evaluación usa `corpus.py` |

---

## 6. Trayectorias (entregable §9.4)

`trajectory/logger.py` escribe JSONL, un fichero por ejecución de agente:

```json
{"ts":"...","agent":"CurriculumPlanner","step":"llm_call","attempt":1,
 "system":"...","user":"...","model":"gemini-...","cache_hit":true}
{"ts":"...","agent":"CurriculumPlanner","step":"validation","attempt":1,
 "violations":[{"code":"PREREQ_VIOLATION","message":"ingress requiere services (mastery 0.30)"}]}
{"ts":"...","agent":"CurriculumPlanner","step":"repair_prompt","attempt":2,"user":"..."}
{"ts":"...","agent":"CurriculumPlanner","step":"validation","attempt":2,"violations":[]}
{"ts":"...","agent":"CurriculumPlanner","step":"result","decision":{...},"cost_usd":0.0031}
```

Se exportan las 5 trayectorias representativas a `trajectories/` con `make trajectories`.
El logger se escribe en la **Fase 0**: reconstruir trayectorias a posteriori es imposible.

---

## 7. Medición de coste y tiempo (§6.3 lo exige)

`providers/llm/meter.py` envuelve toda llamada y acumula tokens, coste estimado y latencia por
ejecución. `eval/runner.py` los agrega en `experiments/<nombre>.json`. Sin esta pieza desde el
principio, las columnas "Cost per task" y "Human time per task" del §6.3 no se pueden rellenar.
