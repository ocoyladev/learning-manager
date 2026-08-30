---
name: eval-experiment-loop
description: Ejecuta el ciclo evaluar → guardar experimento → anotar changelog del proyecto Learning Manager. Úsalo siempre que vayas a medir el efecto de un cambio, correr una iteración del changelog, o antes de afirmar cualquier cifra sobre el rendimiento del sistema.
---

# Ciclo de evidencia

Ninguna cifra sobre este proyecto se afirma sin pasar por aquí. Es el mecanismo que sostiene
45 de los 100 puntos de la rúbrica de la hackathon.

## Cuándo usarlo

- Vas a medir si un cambio mejoró algo.
- Vas a ejecutar una iteración del Improvement Changelog.
- Alguien pregunta "¿cuánto mejoró X?".
- Vas a escribir un número en el README, el changelog o el guion del vídeo.

## El ciclo

### 1. Antes de medir: declara la hipótesis

Escríbela **antes** de ejecutar, en una frase, nombrando la comprobación de NSDQ que esperas
mover:

> "Añadir el scheduler debería subir `includes_due_reviews` de 2/11 a ~11/11 y no debería
> afectar a `respects_prerequisites`."

Declarar la hipótesis primero es lo que impide racionalizar el resultado después.

### 2. Ejecuta con el nombre correcto

```bash
make eval-replay NAME=<nombre-de-la-iteracion>
```

Nombres reservados y ya congelados: `baseline`, `iteration-01`…`iteration-04`, `final`.
El runner **se niega a sobrescribir** un experimento existente. Eso es intencional: la evidencia
no se pisa en silencio. Si necesitas repetir, usa otro nombre.

Para aislar la contribución de una pieza, ábrela con su flag de ablación:
`ABLATE_VERIFIER` · `ABLATE_SCHEDULER` · `ABLATE_LEARNER_STATE` · `ABLATE_SOURCE_RANKING`.

### 3. Lee el desglose, no solo el total

El número global de NSDQ dice poco. Lo que explica *por qué* algo funcionó es
`checks` en `experiments/<nombre>.json`: qué comprobación se movió y cuánto.
Un cambio que sube el total pero baja una comprobación está escondiendo un problema.

Mira también `reliability`: `repair_rate` alto con `fallback_rate` cero significa que el bucle
de reparación está haciendo trabajo real. `fallback_rate` alto significa que el prompt del
planner es malo.

### 4. Anota en el changelog inmediatamente

Una fila en `CHANGELOG_IMPROVEMENT.md`, con:
qué probaste · por qué · la cifra **enlazada a su fichero** · la decisión (mantener / revisar /
eliminar) · qué aprendiste.

**Hazlo ahora, no al final.** Reconstruir el changelog de memoria el último día es exactamente
lo que advierte el §5.2 de las bases.

### 5. Si no mejoró, no lo borres

Un experimento que falló es evidencia igual de válida y el §5 de las bases pide explícitamente
incluir lo que se descartó y qué enseñó. Un changelog donde todo funcionó a la primera es menos
creíble, no más.

## Reglas duras

- **Nunca** modifiques un caso de `eval/cases/` ni una clave de `eval/keys/` después de haber
  visto resultados. Invalida la comparación (bases §6.1). Si una clave parece mal: para y
  pregunta al humano.
- **Nunca** escribas una cifra que no salga de un fichero de `experiments/`.
- **Nunca** cambies la métrica principal después de ver los números (bases §6.1).
- Si `make eval-replay` da resultados distintos entre dos ejecuciones, hay no determinismo:
  arréglalo antes de seguir midiendo nada.
