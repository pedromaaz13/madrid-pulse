# CHANGELOG.md

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Solo se registran cambios realmente realizados y verificables — nunca funcionalidad planeada o supuesta.

## [Unreleased]

### MP-012 — Motor de movimiento v1

#### Added
- `packages/movement/`: motor genérico con estados `observed`/`estimated`/`stale`/`scheduled`, contrato tipado directo para MP-013 (`confidence`, `age_s`, `source`, progreso, timestamps y anomalías) y umbrales configurables.
- Pipeline completo de ADR-0004 sobre APIs existentes: resolución literal GTFS, map-matching OSM, perfil de horario con horas >24/día de servicio, offset temporal, interpolación limitada y fallback a la última muestra plausible.
- `off_track`, `backward_jump` y `station_skip_anomaly` calculados y expuestos en cada resultado; `implausible_speed` refinado con distancia map-matched.
- ADR-0012 (`Propuesto`)/DEC-026: el motor vive en `packages/movement`, separado de geometría y reglas sobre observaciones crudas. `packages/geo.point_at_arc_length` añadido como primitiva geométrica genérica.

#### Calibrated
- Defaults `60s/180s` mantenidos: con `vehicle_positions` cada ~20–22 s equivalen a ~3/~8 polls perdidos.
- Límite físico de estimación 160 km/h y aceleración 1,2 m/s² separados del filtro de discontinuidad de fuente 900 km/h. El soak real midió un máximo map-matched de 666,4 km/h, coherente con los saltos crudos 246–787 km/h ya encontrados por MP-008.

#### Verified
- 90/90 tests en verde: 11 movement (10 deterministas + integración real), 7 GTFS, 8 geo, 31 contratos, 6 fixtures, 9 collector, 13 quality y 5 snapshotter.
- Volumen PostgreSQL real consultado en solo lectura: 668 posiciones antes/después, 177 a ≤200 m del corredor; recuentos finales `668/484/3/120/0` sin residuo.
- Cambio de día de servicio/horas GTFS >24, UTC estricto, transición de estados, fuentes distintas, saltos de estación, retrocesos, off-track y velocidades imposibles cubiertos por test.

### MP-011 — Prototipo de geometría ferroviaria sobre OSM

#### Added
- `packages/geo/overpass.py`: cliente Overpass API genérico (por id de relación o `ref`/`network`), solo `urllib`.
- `packages/geo/corridor.py`: encadena los `ways` de vía de una relación OSM en el orden declarado, uniendo por nodo extremo compartido; registra huecos reales como `ChainGap` y mantiene cada tramo continuo (`Corridor.segments`) separado para que ningún cálculo geométrico fabrique una unión a través de un hueco.
- `packages/geo/geometry.py`: Haversine real + proyección punto-polilínea sin `shapely`/`pyproj`.
- `packages/geo/tools/fetch_fixture.py` y `tools/render_preview.py`: descarga/congela geometría real y genera un SVG de depuración reproducible (un `<polyline>` por tramo continuo).
- Fixture real de 4 relaciones OSM de C5 Madrid con checksum (4 SHA-256) y atribución ODbL; 8 tests contra ella.

#### Found
- La variante base de 6 estaciones de la ruta corta del GTFS (`10T0047C5`, sin Atocha) no tiene relación OSM propia: es una subsecuencia **contigua** real de paradas de la ruta larga, confirmado por comparación literal de IDs. Una variante real distinta del mismo `route_id` (7 estaciones, con Atocha antepuesta) proyecta en orden monótono sobre el mismo corredor pero **no** es contigua — omite 4 paradas intermedias reales.
- Las relaciones OSM `3418148`/`3418149` ("Fuenlabrada → Atocha → Móstoles-El Soto") son la ruta larga truncada en Fuenlabrada y no coinciden con el patrón real de 6 estaciones de la ruta corta — variante real documentada, no usada.
- `usage=main` (30 `ways`) / `usage=branch` (60 `ways`) en la vía: trazado troncal potencialmente compartido con otras líneas de Cercanías vs. ramal específico de C5 — no verificado qué otras líneas comparten el tramo.
- "C5"/"C-5" colisiona también en OSM entre núcleos (Asturias, Sevilla, Cantabria, Valencia, Madrid), igual que ya documentó ADR-0008/DEC-017 para el GTFS de Renfe.
- El endpoint público de Overpass devolvió `502 Gateway Timeout` por capacidad varias veces durante la descarga real; reintentos con pocos segundos de espera tuvieron éxito.

#### Verified
- 79/79 tests en verde: 8 geo nuevos + 71 de regresión (7 GTFS, 31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL.
- Las 4 relaciones direccionales encadenan sus `ways` de vía sin huecos; las 23 estaciones reales de la ruta larga (ambos sentidos) proyectan en orden monótono con distancia máxima real de 63,7 m.
- Evidencia visual real: SVG renderizado y revisado en navegador (Chrome DevTools MCP, captura completa) — forma real de la C5 reconocible, estaciones sin saltos sobre la vía.
- La lógica de `corridor.py`/`geometry.py`/`overpass.py` no contiene el literal de la línea piloto (test de regresión).

#### Fixed after Codex review (first round, blocking)
- `build_corridor` registraba `ChainGap` pero seguía concatenando ambos `ways` en una única `polyline`, así que `project_station`/`corridor_length_m` fabricaban un segmento recto sobre un hueco real (repro de Codex: `distance_m=0.0` en el centro de un hueco sintético). Corregido con `Corridor.segments` (tramos realmente continuos, separados en cada hueco); verificado revirtiendo el fix y confirmando que el nuevo test de regresión falla exactamente como describió Codex y pasa con el fix restaurado. `render_preview.py` corregido en paralelo para dibujar un `<polyline>` por tramo.
- Documentación corregida: recuento de tests (8/79, no 7/78); la variante de 7 estaciones de `10T0047C5` deja de describirse como "subsegmento contiguo" (solo es monótona); 4 SHA-256 añadidos a `tests/fixtures/osm_c5_real/MANIFEST.md` y verificados contra los ficheros reales.

### MP-010 — Topología GTFS C5

#### Added
- `packages/gtfs/`: parser en streaming de las seis tablas reales del GTFS estático, selección genérica por IDs/red/nombre corto, agrupación de variantes por `(network_id, short_name)` y API de resolución literal `trip_id` → `route_id` y `stop_id` → `stop_sequence`.
- Validador de referencias, secuencias, shapes y patrones de recorrido; fixture real reducida y reproducible con checksum/licencia; 7 tests contra esa fixture.

#### Found
- La descarga oficial del `2026-11-19` contiene para C5 Madrid 5 rutas, 8.160 trips, 23 estaciones, 165.205 stop_times, 630 puntos de shape, 30 servicios y 14 patrones de recorrido. `10T0035C5` aporta 8 trips pero ningún stop_time.
- `trips.txt` no contiene `direction_id`; la dirección real disponible se valida por el orden de `stop_sequence` y `shape_id`. No se inventó la columna ni recorrido para los huérfanos.

#### Verified
- 71/71 tests en verde: 7 GTFS nuevos + 64 regresiones (31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL. Parser ejecutado además contra el ZIP oficial completo: validación válida, 0 errores, 14 patrones y 8 huérfanos informados.
- Las cinco variantes permanecen separadas y agrupables; los recorridos completos y cortos incluyen sus pares inversos reales. La lógica de parser/resolución no contiene el literal de la línea piloto.

#### Independent review (approved)
- Claude Code auditó `add8aa6`: código íntegro de `packages/gtfs/` leído, 71/71 tests reejecutados de forma propia (subiendo/bajando el contenedor `madrid-pulse` él mismo), recuentos reales `668/484/3/120/0` confirmados idénticos antes y después de los tests, ausencia del literal `"C5"` en `parser.py`/`topology.py` verificada por lectura directa (reforzada por el test de regresión que lo impone), identidad Git y enlaces a ADR-0011/DEC-022/DEC-023 correctos. MP-010 queda `DONE`.

### MP-009 — Exportador histórico (Parquet particionado)

#### Added
- `services/snapshotter/export.py`: DuckDB como único motor para exportar las cinco tablas "hot" de PostgreSQL a Parquet particionado `date=YYYY-MM-DD/hour=HH`, comprimido ZSTD. Sin `pandas`/`pyarrow` adicionales (DEC-021).
- `services/snapshotter/gold.py`: resumen diario inicial por núcleo (`nucleo_prefix`), partición `date=YYYY-MM-DD`.
- `services/snapshotter/__main__.py`: CLI `python -m services.snapshotter YYYY-MM-DD`.
- 5 tests nuevos: 3 puros de límites de día de servicio (incluido CEST/verano) y 2 de replay real contra PostgreSQL.

#### Found
- Los datos reales del soak test de MP-007 (`23:31:42 UTC` del 18-nov-2026) pertenecen al día de servicio **19-nov** en Europe/Madrid (CET, UTC+1 en noviembre) — leer la fecha UTC directamente habría exportado esas filas al día equivocado, exactamente el error que `docs/DATA_MODEL.md` ya advertía. Corregido convirtiendo siempre a `Europe/Madrid` antes de calcular los límites del día de servicio y la partición.

#### Verified
- Exportación real completa del día `2026-11-19` (datos reales del soak test, no fixtures): 1272 filas (668 posiciones + 484 actualizaciones + 120 ejecuciones de ingesta), ~76 KB comprimidos; releído con una consulta DuckDB independiente, recuento exacto sin pérdida.
- Test de replay real: día de prueba conocido insertado y COMPROMETIDO (no `rollback()` — DuckDB usa su propia conexión `libpq`), exportado, verificado fila a fila, y limpiado explícitamente (`finally`).
- Suite completa: 64/64 pruebas en verde (31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter).

#### Fixed after Codex review (first round, blocking)
- `services/snapshotter/export.py`: `service_alert` no tiene columna propia de observación/recepción; se particionaba por `active_period_start` (la ventana de VIGENCIA del aviso), por lo que 3 alertas reales ingeridas el 19-nov desaparecían de ese día si su vigencia caía en otra fecha. Corregido uniendo `service_alert` a `source_ingestion_run` (vía `ingestion_run_id`) y usando `started_at` de esa ejecución como el momento de observación real. `test_export_replay.py` ampliado para cubrir las 5 tablas (antes solo `vehicle_position_observation`/`trip_update_observation`); verificado revirtiendo el fix (falla `0 ≠ 1` exactamente como reportó Codex) y restaurándolo. Reexportado el día real: `service_alert` pasa de 0 a 3 filas.

#### Independent review (second round, approved)
- Codex auditó `a7b36b0`, ejecutó los 2 tests de replay ampliados contra PostgreSQL real y confirmó limpieza completa de las filas temporales en las 5 tablas. Reexportó independientemente `2026-11-19` (668 posiciones, 484 actualizaciones, 3 alertas, 120 ejecuciones, 0 eventos de calidad) y leyó las tres alertas esperadas desde Parquet. MP-009 queda `DONE` y completa el Hito 1 (`MP-002` → `MP-009`), pendiente de que el propietario autorice los siguientes pasos.

#### Known limitation (documented, not blocking)
- El resumen gold calcula por núcleo, no por `route_id`/`station_id` (`daily_line_metrics`/`station_daily_metrics`): esa resolución depende de MP-010 (GTFS estático), que no es dependencia de MP-009. Ver DEC-021.

### MP-008 — Quality engine

#### Added
- `packages/quality/engine.py`: reglas puras para los cinco flags admitidos por el esquema v1, con umbrales calibrables nombrados y eventos estructurados.
- `packages/quality/db.py`: lectura de historial reciente y persistencia transaccional de `data_quality_event`; derivación estable de `vehicle_position_observation.quality_flags`.
- Integración en el colector: calidad evaluada sobre observaciones normalizadas antes de persistirlas, dentro de la misma transacción del poll.
- 13 tests de calidad: disparo y control de falso positivo para cada regla, cambio de día UTC y dos pruebas contra PostgreSQL real con rollback.

#### Changed
- `duplicate_snapshot` se calcula sobre el hash del payload completo sostenido más de 180s; la deduplicación normal entre polls consecutivos de MP-007 no se marca.
- `implausible_speed` se calcula en Python con Haversine entre posiciones consecutivas del mismo `source_vehicle_id`; no espera el campo `speed_kmh`, ausente en Renfe.
- `docs/DATA_QUALITY.md` distingue los cinco flags implementados de las tres reglas geométricas diferidas a MP-012.

#### Verified
- Suite completa: 59/59 pruebas en verde (31 contratos + 6 fixtures + 9 colector + 13 calidad), incluidas integraciones reales con PostgreSQL/PostGIS.
- Las inserciones de prueba se ejecutaron dentro de una transacción ambiente y terminaron en rollback; el volumen del soak test no se borró ni truncó.

#### Revisión independiente (Claude Code, 2026-11-19)
- Reproducidas las 59 pruebas contra el mismo PostgreSQL real; revisado el diseño de `engine.py`/`db.py`/`collector.py`. **APROBADA.**
- **Hallazgo empírico documentado, no bloqueante:** se repitieron 117 pares reales de posiciones consecutivas del soak test de MP-007 contra `check_implausible_speed`; 12/117 (~10%) dispararon con velocidades implícitas de 246–787 km/h. La inspección de la secuencia completa del vehículo `21053` confirmó que son saltos reales entre filas ya almacenadas (20-40s de separación, varios km), no un error del cálculo de Haversine — indica que el feed en vivo de Renfe actualiza posición en saltos más gruesos de lo que sugiere la cadencia de poll. Registrado para calibrar el umbral `implausible_speed_kmh` en MP-012.

### MP-007 — Collector idempotente

#### Added
- `services/collector/`: colector de polling contra los tres feeds GTFS-RT de Renfe, con reintentos/backoff/timeout (`http_client.py`, solo `urllib`), filtro de alcance por núcleo (ADR-0008), deduplicación por hash canónico contra la última fila almacenada (ADR-0010, nuevo) y persistencia en PostgreSQL (MP-006).
- `requirements.txt` + `.venv`: primera dependencia de terceros del proyecto (`psycopg[binary]`) para escribir en PostgreSQL desde Python; Python 3.12 fijado como versión de desarrollo (DEC-019).

#### Verified
- 46 tests reales en verde (31 contratos, 6 fixtures, 9 colector — 5 de ellos integración real contra PostgreSQL, no mocks).
- Soak test real de 20 minutos contra los tres feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión nueva tras el proceso.
- Rechazo de duplicados y detección de cambios reales verificados contra PostgreSQL real (no simulado).
- Segunda revisión independiente de Codex aprobada: test de regresión del empate y suite completa reejecutados contra PostgreSQL real; `id DESC` confirmado como desempate determinista en las tres consultas de deduplicación. MP-007 pasa a `DONE`.

#### Fixed during verification
- `packages/contracts/nucleo.py`: `nucleo_prefix()` no reconocía trip_id de refuerzo con formato `SPECIAL_<núcleo>_<resto>` (sin prefijo numérico directo) — hallazgo real del feed en vivo, corregido con una regex específica.
- `packages/contracts/raw.py`: `RawStopTimeArrival.delay` y los tres `entity` de `Raw*Feed` eran obligatorios basándose en las fixtures de MP-004; el feed en vivo trajo un `arrival` sin `delay` (tren `ADDED`) y una respuesta sin la clave `entity` (0 vehículos activos) — ambos corregidos a opcionales/con default, con test de regresión.
- `services/collector/db.py`: una versión anterior envolvía cada `INSERT` en su propio `with conn.transaction()`; con una conexión de larga duración, esto dejaba filas de observación sin comprometer indefinidamente mientras `source_ingestion_run` sí persistía (detectado verificando con una conexión nueva, no confiando en la ausencia de excepción). Corregido centralizando el límite de transacción en `run_cycle` (todo el ciclo se compromete como una unidad).
- Tests de integración: `addCleanup` en orden LIFO cerraba la conexión antes de poder hacer `rollback()`; corregido el orden de registro.

#### Fixed after Codex review (first round, blocking)
- `services/collector/db.py`: `latest_payload_hash` ordenaba solo por `observed_at DESC` sin desempate; dos filas de la misma entidad con `observed_at` empatado (ese timestamp lo reporta la fuente, no nuestro poll) hacían que Postgres devolviera una fila arbitraria, insertando una fila duplicada real en vez de deduplicar (reproducido por Codex: `(1, 6)` en vez de `(0, 7)` en el tercer ciclo de una secuencia inicial→cambio→repetición). Corregido con `id DESC` como desempate secundario en las 3 consultas de `_LATEST_HASH_QUERIES`; test de regresión `test_tied_observed_at_does_not_break_dedup_on_third_cycle` verificado contra el fix revertido (falla igual que reportó Codex) y restaurado (pasa).

#### Known limitation (documented, not blocking)
- El filtro de ingesta descarta por núcleo (Madrid), no todavía por línea C5 específicamente (ADR-0001, `Aceptado`) — ver DEC-020. Acotar a C5 exige la resolución `trip_id` → `route_id` vía el GTFS estático, asignada explícitamente a MP-010 por ADR-0009.

### MP-006 — Esquema PostgreSQL/PostGIS v1

#### Added
- Compose local aislado con `postgis/postgis:17-3.5`, puerto `127.0.0.1:5433`,
  volumen/red propios y montaje de migraciones en solo lectura.
- Migración SQL plana `0001_init` up/down con 14 tablas de aplicación,
  `source_feed_version`, PostGIS, constraints de dominio/deduplicación y los cinco
  índices propuestos (incluidos dos GIST).
- Documentación de arranque/parada, aplicación ordenada, rollback y diferencias
  de nombres resueltas a favor de `packages/contracts/canonical.py`.

#### Verified
- Aplicación real en PostgreSQL 17/PostGIS 3.5.2: 14 `CREATE TABLE`, 5
  `CREATE INDEX`, `COMMIT`; geometría generada y caso de posición ausente nulo.
- Duplicados de route, trip y observación rechazados realmente por PostgreSQL
  (exit 1 y nombre de constraint en cada caso).
- Rollback real: 14 `DROP TABLE`, `COMMIT` y 0 tablas de aplicación restantes;
  ciclo posterior `down → up` completado con exit 0.
- Regresión: 23 tests de contratos y 6 tests de fixtures, todos `OK`.

#### Fixed during verification
- La etiqueta oficial no ofrece manifiesto ARM64: Compose fija `linux/amd64` para
  Docker Desktop en Apple Silicon.
- El primer `down` intentaba retirar `postgis`, pero la imagen ya había creado
  extensiones dependientes y PostgreSQL revirtió la transacción. El rollback final
  conserva correctamente esa infraestructura preexistente y elimina solo el
  esquema de aplicación, sin `CASCADE` destructivo.

#### Revisión independiente (Claude Code, 2026-11-19)
- Reproducido el ciclo completo `down → up → datos → 3 rechazos UNIQUE → down → up`
  de forma propia en el mismo worktree, sin depender solo del reporte de Codex;
  confirmados los 2 índices `GIST`, la ausencia real de `effect`/`cause`/
  `header_text`/`current_stop_sequence`, y las suites de regresión (23/23, 6/6).
  `*-traza-app` verificado intacto antes y después. **APROBADA.**
- **Hallazgo corregido:** `docs/STATUS.md` había sustituido el checklist completo
  de MP-005 en "Tarea actual" por el de MP-006 sin archivarlo primero en "Tareas
  cerradas de la cadena", rompiendo el patrón seguido por MP-002/MP-003/MP-004.
  Corregido moviendo el registro íntegro de MP-005 a esa sección.

### MP-005 — Contrato canónico interno

#### Added
- `packages/contracts/raw.py`: modelos Pydantic fieles al JSON bruto observado de Renfe (vehicle_positions, trip_updates, alerts), sin campos inventados.
- `packages/contracts/nucleo.py`: tabla de prefijos de núcleo verificada en MP-003 y helpers de disambiguación.
- `packages/contracts/canonical.py`: esquema normalizado (`VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth`) con UTC, dato ausente = `None`, y `nucleo_prefix` como campo derivado.
- `packages/contracts/normalize.py`: funciones puras `raw → canonical`.
- `packages/contracts/tests/`: 17 tests (`test_raw_parsing.py`, `test_canonical_normalization.py`, `test_synthetic_schema.py`).
- `docs/adr/0009-unobserved-raw-fields.md` (`Propuesto`) y DEC-018.

#### Changed
- `docs/DATA_MODEL.md`: `speed_kmh`/`bearing` marcados `nullable` (no observados nunca), `current_stop_sequence` renombrado a `current_stop_id` (el feed da stopId, no posición de secuencia), eliminados `effect`/`cause`/`header_text` de `service_alert` (no observados), añadido `schedule_relationship` y `description_language` (sí observados).
- `docs/DATA_QUALITY.md`: nota aclarando que `implausible_speed` debe calcularse a partir de posiciones consecutivas, no leerse de un campo `speed_kmh` de origen.

#### Verified
- `python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`: 23 tests, `OK`.
- JSON Schema exportable (`model_json_schema`) incluyendo campos derivados en modo serialización.
- Rechazo activo de datos inválidos (`ValidationError` en tipos incorrectos y campos obligatorios ausentes).

#### Found
- `docs/DATA_MODEL.md` (escrito en MP-001, antes de verificación empírica) asumía tres grupos de campos que el feed real de Renfe nunca emite — ver DEC-018/ADR-0009.

#### Fixed (tras 1ª revisión de Codex, dispatch `ctx_ea1d5cf46d74`)
- **Bloqueante:** `RawActivePeriod.end` carecía del comentario de "no observado" que sí tienen los demás campos corregidos tras el hallazgo de MP-005 — se corrigió añadiendo un comentario. Insuficiente: ver 2ª ronda.
- **Bloqueante:** el esquema canónico documentaba "UTC siempre" sin exigirlo — añadidos `require_utc`/`require_utc_or_none` como `field_validator` en los 4 modelos; 5 tests nuevos prueban el rechazo real de `datetime` naive u offset no UTC (22 tests en total).
- **Bloqueante:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato de `deep-research-report.md` queda contradicho por esta verificación — añadida la fila, sin editar el documento congelado.
- **Menor:** `ADR-0009` decía erróneamente que Codex (revisor) podía promover el ADR a `Aceptado` — corregido, solo el propietario puede; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos).

#### Fixed (tras 2ª revisión de Codex, dispatch `ctx_ded900b82f20`)
- **Bloqueante:** Codex señaló que un comentario no resuelve una contradicción -- `packages/contracts/raw.py` declara explícitamente que no debe contener campos no observados, y `RawActivePeriod.end` seguía declarado. Corregido eliminando `end` del modelo `raw` (no comentándolo); `normalize.py` ya no lo lee (`active_period_end` siempre `None` hoy); `canonical.py` conserva `ServiceAlert.active_period_end` como campo opcional de cara al futuro, con un comentario que aclara por qué siempre es `None` actualmente. Añadido test de regresión que falla si se reintroduce sin verificar, incluso si el JSON de origen lo trae (se ignora por `extra="ignore"`). 23 tests en total.

#### Reviewed
- Tercera revisión independiente de Codex: **APROBADA**, sin hallazgos abiertos. Reejecutados 23/23 tests; verificados directamente el esquema `raw`, el descarte de campos extra no observados, el enforcement UTC, la trazabilidad del modelo candidato, ADR-0009, enlaces, ausencia de secretos y whitespace.

### MP-004 — Fixtures reproducibles

#### Added
- Fixtures JSON reducidas de capturas reales frescas de `vehicle_positions`, `trip_updates` y `alerts`, sin cabeceras ni cookies, con casos Madrid y colisión C5 entre núcleos.
- `tests/fixtures/MANIFEST.md`: fecha UTC, endpoints, recuentos original/conservado y SHA-256 de cada fixture.
- `tests/fixtures/test_parse_fixtures.py`: 6 pruebas offline con `unittest` para integridad, envoltura GTFS-RT, esquemas observados y disambiguación por prefijo de núcleo.

#### Verified
- Capturas directas: `200 application/json`; 394 posiciones, 401 actualizaciones y 76 alertas antes del recorte.
- `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v`: 6 tests ejecutados, `OK`.
- Los 3 JSON pasan `python3 -m json.tool`; SHA-256 recalculados coinciden con el manifiesto.

#### Reviewed
- Claude Code aprobó MP-004 el 2026-11-18 tras re-verificación independiente: hashes SHA-256 recalculados de forma propia (coinciden), suite de 6 tests re-ejecutada (`OK`), e inspección manual confirmando que el test de colisión C5 es sustantivo, no tautológico. MP-004 pasa a `DONE`.

### MP-003 — Probe real de feeds C5

#### Added
- `docs/research/MP-003-probe-findings.md`: evidencia real (status HTTP, timestamps, esquema JSON observado) de los 3 feeds GTFS-RT y descarga/inspección real del GTFS estático de Cercanías.
- `docs/adr/0008-route-identity.md` (`Propuesto`): `route.source_route_id` debe ser el `route_id` completo, no el código de línea.

#### Changed
- `docs/legal/DATA_SOURCES.md`: disponibilidad y esquema de los 3 feeds GTFS-RT y del GTFS estático pasan de `PENDING MP-003` a `VERIFIED`.
- `docs/DATA_MODEL.md`: entidad `route` corregida para explicitar `source_route_id` como `route_id` completo y añadir `nucleo_prefix`.
- `docs/DECISIONS.md`: DEC-017 (route_id completo, no código de línea).

#### Verified
- `vehicle_positions.json`, `trip_updates.json`, `alerts.json`: `200 OK`, JSON real GTFS-RT 2.0, no protobuf.
- Frecuencia de refresco de `vehicle_positions`: ~20–22 s medidos con 3 polls reales (coincide con `Cache-Control: max-age=30`).
- GTFS estático: descarga real exitosa (15,7 MB) vía `ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip`; el fallo SSL mencionado en MP-002 correspondía al enlace de portal (CKAN), no al enlace de descarga real.
- `stop_id` del feed en vivo coincide con `stops.txt` del GTFS estático (coordenadas verificadas).

#### Found
- **"C5" no es un identificador único**: existe también en Asturias (`20T0011C5`, Gijón–Pola de Laviana) y Andalucía (`30T0009C5`, Jardines de Hércules–Benacazón) en el mismo feed nacional. Ver DEC-017.
- Cobertura de `trip_updates` para Madrid fue 0/302 en el único poll realizado — pendiente de más muestreo antes de concluir nada (no se afirma que sea un problema sistemático).

#### Fixed (tras 1ª revisión de Codex, dispatch `ctx_61d7dd4fd86b`)
- **Bloqueante:** corregida la afirmación de que el `trip_id` en vivo no coincidía literalmente con `trips.txt`. Era falsa — causada por un `grep` propio anclado al campo equivocado (`trip_id` es el 3er campo del CSV, no el 1º). Verificado con comparación de conjuntos completa: 403/403 coinciden.
- **Bloqueante:** corregida la cardinalidad imposible en `docs/DATA_MODEL.md` — `UNIQUE(network_id, source_route_id)` exige una fila `route.id` por cada una de las 5 variantes de C5 Madrid, no una fila con una lista de `source_route_id`. `docs/adr/0008-route-identity.md` actualizado igual.
- **Menor:** corregida la afirmación falsa de que el GTFS estático no incluía `shapes.txt` (sí lo incluye).
- **Menor:** medida la frecuencia real de `trip_updates` (Δ42s) y `alerts` (Δ20s) con 2 polls cada uno — antes solo se había medido `vehicle_positions`.

#### Reviewed
- OpenAI Codex aprobó MP-003 el 2026-11-18 tras re-verificación independiente final: 404/404 `trip_id` de un snapshot fresco coincidieron literalmente con `trips.txt`, sin elementos no resueltos; DEC-017/ADR-0008 y `docs/DATA_MODEL.md` quedaron coherentes. MP-003 pasa a `DONE`.

### MP-002 — Matriz de fuentes y licencias

#### Changed
- `docs/legal/DATA_SOURCES.md`: licencias de Renfe GTFS/GTFS-RT, CRTM GTFS, estadística 1923861, OpenStreetMap y proyectos de referencia verificadas contra páginas oficiales y ficheros `LICENSE`, con `source_id`, publisher, dataset, URL, fecha UTC, restricciones y checklist reproducible.
- `docs/legal/LICENSE_MATRIX.md`: sustituidas las hipótesis `PENDING` por resultados verificables; documentadas la reciprocidad ODbL para bases derivadas, la separación consulta/software, y las obligaciones AGPL de Via Península sin reutilizar código.
- `docs/legal/ATTRIBUTION.md`: textos operativos de atribución para Renfe, CRTM, OSM, Comunidad de Madrid y el uso eventual de datos normalizados de Valfiguer.
- `docs/DECISIONS.md`: DEC-016 registra que los datos/API de Valfiguer son `CC BY 4.0`, pero no existe un repositorio público de implementación verificable ni puede inferirse su licencia de código.
- `docs/TASKS.md` y `docs/STATUS.md`: MP-001 reflejada como `DONE`, Hito 1 autorizado y MP-002 entregada en `REVIEW` para auditoría de Claude Code.

#### Verified
- Via Península: `AGPL-3.0`; Niltra/cercanias: `MIT`; atlas-ferroviario: texto MIT para código más aviso Renfe `CC BY 4.0`; Valfiguer: datos/API `CC BY 4.0`, código desconocido.
- Renfe Data: `CC BY 4.0` en GTFS estático y los tres datasets GTFS-RT, con condiciones adicionales del portal; CRTM: licencia propia `CRTM-LDA`; OpenStreetMap: `ODbL-1.0`.

### MP-001 — Bootstrap documental del repositorio

#### Added
- Estructura de monorepo: `apps/{web,api}`, `services/{collector,normalizer,snapshotter}`, `packages/{contracts,gtfs,geo,quality}`, `analytics/{dbt,duckdb}`, `infra/{docker,cloudflare,migrations}`, `tests/{fixtures,integration,e2e}`, `.github/{ISSUE_TEMPLATE,pull_request_template.md}` — todos los directorios de servicios futuros contienen únicamente `README.md` explicativo, sin código funcional.
- `AGENTS.md` y `CLAUDE.md`: protocolo de colaboración Claude Code ↔ Codex, regla de autoría exclusiva del propietario humano, principios de datos transversales.
- `docs/PLAN.md`: roadmap por fases F0–F10 con dependencias, entregables y gates de calidad.
- `docs/TASKS.md`: backlog completo MP-001 a MP-015 con ejecutor, revisor, dependencias, entradas/entregables, criterios de aceptación y estado.
- `docs/STATUS.md`: tablero vivo con checklist, bloqueos y bitácora.
- `docs/DECISIONS.md`: decisiones aceptadas, propuestas y pendientes.
- `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/DATA_QUALITY.md`, `docs/DEVELOPMENT.md`.
- `docs/adr/0001` a `0006`: decisiones de alcance C5, fuentes de datos, estrategia de almacenamiento, modelo de posición, contrato de API y política de licenciamiento.
- `docs/legal/DATA_SOURCES.md`, `LICENSE_MATRIX.md`, `ATTRIBUTION.md`.
- `docs/research/TRACEABILITY.md`: trazabilidad entre decisiones/tareas y evidencia consultada.
- `README.md` reescrito con visión del producto, estructura del repo y enlaces a la documentación.
- `.gitignore` para Python/Node/datos/env.

- `docs/adr/0007-autonomy-model.md` y DEC-014 en `docs/DECISIONS.md`: modelo de autonomía acotada (autorización por hito, commits de iteración en worktree, gates limitados a licencia/coste), a petición explícita del propietario.

#### Changed
- `deep-research-report.md` y `MADRID_PULSE_BRIEF_INICIAL.md` movidos a `docs/research/`, contenido preservado íntegro.
- `AGENTS.md`/`CLAUDE.md`: protocolo de coordinación en Orca (un worktree por tarea, delegación directa agente-a-agente) añadido a petición del propietario.
- `AGENTS.md`/`CLAUDE.md`: regla de autoría reescrita tras la revisión de Codex (hallazgo bloqueante — contradicción entre la excepción de "commit si el propietario lo pide" y la prohibición absoluta) y para incorporar la nueva política de commits de iteración en worktree.
- `docs/TASKS.md`: añadido `analytics/dbt/` a los componentes afectados de MP-009 y MP-015 (hallazgo menor de Codex); grafo de dependencias en ASCII sustituido por tabla exacta de dependencias directas (hallazgo menor de Codex).
- `AGENTS.md`: añadida nota de excepción de naming de rama para `chore/mp-001-foundation` (hallazgo menor de Codex).
- Segunda ronda de correcciones tras la primera re-verificación de Codex (2 bloqueantes + 2 menores, dispatch `ctx_e72e7a44721a`): añadida la sección "Modelo de autonomía por hito" a `AGENTS.md` (antes referenciada pero inexistente); reescritos el protocolo de worktree, el diagrama de flujo y la regla 10 en `AGENTS.md`/`CLAUDE.md`/`docs/TASKS.md`/`docs/PLAN.md` para reflejar autorización por hito y worktrees paralelos entre tareas independientes, en vez del texto anterior que seguía exigiendo autorización y merge por tarea individual; `docs/adr/0007-autonomy-model.md` corregido para que los ADR de arquitectura propuestos durante la autonomía se registren como `Propuesto` (nunca `Aceptado`) hasta la revisión del propietario, coherente con `docs/adr/README.md`; `docs/STATUS.md` corregido para quitar MP-010 del paralelismo de Hito 1 (está fuera de su rango MP-002→MP-009) y quitar DEC-003 de los gates de licencia/coste (es una decisión de visibilidad, no de licencia/coste).
- Tercera ronda de correcciones tras la segunda re-verificación de Codex (1 bloqueante + 1 menor, dispatch `ctx_762cad1ca40c`): el protocolo exigía que la dependencia directa de una tarea estuviera fusionada en `main` antes de abrir el siguiente worktree, lo que obligaba al propietario a fusionar en tiempo real tras cada tarea y anulaba el propósito del modelo de autonomía (ADR-0007 solo exigía `DONE`, no fusionada). Corregido introduciendo un mecanismo de ramas encadenadas: el worktree de una tarea dependiente se crea a partir de la rama de su dependencia directa en cuanto está `DONE`, sin esperar merge a `main`; el propietario decide cuándo fusionar (en lote al cierre del hito u otro momento) sin bloquear el avance. Reescrito en `AGENTS.md` (regla 10, sección de autonomía por hito, pasos 1/6/7 del protocolo, diagrama de flujo), `CLAUDE.md`, `docs/TASKS.md` y `docs/PLAN.md`. También corregido el "Principio rector" de `docs/PLAN.md`, que afirmaba una cadena de fases estrictamente lineal contradiciendo la excepción de dependencias (F5↔F2) ya documentada en la misma página.
- Cuarta revisión de Codex (dispatch `ctx_0ee25a6a5d2c`): **APROBADA**, sin hallazgos bloqueantes ni menores. Registrada la sugerencia no bloqueante de Codex (cómo converge una tarea con varias dependencias de ramas paralelas, relevante para MP-012) como DEC-015 en `docs/DECISIONS.md` y como nota en la ficha de MP-012 en `docs/TASKS.md`, a resolver antes de abrir esa tarea, no antes de cerrar MP-001.

#### Not done in this task
- Sin código de producto, sin dependencias instaladas, sin servicios cloud configurados, sin bases de datos ni contenedores — fuera de alcance de MP-001 según `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` §7.
