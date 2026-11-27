# TASKS.md — Backlog Madrid Pulse

> El [tablero](STATUS.md#tablero-de-trabajo) resume el estado vigente. El [índice](#backlog-planificado-y-tracks-generado), las [fichas de reanudación](#fichas-de-reanudación) y el [registro de diferidos](#registro-de-hallazgos-y-propuestas-diferidas) se generan desde [`PROJECT_STATE.json`](governance/PROJECT_STATE.json). Las fichas históricas de MP-001…MP-022 documentan el cierre técnico de su alcance.

Numeración y dependencias conservadas de `docs/research/deep-research-report.md`. Cualquier desviación de la numeración original debe justificarse aquí y registrarse en `docs/DECISIONS.md`.

Leyenda de estado: `TODO` · `IN_PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`.

Cada tarea se trabaja en **un único worktree/rama** (`mp-00X-nombre-corto`), compartido secuencialmente por el ejecutor y el revisor hasta su aprobación — ver el protocolo completo en `AGENTS.md` ("Protocolo de coordinación en Orca" y "Modelo de autonomía por hito") y `CLAUDE.md`. El worktree de una tarea se abre, ramificado desde la rama de su dependencia directa, en cuanto esa dependencia (ver "Grafo de dependencias" más abajo) está `DONE` — **no** es necesario que ya esté fusionada en `main` — y la tarea está dentro del hito autorizado vigente (`docs/STATUS.md`); no se requiere autorización nueva por cada tarea. El propietario decide cuándo fusionar esas ramas a `main` (en lote al cierre del hito u otro momento), sin que eso bloquee el avance. Tareas que no dependen entre sí dentro del mismo hito pueden tener sus worktrees abiertos en paralelo.

---

## MP-001 — Bootstrap documental del repositorio

- **Fase:** F0 — Gobierno y documentación
- **Objetivo:** convertir la investigación en un repositorio profesional: estructura, documentación de arquitectura, backlog y protocolo de agentes, sin código de producto.
- **Prioridad:** P0
- **Depende de:** —
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** raíz del repo, `docs/*`, `AGENTS.md`, `CLAUDE.md`, `.github/*`, estructura de `apps/`, `services/`, `packages/`, `analytics/`, `infra/`, `tests/`.
- **Entradas:** `deep-research-report.md`, `MADRID_PULSE_BRIEF_INICIAL.md`, `README.md` originales.
- **Entregables:** estructura de monorepo; `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`; `docs/PLAN.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/DATA_QUALITY.md`, `docs/DEVELOPMENT.md`; `docs/adr/0001`–`0006`; `docs/legal/DATA_SOURCES.md`, `LICENSE_MATRIX.md`, `ATTRIBUTION.md`; `docs/research/` con los dos documentos originales íntegros + `TRACEABILITY.md`; plantillas `.github/`.
- **Criterios de aceptación:** ver `MADRID_PULSE_BRIEF_INICIAL.md` §7 (enlaces navegables, separación confirmado/propuesto/pendiente, cada tarea con responsable y revisor, `STATUS.md` con checklist y bitácora, `AGENTS.md`/`CLAUDE.md` coherentes, sin servicios cloud configurados, sin producto implementado).
- **Pruebas necesarias:** validación documental (enlaces internos resuelven, tabla de tareas sin huecos de responsable/revisor, ausencia de secretos).
- **Evidencia de verificación:** 4 rondas de revisión cruzada con Codex en este mismo worktree (dispatches `ctx_64731a94e6bc` → `ctx_e72e7a44721a` → `ctx_762cad1ca40c` → `ctx_0ee25a6a5d2c`): 1 bloqueante + 3 menores (ronda 1), 2 bloqueantes + 2 menores (ronda 2), 1 bloqueante + 1 menor (ronda 3), **APROBADO sin hallazgos** (ronda 4). Detalle completo en `docs/STATUS.md` → bitácora.
- **Estado:** `DONE` — **Codex: APROBADO** en revisión cruzada; el propietario autorizó Hito 1 (`MP-002` → `MP-009`) el 2026-11-18. El merge a `main` no es requisito para `DONE` según ADR-0007.

---

## MP-002 — Matriz de fuentes y licencias

- **Fase:** F1 — Factibilidad real de datos
- **Objetivo:** documentar y verificar formalmente las licencias y condiciones de uso de Renfe Data, CRTM, OpenStreetMap y los proyectos de referencia (Via Península, Valfiguer, Niltra/cercanias, xaviour-ai-2026/atlas-ferroviario).
- **Prioridad:** P0
- **Depende de:** MP-001
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `docs/legal/DATA_SOURCES.md`, `docs/legal/LICENSE_MATRIX.md`, `docs/legal/ATTRIBUTION.md`.
- **Entradas:** URLs y licencias preliminares listadas en `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` §2 y en el informe completo.
- **Entregables:** matriz de licencias confirmada (no asumida) con `source_id`, publisher, licencia exacta, texto de atribución y restricciones por fuente.
- **Criterios de aceptación:** cada fuente usada tiene licencia verificada contra su página oficial (no solo citada por la investigación previa); AGPL de Via Península y ODbL de OSM explícitamente resueltos con sus implicaciones documentadas.
- **Pruebas necesarias:** checklist de verificación por fuente (URL accedida, fecha de verificación, captura/registro de la licencia vigente).
- **Evidencia de verificación:** checklist por fuente, URLs oficiales accedidas, fecha/hora UTC, hallazgo y hashes de los ficheros `LICENSE` registrados en `docs/legal/DATA_SOURCES.md`; implicaciones ODbL/AGPL resueltas en `docs/legal/LICENSE_MATRIX.md`; textos de atribución en `docs/legal/ATTRIBUTION.md`. Valfiguer queda documentado con datos/API `CC BY 4.0` y licencia de implementación desconocida (DEC-016). **Auditoría independiente de Claude Code (revisor):** re-verificadas de forma autónoma (no solo leyendo el reporte de Codex) las licencias de Via Península, Niltra/cercanias y atlas-ferroviario vía `gh api` y lectura directa de los ficheros `LICENSE`, y las de Renfe/CRTM vía fetch directo de `data.renfe.com/legal`, la ficha del dataset `ubicacion-vehiculos` y `crtm.es/licencia-de-uso` — todas coinciden con lo documentado. Enlaces y secretos re-validados sin hallazgos. **APROBADO.**
- **Estado:** `DONE` — Codex ejecutó, Claude Code revisó y aprobó el 2026-11-18 sin hallazgos bloqueantes ni menores.

---

## MP-003 — Probe real de feeds C5 (GTFS + GTFS-RT)

- **Fase:** F1 — Factibilidad real de datos
- **Objetivo:** validar empíricamente, mediante peticiones reales, los endpoints `gtfsrt.renfe.com/vehicle_positions.json`, `trip_updates.json`, `alerts.json` y el GTFS estático de Cercanías para la línea C5.
- **Prioridad:** P0
- **Depende de:** MP-002
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `docs/research/MP-003-probe-findings.md` (nuevo), `docs/legal/DATA_SOURCES.md`, `docs/DATA_MODEL.md`, `docs/DECISIONS.md` (DEC-017), `docs/adr/0008-route-identity.md` (nuevo, `Propuesto`); fixtures crudas temporales (no versionadas todavía — ver MP-004).
- **Entradas:** endpoints hipotéticos de `MADRID_PULSE_BRIEF_INICIAL.md` §2.
- **Entregables:** captura controlada de los tres feeds GTFS-RT y del GTFS estático; esquema real de payload documentado (campos observados, no asumidos); frecuencia de actualización medida (no asumida en ~20/30/60 s).
- **Criterios de aceptación:** evidencia reproducible (comandos, timestamps, status HTTP) de que los endpoints responden y cubren trenes de la C5; cualquier discrepancia con lo documentado en la investigación queda registrada en `docs/DECISIONS.md`.
- **Pruebas necesarias:** capturas repetidas en ventanas de tiempo distintas para medir frecuencia real; validación de que `trip_id` del feed en vivo es resoluble contra el GTFS estático.
- **Evidencia de verificación:** `docs/research/MP-003-probe-findings.md` — 3 polls reales de `vehicle_positions.json` espaciados ~20 s (headers/timestamps), 1 poll de `trip_updates.json` (302 entidades) y de `alerts.json` (82 entidades), descarga real del GTFS estático (15,7 MB, `200 OK`) e inspección de `routes.txt`/`trips.txt`/`stops.txt`/`calendar.txt`. `docs/legal/DATA_SOURCES.md` actualizado de `PENDING MP-003` a `VERIFIED` para disponibilidad/esquema. Hallazgo crítico registrado como DEC-017/ADR-0008 (`Propuesto`): "C5" no es único en el feed nacional (existe también en Asturias y Andalucía); `docs/DATA_MODEL.md` corregido en consecuencia.
- **Estado:** `DONE` — aprobado por OpenAI Codex el 2026-11-18 tras tres rondas de revisión. Verificación final independiente: snapshot fresco con 404/404 `trip_id` resueltos por igualdad literal contra `trips.txt` y 0 sin match; cardinalidad de las 5 variantes coherente entre `docs/DATA_MODEL.md`, DEC-017 y ADR-0008; esquema vivo, colisión nacional de "C5", enlaces, ausencia de secretos y licencias revalidados. Los hallazgos de rondas previas quedaron corregidos en `bdf263e` y `f6d8ee9`. Pendientes no bloqueantes y fuera de alcance: cobertura larga de `trip_updates` para Madrid (MP-007/MP-008), descarga del GTFS CRTM con login, detalle de `shapes`/`stop_times` (MP-010) y cambio de día de servicio (MP-012).

---

## MP-004 — Fixtures reproducibles

- **Fase:** F2 — Contratos y calidad de datos
- **Objetivo:** congelar fixtures anonimizadas de los payloads reales capturados en MP-003, con hashes y tests de parseo.
- **Prioridad:** P0
- **Depende de:** MP-003
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `tests/fixtures/`.
- **Entradas:** capturas de MP-003.
- **Entregables:** fixtures congeladas (JSON/protobuf decodificado) con hash de verificación; tests de parseo contra esas fixtures.
- **Criterios de aceptación:** fixtures no contienen datos sensibles ni dependen de endpoints en vivo; tests de parseo reproducibles sin red.
- **Pruebas necesarias:** suite de parseo ejecutada en CI local.
- **Evidencia de verificación:** captura fresca del 2026-11-18T16:01Z: 394 entidades de `vehicle_positions`, 401 de `trip_updates` y 76 de `alerts`, reducidas respectivamente a 10/8/3 entidades representativas. `tests/fixtures/MANIFEST.md` registra endpoints, recuentos y SHA-256 (`80af5343…`, `78974c85…`, `cdd94af7…`). Ejecución real offline: `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v` → `Ran 6 tests in 0.001s`, `OK`. Validación adicional: `python3 -m json.tool` sobre los 3 JSON y `shasum -a 256 tests/fixtures/*.json`, ambas sin error y con hashes coincidentes con el manifiesto. **Auditoría independiente de Claude Code (revisor):** hashes SHA-256 recalculados de forma independiente — coinciden exactamente; suite de tests re-ejecutada — 6/6 `OK`; inspección manual de `test_c5_label_alone_mixes_nuclei` confirma que es un test sustantivo (no tautológico): un filtro ingenuo por `"C5" in label` captura entidades de 4 núcleos distintos (`10`/`20`/`30`/`40`), mientras que el filtro correcto (`"C5"` + prefijo `10`) aísla solo Madrid; `test_alerts_schema_and_madrid_c5_routes` verifica las 5 variantes exactas de `route_id` de C5 Madrid encontradas en MP-003. Sin cookies/secretos en ningún fichero. Enlaces y licencias revalidados. **APROBADO.**
- **Estado:** `DONE` — Codex ejecutó, Claude Code revisó y aprobó el 2026-11-18 sin hallazgos bloqueantes ni menores.

---

## MP-005 — Contrato canónico interno

- **Fase:** F2 — Contratos y calidad de datos
- **Objetivo:** definir el esquema canónico interno (Pydantic/JSON Schema) para vehículo, viaje y salud de feed, desacoplado del formato bruto de Renfe.
- **Prioridad:** P0
- **Depende de:** MP-004
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `packages/contracts/` (nuevo: `raw.py`, `canonical.py`, `nucleo.py`, `normalize.py`, `tests/`), `docs/DATA_MODEL.md`, `docs/DATA_QUALITY.md`, `docs/DECISIONS.md` (DEC-018), `docs/adr/0009-unobserved-raw-fields.md` (nuevo, `Propuesto`).
- **Entradas:** fixtures de MP-004, modelo propuesto en `docs/DATA_MODEL.md` y `docs/DATA_CONTRACTS.md`.
- **Entregables:** esquema canónico versionado, con separación explícita `raw` vs `normalized`.
- **Criterios de aceptación:** el esquema resuelve el modelo candidato de `docs/DATA_MODEL.md` sin contradicciones no documentadas; cambios respecto al modelo candidato se registran como ADR.
- **Pruebas necesarias:** tests de validación de esquema contra fixtures reales y sintéticas.
- **Evidencia de verificación:** `packages/contracts/tests/` — 23 tests (`python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`), `OK`. Hallazgo: `docs/DATA_MODEL.md` asumía `speed_kmh`/`bearing`/`current_stop_sequence`/`effect`/`cause`/`header_text` que el feed real nunca emite — corregido, registrado como DEC-018/ADR-0009 (`Propuesto`). **Primera revisión de Codex (dispatch `ctx_ea1d5cf46d74`): no aprobada** — 3 bloqueantes + 1 menor. (2) UTC enforcement, (3) trazabilidad y (4) ADR-0009/redacción quedaron resueltos en esa ronda. (1) `RawActivePeriod.end` se había dejado como campo opcional con un comentario explicando que no se observaba — eso **documentaba** la contradicción con el propio docstring de `raw.py` ("no debe contener ningún campo que no se haya observado") en vez de **resolverla**. **Segunda revisión de Codex (dispatch `ctx_ded900b82f20`): no aprobada** — señaló correctamente que un comentario no corrige una contradicción. Corregido eliminando `end` de `RawActivePeriod` (no solo comentándolo); `normalize.py` y `canonical.py` ajustados en consecuencia; añadido test de regresión que falla si alguien reintroduce el campo. **Tercera revisión independiente de Codex: APROBADA** — reejecutó 23/23 tests y verificó directamente ausencia de `end` en `RawActivePeriod.model_fields`, descarte del extra, enforcement UTC, trazabilidad y documentación, sin hallazgos abiertos.
- **Estado:** `DONE` — aprobado por OpenAI Codex el 2026-11-18 tras tres rondas de revisión independiente.

---

## MP-006 — Esquema PostgreSQL/PostGIS v1

- **Fase:** F3 — Persistencia e ingesta mínima
- **Objetivo:** migraciones iniciales del esquema relacional (entidades, constraints, índices) con rollback probado.
- **Prioridad:** P0
- **Depende de:** MP-005
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `infra/migrations/`.
- **Entradas:** modelo relacional de `docs/DATA_MODEL.md`.
- **Entregables:** migraciones versionadas (up/down), constraints de unicidad e índices (incluyendo `GIST` sobre geometría).
- **Criterios de aceptación:** migraciones aplican y revierten limpiamente sobre PostgreSQL/PostGIS local; constraints reflejan las claves de deduplicación documentadas.
- **Pruebas necesarias:** aplicación y rollback de migraciones en base local, verificación de constraints con datos de prueba.
- **Evidencia de verificación:** PostgreSQL 17 + PostGIS 3.5.2 real en
  `postgis/postgis:17-3.5`, proyecto Compose aislado `madrid-pulse` y puerto host
  `127.0.0.1:5433`. `0001_init.up.sql` ejecutada con `ON_ERROR_STOP=1`: 14 tablas
  de aplicación y 5 índices propuestos creados, `COMMIT`. Datos válidos insertados:
  la geometría generada devolvió `POINT(-3.689 40.406)` y una observación sin
  posición conservó coordenadas/`geom` como `NULL`. PostgreSQL rechazó realmente
  tres duplicados (exit 1): `route_network_id_source_route_id_key`,
  `trip_service_date_source_trip_id_key` y
  `vehicle_position_observation_ingestion_run_id_payload_hash_key`.
  `0001_init.down.sql` ejecutada con `ON_ERROR_STOP=1`: 14 `DROP TABLE`, `COMMIT`;
  consulta posterior: `remaining_application_tables = 0`. Ciclo final
  `down → up` repetido con ambos comandos en exit 0. Las extensiones provistas por
  la imagen se conservan deliberadamente en rollback (ver README). Contenedor
  detenido al terminar con `docker compose -p madrid-pulse ... down`; volumen
  nombrado conservado con la migración final aplicada.
- **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Reproducida de
  forma propia en el mismo worktree, no solo verificado lo reportado por Codex:
  contenedor levantado, `0001_init.up.sql` aplicada sobre un volumen que ya tenía
  el esquema cargado (rollback previo necesario, reproducido primero), geometría
  generada confirmada (`POINT(-3.689 40.406)` con posición, `NULL` sin ella), los
  tres `UNIQUE` (`route`, `trip`, `vehicle_position_observation`) rechazados de
  verdad con `exit 1`, los dos índices `GIST` presentes, ausencia confirmada de
  `effect`/`cause`/`header_text` y `current_stop_sequence`. Ciclo completo
  `down → up → down → up` repetido independientemente, exit 0 en cada paso.
  Suites de regresión reejecutadas de forma independiente: contratos 23/23 `OK`,
  fixtures 6/6 `OK`. `check_links.py` sobre todo el repo: 46 enlaces, ninguno roto.
  Identidad Git verificada (`Pedro Matute`, sin coautores). Contenedores
  `*-traza-app` confirmados intactos antes y después.
  **Hallazgo (corregido):** `docs/STATUS.md` reemplazó el registro completo de
  MP-005 en "Tarea actual" por el de MP-006 sin archivarlo primero en "Tareas
  cerradas de la cadena", rompiendo el patrón seguido por MP-002/MP-003/MP-004 —
  el checklist detallado de MP-005 se perdía del documento vivo (solo quedaba una
  línea de bitácora y el CHANGELOG). Corregido moviendo el registro completo de
  MP-005 a "Tareas cerradas de la cadena".
- **Estado:** `DONE` (aprobado el 2026-11-19). MP-007 puede ramificar desde
  `mp-006-postgis-schema` sin esperar merge a `main`.

---

## MP-007 — Collector idempotente

- **Fase:** F3 — Persistencia e ingesta mínima
- **Objetivo:** servicio de polling contra los feeds de Renfe con reintentos, timeout, hashing de payload y deduplicación.
- **Prioridad:** P0
- **Depende de:** MP-005, MP-006
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `services/collector/`.
- **Entradas:** contrato canónico (MP-005), esquema de persistencia (MP-006).
- **Entregables:** colector con polling parametrizable, reintentos con backoff, timeout, hash canónico de payload, deduplicación, métricas de ejecución (`feed_run`).
- **Criterios de aceptación:** ejecución sostenida sin errores críticos durante la ventana de prueba definida en `docs/PLAN.md` (F3); deduplicación verificada con payloads idénticos repetidos.
- **Pruebas necesarias:** test de idempotencia (mismo payload → una sola observación almacenada), test de manejo de fallos de red.
- **Evidencia de verificación:**
  - 46 tests reales en verde: 31 `packages/contracts` (23 previos + 1 regresión de `entity` ausente + 7 de `nucleo_prefix`/`SPECIAL_`), 6 fixtures de MP-004, 9 de `services/collector` (4 de reintentos/backoff sin red, 5 de integración contra PostgreSQL real: idempotencia, fila nueva ante cambio real, empate de `observed_at`, filtro de alcance por núcleo, fallo de red registrado sin relanzar).
  - **Soak test real de 20 minutos** contra los tres feeds en vivo de Renfe (`https://gtfsrt.renfe.com/*.json`, ventana `2026-11-18 23:31:55Z`–`23:51:47Z`): 40 ciclos completos (120 fetches), **0 errores, 0 tracebacks**. Totales acumulados: 1155 entidades insertadas, 304 deduplicadas, 2622 descartadas por estar fuera de núcleo (Madrid). Verificado con una conexión `psql` nueva (no la del proceso) tras finalizar: `vehicle_position_observation`=668, `trip_update_observation`=484, `service_alert`=3, `source_ingestion_run` status=`ok`×120/`error`×0 — confirma que `run_cycle` compromete cada ciclo de verdad, no solo en memoria. Esta ventana de 20 min demuestra el comportamiento sostenido pedido por el criterio de aceptación; el *exit gate* de 24 h de la fase F3 completa (`docs/PLAN.md`) es una validación más larga, pendiente como actividad de monitorización continuada, no bloqueante para cerrar MP-007 bajo el régimen de autonomía de ADR-0007 (no es una decisión de licencia/coste).
  - Rechazo de duplicados real: verificado por `test_repeated_identical_payload_stores_a_single_row_per_entity` contra PostgreSQL real (no mock) — un payload idéntico repetido no inserta fila nueva; un cambio real (ej. `currentStatus`) inserta exactamente una fila nueva.
  - **3 hallazgos reales corregidos durante la verificación** (feed en vivo, fuera de lo cubierto por las fixtures más pequeñas de MP-003/MP-004): (1) `trip_id` de refuerzo `SPECIAL_<núcleo>_<resto>` sin prefijo numérico directo — corregido `packages/contracts/nucleo.py`; (2) `stopTimeUpdate[].arrival` sin `delay` en un tren `ADDED` — corregido `raw.py` a `Optional`; (3) una respuesta real omitió la clave `entity` por completo (0 vehículos) — corregido con `default_factory=list` en los tres `Raw*Feed`. Las tres correcciones tienen test de regresión. Detalle completo en `docs/research/MP-003-probe-findings.md` §10 y adendas de ADR-0008/ADR-0009.
  - **1 bug de transacciones corregido antes de llegar a producción:** una versión anterior de `db.py` envolvía cada `INSERT` en su propio `with conn.transaction()`; con una conexión de larga duración, solo el primero de una secuencia se comprometía como transacción real — los siguientes quedaban como `SAVEPOINT` de una transacción ambiente que nunca se comprometía, por lo que `vehicle_position_observation` quedaba vacío pese a que `source_ingestion_run` sí persistía. Detectado al verificar con una conexión nueva tras cerrar la original (no solo confiando en que `run_cycle` "no lanzó excepción"). Corregido centralizando el límite de transacción en `run_cycle` (un único `with conn.transaction()` por ciclo).
  - **Hallazgo de alcance documentado, no bloqueante:** el filtro de ingesta descarta por núcleo (`nucleo_prefix == "10"`, Madrid) pero no acota todavía a la línea C5 específicamente, que es el alcance real de ADR-0001 (`Aceptado`). Ver DEC-020/ADR-0008 (adenda). Acotar a C5 exige resolver `trip_id` → `route_id` vía el GTFS estático, trabajo asignado explícitamente a MP-010 por ADR-0009.
  - `ADR-0010` (nuevo, `Propuesto`): estrategia de deduplicación — hash canónico completo de la entidad comparado contra la última fila almacenada por clave de entidad de origen, sin `seen_count`.
  - Identidad Git verificada en cada commit (`Pedro Matute`, sin coautores); contenedor `madrid-pulse` detenido al finalizar (`docker compose ... down`, sin `--volumes`: el volumen con los datos reales del soak test se conserva); contenedores `*-traza-app` confirmados intactos antes y después.
  - **Primera revisión independiente de Codex (dispatch `ctx_a674a371ce8a`): no aprobada — 1 bloqueante real y reproducible.** Repitió las 45 pruebas, auditó transacciones/alcance/secretos/identidad Git/enlaces y consultó directamente los feeds vivos; el snapshot puntual no contenía `SPECIAL_`/`ADDED`, que se confirmaron en el volumen real conservado del soak test. Encontró que `latest_payload_hash` (`db.py`) ordenaba solo por `observed_at DESC` sin desempate: cuando dos filas de la misma entidad comparten `observed_at` (plausible porque ese timestamp lo reporta la fuente, no nuestro poll), Postgres puede devolver cualquiera de las filas empatadas sin garantía de orden. En su reproducción de 3 ciclos (inicial → cambio con mismo `observed_at` → repetición del cambio) obtuvo `(1, 6)` en el tercer ciclo en vez de `(0, 7)`: una fila duplicada real para el vehículo 19705, no solo un riesgo teórico.
  - Corregido añadiendo `id DESC` como desempate secundario en las tres consultas de `_LATEST_HASH_QUERIES`. Verificado revirtiendo el fix temporalmente y confirmando que el nuevo test de regresión (`test_tied_observed_at_does_not_break_dedup_on_third_cycle`) falla exactamente con `(1, 6)` como reportó Codex, y pasa `(0, 7)` con el fix restaurado. 46 tests en verde tras el fix (45 + 1 nuevo).
  - **Segunda revisión independiente de Codex (dispatch `ctx_801574c4ef71`): APROBADA.** Inspeccionó el diff de `3f83699`, ejecutó el test específico `test_tied_observed_at_does_not_break_dedup_on_third_cycle` contra PostgreSQL real (`OK`) y repitió las 46 pruebas completas: 31 contratos, 6 fixtures y 9 colector, todas `OK`. Confirmó que `ORDER BY <timestamp> DESC, id DESC` elimina el empate no determinista en las tres consultas.
- **Estado:** `DONE` — aprobado por OpenAI Codex el 2026-11-19 tras dos rondas de revisión independiente; el bloqueante de deduplicación de la primera ronda quedó corregido y re-verificado contra PostgreSQL real.

---

## MP-008 — Quality engine

- **Fase:** F4 — Motor de calidad e histórico
- **Objetivo:** motor de detección de anomalías: datos obsoletos (stale), velocidades implausibles, IDs ausentes, snapshots duplicados, anomalías de reloj (incluido cambio de día).
- **Prioridad:** P0
- **Depende de:** MP-007
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `packages/quality/`.
- **Entradas:** observaciones persistidas por el colector (MP-007); catálogo de problemas empíricos documentado en `docs/DATA_QUALITY.md` (inspirado en los hallazgos públicos de Valfiguer y Niltra/cercanias, reimplementado de forma independiente).
- **Entregables:** reglas de calidad con flags documentados (`quality_flags`), eventos de calidad persistidos (`data_quality_event`).
- **Criterios de aceptación:** cada regla tiene al menos un test con caso real o fixture que la dispara y uno que no la dispara (falso positivo controlado).
- **Pruebas necesarias:** suite de tests de reglas de calidad.
- **Evidencia de verificación:** 59 pruebas reales ejecutadas en verde: 31 contratos, 6 fixtures, 9 colector y 13 calidad. La suite de calidad incluye al menos disparo + falso positivo controlado para cada uno de los 5 flags, caso UTC de cambio de día y 2 integraciones PostgreSQL con rollback (persistencia atómica de `quality_flags`/`data_quality_event` y feed idéntico que solo dispara `duplicate_snapshot` tras 181s, no en el poll normal inicial). `implausible_speed` usa Haversine entre posiciones consecutivas del mismo vehículo; los casos anómalos no presentes en fixtures están identificados explícitamente como sintéticos. Contenedor `madrid-pulse-postgres-1` dejado levantado y saludable para revisión; volumen real conservado, `*-traza-app` intactos.
- **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Reproducida de
  forma propia en el mismo worktree: 59/59 pruebas reejecutadas contra el
  PostgreSQL real (los mismos 668/484/3/120 registros del soak test de MP-007,
  intactos antes y después — `data_quality_event` seguía en 0 porque el
  motor no existía durante ese soak). Revisados `engine.py`/`db.py`/
  `collector.py`: separación limpia reglas-puras/persistencia, transacción
  atómica correcta (reutiliza el patrón `id DESC` de MP-007 en las nuevas
  consultas de historial), `duplicate_snapshot` correctamente distinto de la
  deduplicación normal de MP-007, `implausible_speed` sin depender de
  `speed_kmh` de origen (ausente, ADR-0009).
  **Hallazgo empírico documentado, no bloqueante:** se repitieron 117 pares
  reales de posiciones consecutivas del soak test de MP-007 contra
  `check_implausible_speed`; 12/117 (~10%) dispararon con velocidades
  implícitas de 246–787 km/h, físicamente imposibles para un tren de
  Cercanías. Inspeccionada la secuencia completa del vehículo `21053`:
  son saltos reales entre filas ya almacenadas (no duplicadas, 20–40s de
  separación, varios km de distancia), no un error en el cálculo de
  Haversine. Indica que el feed en vivo de Renfe actualiza la posición en
  saltos más gruesos de lo que el cadencia de poll (~20-30s) sugiere, no
  como GPS continuo — un hallazgo real sobre la fuente, no un defecto del
  motor. El umbral de `200 km/h` ya estaba documentado como "a calibrar, no
  verdad de diseño" (ver `QualityThresholds`); esta evidencia debe
  considerarse explícitamente al calibrarlo en MP-012, registrada aquí para
  no perderse.
- **Estado:** `DONE` (aprobado el 2026-11-19). MP-009 puede ramificar desde
  `mp-008-quality-engine` sin esperar merge a `main`.

---

## MP-009 — Exportador histórico (Parquet particionado)

- **Fase:** F4 — Motor de calidad e histórico
- **Objetivo:** exportación diaria particionada a Parquet con compresión, y test de replay.
- **Prioridad:** P1
- **Depende de:** MP-007, MP-008
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `services/snapshotter/`, `analytics/duckdb/`, `analytics/dbt/` (transformación silver → gold inicial).
- **Entradas:** datos hot de PostgreSQL (MP-006/007) y flags de calidad (MP-008).
- **Entregables:** exportador con particionado `date=YYYY-MM-DD/hour=HH` (raw) y `date=YYYY-MM-DD` (silver/gold), compresión ZSTD.
- **Criterios de aceptación:** un día exportado puede reconstruirse (*replay*) reproduciendo el estado observado sin pérdida de eventos relevantes.
- **Pruebas necesarias:** test de replay de un día completo de fixtures.
- **Evidencia de verificación:**
  - `services/snapshotter/` (nuevo): DuckDB como único motor para leer PostgreSQL
    (`ATTACH ... TYPE POSTGRES`) y escribir Parquet particionado nativamente
    (`COPY ... FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY`); sin
    `pandas`/`pyarrow` adicionales (DEC-021).
  - **Hallazgo real durante la implementación:** los datos reales del soak
    test de MP-007 (`23:31:42 UTC` del 18-nov-2026) pertenecen al día de
    servicio **19-nov** en Europe/Madrid (CET, UTC+1 en noviembre) — leer la
    fecha UTC directamente habría exportado esas filas al día equivocado,
    exactamente el error que `docs/DATA_MODEL.md` ya advertía. Corregido con
    conversión explícita a `Europe/Madrid` antes de calcular límites de día
    y partición; 3 tests de regresión puros (incluido un caso de horario de
    verano, CEST) en `services/snapshotter/tests/test_export.py`.
  - **Test de replay real** (`test_export_replay.py`): inserta un día de
    prueba conocido (`2099-01-01`, sin colisión con datos reales),
    COMPROMETIDO (no `rollback()` — DuckDB usa su propia conexión `libpq` y
    no vería una transacción sin comprometer), lo exporta y confirma que el
    Parquet reproduce exactamente las filas insertadas sin pérdida; limpia
    sus propias filas en `finally`. 2 tests (exportación raw + resumen
    gold).
  - **Exportación real completa** del día `2026-11-19` (datos reales del
    soak test de MP-007, no fixtures): 668 posiciones + 484 actualizaciones
    de viaje + 120 ejecuciones de ingesta + 0 alertas/eventos de calidad
    (ninguno en esa ventana) = 1272 filas, ~76 KB comprimidos en Parquet
    ZSTD particionado `date=2026-11-19/hour=HH`. Verificado leyendo de
    vuelta con una consulta DuckDB independiente: recuento exacto, sin
    pérdida.
  - **Resumen gold inicial por núcleo** (`gold.py`): para el día real,
    produce 1 fila (`nucleo_prefix=10`, Madrid): 668 posiciones, 24
    vehículos distintos, 484 actualizaciones, 24 viajes distintos. **No**
    calcula `daily_line_metrics`/`station_daily_metrics` (requieren
    `route_id`/`station_id`, diferido explícitamente a MP-010 — DEC-021, sin
    inventar un join no verificado).
  - CLI real probado: `python -m services.snapshotter 2026-11-19` ejecuta
    export + resumen gold de punta a punta contra el PostgreSQL real.
  - 64 tests reales en verde: 31 contratos + 6 fixtures + 9 colector + 13
    calidad + 5 snapshotter (3 puros de huso horario + 2 de replay real).
  - **Primera revisión independiente de Codex (dispatch `ctx_d2b95955a73a`): no aprobada — 1 bloqueante real y reproducible.** Repitió las 64 pruebas, confirmó la conversión Europe/Madrid, reprodujo el export real (668/484/120/0) y el resumen gold (668/24/484/24), y verificó que `test_export_replay.py` limpiaba de verdad sus filas. Encontró que las 3 `service_alert` reales del `ingestion_run` 78 (ingeridas el `2026-11-18 23:31:55Z`, día local 19-nov) desaparecían del export del 19-nov porque `export.py` particionaba `service_alert` por `active_period_start` — la ventana de VIGENCIA del aviso, no el momento en que se observó. `service_alert` no tiene ninguna columna propia de observación/recepción.
  - Corregido uniendo `service_alert` a `source_ingestion_run` (vía `ingestion_run_id`) y usando `started_at` de esa ejecución como el momento de observación real, igual que el resto de tablas. Verificado revirtiendo el fix temporalmente: el test ampliado (ahora cubre las 5 tablas, no solo 2) falla exactamente con `service_alert: 0 != 1`, y pasa con el fix restaurado. Reexportado el día real `2026-11-19`: `service_alert` pasa de 0 a **3** filas, el resto sin cambios (668/484/120/0). 64 tests en verde tras el fix (mismo total; 2 tests existentes ampliados, no se añadieron archivos nuevos).
  - **Segunda revisión independiente de Codex (dispatch `ctx_095ae1499806`): APROBADA.** Auditó el diff de `a7b36b0`, ejecutó los 2 tests de replay ampliados contra PostgreSQL real (`OK`) y confirmó que sus filas temporales se limpian de las 5 tablas (`vp=0`, `tu=0`, `alert=0`, `dqe=0`, `run=0`). Reexportó independientemente el día real `2026-11-19`: 668 posiciones + 484 actualizaciones + **3 alertas** + 120 ejecuciones + 0 eventos de calidad; leyó el Parquet y confirmó exactamente `AVISO_467462`, `AVISO_483553` y `AVISO_525129`, ligadas al `ingestion_run` 78. `git diff --check` e identidad Git (`Pedro Matute`, sin coautores) correctos; `*-traza-app` intactos y contenedor de Madrid Pulse detenido sin borrar el volumen.
- **Estado:** `DONE` — aprobado por OpenAI Codex el 2026-11-19 tras dos rondas de revisión independiente; el bloqueante de semántica temporal de alertas quedó corregido y re-verificado contra los datos reales. Con MP-009 queda completo el Hito 1 (`MP-002` → `MP-009`); no se inicia MP-010 sin una nueva autorización del propietario.

---

## MP-010 — Topología GTFS C5

- **Fase:** F5 — Geometría y topología
- **Objetivo:** modelar estaciones, trips y shapes de la C5 a partir del GTFS estático, con validación de recorrido.
- **Prioridad:** P0
- **Depende de:** MP-004
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `packages/gtfs/`.
- **Entradas:** GTFS estático capturado en MP-003/MP-004.
- **Entregables:** parser de topología GTFS para C5, validación de que el recorrido de estaciones coincide con lo esperado (orden, direcciones).
- **Criterios de aceptación:** topología validada contra el GTFS estático real, sin datos inventados.
- **Pruebas necesarias:** tests de parseo de `routes`, `trips`, `stops`, `stop_times`, `shapes` para C5.
- **Evidencia de verificación:** 71/71 tests en verde (7 GTFS nuevos + 64 de regresión: 31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL. Los 7 tests de topología usan una reducción trazable del GTFS real (SHA-256 y proceso en `tests/fixtures/gtfs_c5_real/MANIFEST.md`). Ejecución adicional directa contra el ZIP oficial completo del `2026-11-19`: 5 rutas, 8.160 trips, 23 estaciones, 165.205 stop_times, 630 puntos de shape, 30 servicios, 14 patrones de recorrido y 8 trips huérfanos de `10T0035C5`; validación estructural sin errores. Hallazgo de fuente: `trips.txt` no trae `direction_id`; la dirección se valida mediante los patrones ordenados de `stop_sequence`/`shape_id`, sin inventar columna.
- **Nota de alcance (ADR-0011, `Propuesto`):** la resolución de `route_id`/`trip_id`/`stop_id` debe ser genérica (sin literales `"C5"` hardcodeados en la lógica), aunque Hito 2 solo pueble datos de C5 — ver `docs/adr/0011-public-scope-vs-technical-pilot.md`.
- **Estado:** `DONE` — implementación de Codex (commit `add8aa6`) auditada y aprobada por Claude Code el 2026-11-19. Revisión independiente: código de `packages/gtfs/` leído íntegro; 71/71 tests reejecutados de forma propia (7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter), subiendo y bajando el contenedor `madrid-pulse` yo mismo y confirmando los recuentos reales `668/484/3/120/0` idénticos antes y después (sin residuo). Confirmado que `parser.py` no contiene el literal `"C5"` (lo exige además un test de regresión propio) y que `load_feed`/`route_groups`/`resolve_trip_route_id` son genéricos por `route_ids`/`network_id`/`short_name`, conforme a ADR-0011. `git diff --check` limpio, sin secretos, identidad Git correcta (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor), enlaces a ADR-0011/DEC-022/DEC-023 resuelven. Sin hallazgos bloqueantes ni menores.

---

## MP-011 — Prototipo de geometría ferroviaria sobre OSM

- **Fase:** F5 — Geometría y topología
- **Objetivo:** derivar geometría ferroviaria de la C5 desde OpenStreetMap, con atribución y registro de casos ambiguos.
- **Prioridad:** P1
- **Depende de:** MP-010
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `packages/geo/`.
- **Entradas:** topología GTFS (MP-010), datos OSM.
- **Entregables:** geometría de la C5 entre estaciones consecutivas, atribución ODbL incluida, documentación de ambigüedades (vía doble, cambios de ancho, etc.) sin copiar la implementación de Via Península.
- **Criterios de aceptación:** geometría renderizable y revisable visualmente contra el trazado real; atribución OSM presente.
- **Pruebas necesarias:** test de continuidad geométrica (sin saltos) entre estaciones consecutivas de la C5.
- **Evidencia de verificación:** `packages/geo/` implementado (`overpass.py`, `corridor.py`, `geometry.py`) contra 4 relaciones OSM reales (`11331`/`3418148`/`3418149`/`3418150`, `ref=C-5`/`network=Cercanías Madrid`). 8 tests nuevos en verde + 71 de regresión (79/79 totales): las 4 relaciones encadenan sus `ways` de vía sin huecos; las 23 estaciones reales de la ruta larga (ambos sentidos) proyectan en orden monótono sobre su corredor con distancia máxima real de 63,7 m; la variante base de 6 estaciones de la ruta corta (`10T0047C5`) se confirma como subsecuencia **contigua** real de paradas de la ruta larga (comparación literal de IDs, no solo orden monótono), sin geometría inventada. **Primera revisión independiente de Codex: no aprobada** — bloqueante real (`ChainGap` se registraba pero `project_station`/`corridor_length_m` seguían fabricando una unión a través del hueco; repro sintética con `distance_m=0.0`) + 2 menores (recuento de tests incorrecto; una variante real de 7 estaciones de `10T0047C5` se documentó como "subsegmento contiguo" sin serlo — sí proyecta monótonamente, pero omite 4 paradas intermedias reales; checksums anunciados pero ausentes del manifiesto). Corregido: `Corridor.segments` separa tramos reales (ya no se puede fabricar distancia a través de un hueco, con test de regresión verificado revirtiendo el fix y confirmando que falla); `render_preview.py` dibuja un `<polyline>` por tramo; test de la ruta corta dividido en "variante base contigua" (6 estaciones) y "variante con Atocha, monótona pero no contigua" (7 estaciones); 4 SHA-256 añadidos al `MANIFEST.md` y verificados. Renderizado y revisado visualmente en navegador (Chrome DevTools MCP, captura completa): forma real de la C5 reconocible, estaciones sobre la vía sin saltos — ver `packages/geo/README.md`. Atribución ODbL en `docs/legal/ATTRIBUTION.md`/`docs/legal/DATA_SOURCES.md` (DEC-024). Ambigüedades documentadas, no forzadas: relaciones "Fuenlabrada→Atocha→Móstoles" sin coincidir con el patrón corto real, huérfano `10T0035C5` aún sin validar, trazado troncal (`usage=main`) vs. ramal (`usage=branch`) sin verificar qué otras líneas comparten el tramo (DEC-025).
- **Estado:** `DONE` — segunda verificación independiente de OpenAI Codex aprobada el 2026-11-19 sobre `f795036`. Leído íntegramente `packages/geo/corridor.py`; reproducción sintética propia con dos `ways` desconectados confirmó 2 tramos, `distance_m=2223,9 m` en el centro del hueco (no ~0) y longitud limitada a los tramos reales. Ejecutados realmente 8/8 tests geo y 71/71 de regresión (79/79 total), con PostgreSQL `668/484/3/120/0` idéntico antes/después y contenedor bajado sin borrar el volumen. Comparación literal propia: patrón base de 6 estaciones contiguo en índice 16 del patrón largo; variante de 7 con Atocha no contigua (posiciones 11,16–21), aunque monótona. Los 4 SHA-256 coinciden con el manifiesto; `git diff --check fbc3fde..f795036` limpio e identidad Git correcta, sin coautor. Sin hallazgos abiertos.

---

## MP-012 — Motor de movimiento v1

- **Fase:** F6 — Motor de movimiento
- **Objetivo:** implementar los estados `OBSERVED / ESTIMATED / STALE / SCHEDULED` con tests deterministas.
- **Prioridad:** P1
- **Depende de:** MP-008, MP-010, MP-011
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Nota de worktree (resuelta el 2026-11-19, DEC-015):** MP-012 depende de MP-008, MP-010 y MP-011. Con Hito 1 ya fusionado a `main`, MP-008 es ancestro de `main` (`git merge-base --is-ancestor origin/main HEAD` confirmado `true` desde `mp-011-osm-geometry`); al ramificar MP-012 desde `mp-011-osm-geometry` (que a su vez parte de MP-010), las tres dependencias quedan satisfechas sin ningún `git merge` real — ver mecanismo general en `AGENTS.md` y resolución aplicada en `docs/STATUS.md`.
- **Archivos/componentes afectados:** `packages/geo/`, `packages/quality/`, lógica de movimiento (ubicación exacta a definir en ADR si no cabe en paquetes existentes).
- **Entradas:** flags de calidad (MP-008), topología (MP-010), geometría (MP-011).
- **Entregables:** motor de movimiento con los cuatro estados, `confidence`, `age_s`, umbrales parametrizados (no fijos) siguiendo `docs/DATA_QUALITY.md`.
- **Criterios de aceptación:** tests deterministas cubren transición entre estados, saltos de estación y velocidades físicamente inverosímiles.
- **Pruebas necesarias:** suite de tests deterministas del motor de movimiento.
- **Evidencia de verificación:** `packages/movement/` implementa el pipeline completo de ADR-0004 como capa independiente (ADR-0012, `Propuesto`): resolución GTFS literal, map-matching mediante `Corridor.project_station`, perfil horario con horas >24/cambio de día de servicio, offset temporal, interpolación limitada por aceleración/velocidad y fallback a la última muestra plausible. Contrato directo para MP-013 con `position_mode`, `confidence`, `age_s`, `source` y anomalías estructuradas. Defaults `60s/180s` mantenidos tras calibración contra la cadencia real ~20–22 s; límite físico estimado 160 km/h separado del filtro de salto de feed 900 km/h. `off_track`/`backward_jump`/`station_skip_anomaly` implementados y expuestos; persistencia diferida explícitamente porque `data_quality_event` v1 representa observaciones crudas, no posiciones derivadas. **90/90 tests reales en verde:** 11 movement (10 deterministas + 1 integración PostgreSQL), 7 GTFS, 8 geo, 31 contratos, 6 fixtures, 9 collector, 13 quality y 5 snapshotter. Integración de solo lectura sobre el soak: `668` posiciones antes/después, 177 a ≤200 m del corredor, máximo salto map-matched 666,4 km/h; volumen completo conservado `668/484/3/120/0`. `python -m compileall` y `git diff --check` sin errores al cierre.
- **Estado:** `DONE` — implementación de Codex (commit `1edfa14`) auditada y aprobada por Claude Code el 2026-11-19. Revisión independiente: `packages/movement/` leído íntegro (`model.py`, `schedule.py`, `engine.py`); 90/90 tests reejecutados de forma propia, incluida la integración real de solo lectura contra PostgreSQL (668/484/3/120/0 confirmados idénticos antes y después), subiendo/bajando el contenedor yo mismo. Verificado el pipeline matemáticamente: offset temporal correcto en ambos sentidos del corredor (`directed_progress`/`physical_arc`), estimación nunca retrocede y queda acotada por velocidad/aceleración, fallback a última observación plausible reaplica la clasificación de estado completa por recursión (no fuerza `OBSERVED` artificialmente), separación deliberada y bien calibrada entre el límite físico de interpolación (160 km/h) y el filtro de discontinuidad del feed (900 km/h, coherente con los 246-787 km/h ya encontrados en MP-008 y el máximo real map-matched de 666,4 km/h). Confirmado que `engine.py`/`model.py`/`schedule.py` no contienen el literal `"C5"`. Identidad Git correcta (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor), `git diff --check` limpio, sin secretos, ADR-0012 y DEC-026 coherentes y enlazados. Sin hallazgos bloqueantes ni menores.

---

## MP-013 — FastAPI v1

- **Fase:** F7 — API propia
- **Objetivo:** API propia versionada con OpenAPI, endpoints de vehículos en vivo, salud de feed, líneas y estaciones.
- **Prioridad:** P1
- **Depende de:** MP-005, MP-007, MP-012
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `apps/api/`.
- **Entradas:** contrato canónico (MP-005), datos del colector (MP-007), motor de movimiento (MP-012).
- **Entregables:** API FastAPI conforme a `docs/DATA_CONTRACTS.md`, OpenAPI publicado.
- **Criterios de aceptación:** endpoints responden con los campos de frescura/calidad exigidos; sin inventar datos ausentes como ceros.
- **Pruebas necesarias:** tests de contrato de API (schema de respuesta, casos de borde de frescura).
- **Evidencia de verificación:** `apps/api/` implementado (FastAPI real, `psycopg` directo, resolución vía `packages.gtfs`/`packages.geo`/`packages.movement`, sin SQL a `route`/`station`/`trip` porque esas tablas siguen vacías y `vehicle_position_observation.trip_id` sigue `NULL` en los datos reales — verificado empíricamente contra PostgreSQL, consistente con el diferimiento de esa resolución a MP-010 ya documentado en ADR-0008/DEC-020). 7 endpoints reales: `health`, `live/vehicles`(`/{id}`), `lines`(`/{id}`), `stations`(`/{id}`); `history`/`metrics` diferidos explícitamente (DEC-027, DATA_CONTRACTS.md). OpenAPI generado y congelado en `apps/api/openapi.json`. 11 tests de contrato + regresión completa, **101/101 en verde**: 11 movement + 7 GTFS + 8 geo + 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter + 11 API, incluidas las integraciones reales contra PostgreSQL. App arrancada de verdad con `uvicorn` y probada con `curl` real (`/api/v1/lines`, `/docs`). Hallazgos reales: de los 24 vehículos distintos del soak de MP-007 solo 4 son C5; 19 pertenecen a C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 y 1 trip de refuerzo no resuelve (confirma DEC-020 — DEC-029); un único corredor OSM basta para ambos sentidos de C5 porque el horario detecta el sentido automáticamente (DEC-028); la API nunca fabrica `route_id`/posición para un vehículo no resoluble, devuelve `null` honesto (probado explícitamente). Nueva dependencia `fastapi`/`uvicorn`/`httpx` documentada (DEC-030). **Revisión final independiente de Codex:** los dos bloqueantes de la primera ronda y el cruce GTFS completo quedaron verificados en la segunda ronda (101/101); en la ronda final, `15170c4` solo corrige el docstring residual para enumerar las 9 líneas y el trip sin resolver (`git diff --check c82e62f..15170c4` limpio), 11/11 tests API pasan y PostgreSQL conserva `668/484/3/120/0`. Autor y committer: `Pedro Matute <pedromaaz13@gmail.com>`, sin coautor. Sin hallazgos abiertos.
- **Estado:** `DONE` — revisión final independiente de OpenAI Codex aprobada el 2026-11-19 sobre `15170c4`.

---

## MP-014 — Frontend React/MapLibre C5

- **Fase:** F8 — Frontend Live
- **Objetivo:** mapa funcional de la C5 con movimiento y visualización explícita de incertidumbre de posición.
- **Prioridad:** P1
- **Depende de:** MP-013
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `apps/web/`.
- **Entradas:** API v1 (MP-013).
- **Entregables:** mapa React/TypeScript/MapLibre consumiendo la API real, con diferenciación visual de los cuatro estados de posición y atribución OSM visible en UI.
- **Criterios de aceptación:** demo funcional contra API real (no mocks), estados de posición distinguibles por el usuario.
- **Pruebas necesarias:** smoke test de carga de mapa y de consumo de API; verificación manual en navegador (no solo tests automatizados).
- **Evidencia de verificación:** API real + GTFS oficial completo + PostgreSQL + un ciclo fresco de `vehicle_positions`: `/api/v1/live/vehicles` devolvió 145 vehículos, 31 map-matched sobre el corredor de la línea y los cuatro estados simultáneamente (`observed` 24, `estimated` 2, `stale` 4, `scheduled` 1); los 114 restantes permanecen visibles como no ubicables, sin ruta/posición fabricada. Regresión Python completa 102/102 (12 API + 90 previos); frontend lint, typecheck, 5/5 tests y build en verde. Los cuatro runs del smoke se retiraron por ID y el volumen PostgreSQL quedó restaurado exactamente a `668/484/3/120/0`. Claude auditó en cuatro rondas con navegador real: (1) desktop/estrecho/estados/nulls/atribución correctos, bloqueante de `504` en el worker de Vite dev; (2) dev corregido, pero el worker no se emitía en la build de producción (fallback HTML); (3) worker de producción corregido y verificado por SHA-256, pero una carrera de carga en frío retrasaba corredor/estaciones hasta el siguiente poll; (4) build de producción reconstruida, 3/3 pestañas nuevas (carga en frío) mostraron corredor/23 estaciones de inmediato sin errores de consola, dev revalidado, interacción de capas comprobada. Las cuatro rondas de hallazgos quedaron corregidas y re-verificadas.
- **Estado:** `DONE` — implementación de Codex auditada por Claude Code (código + cuatro rondas de inspección visual real en navegador) en el mismo worktree; todos los hallazgos corregidos y re-verificados.

---

## MP-015 — E2E y readiness MVP

- **Fase:** F9 — Histórico/Explore y endurecimiento
- **Objetivo:** validación end-to-end completa, CI verde, checklist de preparación de MVP y ADRs actualizados a la implementación real.
- **Prioridad:** P1
- **Depende de:** MP-009, MP-012, MP-013, MP-014
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `tests/e2e/`, `.github/workflows/` (si se crea en esta tarea), `docs/adr/`, `analytics/dbt/`, `analytics/duckdb/` (ampliación de métricas con cobertura, ver `docs/PLAN.md` F9).
- **Entradas:** todos los componentes de F1 a F8.
- **Entregables:** replay E2E completo, pipeline CI configurado y verde, checklist de MVP documentado, ADRs reconciliados con la implementación final.
- **Criterios de aceptación:** checklist de MVP superado y aceptado por el propietario; ningún ADR describe algo distinto de lo implementado.
- **Pruebas necesarias:** suite E2E completa + CI.
- **Evidencia de verificación:** `daily_line_metrics`/`station_daily_metrics` reales (DEC-033), con porcentajes en la escala contractual `0..100`; CI verificado contra la base de desarrollo (115/115 sin `skip`) y dos PostgreSQL frescos (la última corrida: 110 en verde + 5 `skip`, de 115; DEC-035); replay E2E determinista (`tests/e2e/test_replay.py`, dos escenarios reales); frontend lint/typecheck/5 tests/build en verde; auditoría de contenido de los 12 ADRs y nuevo ADR-0013 (`Propuesto`, ningún `Estado` promovido); `docs/MVP_READINESS.md` y recuperación fiel de `docs/HITO_3_BACKLOG.md` desde una rama divergente. Codex auditó el diff completo y realizó dos rondas de hallazgos: seis correcciones funcionales/documentales en la primera y tres de gobernanza/coherencia en la segunda, todas re-verificadas. Detalle completo en `docs/STATUS.md` → "Tarea actual".
- **Estado:** `DONE` — implementación de Claude Code aprobada por OpenAI Codex tras auditoría completa y dos rondas de corrección/re-verificación en el mismo worktree. Hito 2 queda funcionalmente cerrado; el propietario decide la auditoría de integración final y el momento de fusionar a `main`.

---

# Hito 3 — MP-016 a MP-022 ("toda Cercanías Madrid")

Autorizado por el propietario el `2026-11-22` (mensaje "ORCA — MADRID PULSE / EJECUCIÓN AUTÓNOMA DEL HITO 3"), a partir del kit externo `~/Documents/DATA/Madrid-Pulse-Orca-Hito3-FINAL/` (versión `hito3-v4-definitivo`, integridad verificada — 48 archivos, hashes OK). El kit queda instalado en `docs/hitos/hito-03/` de cada worktree de esta cadena (documentos, prototipo `diseno/live.html`, mockups); `data/hito-03/` (replay 1532/1533, GTFS oficial, parche de referencia) vive fuera de Git bajo la regla `/data/` ya existente en `.gitignore`. Fuente de verdad del reparto/dependencias: `docs/hitos/hito-03/PLAN-Y-ACEPTACION.md`; criterios de aceptación vinculantes adicionales en `MATRIZ-CIERRE-MADRID.md`, `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md` y `ANEXO-CRITICO-POSICION-Y-RELOJ.md` del mismo directorio. Protocolo de autonomía/permisos del coordinador: `AUTONOMIA-ORCA-Y-PERMISOS.md`.

## MP-016 — Fiabilidad realtime (SKIPPED, UTC, live/replay)

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** reproducir y corregir los hallazgos de fiabilidad de ingesta/colector/API documentados en `docs/hitos/hito-03/referencia/01-auditoria-live.md` antes de tocar el resto de la cadena: paradas `SKIPPED` sin `arrival`, timestamps UTC leídos de PostgreSQL, distinción explícita live/replay, salud de feed/collector/GPS medida por separado.
- **Prioridad:** P0
- **Depende de:** MP-015 (`DONE`, fusionada a `main` en `990c95d`)
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `services/collector/`, `packages/contracts/`, `packages/quality/db.py`, `apps/api/db.py`, `apps/api/service.py`, `apps/api/tests/test_api_contract.py`, `tests/e2e/test_replay.py` — ver el alcance exacto en `data/hito-03/madrid-pulse-live.patch` (referencia, no aplicar ciegamente; 11 ficheros tocados, inspeccionar y adaptar al HEAD real de `main`/`990c95d`).
- **Entradas:** `docs/hitos/hito-03/referencia/01-auditoria-live.md`, `data/hito-03/replay/` (capturas `1532`/`1533`, GTFS oficial `fomento_transit.zip`, `comprobar.py`), parche de referencia.
- **Entregables:** parser/colector corregido con fixtures verificadas; `SKIPPED` sin `arrival` tratado como afecta-a-la-parada (no congela la circulación completa salvo evidencia de cancelación real); edad de observación visible aunque se use un ancla anterior; arranque local documentado con modos `Live` y `Replay` explícitos.
- **Criterios de aceptación:** replay reproduce los conteos congelados del kit (corte `1532`: 119 vehículos Madrid, 119 matches, 49 `SKIPPED` sin `arrival`; corte `1533`: 121 matches, 49 `SKIPPED`) — conteos de fixture, no expectativa del feed en vivo de hoy. Tests reales contra PostGIS, no solo la sonda Python del replay. Casos probados: respuesta inválida, reloj desfasado, colector detenido.
- **Pruebas necesarias:** suite real del proyecto (Python contra PostgreSQL real) + `python3 data/hito-03/replay/comprobar.py` como sonda adicional, nunca sustituto.
- **Evidencia de verificación:** replay Hito 3 exacto (`1532`: 119/119/49; `1533`: 121/121/49); 123/123 tests Python contra PostgreSQL de desarrollo y 118 en verde + 5 `skip` documentados (de 123) contra PostGIS 17-3.5 fresco; frontend lint/typecheck/5 tests/build en verde; reproducción real `SHOW TIME ZONE = Europe/Madrid` y normalización `+01:00`→UTC; `/api/v1/health` real muestra los tres feeds `stale` por separado, con edad de fuente y de sondeo. Detalle y comandos en `docs/STATUS.md` → "Tarea actual".
- **Estado:** `DONE` — implementación de Codex auditada por Claude Code (diff completo, re-ejecución independiente de la suite contra dev y contra un segundo PostgreSQL fresco, verificación en vivo del escenario "colector detenido") en el mismo worktree; sin hallazgos.

---

## MP-017 — Catálogo completo de Madrid (identidad y vigencia)

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** catálogo versionado de todo el núcleo Madrid (línea/variante/patrón) desde el GTFS completo, enumeración explícita de servicios programados elegibles (calendar + calendar_dates), y resolución de avisos por estación sin fabricar matches.
- **Prioridad:** P0
- **Depende de:** MP-016 (`DONE`)
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `packages/gtfs/` (nuevo `catalog.py`, `parser.py` extendido con `calendar_dates.txt` opcional), `packages/contracts/` (`raw.py`/`canonical.py`/`normalize.py`: `stop_id` en avisos), `services/collector/` (`collector.py`/`__main__.py`/`config.py`: resolución de avisos por estación), `apps/api/db.py`/`service.py` (ventana de recencia en `latest_trip_update`).
- **Entradas:** GTFS oficial completo (`data/hito-03/replay/fomento_transit.zip` o `data/gtfs_static/fomento_transit.zip`, ambos fuera de Git), `docs/hitos/hito-03/referencia/01-auditoria-live.md` (hallazgo P1 "Avisos de estación").
- **Entregables:** `packages.gtfs.catalog`: `build_catalog` (líneas/variantes/patrones, conserva líneas con 0 patrones válidos), `scheduled_service_ids_for_date`/`scheduled_trip_instances_for_date` (enumeración real de servicios programados, no el fallback `SCHEDULED` del motor), soporte opcional de `calendar_dates.txt`. Avisos por estación (`stopId` sin `routeId`) resueltos contra el catálogo real de paradas de Madrid, no descartados por defecto. Ventana de recencia (20h) en `latest_trip_update` para que un retraso de un día de servicio anterior no complete el viaje de hoy.
- **Criterios de aceptación:** 42 `route_id` agrupados en 12 nombres de línea/variante (verificado contra el GTFS oficial real); las 12 permanecen en catálogo aunque alguna tenga cero vehículos; `stopId` 60104 (Valdemoro) resuelve como estación real de Madrid; un `trip_id` `SPECIAL_` nunca aparece como instancia programada; un trip con horas `24:xx` real (`1023V19788C5`) se enumera correctamente sin desplazar `service_date`; un retraso de hace 26h no completa el viaje de hoy.
- **Pruebas necesarias:** suite real del proyecto + nuevo módulo `packages.gtfs.tests.test_catalog` (lógica síncrona con topología sintética + clase gateada por la presencia del ZIP oficial, `skip` explícito si no está, igual criterio que el soak de MP-007).
- **Evidencia de verificación:** 141/141 tests contra la base de desarrollo real (`668/484/3/120/0` intacto); 141 tests/10 `skip` contra un segundo PostgreSQL fresco desechable con `data/` ausente (simulando CI real sin el ZIP oficial). Primera revisión de Codex encontró dos hallazgos reales (versión/procedencia e identidad red/operador ausentes en el catálogo; sin estado activo/caducado separado del último histórico) — ambos corregidos y re-verificados. Detalle completo en `docs/STATUS.md` → "Tarea actual".
- **Estado:** `DONE` — implementación de Claude Code aprobada por OpenAI Codex tras tres rondas de revisión/corrección (versión/procedencia e identidad red/operador; estado activo/caducado de la circulación; sincronización del contrato OpenAPI/frontend) en el mismo worktree; sin hallazgos abiertos.

---

## MP-018 — Corredores ferroviarios por patrón y sentido

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** extender la geometría OSM de un único corredor fijo (C5, MP-011) a un catálogo de corredores indexado por patrón y sentido, con matriz de cobertura honesta (`validated`/`partial`/`pending`) para las 12 líneas del catálogo de MP-017.
- **Prioridad:** P0
- **Depende de:** MP-017 (`DONE`)
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code (posible escalado a Opus por complejidad geoespacial, política de selección de modelo ya fijada en Hito 2)
- **Archivos/componentes afectados:** `packages/geo/` (nuevo módulo de catálogo de corredores), nuevas fixtures OSM reales versionadas (`tests/fixtures/osm_*_real/`, análogas a `osm_c5_real`).
- **Entradas:** `packages.gtfs.catalog` (MP-017, patrones/líneas completos), Overpass API (geometría real).
- **Entregables:** catálogo de `Corridor` por patrón/sentido; matriz de cobertura de las 12 líneas; al menos un ramal de C4 y un tramo compartido con geometría OSM real descargada y versionada (mismo formato que `osm_c5_real/MANIFEST.md`); proyección/distancia trazable (`Projection`/`distance_from_raw_m`) reutilizable por MP-019.
- **Criterios de aceptación:** C5 sigue encadenando sin huecos; nuevo ramal C4 y tramo compartido verificados contra Overpass real, con hallazgos (huecos, ambigüedades) documentados, no forzados; matriz de cobertura cubre los patrones de las 12 líneas, mayoría `pending` honesto, no fabricado.
- **Pruebas necesarias:** suite real del proyecto + nuevos tests de geometría real (Overpass).
- **Evidencia de verificación:** `packages.geo.tests.test_catalog` (11 pruebas: 3 ejecutables en CI sin el ZIP no versionado + 8 contra el catálogo oficial completo), regresión `packages.geo.tests.test_real_feed`; matriz exportada de 103 patrones/12 líneas (`28 validated`, `3 partial`, `72 pending`). Suite Python exacta de CI: **153/153 OK** contra PostgreSQL real, recuentos antes/después `668/484/3/120/0`; frontend Node `22.13.1`: lint/typecheck/5 tests/build en verde; `git diff --check` limpio. Re-verificado de forma independiente por el revisor sobre `1b19df8`: **153/153 OK sin `skip`** contra la base de desarrollo y **153 ejecutados con 5 `skip` explícitos** (soak irrepetible de MP-007, DEC-035) contra un segundo PostgreSQL fresco desechable; matriz regenerada byte-idéntica al CSV versionado y los 77 `way` compartidos C4a/C4b reproducidos de forma independiente (tramo contiguo de 41,65 km). Overpass respondió 502 dos veces para C4b Parla→Colmenar (`9174512`), registrado como `pending`, no como ausencia de relación.
- **Estado:** `DONE` — implementación de OpenAI Codex aprobada por Claude Code el `2026-11-22` tras dos rondas en el mismo worktree. La primera auditoría confirmó código, fixtures y pruebas pero detectó un hallazgo real: los registros legales centrales de DEC-024 nombraban solo la base derivada C5. Corregido en `1b19df8` sin tocar código (`ATTRIBUTION.md`, la fila `osm.rail_geometry` de `DATA_SOURCES.md` y DEC-024 ya cubren `osm_c4_real/` y las relaciones `11332`/`9174510`/`9174511`) y re-verificado por el revisor. Sin hallazgos abiertos.

---

## MP-019 — Contrato de snapshot/API coherente

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** snapshot API coherente y cacheable (catálogo separado del feed operativo, lote/batch sin N+1), con separación explícita raw/matched/rendered, ETA con método/procedencia, y un contrato temporal de movimiento elegido por ADR comparativo (no una segunda implementación divergente del motor de MP-012).
- **Prioridad:** P0
- **Depende de:** MP-018 (`DONE`)
- **Ejecutor:** Claude (escalado a Opus — decisión arquitectónica de alto impacto, política de modelo de Hito 2)
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `apps/api/` (nuevo contrato de snapshot), `packages/movement/` (si el ADR exige extenderlo, no duplicarlo), `docs/adr/` (nuevo ADR propuesto).
- **Entradas:** `packages.gtfs.catalog` (MP-017), `packages.geo.catalog` (MP-018, `PositionMatch`/`CorridorCatalog`), `packages.movement` (MP-012).
- **Entregables:** ADR propuesto comparando las tres alternativas de contrato temporal (`docs/hitos/hito-03/MEJORAS-PRODUCTO-VALIDADAS.md`, sección MP-019); snapshot con `snapshot_id` no asumido como ordenable; catálogo cacheable separado del snapshot ligero; ETA con edad de GPS/feed/ETA distintas y procedencia (operador/horario/calculado); tablero de estación basado en servicios+calendario+RT, no en "trenes cercanos".
- **Criterios de aceptación:** tres snapshots (normal/parcial/congelado) se distinguen correctamente; el último snapshot válido sobrevive al fallo de un feed; EXPLAIN + p50/p95 medidos; semántica `0` vs `NULL` correcta; sin N+1 por tren; contrato versionado si rompe compatibilidad.
- **Pruebas necesarias:** suite real del proyecto + nuevos tests de contrato/snapshot.
- **Evidencia de verificación:**
  - [ADR-0014](adr/0014-snapshot-and-temporal-contract.md) escrito **antes** de implementar, comparando las tres alternativas del encargo más dos evaluadas y descartadas. Estado `Propuesto`; no lo promueve el ejecutor.
  - Suite Python exacta de `.github/workflows/ci.yml` (con los dos módulos nuevos, `apps.api.tests.test_snapshot_contract` y `packages.movement.tests.test_rendering`): **206/206 OK sin `skip`** contra la base de desarrollo real; recuentos `668/484/3/120/0` idénticos antes y después.
  - Misma suite contra un contenedor PostgreSQL fresco y desechable con `0001`+`0002` aplicadas desde cero: **206 ejecutados, OK con 5 `skip` explícitos** (soak irrepetible de MP-007, DEC-035), repetido tres veces.
  - Frontend con Node `20.20.0`: `npm ci`, lint, typecheck, **5/5 tests**, build (worker MapLibre `550754` bytes).
  - Tres snapshots reales (normal/parcial/congelado) sobre las capturas `1532`/`1533` con reloj controlado y contenedor desechable: `docs/evidence/mp-019-tres-snapshots-replay.md`. 119 y 121 vehículos de Madrid; 13 circulaciones map-matcheadas con avance real; revisión `3 → 6 → 8` en el mismo ámbito; fallo parcial que degrada solo `delays_and_eta`; congelado que conserva el último dato válido sin rejuvenecerlo.
  - `EXPLAIN (ANALYZE, BUFFERS)` de las cuatro consultas y p50/p95 en dos datasets (fixture C5 y núcleo Madrid completo, 42 rutas/12 líneas/103 patrones), con equipo documentado: `docs/evidence/mp-019-explain-y-bench.md`.
  - Ausencia de N+1 probada por conteo de `execute` reales: constante entre 6 y 18 vehículos en `/snapshot`, entre 4 y 14 en `/live/vehicles`, y sin consulta por fila en el tablero.
- **Primera auditoría de Codex (dos hallazgos bloqueantes, corregidos):** (1) `service_instant` no era la inversa de `service_seconds` en los dos días de cambio de hora —`03:30` se reconstruía como `04:30+02` el `2026-03-29` y como `02:30+01` el `2026-10-25`— porque sumaba los segundos sobre un desplazamiento fijo; corregido con una única implementación explícita de reloj de pared en ambas direcciones. (2) La fecha de servicio se elegía por reloj civil y descartaba los viajes `24:xx` del día anterior: a las `00:02` el viaje real `1023V20533C4` se situaba a **10 445 m** de su posición y aparecía `expired` (742 circulaciones de Madrid tienen horas `24:xx` en el ZIP oficial); corregido con `ServiceDateResolver`, que resuelve la fecha por circulación con una ventana derivada del horizonte del propio feed. Evidencia: `docs/evidence/mp-019-dst-y-horas-extendidas.md`; decisión: DEC-039. 16 regresiones nuevas, fixture real `tests/fixtures/gtfs_24h_real/` con su manifiesto y registro legal.
- **Segunda auditoría de Codex (un tercer hallazgo bloqueante, corregido):** `build_station_board` calculaba sus días de servicio candidatos con `now` y no con la ventana pedida, así que al rebasar el horizonte del feed dejaba de consultar el día anterior pese a `lookback_s`: con `gtfs_24h_real`, estación `17000` y `lookback_s=600`, la llamada real de las `24:32` desaparecía a las `00:33`, un minuto después de ocurrir (reproducido también con `1023V21644C2`/`24:53` en `70200` contra el ZIP). El mismo error existía **en el sentido contrario** y no venía en el informe: a las `23:55` no se consultaba el día siguiente y se perdía `1024S27997C5` (salida `00:01`) a seis minutos dentro de `lookahead_s`. Corregido con `service_dates_covering`, que cubre toda la ventana; el límite pasa a ser la ventana pedida (`00:31`–`00:42`, fuera en `00:43`). 11 regresiones nuevas, comprobadas fallando (13 fallos) contra el código anterior.
- **Evidencia reejecutada tras cada ronda (cifras de la última):** **233/233 OK sin `skip`** contra desarrollo (recuentos `668/484/3/120/0` intactos); **233 ejecutados con 5 `skip` explícitos** contra PostGIS fresco con ambas migraciones desde cero; frontend con **Node `22.13.1`** (la versión de CI) en verde con **5/5 tests**; replay de tres snapshots con las siete invariantes en verde; p50/p95 remedidos en los tres escenarios del tablero (uno y dos días candidatos, hacia atrás y hacia delante). Evolución de la suite: 206 → 222 → 233.
- **Re-verificación final independiente de Codex (2026-11-22):** aprobado el delta hasta `60a6eb3` sin hallazgos abiertos. Reproducción propia contra el ZIP completo: `1023V21644C2` permanece en el tablero hasta `01:03` y sale a `01:04` con `lookback_s=600`; `1024S27997C5` aparece desde las `23:55` dentro de `lookahead_s=3600`, consultando los días 20 y 21 y conservando el orden por instante absoluto. Reejecutados realmente los 11 tests focales, 233/233 sin `skip` contra desarrollo, 233 con 5 `skip` contra PostGIS fresco con `0001`+`0002`, frontend completo con Node `22.13.1` y replay de tres snapshots con las siete invariantes. `git diff --check` y autoría exclusivos de Pedro Matute, sin coautor.
- **Hallazgos abiertos (no silenciados):** el coste dominante de cada petición es abrir la conexión PostgreSQL (~66 ms de 68,91 ms de p50 en `/health`), registrado como DEC-038 porque un pool es dependencia nueva; y el `stop_time_update` por parada no está persistido en el modelo canónico, así que no hay evidencia directa de `SKIPPED` por parada (declarado en `limitations` del tablero).
- **Estado:** `DONE` — implementación de Claude Opus aprobada por OpenAI Codex el 2026-11-22 tras tres rondas de auditoría/corrección en el mismo worktree. Los tres hallazgos temporales quedaron corregidos y re-verificados de forma independiente; no quedan hallazgos abiertos. ADR-0014 permanece `Propuesto` para decisión exclusiva del propietario.

---

## MP-020 — Mapa y tablero (React/MapLibre)

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** reconstruir el frontend (hoy limitado a C5, MP-014) como la experiencia map-first de `diseno/live.html`/mockups: mapa de toda Cercanías Madrid, búsqueda, multiselección de líneas, tablero de estación, seguimiento de circulación, movimiento fluido entre polls sobre la geometría real, consumiendo el contrato `/api/v1/catalog`+`/api/v1/snapshot`+`/api/v1/stations/{id}/board` de MP-019.
- **Prioridad:** P0
- **Depende de:** MP-019 (`DONE`)
- **Ejecutor:** Claude (escalado a Opus — rediseño de frontend de alto impacto, política de modelo de Hito 2)
- **Revisor:** OpenAI Codex (auditoría con inspección visual real en navegador, no solo tests automatizados)
- **Archivos/componentes afectados:** `apps/web/` (refactor completo).
- **Entradas:** `docs/hitos/hito-03/diseno/live.html`+PNGs+`INTERACCIONES.md`; contrato de MP-019 (`CatalogOut`/`SnapshotOut`/`StationBoardOut`, `RenderedOut` con `rendering_method`/`progress_m`/`valid_until`).
- **Entregables:** mapa persistente (una instancia MapLibre, marcadores reconciliados por ID estable, nunca recreados por poll); animación por longitud de arco sobre `ProgressEnvelope` (nunca interpolación lat/lon en línea recta); selección/cámara/seguimiento que sobreviven a polls y fallos recuperables; búsqueda+filtros multi-línea; tablero de estación; móvil 390px, teclado, `prefers-reduced-motion`, fallback sin WebGL.
- **Criterios de aceptación:** recorrido completo (Madrid → elegir 2 líneas → estación compartida → salida → tren → Seguir → arrastrar → Volver → History) en escritorio y móvil 390px; dos actualizaciones conservan cámara/selección; frames intermedios varían suavemente sin "teletransporte"; estados con procedencia visible (nunca GPS fabricado); grabación real de ≥60s, no solo capturas estáticas del prototipo.
- **Pruebas necesarias:** suite real del proyecto + inspección visual real en navegador (Claude/Codex, Chrome DevTools MCP) — no se acredita con tests automatizados únicamente.
- **Evidencia de verificación:** `docs/evidence/mp-020-inspeccion-navegador.md` (inspección real en navegador, con las capturas de `docs/evidence/mp-020-capturas/`). Resumen: secuencia continua de **60 s** de la app real siguiendo la circulación `19656` (C5) con 13 muestras de fotogramas intermedios, avance de 110,1–110,5 m cada 5 s = **22,0 m/s**, exactamente el `speed_mps` que publica su envolvente, **1 316,7 m** recorridos y sin teletransporte; coordenada del cliente sobre la del backend con **error < 1 m** en test y 6,6 cm medidos en Python sobre las 44 circulaciones map-matcheadas; cámara/selección/seguimiento intactos tras dos sondeos y tras una caída de 26 s del backend con la edad avanzando («hace 1 min» → «hace 2 min») y sin rejuvenecer al recuperarse; móvil 390 px sin desbordamiento horizontal; teclado completo con foco visible; `prefers-reduced-motion` con deriva nula dentro de un intervalo; fallback sin WebGL navegable. Suites reales con Node `22.13.1`: web **49/49**, lint y typecheck limpios, build con worker de MapLibre verificado; backend **233/233** y recuentos de PostgreSQL intactos (`668/484/3/120/0`). Siete defectos reales que ningún test detectó, encontrados y corregidos mirando el navegador (mapa con altura 0 por orden de carga del CSS de MapLibre, `snapshot_id` usado como señal de dato nuevo, «Volver al tren» que nunca aparecía, scroll horizontal en 390 px, código crudo del contrato en la interfaz, rótulos solapados y ficha que heredaba el desplazamiento).
- **Revisión independiente de Codex (2026-11-22):** diff `74667c0..5f8b739` auditado sin hallazgos abiertos. La inspección visual real en Chrome DevTools se reprodujo desde la sesión coordinadora de Orca contra API `8010` + Vite `5181` (la sesión aislada del revisor no tenía superficie Chrome): mapa completo y cobertura coherente con MP-018, varias líneas simultáneas, circulación real C5 `19656` con URL restaurable y ficha de 23 estaciones, seguimiento explícito, degradación honesta y móvil `390x844`; sin errores de aplicación en consola. Arrastre y emulación de `prefers-reduced-motion` no estuvieron disponibles en esa herramienta y se cerraron mediante la evidencia ejecutada del implementador, los tests de regresión y auditoría directa del código de seguimiento y repintado por `revision`. Reejecutados: web con Node `22.13.1` (lint, typecheck, **49/49**, build), backend **233/233** sin `skip` contra desarrollo (`668/484/3/120/0` intactos) y 233 con 5 `skip` esperados sobre PostGIS fresco con `0001`+`0002`; `git diff --check`, autoría y ausencia de coautores limpios.
- **Estado:** `DONE` — implementación de Claude Opus aprobada por OpenAI Codex el 2026-11-22, sin hallazgos abiertos. La paleta propia por ausencia de `route_color` en `/api/v1/catalog` queda como limitación conocida para MP-021/MP-022.

---

## MP-021 — Histórico y continuidad analítica

- **Fase:** Hito 3 — Cierre ferroviario Madrid
- **Objetivo:** histórico consultable por circulación ligado a la identidad/fecha de Live (MP-019/020), mart reproducible con numeradores/denominadores de cobertura (extendiendo `services/snapshotter/gold.py` de un núcleo a todo el catálogo Madrid vía MP-017/018/019), exportación idempotente, propuesta ejecutable (no necesariamente desplegada) de colector continuo supervisado con coste medido, e History/Explore mínimo navegable conectado a los botones ya deshabilitados en `apps/web/src/ui/TopBar.tsx`.
- **Prioridad:** P0
- **Depende de:** MP-020 (`DONE`)
- **Ejecutor:** Claude (escalado a Opus — continuidad analítica sobre identidad/temporalidad de MP-017/018/019, decisión arquitectónica de alto impacto, política de modelo de Hito 2; asignación fija del kit en `PLAN-Y-ACEPTACION.md`)
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `services/snapshotter/gold.py` (extensión, no duplicación), nuevo módulo de archivo/export bajo `services/` o `packages/` (a decidir por el ejecutor con justificación), `apps/api/` (si expone endpoints de histórico/Explore), `apps/web/src/ui/TopBar.tsx` + nuevas vistas History/Explore, `docs/adr/` (si hay decisión de arquitectura nueva, p. ej. formato de archivo o estrategia de colector continuo).
- **Entradas:** `packages.gtfs.catalog` (MP-017, identidad de circulación/servicio), `packages.geo.catalog` (MP-018), contrato de snapshot/ADR-0014 (MP-019), frontend MP-020 (identidad de circulación, URL restaurable `?train=&trip=&sd=`), `services/snapshotter/gold.py` existente (agregación por núcleo/línea/estación).
- **Entregables:**
  1. Archivo/export propio e **idempotente**: reprocesar el mismo día de servicio dos veces produce exactamente el mismo resultado (mismos agregados, mismo recuento de filas, sin duplicados).
  2. Histórico **consultable por circulación**, enlazado por identidad vehículo+viaje+día de servicio (la misma identidad que usa Live en MP-020), con huecos de cobertura siempre visibles — nunca una métrica de puntualidad sin su denominador, nunca "cobertura" inventada donde no hay dato.
  3. Mart reproducible extendiendo `build_nucleo_daily_summary`/`build_line_daily_metrics`/`build_station_daily_metrics` al catálogo completo de Madrid (42 rutas/12 líneas de MP-017), con `GoldThresholds`/calidad explícitos.
  4. History/Explore **mínimo** navegable: conecta los botones `History`/`Explore` de `TopBar.tsx` (hoy `disabled` con `title="Histórico y Explore se entregan en MP-021"`) a una vista real — no SQL Lab, no dbt obligatorio, no cuentas, no infraestructura distribuida (prohibido explícitamente por el kit).
  5. Propuesta **ejecutable** de colector continuo supervisado (configuración reproducible, p. ej. script/servicio documentado) con **coste medido** (recursos, almacenamiento, transferencia, horas) — nunca una promesa de "24/7 confirmado" sin aprobación explícita del propietario sobre coste/licencias de cualquier servicio de pago. Si no hay host persistente autorizado: entregar la operación local y el plan/coste medido como entregable final, declarando explícitamente qué NO está desplegado.
- **Criterios de aceptación:**
  - Reprocesar el mismo día de servicio dos veces → mismo resultado exacto (test de idempotencia real, no solo revisión de código).
  - Huecos de cobertura siempre visibles en cualquier métrica de puntualidad/fiabilidad expuesta (numerador y denominador juntos).
  - History/Explore mínimo navegable de verdad en navegador (no solo API) — ligado a la identidad de Live, con vuelta de contexto (desde una circulación en History, volver a Live con esa misma identidad si sigue activa).
  - Ninguna afirmación de "24/7 verificado" ni contratación de servicio de pago sin aprobación explícita del propietario; si no se logró, declarar el bloqueo concreto en vez de fingir el estado.
  - No se añaden SQL Lab, dbt obligatorio, cuentas de usuario ni infraestructura distribuida.
- **Pruebas necesarias:** suite real del proyecto (backend+frontend) + test de idempotencia de reprocesado + test de huecos/denominadores del mart + inspección visual real en navegador de History/Explore (Claude/Codex, Chrome DevTools MCP) siguiendo el mismo estándar que MP-020.
- **Qué se construyó:**
  - **Idempotencia real y a prueba de caídas** (`services/snapshotter/export.py`): preparación en `.staging/`, la versión anterior del día se aparta a `.quarantine/` con un `rename` atómico, la preparada ocupa el nombre definitivo con otro, y solo entonces se borra la cuarentena; toda exportación empieza por `recover_interrupted_swaps`. Un origen vacío nunca borra un día ya archivado (`action="preserved_existing"`). Los cuatro agregados llevan `ORDER BY` explícito y son byte-estables. Ver DEC-040 y [ADR-0015](adr/0015-cold-archive-and-history-contract.md).
  - **Límite (a) de DEC-033 cerrado** (`services/snapshotter/gold.py`): el calendario lo resuelve `packages.gtfs.scheduled_service_ids_for_date` (MP-017), con `calendar_dates.txt`, en vez de reimplementarse. (b) y (c) siguen abiertos, con su razón actualizada.
  - **Mart nuevo por circulación** (`services/snapshotter/history.py`): `circulation_daily_history`, grano vehículo + viaje + día de servicio, con los huecos como filas y una columna `coverage` que separa el hueco real de una **anulación del operador** y de un hueco solo de posición. Cada métrica va con el denominador que la sostiene. Ver DEC-042.
  - **Catálogo Madrid completo** (`services/snapshotter/config.py`): `SnapshotterConfig.line_filter` — `MADRID_PULSE_SHORT_NAME=` vacío calcula el mart para las 12 líneas / 42 rutas, no solo C5.
  - **API de histórico** (`apps/api/history.py` + 5 rutas `/api/v1/history/*`): sobre Parquet con DuckDB en solo lectura. El contrato de MP-019 no se toca, y un test lo fija como regresión.
  - **History/Explore navegables** (`apps/web/src/ui/HistoryView.tsx`, `ExploreView.tsx`, `hooks/useHistory.ts`): los botones de `TopBar.tsx` ya no están `disabled`. Ida y vuelta Live ↔ History con la misma identidad.
  - **Operación continua supervisada** (`infra/operate/`): supervisor portable, plantillas `launchd` y `systemd`, archivo diario y medidor de coste real.
  - **Corrección de operación continua** (`services/collector/__main__.py`, DEC-041): una conexión perdida con PostgreSQL termina el proceso con `EX_TEMPFAIL` (75) para que el supervisor lo reinicie, en vez de dejarlo vivo sin ingerir.
- **Evidencia de verificación:** [`docs/evidence/mp-021-inspeccion-navegador.md`](evidence/mp-021-inspeccion-navegador.md) (con las capturas de `docs/evidence/mp-021-capturas/`) y [`docs/evidence/mp-021-coste-colector-continuo.md`](evidence/mp-021-coste-colector-continuo.md) (con el informe crudo `mp-021-medicion-coste.json`). Resumen:
  - **Idempotencia probada contra PostgreSQL real**, no por lectura de código: exportar + agregar dos veces da un archivo **byte-idéntico**; una fila borrada del origen **no sobrevive** en el archivo; reprocesar un día **no toca** otro ya archivado; un origen vacío **conserva** el archivo. Las mismas pruebas ejecutadas contra el `export.py` anterior fallan con el síntoma exacto (`2 != 1 : la fila eliminada del origen sobrevive en el archivo`).
  - **Huecos y denominadores**: 1 304 circulaciones programadas el `2026-11-20`, 122 observadas, **1 179 huecos reales** y 3 anuladas por el operador. Los huecos reales no tienen señal de posición ni parte del operador y conservan sus métricas en `NULL`; las anuladas llevan su actualización real y un `delay_reported_count=0` medido, sin fabricar puntualidad. El `2026-11-19` real tiene 24 circulaciones observadas y **cero** programadas (el `calendar.txt` del ZIP empieza el día 20): se publican como «observadas fuera de programación», no se descartan.
  - **Inspección visual real en Chrome DevTools MCP** (API `8011` + Vite `5182` montados en **este** worktree; el entorno de MP-020 en `8010`/`5181` se dejó intacto y la base `mp020-replay-db` se usó solo en lectura, con sus recuentos `240/199/4/7/2` comprobados al terminar). 10 capturas. Cuatro defectos reales encontrados mirando y corregidos: rótulo del tren fijado en «Sin línea» al llegar por enlace, media pantalla en blanco en móvil en las vistas de archivo, **dos denominadores distintos del mismo día** (1304 vs 1299, por 5 viajes huérfanos reales del GTFS) y una nota de cobertura que afirmaba algo falso para el otro día; la segunda ronda añadió la inspección de las anulaciones.
  - **Operación continua medida de verdad**, no prometida: 21 ciclos completos contra los feeds en vivo de Renfe en 823 s, 0 errores de ingesta; RSS máximo 18,6 MB; 434 KB de bajada por ciclo; ≈631 B/fila en PostgreSQL y ≈48,9 B/fila en Parquet ZSTD. Recuperación verificada provocando los fallos: `kill -9` (el supervisor reinicia en 5 s) y reinicio de PostgreSQL (defecto encontrado así y corregido; ahora sale con 75 y la ingesta se reanuda).
  - **Suites reales tras la revisión**: backend **276/276 en verde** contra desarrollo y 276 con 5 `skip` esperados sobre PostGIS fresco; recuentos intactos en `668/484/3/120/0` y replay `240/199/4/7/2`. Frontend con Node **22.13.1** **88/88**, lint, typecheck y build en verde con el worker de MapLibre verificado (550754 bytes).
- **Lo que NO se hizo, y por qué:** no se ha contratado ningún host persistente ni servicio de pago, no se ha instalado el agente `launchd` en el equipo del propietario (es un cambio en su máquina, no un artefacto del repositorio) y **no se declara «24/7 verificado»**: la ventana medida son 13 min, y todas las cifras de 24/72 h están marcadas como proyección. El umbral de puntualidad (límite (b) de DEC-033) sigue sin calibrar: con dos días archivados no hay base, y fijarlo con esa muestra sería fabricar una calibración.
- **Revisión de OpenAI Codex (1ª ronda, 2026-11-23): DOS HALLAZGOS BLOQUEANTES, ambos ciertos y ya corregidos.**
  1. *Atomicidad falsa.* `export.py` hacía `rmtree(final)` **antes** de `replace()`: una caída entre ambos borraba el día ya archivado sin reemplazo, justo lo que ADR-0015/DEC-040 dicen prevenir. Corregido con cuarentena + dos renombrados atómicos + `recover_interrupted_swaps`, y **se deja de afirmar atomicidad de un solo paso** (`rename(2)` no la ofrece para directorios no vacíos; las alternativas que sí —symlink, `renameat2`— rompen el contrato de lectura de la capa gold o no son portables). Fijado con **inyección de fallo en la costura exacta**: `test_a_crash_between_the_two_renames_never_destroys_the_archived_day` compara el inventario completo (ruta + SHA-256) antes de la caída y tras la recuperación, y **falla contra el mecanismo anterior** con `la versión anterior no está en cuarentena: se ha perdido`.
  2. *Huecos con métricas no nulas.* 3 huecos del `2026-11-20` tenían `trip_updates_count=1` y `delay_reported_count=0`. Rastreado al dato crudo: los tres (`1023V20865C5`, `1023V21340C10`, `1023V21748C2`) tienen una `trip_update_observation` real con `schedule_relationship='CANCELED'` y cero posiciones — **Renfe los había anulado**. Contarlos como hueco culpaba al colector de trenes que nunca salieron. Corregida la semántica con `coverage`/`canceled`, Parquet **regenerado** y documentación alineada con el comportamiento real. Tras la corrección el día cierra como `1304 = 122 observadas + 1179 huecos reales + 3 anuladas`, y de los **1 179 huecos completos** ninguno tiene métricas no nulas ni es una anulación.
  Evidencia detallada en la sección "Segunda ronda" de [`docs/evidence/mp-021-inspeccion-navegador.md`](evidence/mp-021-inspeccion-navegador.md). Un tercer defecto menor salió al re-verificar en navegador (la lista blanca de filtros de `useUrlState.ts` ignoraba las categorías nuevas y caía en silencio a «Todas»), también corregido con regresión.
- **Suites tras la corrección:** backend **276/276** en verde (269 → 276) con los recuentos de desarrollo intactos en `668/484/3/120/0`; frontend con Node `22.13.1` **88/88** (82 → 88), lint, typecheck y build en verde.
- **Revisión independiente de OpenAI Codex (2ª ronda, 2026-11-23): APROBADA, sin hallazgos abiertos.** Reproducidos los cuatro casos funcionales de idempotencia contra PostgreSQL desechable y los tres escenarios de caída/recuperación; el Parquet real cierra `1304 = 122 observadas + 1179 huecos + 3 anuladas`, con 0 métricas no nulas en los huecos reales y el `2026-11-19` en `0` programadas / `24` observadas fuera de programación. Inspección real en navegador de History/Explore, detalle histórico y vuelta honesta a Live; a `390x844` exactos ambas vistas tienen `scrollWidth == clientWidth == 390`, y la tabla ancha de Explore queda confinada a `.table-scroll`. Backend **276/276** contra desarrollo y 276 con 5 `skip` esperados sobre PostGIS fresco; frontend Node `22.13.1` **88/88**, lint, typecheck y build; worker MapLibre 550754 bytes; `git diff --check`, autoría exclusiva de Pedro Matute y ausencia de coautores verificados.
- **Estado:** `DONE` — implementación de Claude Opus aprobada por OpenAI Codex el 2026-11-23 tras dos rondas; sin hallazgos abiertos. ADR-0015 permanece `Propuesto` y su promoción corresponde exclusivamente al propietario.

---

## MP-022 — Validación integral de cierre (Madrid completo)

- **Fase:** Hito 3 — Cierre ferroviario Madrid (última tarea de la cadena)
- **Objetivo:** auditoría final cruzada de todo el Hito 3 — recorrido completo Live → History con la misma identidad de circulación, matriz de cobertura real por línea/variante/patrón (física, de resolución del feed y de ETAs, nunca "cobertura total de GPS" proclamada sobre una muestra congelada), pruebas sin señal y con recuperación, métricas de rendimiento por línea en equipo/navegador/dataset documentados, capturas reales desktop/móvil, y un dossier final para que el propietario decida la integración a `main`. No es una tarea de diseño nuevo: es la última verificación antes de declarar el hito cerrado.
- **Prioridad:** P0
- **Depende de:** MP-021 (`DONE`)
- **Ejecutor:** OpenAI Codex (asignación fija del kit en `PLAN-Y-ACEPTACION.md`)
- **Revisor:** Claude (Sonnet — tarea de auditoría/validación, no de arquitectura nueva; no se escala a Opus salvo que surja un hallazgo que lo justifique)
- **Archivos/componentes afectados:** ningún módulo de producto se reescribe; se añaden/extienden fixtures de prueba, documentación de evidencia (`docs/evidence/`), y posiblemente ajustes menores donde la auditoría encuentre defectos reales (nunca features nuevas).
- **Entradas:** todo lo entregado en MP-016→MP-021 (catálogo Madrid completo, corredores OSM, contrato de snapshot/ADR-0014, frontend map-first, histórico/Explore/ADR-0015); los dos cortes congelados `1532`/`1533` del kit; `docs/hitos/hito-03/MATRIZ-CIERRE-MADRID.md`, `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md`, `ANEXO-CRITICO-POSICION-Y-RELOJ.md`, `REVISION-FINAL-V4.md`.
- **Entregables:**
  1. **Recorrido completo Live → History** demostrado de verdad en navegador: selección desde mapa/lista, seguir→arrastrar→volver, dos sondeos sin pérdida de contexto, respuesta antigua descartada por `revision`, fallo parcial y recuperación, parada/ramal compartido, fuente obsoleta, móvil 390px, teclado completo y `prefers-reduced-motion` — y la trazabilidad real hasta el mart histórico de una circulación (reprocesar el mismo día dos veces, mismo resultado).
  2. **Matriz de cobertura por línea/variante/patrón** del catálogo vigente (12 líneas/42 rutas/103 patrones): cobertura física (geometría OSM map-matcheada vs. no), de resolución del feed (GPS real vs. solo horario), y de ETAs (con procedencia). Los conteos del replay (`1532`/`1533`) son una muestra congelada — explícito en el dossier, nunca "cobertura total de GPS".
  3. **Pruebas E2E que distinguen una captura congelada de datos de producción** (instrucción explícita del kit en `PROMPTS.md`): los dos cortes del kit no prueban por sí solos todos los casos ni precisión física — añadir secuencias derivadas/sintéticas etiquetadas o capturas reales adicionales con manifiesto y reloj controlado, sin atribuir a Renfe un escenario fabricado.
  4. **Métricas de rendimiento por línea** medidas en equipo/navegador/dataset documentados (nunca presupuestos universales) — p50/p95, no solo del contrato de API (ya medido en MP-019) sino del recorrido de usuario real.
  5. **Dossier final** para la integración del propietario: qué está `DONE`, qué ADRs siguen `Propuesto` (ADR-0014, ADR-0015) a la espera de su decisión, qué límites/gates siguen abiertos (DEC-033 (b)/(c), DEC-038, operación 24/7), y el roadmap explícitamente no iniciado de `SIGUIENTES-HITOS.md` (AV/LD/MD, despliegue 24/7 real).
- **Criterios de aceptación:**
  - El recorrido completo se demuestra con vídeo real (≥60s) o capturas reales del frontend integrado — nunca se acredita con el prototipo `diseno/live.html`.
  - La matriz de cobertura declara explícitamente sus límites y denominadores — ninguna afirmación de cobertura total sin la muestra que la sostiene.
  - Las pruebas E2E nuevas distinguen explícitamente "captura congelada" de "producción en vivo" — ningún test se presenta como verificación contra datos reales si usa una fixture sintética.
  - El dossier final es honesto sobre qué queda pendiente de decisión del propietario (ADRs `Propuesto`, DECs abiertas, gates de coste/licencia) — no declara el hito "cerrado" en aspectos que siguen bloqueados por decisión ajena.
- **Pruebas necesarias:** suite real completa del proyecto (backend+frontend) sin romper nada de MP-016→MP-021; nuevas pruebas E2E/sintéticas etiquetadas; inspección visual real en navegador del recorrido completo (Chrome DevTools MCP), mismo estándar que MP-020/MP-021.
- **Evidencia de verificación:** matriz reproducible CSV+Markdown con el esquema vinculante exacto (`docs/evidence/mp-022-coverage.*`): 12 líneas/42 rutas/103 patrones, 1 299 instancias con horario, 121 observaciones exactas del corte 1533, C4 con denominador 0→`null`, geometría 28/103 map-matcheable y fallback declarado. Replay real 119/119/49 y 121/121/49; cuatro snapshots normal/normal/parcial/congelado con revisión 3→6→7, 122 últimos conocidos conservados y sin rejuvenecer. Fixture sintética derivada explícitamente no oficial y 7/7 pruebas focales de calendario 24:xx, recuperación, reloj y contrato de matriz. `.github/workflows/ci.yml` incluye ya `apps.api.tests.test_closure_matrix` y `tests.e2e.test_mp022_synthetic_derived`; su comando actualizado pasó 283/283 con 5 `skip` en `mp022-ci-db:5438`, mientras la corrida independiente anterior del revisor sobre la lista base pasó 276/276 con 1 `skip` en su PostgreSQL fresco `5439` (entornos y alcances distintos, ambos declarados). Frontend Node 22.13.1 89/89, lint, typecheck y build (worker MapLibre 550754 bytes). Benchmark API válido de 30 iteraciones y archivo frío reprocesado dos veces byte-idéntico. Inspección nueva del revisor: reduced-motion con seis muestras/deriva 0; recorrido Live→History completo en desktop, móvil 390×844, teclado y sin WebGL; mapa 182 frames/60,3 fps, p50/p95 16,70/18,30 ms y heap 96,2 MiB usado. El corte estaba congelado desde hacía 68,7 h, por lo que esa última medida acredita zoom/pan, no animación continua de trenes. El hallazgo de sustitución silenciosa de un día no archivado en History se corrigió con estado explícito y regresión focal incluida; typecheck y lint limpios. Dossier completo en `docs/evidence/mp-022-validacion-integrada.md` y `mp-022-dossier-integracion.md`.
- **Revisión independiente de Claude (2026-11-23, dos rondas):** auditoría real, no solo lectura de informe. Reproduje en navegador real (Chrome DevTools MCP) lo que la sesión aislada del ejecutor no pudo —sin superficie de navegador, mismo límite de MP-020—: gate 7 con `matchMedia` forzado a `reduce` antes de montar React, seis muestras de centro/zoom cada 700ms con deriva 0 mientras el reloj seguía avanzando; gate 8 con un recorrido real nuevo (Live → filtro C4a+C4b → tren 20277 → Seguir → arrastre sintético real del lienzo MapLibre → Volver al tren → History 2026-11-20 → Atrás, restaurando exactamente la URL anterior), móvil 390×844 real vía `emulate` (no resize), teclado (Tab+Enter activando un filtro), y sin WebGL vía `initScript` anulando `getContext`; gate 9 con `requestAnimationFrame` real durante zoom+pan (182 frames, 60,3 fps, p50 16,70 ms, p95 18,30 ms) y `performance.memory` (96,2 MiB). Encontré y devolví dos hallazgos reales, ambos corregidos y reverificados por mí de forma independiente: (1) `HistoryView.tsx` sustituía silenciosamente un día de URL no archivado por `days.days[0]` en el encabezado/breadcrumb — corregido con un estado explícito "Día no archivado" que conserva la fecha pedida, con regresión (`HistoryView.test.tsx`) que verifiqué en vivo tras el hot-reload; (2) dos módulos de test nuevos de esta misma tarea (`apps.api.tests.test_closure_matrix`, `tests.e2e.test_mp022_synthetic_derived`, 7 tests que blindan las puertas 2/3/7 y el contrato de la matriz) no estaban en la lista explícita de `.github/workflows/ci.yml` — nunca se habrían ejecutado en una CI real — corregido añadiéndolos al workflow. Reejecuté yo mismo, dos veces, contra contenedores PostgreSQL 17-3.5 desechables propios (puertos 5439 y 5440, migraciones `0001`+`0002` aplicadas desde cero, destruidos al terminar): **283/283 tests Python en verde** con la lista actualizada de CI (276 del conjunto original + 4 de calendario/recuperación/reloj + 3 de matriz de cierre), 1 `skip` real (`test_real_soak_postgres`, ausencia esperada del soak de MP-007 en una base fresca) — diferencia informativa, no bloqueante, frente al `5 skip` que registra el ejecutor en su propio entorno persistente; frontend **89/89** con Node 22.13.1 real, lint y typecheck limpios, build con worker MapLibre de **550754 bytes** verificado byte a byte. `git diff --check` limpio y autoría exclusiva de Pedro Matute sin `Co-authored-by` en los tres commits (`c745374`, `4d25658`, `23ec6c0`). No quedan hallazgos abiertos.
- **Estado:** `DONE` — implementación de OpenAI Codex aprobada por Claude el 2026-11-23 tras dos rondas de auditoría/corrección en el mismo worktree tras inspección visual real en navegador y reejecución independiente de la suite completa. Cierra la cadena `MP-016`→`MP-022` del Hito 3. ADR-0014 y ADR-0015 permanecen `Propuesto`; DEC-033 (b)/(c), DEC-038 y DEC-004 siguen abiertas; el roadmap de AV/LD/MD y operación 24/7 real está explícitamente no iniciado — todo ello pendiente de decisión exclusiva del propietario, nunca autopromovido por los agentes.

---

## Grafo de dependencias

Esta tabla refleja **exactamente** el campo "Depende de" de cada ficha anterior — sin añadir dependencias transitivas redundantes. Para dependencias transitivas (p. ej. qué depende indirectamente de MP-004), recórrase la tabla hacia arriba.

| Tarea | Depende directamente de |
|---|---|
| MP-001 | — |
| MP-002 | MP-001 |
| MP-003 | MP-002 |
| MP-004 | MP-003 |
| MP-005 | MP-004 |
| MP-006 | MP-005 |
| MP-007 | MP-005, MP-006 |
| MP-008 | MP-007 |
| MP-009 | MP-007, MP-008 |
| MP-010 | MP-004 |
| MP-011 | MP-010 |
| MP-012 | MP-008, MP-010, MP-011 |
| MP-013 | MP-005, MP-007, MP-012 |
| MP-014 | MP-013 |
| MP-015 | MP-009, MP-012, MP-013, MP-014 |
| MP-016 | MP-015 |
| MP-017 | MP-016 |
| MP-018 | MP-017 |
| MP-019 | MP-018 |
| MP-020 | MP-019 |
| MP-021 | MP-020 |
| MP-022 | MP-021 |

Dos ramas pueden avanzar en paralelo en worktrees independientes una vez resuelto su ancestro común: `MP-005` y `MP-010` corren en paralelo tras `MP-004` (no dependen entre sí); `MP-006`/`MP-007` corren en la rama de `MP-005`, mientras `MP-011` corre en la rama de `MP-010`, hasta que ambas convergen en `MP-012`. Hito 3 (`MP-016`→`MP-022`) es estrictamente secuencial, un worktree por tarea heredando de la anterior ya `DONE`, conforme a `docs/hitos/hito-03/PLAN-Y-ACEPTACION.md`.

---

## Backlog planificado y tracks (generado)

> **Excepción del gate MP-035:** la columna «Dependencias» enumera lo que debe cerrarse **o quedar `BLOCKED` documentado** (`docs/H4_MP_MAPPING.md`, `docs/H4_TASK_MATRIX.md`): una tarea bloqueada no impide convocar el gate ni emitir NO-GO.

> Índice generado desde `docs/governance/PROJECT_STATE.json` con `python scripts/governance/sync_docs.py`; no se edita a mano. Las fichas completas de MP-023+ viven en `docs/H4_MP_MAPPING.md` y `docs/H4_TASK_MATRIX.md`; D-xx y DES-xx son subtareas con correspondencia a MP existentes (`docs/roadmap/CROSSWALK.md`), **no** backlog adicional.

<!-- BEGIN GENERATED: backlog-index -->

| ID | Título | Track | implementation_status | Dependencias | Ejecutor | Revisor | Alias y relaciones | Integración | Fuente | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUD-00 | Baseline real del Hito 3 y verificación de entorno | AUDIT | IMPLEMENTED | — | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/BASELINE.md](audits/hito-03/BASELINE.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-01 | Tesis de producto, arquitectura y pruebas refutables | AUDIT | IMPLEMENTED | AUD-00 | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/PRODUCT_AUDIT.md](audits/hito-03/PRODUCT_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-02 | Catálogo ferroviario del Hito 3 | AUDIT | IMPLEMENTED | AUD-00 | codex | claude | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/RAILWAY_GEOMETRY_AUDIT.md](audits/hito-03/RAILWAY_GEOMETRY_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-03 | Geometría ferroviaria del Hito 3 | AUDIT | IMPLEMENTED | AUD-00 | codex | claude | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/RAILWAY_GEOMETRY_AUDIT.md](audits/hito-03/RAILWAY_GEOMETRY_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-04 | Raw / matched / rendered y contratos temporales | AUDIT | IMPLEMENTED | AUD-00 | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/POSITION_MOVEMENT_AUDIT.md](audits/hito-03/POSITION_MOVEMENT_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-05 | Frontend en navegador real | AUDIT | IMPLEMENTED | AUD-00 | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/FRONTEND_UX_AUDIT.md](audits/hito-03/FRONTEND_UX_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-06 | Backend, API, datos y operación | AUDIT | IMPLEMENTED | AUD-00 | codex | claude | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/BACKEND_OPERATIONS_AUDIT.md](audits/hito-03/BACKEND_OPERATIONS_AUDIT.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-07 | Revisión adversarial equivalente (EGM) | AUDIT | IMPLEMENTED | AUD-00 | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/EGM_REVIEW.md](audits/hito-03/EGM_REVIEW.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-08 | Reproducción y reconciliación | AUDIT | IMPLEMENTED | AUD-01, AUD-02, AUD-03, AUD-04, AUD-05, AUD-06, AUD-07 | codex | claude | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/AUD08_REPRODUCTION.md](audits/hito-03/AUD08_REPRODUCTION.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| AUD-09 | Registro de hallazgos, decisión ejecutiva y propuesta H4 | AUDIT | IMPLEMENTED | AUD-08 | claude | codex | — | PR #3 | [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) | [docs/audits/hito-03/AUDIT_EXECUTIVE_DECISION.md](audits/hito-03/AUDIT_EXECUTIVE_DECISION.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| MP-023 | Eliminar defaults peligrosos de PostgreSQL (H4-11) | PRODUCT | IMPLEMENTED | — | codex | claude | Alias H4-11 | PR #5 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-023/README.md](evidence/mp-023/README.md); [docs/evidence/mp-023/ROUND2.md](evidence/mp-023/ROUND2.md); [docs/operations/DATABASE_ISOLATION.md](operations/DATABASE_ISOLATION.md) |
| MP-024 | Enmienda de ADR-0014 (estado de parada) (H4-00) | PRODUCT | IMPLEMENTED | — | claude | codex | Alias H4-00 | PR #7 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/adr/0014-amendment-stop-state.md](adr/0014-amendment-stop-state.md); [docs/evidence/mp-024/README.md](evidence/mp-024/README.md); [docs/evidence/mp-024/stop_state_comparison.py](evidence/mp-024/stop_state_comparison.py); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md) |
| MP-025a | Modelo de estado de parada: cierre determinista (H4-04) | PRODUCT | IMPLEMENTED | MP-024 | codex | claude | Alias H4-04 | PR #8 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-025a/README.md](evidence/mp-025a/README.md); [docs/evidence/mp-025a/ronda2/README.md](evidence/mp-025a/ronda2/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md) |
| MP-025b | Validación Live del modelo de parada (H4-04) | PRODUCT | IN_PROGRESS | MP-025a, MP-028 | codex | claude | Alias H4-04 | PR #13 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-025b/README.md](evidence/mp-025b/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) |
| MP-026a | FR-02 replay ?at= y FR-19 vigencia GTFS (H4-01) | PRODUCT | IMPLEMENTED | — | codex | claude | Alias H4-01 | PR #6 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-026a/README.md](evidence/mp-026a/README.md); [docs/operations/GTFS_STATIC_REFRESH.md](operations/GTFS_STATIC_REFRESH.md); [docs/DATA_CONTRACTS.md](DATA_CONTRACTS.md); [docs/evidence/mp-026a/CLOCK_ROBUSTNESS.md](evidence/mp-026a/CLOCK_ROBUSTNESS.md) |
| MP-026b | FR-07 snapshot consistente (H4-01) | PRODUCT | IMPLEMENTED | MP-024 | codex | claude | Alias H4-01 | PR #9 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-026b/README.md](evidence/mp-026b/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md) |
| MP-027 | Portada, legal y puertas falsables (H4-10) | PRODUCT | PLANNED | — | claude | codex | Alias H4-10 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-028 | Captura en vivo (≥2 h, ≥3 días) (H4-12) | PRODUCT | IN_PROGRESS | MP-023 | codex | claude | Alias H4-12 | PR #12 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/operations/CAPTURE_PROTOCOL.md](operations/CAPTURE_PROTOCOL.md); [docs/evidence/mp-025b/README.md](evidence/mp-025b/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md) |
| MP-029 | Corredores, ramales y catálogo honesto (H4-03) | PRODUCT | PLANNED | MP-024 | codex | claude | Alias H4-03 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-030 | Interfaz: procedencia y rótulos veraces (H4-05) | PRODUCT | IMPLEMENTED | MP-024 | codex | claude | Alias H4-05 | PR #11 | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | [docs/evidence/mp-030/README.md](evidence/mp-030/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/CHANGELOG.md](CHANGELOG.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md) |
| MP-031 | Métricas de cierre honestas (H4-06) | PRODUCT | PLANNED | MP-028 | claude | codex | Alias H4-06 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-032 | Operación supervisada local medida (H4-07) | PRODUCT | PLANNED | MP-023 | codex | claude | Alias H4-07 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-033 | Rendimiento y coste (H4-08) | PRODUCT | PLANNED | MP-026a, MP-026b, MP-032 | codex | claude | Alias H4-08 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-034 | Registro estructurado de hallazgos (H4-13) | PRODUCT | PLANNED | — | codex | claude | Alias H4-13 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| MP-035 | Gate de publicación (H4-09) | PRODUCT | PLANNED | MP-023, MP-024, MP-025a, MP-025b, MP-026a, MP-026b, MP-027, MP-028, MP-029, MP-030, MP-031, MP-032, MP-033, MP-034 | codex | claude | Alias H4-09 | — | [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md) | — |
| D-01 | Captura local de 90 min con BD desechable y manifest | MVP0 | PLANNED | MP-023 | claude | codex | Relacionadas MP-028 | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-02 | Contrato de demo estática y exportador determinista | MVP0 | PLANNED | — | codex | claude | — | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-03 | Adaptador estático, reloj en bucle, banner y pie | MVP0 | PLANNED | D-02 | claude | codex | — | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-04 | Teselas configurables y estilo OpenFreeMap | MVP0 | PLANNED | — | claude | codex | Relacionadas MP-027 | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-05 | vite base, verify-build demo y pages.yml | MVP0 | PLANNED | D-03, D-04 | codex | claude | — | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-06 | Validación integrada de la demo y aprobación del propietario | MVP0 | PLANNED | D-01, D-02, D-03, D-04, D-05 | claude | codex | — | — | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md) | — |
| D-11 | Dockerfiles, compose de producción y Caddy mismo origen | LIVE_STAGING | PLANNED | MP-023 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-12 | Migraciones idempotentes en arranque | LIVE_STAGING | PLANNED | D-11 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-14 | Purga y retención de BD caliente | LIVE_STAGING | PLANNED | D-11 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-15 | Rate limit, /healthz y cabeceras de seguridad | LIVE_STAGING | PLANNED | D-11 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-16 | Backups con restauración probada | LIVE_STAGING | PLANNED | D-11 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-17 | CD por SSH con aprobación manual | LIVE_STAGING | PLANNED | D-11 | codex | claude | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| D-18 | Operación supervisada ≥24 h (ideal 72 h) | LIVE_STAGING | PLANNED | D-11, D-12, D-14, D-15, D-16 | claude | codex | Relacionadas MP-032 | — | [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md) | — |
| DES-00 | Baseline y verificación de restricciones | DESIGN | PLANNED | — | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-01 | Inspección real y capturas del frontend existente (Claude + preflight de DevTools/Playwright) | DESIGN | PLANNED | DES-00 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-02 | Comparación de fuentes de diseño (frontend-design, Hallmark, Impeccable) | DESIGN | PLANNED | DES-00 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-03 | Brief y tres conceptos A/B/C | DESIGN | PLANNED | DES-01, DES-02 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-04 | Prototipo A Titanium Control | DESIGN | PLANNED | DES-03 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-05 | Prototipo B Immersive Rail Map | DESIGN | PLANNED | DES-03 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-06 | Prototipo C Contemporary Signal | DESIGN | PLANNED | DES-03 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-07 | Comparativa de iconografía ferroviaria | DESIGN | PLANNED | DES-03 | codex | claude | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-08 | Verificación comparativa A/B/C en navegador real (Claude + preflight; Codex audita código y artefactos) | DESIGN | PLANNED | DES-04, DES-05, DES-06, DES-07 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| DES-09 | Índice comparativo y gate humano de elección | DESIGN | PLANNED | DES-08 | claude | codex | — | — | [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md) | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| MP-036 | Fallback del motor: una observación rechazada no reaparece como ancla aceptada (A→B→A) | PRODUCT | IMPLEMENTED | — | codex | claude | — | PR #15 | [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md) | [docs/evidence/mp-036/README.md](evidence/mp-036/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) |
| MP-037 | Estudio de contradicciones de estado: M7 frente a R4 y STOPPED_AT incoherente con el GPS | PRODUCT | IMPLEMENTED | MP-025b | codex | claude | — | PR #16 | [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md) | [docs/evidence/mp-037/README.md](evidence/mp-037/README.md) |
| MP-038 | Evaluación comparable antes/después sobre las mismas entradas | PRODUCT | IMPLEMENTED | MP-025b, MP-036, MP-037 | codex | claude | — | PR #17 | [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md) | [docs/evidence/mp-038/README.md](evidence/mp-038/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) |
| GOV-TRACKING | Seguimiento recuperable del plan | GOVERNANCE | IMPLEMENTED | — | codex | claude | — | PR #14 | [docs/governance/UPDATE_PROTOCOL.md](governance/UPDATE_PROTOCOL.md) | [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md); [tests/governance/test_governance.py](../tests/governance/test_governance.py); [docs/STATUS.md](STATUS.md) |

### Alias (mismo trabajo, otro identificador)

| ID | alias_of | Título |
| --- | --- | --- |
| D-10 | MP-023 | Defaults seguros de BD (= MP-023) |
| D-13 | MP-026a | Descarga/validación GTFS con aviso de vigencia (FR-19) |

### Extensiones propuestas

- **PROPUESTA sin ID asignado** · Staging Live en VPS (Docker, Caddy, backups) como tarea propia. El plan lo llama subalcance de MP-032; si MP-032 (operación medida) se desborda, separar evita mezclar medición con despliegue. Sin ID asignado hasta decisión del propietario. Origen: OPS-01, OPS-02, D-11, D-17.
- **PROPUESTA sin ID asignado** · PoC de snapshot publisher y manifest versionado. SRV-01/SRV-02 no tienen tarea MP; el plan los difiere hasta que haya beta Live y métricas que lo justifiquen. Origen: SRV-01, SRV-02.
- **PROPUESTA sin ID asignado** · Build geográfico reproducible (grafo OSM/Geofabrik). GEO-03 excede el alcance de MP-029 si el PoC de grafo (GEO-02) tiene éxito. Origen: GEO-02, GEO-03.

### Fichas de reanudación

#### Reanudar MP-007

Collector idempotente

- **Última actualización** · 2026-11-19
- **Criterio de cierre** · Soak de 24 h de ingesta real (F3); conservar volcado, cobertura y errores.
- **Implementación** · IMPLEMENTED_WITH_OPEN_GATE
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Colector idempotente revisado; soak corto de 20 min (668 posiciones).
- **Pendiente** · Evidencia de 24 h de ingesta.
- **Motivo** · Gate F3 abierto; el soak disponible es corto.
- **Dependencias** · MP-005, MP-006
- **Condición para retomar** · MP-032 autorizado y entorno aislado disponible.
- **Próxima acción** · Ejecutar y documentar el soak de 24 h en la operación aislada de MP-032.
- **Ejecutor** · claude
- **Revisor** · codex
- **Fecha de revisión** · 2026-11-19
- **HEAD revisado** · 6654516
- **Rama** · mp-007-collector
- **Commit de referencia** · 6654516
- **PR** · 1
- **Merge** · f567d3c
- **Ficha de alcance** · [docs/TASKS.md](TASKS.md)
- **Evidencias** · [docs/TASKS.md#mp-007--collector-idempotente](TASKS.md#mp-007--collector-idempotente)

Gate literal de F3 (24 h de ingesta) sin evidencia: el soak real disponible es una ventana corta (668 filas). Ver MP-032.

#### Reanudar MP-009

Exportador histórico (Parquet particionado)

- **Última actualización** · 2026-11-19
- **Criterio de cierre** · Reproducir un día de servicio completo tras exportar a Parquet (F4).
- **Implementación** · IMPLEMENTED_WITH_OPEN_GATE
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Exportación y replay revisados sobre la ventana registrada.
- **Pendiente** · Demostrar replay de un día de servicio completo.
- **Motivo** · Gate F4 abierto; cobertura parcial.
- **Dependencias** · MP-007, MP-008
- **Condición para retomar** · Captura de un día con cobertura acreditada; ver MP-028/MP-032.
- **Próxima acción** · Exportar y reproducir un día completo a partir de una captura con cobertura acreditada.
- **Ejecutor** · claude
- **Revisor** · codex
- **Fecha de revisión** · 2026-11-19
- **HEAD revisado** · 8be1272
- **Rama** · mp-009-historical-export
- **Commit de referencia** · 8be1272
- **PR** · 1
- **Merge** · f567d3c
- **Ficha de alcance** · [docs/TASKS.md](TASKS.md)
- **Evidencias** · [docs/TASKS.md#mp-009--exportador-histórico-parquet-particionado](TASKS.md#mp-009--exportador-histórico-parquet-particionado)

Replay de 'un día completo' sin evidencia: el archivo real cubre la ventana de soak. Ver MP-028/MP-032.

#### Reanudar MP-023

Eliminar defaults peligrosos de PostgreSQL (H4-11)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · RED/GREEN y fallo seguro con DSN ausente o inválido en entorno desechable.
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Defaults seguros y fallo antes de conectar; PR #5.
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-25
- **HEAD revisado** · becaf7f
- **Rama** · pedromaaz13/mp-023-db-segura
- **Commit de referencia** · c005dcd
- **PR** · 5
- **Merge** · 4b80ce7
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-023/README.md](evidence/mp-023/README.md); [docs/evidence/mp-023/ROUND2.md](evidence/mp-023/ROUND2.md); [docs/operations/DATABASE_ISOLATION.md](operations/DATABASE_ISOLATION.md)

Implementada y aprobada por Claude Sonnet High en 2 rondas (0 B). Regresión RED en beb9434 / GREEN; suite de 28 módulos 283 tests/18 skipped sobre PostgreSQL desechable propio (puerto 5451; revisor 5461); 5433 no tocada. Recomendaciones registradas y no aplicadas: A5 (arnés de aislamiento no está en CI), A6 parcial (suite con entorno vacío: 12 errores, solo molestia local), A7 (reinicio del supervisor ante error de configuración), A10 (cambios menores en export.py y measure-cost.py). Integrada en main por PR #5 (merge commit 4b80ce7, 2026-11-25) por autorización del propietario.

#### Reanudar MP-024

Enmienda de ADR-0014 (estado de parada) (H4-00)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Dirección autorizada por el propietario, comparación reproducible y revisión de la corrección final.
- **Implementación** · IMPLEMENTED
- **Revisión** · CHANGES_REQUESTED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Enmienda 1 y decisión de dirección integradas (#7); alcance del ADR base aclarado (#10).
- **Pendiente** · Revisión independiente del ajuste final y evidencia de visibilidad histórica.
- **Motivo** · CHANGES_REQUESTED parcial (B2); corrección 68d7df7 sin re-verificación.
- **Gates humanos** · HG-ADR-0014
- **Condición para retomar** · Revisor independiente disponible.
- **Próxima acción** · Revisar 68d7df7 y comprobar si hay evidencia de visibilidad por hora civil.
- **Ejecutor** · claude
- **Revisor** · codex
- **Fecha de revisión** · 2026-11-25
- **HEAD revisado** · c7b4df6
- **Rama** · pedromaaz13/mp-024-adr-estado-parada
- **Commit de referencia** · 68d7df7
- **PR** · 7
- **Merge** · 2b71d17a6623a54ff63fb57d7fe9203f80c61724
- **Decisiones del propietario** · Resolver la promoción del ADR-0014 base: §§1, 4, 6, 7, 8, alternativas y consecuencias., Decidir el nombre contractual del campo de cancelación tras verificar el contrato de la fuente.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/adr/0014-amendment-stop-state.md](adr/0014-amendment-stop-state.md); [docs/evidence/mp-024/README.md](evidence/mp-024/README.md); [docs/evidence/mp-024/stop_state_comparison.py](evidence/mp-024/stop_state_comparison.py); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md)

Propuesta de enmienda de ADR-0014 (estado Propuesto) con evidencia comparativa reproducible. Ejecutor Claude Opus High (argv verificado); revisor Codex Astra High (recibo de Orca; esfuerzo no verificable en argv). Ronda 1: CHANGES_REQUESTED (7 B, 4 A). Ronda 2: B1, B3, B4, B7, A1, A2, A4 resueltos; B2, B5, B6, A3 parciales. Verificación focalizada del delta final (autorizada por el propietario, sobre c7b4df6): B5, B6 y A3 RESUELTOS; B2 PARCIAL solo en la garantía de replay por hora (started_at vs visibilidad del commit). Corrección posterior (68d7df7): garantía de replay acotada a «reconstrucción exacta dado el identificador del ancla/run»; la visibilidad histórica por hora queda UNVERIFIED para MP-026b/MP-032; NO re-verificada. Sin dictamen APPROVED. DECISIÓN DEL PROPIETARIO (2026-11-25): dirección aprobada (A con C como R8, F1, P-024 provisional) con limitaciones aceptadas; HG-ADR-0014 = APPROVED_BY_OWNER solo para esa dirección. El dictamen de revisor sigue CHANGES_REQUESTED y los supuestos UNVERIFIED siguen sin validar. Integración verificada: PR #7 (2b71d17, 2026-11-25) incorporó la enmienda y decisión; PR #10 (a0267c8, 2026-11-26) incorporó la aclaración sobre ADR base. F1 para R-STALE ya se decidió; F2 deja de ser una decisión pendiente. El ADR base sigue Propuesto; sus decisiones residuales no bloquean la entrega de la enmienda.

#### Reanudar MP-025a

Modelo de estado de parada: cierre determinista (H4-04)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Equivalencia Python↔TypeScript, RED en beb9434 y GREEN en cortes congelados; validación Live en MP-025b.
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Motor de parada y cierre determinista RED/GREEN; PR #8.
- **Dependencias** · MP-024
- **Gates humanos** · HG-ADR-0014
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-25
- **HEAD revisado** · 0f0ce54
- **Rama** · pedromaaz13/mp-025a-estado-parada
- **Commit de referencia** · 0f0ce54
- **PR** · 8
- **Merge** · c490f42
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-025a/README.md](evidence/mp-025a/README.md); [docs/evidence/mp-025a/ronda2/README.md](evidence/mp-025a/ronda2/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md)

Implementación del motor aprobado (ADR-0014 enmienda 1: A con C como R8, F1, P-024 provisional). Ejecutor Codex gpt-6.2-astra high (recibo de Orca; argv no verificable); revisor Claude Opus 5.5 high (argv verificado): ronda 1 CHANGES_REQUESTED (3 B, 10 A); ronda 2 APPROVED sobre 0f0ce54. RED en beb9434 / GREEN; suite 315 tests con 18 skipped, Vitest 110. Incluye migraciones 0003 y 0004 (marca de carga retroactiva por trigger y huella de versión por run; idempotentes y reversibles; CAMBIO DE ESQUEMA persistente: no aplicar a la BD 5433 sin decisión del propietario), bloqueo de colector único y señalización de cancelaciones. NO cierra FR-01: se cierra solo con MP-025b sobre >=500 pares en vivo. Supuestos UNVERIFIED siguen sin validar (semántica en vivo IN_TRANSIT_TO/INCOMING_AT, latencia de salidas retenidas, salto de recuperación ~311 m, replay exacto por hora civil sin garantía). Recomendaciones documentadas sin implementar: A2 (bloqueo huérfano con SIGSTOP), A4, A8, A9, A10; descubrimiento no bloqueante: test_collector_without_gtfs_holds_from_first_frame no puede fallar. Rótulos de UI y vigencia desde snapshot siguen pendientes de MP-030. Actualiza 5 expectativas de pruebas previas, autorizadas y documentadas una a una. Autorizada por el propietario el 2026-11-25. Integrada en main por PR #8 (merge commit c490f42, 2026-11-26) por autorización del propietario. Las migraciones 0003 y 0004 NO se aplican a la BD 5433. FR-01 sigue abierto hasta MP-025b; no cierra HG-H4-SCOPE.

#### Reanudar MP-025b

Validación Live del modelo de parada (H4-04)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Validación Live (≥500 pares, salto p50 ≤200 m), con estratos, salidas retenidas, F1 y dictamen sobre FR-01.
- **Implementación** · IN_PROGRESS
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Informe provisional de jornada 1 integrado (#13); comparación de jornada 2 en MP-038.
- **Pendiente** · Validar motor con cohortes representativas y resolver FR-01.
- **Motivo** · H1 en movimiento no cumple; falta jornada 3 y revisión de representatividad.
- **Dependencias** · MP-025a, MP-028
- **Bloqueos** · MP-028
- **Condición para retomar** · Jornada 3 capturada y verificada.
- **Próxima acción** · Tras MP-028, completar el contraste de las tres jornadas con los umbrales originales.
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-26
- **HEAD revisado** · cc7181b
- **Rama** · pedromaaz13/mp-025b-validacion
- **Commit de referencia** · cc7181b
- **PR** · 13
- **Merge** · d0dd0bc
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-025b/README.md](evidence/mp-025b/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md)

Validación PROVISIONAL del motor sobre la jornada 1 de MP-028 (1 de 3 jornadas; ~2 h efectivas tras excluir un hueco de 59,5 min por suspensión del equipo). Ejecutor Codex gpt-6.2-astra high (harness e informe; recibo de Orca); correcciones por sustitución registrada: Codex gpt-6.2-sol medium (recibo de Orca; en lugar de Astra High por economía); revisor Claude Opus 5.5 high (argv verificado): revisión completa CHANGES_REQUESTED (2 B, 4 A); verificación del delta cc7181b APPROVED (B1, B2, A1-A4 resueltos; resultados previos idénticos con cmp; sin descubrimientos nuevos). APPROVED significa que el INFORME provisional es correcto y honesto; NO valida el motor ni cierra FR-01. Resultados: H1 cumple literalmente (11 425 pares, p50 0 m) pero no es informativo; H1 estratificado NO cumple en movimiento (p50 963,5 m con avance >=100 m, n=1 843; 499,8 m en IN_TRANSIT_TO, n=2 240); STOPPED_AT con avance 19/7 001 planes (GPS fantasma por cuantización del feed, semántica UNVERIFIED); M7 adversa 135/1 441; salidas retenidas 402/6 918 (latencia máx 49 s); F1 0/65 retrocesos. FR-01 permanece ABIERTO. Hallazgos propuestos (no aceptados, tareas nuevas): reaparición del GPS rechazado (engine.py:110-124; 416 tríadas A→B→A) y preferir stop_id con STOPPED_AT frente a un GPS incoherente. Pendientes: jornada 3 y revisión de representatividad; la jornada 2 se evalúa en MP-038. Autorizada por el propietario el 2026-11-26; Integrada en main por PR #13 (merge commit d0dd0bc, 2026-11-26) como informe PROVISIONAL por autorización del propietario: no valida el motor ni cierra FR-01.

#### Reanudar MP-026a

FR-02 replay ?at= y FR-19 vigencia GTFS (H4-01)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · RED/GREEN de edades negativas y vigencia GTFS; evidencia integrada para el cierre de los hallazgos.
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Correcciones de replay y vigencia integradas (#6); Actions del PR en verde.
- **Pendiente** · Verificar el cierre de FR-02 y FR-19 en la validación integrada.
- **Motivo** · FR-02 sigue OPEN. Falta comprobar: cierre en validación integrada.
- **Condición para retomar** · Replay de aceptación en un entorno integrado y aislado.
- **Próxima acción** · Reproducir el replay antes del primer dato y GTFS vencido en la validación integrada.
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-25
- **HEAD revisado** · ec45d95
- **Rama** · pedromaaz13/mp-026a-replay-gtfs
- **Commit de referencia** · ec45d95
- **PR** · 6
- **Merge** · 7a5312f
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-026a/README.md](evidence/mp-026a/README.md); [docs/operations/GTFS_STATIC_REFRESH.md](operations/GTFS_STATIC_REFRESH.md); [docs/DATA_CONTRACTS.md](DATA_CONTRACTS.md); [docs/evidence/mp-026a/CLOCK_ROBUSTNESS.md](evidence/mp-026a/CLOCK_ROBUSTNESS.md)

FR-02 (replay ?at=) y FR-19 (vigencia GTFS en ejecución) corregidos. Ejecutor Codex gpt-6.2-sol high (recibo de Orca; argv no verificable); revisor Claude Opus 5.5 high (argv verificado): ronda 1 CHANGES_REQUESTED (1 B, 6 A), ronda 2 APPROVED. RED en fe0ea85/beb9434 y GREEN; suite 296 tests con 18 skipped; web 89 tests. Contrato con 3 excepciones a «aditivo» declaradas y esquema 1.1. PROPUESTO (no aceptado): display_lag_s sin límite superior da 500 (preexistente). Robustez temporal (autorizada por el propietario): suite con reloj controlado en 8 fechas (2026-11-25 a 2027-01-15) con 298 tests/18 skipped; fechas de fixtures sin ampliar; replay histórico evalúa la vigencia contra el instante reproducido; delta de pruebas dd92247..ec45d95 APPROVED por Claude Opus High, aprobación del código funcional conservada en 70170c7. Rotulado de degradación integrado en MP-030; gh pr checks 6 confirmó frontend, governance y python en PASS. Integrada en main por PR #6 (merge commit 7a5312f, 2026-11-25) tras #5.

#### Reanudar MP-026b

FR-07 snapshot consistente (H4-01)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · RED/GREEN de carrera y lectura consistente intra-respuesta; medir coste.
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Snapshot y tablero consistentes por respuesta; PR #9.
- **Dependencias** · MP-024
- **Gates humanos** · HG-ADR-0014
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-25
- **HEAD revisado** · ff5e6ad
- **Rama** · pedromaaz13/mp-026b-snapshot-consistente
- **Commit de referencia** · ff5e6ad
- **PR** · 9
- **Merge** · 4bc8612
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-026b/README.md](evidence/mp-026b/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md)

Lectura consistente de snapshot y tablero (ADR-0014 enmienda §4.7, FR-07): una transacción REPEATABLE READ de solo lectura por petición. Ejecutor Codex gpt-6.2-sol high (recibo de Orca; argv no verificable); revisor Claude Opus 5.5 high (argv verificado): APPROVED en la 1ª ronda (0 B, 4 A). RED 8/8 contra 1d9a424 (carrera de AUD-06 reproducida) y GREEN; suite 323 tests con 18 skipped (+36 de gobernanza); snapshot p50/p95 con 300 000 runs 1 484,90/1 605,30 → 206,44/239,72 ms. Garantía INTRA-respuesta: sequence es una cota, no identidad; visibilidad histórica por hora civil sigue UNVERIFIED. Recomendaciones no bloqueantes sin aplicar: A1 (el desempate/snapshot_id del tablero no es identidad de contenido, preexistente), A2 (sin statement_timeout ni pool; MP-032/033), A3 (consistent_read lanza ValueError con conexión ya en transacción), A4 (_revision_scope solo degrada con InsufficientPrivilege). NO cierra FR-01 ni HG-H4-SCOPE. Apilada sobre MP-025a (PR #8): rama pedromaaz13/mp-026b-snapshot-consistente; Integrada en main por PR #9 (merge commit 4bc8612, 2026-11-26) tras #8. gh pr checks 9 confirmó frontend, governance y python en PASS. La visibilidad histórica por hora permanece UNVERIFIED.

#### Reanudar MP-027

Portada, legal y puertas falsables (H4-10)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Criterios de portada, atribución y teselas.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Gates humanos** · HG-TILES
- **Bloqueos** · HG-H4-SCOPE, HG-TILES
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Revisar condiciones y presentar proveedor de teselas.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4; elegir proveedor de teselas y confirmar condiciones, DEC-002/003 según la ficha.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar MP-028

Captura en vivo (≥2 h, ≥3 días) (H4-12)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Tres días distintos con ≥120 min efectivos por jornada, cierre limpio, manifiesto v2 y volcado con SHA-256.
- **Implementación** · IN_PROGRESS
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · 2/3 jornadas completadas; supervisor corregido integrado (#12).
- **Pendiente** · Jornada 3 pendiente de ejecución, sin programar.
- **Motivo** · Falta confirmar disponibilidad del Mac y ventana de servicio.
- **Dependencias** · MP-023
- **Gates humanos** · HG-CAPTURE
- **Condición para retomar** · Ventana confirmada para capturar antes de que venza el GTFS (2026-12-18).
- **Próxima acción** · Acordar ventana y ejecutar el protocolo versionado.
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-26
- **HEAD revisado** · 172aa1b
- **Rama** · pedromaaz13/mp-028-captura
- **Commit de referencia** · 172aa1b
- **PR** · 12
- **Merge** · 2ffaee4fe51ed03937b01cadaa8e69dd5f86e711
- **Decisiones del propietario** · Confirmar la ventana de servicio y disponibilidad del Mac para la jornada 3.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/operations/CAPTURE_PROTOCOL.md](operations/CAPTURE_PROTOCOL.md); [docs/evidence/mp-025b/README.md](evidence/mp-025b/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md)

Preparación y smoke: Claude Sonnet 5.5 high aprobó a5ddc9b (300,09 s, 10/10 ciclos por feed, 212 posiciones y 24 vehículos). El delta 172aa1b recibió APPROVED para el supervisor (18 pruebas, 13 regresiones en a5ddc9b; suspensión simulada, falta comprobar: suspensión real del Mac). PR #12 integrado el 2026-11-27 (2ffaee4f). Jornada 1: 2026-11-26, ≥2 h efectivas tras excluir el hueco de suspensión (ver MP-025b). Jornada 2: 2026-11-27 07:54–09:54 UTC, 7 230 s efectivos, sin huecos, 235/235 ciclos por feed, volcado `session-2-20261127T095451Z.dump`, SHA-256 `6a325074c48c021428084af9741772187204f8abc8862cd22376e7ff922ca75f`, HEAD del colector `7300003`. Jornada 3 sigue prevista, pendiente de ejecución y sin programar. El prototipado de diseño puede empezar en paralelo. Preflight: Mac conectado al cargador y con tapa abierta, Docker y red operativos, ventana de servicio confirmada antes del fin de vigencia del GTFS (2026-12-18), worktree limpio y HEAD registrado. Desde el worktree de captura, seguir CAPTURE_PROTOCOL.md y lanzar desacoplado con `nohup caffeinate -i -s python infra/operate/capture/run-session.py 120 --max-civil-minutes 360 --gap-seconds 120 > jornada-3.log 2>&1 &` (usar el Python del entorno de captura). Verificar cierre y cobertura en `manifest.json` y ejecutar `shasum -a 256 -c capture.dump.sha256` desde el directorio de la sesión. Los datos quedan privados. Falta comprobar: verificación directa del manifiesto y SHA-256 privados en este worktree; constan en la evidencia de MP-038.

#### Reanudar MP-029

Corredores, ramales y catálogo honesto (H4-03)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Corredores y ramales acotados; catálogo con cobertura explícita.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Dependencias** · MP-024
- **Bloqueos** · HG-H4-SCOPE
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Delimitar los corredores y el modelo de segmentos; comprobar atribución OSM.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4 y descargas OSM con atribución.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Depende del modelo de segmentos (en MP-024 o ADR propio, H4_TASK_MATRIX). Alcance H4: mejoras sin rediseño y catálogo honesto. El PoC de grafo y la expansión por cobertura son trabajo posterior a la beta (propuestas). El grafo completo queda fuera del lote.

#### Reanudar MP-030

Interfaz: procedencia y rótulos veraces (H4-05)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Procedencia, congelación, cancelación y vigencia inequívocas en escritorio y móvil; revisión del HEAD final.
- **Implementación** · IMPLEMENTED
- **Revisión** · CHANGES_REQUESTED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Interfaz mínima integrada (#11); delta visual focalizado PASS.
- **Pendiente** · A1 cancelado «En servicio hoy»; A2 avance contradictorio; A3 cancelado y congelado iguales en el mapa.
- **Motivo** · Código final sin re-verificación independiente; quedan casos visuales NOT RUN.
- **Dependencias** · MP-024
- **Condición para retomar** · Revisor independiente y navegador disponibles; autorización para corregir A1–A3.
- **Próxima acción** · Solicitar revisión del código final y repetir la matriz de navegador y accesibilidad.
- **Ejecutor** · codex
- **Revisor** · claude
- **Fecha de revisión** · 2026-11-26
- **HEAD revisado** · 6e60249
- **Rama** · pedromaaz13/mp-030-interfaz-veraz
- **Commit de referencia** · 0600610
- **PR** · 11
- **Merge** · 359932dbe8e6706e42b7a96c49acdc2afba535b5
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)
- **Evidencias** · [docs/evidence/mp-030/README.md](evidence/mp-030/README.md); [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md); [docs/CHANGELOG.md](CHANGELOG.md); [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md)

Interfaz funcional mínima (procedencia por método y espacio, hold_reason, congelación F1, cancelación, degradación GTFS desde el snapshot); sin rediseño A/B/C. Ejecutor Codex gpt-6.1-terra medium (recibo de Orca; sin navegador); revisor Claude Sonnet 5.5 high con Chrome DevTools MCP verificado (argv verificado). Revisión completa: CHANGES_REQUESTED (2 B, 7 A). Verificación del delta (6e60249): B1, B2, A2-A7 resueltos; A1 parcial con un hallazgo material (congelada indistinguible de observada sobre corredor). Corrección final 0600610 (Terra, 142 tests). COMPROBACIÓN VISUAL EXCEPCIONAL (autorizada por el propietario, 2026-11-26): PASS en escritorio 1440x900 y móvil 390x844 con navegador real (Chrome DevTools MCP) sobre HEAD 35489b2 (apps/web idéntico a 0600610): la congelada (authorized_envelope_end y anchor_version_changed) se distingue de observada sobre corredor, extrapolada y bruta por contorno y punto interior, no solo por color; leyenda sin duplicado; Ampliar panel sin solapar el aviso GTFS. Cancelado y terminal EXISTEN en los datos reales de la jornada 1 (20226, 75303, 20797; terminal 20710 y 19601): evidencia REAL. Solo el motivo terminal en la fixture de 20797 es SIMULADO (identificado y separado). 0 B, 3 A no bloqueantes: A1 un cancelado muestra Estado: En servicio hoy; A2 mensajes contradictorios (puede seguir avanzando frente a no avanza); A3 en el mapa un cancelado es indistinguible de un congelado (solo lo dice el panel). NOT RUN: schedule_incoherent, outside_schedule_extent, horizon_exhausted, not_yet_valid, lector de pantalla y otros navegadores. Capturas fuera de Git en data/capture/2026-11-26/mp030-visual-final/. PR #11 integrado el 2026-11-27 (359932db). Se conserva CHANGES_REQUESTED sobre el delta de código 6e60249; la comprobación visual de 35489b2 (apps/web idéntico a 0600610) fue focalizada y no re-verificó el código final. Falta comprobar: acceso a las capturas privadas para reproducir la revisión visual.

#### Reanudar MP-031

Métricas de cierre honestas (H4-06)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Métricas de cierre con denominadores y cobertura.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Dependencias** · MP-028
- **Bloqueos** · HG-H4-SCOPE, MP-028
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Preparar el contraste con la captura validada de MP-028.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar MP-032

Operación supervisada local medida (H4-07)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Medición de operación local supervisada.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Dependencias** · MP-023
- **Gates humanos** · HG-HOSTING
- **Bloqueos** · HG-H4-SCOPE, HG-HOSTING
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Definir el protocolo de operación y medir coste en entorno aislado.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4 y decidir host persistente y coste, sin contratación en este lote.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar MP-033

Rendimiento y coste (H4-08)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Medición de rendimiento y coste.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Dependencias** · MP-026a, MP-026b, MP-032
- **Gates humanos** · HG-DEC-038, HG-DEC-004
- **Bloqueos** · HG-H4-SCOPE, MP-032, HG-DEC-038, HG-DEC-004
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Medir carga tras MP-032 y documentar alternativas de pool y retención.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4 y decidir pool (DEC-038) y retención (DEC-004).
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar MP-034

Registro estructurado de hallazgos (H4-13)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Aprobación humana donde indica docs/H4_MP_MAPPING.md; prueba RED en beb9434 y GREEN tras el fix
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Registro estructurado de hallazgos de auditoría.
- **Motivo** · Alcance general H4 pendiente de autorización.
- **Bloqueos** · HG-H4-SCOPE
- **Condición para retomar** · Autorización de alcance y resolución de condiciones de la ficha.
- **Próxima acción** · Cruzar FINDINGS_REGISTER.md con correcciones y evidencia.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar alcance H4.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar MP-035

Gate de publicación (H4-09)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Todas las tareas MP-023…MP-034 cerradas o con BLOCKED documentado; decisión humana GO/NO-GO de publicación
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Alcance documentado.
- **Pendiente** · Dictamen GO/NO-GO y gate de publicación.
- **Motivo** · NO-GO público y criterios de dependencias abiertos.
- **Dependencias** · MP-023, MP-024, MP-025a, MP-025b, MP-026a, MP-026b, MP-027, MP-028, MP-029, MP-030, MP-031, MP-032, MP-033, MP-034
- **Gates humanos** · HG-LIVE-PUBLIC
- **Bloqueos** · FR-01, FR-02, HG-LIVE-PUBLIC
- **Condición para retomar** · Dictamen GO documentado y aprobación del propietario.
- **Próxima acción** · Auditar criterios de cada dependencia y presentar dictamen al propietario.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar expresamente despliegue Live público tras dictamen GO.
- **Ficha de alcance** · [docs/H4_MP_MAPPING.md](H4_MP_MAPPING.md)

Planificada; implementación H4 no autorizada.

#### Reanudar D-01

Captura local de 90 min con BD desechable y manifest

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Captura de 90 min y manifiesto.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Dependencias** · MP-023
- **Gates humanos** · HG-CAPTURE
- **Bloqueos** · HG-CAPTURE
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Confirmar autorización y preparar captura desechable propia.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar captura continua local para D-01.
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-02

Contrato de demo estática y exportador determinista

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Contrato y exportador reproducible.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Definir contrato y verificar hash y paridad API del exportador.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-03

Adaptador estático, reloj en bucle, banner y pie

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Adaptador, reloj y rótulos de demo.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Dependencias** · D-02
- **Bloqueos** · D-02
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Construir el modo estático sobre el contrato D-02.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-04

Teselas configurables y estilo OpenFreeMap

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Teselas y atribución de demo.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Gates humanos** · HG-TILES
- **Bloqueos** · HG-TILES
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Verificar condiciones de OpenFreeMap y proponer configuración.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Confirmar proveedor y condiciones de teselas.
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-05

vite base, verify-build demo y pages.yml

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Build verificable y workflow Pages.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Dependencias** · D-03, D-04
- **Bloqueos** · D-03, D-04
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Probar vite base y verify-build en entorno previo.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Autorizar Pages y despliegue de la demo cuando se apruebe.
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-06

Validación integrada de la demo y aprobación del propietario

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 0 de docs/plans/MVP_LIVE_END_TO_END.md en dos tiempos: (1) contrato, build y capturas en entorno previo; (2) tras HG-MVP0-PUBLISH, comprobación de la URL pública. No se da por cerrado hasta el segundo tiempo
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Plan de demo documentado.
- **Pendiente** · Validación integrada y URL comprobada.
- **Motivo** · Ejecución de MVP 0 pendiente de autorización.
- **Dependencias** · D-01, D-02, D-03, D-04, D-05
- **Gates humanos** · HG-MVP0-PUBLISH
- **Bloqueos** · D-01, D-02, D-03, D-04, D-05, HG-MVP0-PUBLISH
- **Condición para retomar** · Autorización de MVP 0 y precondiciones de la ficha.
- **Próxima acción** · Ejecutar contrato, build, capturas y atribuciones; presentar la demo.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Aprobar publicar la URL de la demo estática.
- **Ficha de alcance** · [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](deployment/MVP0_IMPLEMENTATION_PLAN.md)

Planificada; no autorizada. La demo no condiciona ni bloquea los P0 de Live.

#### Reanudar D-11

Dockerfiles, compose de producción y Caddy mismo origen

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Dockerfiles, Compose y Caddy.
- **Motivo** · Staging sin autorización.
- **Dependencias** · MP-023
- **Bloqueos** · PROPOSAL-STAGING-LIVE, MP-023
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Confirmar alcance de staging y validar un arranque aislado.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-12

Migraciones idempotentes en arranque

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Migraciones idempotentes en arranque.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Probar dos arranques en una base desechable.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-14

Purga y retención de BD caliente

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Purga y archivo en volumen.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Medir crecimiento de la BD caliente y contrastar DEC-004.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste., Decidir plazo de retención y umbral de crecimiento (DEC-004).
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-15

Rate limit, /healthz y cabeceras de seguridad

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Rate limit y salud.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Medir limitación de ráfagas y liveness sin BD.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-16

Backups con restauración probada

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Backups y restauración.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Restaurar un backup en una BD desechable y cuadrar filas.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-17

CD por SSH con aprobación manual

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · CD por SSH con aprobación manual.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Verificar que el workflow requiere aprobación antes del despliegue.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar D-18

Operación supervisada ≥24 h (ideal 72 h)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Gate 1 de docs/plans/MVP_LIVE_END_TO_END.md
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Subalcance propuesto documentado.
- **Pendiente** · Operación supervisada durante ≥24 h.
- **Motivo** · Staging sin autorización.
- **Dependencias** · D-11, D-12, D-14, D-15, D-16
- **Bloqueos** · PROPOSAL-STAGING-LIVE, D-11, D-12, D-14, D-15, D-16
- **Condición para retomar** · Staging autorizado y precondiciones de despliegue acreditadas.
- **Próxima acción** · Medir continuidad, recursos y recuperación tras abrir el staging.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Decidir si se autoriza staging como tarea propia y, si procede, hosting y coste.
- **Ficha de alcance** · [docs/deployment/MVP_RELEASE_CHECKLIST.md](deployment/MVP_RELEASE_CHECKLIST.md)

Subalcance de staging propuesto (separado de MP-032 local hasta decisión del propietario); no duplica backlog. D-19 (cierre de FR-01 y FR-02) = MP-024, MP-025a/b y MP-026a: solo en CROSSWALK.

#### Reanudar DES-00

Baseline y verificación de restricciones

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Baseline versionado y restricciones comprobadas
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Baseline versionado y restricciones comprobadas.
- **Motivo** · Pendiente de despacho.
- **Gates humanos** · HG-DESIGN-START
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Verificar HEAD, worktrees y restricciones; redactar 00_BASELINE/STATE.md.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-01

Inspección real y capturas del frontend existente (Claude + preflight de DevTools/Playwright)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Capturas desktop/móvil y consola del frontend actual
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Capturas desktop/móvil y consola del frontend actual.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-00
- **Bloqueos** · DES-00
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Hacer preflight de navegador y capturar vistas; si falta, registrar NOT RUN.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-02

Comparación de fuentes de diseño (frontend-design, Hallmark, Impeccable)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Comparativa de tres fuentes de diseño
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Comparativa de tres fuentes de diseño.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-00
- **Bloqueos** · DES-00
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Comprobar versiones, licencias, hooks y permisos sin instalar.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-03

Brief y tres conceptos A/B/C

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Brief factual y conceptos A/B/C
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Brief factual y conceptos A/B/C.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-01, DES-02
- **Bloqueos** · DES-01, DES-02
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Redactar el brief desde baseline y revisión de fuentes.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-04

Prototipo A Titanium Control

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Prototipo A Titanium Control
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Prototipo A Titanium Control.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-03
- **Bloqueos** · DES-03
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Montar A en su worktree aislado según el brief.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-05

Prototipo B Immersive Rail Map

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Prototipo B Immersive Rail Map
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Prototipo B Immersive Rail Map.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-03
- **Bloqueos** · DES-03
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Montar B con jerarquía map-first en worktree aislado.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-06

Prototipo C Contemporary Signal

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Prototipo C Contemporary Signal
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Prototipo C Contemporary Signal.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-03
- **Bloqueos** · DES-03
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Montar C con navegación propia en worktree aislado.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-07

Comparativa de iconografía ferroviaria

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Iconografía comparada y medición en MapLibre
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Iconografía comparada y medición en MapLibre.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-03
- **Bloqueos** · DES-03
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Probar variantes de iconos; medir solo con navegador verificado.
- **Ejecutor** · codex
- **Revisor** · claude
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-08

Verificación comparativa A/B/C en navegador real (Claude + preflight; Codex audita código y artefactos)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Comparación en navegador; gate visual independiente NOT RUN
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Comparación en navegador; gate visual independiente NOT RUN.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-04, DES-05, DES-06, DES-07
- **Bloqueos** · DES-04, DES-05, DES-06, DES-07
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Preflight y revisión de flujos, responsive, teclado y reduced motion.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar DES-09

Índice comparativo y gate humano de elección

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Índice de evidencia, matriz A/B/C y elección
- **Implementación** · PLANNED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · NOT_VALIDATED
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Inicio de discovery autorizado.
- **Pendiente** · Índice de evidencia, matriz A/B/C y elección.
- **Motivo** · Precondiciones del discovery pendientes.
- **Dependencias** · DES-08
- **Bloqueos** · DES-08, HG-DESIGN-CHOICE
- **Condición para retomar** · Despacho en worktree aislado y precondiciones acreditadas.
- **Próxima acción** · Presentar comparación al propietario y esperar su elección.
- **Ejecutor** · claude
- **Revisor** · codex
- **Commit de referencia** · UNKNOWN
- **Decisiones del propietario** · Elegir A/B/C en HG-DESIGN-CHOICE; cualquier integración productiva requiere autorización.
- **Ficha de alcance** · [docs/design/DESIGN_DISCOVERY_A_B_C.md](design/DESIGN_DISCOVERY_A_B_C.md)
- **Evidencias** · [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)

Subtarea interna. Sustitución temporal y alcance en el override del 2026-11-27; roles del plan sujetos al despacho efectivo. HG-DESIGN-CHOICE abierto.

#### Reanudar MP-036

Fallback del motor: una observación rechazada no reaparece como ancla aceptada (A→B→A)

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Regresión RED/GREEN; reconstrucción determinista del historial sin cambiar el esquema; coste acotado y medido; una revisión completa y una verificación del delta
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Fallback determinista K=2 integrado (#15); 0/416 reapariciones en jornada 1.
- **Pendiente** · Caracterizar recuperación, jitter y cota 256 en más datos.
- **Motivo** · El propietario aceptó los costes para desarrollo local; FR-01 sigue abierto.
- **Condición para retomar** · Datos de una jornada completa y autorización para el contraste.
- **Próxima acción** · Medir cota 256 y recuperación sobre una jornada completa antes de plantear ajustes.
- **Ejecutor** · codex
- **Revisor** · claude
- **HEAD revisado** · 8c005c8
- **Rama** · pedromaaz13/mp-036-fallback-gps-rechazado
- **Commit de referencia** · 0c518fa
- **PR** · 15
- **Merge** · d3be45dc5523a36ade751fd6e2aad28700e19c44
- **Decisiones del propietario** · Decidir si se autoriza evaluar cambios de K/cota tras medir los costes con datos posteriores.
- **Ficha de alcance** · [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md)
- **Evidencias** · [docs/evidence/mp-036/README.md](evidence/mp-036/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md)

Revisión Opus High: a7e01b8 CHANGES_REQUESTED (2 B, 8 A); delta 8c005c8 APPROVED (3 A residuales). Reconstrucción determinista del historial sin migraciones; re-anclaje K=2 configurable; RED 9+5, GREEN 339/18 omitidos. Integrada el 2026-11-27 (d3be45dc). El propietario aceptó los costes medidos exclusivamente para desarrollo local. Precisión física, cumplimiento integral del motor y preparación para publicación siguen pendientes; FR-01 y NO-GO público abiertos.

#### Reanudar MP-037

Estudio de contradicciones de estado: M7 frente a R4 y STOPPED_AT incoherente con el GPS

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Comparación de políticas sobre la captura existente; recomendación y, si cambia la precedencia aprobada del ADR, enmienda concreta para decisión del propietario antes de implementar
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Estudio M7/R4 y STOPPED_AT integrado (#16); R4 conservada.
- **Pendiente** · Validar candidatas parada_previa, gps_previo y R7→R8 condicional con datos posteriores.
- **Motivo** · La evidencia no establece exactitud física; alternativas pendientes de decisión.
- **Dependencias** · MP-025b
- **Condición para retomar** · Autorización del contraste y datos posteriores para decidir.
- **Próxima acción** · Contrastar la jornada 2 y añadir la 3 cuando exista; presentar los deltas al propietario.
- **Ejecutor** · codex
- **Revisor** · claude
- **HEAD revisado** · ebaea29
- **Rama** · pedromaaz13/mp-037-estudio-m7-r4
- **Commit de referencia** · ebaea29
- **PR** · 16
- **Merge** · 14709bba5280b71b2bd8b9c129a3e4ca10421681
- **Decisiones del propietario** · Decidir si se acepta alguna candidata, con enmienda si cambia la precedencia del ADR.
- **Ficha de alcance** · [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md)
- **Evidencias** · [docs/evidence/mp-037/README.md](evidence/mp-037/README.md)

Estudio de 19 planes positivos con STOPPED_AT incoherente y 135 retenciones de M7. Conservar R4 produjo menos discontinuidades frente a GPS discretizado; exactitud física UNVERIFIED. parada_previa tuvo efecto mínimo y gps_previo intercambió discontinuidades; R7→R8 condicional sigue candidata. Revisión Opus High: CHANGES_REQUESTED (2 B, 5 A) y delta APPROVED. PR #16, merge 14709bba (2026-11-26 23:01 UTC, 2026-11-27 hora de Madrid), integrado como estudio. R4 y el ADR siguen intactos.

#### Reanudar MP-038

Evaluación comparable antes/después sobre las mismas entradas

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Baseline y corrección sobre las mismas entradas; dump, manifiesto y resultados originales intactos; métricas globales y estratificadas con denominadores, exclusiones y casos adversos
- **Implementación** · IMPLEMENTED
- **Revisión** · APPROVED
- **Integración** · MERGED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_DEPLOYED
- **Terminado** · Evaluación reproducible integrada (#17); jornadas 1 y 2 comparadas.
- **Pendiente** · Completar evidencia de aceptación del motor tras la jornada 3.
- **Motivo** · La evaluación mide costes y discontinuidades; FR-01 abierto.
- **Dependencias** · MP-025b, MP-036, MP-037
- **Bloqueos** · MP-028
- **Condición para retomar** · Jornada 3 capturada y artefactos verificados.
- **Próxima acción** · Repetir la comparación con entradas de jornada 3 y criterios congelados.
- **Ejecutor** · codex
- **Revisor** · claude
- **HEAD revisado** · dc59299
- **Rama** · pedromaaz13/mp-038-evaluacion-comparable
- **Commit de referencia** · b7aed67
- **PR** · 17
- **Merge** · 453a5eb53f53c1f5c45314b1a77d1aae7daa06f0
- **Ficha de alcance** · [docs/roadmap/CROSSWALK.md](roadmap/CROSSWALK.md)
- **Evidencias** · [docs/evidence/mp-038/README.md](evidence/mp-038/README.md); [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md)

Separa discrepancia frente al GPS bruto (incluso rechazado), cambio de ancla efectiva aceptada y discontinuidad de la posición presentada. No cambia retrospectivamente el criterio de aceptación. Autorizada el 2026-11-26. FR-01 permanece abierto. RESULTADO (2026-11-26): baseline 4bc8612 frente a corrección 0c518fa sobre la misma jornada 1; saltos presentados >200 m 2 935→2 771 (24 nuevos frente a 188 reducidos; 8 vehículos peores; STOPPED_AT 32↑/23↓); discrepancia frente al GPS bruto en 216 retenciones 674,5→1 845,6 m (se aleja con GPS congelado, 113/113). Revisión Opus High: 1ª pasada CHANGES_REQUESTED (2 B, 7 A) → delta APPROVED. FR-01 abierto. Evidencia: informe docs/evidence/mp-038/README.md en el PR #17 (head 39166da; revisado en 6615d53). JORNADA 2 (2026-11-27, captura 07:54–09:54 UTC: 7 230 s efectivos, 0 huecos, feeds 235/235): baseline 4bc8612 frente a MP-036 0c518fa con la configuración actual (K=2, cota 256, sin ajustes): reapariciones A→B→A 5→0 sobre 373 tríadas; saltos comunes >200 m 2 587→2 461 sobre 39 973 pares; COSTES: ancla más antigua en 1 932/40 117 fotogramas (mediana +78 s, máx 220 s), retenciones >180 s 3→12 (7 censuradas), p90 de recuperación 30,9→61,7 s, discrepancia frente al GPS bruto mayor en 52/52 pares con coordenada repetida. Verificación única Opus High: APPROVED (2 observaciones no bloqueantes, resueltas). Informe docs/evidence/mp-038/JORNADA2.md en el PR #17 (head b7aed67; verificado en dc59299). FR-01 abierto: una jornada más no cierra nada. INTEGRADA el 2026-11-27 por decisión del propietario (PR #17, merge commit 453a5eb5). Integrar NO es validar ni publicar: FR-01 y el NO-GO público siguen abiertos. Las evidencias enlazadas conservan los denominadores, exclusiones y casos censurados originales; la revisión y la integración tienen el alcance del informe.

#### Reanudar GOV-TRACKING

Seguimiento recuperable del plan

- **Última actualización** · 2026-11-27
- **Criterio de cierre** · Estado coherente con main y evidencias, regeneración determinista, preservación manual, tests de gobernanza y revisión independiente.
- **Implementación** · IMPLEMENTED
- **Revisión** · NOT_REVIEWED
- **Integración** · NOT_INTEGRATED
- **Validación** · PROVISIONAL
- **Despliegue** · NOT_APPLICABLE
- **Terminado** · Tablero, fichas de reanudación y registro de diferidos implementados.
- **Pendiente** · Revisión de Claude pendiente.
- **Motivo** · Claude sin cuota; implementación pendiente de revisión.
- **Condición para retomar** · Claude vuelve a estar disponible.
- **Próxima acción** · Revisar el diff del PR #14 y repetir la suite de gobernanza sobre el HEAD entregado.
- **Ejecutor** · codex
- **Revisor** · claude
- **Rama** · docs/tareas-lote-correccion
- **Commit de referencia** · f3e3b0a
- **PR** · 14
- **Ficha de alcance** · [docs/governance/UPDATE_PROTOCOL.md](governance/UPDATE_PROTOCOL.md)
- **Evidencias** · [docs/governance/DISPATCH_LOG.md](governance/DISPATCH_LOG.md); [tests/governance/test_governance.py](../tests/governance/test_governance.py); [docs/STATUS.md](STATUS.md)

El HEAD indicado es la base verificada de este despacho (no el HEAD de revisión); el commit de entrega se identifica en la rama.

### Registro de hallazgos y propuestas diferidas

Estado `DEFERRED`. Trabajo sujeto a autorización.

| ID | Origen | Hallazgo o propuesta | Motivo | Condición para retomar |
| --- | --- | --- | --- | --- |
| DEF-DISPLAY-LAG | [docs/evidence/mp-026a/README.md](evidence/mp-026a/README.md) | Añadir tope le=3600 a display_lag_s y devolver 422 por encima. | Propuesta fuera del fix temporal. | Autorización explícita y regresión de límites de la API. |
| DEF-MP-030-A1 | [docs/CHANGELOG.md](CHANGELOG.md) | El cancelado aparece como «En servicio hoy». | Observación no bloqueante de la comprobación focalizada del PR #11. | Autorizar el ajuste y verificar en navegador con replay identificado. |
| DEF-MP-030-A2 | [docs/CHANGELOG.md](CHANGELOG.md) | El panel contradice si el tren puede seguir avanzando. | Observación no bloqueante de la comprobación focalizada del PR #11. | Autorizar el ajuste y verificar en navegador con replay identificado. |
| DEF-MP-030-A3 | [docs/CHANGELOG.md](CHANGELOG.md) | Cancelado y congelado son indistinguibles en el mapa. | Observación no bloqueante de la comprobación focalizada del PR #11. | Autorizar el ajuste y verificar en navegador con replay identificado. |
| DEF-MP-030-NOT-RUN | [docs/CHANGELOG.md](CHANGELOG.md) | schedule_incoherent, outside_schedule_extent, horizon_exhausted, not_yet_valid, lector de pantalla y otros navegadores: NOT RUN. | Quedaron fuera de la comprobación visual focalizada. | Matriz de pruebas y entorno con navegador y lector de pantalla disponibles. |
| DEF-MP-036-K | [docs/evidence/mp-036/README.md](evidence/mp-036/README.md) | 20752 no recuperado con K=2; K=1 rompe A→B→A. | El ajuste cambia el compromiso entre recuperación y reapariciones. | Medir ambos costes con datos posteriores y solicitar autorización. |
| DEF-MP-036-CATALOGO | [docs/evidence/mp-036/README.md](evidence/mp-036/README.md) | Listado legado C1/C8a/C9↔C4. | La corrección preserva el catálogo existente. | Comprobar el catálogo y sus patrones con evidencia versionada antes de cambiarlo. |
| DEF-MP-036-JITTER | [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) | Coste del re-anclaje erróneo, retenciones y jitter. | Costes aceptados solo para desarrollo local. | Probar latencia, recuperación y transiciones adversas con jornadas adicionales. |
| DEF-COTA-256 | [docs/evidence/mp-036/README.md](evidence/mp-036/README.md) | Medir la cota de 256 muestras con una jornada completa. | Las ventanas disponibles no cubren un día completo. | Captura de día completo y benchmark de historial con denominadores. |
| DEF-MP-037-PARADA | [docs/evidence/mp-037/README.md](evidence/mp-037/README.md) | Candidata parada_previa. | Estudio integrado sin cambios de política; evidencia acotada a la jornada 1. | Contrastar en jornadas posteriores; decisión expresa del propietario antes de implementar. |
| DEF-MP-037-GPS | [docs/evidence/mp-037/README.md](evidence/mp-037/README.md) | Candidata gps_previo. | Estudio integrado sin cambios de política; evidencia acotada a la jornada 1. | Contrastar en jornadas posteriores; decisión expresa del propietario antes de implementar. |
| DEF-MP-037-R8 | [docs/evidence/mp-037/README.md](evidence/mp-037/README.md) | Candidata R7→R8 condicional. | Estudio integrado sin cambios de política; evidencia acotada a la jornada 1. | Contrastar en jornadas posteriores; decisión expresa del propietario antes de implementar. |
| DEF-SOAK-MP-007 | [docs/TASKS.md#mp-007--collector-idempotente](TASKS.md#mp-007--collector-idempotente) | Soak real de 24 h para gate F3. | Soak disponible de 20 min, con 668 posiciones. | Autorizar operación aislada de MP-032 y documentar una corrida de 24 h. |
| DEF-TEST-SEGMENTS | [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) | test_segments en el endpoint histórico de MP-025b: NOT RUN. | Los replays ejecutaron check_segment sobre las vistas temporales. | Reproducir el endpoint de prueba en entorno aislado y ejecutar la suite. |
| DEF-ADR-CANCELACION | [docs/adr/0014-amendment-stop-state.md](adr/0014-amendment-stop-state.md) | Falta comprobar: nombre contractual del campo de cancelación. | El ADR deja abierto el nombre definitivo. | Verificar contrato y evidencia de fuente; decisión expresa del propietario. |
| DEF-VISUAL-INDEPENDIENTE | [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) | Gate visual independiente del discovery: NOT RUN. | Falta capacidad de navegador verificada para revisión cruzada. | Preflight de navegador en proveedor contrario y capturas reproducibles. |
| DEF-GPS-CUANTIZADO | [docs/evidence/mp-038/JORNADA2.md](evidence/mp-038/JORNADA2.md) | GPS Renfe cuantizado y coordenadas repetidas. | La repetición no demuestra posición física ni origen de la cuantización. | Contrastar con más jornadas y evidencia operativa independiente. |
| DEF-REPLAY-CIVIL | [docs/adr/0014-amendment-owner-decision.md](adr/0014-amendment-owner-decision.md) | Visibilidad histórica exacta por hora civil UNVERIFIED. | La garantía aprobada usa identificador de ancla/run. | Obtener evidencia histórica de publicación y una prueba entre inicio y commit (MP-026b/MP-032). |
| DEF-MP-023-REVISION | [docs/evidence/mp-023/ROUND2.md](evidence/mp-023/ROUND2.md) | Arnés de aislamiento fuera de CI, errores con entorno vacío, reinicio del supervisor y ajustes menores de herramientas. | Recomendaciones no bloqueantes de la revisión. | Autorizar el seguimiento o priorizarlo al planificar operación local. |
| DEF-MP-026B-REVISION | [docs/evidence/mp-026b/README.md](evidence/mp-026b/README.md) | Identidad del tablero, statement_timeout/pool y casos de error en consistent_read y _revision_scope. | Observaciones no bloqueantes; el ticket cubre coherencia intra-respuesta. | Revisarlas con las mediciones de MP-032/033 y autorización del alcance. |
| DEF-MP-028-SUSPENSION | [docs/operations/CAPTURE_PROTOCOL.md](operations/CAPTURE_PROTOCOL.md) | Falta comprobar suspensión real y recuperación de un colector huérfano. | La cobertura del delta de supervisor se verificó mediante simulación. | Ensayo controlado en entorno aislado y ventana separada de la jornada 3. |
| DEF-MP-025A-REVISION | [docs/evidence/mp-025a/ronda2/README.md](evidence/mp-025a/ronda2/README.md) | Bloqueo huérfano con SIGSTOP y valor de regresión de test_collector_without_gtfs_holds_from_first_frame. | Observaciones no bloqueantes fuera del cierre determinista de MP-025a. | Reproducir el escenario y acordar prioridad con el propietario. |

<!-- END GENERATED: backlog-index -->
