# Fase 14 — Evaluación, experimentos y changelog

**Pista:** ninguna (SECUENCIAL) · **Depende de:** F13 · **Duración objetivo:** 5 h · **CP5**

**Entrega:** `experiments/*.json` para cada iteración + `CHANGELOG_IMPROVEMENT.md` con evidencia.

> **Aquí se cobran los 45 puntos.** El changelog no es documentación escrita al final: es la
> evidencia de la categoría de 30 puntos ("¿qué decisiones de diseño ayudaron?") y de la de 15
> ("¿qué cambios mejoraron realmente el resultado?").
>
> **Regla:** cada iteración se ejecuta **por separado**, con un flag que desactiva la mejora, y
> se guarda su JSON. Reconstruir el changelog de memoria al final es exactamente lo que el §5.2
> de las bases advierte que no se haga.

---

## Tarea 14.1 — Flags de ablación

**Ficheros:** `learning_manager/config.py`; Test `tests/test_ablation_flags.py`

Para medir la contribución de cada pieza hay que poder **apagarla**:

```bash
ABLATE_VERIFIER=true        # sin validación de restricciones ni reparación
ABLATE_SCHEDULER=true       # sin repasos espaciados ni deadline_status calculado
ABLATE_LEARNER_STATE=true   # el planner solo ve el último resultado, no el modelo completo
ABLATE_SOURCE_RANKING=true  # fuentes en orden de descubrimiento, sin autoridad ni versión
```

- [ ] **Paso 1: test que falla**

```python
def test_ablate_verifier_disables_repair(monkeypatch) -> None:
    monkeypatch.setenv("ABLATE_VERIFIER", "true")
    _, outcome = CurriculumPlanner(fake_llm_always_bad, _rec()).next_session(...)
    assert outcome.attempts == 1 and outcome.used_fallback is False


def test_ablation_flags_default_to_false() -> None:
    assert Settings().ablate_verifier is False
```

- [ ] **Paso 2–4:** implementar y verificar
- [ ] **Paso 5: commit** → `feat(config): add ablation flags for changelog measurement`

---

## Tarea 14.2 — Ejecutar las mediciones

Se ejecutan **en este orden**. Cada una escribe su JSON y no se sobrescribe ninguna.

- [ ] **1. Baseline**

```bash
make eval-replay NAME=baseline SYSTEM=baseline
```

- [ ] **2. Iteración 1 — estado del alumno estructurado**
  Agente con learner model completo, **sin** verificador, **sin** scheduler.

```bash
ABLATE_VERIFIER=true ABLATE_SCHEDULER=true make eval-replay NAME=iteration-01
```

  *Hipótesis:* mejora `targets_correct_gap` y `no_redundant_mastery`; no mejora
  `includes_due_reviews` (aún no hay scheduler) ni `respects_prerequisites` (aún no hay
  validación).

- [ ] **3. Iteración 2 — verificación y reparación**
  Se añade el verificador.

```bash
ABLATE_SCHEDULER=true make eval-replay NAME=iteration-02
```

  *Hipótesis:* salto grande en `respects_prerequisites` y `fits_time_budget`.
  **Anota también `repair_rate`**: cuántas decisiones necesitaron reparación. Es la cifra que
  demuestra que el bucle hace algo, no que adorna.

- [ ] **4. Iteración 3 — scheduler adaptativo**

```bash
make eval-replay NAME=iteration-03
```

  *Hipótesis:* salto en `includes_due_reviews` y `deadline_status_correct`.

- [ ] **5. Iteración 4 — ranking de fuentes**
  Comparar con y sin, midiendo la métrica de fuentes.

```bash
ABLATE_SOURCE_RANKING=true make eval-replay NAME=iteration-04-ablated
make eval-replay NAME=iteration-04
```

  *Hipótesis:* baja `outdated_claim_rate`, sobre todo en el caso `nextjs-version-drift`.

- [ ] **6. Final**

```bash
make eval-replay NAME=final
```

- [ ] **Paso 7: commit de la evidencia**

```bash
git add experiments/ && git commit -m "data: record baseline, four iterations and final results"
```

> ⚠️ **Si una iteración NO mejora, no la borres.** El §5 de las bases pide explícitamente
> incluir experimentos que se descartaron y explicar qué enseñaron. Un changelog donde todo
> funcionó a la primera es menos creíble, no más.

---

## Tarea 14.3 — Baseline humano (tiempo de preparación)

> Rellena la fila "Human time per task" del formato §6.3.

- [ ] Elegir 3 de los 11 casos
- [ ] Un humano (tú) prepara a mano la siguiente sesión: revisar el learner model, decidir
      qué enseñar, buscar fuentes, redactar el bloque. **Cronometrar cada uno.**
- [ ] Registrar el procedimiento exacto y los tiempos en `experiments/human_baseline.json`
- [ ] Documentar honestamente la limitación: n=3, un solo evaluador, el evaluador conoce el
      sistema. **No sobreafirmar.** Es evidencia de apoyo, no la métrica principal
- [ ] Commit → `data: record human preparation time baseline`

---

## Tarea 14.4 — Escribir el changelog

**Ficheros:** Crear `CHANGELOG_IMPROVEMENT.md` (**en inglés**, lo leen los jueces)

Estructura del §5.1 de las bases. Una fila por etapa, cada cifra enlazada a su fichero:

```markdown
| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Single Gemini prompt, same input, same schema | NSDQ 0.51 · [baseline.json](experiments/baseline.json) | Starting point. Failed mostly on due reviews (2/11) and prerequisites (5/11) |
| Iteration 1 | Structured learner state instead of last-result-only | NSDQ 0.63 · [iteration-01.json](...) | Kept. Gap targeting 8→11, redundancy 4→9 |
| Iteration 2 | Constraint validation + repair loop | NSDQ 0.79 · repair_rate 0.31 · [iteration-02.json](...) | Kept. Prerequisites 5→11. Biggest single contribution |
| Iteration 3 | Deterministic spaced scheduler | NSDQ 0.87 · [iteration-03.json](...) | Kept. Due reviews 2→11 |
| Iteration 4 | Authority/version source ranking | outdated_claim_rate 0.22→0.03 · [iteration-04.json](...) | Kept |
| Removed | <experimento que se quitó> | <cifra> | <qué enseñó> |
| Final | Combination of what worked | NSDQ 0.87 · [final.json](...) | Main contribution |
```

- [ ] **Paso 1:** rellenar con las cifras **reales** de `experiments/`. Ni una inventada
- [ ] **Paso 2: incluir al menos un experimento eliminado.** El vídeo lo exige (§9.3 punto 8).
      Si ninguno salió mal de forma natural, el candidato honesto es la propia ablación:
      "probamos dejar que el modelo decidiera `deadline_status`; acertaba en 4/11 frente a
      11/11 con el cálculo determinista, así que lo movimos a código"
- [ ] **Paso 3: escribir el failure mode principal** — el que más veces apareció en las
      trayectorias, con el número de veces
- [ ] **Paso 4: escribir el hot take.** Candidatos del §33 de la especificación, pero **elige el
      que tus datos respalden**, no el que suene mejor. Si `repair_rate` fue alto y
      `fallback_rate` cero, el hot take es sobre la reparación. Si el mayor salto vino del
      scheduler, es sobre el scheduling
- [ ] **Paso 5: commit** → `docs: add improvement changelog with linked evidence`

---

## ✅ Criterio de salida — CP5

- [ ] 7 ficheros en `experiments/` (baseline, 4 iteraciones, ablación, final) + `human_baseline.json`
- [ ] Toda cifra del changelog enlaza a su fichero
- [ ] Al menos un experimento eliminado, documentado
- [ ] Failure mode principal identificado con su frecuencia real
- [ ] Hot take respaldado por datos, no por intuición
