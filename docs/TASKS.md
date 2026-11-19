# TASKS.md — Backlog Madrid Pulse (MP-001 a MP-015)

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
  - 45 tests reales en verde: 31 `packages/contracts` (23 previos + 1 regresión de `entity` ausente + 7 de `nucleo_prefix`/`SPECIAL_`), 6 fixtures de MP-004, 8 de `services/collector` (4 de reintentos/backoff sin red, 4 de integración contra PostgreSQL real: idempotencia, fila nueva ante cambio real, filtro de alcance por núcleo, fallo de red registrado sin relanzar).
  - **Soak test real de 20 minutos** contra los tres feeds en vivo de Renfe (`https://gtfsrt.renfe.com/*.json`, ventana `2026-11-18 23:31:55Z`–`23:51:47Z`): 40 ciclos completos (120 fetches), **0 errores, 0 tracebacks**. Totales acumulados: 1155 entidades insertadas, 304 deduplicadas, 2622 descartadas por estar fuera de núcleo (Madrid). Verificado con una conexión `psql` nueva (no la del proceso) tras finalizar: `vehicle_position_observation`=668, `trip_update_observation`=484, `service_alert`=3, `source_ingestion_run` status=`ok`×120/`error`×0 — confirma que `run_cycle` compromete cada ciclo de verdad, no solo en memoria. Esta ventana de 20 min demuestra el comportamiento sostenido pedido por el criterio de aceptación; el *exit gate* de 24 h de la fase F3 completa (`docs/PLAN.md`) es una validación más larga, pendiente como actividad de monitorización continuada, no bloqueante para cerrar MP-007 bajo el régimen de autonomía de ADR-0007 (no es una decisión de licencia/coste).
  - Rechazo de duplicados real: verificado por `test_repeated_identical_payload_stores_a_single_row_per_entity` contra PostgreSQL real (no mock) — un payload idéntico repetido no inserta fila nueva; un cambio real (ej. `currentStatus`) inserta exactamente una fila nueva.
  - **3 hallazgos reales corregidos durante la verificación** (feed en vivo, fuera de lo cubierto por las fixtures más pequeñas de MP-003/MP-004): (1) `trip_id` de refuerzo `SPECIAL_<núcleo>_<resto>` sin prefijo numérico directo — corregido `packages/contracts/nucleo.py`; (2) `stopTimeUpdate[].arrival` sin `delay` en un tren `ADDED` — corregido `raw.py` a `Optional`; (3) una respuesta real omitió la clave `entity` por completo (0 vehículos) — corregido con `default_factory=list` en los tres `Raw*Feed`. Las tres correcciones tienen test de regresión. Detalle completo en `docs/research/MP-003-probe-findings.md` §10 y adendas de ADR-0008/ADR-0009.
  - **1 bug de transacciones corregido antes de llegar a producción:** una versión anterior de `db.py` envolvía cada `INSERT` en su propio `with conn.transaction()`; con una conexión de larga duración, solo el primero de una secuencia se comprometía como transacción real — los siguientes quedaban como `SAVEPOINT` de una transacción ambiente que nunca se comprometía, por lo que `vehicle_position_observation` quedaba vacío pese a que `source_ingestion_run` sí persistía. Detectado al verificar con una conexión nueva tras cerrar la original (no solo confiando en que `run_cycle` "no lanzó excepción"). Corregido centralizando el límite de transacción en `run_cycle` (un único `with conn.transaction()` por ciclo).
  - **Hallazgo de alcance documentado, no bloqueante:** el filtro de ingesta descarta por núcleo (`nucleo_prefix == "10"`, Madrid) pero no acota todavía a la línea C5 específicamente, que es el alcance real de ADR-0001 (`Aceptado`). Ver DEC-020/ADR-0008 (adenda). Acotar a C5 exige resolver `trip_id` → `route_id` vía el GTFS estático, trabajo asignado explícitamente a MP-010 por ADR-0009.
  - `ADR-0010` (nuevo, `Propuesto`): estrategia de deduplicación — hash canónico completo de la entidad comparado contra la última fila almacenada por clave de entidad de origen, sin `seen_count`.
  - Identidad Git verificada en cada commit (`Pedro Matute`, sin coautores); contenedor `madrid-pulse` detenido al finalizar (`docker compose ... down`, sin `--volumes`: el volumen con los datos reales del soak test se conserva); contenedores `*-traza-app` confirmados intactos antes y después.
  - **Primera revisión independiente de Codex (dispatch `ctx_a674a371ce8a`): no aprobada — 1 bloqueante real y reproducible.** Repitió las 45 pruebas, auditó transacciones/alcance/secretos/identidad Git/enlaces, y reprodujo en vivo (`curl` directo) los hallazgos de `SPECIAL_`/`ADDED`. Encontró que `latest_payload_hash` (`db.py`) ordenaba solo por `observed_at DESC` sin desempate: cuando dos filas de la misma entidad comparten `observed_at` (plausible porque ese timestamp lo reporta la fuente, no nuestro poll), Postgres puede devolver cualquiera de las filas empatadas sin garantía de orden. En su reproducción de 3 ciclos (inicial → cambio con mismo `observed_at` → repetición del cambio) obtuvo `(1, 6)` en el tercer ciclo en vez de `(0, 7)`: una fila duplicada real para el vehículo 19705, no solo un riesgo teórico.
  - Corregido añadiendo `id DESC` como desempate secundario en las tres consultas de `_LATEST_HASH_QUERIES`. Verificado revirtiendo el fix temporalmente y confirmando que el nuevo test de regresión (`test_tied_observed_at_does_not_break_dedup_on_third_cycle`) falla exactamente con `(1, 6)` como reportó Codex, y pasa `(0, 7)` con el fix restaurado. 46 tests en verde tras el fix (45 + 1 nuevo).
- **Estado:** `REVIEW` — bloqueante de la primera revisión de Codex corregido y verificado por Claude Code el 2026-11-19;
  pendiente de segunda verificación independiente de OpenAI Codex en este mismo worktree.

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
- **Evidencia de verificación:** suite de tests y ejemplos de flags generados.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** resultado del test de replay.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** suite de tests de topología.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** salida de test de continuidad + capturas de geometría.
- **Estado:** `TODO`

---

## MP-012 — Motor de movimiento v1

- **Fase:** F6 — Motor de movimiento
- **Objetivo:** implementar los estados `OBSERVED / ESTIMATED / STALE / SCHEDULED` con tests deterministas.
- **Prioridad:** P1
- **Depende de:** MP-008, MP-010, MP-011
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Nota de worktree (pendiente de resolver antes de empezar, sugerencia no bloqueante de Codex en la revisión de MP-001):** MP-012 es el primer punto de convergencia de ramas encadenadas — depende de tres tareas que pueden terminar en ramas distintas (MP-008 en la cadena MP-005→009, MP-010 y MP-011 en su propia rama paralela). `AGENTS.md` ("Modelo de autonomía por hito") describe cadenas y bifurcaciones, pero no especifica aún cómo una tarea con varias dependencias elige su rama base e integra las demás (p. ej. ramificar desde MP-011 y hacer `git merge`/rebase de MP-008 sobre ella, o viceversa). Debe decidirse y documentarse en `AGENTS.md` antes de abrir el worktree de MP-012.
- **Archivos/componentes afectados:** `packages/geo/`, `packages/quality/`, lógica de movimiento (ubicación exacta a definir en ADR si no cabe en paquetes existentes).
- **Entradas:** flags de calidad (MP-008), topología (MP-010), geometría (MP-011).
- **Entregables:** motor de movimiento con los cuatro estados, `confidence`, `age_s`, umbrales parametrizados (no fijos) siguiendo `docs/DATA_QUALITY.md`.
- **Criterios de aceptación:** tests deterministas cubren transición entre estados, saltos de estación y velocidades físicamente inverosímiles.
- **Pruebas necesarias:** suite de tests deterministas del motor de movimiento.
- **Evidencia de verificación:** suite de tests.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** suite de tests de contrato + OpenAPI generado.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** capturas/registro de la demo funcional + resultado de smoke tests.
- **Estado:** `TODO`

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
- **Evidencia de verificación:** resultado de CI + checklist firmado.
- **Estado:** `TODO`

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

Dos ramas pueden avanzar en paralelo en worktrees independientes una vez resuelto su ancestro común: `MP-005` y `MP-010` corren en paralelo tras `MP-004` (no dependen entre sí); `MP-006`/`MP-007` corren en la rama de `MP-005`, mientras `MP-011` corre en la rama de `MP-010`, hasta que ambas convergen en `MP-012`.
