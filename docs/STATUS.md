# STATUS.md — Tablero vivo

> Punto de entrada del estado actual. El detalle por tarea vive en `docs/TASKS.md`; el historial de cambios, en `docs/CHANGELOG.md`.

## Hito autorizado actualmente

**Hito 1 — `MP-002` → `MP-009`: completado, aprobado por revisión cruzada el `2026-11-19`, y fusionado a `main` por el propietario (`pedromaaz13`) el `2026-11-19`.** PR #1 (`mp-009-historical-export` → `main`), commit de merge `f567d3c`. Confirmado: `git merge-base --is-ancestor 8be1272 f567d3c` → `0` (el último commit de la cadena MP-009 es ancestro de `main`; nada quedó sin integrar).

```text
Cobertura: F1 (factibilidad) + F2 (contratos) + F3 (persistencia/colector) + F4 (calidad/histórico)
Objetivo de salida: colector idempotente validado + quality engine + histórico exportado y replayable.
Cadena: MP-002 → MP-003 → MP-004 → MP-005 → MP-006 → MP-007 → MP-008 → MP-009.
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007.
```

MP-001 está `DONE`: Codex aprobó la revisión cruzada y, conforme a ADR-0007, no fue necesario que la rama estuviera fusionada en `main` para que una tarea dependiente avanzara. La rama paralela `chore/mp-001-foundation` (bitácora administrativa parcial, superada por el registro completo de la cadena `mp-00X`, ver nota de proceso más abajo) y los 9 worktrees `mp-002` a `mp-009` se conservan intactos tal como exige el propietario — ninguno se ha borrado.

**Hito 2 autorizado por el propietario el `2026-11-19`: `MP-010` → `MP-015` ("Live Railway MVP").**

```text
Cobertura: F5 (geometría y topología) + F6 (motor de movimiento) + F7 (API) + F8 (frontend) + F9 (E2E/readiness)
Objetivo de salida: primera app local funcional mostrando la C5 en vivo — topología GTFS real, geometría OSM,
  motor de movimiento con cuatro estados, API /api/v1 propia, frontend React/MapLibre, E2E + CI.
Tabla ejecutor/revisor (fijada por el propietario, coherente con docs/TASKS.md):
  MP-010 Topología GTFS      → Ejecutor Codex   · Revisor Claude
  MP-011 Geometrías OSM      → Ejecutor Claude   · Revisor Codex
  MP-012 Motor de movimiento → Ejecutor Codex   · Revisor Claude
  MP-013 FastAPI             → Ejecutor Claude   · Revisor Codex
  MP-014 React/MapLibre      → Ejecutor Codex   · Revisor Claude
  MP-015 E2E y MVP readiness → Ejecutor Claude   · Revisor Codex
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007. Además, por instrucción explícita
  del propietario para este hito: ningún push/PR/merge se ejecuta sin solicitar autorización en el momento
  (revierte, para Hito 2, la autorización puntual ya consumida en el cierre de Hito 1 — ver AGENTS.md).
No se avanza fuera de MP-010→MP-015 sin nueva autorización explícita (p. ej. no se implementa la red completa
  de Cercanías Madrid en este hito — eso es Hito 3, solo backlog de planificación, ver docs/PLAN.md F10 y la
  bitácora de este documento).
```

### Política de selección de modelo (Hito 2, fijada por el propietario)

- **Modelo principal: Claude Sonnet, esfuerzo de razonamiento alto** — por defecto para coordinación en Orca, implementación ordinaria, desarrollo de API/frontend, tests automatizados y revisiones cruzadas rutinarias.
- **Escalado: Claude Opus, esfuerzo de razonamiento alto** — solo con justificación técnica concreta (geometría/arquitectura geoespacial compleja, resolución ambigua de topología ferroviaria, algoritmos de map-matching/movimiento, errores persistentes que Sonnet no resuelve, decisiones arquitectónicas de alto impacto, revisión avanzada de UX/rendimiento/arquitectura frontend). Nunca se escala solo porque una tarea "parece importante" sin evaluar primero si Sonnet basta.
- **Verificación empírica realizada el `2026-11-19` (no se asumió ni inventó ningún identificador):** `orca orchestration worker-start --help` confirma que `--model`/`--effort` son parámetros reales y soportados para lanzar un agente Claude (`--model` acepta "opaque provider model ids"; `--effort` requiere `--model`). El identificador verificado empíricamente para "Sonnet" es `sonnet` y para "Opus" es `opus` (documentado como ejemplo real por Orca: `--model opus --effort high`); el esfuerzo de razonamiento se pasa como `--effort high`.
- **Discrepancia señalada al propietario:** el encargo nombra "Claude Sonnet 5.5" / "Claude Opus 5.5 High" como modelos. El contexto de entorno de esta sesión solo confirma la existencia de **Sonnet 5** y **Opus 5** (además de Haiku 4.5) como los modelos Claude más recientes disponibles — no se ha podido verificar ningún identificador "5.5". Siguiendo la instrucción explícita de no inventar identificadores, los workers de Hito 2 se lanzan con `--model sonnet --effort high` (por defecto) y `--model opus --effort high` (escalado), que son los identificadores reales confirmados, no una invención de "5.5".
- Codex: se usa el modelo/nivel de razonamiento disponible más adecuado, priorizando razonamiento alto para geometría, movimiento, contratos e integración, conforme a los roles ya fijados en `docs/TASKS.md`.

## Auditoría independiente de preparación para integración

**OpenAI Codex — `2026-11-19`: APROBADA, sin bloqueantes reales para integrar `mp-009-historical-export` en `main`.** El estado auditado (`c8d3bd0`, antes de registrar esta entrada) contiene de forma lineal y sin merges todo MP-001 → MP-009: `git merge-base --is-ancestor 3e7b533 c8d3bd0` devuelve `0`, y el recorrido desde `origin/main` (`5b45227`) hasta `c8d3bd0` contiene los 23 commits esperados. Los 23 tienen autor y committer `Pedro Matute <pedromaaz13@gmail.com>` y ninguno incluye un trailer literal `Co-authored-by:`.

Evidencia reproducida de forma independiente:

- La rama paralela `chore/mp-001-foundation` se separa en `3e7b533` y añade cinco commits (`fac945c` → `15820ac`) que solo modifican `docs/STATUS.md`, `docs/TASKS.md` y `docs/CHANGELOG.md`. Su contenido es seguimiento administrativo hasta MP-005 en `REVIEW`; la autorización del Hito 1, sus condiciones operativas, los hallazgos y cierres de MP-002 → MP-005 ya están reflejados —con estado final y mayor detalle— en esta rama. No se encontró contenido único material cuya ausencia causase pérdida al integrar únicamente `mp-009-historical-export`.
- Worktrees muestreados limpios antes de registrar esta auditoría: clon original, `mp-004-fixtures`, `mp-007-collector` y `chore/mp-001-foundation`; este worktree también estaba limpio.
- Diff `origin/main..HEAD`: 95 ficheros (92 añadidos, `README.md` modificado y dos renombres `R100` hacia `docs/research/`), sin cachés, entornos virtuales ni temporales versionados. `git diff --check` solo informa de una línea en blanco final en cada una de las tres fixtures JSON; son avisos cosméticos y las pruebas que las parsean pasan.
- Suites ejecutadas realmente: contratos 31/31, fixtures 6/6, collector 9/9, quality 13/13 y snapshotter 5/5 — **64/64 en verde**. PostgreSQL conservó exactamente los recuentos `668/484/3/120/0` en `vehicle_position_observation` / `trip_update_observation` / `service_alert` / `source_ingestion_run` / `data_quality_event` antes y después; no quedó residuo de pruebas.
- Escaneo de secretos: no se encontraron claves, tokens, ficheros de entorno ni llaves privadas. La única contraseña es `madrid_pulse_local`, credencial de desarrollo local usada exclusivamente contra `127.0.0.1:5433`.
- Enlaces: 48 enlaces relativos Markdown comprobados en el repositorio, 0 rotos. `docs/TASKS.md` marca MP-001 → MP-009 como `DONE`; este documento declara el Hito 1 completado y prohíbe iniciar MP-010 sin autorización nueva; `docs/CHANGELOG.md` conserva el historial de las nueve tareas.

**Veredicto de integración:** `mp-009-historical-export` está preparada para que el propietario la integre en `main`; no se identificaron omisiones, pérdida documental, problemas de autoría ni bloqueantes técnicos. Los tres avisos de whitespace en fixtures son los únicos hallazgos abiertos y no son bloqueantes.

## Resolución de DEC-015 (mecánica de convergencia de ramas, antes de MP-012)

**Resuelto el `2026-11-19`, documentado aquí y en `docs/DECISIONS.md`/`AGENTS.md`.** La pregunta abierta era qué rama usar como base y cómo integrar las demás cuando una tarea depende de varias ramas potencialmente distintas (caso previsto: MP-012 depende de MP-008, MP-010 y MP-011).

Con Hito 1 ya fusionado a `main`, el caso concreto de MP-012 **deja de requerir una fusión real de ramas divergentes**: MP-008 ya es ancestro de `main` (se fusionó como parte de la cadena MP-002→MP-009). Si MP-010 y MP-011 se ramifican a partir de `main` (o de una rama que a su vez parte de `main`, como esta misma `chore/hito-2-coordination`), entonces la cadena resultante — `main → MP-010 → MP-011` — ya contiene a MP-008 de forma transitiva. MP-012 puede ramificar simplemente desde la rama de MP-011 sin ningún `git merge` real: sus tres dependencias (MP-008, MP-010, MP-011) son todas ancestros de ese punto.

**Mecanismo general (para este y futuros casos de convergencia múltiple), registrado en `AGENTS.md`:** antes de abrir el worktree de una tarea con varias dependencias directas, comprobar con `git merge-base --is-ancestor <dependencia> <candidata-a-base>` si cada dependencia ya es ancestro de la rama candidata a base (normalmente la más "profunda" en la cadena). Si todas lo son, se ramifica directamente desde esa rama — no hace falta fusión. Solo si una dependencia **no** es ancestro de la otra (p. ej. dos ramas que de verdad divergieron sin que ninguna absorbiera a la otra vía `main`) se necesita una fusión real (`git merge` de la rama no-ancestro sobre la rama base elegida, documentando el resultado y cualquier conflicto en `docs/STATUS.md` antes de continuar). Este hito no necesita ese caso general porque la estructura tras el merge de Hito 1 ya lo evita.

## Tarea actual

**MP-009 — Exportador histórico (Parquet particionado)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-009-historical-export`, ramificada desde `mp-008-quality-engine` (MP-008 `DONE`)

### Checklist de MP-009

- [x] `services/snapshotter/export.py`: DuckDB como único motor (lee PostgreSQL vía `ATTACH ... TYPE POSTGRES`, escribe Parquet nativo); sin `pandas`/`pyarrow` adicionales (DEC-021).
- [x] Partición `date=YYYY-MM-DD/hour=HH` siempre calculada sobre Europe/Madrid, nunca UTC directo — ver hallazgo real abajo.
- [x] **Hallazgo real:** los datos del soak test de MP-007 (`23:31:42 UTC` 18-nov) pertenecen al día de servicio **19-nov** en Europe/Madrid (CET, UTC+1) — exactamente el error que `docs/DATA_MODEL.md` ya advertía. 3 tests de regresión puros (incluido CEST/verano) en `test_export.py`.
- [x] Test de replay real (`test_export_replay.py`): día de prueba conocido, COMPROMETIDO (no `rollback()`, DuckDB usa conexión `libpq` propia), exportado y verificado sin pérdida; limpieza explícita en `finally`.
- [x] Exportación real completa del día `2026-11-19` (datos reales, no fixtures): 1272 filas (668+484+120+0+0), ~76 KB ZSTD particionado; releído con consulta DuckDB independiente, recuento exacto.
- [x] `services/snapshotter/gold.py`: resumen diario por núcleo (1 fila para Madrid: 668 posiciones/24 vehículos, 484 actualizaciones/24 viajes). **Limitación deliberada documentada:** no calcula `daily_line_metrics`/`station_daily_metrics` (requieren resolución `route_id`/`station_id` diferida a MP-010, ADR-0009) — ver DEC-021.
- [x] CLI (`python -m services.snapshotter YYYY-MM-DD`) probado de punta a punta contra PostgreSQL real.
- [x] 64 tests reales en verde: 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter.
- [x] Identidad Git verificada; contenedor `madrid-pulse` detenido al finalizar la implementación (volumen real conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_d2b95955a73a`): no aprobada** — reejecutó las 64 pruebas, confirmó la conversión Europe/Madrid y el export/gold reales, y encontró un bloqueante real: las 3 `service_alert` reales (ingeridas el 19-nov vía `ingestion_run` 78) desaparecían del export de ese día porque `export.py` particionaba `service_alert` por `active_period_start` (ventana de vigencia del aviso) en vez de por cuándo se observó — esa tabla no tiene columna propia de observación.
- [x] Corregido uniendo `service_alert` a `source_ingestion_run` y usando `started_at` de esa ejecución; verificado revirtiendo el fix (el test ampliado falla `0 != 1` exactamente como reportó Codex) y restaurándolo (pasa). Reexportado el día real: `service_alert` pasa de 0 a 3 filas. Test de replay ampliado para cubrir las 5 tablas (antes solo 2).
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_095ae1499806`): APROBADA** — 2/2 tests de replay ampliados en verde contra PostgreSQL real; limpieza de las 5 tablas confirmada (`vp/tu/alert/dqe/run = 0` tras el test). Export real independiente: 668/484/**3**/120/0; los tres avisos esperados aparecen en Parquet ligados al run 78. Diff, identidad Git y aislamiento de contenedores correctos.

### Resultado y límites

El exportador mueve de verdad datos reales de PostgreSQL a Parquet particionado sin pérdida, con dos trampas reales encontradas y corregidas con evidencia, no solo teóricas: el huso horario Europe/Madrid vs. UTC, y la semántica temporal de `service_alert` (vigencia vs. observación). El agregado gold queda deliberadamente acotado a núcleo (no a línea/estación) hasta que MP-010 resuelva las FK necesarias — documentado, no improvisado.

### Bloqueos

Ninguno: el bloqueante real de la primera revisión de Codex (semántica temporal de `service_alert`) está corregido y re-verificado independientemente; la limitación de alcance del agregado gold está documentada y no bloquea el criterio de aceptación real (replay sin pérdida de la capa raw).

### Siguiente paso

MP-009 y el Hito 1 (`MP-002` → `MP-009`) están completos. El worktree queda listo para revisión del propietario; no se inicia MP-010 ni otro hito hasta que el propietario lo autorice expresamente.

## Tareas cerradas de la cadena

**MP-008 — Quality engine**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-008-quality-engine`, ramificada desde `mp-007-collector` (MP-007 `DONE`)

### Checklist de MP-008

- [x] Cinco flags del `CHECK` de MP-006 implementados: `stale`, `implausible_speed`, `missing_id`, `duplicate_snapshot`, `clock_anomaly`.
- [x] Reglas puras en `packages/quality/engine.py`, separadas de red/BD; capa PostgreSQL en `packages/quality/db.py`.
- [x] Umbrales calibrables y nombrados: stale 180s, velocidad 200km/h, feed congelado 180s, drift de reloj 300s; documentados como puntos de partida, no contrato de Renfe.
- [x] Velocidad implícita calculada por Haversine entre posiciones consecutivas del mismo vehículo, sin usar `speed_kmh` de origen.
- [x] `duplicate_snapshot` opera sobre el hash completo del feed sostenido en el tiempo; dos polls normales iguales no disparan la regla.
- [x] Eventos y `quality_flags` persistidos dentro de la misma transacción atómica del colector; flags de feed no se atribuyen falsamente a una observación.
- [x] 13 tests de calidad: al menos disparo + falso positivo por cada regla, rollover UTC de medianoche y dos integraciones PostgreSQL reales con rollback.
- [x] Suite completa ejecutada: **59/59** (31 contratos + 6 fixtures + 9 colector + 13 calidad), todas `OK`.
- [x] Casos anómalos ausentes de las fixtures reales marcados explícitamente como sintéticos; no se presentan como observados.
- [x] Contenedor `madrid-pulse-postgres-1` dejado levantado para la revisión, volumen real conservado; contenedores `*-traza-app` verificados intactos.
- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Reproducidas
  59/59 pruebas contra el mismo PostgreSQL real (668/484/3/120 registros del
  soak test de MP-007, intactos). Revisado el diseño (reglas puras vs.
  persistencia, transacción atómica, reutilización del patrón `id DESC` de
  MP-007 en el historial de calidad).
  **Hallazgo empírico documentado, no bloqueante:** al repetir 117 pares
  reales de posiciones consecutivas del soak test contra
  `check_implausible_speed`, 12/117 (~10%) dispararon con velocidades
  implícitas de 246–787 km/h. Inspección de la secuencia del vehículo
  `21053` confirmó que son saltos reales entre filas ya almacenadas (20-40s,
  varios km), no un error de cálculo — indica que Renfe actualiza posición
  en saltos más gruesos que el cadencia de poll, no como GPS continuo.
  Registrado para considerarlo al calibrar el umbral en MP-012 (ya
  documentado como "a calibrar, no verdad de diseño").

### Resultado y límites

El motor queda integrado antes de persistir para aprovechar los objetos canónicos de MP-005 y conservar atomicidad con MP-007, sin duplicar el colector. Las reglas geométricas `off_track`, `backward_jump` y `station_skip_anomaly` siguen diferidas a MP-012: requieren map-matching y no caben en el `CHECK` actual.

### Bloqueos

Ninguno. Los umbrales requieren calibración operativa futura (ver hallazgo de `implausible_speed` arriba), tal como exige `docs/DATA_QUALITY.md`, pero no bloquean el punto de partida probado.

### Siguiente paso

MP-008 está `DONE`. MP-009 puede ramificar desde `mp-008-quality-engine` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-007 — Collector idempotente**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-007-collector`, ramificada desde `mp-006-postgis-schema` (MP-006 `DONE`)

### Checklist de MP-007

- [x] `services/collector/http_client.py`: `fetch_with_retry` con backoff exponencial y timeout, solo `urllib` (sin dependencia nueva para HTTP).
- [x] `services/collector/db.py`: capa de acceso a PostgreSQL (MP-006); corregido un bug real de transacciones (ver más abajo) para que cada ciclo se comprometa como unidad atómica.
- [x] `services/collector/collector.py`: `run_cycle` = fetch → parse → filtro de alcance (núcleo Madrid, ADR-0008) → dedupe (ADR-0010) → persist, con el ciclo entero en una sola transacción.
- [x] `services/collector/__main__.py`: bucle de polling infinito, un feed fallido no detiene el colector completo.
- [x] `docs/adr/0010-dedup-strategy.md` (nuevo, `Propuesto`): hash completo de la entidad comparado contra la última fila almacenada por clave de entidad; sin `seen_count`.
- [x] 46 tests reales en verde (31 contratos + 6 fixtures + 9 colector); 5 de los 9 del colector son integración real contra PostgreSQL (no mocks de BD).
- [x] **Soak test real de 20 minutos** contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión `psql` nueva tras el proceso.
- [x] **3 hallazgos reales corregidos** (feed en vivo, no cubiertos por fixtures de MP-003/MP-004): `trip_id` de refuerzo `SPECIAL_<núcleo>_<resto>`, `stopTimeUpdate[].arrival` sin `delay`, respuesta real sin la clave `entity`. Los tres con test de regresión. Detalle en `docs/research/MP-003-probe-findings.md` §10.
- [x] **1 bug de transacciones corregido antes de producción:** `with conn.transaction()` por `INSERT` individual, con una conexión de larga duración, dejaba `vehicle_position_observation` sin comprometer mientras `source_ingestion_run` sí persistía — detectado verificando con una conexión nueva, no confiando en la ausencia de excepción. Corregido centralizando la transacción en `run_cycle`.
- [x] **Hallazgo de alcance documentado, no bloqueante** (DEC-020): el filtro descarta por núcleo (Madrid), no todavía por línea C5 específica (ADR-0001 `Aceptado`) — acotar a C5 requiere la resolución `trip_id`→`route_id` de MP-010.
- [x] Identidad Git verificada en cada commit; contenedor `madrid-pulse` detenido al finalizar (volumen con los datos reales del soak test conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_a674a371ce8a`): no aprobada** — reejecutó las 45 pruebas, consultó el feed vivo (el snapshot puntual no contenía `SPECIAL_`/`ADDED`), confirmó esos casos en el volumen real conservado del soak test y encontró un bloqueante real: `latest_payload_hash` sin desempate (`ORDER BY observed_at DESC` solo) producía una fila duplicada real en su reproducción de 3 ciclos (`(1, 6)` en vez de `(0, 7)` en el tercer ciclo) cuando dos filas de la misma entidad comparten `observed_at`.
- [x] Corregido con `id DESC` como desempate secundario en las 3 consultas de `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix temporalmente y confirmando que el nuevo test (`test_tied_observed_at_does_not_break_dedup_on_third_cycle`) falla exactamente como reportó Codex y pasa con el fix restaurado. 46 tests en verde.
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_801574c4ef71`): aprobada** — inspeccionó el diff de `3f83699`, ejecutó el test de regresión específico contra PostgreSQL real (`OK`) y repitió las 46 pruebas completas (31 contratos + 6 fixtures + 9 colector, todas `OK`). Confirmado que `id DESC` resuelve el empate en las tres consultas de deduplicación. **APROBADO.**

### Resultado y límites

El colector ingiere y deduplica de verdad contra el feed en vivo de Renfe, con evidencia de ejecución sostenida de 20 minutos sin errores. No resuelve `trip_id` contra el GTFS estático (diferido a MP-010 por ADR-0009) ni acota a C5 específicamente (DEC-020) — ambas limitaciones ya estaban previstas y documentadas antes de empezar la tarea, no son hallazgos de última hora sin plan.

### Bloqueos

Ninguno. El bloqueante real encontrado por la primera revisión de Codex (dedup no determinista) está corregido y verificado independientemente; los dos puntos de alcance documentados no bloquean el cierre de MP-007 según los criterios de aceptación de `docs/TASKS.md`.

### Siguiente paso

MP-007 está `DONE`. MP-008 puede abrir su worktree desde `mp-007-collector` conforme al hito autorizado y al modelo de autonomía de ADR-0007, sin esperar merge a `main`.

**MP-006 — Esquema PostgreSQL/PostGIS v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

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
- [x] Revisión independiente de Claude Code (2026-11-19): **APROBADA**. Reproducido
  el ciclo completo de forma propia (no solo verificado el reporte de Codex):
  rollback necesario primero porque el volumen ya tenía el esquema cargado, luego
  `up → datos de prueba → 3 duplicados rechazados → down → up` otra vez, todo
  `exit 0`/`exit 1` según corresponde. GIST confirmados en `vehicle_position_observation.geom`
  y `station.geom`. Confirmada la ausencia real de `effect`/`cause`/`header_text`
  y `current_stop_sequence`. Suites de regresión reejecutadas de forma
  independiente (23/23 y 6/6). `check_links.py`: 46 enlaces, ninguno roto.
  Identidad Git verificada. Contenedores `*-traza-app` intactos.
  **Hallazgo (corregido en esta misma revisión):** este documento había
  reemplazado el registro completo de MP-005 en "Tarea actual" por el de MP-006
  sin archivarlo primero aquí, rompiendo el patrón de MP-002/MP-003/MP-004 —
  corregido moviendo el registro íntegro de MP-005 a esta sección.

### Resultado y límites

SQL plano permite auditar el DDL inicial sin introducir todavía un framework de
migraciones. El rollback elimina el esquema de aplicación pero no usa
`DROP EXTENSION ... CASCADE`: las extensiones PostGIS dependientes vienen
preinstaladas por la imagen y no pertenecen a esta migración.

### Bloqueos

Ninguno.

### Siguiente paso

MP-006 está `DONE`. MP-007 puede ramificar desde `mp-006-postgis-schema` sin
esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-005 — Contrato canónico interno**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-005-contrato-canonico`, ramificada desde `mp-004-fixtures` (MP-004 `DONE`)

### Checklist de MP-005

- [x] `packages/contracts/raw.py`: modelos Pydantic que reflejan exactamente el JSON bruto observado en MP-003/MP-004 (sin inventar campos); acepta campos nuevos no verificados sin fallar (`extra="ignore"`).
- [x] `packages/contracts/nucleo.py`: tabla de prefijos de núcleo verificada en MP-003, con `is_madrid`/`nucleo_name`.
- [x] `packages/contracts/canonical.py`: `VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth` — UTC siempre, dato ausente = `None` nunca `0`, `nucleo_prefix` derivado como `computed_field` (no aceptado como entrada independiente).
- [x] `packages/contracts/normalize.py`: funciones puras `raw → canonical`, sin red ni base de datos.
- [x] 23 tests reales ejecutados (`python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`) → `OK`: parseo contra fixtures reales, normalización (incluido el test de colisión núcleo/C5 a nivel de contrato canónico), sintéticos (JSON Schema, rechazo de datos inválidos, caso multi-núcleo no observado), enforcement UTC y regresión de campos `raw` no observados.
- [x] **Hallazgo:** `docs/DATA_MODEL.md` asumía `speed_kmh`/`bearing`/`current_stop_sequence` y `effect`/`cause`/`header_text` de alertas que el feed real NUNCA emite (verificado contra ~800 entidades combinadas de MP-003/MP-004). Corregido `docs/DATA_MODEL.md`, `docs/DATA_QUALITY.md` (nota sobre cómo calcular `implausible_speed` sin un campo de origen), registrado DEC-018/ADR-0009 (`Propuesto`).
- [x] Autocorregido antes de delegar: una edición introdujo una fila duplicada en `docs/DATA_QUALITY.md` (`off_track` repetida) — detectado y corregido en la misma ronda, sin necesitar que Codex lo señalara.
- [x] Primera revisión independiente de Codex (dispatch `ctx_ea1d5cf46d74`): **no aprobada** — reejecutó la suite (17/17 OK en su entorno) y auditó el diff campo a campo. 3 bloqueantes + 1 menor:
  - **Bloqueante 1:** `RawActivePeriod.end` no tenía el comentario de "campo opcional no observado" que sí llevan los demás campos documentados tras el hallazgo de MP-005 — se corrigió **añadiendo un comentario**, lo que resultó insuficiente (ver 2ª ronda).
  - **Bloqueante 2:** el esquema canónico documentaba "UTC siempre" pero no lo exigía — un `datetime` naive o con offset no UTC pasaría la validación sin error. Corregido con `field_validator` en los 4 modelos (`VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth`), con 5 tests nuevos que prueban el rechazo real.
  - **Bloqueante 3:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato original (`deep-research-report.md`) queda contradicho por esta verificación — añadida la fila correspondiente sin editar el documento de investigación congelado.
  - **Menor:** `ADR-0009` decía erróneamente que Codex podía promover el ADR a `Aceptado` (contrario a `AGENTS.md`/ADR-0007: solo el propietario puede) — corregido; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos) — corregido.
- [x] Segunda revisión independiente de Codex (dispatch `ctx_ded900b82f20`): **no aprobada** — señaló correctamente que un comentario no resuelve una contradicción: `raw.py:1-9` declara explícitamente que el módulo no debe contener campos no observados, y `RawActivePeriod.end` seguía ahí. Corregido de verdad esta vez: `end` **eliminado** de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; añadido un test de regresión (`test_raw_active_period_has_no_unobserved_end_field`) que falla si alguien lo reintroduce sin verificarlo, incluso si el JSON de origen lo trae (se ignora por `extra="ignore"`). 23 tests en total.
- [x] Tercera revisión independiente de Codex: **APROBADA**, sin hallazgos abiertos — reejecutó 23/23 tests; confirmó independientemente que `RawActivePeriod.model_fields == {"start"}`, que un `end` extra se ignora sin convertirse en atributo, que fechas naive y `+02:00` se rechazan mientras UTC se acepta, y que trazabilidad, ADR, enlaces, secretos y whitespace son coherentes.

### Resultado y límites

El contrato canónico se valida contra datos reales (MP-004) y sintéticos. La separación `raw`/`canonical` evita que un cambio futuro del feed de Renfe se propague directamente al resto del sistema sin pasar por una capa de normalización explícita. Los hallazgos de campos no observados (ADR-0009) son correcciones al modelo candidato de MP-001, no contradicciones nuevas sin resolver.

### Bloqueos

Ninguno.

### Siguiente paso

MP-005 está `DONE`. MP-006 pudo ramificar desde esta rama sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

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
| `2026-11-19` | MP-006 | Revisión independiente de Claude Code: ciclo `up/down/up` reproducido desde cero en el worktree, 3 `UNIQUE` rechazados de verdad, 2 `GIST` confirmados, ausencia de campos no observados verificada, suites de regresión reejecutadas (23/23, 6/6), 46 enlaces sin romper. **APROBADA**. Hallazgo de proceso: `STATUS.md` había perdido el checklist completo de MP-005 al no archivarlo antes de escribir el de MP-006; corregido en la misma revisión. Tarea pasa a `DONE` | commit `30507cf`; commit de revisión pendiente |
| `2026-11-18T23:31Z–23:51Z` | MP-007 | Soak test real de 20 min contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 insertadas/304 dedup/2622 fuera de alcance; durabilidad confirmada con conexión `psql` nueva | `services/collector/`; log del soak test |
| `2026-11-18` | MP-007 | 3 hallazgos reales corregidos (trip_id `SPECIAL_`, `arrival` sin `delay`, `entity` ausente) y 1 bug de transacciones corregido antes de producción (commits parciales con conexión de larga duración); tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `packages/contracts/nucleo.py`; `packages/contracts/raw.py`; `services/collector/db.py` |
| `2026-11-19` | MP-007 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (dedup no determinista por `observed_at` empatado, fila duplicada real en reproducción de 3 ciclos) | dispatch `ctx_a674a371ce8a` |
| `2026-11-19` | MP-007 | Corregido con `id DESC` como desempate en `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix y confirmando que el test de regresión reproduce exactamente el fallo reportado y pasa con el fix restaurado; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-007 | Segunda revisión independiente de Codex: test específico y suite completa (46/46) reejecutados contra PostgreSQL real; fix de desempate confirmado. **APROBADA**. MP-007 pasa a `DONE` | dispatch `ctx_801574c4ef71`; commit de revisión pendiente |
| `2026-11-19` | MP-008 | Motor de cinco reglas implementado e integrado transaccionalmente en el colector; umbrales calibrables documentados y reglas geométricas diferidas explícitamente a MP-012 | `packages/quality/`; `services/collector/` |
| `2026-11-19` | MP-008 | Suite completa ejecutada contra PostgreSQL real: 59/59 (31 contratos + 6 fixtures + 9 colector + 13 calidad), incluidos 10 casos mínimos disparo/no-disparo, medianoche UTC y persistencia/feed congelado con rollback. Tarea pasa a `REVIEW` para Claude Code | `packages/quality/tests/`; dispatch `ctx_63638731fde4` |
| `2026-11-19` | MP-008 | Revisión independiente de Claude Code: 59/59 reproducidas contra el mismo PostgreSQL real; diseño auditado. Hallazgo empírico no bloqueante: 12/117 pares reales de posiciones consecutivas del soak test disparan `implausible_speed` (246–787 km/h) — saltos reales de posición, no bug de cálculo; registrado para calibración en MP-012. **APROBADA**. Tarea pasa a `DONE` | commit `c3db20b`; commit de revisión pendiente |
| `2026-11-19` | MP-009 | Exportador DuckDB implementado; hallazgo real de huso horario (Europe/Madrid vs. UTC) encontrado y corregido antes de delegar; export real del 19-nov (1272 filas, ~76 KB ZSTD) y test de replay verificados; tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `services/snapshotter/`; commit `0119c6a` |
| `2026-11-19` | MP-009 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (3 `service_alert` reales desaparecían del export por particionar por `active_period_start` en vez de por observación real vía `ingestion_run_id`) | dispatch `ctx_d2b95955a73a` |
| `2026-11-19` | MP-009 | Corregido uniendo `service_alert` a `source_ingestion_run`; replay ampliado a las 5 tablas; verificado revirtiendo el fix (falla `0≠1` como reportó Codex) y restaurándolo; reexportado el día real: `service_alert` pasa de 0 a 3; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-009 / Hito 1 | Segunda revisión independiente de Codex aprobada: replay ampliado 2/2, limpieza completa, export real 668/484/3/120/0 y tres alertas confirmadas en Parquet. MP-009 pasa a `DONE`; Hito 1 (`MP-002` → `MP-009`) completo, pendiente de decisión del propietario sobre el siguiente hito | dispatch `ctx_095ae1499806` |
| `2026-11-19` | Hito 1 | Auditoría independiente de Codex (dispatch no registrado como `ctx_` en esta rama, ver worktree `mp-009-historical-export`): **APROBADA**, sin bloqueantes. Propietario crea PR #1 (`mp-009-historical-export` → `main`) y lo fusiona él mismo | PR #1; commit de merge `f567d3c` |
| `2026-11-19` | Hito 2 | Propietario autoriza explícitamente `MP-010` → `MP-015` ("Live Railway MVP"), fija la tabla ejecutor/revisor, la política de selección de modelo y los límites de autonomía (sin push/PR/merge sin autorización puntual; identidad Git exclusiva del propietario; sin coautores de agente) | mensaje de autorización del propietario, `2026-11-19` |
| `2026-11-19` | Hito 2 | Sincronización inicial: `git fetch`/`git pull --ff-only` confirma `main` local al día con `origin/main`; verificado que `8be1272` (tope de `mp-009-historical-export`) es ancestro de `f567d3c`, sin commits perdidos. Verificación empírica (no asumida) de que `orca orchestration worker-start --model/--effort` son parámetros reales para Claude; identificadores confirmados `sonnet`/`opus` (no existe un "5.5" verificable en este entorno) | `agent-context.json`; `worker-start --help` |
| `2026-11-19` | Hito 2 | DEC-015 resuelto: con Hito 1 ya en `main`, la convergencia de MP-012 (MP-008+MP-010+MP-011) no requiere `git merge` real — basta ramificar la cadena MP-010→MP-011 desde una rama que ya contenga a `main` (y por tanto a MP-008) como ancestro; mecanismo general documentado en `AGENTS.md` para casos futuros con divergencia real | este documento; `AGENTS.md` |
| `2026-11-19` | Hito 2 | ADR-0011 (`Propuesto`) redactado: distingue el piloto técnico de Hito 2 (C5) del objetivo de primera versión pública (toda la red de Cercanías Madrid), sin reescribir ADR-0001 (`Aceptado`) — amplía su alcance de implementación sin contradecir su decisión ya aceptada | `docs/adr/0011-public-scope-vs-technical-pilot.md` |
| `2026-11-19` | Hito 2 | Worktrees de MP-010 (ejecutor Codex) y, tras su cierre, MP-011 (ejecutor Claude Code) preparados ramificando desde esta rama de coordinación (`chore/hito-2-coordination`, a su vez ramificada desde `main`) | `docs/TASKS.md` |

## Cómo usar este documento

Al empezar una tarea, comprobar aquí el hito autorizado y en `docs/TASKS.md` que sus dependencias directas están `DONE`. Ningún estado `DONE` se declara sin aprobación del revisor, y ningún test/verificación se reporta sin evidencia ejecutada.
