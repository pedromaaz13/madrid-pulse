# CHANGELOG.md

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Solo se registran cambios realmente realizados y verificables — nunca funcionalidad planeada o supuesta.

## [Unreleased]

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
- `python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`: 17 tests, `OK`.
- JSON Schema exportable (`model_json_schema`) incluyendo campos derivados en modo serialización.
- Rechazo activo de datos inválidos (`ValidationError` en tipos incorrectos y campos obligatorios ausentes).

#### Found
- `docs/DATA_MODEL.md` (escrito en MP-001, antes de verificación empírica) asumía tres grupos de campos que el feed real de Renfe nunca emite — ver DEC-018/ADR-0009.

#### Fixed (tras 1ª revisión de Codex, dispatch `ctx_ea1d5cf46d74`)
- **Bloqueante:** `RawActivePeriod.end` carecía del comentario de "no observado" que sí tienen los demás campos corregidos tras el hallazgo de MP-005 — añadido.
- **Bloqueante:** el esquema canónico documentaba "UTC siempre" sin exigirlo — añadidos `require_utc`/`require_utc_or_none` como `field_validator` en los 4 modelos; 5 tests nuevos prueban el rechazo real de `datetime` naive u offset no UTC (22 tests en total).
- **Bloqueante:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato de `deep-research-report.md` queda contradicho por esta verificación — añadida la fila, sin editar el documento congelado.
- **Menor:** `ADR-0009` decía erróneamente que Codex (revisor) podía promover el ADR a `Aceptado` — corregido, solo el propietario puede; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos).

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
