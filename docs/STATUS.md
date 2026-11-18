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

**MP-006 — Esquema PostgreSQL/PostGIS v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **REVIEW**

Worktree/rama: `mp-006-postgis-schema`, ramificada desde `mp-005-contrato-canonico` (MP-005 `DONE`)

### Checklist de MP-006

- [x] Compose aislado: proyecto `madrid-pulse`, imagen `postgis/postgis:17-3.5`,
  puerto `127.0.0.1:5433`, red y volumen nombrados propios; los contenedores
  `*-traza-app` no se tocaron.
- [x] `0001_init.up.sql` transaccional: PostGIS y las 14 entidades de aplicación
  (más `source_feed_version`, exigida por el versionado GTFS y su FK), constraints
  e índices B-tree/GIST.
- [x] Correspondencia canónica documentada: `entity_count`, `affected_route_ids`,
  `latitude`/`longitude`, `raw_vehicle_label`, `next_stop_id`,
  `nucleo_prefix`/`nucleo_name`/`nucleo_prefixes`; `geom` generado desde las
  coordenadas y nullable cuando la fuente no aporta posición.
- [x] Migración aplicada sobre PostgreSQL/PostGIS real con `ON_ERROR_STOP=1`:
  `CREATE TABLE` ×14, `CREATE INDEX` ×5 y `COMMIT`; PostGIS `3.5.2`.
- [x] Datos válidos insertados; `geom` generado como `POINT(-3.689 40.406)` y
  observación sin posición persistida con `latitude`, `longitude` y `geom` nulos.
- [x] Constraints probadas con fallos reales (todos exit 1): duplicado de
  `(network_id, source_route_id)`, de `(service_date, source_trip_id)` y de
  `(ingestion_run_id, payload_hash)` rechazados por sus `UNIQUE` respectivos.
- [x] Rollback real con `ON_ERROR_STOP=1`: 14 tablas eliminadas y `COMMIT`;
  consulta posterior `remaining_application_tables = 0`. PostGIS se conserva
  porque la imagen instala extensiones dependientes antes de la migración.
- [x] Ciclo final `down → up` repetido desde cero: ambos comandos exit 0.
- [x] Suites de regresión reejecutadas: contratos 23/23 `OK`; fixtures 6/6 `OK`.
- [x] `docker compose ... config --quiet` y `git diff --check`: exit 0.
- [x] Contenedor de Madrid Pulse detenido al finalizar; volumen propio conservado
  con la migración final aplicada para que el propietario pueda reanudarlo.

### Resultado y límites

SQL plano permite auditar el DDL inicial sin introducir todavía un framework de
migraciones. El rollback elimina el esquema de aplicación pero no usa
`DROP EXTENSION ... CASCADE`: las extensiones PostGIS dependientes vienen
preinstaladas por la imagen y no pertenecen a esta migración.

### Bloqueos

Ninguno.

### Siguiente paso

Claude Code debe auditar el diff y repetir las comprobaciones pertinentes en este
mismo worktree. MP-006 no pasa a `DONE` hasta esa aprobación independiente.

## Tareas cerradas de la cadena

**MP-004 — Fixtures reproducibles**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-004-fixtures`, ramificada desde `mp-003-probe-c5` (MP-003 `DONE`)

### Checklist de MP-004

- [x] Capturas frescas directas de `vehicle_positions.json`, `trip_updates.json` y `alerts.json`: `200 application/json`, sin guardar cabeceras ni cookies.
- [x] Tres fixtures JSON reducidas y versionables: 394 → 10 posiciones, 401 → 8 actualizaciones y 76 → 3 alertas.
- [x] Cada fixture conserva entidades de Madrid; posiciones conserva además C5 con prefijos `20`, `30` y `40` para probar la colisión entre núcleos.
- [x] `tests/fixtures/MANIFEST.md` registra fecha UTC, endpoint, recuentos y SHA-256.
- [x] Tests offline con Python `unittest`: envoltura GTFS-RT, esquema por feed, integridad SHA-256, cobertura Madrid y rechazo del filtro ingenuo por etiqueta C5.
- [x] Ejecución real: `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v` → 6 tests, `OK` (0.001 s).
- [x] Los tres ficheros pasan `python3 -m json.tool`; hashes re-verificados con `shasum -a 256`.
- [x] Revisión independiente de Claude Code: SHA-256 recalculados de forma propia (coinciden), suite re-ejecutada (6/6 `OK`), inspección del test de colisión C5 confirmando que es sustantivo (un filtro ingenuo por etiqueta captura 4 núcleos, el correcto aísla solo Madrid), sin cookies/secretos, enlaces y licencias revalidados. **APROBADO.**

### Resultado y límites

Las fixtures se cargan exclusivamente desde disco y no incluyen código de red ni dependencias externas. La captura de posiciones no contenía ninguna entidad sin `position`; el caso observado en MP-003 no se fabricó. `pytest` no estaba instalado, por lo que se eligió `unittest` de la biblioteca estándar para mantener la suite reproducible sin instalación adicional.

### Bloqueos

Ninguno.

### Siguiente paso

MP-004 está `DONE`. MP-005 (Contrato canónico interno, ejecutor Claude Code, revisor Codex) puede ramificar desde `mp-004-fixtures` sin esperar merge a `main`.

**MP-003 — Probe real de feeds C5 (GTFS + GTFS-RT)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-003-probe-c5`, ramificada desde `mp-002-fuentes-licencias` (MP-002 `DONE`)

### Checklist de MP-003

- [x] `vehicle_positions.json` probado en vivo: `200 OK`, JSON real (GTFS-RT 2.0), 3 polls espaciados ~20 s confirmando frecuencia de refresco real (~20–22 s).
- [x] `trip_updates.json` probado en vivo: `200 OK`, 302 entidades, esquema con `delay` en segundos por parada.
- [x] `alerts.json` probado en vivo: `200 OK`, 82 alertas activas, confirma `routeId` completo por entidad informada.
- [x] GTFS estático descargado realmente (15,7 MB, `200 OK`) desde el enlace real (`ssl.renfe.com`, distinto del enlace de portal que había fallado en MP-002) e inspeccionado (`routes/trips/stops/calendar/shapes/stop_times/transfers/agency.txt`).
- [x] **Hallazgo crítico:** "C5" no es único — existe también en Asturias (`20T0011C5`) y Andalucía (`30T0009C5`) en el mismo feed nacional. Registrado como DEC-017/ADR-0008 (`Propuesto`); `docs/DATA_MODEL.md` corregido.
- [x] Resolución de `trip_id` del feed en vivo contra GTFS estático: **igualdad literal de cadena** contra el campo `trip_id` de `trips.txt` (3er campo del CSV), confirmado 403/403 (y 404/404 en la re-verificación de Codex con datos frescos) — es un `JOIN` directo, no requiere reconstrucción por `(service_id, vehículo, línea)`.
- [x] `docs/legal/DATA_SOURCES.md` actualizado de `PENDING MP-003` a `VERIFIED` para los 4 recursos Renfe.
- [x] `docs/research/MP-003-probe-findings.md`, `docs/TASKS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` actualizados.
- [x] Primera revisión independiente de Codex (dispatch `ctx_61d7dd4fd86b`): **no aprobada** — repitió los probes en vivo él mismo (no solo leyó el reporte), incluida una comparación sistemática `comm -12`/`comm -23` de los 403 `trip_id` en vivo contra `trips.txt`. 2 bloqueantes + 2 menores:
  - **Bloqueante 1:** 403/403 `trip_id` en vivo coinciden literalmente con `trips.txt` — contradice la afirmación anterior de este documento. Causa raíz: un `grep` propio anclado al campo equivocado (`trip_id` es el 3er campo de `trips.txt`, no el 1º). Corregido en `docs/research/MP-003-probe-findings.md` §7 con la comparación de conjuntos completa.
  - **Bloqueante 2:** `docs/DATA_MODEL.md` tenía `UNIQUE(network_id, source_route_id)` junto con una nota que agrupaba 5 `source_route_id` bajo un único `route.id` — cardinalidad imposible. Corregido: 5 filas `route.id`, agrupadas por `(network_id, short_name)`.
  - **Menor:** findings afirmaba falsamente que el GTFS no incluía `shapes.txt` (sí lo incluye, está en la propia tabla del documento). Corregido.
  - **Menor:** no se había medido la frecuencia de `trip_updates`/`alerts` (solo `vehicle_positions`). Medido: `trip_updates` Δ42s, `alerts` Δ20s (2 polls cada uno).
  - Codex confirmó que el resto de pendientes (cobertura larga de `trip_updates`, CRTM, shapes/stop_times detallados, cambio de día) están razonablemente fuera de alcance de MP-003.
- [x] Revisión final independiente de Codex: **APROBADA**, sin hallazgos abiertos. Repetida la comparación con datos frescos: 404/404 `trip_id` vivos coinciden literalmente con `trips.txt`, 0 sin match. Confirmada la coherencia de cardinalidad entre `docs/DATA_MODEL.md`, DEC-017 y ADR-0008; enlaces, secretos y licencias revalidados.

### Resultado y límites

Los tres feeds GTFS-RT y el GTFS estático están disponibles, accesibles y documentados con esquema real. El hallazgo de la colisión de "C5" entre núcleos es el resultado más importante de esta tarea y obliga a una corrección de `docs/DATA_MODEL.md` (ver DEC-017/ADR-0008, `Propuesto`, pendiente de promoción por el propietario).

**Pendiente explícito, no bloqueante para MP-003, a resolver en tareas posteriores:** cobertura real de `trip_updates` para Madrid en ventana más larga (en el único poll realizado, Madrid tuvo 0/302 — no se puede concluir si es casualidad puntual o un patrón, ver findings §5); descarga del GTFS de CRTM (el NAP exigía login, no se probó); validación detallada de `shapes`/`stop_times` de las 5 variantes de C5 Madrid (corresponde a MP-010); comportamiento en cambio de día de servicio (corresponde a MP-012).

### Bloqueos

Ninguno. El hallazgo de la colisión de "C5" no bloquea MP-003 (ya está documentado y corregido en el modelo); sí debe tenerse en cuenta en MP-005 (contrato canónico) y MP-007 (colector) antes de implementarlos.

### Siguiente paso

MP-004 puede ramificar desde `mp-003-probe-c5` conforme al hito autorizado y al grafo de dependencias; no necesita esperar a que el propietario fusione esta rama a `main`.

### MP-001 y MP-002 — cerradas en ramas anteriores de esta cadena

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
| `2026-11-18T15:28–15:31Z` | MP-003 | Probe real de los 3 feeds GTFS-RT (3 polls de `vehicle_positions` espaciados ~20 s, 1 poll de `trip_updates` y `alerts`) y descarga real del GTFS estático (15,7 MB) | `docs/research/MP-003-probe-findings.md` |
| `2026-11-18` | MP-003 | Hallazgo crítico: "C5" no es único en el feed nacional (también en Asturias y Andalucía); corregido `docs/DATA_MODEL.md`, registrado DEC-017/ADR-0008 (`Propuesto`) | `docs/DECISIONS.md`; `docs/adr/0008-route-identity.md` |
| `2026-11-18` | MP-003 | Entregables completados; tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | `docs/TASKS.md`; commit local de MP-003 |
| `2026-11-18` | MP-003 | Revisión de Codex (repitiendo probes en vivo él mismo): no aprobada — 2 bloqueantes (trip_id sí coincide literalmente con trips.txt; cardinalidad imposible en DATA_MODEL.md) + 2 menores (shapes.txt sí incluido; faltaba medir frecuencia de trip_updates/alerts) | dispatch `ctx_61d7dd4fd86b` |
| `2026-11-18` | MP-003 | Los 4 hallazgos corregidos tras verificación propia (comparación de conjuntos 403/403, medición real de trip_updates Δ42s y alerts Δ20s); reenviado a Codex | `bdf263e` |
| `2026-11-18` | MP-003 | Segunda revisión de Codex (con descarga fresca, 404/404 confirmado): **no aprobada** — hallazgo menor residual: `docs/STATUS.md` conservaba la afirmación bloqueante ya desmentida en un bullet que no se había actualizado; además "alerts sin cambios de contenido" se basaba solo en igual recuento, no en comparación real de contenido | dispatch `ctx_e4a31f1e7e61` |
| `2026-11-18` | MP-003 | Revisión final de Codex: **APROBADA** — 404/404 `trip_id` resueltos por igualdad literal, 0 sin match; cardinalidad, documentación, enlaces, secretos y licencias coherentes. MP-003 pasa a `DONE` | revisión posterior a `f6d8ee9` |
| `2026-11-18T16:01Z` | MP-004 | Capturas frescas de los 3 feeds; fixtures reducidas 394→10, 401→8 y 76→3 con hashes SHA-256 documentados | `tests/fixtures/MANIFEST.md` |
| `2026-11-18T16:04Z` | MP-004 | Suite offline ejecutada: 6 tests `unittest`, `OK`; JSON y hashes revalidados; tarea pasa a `REVIEW` | `tests/fixtures/test_parse_fixtures.py`; `docs/TASKS.md` |
| `2026-11-18` | MP-004 | Revisión independiente de Claude Code: hashes y suite re-ejecutados, test de colisión C5 inspeccionado y confirmado sustantivo. **APROBADO**, sin hallazgos. MP-004 pasa a `DONE` | commit pendiente |
| `2026-11-18` | MP-005 | Contrato canónico implementado (`packages/contracts/`) con 17 tests reales (reales + sintéticos) ejecutados en verde | commit pendiente |
| `2026-11-18` | MP-005 | Hallazgo: `speed_kmh`/`bearing`/`current_stop_sequence`/`effect`/`cause`/`header_text` del modelo candidato nunca aparecen en el feed real; corregidos `docs/DATA_MODEL.md`/`docs/DATA_QUALITY.md`, registrado DEC-018/ADR-0009 (`Propuesto`) | — |
| `2026-11-18` | MP-005 | Tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | — |
| `2026-11-18` | MP-005 | Primera revisión de Codex: no aprobada — 3 bloqueantes + 1 menor, todos reales (comentario inconsistente, falta de enforcement UTC, falta de trazabilidad, redacción incorrecta en ADR-0009) | dispatch `ctx_ea1d5cf46d74` |
| `2026-11-18` | MP-005 | Los 4 hallazgos corregidos: `require_utc`/`require_utc_or_none` añadidos con 5 tests nuevos (22 en total), `TRACEABILITY.md` actualizado, `ADR-0009` y `raw.py` corregidos; reenviado a Codex | commit `cf11012` |
| `2026-11-18` | MP-005 | Segunda revisión de Codex: no aprobada — el bloqueante 1 de la ronda anterior solo se había documentado con un comentario, no resuelto; `raw.py` seguía declarando `end` pese a que el propio módulo prohíbe campos no observados | dispatch `ctx_ded900b82f20` |
| `2026-11-18` | MP-005 | `end` eliminado de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; test de regresión añadido (23 tests); reenviado a Codex para tercera verificación | commit `a9b1172` |
| `2026-11-18` | MP-005 | Tercera revisión independiente de Codex: **APROBADA** — 23/23 tests, esquema `raw`, enforcement UTC, trazabilidad, ADR, enlaces, secretos y whitespace verificados; tarea pasa a `DONE` | revisión posterior a `a9b1172` |
| `2026-11-18T22:53:33Z` | MP-006 | Migración PostGIS aplicada, constraints probadas con duplicados reales, rollback verificado (`0` tablas de aplicación) y ciclo final `down → up` completado; tarea pasa a `REVIEW` | `infra/migrations/`; salida real de `psql` documentada en TASKS/checklist |

## Cómo usar este documento

Al empezar una tarea, comprobar aquí el hito autorizado y en `docs/TASKS.md` que sus dependencias directas están `DONE`. Ningún estado `DONE` se declara sin aprobación del revisor, y ningún test/verificación se reporta sin evidencia ejecutada.
