# AGENTS.md — Instrucciones para agentes ejecutores

> Lo lee cualquier agente que trabaje en este repo: Codex, Cursor, Claude Code u otro.
> **Léelo entero antes de tocar un fichero.**

---

## 1. Qué es este proyecto

Learning Manager: un agente persistente que gestiona el recorrido de una persona desde una meta
de aprendizaje hasta un dominio verificable. Se presenta a la **micro1 Agentic Workflows
Hackathon**, cuyas bases están en `01_hackathon_micro1_detalles.md`.

Esto cambia las prioridades respecto a un proyecto normal:

- **La evidencia vale más que las funcionalidades.** Una cifra reproducible en `experiments/`
  puntúa; una pantalla bonita sin medición, no.
- **La reproducibilidad es un requisito, no un extra.** Un juez debe ejecutarlo desde cero.
- **Cada decisión de diseño debe poder justificarse con un número.** Es la pregunta de control
  de la categoría de 30 puntos.

## 2. Orden de lectura obligatorio

1. `PLAN.md` — cronograma, checkpoints, tu pista y tu fase
2. `docs/03_decisiones_congeladas.md` — lo que NO se discute
3. `docs/04_arquitectura.md` — límites de módulo
4. `docs/05_evaluacion.md` — solo si tocas `eval/`
5. `plan/NN-*.md` — tu fase concreta

## 3. Reglas que no se negocian

1. **`packages/core/learning_manager/contracts.py` es de solo lectura tras la Fase 0.**
   Si crees que necesitas cambiarlo: PARA y pregunta al humano. Es la fuente única de verdad
   que permite a tres agentes trabajar en paralelo.
2. **No salgas de los directorios de tu pista** (tabla en `PLAN.md` § Contrato de paralelismo).
3. **Cero dependencia de suscripciones.** Único acceso a LLM: `GEMINI_API_KEY` con
   `google-genai`. Nunca invoques CLIs de agentes desde el runtime del producto.
4. **Prohibidas las librerías de ingeniería inversa.** WhatsApp solo por Meta Cloud API oficial.
   Nada de `whatsapp-web.js`. Nada de MCP no oficiales de NotebookLM. Es una regla de
   elegibilidad de la hackathon (R3), no una preferencia.
5. **Ninguna fecha desde `datetime.now()`** en lógica de negocio: siempre `today: date` por
   parámetro. Hay un test que lo verifica y debe seguir pasando.
6. **Toda llamada a LLM pasa por `LLMProvider`.** Ninguna llamada directa al SDK fuera de
   `providers/llm/gemini.py`. Si no, la trayectoria queda incompleta y el §9.4 no se cumple.
7. **Temperatura 0** siempre.
8. **`.env` no se commitea nunca.** Si necesitas una variable nueva, añádela a `.env.example`.
9. **Nada de `print` ni `console.log`** sueltos: usa el logger.
10. **No inventes cifras.** Si el README necesita un número, tiene que salir de un fichero de
    `experiments/` generado por `make eval`.

## 4. Cómo trabajar una fase

```
1. Lee plan/NN-*.md entero antes de escribir código.
2. Crea la rama de tu pista si no existe: git checkout -b track/a-core
3. Por cada tarea, en este orden:
   a. Escribe el test que falla.
   b. Ejecútalo y confirma que falla por el motivo correcto.
   c. Escribe la implementación mínima.
   d. Ejecuta el test y confirma que pasa.
   e. Ejecuta `make check`.
   f. Commit (Conventional Commits).
4. Marca la casilla de la tarea en plan/NN-*.md.
5. Al terminar la fase: rebase sobre main, CI verde, merge.
```

**TDD estricto obligatorio** en `domain/`, `scheduler/`, `verification/`, `persistence/` y
`eval/graders/`. Son los módulos que sostienen la evidencia: si su test se escribe después,
mide lo que el código hace, no lo que debería hacer.
Tests después es aceptable en `apps/web/` y en `providers/notify/`.

## 5. Comandos

```bash
make setup          # venv, dependencias, pre-commit
make up             # docker compose up -d (4 servicios)
make down
make check          # ruff + mypy --strict + pytest        ← antes de cada commit
make test           # solo pytest
make stub-api       # servidor stub desde openapi.json (para la Pista C)
make eval-replay    # evaluación determinista, sin keys, sin coste
make eval-live      # evaluación real contra Gemini, regraba cassettes
make record         # graba cassettes del happy path
make simulate       # simulate-day 1..N end-to-end
make trajectories   # exporta las 5 trayectorias a trajectories/
```

## 6. Cuándo PARAR y preguntar al humano

- Necesitas modificar `contracts.py` u `openapi.json`.
- Necesitas escribir fuera de los directorios de tu pista.
- Un caso de evaluación o una clave de respuestas parece "mal": **no lo cambies**. Las claves se
  congelan antes de optimizar; tocarlas después invalida la comparación (bases §6.1).
- Vas a añadir una dependencia que no está en `pyproject.toml` / `package.json`.
- Un checkpoint de `PLAN.md` no se cumple a tiempo.
- Vas a hacer algo que envía mensajes de verdad a una persona (base R4: requiere aprobación
  humana explícita, y por defecto `SCHEDULER_MODE=simulation`).

## 7. Definición de "terminado" para una tarea

- [ ] El test existe, se escribió primero y pasa.
- [ ] `make check` en verde.
- [ ] Sin `TODO`, sin `pass  # implementar`, sin datos inventados.
- [ ] Si toca un agente: su llamada queda registrada en la trayectoria.
- [ ] Si toca coste o latencia: el medidor lo refleja.
- [ ] Commit hecho, casilla marcada en `plan/NN-*.md`.

## 8. Idioma

Español para planes, documentos y comentarios de decisión.
Inglés para identificadores de código, comandos, mensajes de commit y los tres entregables que
leen los jueces: `README.md`, `REPRODUCTION.md`, `CHANGELOG_IMPROVEMENT.md`.
