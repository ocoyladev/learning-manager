# Fase 10 — UI Next.js

**Pista:** C (Cursor / Claude Code) · **Depende de:** F0 (`openapi.json` + `make stub-api`)
**Duración objetivo:** 4 h · **Tests: después, no TDD**

**Entrega:** onboarding, sesión diaria y dashboard, contra el contrato congelado.

> **Arranca inmediatamente tras CP0, sin esperar a la Pista A.** Construye contra
> `make stub-api` en `:8001`. Cuando la F5 esté lista, solo cambia `NEXT_PUBLIC_API_URL`.
>
> **La UI no contiene lógica de negocio.** Nada de decidir qué estudiar, calcular mastery ni
> fechas de repaso en el cliente: eso vive en el core y es lo que se califica. La UI presenta
> lo que la API devuelve.

---

## Tarea 10.1 — Andamiaje

**Ficheros:** `apps/web/` completo

- [x] Next.js 15 App Router, TypeScript **estricto**, Tailwind, sin `any` sin comentario
- [x] `apps/web/src/lib/api.ts` — **tipos generados desde `openapi.json`**, no escritos a mano:
      `npx openapi-typescript ../../openapi.json -o src/lib/api-types.ts`. Un tipo escrito a
      mano se desincroniza y rompe la integración de la F13
- [x] `apps/web/Dockerfile` multi-stage sobre `node:24-alpine`
- [x] `npm run lint && npx tsc --noEmit && npm run build` en verde
- [x] Commit → `chore(web): scaffold Next.js app with generated API types`

---

## Tarea 10.2 — Onboarding (`/`)

Pantalla 1 de la especificación §40.

- [x] Formulario: qué quieres aprender · por qué · minutos/día · deadline · casillas de formato
- [x] `POST /goals` → redirige a `/goals/{id}/diagnostic`
- [x] Validación en cliente: deadline futuro, minutos entre 5 y 240
- [x] Estado de carga real: crear la meta implica una llamada al LLM, tarda segundos.
      **Muestra qué está haciendo el agente** ("descomponiendo la meta en conceptos…"), no un
      spinner mudo. Es lo que hace visible el trabajo agentic en el vídeo
- [x] Commit → `feat(web): add goal onboarding screen`

---

## Tarea 10.3 — Diagnóstico (`/goals/[id]/diagnostic`)

- [x] `POST /goals/{id}/diagnostic` → renderiza los ítems uno a uno
- [x] Envía respuestas a `/diagnostic/answers`
- [x] Muestra el **Knowledge Map** resultante con el formato del §9 de la especificación:
      barras de dominio por concepto, ordenadas, con el estado en color
- [x] Cierra con el resumen de "Goal readiness" del §40: sesiones estimadas, minutos/día,
      finalización proyectada vs. deadline
- [x] Commit → `feat(web): add diagnostic flow and knowledge map`

---

## Tarea 10.4 — Sesión diaria (`/goals/[id]/today`)

Pantalla del §41. **Es la pantalla que sale en el vídeo.**

- [x] `GET /goals/{id}/next-session?today=...`
- [x] Renderiza los bloques con su tipo, minutos y objetivo
- [x] **Muestra el `rationale` de forma prominente** bajo el título "¿Por qué esta sesión?" —
      es lo que hace percibir la adaptación agentic y lo que un juez busca
- [x] Si `deadline_status != on_track`, banner visible con el estado y qué implica
- [x] Los bloques `retrieval` son interactivos: se responden y se envían a `/sessions/{id}/assess`
- [x] Tras evaluar, muestra el delta del learner model: qué subió, qué bajó, qué se reprogramó
- [x] Commit → `feat(web): add daily session screen with adaptation rationale`

---

## Tarea 10.5 — Dashboard (`/goals/[id]`)

Formato del §42.

- [x] Progreso global, `on_track`, `deadline_status`, deadline, `estimated_sessions` y
      `projected_completion` (los devuelve `GET /goals/{id}/dashboard`)
- [x] Listas de fuerte / necesita trabajo
- [x] Próximo repaso **con su motivo** ("2 intentos de recuperación fallidos")
- [x] Panel de **fuentes**: las que sustentan la sesión, con autoridad, versión y fecha.
      Hace visible el Diferenciador 6 y permite al usuario auditar (§44)
- [x] Controles humanos del §44: cambiar disponibilidad, pausar meta, rechazar una recomendación,
      marcar una sesión como inadecuada. **El agente no puede cambiar la meta en silencio**
- [x] Commit → `feat(web): add mastery dashboard with source panel and human controls`

---

## Tarea 10.6 — Tests de la UI

- [x] Tests de componente para el Knowledge Map y el panel de racional (Vitest + Testing Library)
- [x] Un test end-to-end con Playwright contra `make stub-api`: onboarding → diagnóstico →
      sesión → dashboard
- [x] `npm run lint && npx tsc --noEmit && npm test && npm run build` en verde
- [x] Commit → `test(web): add component and e2e coverage`

---

## ✅ Criterio de salida

- [x] Las 4 pantallas funcionan contra el stub sin que la Pista A haya terminado
- [x] Cero lógica de negocio en el cliente — verificado leyendo `src/`: nada de umbrales de
      mastery, aritmética de fechas de repaso ni selección de conceptos
- [x] Tipos generados desde `openapi.json`, no escritos a mano
- [x] `docker compose up` sirve la web en `:3000`
