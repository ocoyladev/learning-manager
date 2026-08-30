# micro1 Agentic Workflows Hackathon — Guía consolidada

> **Documento de trabajo**
>
> Fuente primaria: PDF oficial **“Agentic Workflows Hackathon”** proporcionado en la conversación (10 páginas).
>
> Fecha de consolidación: **2026-08-30**
>
> Este archivo resume y organiza las bases de la hackathon para usarlas como referencia durante el diseño, implementación, evaluación y presentación. Cuando este documento añade recomendaciones prácticas, se marcan como **Interpretación / recomendación**, para distinguirlas de las reglas del PDF.

---

## 1. Propósito de la hackathon

La hackathon pide elegir **un problema específico, significativo y entendido por el participante**, y utilizar agentes para crear una solución que una persona real consideraría útil.

La propuesta no debe justificarse por “usar IA” o “usar muchos agentes”. Debe demostrar que:

1. existe un usuario real con un problema concreto;
2. existe un cuello de botella que vale la pena resolver;
3. el agente resuelve ese problema de manera fiable;
4. otra persona puede reproducir el resultado.

La guía enfatiza la utilidad práctica: el objetivo es construir **“something people would genuinely find useful”** y mostrar evidencia de que la solución mejora la forma en que actualmente se realiza la tarea.

---

## 2. Las cuatro preguntas centrales

Todo el proyecto debe poder responder con claridad:

### 2.1 Who has this problem?
¿Quién experimenta el problema?

Debe definirse un usuario concreto. Evitar segmentos excesivamente amplios como “todo el mundo” si no existe una necesidad y contexto claramente delimitados.

### 2.2 What bottleneck makes it worth solving?
¿Cuál es el cuello de botella?

Debe explicarse:

- qué hace hoy el usuario;
- qué parte consume tiempo, dinero o esfuerzo;
- qué errores aparecen;
- por qué vale la pena cambiar el proceso.

### 2.3 Does the agent solve it well?
¿El agente realmente mejora la tarea?

No basta con que el prototipo “funcione”. Debe existir evidencia que permita comparar el resultado con un baseline razonable.

### 2.4 Can another person reproduce the result?
¿Puede otra persona reproducir el resultado?

Un tercero debería poder partir de un entorno limpio y:

- instalar el proyecto;
- ejecutar el baseline;
- ejecutar la solución agentic;
- utilizar los datos/casos de prueba;
- obtener resultados comparables.

---

## 3. Cómo pueden ayudar los agentes

La guía permite utilizar las capacidades que realmente mejoren la solución.

Ejemplos mencionados:

- mejor contexto;
- mejores herramientas;
- memoria;
- verificación;
- skills especializadas;
- orquestación entre varios agentes.

### Principio esencial

> **Purposeful choices matter more than the number of components.**

No se premia la cantidad de agentes. Se premia que cada decisión tenga una razón y produzca una mejora demostrable.

### Implicación práctica

Una arquitectura con un agente y varias herramientas puede ser mejor que una arquitectura con seis agentes si:

- es más fiable;
- es más simple;
- es más reproducible;
- obtiene mejores resultados.

---

# 4. Baseline obligatorio

La solución debe compararse con una forma básica y razonable de resolver la misma tarea.

La guía propone como posibles baselines:

- un único prompt con instrucciones básicas;
- un agente generalista con herramientas básicas;
- un script o plantilla simple;
- el proceso manual utilizado actualmente.

## 4.1 Reglas para una comparación justa

El baseline y la solución final deben:

- recibir la misma tarea;
- utilizar los mismos casos de evaluación;
- evaluarse con el mismo criterio;
- documentar diferencias importantes en los recursos disponibles.

## 4.2 Qué debe demostrar el baseline

El baseline establece el punto de partida.

Ejemplo genérico:

```text
BASELINE

Input
  ↓
LLM con un prompt directo
  ↓
Resultado
```

versus:

```text
FINAL

Input
  ↓
Agent / planner
  ↓
herramientas
  ↓
verificación
  ↓
corrección
  ↓
resultado
```

La comparación final debe demostrar **cuánto mejoró el resultado total**.

---

# 5. Improvement Changelog

Además de la comparación baseline/final, debe existir un **changelog de mejora**.

Su función es contar la historia de cómo evolucionó el proyecto.

Cada experimento importante debería indicar:

1. qué se intentó;
2. por qué se intentó;
3. qué resultado produjo;
4. qué decisión se tomó después;
5. si se mantuvo, modificó o eliminó.

La guía pide incluir también experimentos que finalmente se quitaron, explicando qué enseñaron.

## 5.1 Estructura sugerida

| Stage | What you tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Enfoque inicial | Resultado baseline | Punto de partida |
| Iteration 1 | Cambio para resolver problema X | Nuevo resultado | Mantener/revisar/eliminar |
| Iteration 2 | Añadir verificación tras fallo Y | Nuevo resultado | Mantener/revisar/eliminar |
| Iteration 3 | Cambiar orquestación | Nuevo resultado | Aprendizaje |
| Final | Combinar lo que funcionó | Resultado final | Contribución principal |

## 5.2 Interpretación / recomendación

Guardar los resultados desde el principio.

Por cada iteración conviene registrar:

```text
/experiments
  baseline.json
  iteration-01.json
  iteration-02.json
  final.json
```

Y no reconstruir el changelog de memoria el último día.

---

# 6. Cómo evaluar la solución

La guía pide escoger **una métrica principal** que represente el éxito desde la perspectiva del usuario.

Ejemplos oficiales:

- desarrolladores: tests que pasan;
- operaciones: tiempo ahorrado o reducción de costos;
- forecasting: calibración.

## 6.1 Definir éxito antes de ejecutar

Antes de evaluar hay que decidir:

> ¿Qué significa un buen resultado final para el usuario?

Evitar cambiar la métrica después de ver los resultados.

## 6.2 Mismos casos

Usar los mismos casos para:

- baseline;
- solución agentic.

La guía indica que **10 o más casos es un buen objetivo cuando la naturaleza de la tarea lo permite**.

Debe incluirse **al menos un caso desafiante** y explicar qué reveló.

## 6.3 Formato de referencia del PDF

| Metric | Simple baseline | Agent solution | Change |
|---|---:|---:|---:|
| Primary outcome | valor | valor | cambio |
| Human time per task | valor | valor | cambio |
| Cost per task | valor | valor | cambio |

Si este formato no encaja con el proyecto, se puede crear una rúbrica propia clara y justificable.

---

# 7. Rúbrica de evaluación — 100 puntos

## 7.1 Problem & User Value — 15 puntos

Un proyecto fuerte:

- resuelve un problema significativo;
- define claramente quién lo experimenta;
- explica por qué resolverlo genera valor.

Pregunta de control:

> **Who experiences the bottleneck and why does solving it matter?**

---

## 7.2 Agent Solution & Engineering — 30 puntos

Es la categoría con mayor peso.

Un proyecto fuerte:

- usa agentes con propósito;
- es técnicamente sólido;
- usa contexto, tools, memoria, verificación, skills u orquestación cuando aportan valor;
- justifica sus decisiones de diseño.

Pregunta de control:

> **Which design choices helped the agent solve the problem?**

### Consecuencia

Un wrapper trivial alrededor de una API puede funcionar, pero tendrá más dificultad para demostrar una contribución agentic sustancial.

---

## 7.3 End-to-End Quality — 20 puntos

La solución debe:

- ejecutar una trayectoria realista completa;
- ser autocontenida;
- producir un resultado realmente utilizable;
- tener acabado suficiente para que una persona pondría su nombre en él.

La guía contrasta esto con entregar un borrador que obviamente parezca contenido generado sin revisión.

Pregunta de control:

> **Would the intended user consider this output high quality?**

---

## 7.4 Measured Improvement — 15 puntos

Debe demostrarse:

- mejora frente a baseline;
- comparación justa;
- evidencia;
- changelog que conecte las iteraciones con esa evidencia.

Pregunta de control:

> **Which changes truly improved the outcome?**

---

## 7.5 Reproducibility — 15 puntos

Un proyecto fuerte permite a otra persona:

- ejecutar baseline y solución;
- partir de un entorno limpio;
- seguir instrucciones claras;
- alcanzar el resultado principal.

Pregunta de control:

> **Could they do it from a clean environment?**

---

## 7.6 Hot Take / Insights — 5 puntos

Se valora una observación útil surgida de fallos reales.

No debe ser una frase genérica sobre IA.

Debe convertir un failure mode observado en una lección práctica para construir agentes más fiables.

Pregunta de control:

> **What did you learn and how would it change what you build next?**

---

# 8. Ground Rules

Las reglas base de elegibilidad indicadas en el PDF son:

1. Se pueden usar herramientas y componentes que el participante ya conozca.
2. Debe quedar claro qué existía antes de la competencia y qué se añadió durante ella.
3. Cada herramienta y componente debe usarse respetando su licencia y términos del servicio.
4. Las acciones con consecuencias deben mantenerse controladas mediante sandbox o simulación; debe existir aprobación humana antes de ejecutarlas.
5. Cuando una solución pueda afectar significativamente a alguien, debe intervenir un revisor humano cualificado.
6. El caso de uso debe ser legal y ético y tratar responsablemente a las personas y sus datos.
7. Usar información que se tenga permiso para compartir. Datos públicos o sintéticos suelen ser los más sencillos; también pueden usarse datos anónimos autorizados.
8. Mantener credenciales e información privada fuera de la submission.
9. Toda afirmación sobre resultados debe estar conectada con evidencia presentada.
10. Los jueces deben tener suficiente acceso para ejecutar el proyecto y reproducir el resultado principal.

---

# 9. Entregables finales

La guía exige cuatro elementos.

## 9.1 Complete solution code and improvement changelog

Compartir:

- proyecto completo;
- código;
- instrucciones que configuran cada agente;
- README.

El README debe:

- presentar al usuario;
- explicar el cuello de botella;
- explicar el valor de resolverlo;
- incluir un **Improvement Changelog** claramente identificado;
- incluir cada iteración significativa;
- conectar cada cambio con evidencia;
- terminar con:
  - principal failure mode;
  - hot take / insight.

---

## 9.2 Reproduction guide

Debe estar escrito para una persona que parte de un entorno limpio.

Incluir:

- configuración;
- dependencias;
- versiones relevantes;
- comandos exactos;
- cómo ejecutar la solución;
- cómo ejecutar el baseline;
- cómo ejecutar la evaluación;
- datos necesarios;
- output esperado;
- runtime aproximado;
- costo aproximado.

---

## 9.3 Solution video

Duración máxima indicada: **5 minutos**.

Debe mostrar:

1. problema;
2. baseline simple;
3. una ejecución realista completa de inicio a fin;
4. resultado final;
5. comparación baseline/final;
6. changelog resumido;
7. cambio que más contribuyó;
8. un experimento que fue eliminado.

### Interpretación / recomendación

Estructura posible:

```text
0:00–0:30  Problema y usuario
0:30–0:55  Baseline
0:55–2:45  Demo end-to-end
2:45–3:30  Arquitectura agentic
3:30–4:20  Evaluación y resultados
4:20–4:45  Changelog / experimento eliminado
4:45–5:00  Hot take + cierre
```

---

## 9.4 Agent trajectories

Hay que incluir trayectorias representativas para **cada agente utilizado**.

Cada trayectoria debería permitir seguir:

- instrucciones del agente;
- acciones;
- herramientas invocadas;
- respuestas de las herramientas;
- feedback;
- retries;
- checkpoints humanos;
- resultado final.

---

# 10. Ejemplos de referencia incluidos en las bases

El PDF incluye tres ejemplos. No son requisitos de temática; sirven para mostrar cómo formular el problema y la evaluación.

---

## 10.1 Code analysis: “Is this repository actually good?”

### Usuario
Equipo que evalúa comprar un repositorio privado y necesita estimar la calidad real del código.

### Cuello de botella
README y demo no revelan suficientemente:

- arquitectura;
- tests;
- dependencias;
- deuda técnica;
- mantenimiento;
- PRs;
- issues.

Sin método repetible, dos evaluadores pueden llegar a conclusiones distintas.

### Posible solución agentic
Analizar repositorio y producir una evaluación de calidad basada en evidencia.

### Evaluación
Revisores cualificados ordenan 10 repositorios usando una rúbrica compartida.

Luego:

- baseline;
- agente;

analizan los mismos repositorios.

Se mide qué tan cerca están de los revisores y si justifican cada posición con evidencia.

### Reproducibilidad
Usar repositorios autorizados y documentar:

- setup;
- comandos;
- versiones;
- output.

Cada score debe poder rastrearse a archivos, tests o build outputs.

---

## 10.2 Candidate evaluation: “Should we hire this person?”

### Usuario
Recruiters y hiring managers.

### Cuello de botella
La evidencia está repartida entre:

- job description;
- perfil esperado;
- CV;
- entrevistas;
- evaluaciones.

Puede haber contradicciones o señales sobrerrepresentadas.

### Posible solución
Agente que:

- conecta requisitos con evidencia;
- revisa experiencia declarada;
- señala discrepancias;
- explicita incertidumbre.

La decisión final debe permanecer en un revisor humano cualificado.

### Evaluación
Casos de candidatos sintéticos o autorizados, incluyendo uno con señales conflictivas.

---

## 10.3 Podcast translation: “Can every version still feel like the same show?”

### Usuario
Creadores/equipos de podcasts multilingües.

### Cuello de botella
El contexto se extiende entre:

- horas de audio;
- múltiples hablantes;
- episodios anteriores;
- elecciones de traducción.

Un episodio puede ser correcto aisladamente y aun así romper la coherencia de la serie.

### Posible solución
Traducción consistente en:

- nombres;
- pronunciación;
- términos recurrentes;
- tono;
- referencias previas.

### Evaluación
Mismos episodios y lenguajes para baseline/agente, incluyendo un caso que dependa de información recurrente.

Las elecciones deben poder rastrearse a la fuente.

---

# 11. Checklist de diseño antes de programar

## Problema
- [ ] Usuario específico definido.
- [ ] Cuello de botella actual descrito.
- [ ] Valor cuantificable identificado.
- [ ] Proceso actual documentado.

## Agentic
- [ ] Cada agente/tool tiene un propósito explícito.
- [ ] Se evitó crear agentes redundantes.
- [ ] El estado/memoria está claramente definido.
- [ ] Se definieron checkpoints humanos.
- [ ] Se definieron failure modes y retries.

## Baseline
- [ ] Baseline congelado antes de optimizar.
- [ ] Usa los mismos inputs que la solución.
- [ ] Tiene recursos comparables o se explican diferencias.

## Evaluación
- [ ] Métrica principal definida.
- [ ] Métricas secundarias definidas.
- [ ] Casos de evaluación congelados.
- [ ] Caso difícil incluido.
- [ ] Se registra tiempo humano.
- [ ] Se registra costo.
- [ ] Se guardan outputs.

## Reproducibilidad
- [ ] `.env.example`.
- [ ] README desde entorno limpio.
- [ ] versiones fijadas.
- [ ] dataset/casos permitidos.
- [ ] comandos baseline/final/evaluation.
- [ ] credenciales excluidas.

## Submission
- [ ] Código completo.
- [ ] Improvement Changelog.
- [ ] Reproduction Guide.
- [ ] Vídeo ≤5 min.
- [ ] Agent trajectories.
- [ ] Failure mode principal.
- [ ] Hot take.
- [ ] Evidencia de todas las afirmaciones.

---

# 12. Estrategia recomendada para maximizar la rúbrica

> Esta sección es interpretación práctica, no texto oficial.

Prioridad de ingeniería:

```text
1. Trayectoria end-to-end funcional
2. Baseline reproducible
3. Evaluación automatizable
4. Verificación / reliability loop
5. Changelog con evidencia
6. UX suficiente para demo
7. Funciones adicionales
```

Debido a la ponderación:

```text
Agent Engineering       30
End-to-End Quality      20
Problem & Value         15
Measured Improvement    15
Reproducibility         15
Hot Take                 5
                       ----
                        100
```

Un proyecto pequeño pero completo, evaluado y reproducible puede ser más competitivo que un producto enorme parcialmente terminado.

---

# 13. Qué NO está definido en el PDF proporcionado

El documento adjunto no aporta en las páginas analizadas:

- fecha/hora exacta de cierre de la competencia;
- URL concreta de submission;
- premios;
- formato de repositorio obligatorio;
- proveedor LLM obligatorio;
- framework obligatorio;
- número mínimo de agentes.

Si cualquiera de esos puntos resulta necesario para la entrega, debe verificarse en el portal oficial de la hackathon y no inferirse a partir de este documento.

---

# 14. Fuente primaria

**micro1 — Agentic Workflows Hackathon**, PDF proporcionado por el usuario, 10 páginas.

Este archivo debe mantenerse como referencia de requisitos. Las decisiones específicas de nuestro producto se documentan separadamente en `02_learning_manager_especificacion.md`.
