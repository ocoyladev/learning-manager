# Decisiones congeladas — Learning Manager

> **Estado:** CONGELADO el 2026-08-30. Cualquier cambio requiere aprobación humana explícita.
> Este documento es el *delta* sobre `02_learning_manager_especificacion.md`: resuelve las
> 12 decisiones pendientes del §50 y corrige tres puntos del diseño original.
> **Los agentes ejecutores NO pueden modificar este archivo.**

---

## 1. Restricciones del proyecto

| Restricción | Valor |
|---|---|
| Tiempo hasta la entrega | ~36 h de reloj desde 2026-08-30 |
| Ejecutores | Codex (principal), Cursor y Claude Code (UI/UX en paralelo) |
| Alcance | **Completo A–J del §22.** Riesgo de "60 % terminado" señalado y asumido por el autor |
| Estrategia frente al riesgo | Secuenciación por riesgo de puntaje + línea de corte explícita por checkpoint |

---

## 2. Resolución del §50 (decisiones pendientes)

| # | Decisión pendiente | Resolución congelada |
|---|---|---|
| 1 | Stack frontend/backend | Core **Python 3.12** (FastAPI, SQLAlchemy, Pydantic v2, pytest) + UI **Next.js 15 App Router / React / TS estricto / Tailwind** |
| 2 | KnowledgeProvider principal del MVP | `LiveSearchProvider` (búsqueda real, fuentes actuales) como camino del producto; `CorpusProvider` (snapshot congelado) como camino calificado de la evaluación |
| 3 | NotebookLM | **Interfaz documentada sin implementar.** Ni MCP no oficial ni API Enterprise. Coherente con §17 |
| 4 | LLM principal | **Gemini vía API key** (`google-genai`). Modelo por `GEMINI_MODEL`, ID verificado al construir. **Cero dependencia de suscripciones** |
| 5 | Persistencia | **PostgreSQL 16** como servicio de compose. Descartado SQLite: `api` y `worker` escriben concurrentemente y un fichero montado en contenedor produce bloqueos justo antes de la demo |
| 6 | Canal de notificación del demo | `ConsoleProvider` (por defecto, cero configuración) · `TelegramProvider` (reproducible por el juez con solo un token de BotFather, long-polling, sin HTTPS público) · `WhatsAppProvider` (**API oficial Meta Cloud**, activado por variable de entorno, opcional) |
| 7 | Dominio de los casos de evaluación | Ecosistema de contenedores en profundidad (Docker + Kubernetes) + **1 caso React/Next.js** como caso desafiante con deriva de versiones (§6.2 exige al menos uno) |
| 8 | Métrica principal | **NSDQ — Next-Session Decision Quality.** Ver `docs/05_evaluacion.md` |
| 9 | Rúbrica de adaptación correcta | 6 comprobaciones por caso, calificadas **por código**, no por un LLM |
| 10 | Algoritmo de scheduling | Heurística determinista del §25 + bonificación por racha. **Función pura, sin LLM** |
| 11 | Visualización de mastery/confidence | Barras de dominio + banda de confianza + estado del concepto + "por qué esta sesión" en el dashboard |
| 12 | Agentes separados vs. tools | **5 agentes** donde hace falta juicio; **funciones puras** donde no. Ver §4 |

---

## 3. Tres correcciones sobre la especificación original

### 3.1 La métrica principal cambia (corrige §28.2)

El "Adaptive Gap Resolution Score" no era calificable de forma determinista, y el §31 ya admitía
que un pre/post test no demuestra superioridad pedagógica. **No se reclama resultado de aprendizaje.
Se reclama calidad de decisión**, que sí es demostrable. La métrica primaria pasa a ser NSDQ.

### 3.2 El baseline cambia (corrige §27)

Comparar contra "Gemini Study Notebook / NotebookLM" es inejecutable por un juez desde un entorno
limpio (Regla 10) y compara dos *productos*, no la contribución del manager.

**Baseline congelado:** un único prompt a Gemini que recibe *exactamente* la misma entrada
(meta, estado del alumno, deadline, minutos/día, mismas fuentes del corpus) y debe devolver la
siguiente sesión en el mismo esquema JSON. Mismo modelo, mismas fuentes, mismos casos, mismo
calificador. La única variable independiente es el manager. Esto es literalmente lo que exige §4.1.

### 3.3 La verificación se extiende a las salidas del agente (amplía §13)

La especificación solo verificaba *fuentes*. Se añade verificación de *salidas*: validación de
esquema → validación de restricciones → prompt de reparación con los errores concretos → reintento
→ fallback determinista. Es el artefacto de ingeniería agentic más demostrable del proyecto,
genera trayectorias con reintentos visibles (§9.4) y produce evidencia directa para el changelog.

---

## 4. Los 5 agentes y las funciones puras

**Principio rector:** la rúbrica (§7.2) dice que la cantidad de componentes no puntúa, y el §9.4
**cobra una trayectoria por cada agente**. Los agentes tienen coste marginal negativo. Por eso:
un LLM solo donde hay juicio genuino.

| Agente (usa LLM) | Responsabilidad | Trayectoria obligatoria |
|---|---|---|
| `GoalManager` | Meta libre → objetivo estructurado, criterios de éxito, grafo de conceptos candidato | ✔ |
| `Diagnostician` | Genera el diagnóstico inicial, califica respuestas, produce el learner model inicial | ✔ |
| `Researcher` | Busca fuentes, juzga autoridad/versión/fecha, contrasta, produce corpus verificado | ✔ |
| `CurriculumPlanner` | Learner model + meta + deadline → siguiente sesión y replanificación. **Lo que mide NSDQ** | ✔ |
| `Assessor` | Genera evaluación, califica, extrae misconceptions, actualiza el learner model | ✔ |

| Componente determinista (sin LLM) | Por qué no es un agente |
|---|---|
| `scheduler` | Aritmética de fechas sobre la heurística del §25. Función pura, testeable al 100 % |
| `verifier` | Reglas duras: prerrequisitos, presupuesto de tiempo, no repetir dominado, repaso vencido |
| `trajectory` | Registro JSONL. Infraestructura |
| `graders` | Calificación contra clave de respuestas. **Debe ser determinista o la evidencia no vale** |

Este reparto es en sí mismo la respuesta a la pregunta de control del §7.2
("¿qué decisiones de diseño ayudaron al agente?") y debe defenderse así en el vídeo.

---

## 5. Modo de ejecución del LLM

```
LLM_MODE=live    → GeminiProvider real. Requiere GEMINI_API_KEY. Graba cassette de cada llamada.
LLM_MODE=replay  → CachedLLMProvider. Cero keys, cero coste, determinista. POR DEFECTO.
LLM_MODE=fake    → FakeLLM con respuestas fijas. Solo tests unitarios. Cero red.
```

Clave de cassette: `sha256(model + system + user + schema_name + temperature)`.
Cassettes commiteados en `fixtures/cassettes/`.

**Esto no sustituye a la API key.** El camino canónico del producto es `live` con clave de Gemini.
`replay` existe para que (a) un juez reproduzca los mismos números sin pagar, (b) CI corra gratis,
(c) la demo grabada no dependa de la red. Ambos modos se documentan en `REPRODUCTION.md`.

---

## 6. Reglas de compliance mapeadas

| Regla base | Cómo se cumple |
|---|---|
| R2 — qué existía antes | Repo inicializado el 2026-08-30 con solo los 2 documentos previos. Todo el código es de la competencia. Se declara en el README |
| R3 — licencias y TOS | Gemini vía API oficial. WhatsApp vía Meta Cloud API oficial. **Prohibido** `whatsapp-web.js` o cualquier librería de ingeniería inversa, por el mismo motivo que se rechazó el MCP de NotebookLM en §17 |
| R4 — acciones con consecuencias | `SCHEDULER_MODE=simulation` por defecto. El envío real de notificaciones exige `NOTIFY_LIVE=true` **y** confirmación humana explícita |
| R7 — datos permitidos | Solo learner states sintéticos. Ningún dato personal real en el repo |
| R8 — credenciales fuera | `.env` en `.gitignore`; solo se commitea `.env.example`. Hook de pre-commit que bloquea patrones de secreto |
| R9 — evidencia | Toda cifra del README procede de un fichero en `experiments/` generado por `make eval` |
| R10 — acceso de los jueces | `docker compose up` + `make eval-replay` sin ninguna key |

---

## 7. Convención de idioma

| Artefacto | Idioma |
|---|---|
| Planes, documentos de diseño, comentarios de decisión | Español |
| Identificadores de código, comandos, mensajes de commit | Inglés |
| `README.md`, `REPRODUCTION.md`, `CHANGELOG_IMPROVEMENT.md`, vídeo | **Inglés** (los leen los jueces) |
