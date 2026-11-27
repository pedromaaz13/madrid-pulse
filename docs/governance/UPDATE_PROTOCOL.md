# UPDATE_PROTOCOL.md — Cómo se mantiene el estado documental

**Fecha:** 2026-11-25. Complementa (no sustituye) `AGENTS.md`, `CLAUDE.md` y `docs/ORCHESTRATION_POLICY.md`; si contradice a `AGENTS.md`, manda `AGENTS.md`.

## 1. Una sola fuente de verdad
*Origen de los datos de `PROJECT_STATE.json`:* estados, roles y dependencias de MP-001…022 se extrajeron de `docs/TASKS.md`; SHA y fechas de `git`; la auditoría, de su registro de despachos. Los cambios de estado y reanudación se registran en `PROJECT_STATE.json`; si cambia el alcance o la evidencia, se actualiza su fuente en el mismo commit. `check_docs.py` valida las referencias estructuradas y la actualización de las vistas generadas.
| Qué | Dónde | Quién lo escribe |
|---|---|---|
| Índice estructurado de fases, hitos, tareas, gates y hallazgos abiertos | `docs/governance/PROJECT_STATE.json` | agente ejecutor/coordinador, **a mano y revisado** |
| Tablero, resumen, hitos, índice, fichas de reanudación y diferidos | secciones entre marcadores `GENERATED` de `docs/STATUS.md`, `docs/roadmap/MILESTONES.md`, `docs/TASKS.md` | **solo** `scripts/governance/sync_docs.py` |
| Alcance y evidencia de tarea | fichas históricas de `docs/TASKS.md`, fuentes de alcance en `source`, resultados en `evidence` | ejecutor y revisor |
| Cambios confirmados | `docs/CHANGELOG.md` | **manual**, sobre entregas realizadas, con alcance y límites de integración, revisión y validación |
| Decisiones | `docs/DECISIONS.md` y `docs/adr/` | propuesta del agente; **aceptación solo del propietario** |

Ningún documento nuevo puede crear una segunda verdad. El texto histórico de STATUS/TASKS/CHANGELOG **no se borra**; se corrige con notas fechadas.

## 2. Dimensiones de estado
`implementation_status` (¿está construido?) · `review_status` (¿lo aprobó un revisor de proveedor contrario?) · `integration_status` (¿está en `main`?) · `deployment_status` (¿está desplegado y dónde?). Un técnico `DONE` no es `MERGED` ni `LIVE`; un CI verde no significa cero P0. `IMPLEMENTED_WITH_OPEN_GATE` = hay código, pero el exit gate literal no tiene evidencia.

`validation_status` es opcional y registra la evidencia de aceptación del alcance (`NOT_VALIDATED`, `PROVISIONAL`, `VALIDATED`); un merge solo acredita integración. La ausencia del campo deja la validación sin registrar.

Para reanudar, actualizar `last_update`, `done`, `remaining`, `not_closed_reason` y `next_action`; si hay espera, documentar `blocked_by` con IDs canónicos y `unblock_condition`. Mantener `gate`, `depends_on`, `evidence` y la referencia de rama/commit/PR; `reviewed_head` conserva el commit evaluado y `owner_decisions` enumera decisiones concretas. En una entrega cerrada basta anotar fecha y resultado. Si falta una comprobación relevante, dejar constancia con «falta comprobar: …».

## 3. Transiciones válidas
```text
implementation: NOT_STARTED → PLANNED → IN_PROGRESS → IMPLEMENTED | IMPLEMENTED_WITH_OPEN_GATE | BLOCKED ; DROPPED
review:         NOT_REVIEWED → IN_REVIEW → CHANGES_REQUESTED ↔ IN_REVIEW → APPROVED   (APPROVED sobre un HEAD; un cambio posterior lo invalida)
integration:    NOT_INTEGRATED → MERGED                                                (solo tras merge real o incorporación a main verificada: SHA y fecha; `integration_kind` distingue `merge_commit` de `content_in_main`, p. ej. el commit inicial)
deployment:     NOT_DEPLOYED → STAGING → PUBLIC                                        (PUBLIC exige el gate humano propio del track —p. ej. HG-MVP0-PUBLISH para la demo— y, fuera de MVP 0, también HG-LIVE-PUBLIC)
closure (fase/hito): OPEN → CLOSED                                                     (exige gate y evidencia; CLOSED es inmutable salvo corrección documentada)
  Un hito puede estar CLOSED (cierre histórico revisado) y a la vez IMPLEMENTED_WITH_OPEN_GATE solo si lista en `open_gates_inherited` las fases cuyo gate sigue OPEN (p. ej. H1 → F3, F4). Una fase nunca.
```
## 4. Responsables
- **Ejecutor:** actualiza `PROJECT_STATE.json` al pasar a `REVIEW` con comandos y resultados reales; no se auto-aprueba.
- **Revisor (proveedor contrario):** registra el dictamen `APPROVED`/`CHANGES_REQUESTED`/`BLOCKED` con evidencia; lo anotado como `NOT RUN` no cuenta como aprobado.
- **Coordinador:** reconcilia el estado y lanza `sync_docs.py` y `check_docs.py`; **no declara `APPROVED` por deducción**.
- **Propietario:** ADR, elección de diseño, hosting/coste, push/PR/merge, publicación. Esas aprobaciones se registran en `human_gates` **solo cuando existen** (`approved_by: owner`, fecha, evidencia). Ningún script ni workflow las genera.

## 5. Criterio de `DONE` (técnico)
Dictamen `APPROVED` de proveedor contrario sobre el HEAD final; pruebas de aceptación **ejecutadas** (regresión RED en `beb9434` y GREEN tras el fix cuando aplique); evidencia enlazada; sin escritura en bases persistentes; autoría humana sin `Co-authored-by`. `DONE` no implica integración ni despliegue.

## 6. Hallazgos nuevos
Un hallazgo nuevo entra como `PROPOSED` (`open_findings` o `proposed_extensions`) hasta que el propietario lo acepta; no cambia gates ni abre tareas por sí solo. No se cierra un P0 sin prueba que falle antes y pase después. `deferred_items` registra hallazgos y propuestas aplazados con ID, origen, descripción, motivo, condición para retomar y estado `DEFERRED`. Su registro mantiene pendiente la autorización correspondiente.

## 7. Cierre de fases e hitos
**Cierre histórico ≠ preparación para release:** `CLOSED` registra que un gate se evidenció y no se reescribe; la disponibilidad para publicar se decide aparte (gate MP-035, aprobación humana) y no se deduce de ningún cierre. Los P0 abiertos y el NO-GO público permanecen visibles en `PROJECT_STATE.json` y en las tablas generadas.
1. Cada fase/hito declara su exit gate literal. 2. Se contrasta con evidencia real; si falta, queda `IMPLEMENTED_WITH_OPEN_GATE` y `OPEN`. 3. Solo con gate evidenciado pasa a `CLOSED`. 4. Si más tarde aparece un defecto, **no se reescribe el cierre**: se enlaza como `open_findings` y se abre trabajo nuevo.

## 8. Flujo por tarea
preflight → rama propia → implementación → pruebas y artefactos → revisión de proveedor contrario → actualizar `PROJECT_STATE.json` y fichas → `python scripts/governance/sync_docs.py` → `python scripts/governance/check_docs.py` → commit de iteración en el worktree (permitido a los agentes) → **[acciones exclusivas del propietario, `AGENTS.md` y `CLAUDE.md`: `git push`, abrir el PR]** → CI del PR en verde → revisión del propietario → **[merge a `main`, exclusivo del propietario]** → commit documental posterior que registra SHA e integración (lo prepara el agente y lo comitea/empuja el propietario). Ningún workflow aprueba, fusiona ni despliega por deducción.
**Prevalencia:** `AGENTS.md` (modelo de autonomía por hito, un worktree por tarea, regla de autoría) y `CLAUDE.md` mandan sobre este flujo. En particular, una tarea queda `DONE` (revisión aprobada) y sus dependientes pueden ramificar desde ella **antes** del merge a `main`; `integration_status` solo pasa a `MERGED` con merge real o incorporación a `main` verificada (`integration_kind`: `merge_commit` o `content_in_main`).

## 9. Mecanismo y límites
`sync_docs.py` regenera solo entre marcadores y es determinista; `check_docs.py` falla ante: IDs duplicados, dependencias inexistentes o cíclicas, `APPROVED`/`IMPLEMENTED` sin revisor o evidencia, fase/hito `CLOSED` sin gate, SHA o fechas inválidos, `MERGED` sin SHA, despliegue sin evidencia, aprobaciones humanas sin autor, rutas de evidencia inexistentes y bloques desincronizados. Corre en CI (job `governance`, sin red ni secretos). **Límite:** valida coherencia interna y las rutas/referencias estructuradas del JSON (no todos los enlaces Markdown), no la verdad del mundo real; «sin red» aplica al verificador local (el job de CI sí descarga el checkout y `setup-python`); la veracidad de cada dato sigue dependiendo de la evidencia enlazada y de la revisión humana.

## Significado de `UNKNOWN` en `evidence`

`evidence` solo admite rutas que existan en la rama que se valida o el literal `UNKNOWN`. `UNKNOWN` **no** significa «sin evidencia»: significa que la evidencia existe pero **todavía no está en esta rama** (p. ej. vive en la rama de un PR abierto) y por eso no se enlaza una ruta que aquí no existe. En esos casos el campo `notes` cita el PR y el commit exactos donde está el informe, y la entrada se sustituye por la ruta real cuando el PR se integra en `main`. Una tarea con `UNKNOWN` no se da por verificada por esta rama: la comprobación es la del PR citado.
