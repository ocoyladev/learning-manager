# Fase 4 — Informe de corrección, ronda 5

Base revisada: `370da26`.

## Cambios y evidencia

| Requisito | Implementación | Prueba de aceptación |
|---|---|---|
| Researcher usa LLM con `KnowledgeProvider` inyectado | `packages/core/learning_manager/agents/researcher.py` conserva ambos proveedores, registra `provider_retrieval`, usa `complete_json` con `SourceSelection` tipado y filtra por IDs de las fuentes recibidas. | `test_researcher_uses_the_llm_to_filter_provider_sources_without_inventing_them` verifica una llamada a temperatura 0, elimina `invented` y comprueba todos los pasos de trayectoria. |
| Prompt de Researcher versionado y cargado por la ruta común | `agents/prompts/researcher.md`; el mapa de `complete_json` en `agents/_common.py` incluye `Researcher`. | `test_every_llm_backed_agent_uses_its_versioned_system_prompt` compara el prompt enviado por GoalManager, Diagnostician, Researcher, CurriculumPlanner, Assessor y Teacher contra su `.md`. |
| Ciclo persistente de GoalManager | Sin cambio de lógica: la reparación existente agota intentos y eleva `GoalPlanningError` accionable. | `test_goal_manager_reports_a_cycle_after_exhausting_repair` exige `GoalPlanningError` cuyo mensaje contiene `cycle`. |
| Planner: intento válido, reparación, `today` y rationale | Sin cambio de lógica: el planner conserva la fecha inyectada y usa `run_with_repair`. | `test_planner_accepts_valid_first_attempt_and_uses_injected_today` y `test_planner_repairs_a_prerequisite_violation_on_second_attempt`. |
| Diagnóstico con dominio completo tras respuestas correctas | Sin cambio de lógica: grading determinista calcula mastery por concepto. | `test_diagnostician_assigns_mastery_to_all_covered_concepts_for_correct_answers`. |
| Assessor: misconceptions y reparación | Sin cambio de lógica: grading mantiene misconceptions solo para fallos y generation usa repair. | `test_assessor_only_records_misconceptions_for_wrong_answers` y `test_assessor_repairs_generated_items_that_target_another_concept`. |
| Teacher seguro ante contenido/citas inválidos | Sin cambio de lógica: fallback devuelve contenido y filtra citations a las fuentes permitidas. | `test_teacher_falls_back_for_empty_content_and_unavailable_citations`. |
| Trayectorias de los cinco agentes | Researcher ahora registra recuperación, llamada, parseo y resultado final estructurado. Los otros cuatro ya usaban la ruta común/reparación. | `test_each_of_the_five_agents_records_a_call_and_final_result`. |
| Limpieza de GoalManager | Se eliminó `# ruff: noqa: E501`; el archivo sigue formateado por Ruff. | `make check` incluye `ruff check` y `ruff format --check`. |

## TDD aplicado

1. Se añadió primero `test_researcher_uses_the_llm_to_filter_provider_sources_without_inventing_them`.
2. RED confirmado: falló con `assert 0 == 1` porque Researcher no llamaba al LLM.
3. Se implementaron `SourceSelection`, el prompt versionado, la ruta `complete_json` y el filtrado duro.
4. GREEN confirmado con el test dirigido y posteriormente con toda la suite de agentes.

## Gates ejecutados

- `source .venv/bin/activate && make check`: mypy correcto, Ruff correcto, formato correcto, `106 passed, 16 skipped`.
- `git diff --check`: sin errores de whitespace.
- Diff de archivos congelados: sin cambios en `packages/core/learning_manager/contracts.py` ni `openapi.json`.
