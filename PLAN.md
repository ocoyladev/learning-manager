# Learning Manager — Plan de implementación

> **Para agentes ejecutores:** lee `AGENTS.md` ANTES de tocar nada. Cada fase vive en
> `plan/NN-*.md` y es ejecutable de forma independiente. Los pasos usan casillas `- [ ]`.
> En Claude Code puedes usar `superpowers:subagent-driven-development` o
> `superpowers:executing-plans`; en Codex/Cursor ejecuta las fases directamente.

**Objetivo:** Un agente persistente que gestiona el recorrido desde una meta de aprendizaje
hasta un dominio verificable, y que demuestra con cifras deterministas que **decide mejor**
qué estudiar a continuación que un LLM con un solo prompt sobre la misma entrada.

**Arquitectura:** Core Python headless (5 agentes LLM + scheduler/verificador deterministas +
Postgres) tras una API FastAPI, con UI Next.js y canales Telegram/WhatsApp. Todo LLM pasa por
una capa de grabación/reproducción que hace la evaluación determinista y reproducible sin keys.
Detalle en `docs/04_arquitectura.md`.

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · Postgres 16 · pytest · ruff ·
mypy · Next.js 15 (App Router, TS estricto, Tailwind) · Docker Compose · GitHub Actions ·
`google-genai` (Gemini).

**Especificaciones:** `docs/03_decisiones_congeladas.md` (decisiones) ·
`docs/04_arquitectura.md` (arquitectura) · `docs/05_evaluacion.md` (evaluación) ·
`01_hackathon_micro1_detalles.md` (bases) · `02_learning_manager_especificacion.md` (visión).

---

## Restricciones globales

Se aplican a **todas** las tareas. Copiadas literalmente de los documentos congelados.

1. **`packages/core/learning_manager/contracts.py` es de solo lectura tras la Fase 0.**
   Si una tarea parece necesitar cambiarlo, PARA y pregunta al humano.
2. **Cero dependencia de suscripciones.** El único acceso a LLM es `GEMINI_API_KEY` vía
   `google-genai`. Prohibido invocar CLIs de agentes desde el runtime.
3. **`LLM_MODE=replay` es el modo por defecto** en tests, CI y `docker compose up`.
4. **Prohibidas las librerías de ingeniería inversa.** WhatsApp solo por la Meta Cloud API
   oficial. Nada de `whatsapp-web.js` ni MCP no oficiales de NotebookLM (base R3, spec §17).
5. **Ninguna fecha sale de `datetime.now()`** en lógica de negocio. Siempre del parámetro
   `today: date`. Hay un test que lo verifica.
6. **Toda llamada a LLM pasa por `LLMProvider`** y queda registrada en la trayectoria.
   Ninguna llamada directa al SDK fuera de `providers/llm/gemini.py`.
7. **Temperatura 0** en todas las llamadas de producción y evaluación.
8. **TDD estricto** en `domain/`, `scheduler/`, `verification/`, `eval/graders/`,
   `persistence/`: test que falla primero, siempre. Tests después en UI y canales.
9. **Sin `any` en TypeScript** sin comentario justificándolo. `mypy --strict` en el core.
10. **Nada de `print`/`console.log`** sueltos: usar el logger del proyecto.
11. **Commits en Conventional Commits** y frecuentes: uno por tarea como mínimo.
12. **`.env` nunca se commitea.** Solo `.env.example`.
13. **Toda cifra que aparezca en el README debe existir en un fichero de `experiments/`.**

---

## Cronograma, pistas paralelas y checkpoints

`T+0` = arranque. Tres pistas trabajan en directorios **disjuntos**.

```
T+0 ──────────── FASE 0 · SECUENCIAL · BLOQUEA TODO ────────────── T+2
                 contratos · compose · CI · trajectory · stub API
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
  PISTA A (Codex #1)         PISTA B (Codex #2)         PISTA C (Cursor + Claude Code)
  núcleo del producto        conocimiento y evidencia    UI y canales
  F1 learner model           F6 Gemini + cassettes       F10 dashboard Next.js
  F2 scheduler puro          F7 researcher + fuentes     F11 Telegram
  F3 verificador + repair    F8 corpus + claves          F12 WhatsApp (tope 60 min)
  F4 los 5 agentes           F9 eval + baseline + graders
  F5 API FastAPI
      └───────────────────────────┼───────────────────────────┘
                                  ▼
T+22 ────── F13 integración end-to-end · SECUENCIAL ────── T+26
T+26 ────── F14 evaluación, experimentos y changelog ───── T+31
T+31 ────── F15 entregables de submission y vídeo ──────── T+36
```

### Checkpoints con gate duro

| CP | Momento | Condición para pasar | Si falla |
|---|---|---|---|
| **CP0** | T+2 | `contracts.py` congelado y commiteado · `docker compose up` levanta 4 servicios · CI verde · `make stub-api` responde | **No se paraleliza.** Se termina la Fase 0 antes de lanzar nada más |
| **CP1** | T+8 | Baseline congelado · graders NSDQ pasando contra 3 salidas de ejemplo escritas a mano · 11 casos y claves commiteados | Se corta alcance de la Pista A, nunca de la evidencia |
| **CP2** | T+16 | Happy path completo en `replay`: goal → diagnostic → research → plan → lesson → assess → update → schedule | Se aplica corte nivel 1 |
| **CP3** | T+22 | `experiments/baseline.json` y `experiments/iteration-01.json` existen. Changelog iniciado | Se aplica corte nivel 2 |
| **CP4** | T+28 | UI y Telegram integrados · cassettes grabados en `live` · trayectorias exportables | Se aplica corte nivel 3 |
| **CP5** | T+32 | Eval final · README · REPRODUCTION · 5 trayectorias · changelog cerrado | Se aplica corte nivel 4 |
| **CP6** | T+35 | Vídeo ≤ 5 min grabado | Se graba una versión sin editar |

### Línea de corte (contingencia)

Solo se ejecuta si un checkpoint falla. **Se corta de arriba hacia abajo, nunca de abajo hacia
arriba.** El objetivo es que lo terminado sea un todo coherente, no diez mitades.

| Nivel | Qué se abandona | Por qué es lo primero en caer |
|---|---|---|
| 1 | WhatsApp (queda Telegram + Console) | Telegram ya demuestra el canal y es reproducible por el juez |
| 2 | Casos 9 y 10 del eval (quedan 9 + el difícil = 10) | Las bases piden "10 o más"; 10 sigue cumpliendo |
| 3 | Dashboard Next.js → informe HTML estático generado por el core | El vídeo puede mostrar el informe; la lógica calificada no cambia |
| 4 | Verificación de fuentes como métrica → queda como evidencia cualitativa | Duele, pero NSDQ sostiene sola la Measured Improvement |
| 5 | Diagnóstico adaptativo → diagnóstico fijo de 8 preguntas | Reduce una llamada de agente, no rompe el bucle |

**Nunca se cortan:** contratos, scheduler, verificador + reparación, graders, baseline,
ejecución de evaluación, README, REPRODUCTION, trayectorias, vídeo. Son la rúbrica entera.

---

## Índice de fases

| Fase | Fichero | Pista | Depende de | Entrega |
|---|---|---|---|---|
| 0 | `plan/00-contratos-y-andamiaje.md` | — | — | Contratos congelados, compose, CI, logger, stub API |
| 1 | `plan/01-learner-model-persistencia.md` | A | F0 | Modelo del alumno + repositorios Postgres |
| 2 | `plan/02-scheduler-puro.md` | A | F0 | Spacing y viabilidad de deadline, funciones puras |
| 3 | `plan/03-verificador-y-reparacion.md` | A | F0, F2 | Restricciones + bucle de reparación + fallback |
| 4 | `plan/04-agentes.md` | A | F1, F2, F3, F6 | Los 5 agentes con sus prompts |
| 5 | `plan/05-api-y-worker.md` | A | F1–F4 | FastAPI, worker, `simulate-day` |
| 6 | `plan/06-llm-provider-cassettes.md` | B | F0 | Gemini + cache + medidor de coste |
| 7 | `plan/07-researcher-y-fuentes.md` | B | F0, F6 | Búsqueda en vivo + verificación de autoridad/versión |
| 8 | `plan/08-corpus-y-casos.md` | B | F0, F7 | Corpus congelado, 11 casos, claves de respuestas |
| 9 | `plan/09-eval-baseline-graders.md` | B | F0, F8 | Graders deterministas, baseline, runner |
| 10 | `plan/10-ui-dashboard.md` | C | F0 (stub) | Onboarding, sesión diaria, dashboard |
| 11 | `plan/11-canal-telegram.md` | C | F0 (stub) | Notificación proactiva + captura de respuesta |
| 12 | `plan/12-canal-whatsapp.md` | C | F11 | Meta Cloud API, opcional, tope 60 min |
| 13 | `plan/13-integracion-e2e.md` | — | Todas | Trayectoria completa real, cassettes grabados |
| 14 | `plan/14-evaluacion-y-changelog.md` | — | F13 | Experimentos, iteraciones, changelog con evidencia |
| 15 | `plan/15-entregables.md` | — | F14 | README, REPRODUCTION, trayectorias, guion de vídeo |

---

## Cobertura del alcance (A–J del §22 y §48 de la especificación)

Verificación de que el alcance completo elegido está cubierto. Ninguna letra se cayó.

| §22 | Capacidad | Fases que la construyen |
|---|---|---|
| A | Onboarding (meta, propósito, deadline, min/día, preferencias) | F4.1 GoalManager · F5.1 `POST /goals` · F10.2 UI |
| B | Diagnóstico (5–10 preguntas, gaps) | F4.2 Diagnostician · F5.1 · F10.3 UI + knowledge map |
| C | Research con fuentes verificables | F7.1 autoridad · F7.3 búsqueda en vivo · F7.4 claims |
| D | Plan inicial (knowledge map, sesiones, tiempo estimado) | F1.2 grafo · F2.2 viabilidad · F10.3 goal readiness |
| E | Una micro-lección | F4.5 Teacher · F10.4 pantalla de sesión |
| F | Evaluación posterior con resultados guardados | F4.4 Assessor · F1.3 persistencia · F5.1 |
| G | Learner model actualizado | F1.1 `apply_assessment` · F1.3 repositorio |
| H | Adaptación de la siguiente sesión | F4.3 planner · F3 verificador · F2 scheduler |
| I | Recordatorio proactivo reproducible | F5.2 `simulate-day` · F11.2 Telegram · F11.3 bucle |
| J | Mastery dashboard con motivos | F10.5 · endpoint `/dashboard` |

| §48 | Criterio del MVP | Dónde se demuestra |
|---|---|---|
| 1–10 | Los diez, en una sola trayectoria | F13.2 `test_full_goal_to_mastery_trajectory` |

| §9 bases | Entregable | Fase |
|---|---|---|
| 9.1 | Código completo + Improvement Changelog | F14.4 · F15.1 |
| 9.2 | Reproduction guide | F15.2 (verificada en F13.4) |
| 9.3 | Vídeo ≤ 5 min | F15.4 |
| 9.4 | Trayectorias por agente | F0.3 logger · F15.3 exportación |

---

## Contrato de paralelismo

**Propiedad de directorios.** Un agente solo escribe dentro de los suyos.

| Pista | Escribe en | Lee (sin escribir) |
|---|---|---|
| A | `learning_manager/{domain,scheduler,verification,agents,persistence,api,worker}/` | `contracts.py`, `providers/` |
| B | `learning_manager/providers/`, `eval/`, `corpus/`, `fixtures/` | `contracts.py` |
| C | `apps/web/`, `learning_manager/providers/notify/` | `contracts.py`, `openapi.json` |

**Reglas.**
1. `contracts.py` y `openapi.json` se congelan en la Fase 0. Nadie los edita después.
2. Cada pista trabaja en su rama: `track/a-core`, `track/b-eval`, `track/c-ui`.
3. Rebase sobre `main` antes de cada merge. CI debe estar verde para mergear.
4. Si una pista necesita algo de otra que aún no existe, usa el doble de `contracts.py`
   (`FakeLLM`, `StubKnowledgeProvider`, `make stub-api`). **Nunca esperar bloqueado.**
5. Conflicto entre pistas = error de diseño de fase. Se para y se avisa al humano.
