# CHANGELOG.md

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Solo se registran cambios realmente realizados y verificables — nunca funcionalidad planeada o supuesta.

## [Unreleased]

### MP-007 — Collector idempotente

#### Added
- `services/collector/`: colector de polling contra los tres feeds GTFS-RT de Renfe, con reintentos/backoff/timeout (`http_client.py`, solo `urllib`), filtro de alcance por núcleo (ADR-0008), deduplicación por hash canónico contra la última fila almacenada (ADR-0010, nuevo) y persistencia en PostgreSQL (MP-006).
- `requirements.txt` + `.venv`: primera dependencia de terceros del proyecto (`psycopg[binary]`) para escribir en PostgreSQL desde Python; Python 3.12 fijado como versión de desarrollo (DEC-019).

#### Verified
- 45 tests reales en verde (31 contratos, 6 fixtures, 8 colector — 4 de ellos integración real contra PostgreSQL, no mocks).
- Soak test real de 20 minutos contra los tres feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión nueva tras el proceso.
- Rechazo de duplicados y detección de cambios reales verificados contra PostgreSQL real (no simulado).

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
