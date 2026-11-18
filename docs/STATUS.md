# STATUS.md — Tablero vivo

> Punto de entrada del estado actual. El detalle por tarea vive en `docs/TASKS.md`; el historial de cambios, en `docs/CHANGELOG.md`.

## Hito autorizado actualmente

**Hito 1 autorizado por el propietario el `2026-11-18`: `MP-002` → `MP-009`.**

```text
Cobertura: F1 (factibilidad) + F2 (contratos) + F3 (persistencia/colector) + F4 (calidad/histórico)
Objetivo de salida: colector idempotente validado + quality engine + histórico exportado y replayable.
Cadena: MP-002 → MP-003 → MP-004 → MP-005 → MP-006 → MP-007 → MP-008 → MP-009.
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007.
```

MP-001 está `DONE`: Codex aprobó la revisión cruzada y, conforme a ADR-0007, no es necesario que la rama esté fusionada en `main` para que una tarea dependiente avance.

## Tarea actual

**MP-002 — Matriz de fuentes y licencias**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado por Claude Code el 2026-11-18)

Worktree/rama: `mp-002-fuentes-licencias`

### Checklist de MP-002

- [x] Documentación y ADRs obligatorios leídos antes de modificar archivos.
- [x] Renfe GTFS estático verificado como `CC BY 4.0` en el recurso oficial.
- [x] Renfe GTFS-RT Vehicle Positions, Trip Updates y Alerts verificados como `CC BY 4.0` en sus datasets oficiales.
- [x] Condiciones adicionales de Renfe Data verificadas: atribución, actualización, conservación de metadatos y no patrocinio.
- [x] GTFS Cercanías Madrid identificado en Comunidad de Madrid/NAP y licencia propia `CRTM-LDA` verificada en CRTM.
- [x] Requisitos CRTM documentados: `Powered by CRTM`, bruto/explotado, actualización/metadatos, no falseamiento/no patrocinio.
- [x] OpenStreetMap verificado como `ODbL-1.0`; consulta/base colectiva separadas de una base derivada distribuida.
- [x] `LICENSE` de Via Península verificado como `AGPL-3.0`; política de no copiar código preservada.
- [x] `LICENSE` de Niltra/cercanias verificado como MIT.
- [x] `LICENSE` de atlas-ferroviario verificado: MIT para código más aviso Renfe `CC BY 4.0` para datos.
- [x] Valfiguer verificado: datos/API normalizados `CC BY 4.0`; no se localizó repo público de implementación ni licencia de código (DEC-016).
- [x] Dataset estadístico Comunidad de Madrid 1923861 verificado como `CC BY 4.0` y de ámbito declarado nacional.
- [x] `DATA_SOURCES.md`, `LICENSE_MATRIX.md` y `ATTRIBUTION.md` actualizados con evidencia y fecha real.
- [x] `TASKS.md`, `STATUS.md`, `CHANGELOG.md` y `DECISIONS.md` actualizados.
- [x] Revisión independiente de Claude Code: re-verificación propia (no solo lectura del reporte de Codex) vía `gh api` y fetch directo de `data.renfe.com`, `crtm.es` y los ficheros `LICENSE` reales de los tres repos de referencia. Todas las afirmaciones de Codex se confirmaron exactas, incluido el matiz MIT-pero-`NOASSERTION` de atlas-ferroviario. **APROBADO.**

### Resultado y límites

No apareció una incompatibilidad que bloquee el uso previsto de las fuentes primarias. Renfe y CRTM permiten reutilización comercial y no comercial con sus respectivas condiciones; OSM es utilizable con atribución, pero una base derivada distribuida debe cumplir ODbL. Via Península permanece estrictamente como referencia conceptual por AGPL.

La verificación de MP-002 cubre **licencia y atribución**, no disponibilidad técnica, esquema, frecuencia ni cobertura C5. Esas propiedades siguen `PENDING MP-003`. El portal Renfe mostraba un fallo histórico SSL en el comprobador del recurso GTFS estático y NAP pedía inicio de sesión para descargar el GTFS CRTM; ambos se probarán técnicamente en MP-003 y no alteran la licencia verificada.

### Bloqueos

Ninguno. La licencia desconocida de la implementación Valfiguer no bloquea porque DEC-006 prohíbe usarla como dependencia de producción; queda registrada en DEC-016 y en la matriz.

### Siguiente paso

MP-002 está `DONE`. MP-003 ramifica desde esta rama (`mp-002-fuentes-licencias`) sin esperar merge a `main`, conforme a ADR-0007.

### Nota de proceso (ramas encadenadas)

Esta rama se bifurcó de `chore/mp-001-foundation` en el commit `3e7b533`, **antes** de que esa rama recibiera un commit posterior (`fac945c`) registrando la aceptación de MP-001 por el propietario y la autorización de Hito 1. Codex infirió correctamente esa autorización por el contexto del encargo (no por leer un `STATUS.md` ya actualizado, que en esta rama no existía todavía) y la registró aquí de forma independiente. Resultado: `chore/mp-001-foundation` y esta rama tienen ahora dos redacciones distintas, pero no contradictorias, de "MP-001 está DONE / Hito 1 autorizado". Claude Code alineó el campo `Estado` de MP-001 en `docs/TASKS.md` de ambas ramas a `DONE` para que la reconciliación en el merge final sea trivial. **Lección para hitos futuros:** si se edita el `STATUS.md` de la rama base después de que una rama hija ya se bifurcó, esa edición no llega a la hija automáticamente — hay que reconciliarla explícitamente, como aquí.

## Bitácora

| Timestamp UTC | Tarea | Evento | Evidencia |
|---|---|---|---|
| `2026-11-18` | MP-001 | Revisión cruzada aprobada; tarea tratada como `DONE` para la cadena autorizada | `docs/TASKS.md`; dispatch de revisión `ctx_0ee25a6a5d2c` |
| `2026-11-18` | Hito 1 | Propietario autoriza explícitamente `MP-002` → `MP-009` | Despacho Orca de MP-002 (`task_8f7f49749f10`) |
| `2026-11-18T15:16:53Z` | MP-002 | Cierre de verificación formal de licencias y condiciones | Checklist y enlaces en `docs/legal/DATA_SOURCES.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Hallazgo Valfiguer: datos/API `CC BY 4.0`, implementación sin repo/licencia verificable | DEC-016; `docs/legal/LICENSE_MATRIX.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Entregables documentales completados; tarea pasa a `REVIEW` | `docs/TASKS.md`; commit local de MP-002 |
| `2026-11-18` | MP-002 | Revisión independiente de Claude Code (gh api + fetch directo de Renfe/CRTM/LICENSE reales): **APROBADO**, sin hallazgos bloqueantes ni menores sobre el contenido. Hallazgo de proceso (divergencia de ramas) documentado y reconciliado | — |

## Cómo usar este documento

Al empezar una tarea, comprobar aquí el hito autorizado y en `docs/TASKS.md` que sus dependencias directas están `DONE`. Ningún estado `DONE` se declara sin aprobación del revisor, y ningún test/verificación se reporta sin evidencia ejecutada.
