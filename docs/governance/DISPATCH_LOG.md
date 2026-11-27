# DISPATCH_LOG.md — Registro de despachos de agentes (2026-11-25 → 2026-11-27)

**Qué es:** quién ejecutó y quién revisó cada tarea, con qué modelo y esfuerzo, y qué consta de forma verificable. Complementa `docs/ORCHESTRATION_POLICY.md` (la regla) y `docs/H4_TASK_MATRIX.md` (el reparto previsto). Los registros del Hito 3 siguen en `docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md`. **Los dictámenes históricos no se reescriben:** las correcciones se añaden con fecha.

## Cómo se decide y qué se verifica
- **El coordinador (Claude Sonnet 5.5) fija `--agent`, `--model` y `--effort` en cada `worker-start`**; Orca no elige el modelo (la política prohíbe depender del modelo por defecto). Un mensaje de seguimiento al mismo despacho conserva su modelo y esfuerzo.
- **Evidencia de identidad:** Claude → el `argv` del proceso muestra `--model` y `--effort` (verificado). Codex → solo el **recibo de Orca** (el proceso `app-server` no expone modelo ni esfuerzo; **no verificable de forma independiente**). El autoinforme del modelo no cuenta.
- **Independencia:** ejecutor y revisor de proveedores distintos. Una sustitución de ejecutor dentro del mismo proveedor se registra aquí (ver MP-025b).

## Despachos
| Tarea | Ejecutor (modelo · esfuerzo) | Revisor (modelo · esfuerzo) | Identidad verificada | HEAD revisado | Dictamen |
|---|---|---|---|---|---|
| Fase 1 · scripts `sync_docs`/`check_docs` | Codex `gpt-6.2-sol` · medium | Claude `sonnet-5-5` · high | revisor por argv; ejecutor por recibo | `7702e89`→`60e8e9b`→`21edbf0` | APPROVED (3 pasadas) |
| Fase 1 · reconciliación documental | Claude `sonnet-5-5` (coordinador) | Codex `gpt-6.2-sol` · medium | recibo | `7702e89`→`60e8e9b`→`5d7a9a1` | CHANGES_REQUESTED ×3 (la verificación posterior de `b699cd7` la hizo el propietario, sin worker) |
| MP-023 BD segura | Codex `gpt-6.2-sol` · medium | Claude `sonnet-5-5` · high | argv (revisor) | `becaf7f` | APPROVED (2 rondas) |
| MP-024 ADR-0014 enmienda | Claude `opus-5-5` · high | Codex `gpt-6.2-astra` · high | argv (ejecutor) | `f0f8224`→`559a5c2`→`c7b4df6` | CHANGES_REQUESTED parcial; sin APPROVED; dirección aprobada por el propietario |
| MP-026a replay y GTFS | Codex `gpt-6.2-sol` · high | Claude `opus-5-5` · high | argv (revisor) | `fe0ea85`→`70170c7`→`ec45d95` | APPROVED (2 rondas + delta de reloj) |
| MP-025a motor de parada | Codex `gpt-6.2-astra` · high | Claude `opus-5-5` · high | argv (revisor) | `5514016`→`0f0ce54` | APPROVED en ronda 2 |
| MP-026b snapshot consistente | Codex `gpt-6.2-sol` · high | Claude `opus-5-5` · high | argv (revisor) | `ff5e6ad` | APPROVED en ronda 1 |
| MP-028 captura (preparación y smoke) | Codex `gpt-6.2-sol` · medium | Claude `sonnet-5-5` · high | argv (revisor) | `a5ddc9b` | APPROVED (preparación y smoke); sesiones 1 de 3 |
| MP-030 interfaz mínima | Codex `gpt-6.1-terra` · medium (sin navegador) | Claude `sonnet-5-5` · high con Chrome DevTools MCP | argv + preflight de navegador | `b799b7a`→`6e60249`; final `0600610` | CHANGES_REQUESTED ×2; corrección final no re-verificada |
| MP-025b validación provisional | Codex `gpt-6.2-astra` · high | Claude `opus-5-5` · high | argv (revisor) | `6398707` | CHANGES_REQUESTED (2 B, 4 A) |
| MP-025b correcciones | **Sustitución:** Codex `gpt-6.2-sol` · medium (en lugar de Astra High) | Claude `opus-5-5` · high (una verificación del delta) | recibo; despachado por el lanzador programado a las 14:36 | `cc7181b` | APPROVED (del informe provisional; **no** valida el motor ni cierra FR-01) |
| MP-036 fallback GPS rechazado | Codex `gpt-6.2-sol` · high | Claude `opus-5-5` · high (revisión completa + una verificación del delta) | argv (revisor); recibo (ejecutor) | `a7e01b8`→`8c005c8` (PR #15 en borrador) | 1ª pasada CHANGES_REQUESTED (2 B, 8 A); delta APPROVED (3 A residuales). **No** valida el motor ni cierra FR-01 |
| MP-037 estudio M7 frente a R4 | Codex `gpt-6.2-sol` · medium | Claude `opus-5-5` · high | recibo (ejecutor) | — | **BLOQUEADA por cuota de Codex** al arrancar (reapertura 19:36); sin retry ni cambio de proveedor |
| MP-038 comparación sobre la jornada 2 (continuación) | Codex `gpt-6.2-sol` · medium (bloqueado por límite semanal el 2026-11-27; el propietario restableció la cuota y se reanudó con un worker nuevo, mismo modelo) | Claude `opus-5-5` · high (una verificación única) | recibo (ejecutor); argv no visible en el revisor | `dc59299` (→ `b7aed67` con 2 observaciones menores) | APPROVED. **No** cierra FR-01 |

## Sustituciones y bloqueos de cuota (registrados, no reintentados)
- **MP-025b correcciones (2026-11-26):** se reasignan de Astra High a **Sol Medium** por economía (cambios de documento y tests, sin tocar datos ni métricas existentes; condición: resultados previos idénticos con `cmp`). Mismo proveedor, revisor sin cambios; la independencia se conserva. La cuota de Codex es de cuenta, así que el cambio de modelo no adelanta la reapertura (14:35).
- **Cuota de Codex agotada** en MP-026a (reapertura 17:38), MP-025a (22:39), MP-025b (03:40) las correcciones de MP-025b (14:35) MP-037 (2026-11-26, reapertura 19:36) y la comparación de la jornada 2 de MP-038 (2026-11-27, **límite semanal**, reapertura 2026-12-01 21:53); **de Claude** una vez en MP-024 (17:00). No se compró cuota ni se cambió de proveedor para sortearla.
- **Terra (`gpt-6.1-terra`):** disponible en el catálogo local; ejecuta React/TypeScript **sin navegador**; la validación visual la hace siempre Claude con preflight (`docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md`).
- **Coordinador:** Claude Sonnet 5.5; su esfuerzo efectivo no es verificable desde dentro de la sesión.

## Actualización del 2026-11-27

- **Integraciones coordinadas por Claude Sonnet 5.5 por orden del propietario:** MP-036 #15 (`d3be45dc`), MP-038 #17 (`453a5eb5`), MP-028 #12 (`2ffaee4f`), MP-030 #11 (`359932db`) y MP-037 #16 (`14709bba`, 2026-11-26 23:01 UTC, 2026-11-27 en Madrid). La autoría compartida en Git se conserva según AGENTS.md. Las integraciones y sus alcances se comprobaron con `git log origin/main --first-parent` y `gh pr list --state merged`.
- **MP-037 reanudada:** estudio entregado por Codex Sol Medium, con revisión Claude Opus High. Tras CHANGES_REQUESTED (2 B, 5 A), el delta `ebaea29` recibió APPROVED. Las candidatas quedan pendientes de evidencia posterior y decisión del propietario.
- **MP-030:** la comprobación visual excepcional sobre `35489b2` (frontend idéntico a `0600610`) dio PASS focalizado en escritorio y móvil, 0 B y 3 A. El último código revisado con dictamen sigue siendo `6e60249`, CHANGES_REQUESTED. El código de la corrección final sigue pendiente de re-verificación independiente.
- **Autorización del propietario:** inicio de Design Discovery; `HG-DESIGN-CHOICE` sigue OPEN, con integración de un rediseño sujeta a autorización. Sustitución temporal por cuota de Claude hasta aproximadamente el domingo. Codex realiza las integraciones ya revisadas, seguimiento, baseline y materiales y prototipos aislados. Sol Medium para documentación y mecánica, Terra o Sol High para prototipos; Astra solo ante bloqueo técnico concreto. Las entregas nuevas quedan **IMPLEMENTADAS / PENDIENTES DE REVISIÓN** por Claude. Terra sin navegador: pasos visuales sin ejecutar quedan NOT RUN.
- **Seguimiento del plan (PR #14):** Codex `gpt-6.2-sol` · medium, identidad según recibo Orca (`task_775931bf652e`, `ctx_7ef1162056ed`). Base `f3e3b0a`, rama `docs/tareas-lote-correccion`. Dictamen **NOT_REVIEWED**; revisión de Claude pendiente.
- **Restricciones del lote:** sin BD 5433, contratación, publicación de datasets, despliegue público, ampliación del motor, cambios en R4 ni inicio del grafo completo de MP-029. Jornada 3 de MP-028 sin programar; falta confirmar ventana.

### Evidencia local del seguimiento del plan

Commit de implementación `6aa02bf` en `docs/tareas-lote-correccion`. Python 3.12.3. Dictamen independiente pendiente.

| Comando | Resultado |
|---|---|
| `python3 scripts/governance/sync_docs.py` | PASS (0), actualizó los bloques generados en STATUS, TASKS y MILESTONES |
| `python3 scripts/governance/sync_docs.py --check` | PASS (0), sin salida |
| `python3 scripts/governance/check_docs.py` | PASS (0), «Documentación de gobernanza correcta.» |
| `python3 -m unittest tests.governance.test_governance -v` | PASS (0), «Ran 38 tests», «OK» |
| `git diff --check` | PASS (0), sin salida |
| Jornada 3, validación de producto y gate visual independiente | NO EJECUTADO en este despacho |

Falta comprobar: acceso directo al manifiesto y al volcado privados de la jornada 2, acceso a capturas privadas de MP-030, suspensión real del Mac, nombre contractual del campo de cancelación y visibilidad histórica por hora civil. Los artefactos y resultados de las jornadas anteriores se citan desde su evidencia versionada.
