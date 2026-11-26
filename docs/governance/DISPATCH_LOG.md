# DISPATCH_LOG.md — Registro de despachos de agentes (2026-11-25 → 2026-11-26)

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
| MP-025b correcciones | **Sustitución:** Codex `gpt-6.2-sol` · medium (en lugar de Astra High) | Claude `opus-5-5` · high (una verificación del delta) | recibo; lanzador programado 14:36 | pendiente | pendiente |

## Sustituciones y bloqueos de cuota (registrados, no reintentados)
- **MP-025b correcciones (2026-11-26):** se reasignan de Astra High a **Sol Medium** por economía (cambios de documento y tests, sin tocar datos ni métricas existentes; condición: resultados previos idénticos con `cmp`). Mismo proveedor, revisor sin cambios; la independencia se conserva. La cuota de Codex es de cuenta, así que el cambio de modelo no adelanta la reapertura (14:35).
- **Cuota de Codex agotada** en MP-026a (reapertura 17:38), MP-025a (22:39), MP-025b (03:40) y las correcciones de MP-025b (14:35); **de Claude** una vez en MP-024 (17:00). No se compró cuota ni se cambió de proveedor para sortearla.
- **Terra (`gpt-6.1-terra`):** disponible en el catálogo local; ejecuta React/TypeScript **sin navegador**; la validación visual la hace siempre Claude con preflight (`docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md`).
- **Coordinador:** Claude Sonnet 5.5; su esfuerzo efectivo no es verificable desde dentro de la sesión.
