# Learning Manager — Especificación consolidada del proyecto

> **Estado:** documento de definición previo al plan de implementación  
> **Fecha:** 2026-08-30  
> **Nombre de trabajo:** **Learning Manager**  
> **Categoría:** Agentic learning / autonomous learning management  
> **Objetivo del documento:** congelar el problema, propuesta, diferenciación y arquitectura conceptual antes de crear el plan, diseñar e implementar.

---

# 1. Resumen ejecutivo

Learning Manager parte de una observación sencilla:

> Una persona que quiere aprender algo nuevo no solo necesita explicaciones. También debe descubrir fuentes, evaluar cuáles son confiables y actuales, ordenar prerrequisitos, construir un plan, estudiar, comprobar cuánto entendió, recordar lo que olvidó y decidir qué estudiar después.

Actualmente muchas herramientas de IA resuelven fragmentos de este proceso:

- búsqueda y grounding;
- generación de resúmenes;
- generación de quizzes y flashcards;
- tutoría conversacional;
- planificación de cursos;
- seguimiento de progreso.

La propuesta **no debe competir intentando reconstruir todas esas capacidades**.

La visión es:

> **Un agente persistente que administra el recorrido desde una meta de aprendizaje hasta un nivel de dominio verificable.**

El producto recibe principalmente:

```text
¿Qué quieres aprender?
¿Para qué quieres aprenderlo?
¿Cuánto tiempo tienes?
¿Cuál es tu deadline?
¿Cómo prefieres aprender?
```

Y el sistema gestiona:

```text
goal
  ↓
diagnose
  ↓
research
  ↓
verify
  ↓
plan
  ↓
teach
  ↓
assess
  ↓
remember
  ↓
adapt
  ↓
schedule
  ↓
remind
  ↓
reassess
  ↓
mastery
```

La contribución diferencial debe concentrarse especialmente en **lo que ocurre entre sesiones**:

- decidir qué debe estudiar la persona;
- mantener un modelo persistente de lo que sabe;
- detectar conocimiento frágil u olvidado;
- adaptar el currículo;
- programar repasos;
- actuar proactivamente;
- determinar si el usuario va encaminado a alcanzar su meta.

---

# 2. Problema

## 2.1 Problema amplio

Existe abundancia de información para aprender casi cualquier materia, pero esa abundancia introduce fricción:

```text
1000 tutoriales
300 videos
50 cursos
20 opiniones
documentación
posts viejos
posts nuevos
────────────────
¿qué estudio?
¿en qué orden?
¿qué es correcto?
¿qué debo ignorar?
```

El problema no es únicamente falta de contenido.

Es **gestionar el proceso de adquisición de conocimiento**.

---

## 2.2 Cuello de botella

Una persona con poco tiempo puede gastar una parte importante de su disponibilidad en:

1. buscar recursos;
2. comparar recursos;
3. comprobar actualidad/credibilidad;
4. decidir por dónde empezar;
5. crear un plan;
6. transformar fuentes en materiales;
7. recordar que debe estudiar;
8. decidir qué repasar;
9. evaluar si realmente aprendió;
10. replanificar cuando falla o avanza más rápido de lo previsto.

El tiempo de preparación puede competir directamente con el tiempo real de estudio.

---

# 3. Usuario objetivo

Evitar:

> “Todo el mundo que quiera aprender.”

Es demasiado amplio para la hackathon.

## Usuario primario recomendado

> **Profesional ocupado que desea adquirir una nueva habilidad o conocimiento concreto, pero dispone de tiempo limitado y no quiere invertirlo en investigar, organizar y mantener manualmente un plan de aprendizaje.**

Ejemplo de persona:

```text
Ana
Profesional a tiempo completo
Objetivo: aprender SQL para optar a un nuevo puesto
Disponibilidad: 20 minutos/día
Deadline: 3 semanas
Preferencia: ejemplos prácticos + ejercicios
Problema: pierde tiempo comparando recursos y abandona planes que no se adaptan
```

### Casos de uso compatibles

- habilidad profesional;
- preparación para entrevista;
- certificación;
- curso universitario;
- tecnología nueva;
- idioma;
- conocimiento general.

### MVP recomendado

Para la hackathon, concentrar la demo en **una habilidad profesional o técnica** porque:

- se pueden encontrar fuentes oficiales;
- se puede evaluar conocimiento;
- es fácil producir casos reproducibles;
- evita depender de afirmaciones médicas, legales u otras áreas de alto impacto.

---

# 4. Propuesta de valor

## Frase principal

> **Tell me what you want to learn. I’ll manage the journey to mastery.**

Alternativas:

> **Don’t build a study plan. Give me the goal.**

> **An autonomous learning manager that owns the journey from goal to mastery.**

> **NotebookLM helps you work with knowledge. Learning Manager decides what you should learn next and when.**

---

# 5. Qué NO es el producto

Learning Manager no debe presentarse como:

- otro chatbot educativo;
- otro generador de cursos;
- otro NotebookLM;
- otro generador de flashcards;
- otro resumidor;
- otro “AI tutor” reactivo;
- un wrapper con una pantalla diferente.

Si la arquitectura termina siendo:

```text
frontend
   ↓
NotebookLM
   ↓
resultado
```

la diferenciación sería insuficiente.

---

# 6. Hipótesis central

## Hipótesis

Un agente persistente que mantiene un modelo del alumno y gestiona proactivamente **qué aprender, cuándo aprender y cuándo repasar** reduce el esfuerzo de administración del estudio y adapta mejor el recorrido a los gaps reales que una herramienta reactiva de estudio.

## Pregunta de la hackathon

> ¿Añadir un Learning Manager por encima de una herramienta de conocimiento/tutoría ya competente mejora de forma medible la gestión del aprendizaje?

---

# 7. Loop central: Goal → Mastery

```text
                        USER GOAL
                            │
                            ▼
                    ┌───────────────┐
                    │ GOAL MANAGER  │
                    └───────┬───────┘
                            │
                            ▼
                    Initial diagnostic
                            │
                            ▼
                    Knowledge state
                            │
                            ▼
                    Research / sources
                            │
                            ▼
                    Verified knowledge
                            │
                            ▼
                    Living curriculum
                            │
                            ▼
                      Today's session
                            │
                            ▼
                        Assessment
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
              MASTERED              WEAK
                  │                   │
                  ▼                   ▼
             lower priority       reinforce
                  │                   │
                  └─────────┬─────────┘
                            ▼
                       Learner Model
                            │
                            ▼
                    Replan curriculum
                            │
                            ▼
                       Scheduler
                            │
                            ▼
                       🔔 Proactive
                            │
                            ▼
                        Reassess
                            │
                            ▼
                        MASTERY
```

---

# 8. Diferenciador 1 — Goal ownership

El sistema no recibe únicamente:

> “Explícame Kubernetes.”

Recibe una meta:

```json
{
  "goal": "Poder desplegar una aplicación en Kubernetes y responder preguntas fundamentales de entrevista",
  "deadline": "2026-09-20",
  "daily_minutes": 25,
  "current_level": "beginner",
  "preferred_learning": ["practice", "visual explanations"]
}
```

El agente debe transformar esa meta en un estado gestionable.

---

# 9. Diferenciador 2 — Diagnóstico antes de enseñar

No comenzar necesariamente con el capítulo 1.

Primero comprobar qué sabe el usuario.

Ejemplo:

```text
Knowledge Map

Containers           ███████░░░ 70%
Images               █████░░░░░ 50%
Volumes              ██░░░░░░░░ 20%
Networking           ░░░░░░░░░░  0%
Docker Compose       ██░░░░░░░░ 20%
Security             ░░░░░░░░░░  0%
```

Después priorizar gaps.

### Principio

> No hacer estudiar al usuario aquello que ya puede demostrar que domina.

---

# 10. Diferenciador 3 — Living Curriculum

El currículo no es un curso generado una vez.

Debe cambiar.

Plan inicial:

```text
D1 Containers
D2 Images
D3 Volumes
D4 Networking
D5 Compose
```

Después de evaluaciones:

```text
Containers       95% mastered
Images           93% mastered
Networking       weak
```

Nuevo plan:

```text
D3 Volumes
D4 Networking
D5 Networking practice   ← añadido
D6 Compose
```

El sistema puede:

- comprimir;
- expandir;
- reordenar;
- introducir prerequisitos;
- añadir recuperación;
- eliminar contenido redundante.

---

# 11. Diferenciador 4 — Learner Model persistente

El corazón del producto no debería ser un historial de chat, sino un **modelo del alumno**.

Ejemplo conceptual:

```json
{
  "goal_id": "kubernetes-interview",
  "concepts": {
    "pods": {
      "mastery": 0.91,
      "confidence": 0.86,
      "last_assessed": "2026-08-30",
      "next_review": "2026-09-03"
    },
    "services": {
      "mastery": 0.42,
      "confidence": 0.75,
      "misconceptions": [
        "confuses ClusterIP with NodePort"
      ],
      "next_review": "2026-08-31"
    }
  }
}
```

## El modelo debería distinguir

- conocimiento nunca evaluado;
- conocimiento débil;
- conocimiento dominado;
- conocimiento posiblemente olvidado;
- misconception concreta;
- confianza en la estimación.

---

# 12. Diferenciador 5 — Proactividad temporal

Una notificación genérica:

> “Recuerda estudiar.”

no es suficiente.

Una notificación inteligente podría ser:

> “Ayer confundiste `ClusterIP` con `NodePort`. Antes de continuar, ¿qué opción expone el servicio solo dentro del cluster?”

La respuesta modifica el learner model.

Loop:

```text
notification
     ↓
micro-question
     ↓
answer
     ↓
assessment
     ↓
learner model
     ↓
scheduler
```

---

# 13. Diferenciador 6 — Verification / trusted knowledge

El sistema no debería generar material educativo desde una mezcla arbitraria de fuentes.

Para materias sujetas a cambios:

```text
search
 ↓
authority
 ↓
date/version
 ↓
cross-check
 ↓
trusted corpus
```

Ejemplo de caso difícil:

> aprender React Server Components.

El sistema puede encontrar:

- documentación actual;
- posts antiguos;
- tutoriales de versiones previas;
- respuestas de foros;
- contenido SEO.

El agente debe preferir fuentes apropiadas y evitar enseñar comportamiento obsoleto como si fuera actual.

---

# 14. Principio de arquitectura: no reconstruir NotebookLM

NotebookLM ya cubre una parte importante del pipeline de conocimiento.

NotebookLM permite buscar fuentes desde la Web/Drive con Fast Research y también usar Deep Research; su función Discover Sources parte de una consulta y ayuda a incorporar fuentes relevantes.

Por ello, **research/RAG/artifact generation no debería ser la contribución principal**.

La arquitectura debe permitir delegar esa capa.

---

# 15. NotebookLM / Gemini como Knowledge Provider

## Estrategia

Tratar NotebookLM como una **tool especializada**, no como el producto.

```text
Learning Manager
      │
      ├── Goal Manager
      ├── Learner Model
      ├── Curriculum Manager
      ├── Assessment
      ├── Adaptive Scheduler
      └── KnowledgeProvider
               │
        ┌──────┴───────────┐
        ▼                  ▼
   Notebook/Gemini      fallback
      provider          provider
```

## Interfaz conceptual

```ts
interface KnowledgeProvider {
  research(topic: string): Promise<ResearchResult>
  query(question: string): Promise<GroundedAnswer>
  summarize(scope: string): Promise<Summary>
  getSources(): Promise<Source[]>
  createPractice(topic: string): Promise<PracticeItem[]>
}
```

El sistema no debería depender directamente de la UI o estructura interna de NotebookLM.

---

# 16. Qué delegar y qué conservar

| Capacidad | Proveedor especializado | Learning Manager |
|---|---:|---:|
| Buscar fuentes | ✓ | orquesta |
| Deep/Fast Research | ✓ | decide cuándo |
| Grounding | ✓ | usa el resultado |
| Resumir corpus | ✓ | contextualiza |
| Flashcards base | opcional | selecciona |
| Quiz base | opcional | decide objetivo/dificultad |
| Objetivo final | | **✓** |
| Deadline | | **✓** |
| Tiempo diario | | **✓** |
| Learner model persistente | | **✓** |
| Knowledge graph orientado a la meta | | **✓** |
| Decidir qué enseñar después | | **✓** |
| Spaced review | | **✓** |
| Detectar olvido | | **✓** |
| Scheduling | | **✓** |
| Notificaciones proactivas | | **✓** |
| Replanificación | | **✓** |
| Mastery decision | | **✓** |

---

# 17. NotebookLM MCP — oportunidad y riesgo

## Hallazgo

Existen MCP comunitarios para NotebookLM.

Sin embargo, algunos indican explícitamente que:

- utilizan APIs internas no documentadas;
- dependen de cookies del navegador;
- pueden romperse si Google cambia endpoints;
- son experimentales.

## Riesgo para la hackathon

La guía exige:

- respetar términos/licencias;
- reproducibilidad desde entorno limpio.

Por tanto, un MCP de ingeniería inversa puede perjudicar:

1. **compliance**;
2. **reproducibilidad**;
3. **estabilidad del demo**.

## Decisión arquitectónica

No acoplar el proyecto a un MCP no oficial.

Debe existir:

```text
KNOWLEDGE_PROVIDER=...
```

y un fallback.

Ejemplo:

```text
NotebookProvider
GeminiProvider
WebResearchProvider
```

---

# 18. Opción oficial de Google

Google Cloud expone actualmente APIs de **Gemini Notebook Enterprise** en preview para gestionar notebooks y fuentes.

La documentación oficial permite, entre otras operaciones:

- crear notebook;
- recuperar notebook;
- listar;
- eliminar;
- compartir;
- añadir fuentes;
- cargar archivos;
- añadir contenido web;
- usar Google Docs/Slides;
- usar YouTube.

Requiere configuración/licenciamiento de Gemini Notebook Enterprise y la superficie está en Preview.

### Implicación

Para la hackathon debe evaluarse:

- disponibilidad real para el equipo;
- costo/configuración;
- funciones expuestas frente a las que necesita el MVP;
- tiempo de integración.

No asumir que la API Enterprise equivale a automatizar todas las capacidades de la UI consumer de NotebookLM.

---

# 19. Estado de la competencia — 2026-08-30

La categoría está avanzando rápidamente.

## 19.1 Gemini Study Notebooks — competidor crítico

Google lanzó Study Notebooks en Gemini en junio de 2026.

Ya ofrecen:

- objetivo de aprendizaje;
- diagnóstico;
- detección de fortalezas/gaps;
- lecciones personalizadas;
- lecciones breves;
- quizzes;
- seguimiento de progreso;
- actualización de recomendaciones según desempeño.

### Consecuencia

La diferenciación NO puede ser:

> “diagnóstico + lecciones + quizzes + adaptación”.

Google ya ocupa gran parte de ese espacio.

### Oportunidad restante

Concentrarse en:

- gestión persistente entre sesiones;
- deadline;
- disponibilidad diaria;
- scheduler;
- reactivación proactiva;
- forgetting / spaced review;
- gestión de la trayectoria global;
- meta de dominio verificable.

---

## 19.2 NotebookLM

Capacidades relevantes:

- fuentes propias;
- Discover Sources;
- búsqueda Web/Drive;
- Fast Research;
- Deep Research;
- grounding sobre fuentes;
- artefactos de estudio.

### Consecuencia

No reconstruir una plataforma de “fuentes → resumen → quiz” como núcleo.

---

## 19.3 Google Learn About

Google Learn About combina Google Search, Gemini y principios didácticos.

Ofrece:

- explicaciones;
- imágenes y videos;
- tarjetas de misconceptions;
- “stop and think”;
- pruebas de conocimiento;
- guías interactivas;
- uso de materiales subidos.

A la fecha consultada, Google indica disponibilidad en EE. UU. y en inglés.

### Diferencia posible

Learn About es principalmente una experiencia de aprendizaje interactiva; Learning Manager debe diferenciarse mediante gestión longitudinal/proactiva de objetivos.

---

## 19.4 ChatGPT Study Mode

Study Mode puede:

- enseñar desde cero;
- hacer preguntas de estilo socrático;
- explicar por niveles;
- comprobar comprensión;
- crear práctica/flashcards;
- trabajar con materiales subidos;
- usar Memoria para personalizar cuando está habilitada.

### Diferencia posible

Learning Manager no debería competir por “mejor chat de estudio”.

La contribución debe estar en:

```text
deadline
+ knowledge state
+ scheduler
+ proactive follow-up
+ replan
+ measurable goal completion
```

---

## 19.5 DeepTutor

DeepTutor es un proyecto open source “agent-native” de tutoría personalizada.

Su arquitectura reciente incluye, entre otras capacidades:

- Guided Learning;
- investigación agentic;
- quiz;
- persistent memory;
- mastery workflows;
- tools/skills;
- MCP;
- partners/tutors persistentes.

### Riesgo competitivo

Es uno de los proyectos más cercanos al concepto de tutor agentic persistente.

### Implicación

No usar como diferenciación simplemente:

> “multi-agent tutor with memory”.

---

## 19.6 Project Cognita

Cognita se presenta como un tutor socrático autónomo que:

- planifica;
- enseña;
- verifica;
- adapta;

orquestando agentes especializados alrededor de un modelo vivo del alumno.

### Riesgo

Ocupa explícitamente:

```text
plan → teach → assess → adapt
```

### Implicación

El Learning Manager debe demostrar que la unidad central es **gestionar la trayectoria temporal hacia una meta**, no solamente la tutoría adaptativa durante una sesión.

---

## 19.7 Coursebox

Coursebox puede generar cursos completos desde un prompt o documentos.

Incluye:

- estructura;
- lecciones;
- quizzes;
- videos;
- escenarios;
- tutor IA;
- LMS.

### Diferencia

Orientación principal hacia creación/entrega de cursos y training.

Learning Manager está pensado desde el alumno:

> “quiero alcanzar esta meta; organiza tú el proceso”.

---

## 19.8 StudyFetch

StudyFetch parte principalmente de materiales del curso.

Ofrece:

- notas;
- flashcards;
- quizzes;
- study plans;
- tutor;
- práctica basada en los archivos proporcionados.

### Diferencia

Learning Manager puede comenzar desde una **meta sin exigir que el usuario ya posea el corpus**.

---

## 19.9 Mindgrasp

Mindgrasp transforma materiales aportados por el usuario en:

- notas;
- resúmenes;
- quizzes;
- flashcards;
- study guides;
- práctica;
- tutor IA.

También muestra progreso por sesión.

### Diferencia

Su experiencia se construye alrededor de los materiales subidos.

Learning Manager busca asumir la responsabilidad de:

```text
goal → fuentes → plan → progreso → adaptación → scheduling
```

---

## 19.10 7taps

7taps demuestra que:

- microlearning;
- entrega vía WhatsApp;
- reminders;

ya existen en herramientas comerciales.

### Consecuencia

La innovación NO puede ser:

> “enviar recordatorios por WhatsApp”.

La notificación es un canal.

La innovación debe ser que el agente decida **qué recuperar y por qué**.

---

# 20. Posicionamiento competitivo recomendado

No decir:

> “Somos un tutor con IA.”

No decir:

> “Creamos cursos con IA.”

No decir:

> “Generamos quizzes automáticamente.”

Sí decir:

> **We manage the learning journey, not just the learning content.**

Tabla conceptual:

| Categoría | Principal unidad de valor |
|---|---|
| NotebookLM | corpus / knowledge workspace |
| Gemini Study Notebook | adaptive study notebook |
| ChatGPT Study | tutoring interaction |
| Coursebox | course creation |
| StudyFetch / Mindgrasp | study materials from user content |
| DeepTutor / Cognita | agentic personalized tutoring |
| **Learning Manager** | **persistent goal-to-mastery management across time** |

---

# 21. Diseño agentic propuesto

No es necesario desplegar siete procesos LLM independientes.

Los “agentes” pueden ser roles/capabilities del mismo runtime.

## 21.1 Goal Manager

Responsable de:

- entender la meta;
- acotar alcance;
- deadline;
- disponibilidad;
- criterio de éxito.

Output:

```json
{
  "goal": "...",
  "deadline": "...",
  "daily_minutes": 20,
  "success_criteria": ["..."]
}
```

---

## 21.2 Diagnostic / Assessment capability

Responsable de:

- generar/seleccionar pruebas;
- medir conocimiento;
- detectar misconceptions;
- asignar confidence.

Debe evitar evaluar únicamente memoria superficial.

---

## 21.3 Research / Knowledge capability

Responsable de:

- obtener material;
- priorizar fuentes;
- comprobar autoridad/versión;
- producir evidencia.

Puede delegarse a KnowledgeProvider.

---

## 21.4 Curriculum Manager

Responsable de:

- construir knowledge graph;
- prerequisitos;
- prioridad;
- duración;
- sesiones;
- adaptación.

---

## 21.5 Teaching capability

Responsable de materializar la sesión utilizando el formato que mejor encaje con:

- objetivo;
- tiempo;
- learner model;
- preferencias.

Para el MVP limitar formatos.

---

## 21.6 Learner Model / Memory

No debería ser solo memoria textual.

Debe almacenar estado estructurado.

Concepto:

```text
concept
mastery
confidence
misconceptions
evidence
last_seen
last_assessed
next_review
```

---

## 21.7 Adaptive Scheduler

Responsable de:

- calcular next review;
- equilibrar material nuevo vs repaso;
- responder al deadline;
- detectar atraso;
- reprogramar.

---

# 22. MVP recomendado para la hackathon

Debido al tiempo, congelar el MVP.

## IN SCOPE

### A. Onboarding
- tema/meta;
- propósito;
- deadline;
- minutos/día;
- preferencia básica de aprendizaje.

### B. Diagnostic
- 5–10 preguntas iniciales;
- knowledge gaps.

### C. Research
- fuentes verificables;
- preferir documentación oficial cuando aplique.

### D. Initial Plan
- knowledge map;
- sesiones planificadas;
- tiempo estimado.

### E. One Micro-Lesson
- formato texto/ejemplo/ejercicio;
- no generar video/podcast en MVP.

### F. Assessment
- evaluación posterior;
- guardar resultados.

### G. Learner Model
- actualizar mastery.

### H. Adaptation
- modificar la próxima sesión basándose en el resultado.

### I. Proactive Reminder
- demostrar al menos un scheduled follow-up real o simulado reproducible.

### J. Mastery Dashboard
Mostrar:

- objetivo;
- progreso;
- áreas fuertes;
- áreas débiles;
- siguiente sesión;
- razones para la recomendación.

---

# 23. Fuera del MVP

No construir durante la hackathon salvo que el core esté completamente terminado:

- podcasts;
- vídeos generados;
- avatares;
- 3D;
- social features;
- marketplace;
- certificados;
- LMS completo;
- múltiples canales de mensajería;
- app móvil nativa;
- gamificación compleja;
- generación de infografías propia;
- un motor RAG desde cero;
- un crawler universal;
- multi-LLM router sofisticado;
- billing.

---

# 24. Preferencias de aprendizaje

Debe usarse con cuidado.

No asumir categorías rígidas tipo “visual learner” como diagnóstico científico.

Para el producto puede interpretarse como **preferencias de presentación**:

```text
preferred_formats:
- concise_text
- examples
- diagrams
- exercises
```

El comportamiento real puede pesar más que la preferencia declarada.

Ejemplo:

> El usuario afirma preferir explicación larga, pero su desempeño mejora con ejercicios breves.

El agente puede adaptar sin etiquetar permanentemente a la persona.

---

# 25. Scheduling y spaced review

Para el MVP puede utilizarse una heurística simple.

Ejemplo conceptual:

```text
mastery < 0.50  → review tomorrow
0.50–0.70       → review in 2 days
0.70–0.85       → review in 4 days
> 0.85           → review in 7 days
```

No es necesario afirmar que esto constituye un algoritmo pedagógico validado.

En el futuro puede evolucionar hacia:

- FSRS;
- SM-2;
- modelos bayesianos;
- knowledge tracing.

---

# 26. Mastery

Evitar:

> “El usuario dominó totalmente X porque obtuvo 8/10 una vez.”

Usar:

```text
mastery estimate
confidence
evidence
```

Una decisión de dominio puede requerir:

- evaluación inicial;
- recuperación posterior;
- aplicación;
- ausencia de misconception crítica.

---

# 27. Baseline recomendado

La comparación más exigente y honesta sería:

## Baseline

Una herramienta competente sin Learning Manager.

Ejemplo:

```text
Gemini Study Notebook / NotebookLM / Study Mode
```

o, si la evaluación debe ser totalmente reproducible mediante API:

```text
single LLM + grounded research prompt
```

## Solución

```text
same knowledge provider
+
goal manager
+
learner model
+
adaptive curriculum
+
scheduler
+
proactive review
```

### Regla

El baseline y la solución deberían compartir tanto como sea razonable la misma capa de conocimiento.

Así se mide la contribución del **manager**, no la diferencia entre dos modelos.

---

# 28. Evaluación propuesta

La guía de la hackathon recomienda aproximadamente 10 casos cuando sea viable.

## 28.1 Casos

Crear 10 metas cortas y reproducibles, por ejemplo:

- Docker fundamentals;
- Kubernetes basics;
- Git branching;
- SQL joins;
- REST fundamentals;
- HTTP caching;
- Python async basics;
- React state;
- TypeScript generics;
- Linux permissions.

Usar dominios donde existan fuentes oficiales.

---

## 28.2 Métrica principal candidata

### Adaptive Gap Resolution Score

Medir cuántos gaps identificados terminan:

- correctamente tratados;
- correctamente reevaluados;
- reflejados en el plan siguiente.

Alternativa más sencilla:

### Plan Adaptation Accuracy

Dado un learner state conocido, evaluar si el sistema:

- prioriza el gap correcto;
- evita contenido ya dominado;
- programa revisión apropiada.

---

## 28.3 Métricas secundarias

| Métrica | Qué mide |
|---|---|
| Human setup time | tiempo que usuario dedica a organizar |
| Source support rate | claims importantes respaldados |
| Outdated/unsupported claim rate | fiabilidad |
| Redundant content | contenido ya dominado repetido |
| Gap detection recall | debilidades detectadas |
| Adaptation correctness | calidad de replanificación |
| Mastery calibration | relación score/confianza |
| Scheduled review relevance | relevancia de repasos |
| Cost per learning goal | costo |
| Latency | experiencia |

---

# 29. Evaluación del research/verification

Caso difícil recomendado:

> Tema con documentación que ha cambiado entre versiones.

Dataset:

- fuente oficial actual;
- artículo antiguo;
- tutorial desactualizado;
- post de foro;
- documentación secundaria.

Baseline:

```text
simple research
```

Final:

```text
research
 ↓
authority
 ↓
version/date
 ↓
cross-check
 ↓
selected sources
```

Evaluar:

- claims correctos;
- claims desactualizados;
- trazabilidad.

---

# 30. Evaluación de adaptación

Crear learner states sintéticos.

Ejemplo:

```json
{
  "pods": 0.9,
  "deployments": 0.8,
  "services": 0.3,
  "ingress": 0.0
}
```

Objetivo:

> elegir la siguiente sesión.

Respuesta esperada:

- no repetir Pods;
- reforzar Services;
- evitar Ingress si Services es prerequisito;
- mantener deadline.

Esto permite evaluar el agente sin esperar semanas de aprendizaje real.

---

# 31. Pre-test / post-test

Puede usarse como evidencia secundaria.

Ejemplo:

```text
PRE   4/10
POST  8/10
```

Pero no debe afirmarse que una prueba corta demuestra científicamente superioridad pedagógica.

El objetivo de la hackathon es demostrar que el **workflow** mejoró.

---

# 32. Improvement Changelog sugerido

## Baseline
Prompt directo / Study tool.

Problema observado:

- contenido genérico;
- no mantiene learner state;
- no sabe cuándo volver;
- repite material.

## Iteration 1 — Structured learner state
Añadir knowledge state estructurado.

Medir:

- mejor selección del siguiente concepto.

## Iteration 2 — Verification
Añadir source/date/version checking.

Medir:

- reducción de unsupported/outdated claims.

## Iteration 3 — Adaptive scheduler
Añadir next-review logic.

Medir:

- mayor relevancia de repasos.

## Iteration 4 — Proactive retrieval
Notificación con una pregunta derivada del weakness concreto.

Medir:

- si el resultado actualiza correctamente el learner state.

## Final
Combinar solo cambios que produjeron mejora.

---

# 33. Posibles “hot takes”

No fijar uno hasta observar los experimentos.

Candidatos:

> **Generating educational content was easy. Deciding what the learner should not study was the hard part.**

> **The useful memory wasn’t chat history; it was a structured model of what the learner could actually demonstrate.**

> **The best reminder wasn’t “study now”; it was a retrieval question selected from the learner’s weakest evidence.**

> **The knowledge model mattered less than the scheduling decision about when to ask again.**

Debe seleccionarse el que realmente esté respaldado por las pruebas.

---

# 34. Riesgos

## 34.1 Google feature overlap

Gemini Study Notebooks ya ocupan una parte grande de:

```text
goal → diagnostic → personalized lessons → quiz → progress → adapt
```

### Mitigación
Priorizar:

- temporal management;
- deadline;
- proactive review;
- external knowledge providers;
- structured learner state;
- explicit mastery evidence.

---

## 34.2 Competidores agent-native

DeepTutor y Cognita reducen la novedad de:

- multi-agent tutoring;
- persistent memory;
- plan/teach/assess/adapt.

### Mitigación
No presentar esos elementos como novedad individual.

Presentar el valor sistémico:

> persistent goal-to-mastery management.

---

## 34.3 Dependencia NotebookLM MCP

### Riesgos
- APIs internas;
- cookies;
- breaking changes;
- TOS;
- reproducibilidad.

### Mitigación
Provider abstraction + fallback.

---

## 34.4 Scope explosion

Es fácil intentar crear:

- tutor;
- LMS;
- RAG;
- app;
- scheduler;
- videos;
- quizzes;
- research engine.

### Mitigación
MVP congelado.

---

## 34.5 Evaluación pedagógica difícil

Aprendizaje real es longitudinal.

### Mitigación
Evaluar técnicamente:

- research;
- gap detection;
- adaptation;
- scheduling;
- reproducibility;

y tratar pre/post como evidencia complementaria.

---

## 34.6 Hallucination

### Mitigación
- grounding;
- sources;
- source selection;
- claim verification;
- confidence;
- evitar dominios de alto impacto en demo.

---

# 35. Privacidad

El sistema podría almacenar:

- objetivos;
- desempeño;
- gaps;
- historial;
- preferencias.

Principios:

- recopilar lo mínimo;
- permitir borrado;
- separar datos de autenticación;
- no publicar learner states en submission;
- usar casos sintéticos/autorizados en evaluación.

---

# 36. Arquitectura conceptual mínima

```text
┌────────────────────────────────────┐
│              CLIENT                │
│ web                                │
└────────────────┬───────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│        LEARNING ORCHESTRATOR       │
│                                    │
│ Goal Manager                       │
│ Curriculum Manager                 │
│ Assessment                         │
│ Scheduler                          │
└───────┬─────────────────┬──────────┘
        │                 │
        ▼                 ▼
┌───────────────┐   ┌────────────────┐
│ Learner State │   │KnowledgeProvider│
│ DB            │   │ interface       │
└───────────────┘   └───────┬────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
         Notebook/Gemini          fallback provider

                 │
                 ▼
        Notification / task
```

---

# 37. Modelo de datos inicial

## User

```text
id
timezone
preferred_language
```

## LearningGoal

```text
id
user_id
title
purpose
deadline
daily_minutes
status
success_criteria
```

## Concept

```text
id
goal_id
name
prerequisites[]
importance
```

## LearnerConceptState

```text
concept_id
mastery
confidence
last_seen
last_assessed
next_review
misconceptions[]
```

## AssessmentAttempt

```text
id
concept_id
questions
answers
score
evidence
created_at
```

## Session

```text
id
goal_id
planned_minutes
concepts[]
status
```

## Source

```text
id
url
title
authority_type
version
published_at
retrieved_at
```

---

# 38. Estados del concepto

Propuesta simple:

```text
UNSEEN
INTRODUCED
WEAK
DEVELOPING
MASTERED
REVIEW_DUE
```

No hace falta ML complejo para el MVP.

---

# 39. Herramientas / modelo

La aplicación debería evitar quedar atada a un único proveedor.

Conceptualmente:

```text
LLMProvider
KnowledgeProvider
NotificationProvider
```

El LLM puede ser intercambiable.

El éxito no debe depender de que el usuario posea el mismo plan de NotebookLM que el desarrollador, salvo que eso quede documentado expresamente.

---

# 40. Diseño de la primera experiencia

Pantalla 1:

```text
What do you want to learn?
[ Kubernetes                                  ]

Why?
[ prepare for a technical interview           ]

How much time can you spend?
[ 25 ] minutes/day

Deadline
[ 3 weeks ]

I learn better with
[x] examples
[x] practice
[ ] long reading
[x] diagrams

[ Build my learning journey ]
```

Después:

```text
First, let's see what you already know.
```

Diagnostic.

Resultado:

```text
Goal readiness

Containers      strong
Images          medium
Networking      weak
Security        unseen

Estimated path: 17 sessions
25 min/day
Projected completion: Sep 18
Deadline: Sep 20
```

---

# 41. Pantalla diaria

```text
TODAY — 22 minutes

Why this lesson?
You understand Pods, but yesterday's
assessment showed confusion between
ClusterIP and NodePort.

1. Concept       6 min
2. Worked example 5 min
3. Practice      7 min
4. Retrieval     4 min

[ Start ]
```

La explicación de **por qué** fue seleccionada la sesión refuerza la percepción de agentic adaptation.

---

# 42. Dashboard

```text
GOAL
Kubernetes interview readiness

Progress          61%
On track          YES
Deadline          Sep 20

Strong
✓ Pods
✓ Deployments

Needs work
! Services
! Networking

Next review
Services — tomorrow

Why?
2 incorrect retrieval attempts
```

---

# 43. Notificaciones

Para el MVP puede bastar una notificación programada.

Formato:

```text
Quick review — 90 seconds

Yesterday you mixed up ClusterIP and NodePort.

Which service type is reachable only from
inside the cluster?

[A] ClusterIP
[B] NodePort
[C] LoadBalancer
```

La respuesta debe quedar registrada.

---

# 44. Human-in-the-loop

El usuario mantiene control.

Debe poder:

- cambiar disponibilidad;
- pausar goal;
- rechazar recomendación;
- marcar una sesión como no adecuada;
- revisar las fuentes;
- pedir explicación alternativa.

No permitir al agente cambiar un objetivo importante de forma silenciosa.

---

# 45. Reproducibilidad para la hackathon

Debe existir un modo demo sin depender de esperar días.

Ejemplo:

```env
SCHEDULER_MODE=simulation
```

Permitir:

```text
simulate_day(1)
simulate_day(2)
```

Así un juez puede reproducir:

```text
diagnostic
→ lesson
→ assessment
→ adaptation
→ review due
→ proactive prompt
```

en minutos.

En producción se sustituye por scheduling real.

---

# 46. Trayectorias que deben guardarse

Guardar una trayectoria representativa por capability/agente.

Ejemplo:

```text
Goal input
 ↓
Goal Manager output
 ↓
Diagnostic generation
 ↓
answers
 ↓
Learner State update
 ↓
Research tool
 ↓
sources
 ↓
Curriculum decision
 ↓
lesson
 ↓
assessment
 ↓
state update
 ↓
schedule decision
```

Incluir:

- prompts/instrucciones;
- tool calls;
- output;
- validation;
- retries;
- decisiones.

---

# 47. Failure modes que conviene probar

1. usuario ya sabe gran parte del tema;
2. deadline irreal;
3. fuentes contradictorias;
4. fuentes desactualizadas;
5. usuario falla dos veces el mismo concepto;
6. usuario supera un concepto antes de lo esperado;
7. disponibilidad cambia;
8. evaluación ambigua;
9. provider falla;
10. scheduler propone demasiados repasos.

---

# 48. Criterios de éxito del MVP

El MVP se considera completo si puede demostrar de forma reproducible:

```text
1. Goal intake
2. Diagnostic
3. Verified source acquisition
4. Initial curriculum
5. One lesson
6. Assessment
7. Learner-state update
8. Curriculum adaptation
9. Scheduled/proactive review
10. Reassessment
```

No es necesario que el usuario haya estudiado tres semanas reales.

---

# 49. Criterio de diferenciación

Antes de añadir una función preguntar:

> ¿Esto ya lo hace NotebookLM/Gemini/ChatGPT?

Si sí:

> ¿Learning Manager necesita construirlo o únicamente consumirlo como tool?

Priorizar únicamente funciones que refuercen:

```text
goal ownership
learner state
longitudinal adaptation
scheduling
proactivity
mastery evidence
```

---

# 50. Decisiones pendientes antes del plan

Estas preguntas deben resolverse en la siguiente fase:

1. **Stack frontend/backend.**
2. **KnowledgeProvider principal del MVP.**
3. **Si NotebookLM se usa mediante integración oficial, MCP experimental o se deja como provider futuro.**
4. **LLM principal.**
5. **Persistencia: SQLite/Postgres/etc.**
6. **Canal de notificación del demo.**
7. **Dominio exacto de los 10 casos de evaluación.**
8. **Métrica principal definitiva.**
9. **Rúbrica para adaptación correcta.**
10. **Algoritmo simple de scheduling.**
11. **Cómo visualizar mastery/confidence.**
12. **Qué capacidades se implementan como agentes separados vs tools del mismo runtime.**

---

# 51. Decisiones que deberían considerarse congeladas

Salvo evidencia nueva:

- no reconstruir NotebookLM;
- no competir por cantidad de formatos;
- no hacer video/podcast en MVP;
- no presentar reminders genéricos como innovación;
- no presentar “multi-agent tutor” como diferenciación;
- mantener provider abstraction;
- learner model estructurado;
- demo goal-to-mastery;
- evaluación reproducible;
- adaptación entre sesiones como núcleo.

---

# 52. Plan posterior a este documento

El siguiente documento debería ser un **Implementation Plan**, no otra lluvia de ideas.

Orden sugerido:

```text
1. Freeze scope
2. Choose stack
3. Define data model
4. Define agent contracts
5. Define provider interfaces
6. Freeze evaluation dataset
7. Build baseline
8. Build end-to-end happy path
9. Add verification/adaptation
10. Run evaluation
11. Improvement changelog
12. Reproduction guide
13. Video
```

---

# 53. Referencias verificadas

Las referencias siguientes se utilizaron para actualizar el estado competitivo y técnico al 2026-08-30.

## micro1
- **Agentic Workflows Hackathon** — PDF oficial proporcionado en la conversación.

## Google / NotebookLM / Gemini
- NotebookLM Discover Sources:  
  https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-discover-sources/
- NotebookLM — agregar/descubrir fuentes:  
  https://support.google.com/notebooklm/answer/16215270
- Gemini Study Notebooks:  
  https://blog.google/innovation-and-ai/products/gemini-app/gemini-study-notebooks/
- Gemini Study Notebooks — ayuda:  
  https://support.google.com/gemini/answer/16972047
- Google Learn About:  
  https://support.google.com/websearch/answer/15662709
- Gemini Notebook Enterprise API — notebooks:  
  https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks
- Gemini Notebook Enterprise API — sources:  
  https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources

## OpenAI
- ChatGPT Study Mode:  
  https://help.openai.com/en/articles/11780217

## Agentic learning
- DeepTutor:  
  https://github.com/HKUDS/DeepTutor
- Project Cognita:  
  https://www.ilmai.co.uk/research/cognita-multi-agent-cognitive-orchestration

## Study/course products
- Coursebox:  
  https://www.coursebox.ai/
- StudyFetch:  
  https://www.studyfetch.com/
- Mindgrasp:  
  https://www.mindgrasp.ai/ai-study-tools
- 7taps WhatsApp microlearning:  
  https://help.7taps.com/en/articles/13008518-share-via-whatsapp-send-microlearning-directly-to-learners-phones

## NotebookLM MCP — ejemplo comunitario / riesgo
- Ejemplo que declara uso de APIs internas y cookies:  
  https://github.com/ran-ai-agency/Notebooklm-mcp

---

# 54. Nota final

Este archivo representa **la definición actual del proyecto**, no una promesa de implementar todas las funciones mencionadas.

El proyecto de hackathon debe seleccionar el mínimo subconjunto que pruebe la tesis:

> **Un agente que mantiene un learner model y gestiona proactivamente el recorrido hacia una meta puede aportar valor por encima de una herramienta que solamente genera o presenta contenido educativo.**

El siguiente paso es convertir esta especificación en un plan técnico con tareas priorizadas por tiempo, riesgo y puntaje de la hackathon.
