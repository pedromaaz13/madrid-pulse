# TASKS.md — Backlog Madrid Pulse (MP-001 a MP-022)

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
- **Hallazgos abiertos (no silenciados):** el coste dominante de cada petición es abrir la conexión PostgreSQL (~66 ms de 68,91 ms de p50 en `/health`), registrado como DEC-038 porque un pool es dependencia nueva; y el `stop_time_update` por parada no está persistido en el modelo canónico, así que no hay evidencia directa de `SKIPPED` por parada (declarado en `limitations` del tablero).
- **Estado:** `REVIEW` — implementado y verificado por el ejecutor (Claude Opus) en el worktree `mp-019-snapshot-api`; pendiente de auditoría independiente de OpenAI Codex sobre el diff completo antes de poder pasar a `DONE`.

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
