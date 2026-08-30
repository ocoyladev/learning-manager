# Fase 15 — Entregables de la submission

**Pista:** ninguna (SECUENCIAL) · **Depende de:** F14 · **Duración objetivo:** 5 h · **CP6**

**Entrega:** los cuatro entregables del §9 de las bases.

> Los tres documentos van **en inglés**: los leen los jueces.

---

## Tarea 15.1 — README.md (entregable §9.1)

**Ficheros:** Crear `README.md` (inglés)

Secciones obligatorias, en este orden:

- [ ] **The user and the bottleneck** — Ana, la profesional con 25 min/día. Qué hace hoy, qué
      parte cuesta tiempo, qué errores comete. Con el dato de `human_baseline.json`
- [ ] **What this is** — "We manage the learning journey, not just the learning content."
      Una frase sobre qué hace el sistema y qué NO hace
- [ ] **Architecture** — el diagrama de `docs/04_arquitectura.md`, con la frase clave:
      **cinco agentes donde hace falta juicio, funciones puras donde no**
- [ ] **What we built vs. what existed before** (regla R2) — declaración explícita: el repo se
      creó el 2026-08-30 con dos documentos de diseño; todo el código es de la competencia.
      Listar dependencias de terceros usadas
- [ ] **Results** — la tabla del §6.3 de las bases:

```markdown
| Metric | Simple baseline | Agent solution | Change |
|---|---:|---:|---:|
| NSDQ (primary) | 0.51 | 0.87 | +0.36 |
| Outdated claim rate | 0.22 | 0.03 | −0.19 |
| Human time per task | 14 min | 40 s | −95 % |
| Cost per task | $0.009 | $0.041 | +$0.032 |
```

  Con la advertencia de comparación justa: mismo modelo, mismas fuentes, mismos casos, mismo
  grader; y la diferencia de recursos documentada (el agente hace más llamadas, de ahí el coste)
- [ ] **Improvement Changelog** — enlace prominente a `CHANGELOG_IMPROVEMENT.md`
- [ ] **Main failure mode** — el real, con su frecuencia
- [ ] **Hot take** — una observación, salida de un fallo observado, no una frase genérica
- [ ] **Limitations** — honestas: NSDQ mide calidad de decisión, no resultado de aprendizaje;
      el baseline humano es n=3 con un solo evaluador; el corpus está congelado a una fecha
- [ ] Commit → `docs: add README with results and evidence links`

---

## Tarea 15.2 — REPRODUCTION.md (entregable §9.2)

**Ficheros:** Crear `REPRODUCTION.md` (inglés)

> Escrito para alguien que parte de cero. **Verifícalo ejecutándolo tú desde un clon limpio**
> (ya lo hiciste en la F13.4: copia esos tiempos reales aquí).

- [ ] **Prerequisites** — Docker ≥ 24, Docker Compose v2+, 4 GB de RAM, ~2 GB de disco.
      **Nada más. Ninguna API key para el camino por defecto**
- [ ] **Quick start (no credentials)**

```bash
git clone <url> && cd learning-manager
cp .env.example .env
docker compose up -d --build     # ~4 min la primera vez
open http://localhost:3000
```

- [ ] **Reproduce the headline numbers**

```bash
make eval-replay NAME=verify
python -m eval.compare experiments/final.json experiments/verify.json
# Expected: zero difference in nsdq and per-check breakdown
```

- [ ] **Run the baseline** — comando exacto y salida esperada
- [ ] **Run live against the real API** — cómo poner `GEMINI_API_KEY`, `LLM_MODE=live`,
      coste aproximado por ejecución completa (sale de `experiments/final.json`)
- [ ] **Optional: Telegram** — los 3 pasos con BotFather. **Optional: WhatsApp** — advertencia
      de que necesita HTTPS público y no es el camino reproducible
- [ ] **Expected output** — pegar la salida real de `make eval-replay`, con las cifras reales
- [ ] **Runtime and cost** — tiempos medidos de verdad en la F13.4, no estimados
- [ ] **Versions** — Python 3.12, Node 24, Postgres 16, el ID exacto del modelo Gemini,
      y el commit SHA con el que se produjeron los resultados
- [ ] **Troubleshooting** — `CassetteMissError` (qué significa y cómo arreglarlo), puerto
      ocupado, Postgres tardando en arrancar
- [ ] Commit → `docs: add reproduction guide verified from a clean clone`

---

## Tarea 15.3 — Trayectorias (entregable §9.4)

- [ ] **Paso 1:** `make trajectories` exporta a `trajectories/`
- [ ] **Paso 2:** verificar que hay una por agente y que cada una permite seguir: instrucciones,
      acciones, herramientas invocadas, respuestas, feedback, **reintentos**, checkpoints
      humanos y resultado final
- [ ] **Paso 3:** elegir como representativa del `CurriculumPlanner` **una que contenga una
      reparación**. Es la que mejor demuestra la ingeniería agentic
- [ ] **Paso 4:** `trajectories/README.md` (inglés) explicando cómo leer un JSONL y qué buscar
      en cada agente
- [ ] **Paso 5:** revisar que ninguna trayectoria contiene credenciales ni datos personales
      (regla R8)
- [ ] Commit → `docs: export representative agent trajectories`

---

## Tarea 15.4 — Vídeo (entregable §9.3, ≤ 5 min)

**Ficheros:** Crear `docs/video_script.md`

Estructura, con los 8 puntos que exige el §9.3:

```
0:00–0:30  Problema y usuario
           Ana, 25 min/día, deadline en 3 semanas. Muestra el dato de tiempo de
           preparación manual del human_baseline. NO empieces por la arquitectura.

0:30–0:55  Baseline simple
           Ejecuta el baseline en vivo sobre k8s-services-gap. Que se vea el fallo
           concreto: propone Ingress con Services al 0.30. Un error humanamente legible.

0:55–2:45  Demo end-to-end
           Onboarding → diagnóstico → knowledge map → sesión de hoy con su "por qué" →
           responder la evaluación → ver el learner model moverse →
           simulate-day → llega la pregunta proactiva por Telegram → responderla →
           ver cómo cambia el plan.
           ESTE ES EL CORAZÓN DEL VÍDEO. No lo comprimas para meter arquitectura.

2:45–3:30  Arquitectura agentic
           El diagrama. La frase: "cinco agentes donde hace falta juicio, funciones puras
           donde no". Muestra una trayectoria REAL con una reparación en pantalla.

3:30–4:20  Evaluación y resultados
           La tabla. Enseña que el grader es código, no un juez LLM. Enseña
           make eval-replay corriendo sin ninguna key.

4:20–4:45  Changelog y experimento eliminado
           El salto más grande y de dónde vino. Y el experimento que se quitó, con
           su cifra.

4:45–5:00  Hot take y cierre
```

- [ ] **Paso 1:** escribir el guion con el texto exacto a decir
- [ ] **Paso 2:** ensayar el recorrido una vez con cronómetro. **Todo en `LLM_MODE=replay`**:
      es instantáneo y no puede fallar por red en mitad de la grabación
- [ ] **Paso 3:** grabar
- [ ] **Paso 4:** verificar que aparecen los 8 puntos que exige el §9.3
- [ ] Commit → `docs: add video script`

---

## Tarea 15.5 — Repaso final de compliance

Recorrer las 10 reglas base del §8 una por una:

- [ ] R1 herramientas conocidas — sin problema
- [ ] R2 qué existía antes — declarado en el README, verificable con `git log`
- [ ] R3 licencias y TOS — API oficial de Gemini, API oficial de Meta. `grep -ri "whatsapp-web"`
      no devuelve nada. Sin MCP no oficiales
- [ ] R4 acciones con consecuencias — `SCHEDULER_MODE=simulation` por defecto, `NOTIFY_LIVE=false`
      por defecto, confirmación humana para enviar
- [ ] R5 revisor humano — controles del §44 en el dashboard; el sistema no cambia la meta solo
- [ ] R6 uso legal y ético — dominio técnico, sin afirmaciones médicas ni legales
- [ ] R7 datos permitidos — corpus público con atribución, learner states sintéticos
- [ ] R8 credenciales fuera — `git log -p | grep -iE "api[_-]?key|token" ` sin resultados reales;
      `.env` nunca commiteado
- [ ] R9 evidencia — toda cifra del README enlaza a `experiments/`
- [ ] R10 acceso de los jueces — clon limpio verificado en la F13.4

- [ ] **Checklist del §11 de las bases**, las 5 secciones, marcadas una a una
- [ ] Commit final → `chore: final compliance review`

---

## ✅ Criterio de salida — CP6 / ENTREGA

- [ ] `README.md` con usuario, cuello de botella, arquitectura, resultados, changelog,
      failure mode y hot take
- [ ] `REPRODUCTION.md` verificado desde un clon limpio, sin keys
- [ ] `CHANGELOG_IMPROVEMENT.md` con cada cifra enlazada
- [ ] 5 trayectorias exportadas, una con reparación visible
- [ ] Vídeo ≤ 5 min con los 8 puntos
- [ ] Las 10 reglas base repasadas
- [ ] Ninguna afirmación sin evidencia
