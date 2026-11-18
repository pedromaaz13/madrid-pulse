# STATUS.md — Tablero vivo

> Este documento se actualiza en cada tarea. No reemplaza `docs/TASKS.md` (detalle) ni `docs/CHANGELOG.md` (historial), es el punto de entrada para saber "¿dónde estamos ahora?".

## Hito autorizado actualmente

**Ninguno todavía.** El modelo de autonomía por hito (ver [ADR-0007](adr/0007-autonomy-model.md) y DEC-014) entra en vigor a partir de MP-002. Propuesta de **Hito 1** pendiente de confirmación explícita del propietario:

```text
Hito 1 (propuesto): MP-002 → MP-009
Cobertura: F1 (factibilidad de datos) + F2 (contratos) + F3 (persistencia/colector) + F4 (calidad/histórico)
Objetivo de salida: colector idempotente validado + quality engine + histórico exportado y replayable.
Paralelismo interno: ninguno. MP-002→MP-003→MP-004→MP-005→MP-006→MP-007→MP-008→MP-009 es una
cadena estrictamente secuencial (cada tarea depende directamente de la anterior, ver docs/TASKS.md
→ "Grafo de dependencias"). El paralelismo entre worktrees (ADR-0007 punto 4) se vuelve relevante
recién en un Hito 2 que incluya MP-010/MP-011 (dependientes solo de MP-004, no de la cadena 005→009).
Gates de pausa activos durante el hito: solo decisiones de licencia o coste — DEC-002 (licencia del
código propio) y DEC-004 (retención/coste del histórico), u otras nuevas de esa naturaleza que surjan.
DEC-003 (visibilidad pública/privada del repositorio) NO es un gate de este tipo: no bloquea ninguna
tarea y puede resolverse en cualquier momento (ver docs/DECISIONS.md).
```

Mientras no se confirme, ninguna tarea posterior a MP-001 se inicia (regla 10 de `AGENTS.md`, reinterpretada por hito según ADR-0007).

## Tarea actual

**MP-001 — Bootstrap documental del repositorio**
Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **REVIEW — Codex APROBADO**, pendiente de aceptación del propietario.
Worktree/rama de la tarea: `chore/mp-001-foundation` (único worktree de MP-001, ver `AGENTS.md` → "Protocolo de coordinación en Orca"; Codex revisó en este mismo worktree, no en uno nuevo, en 4 rondas).

### Checklist de MP-001

- [x] Investigación original leída íntegramente (`deep-research-report.md`, `MADRID_PULSE_BRIEF_INICIAL.md`).
- [x] Investigación conservada íntegra y movida a `docs/research/`.
- [x] Estructura de monorepo creada (`apps/`, `services/`, `packages/`, `analytics/`, `infra/`, `tests/`, `.github/`).
- [x] `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` creados.
- [x] `docs/PLAN.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` creados.
- [x] `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/DATA_QUALITY.md`, `docs/DEVELOPMENT.md` creados.
- [x] ADRs 0001–0006 creados en `docs/adr/`.
- [x] `docs/legal/DATA_SOURCES.md`, `LICENSE_MATRIX.md`, `ATTRIBUTION.md` creados.
- [x] `docs/research/TRACEABILITY.md` creado.
- [x] Plantillas `.github/pull_request_template.md` e `ISSUE_TEMPLATE/` creadas.
- [x] Backlog MP-001 a MP-015 documentado con ejecutor/revisor/dependencias/criterios de aceptación.
- [x] Protocolo de coordinación en Orca (un worktree por tarea, delegación directa entre agentes, cierre de worktree al fusionar) incorporado en `AGENTS.md` y `CLAUDE.md`, y reflejado en `docs/PLAN.md`/`docs/TASKS.md`.
- [x] Primera revisión de Codex completada dentro de este worktree (worker Orca, dispatch `ctx_64731a94e6bc`): 1 hallazgo bloqueante + 3 menores. Ver bitácora.
- [x] Los 4 hallazgos corregidos por Claude Code en este mismo worktree (sin abrir uno nuevo).
- [x] Modelo de autonomía acotada (ADR-0007, DEC-014) incorporado a petición explícita del propietario: autorización por hito, commits de iteración en worktree, gates limitados a licencia/coste.
- [x] Primera re-verificación de Codex: **no aprobada** — 2 bloqueantes + 2 menores nuevos, todos por inconsistencia entre ADR-0007 (recién añadido) y el texto de AGENTS.md/CLAUDE.md/TASKS.md/PLAN.md/adr/README.md que no se había actualizado en consecuencia.
- [x] Los 4 nuevos hallazgos corregidos: añadida la sección "Modelo de autonomía por hito" en AGENTS.md (antes referenciada pero inexistente); reescritos los pasos 1 y 7 del protocolo de worktree, el diagrama de flujo y la regla 10 para reflejar autorización por hito + worktrees paralelos (AGENTS.md, CLAUDE.md, docs/TASKS.md, docs/PLAN.md); ADR-0007 corregido para que los ADR de arquitectura se registren como `Propuesto` (no `Aceptado`) durante la autonomía, coherente con docs/adr/README.md; quitado MP-010 del paralelismo de Hito 1 (está fuera de su rango) y quitado DEC-003 de los gates de licencia/coste (es una decisión de visibilidad, no de licencia/coste).
- [x] Segunda re-verificación de Codex: **aún no aprobada** — 1 bloqueante real (el protocolo exigía "dependencia fusionada en main" para abrir el siguiente worktree, lo que obligaba al propietario a fusionar tras cada tarea y anulaba el propósito del modelo de autonomía) + 1 menor (el "Principio rector" de docs/PLAN.md afirmaba una cadena de fases estrictamente lineal que la propia sección de dependencias ya contradecía).
- [x] Resuelto con un mecanismo de **ramas encadenadas**: el worktree de una tarea dependiente se crea a partir de la rama de su dependencia directa (no desde `main`) en cuanto esa dependencia está `DONE`; el propietario decide cuándo fusionar a `main` (en lote al cierre del hito u otro momento) sin que eso bloquee el avance. Reescrito en AGENTS.md (regla 10, sección "Modelo de autonomía por hito", pasos 1/6/7 del protocolo de worktree, diagrama de flujo), CLAUDE.md, docs/TASKS.md y docs/PLAN.md. "Principio rector" de PLAN.md corregido para no afirmar una cadena de fases estrictamente lineal.
- [x] Tercera re-verificación de Codex (dispatch `ctx_0ee25a6a5d2c`): **APROBADO, sin hallazgos bloqueantes ni menores.** 15 tareas válidas, dependencias 15/15 exactas, cero enlaces rotos, cero secretos, investigación idéntica a HEAD, ningún código/dependencia/configuración cloud. Única observación: sugerencia **no bloqueante** de documentar, antes de MP-012, cómo una tarea con varias dependencias de ramas paralelas (MP-012 = MP-008 + MP-010 + MP-011) elige rama base e integra las demás — registrada como DEC-015 en `docs/DECISIONS.md` y como nota en la ficha de MP-012 en `docs/TASKS.md`. No afecta a Hito 1 (MP-002→MP-009), que no tiene convergencias.
- [ ] Confirmación del propietario del alcance de "Hito 1" (MP-002 → MP-009, propuesto arriba).
- [ ] Aceptación final del propietario y merge de MP-001 a `main`.

### Bloqueos

Ninguno técnico ni de revisión — Codex ya aprobó. Pendiente solo de acción del propietario: (1) confirmación del rango de Hito 1, (2) push + PR + merge de MP-001 a `main`.

### Decisiones pendientes que no bloquean MP-001

Ver `docs/DECISIONS.md` — DEC-002 (licencia del código propio), DEC-003 (repo público/privado), DEC-004 (retención definitiva de histórico detallado), DEC-015 (convergencia de ramas encadenadas, solo relevante antes de MP-012). Ninguna bloquea el cierre de MP-001 según `MADRID_PULSE_BRIEF_INICIAL.md` §7.

### Siguiente tarea autorizable

**MP-002 — Matriz de fuentes y licencias** (ejecutor Codex, revisor Claude Code) — **no iniciar hasta que el propietario confirme el alcance de Hito 1** (ver arriba) y MP-001 esté `DONE` (revisor aprobó; no es necesario que ya esté fusionado en `main` — ver "Modelo de autonomía por hito" en `AGENTS.md`), conforme a la regla 10 de `AGENTS.md` reinterpretada por hito según [ADR-0007](adr/0007-autonomy-model.md).

## Bitácora

| Fecha | Tarea | Evento | Referencia |
|---|---|---|---|
| 2026-11-18 | MP-001 | Lectura íntegra de la investigación (`deep-research-report.md`, `MADRID_PULSE_BRIEF_INICIAL.md`, `README.md` original) | — |
| 2026-11-18 | MP-001 | Investigación movida a `docs/research/` preservando contenido | commit pendiente |
| 2026-11-18 | MP-001 | Estructura de monorepo y documentación de gobernanza/arquitectura/backlog creada | commit pendiente |
| 2026-11-18 | MP-001 | Protocolo de coordinación en Orca (worktree único por tarea, delegación directa agente-a-agente, cierre de worktree al fusionar) añadido a `AGENTS.md`/`CLAUDE.md` y reflejado en `docs/PLAN.md`/`docs/TASKS.md`, a petición explícita del propietario | commit pendiente |
| 2026-11-18 | MP-001 | Revisión de Codex vía worker Orca en este mismo worktree: 1 hallazgo bloqueante (contradicción de autoría en CLAUDE.md) + 3 menores (naming de rama, propiedad de analytics/dbt, ambigüedad en grafo de dependencias) | dispatch `ctx_64731a94e6bc` |
| 2026-11-18 | MP-001 | Los 4 hallazgos corregidos por Claude Code: reescrita regla de autoría en AGENTS.md/CLAUDE.md (incorporando además la nueva política de commits en worktree), añadida excepción de naming para chore/mp-001-foundation, añadido analytics/dbt/ a MP-009/MP-015 en TASKS.md, grafo de dependencias sustituido por tabla exacta | commit pendiente |
| 2026-11-18 | MP-001 | Modelo de autonomía acotada (ADR-0007, DEC-014) añadido a petición del propietario: autorización por hito, commits de iteración en worktree, gates limitados a licencia/coste | commit pendiente |
| 2026-11-18 | MP-001 | Primera re-verificación de Codex: no aprobada — 2 bloqueantes + 2 menores por inconsistencia entre ADR-0007 y el resto de la documentación de protocolo | dispatch `ctx_e72e7a44721a` |
| 2026-11-18 | MP-001 | 4 nuevos hallazgos corregidos: sección "Modelo de autonomía por hito" añadida a AGENTS.md, protocolo de worktree/diagrama/regla 10 actualizados en AGENTS.md/CLAUDE.md/TASKS.md/PLAN.md para reflejar autorización por hito y worktrees paralelos, ADR-0007 corregido (ADRs de arquitectura como `Propuesto` durante autonomía, DEC-003 retirado de los gates), Hito 1 corregido (sin MP-010, fuera de rango) | commit pendiente |
| 2026-11-18 | MP-001 | Segunda re-verificación de Codex: aún no aprobada — 1 bloqueante (protocolo exigía merge a `main` entre cada tarea, anulando el propósito del modelo de autonomía) + 1 menor ("Principio rector" de PLAN.md contradecía la excepción de dependencias ya documentada) | dispatch `ctx_762cad1ca40c` |
| 2026-11-18 | MP-001 | Resuelto con mecanismo de ramas encadenadas: worktree de tarea dependiente se crea desde la rama de su dependencia en `DONE`, sin esperar merge a `main`; reescrito en AGENTS.md/CLAUDE.md/TASKS.md/PLAN.md | commit pendiente |
| 2026-11-18 | MP-001 | Tercera re-verificación de Codex: **APROBADO**, sin hallazgos bloqueantes ni menores. Sugerencia no bloqueante registrada como DEC-015 (convergencia de ramas para MP-012) | dispatch `ctx_0ee25a6a5d2c` |
| 2026-11-18 | MP-001 | Tarea dejada en `REVIEW` (Codex aprobó), pendiente de confirmación del Hito 1 y aceptación final del propietario | — |

## Cómo usar este documento

Al empezar cualquier tarea nueva, cualquier agente debe poder responder, leyendo solo `docs/STATUS.md` + `docs/TASKS.md`:

1. ¿Qué está hecho y qué falta?
2. ¿Qué tarea estoy autorizado a trabajar?
3. ¿Cómo se comprueba que lo que dice "hecho" realmente lo está? (ver columna "Evidencia de verificación" en `docs/TASKS.md`).
