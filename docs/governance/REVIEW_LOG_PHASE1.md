# REVIEW_LOG_PHASE1.md — Registro de ejecución y revisión de la Fase 1 (gobernanza documental)

**Fecha:** 2026-11-25 · Rama `docs/governance-roadmap`, base `origin/main` `7583ca5`. Despachos vía Orca; modelo/esfuerzo **solicitados** según el recibo de Orca. Identidad efectiva: argv del proceso no obtenible durante la ejecución (solo recibo de Orca); el autoinforme de los modelos no cuenta como evidencia.

| Trabajo | Ejecutor | Revisor (proveedor contrario) | HEAD revisado | Resultado |
|---|---|---|---|---|
| Reconciliación documental, roadmap, fuentes importadas | Claude Sonnet 5.5 (coordinador) | Codex `gpt-6.2-sol` · medium | `7702e89` → `60e8e9b` | Ronda 1: CHANGES_REQUESTED (B1–B11, A1–A7). Ronda 2 (última ordinaria): resueltos B1, B3, B7, B9, A5, A7; parciales B2, B4, B5, B6, B10, B11, A1–A4, A6; B8 pendiente de decisión del propietario. Los residuos baratos se corrigieron después en `21edbf0` **sin tercera ronda**: quedan registrados abajo |
| `sync_docs.py`, `check_docs.py`, tests, job CI | Codex `gpt-6.2-sol` · medium | Claude Sonnet 5.5 · high | `7702e89` → `60e8e9b` → `21edbf0` | Ronda 1 APPROVED (0 B, 7 A); ronda 2 APPROVED (A4 parcial); corrección HG-MVP0-PUBLISH verificada APPROVED |

## Evidencia ejecutada (local, no es GitHub Actions)
`python scripts/governance/sync_docs.py --check` = 0; `python scripts/governance/check_docs.py` = OK; `python -m unittest tests.governance.test_governance` = 36 tests OK; comprobación de enlaces y anclas relativos de los Markdown tocados = 0 rotos. Mutaciones del revisor (~110 casos sobre copias): todas fallan con el ID afectado. **Pendiente:** ejecución real del job `governance` en GitHub Actions (no hay PR publicado).

## Residuos conocidos tras la ronda 2 (no se declaran resueltos)
- **B8:** `docs/design/DESIGN_DISCOVERY_A_B_C.md` conserva una ruta absoluta local del original (línea 21); decisión del propietario.
- **A4:** `F10.tasks` lista MP-016…022 aunque su fase de tarea es H3; no hay regla de coherencia fase↔tarea.
- **A6:** fechas de aprobación `UNKNOWN` en varias tareas (no se inventan).
- **Independencia visual de Design A/B/C:** sin navegador para Codex, la verificación visual la ejecuta Claude (override); queda abierta.
- Las correcciones posteriores a la ronda 2 (B2, B4, B5, B6, B10, B11, A1–A3, A6) **no fueron re-verificadas por Codex**; solo lo fue el cambio de script por Claude.

## Cierre acotado de la Fase 1 (2026-11-25) — autorización y verificación excepcional
**Autorización del propietario (2026-11-25):** push de `docs/governance-roadmap` y PR **en borrador** contra `main`. **No** autoriza merge, despliegue, contratación ni el Prompt 02. Autoriza además **una verificación excepcional y focalizada** de los hallazgos documentales pendientes de la ronda 2 y de sus correcciones posteriores, por Codex `gpt-6.2-sol` · medium. No es una tercera auditoría general. Esta instrucción **no** implica aceptar F9/H2 ni `HG-AUDIT-DECISION`; `UNKNOWN` se mantiene donde no hay evidencia.

**Cambios previos a la verificación:** F10 asigna ahora MP-016…MP-022 (`phase: F10`); aclaración «cierre histórico ≠ preparado para release» (MILESTONES, UPDATE_PROTOCOL); MP-030 ↔ demo: sin dependencia técnica, solo solape de archivos (`coordination` en `PROJECT_STATE.json`); aclaración sobre la ruta histórica del original de Design en el override.

### Resultado de la verificación excepcional (Codex `gpt-6.2-sol` · medium, solicitado vía Orca; argv no verificable)
**HEAD revisado: `5d7a9a1`.** Dictamen: **CHANGES_REQUESTED** (no hay `APPROVED`). Por ID (hallazgo original → corrección → resultado):

| ID | Resultado de la verificación |
|---|---|
| B2 (checklist obsoleto; MP-030 tras D-06) | RESUELTO |
| B4 (excepción BLOCKED de MP-035) | RESUELTO |
| B5 (Gate 0 preview vs URL pública) | PARCIAL: el estado canónico seguía describiendo Gate 0 en un solo tiempo |
| B5 descubrimiento (gate MVP0 por identidad) | RESUELTO (reproducción independiente) |
| B6 (F9 CLOSED sin aceptación; F1) | PARCIAL: `docs/PLAN.md` aún decía F9 cerrada |
| B8 (ruta local del original) | RESUELTO (excepción aceptada por el propietario; original íntegro por `cmp`) |
| B10 (CI/merge; `content_in_main`; enlace al override) | PARCIAL: §8 limitaba MERGED al merge real; cabecera de Design sin enlace y con «excepción pendiente» |
| B11 (ARCHITECTURE) | RESUELTO |
| A1, A2, A4 | RESUELTO |
| A3 | PARCIAL: «16 P1 abiertos» en la nota de AUD-09 |
| A6 | PARCIAL + **descubrimiento material nuevo**: la nota de MP-026a llamaba «aprobada por el propietario» a la matriz H4, que es PROPUESTA (HG-H4-SCOPE abierto) |
| Cierres históricos vs release | RESUELTO |

**Correcciones posteriores (commit siguiente), NO re-verificadas por Codex** (la autorización cubría una sola verificación): estado canónico con Gate 0 en dos tiempos; PLAN con F9 abierta; §8 con `integration_kind`; cabecera de Design con enlace relativo y la excepción de la ruta marcada como aceptada; «16 P1 registrados»; nota de MP-026a con la matriz como PROPUESTA y precedencia provisional. Verificación solo local: sync/check/36 tests y `cmp` del original.
