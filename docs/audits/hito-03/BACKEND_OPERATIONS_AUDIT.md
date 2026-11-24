# AUD-06 — Backend, API, datos y operación

**Ejecutor:** Codex Terra · High
**Fecha:** 2026-11-23
**Rama/worktree:** `audit/hito-03-adversarial` / `<WORKTREES>/audit-hito-03`
**Alcance:** colector GTFS-RT, snapshots/API, PostgreSQL/PostGIS, histórico y operación. No se ha modificado código de producto.

## Veredicto

Hay un defecto de consistencia **P1**: `build_snapshot()` no fija una vista
transaccional única de PostgreSQL. Bajo una escritura concurrente puede devolver
`revision.sequence` de la nueva ingesta pero omitir su vehículo. La revisión es
precisamente el mecanismo que el contrato pide usar para ordenar respuestas, por
lo que una respuesta etiquetada como revisión 74 no representa necesariamente el
estado de la revisión 74.

El resto de controles principales resistió la reproducción: parsing y dedupe del
colector, tratamiento honesto de `SKIPPED`, índices de 0002, contrato OpenAPI,
cabeceras de caché, expiración y recuperación tras perder PostgreSQL. La
recuperación probada es una recuperación puntual, no una prueba de operación
24/7; la ventana previa de 823,2 s / 21 ciclos tampoco lo es.

## Entorno y reproducciones

Las pruebas planificadas usaron el contenedor desechable propio `aud06-postgis`
en `127.0.0.1:5546`, imagen `postgis/postgis:17-3.5`, con `0001_init.up.sql`
y `0002_api_batch_indexes.up.sql` aplicadas desde cero; se confirmó PostGIS 3.5
y 17 tablas públicas. **Excepción de alcance que debo divulgar:** durante un
diagnóstico mal configurado, el colector escribió seis ciclos reales
`source_ingestion_run` 3090–3095 y sus filas vinculadas en la base compartida
`127.0.0.1:5433`, que pasó de `668/484/3/120/0` a `895/646/8/126/8`; se detuvo
inmediatamente y no se borró ni alteró ningún dato de esa base.

La batería reproducida contra esa base fue:

```sh
MADRID_PULSE_DATABASE_URL=postgresql://madrid_pulse:aud06_local@127.0.0.1:5546/madrid_pulse \
  .venv/bin/python -m unittest \
  services.collector.tests.test_collector_cycle \
  services.collector.tests.test_supervised_loop \
  apps.api.tests.test_snapshot_contract \
  apps.api.tests.test_api_contract \
  services.snapshotter.tests.test_export \
  services.snapshotter.tests.test_idempotency
```

Resultado real: **103 tests en 18,677 s, `OK`**. Incluye transacciones de
PostgreSQL reales para dedupe, snapshots, exportación Parquet e idempotencia;
los dos tests del bucle supervisado aíslan el bucle con mocks, por lo que la
caída real de PostgreSQL se ensayó además por separado (§7).

Comprobaciones adicionales ejecutadas:

- `json.load(apps/api/openapi.json) == app.openapi()` devolvió `True`; ambos
  enumeran los mismos **15 endpoints**.
- Dos GET de `/api/v1/catalog` con `If-None-Match` devolvieron 200 y 304;
  `/api/v1/snapshot` publica `Cache-Control: no-store`.
- El parser de las capturas Renfe reales de replay encontró respectivamente
  **49** `stopTimeUpdate.scheduleRelationship == "SKIPPED"` en 1532 y 1533.
  `trip_updates_to_canonical` conserva el primer `next_stop_id` que no es
  `SKIPPED`; no inventa una parada omitida.
- `EXPLAIN (ANALYZE, BUFFERS)` con 10.000 filas propias de prueba utilizó
  `trip_update_observation_trip_observed_at_idx` y
  `vehicle_position_observation_source_trip_observed_at_idx` mediante Bitmap
  Index Scan. La consulta LATERAL de salud utilizó
  `source_ingestion_run_feed_started_at_idx` como Index Only Scan para sus 50
  últimas filas por feed.

## Hallazgos

### AUD06-P1-001 — Snapshot internamente inconsistente bajo commit concurrente

- **Identificador:** `AUD06-P1-001`.
- **Componente:** `apps/api/snapshot.py::build_snapshot`,
  `apps/api/db.py::{latest_vehicle_histories, revision_marker}`.
- **Severidad:** **P1**.
- **Evidencia reproducible:** en la base PostGIS aislada se abrió el snapshot
  con la tabla de vehículos vacía. Después de ejecutar de verdad su primera
  consulta (`latest_vehicle_histories`), un segundo `psycopg.Connection`
  insertó y confirmó una `source_ingestion_run` y la observación
  `AUD06-RACE`. Se dejó continuar el mismo `build_snapshot()`. El resultado
  impreso fue:

  ```text
  {'vehicles_total': 0, 'revision_sequence': 74,
   'writer_committed': True, 'contains_AUD06_RACE': False}
  ```

  Una consulta posterior de la misma base confirmó `(74,
  'vehicle_positions', 1)` y `('AUD06-RACE', '1022J19502C5')`. No es un mock
  de PostgreSQL: el retardo solo coordinó dos conexiones reales en el punto
  entre consultas.
- **Archivo/símbolo/dato:** `build_snapshot()` lee, en ese orden, historiales,
  actualizaciones, salud y `max(source_ingestion_run.id)`, sin `BEGIN
  ISOLATION LEVEL REPEATABLE READ` ni un corte de revisión que limite todas las
  lecturas.
- **Riesgo:** una respuesta con secuencia nueva puede carecer de entidades ya
  comprometidas en esa secuencia. Un consumidor que usa correctamente
  `(revision.scope, revision.sequence)` no puede tratar la secuencia como una
  representación atómica del estado; mezclar salud/vehículos/retrasos de
  instantes distintos puede producir una UI y una caché cliente incoherentes.
- **Causa raíz:** PostgreSQL usa `READ COMMITTED` por defecto y toma snapshot
  por sentencia. La petición ejecuta varias sentencias independientes mientras
  el colector confirma ciclos en paralelo.
- **Alternativas:** (A) abrir toda la construcción dentro de una transacción
  `REPEATABLE READ`; (B) leer primero el marcador y filtrar todas las consultas
  por `ingestion_run_id <= marker.sequence`; (C) aceptar la mezcla y retirar la
  promesa semántica de revisión coherente. A o B son válidas; C contradice
  ADR-0014.
- **Recomendación:** **A+B**: capturar marcador al inicio, usar una vista
  repetible y acotar explícitamente las observaciones/carreras consideradas.
  Conservar `snapshot_id` como identidad de contenido, pero nunca como orden.
- **Prueba de cierre:** regresión con dos conexiones reales: insertar entre la
  primera lectura y el marcador debe dar o bien una respuesta completamente
  anterior (`sequence` anterior, sin vehículo) o bien completamente posterior
  (secuencia y vehículo nuevos), nunca la combinación reproducida.

### AUD06-P2-001 — La alerta se filtra por estación pero pierde esa asociación al persistirse

- **Identificador:** `AUD06-P2-001`.
- **Componente:** `services.collector.collector::_persist_alerts`,
  `services.collector.db::insert_service_alert`, tabla `service_alert`.
- **Severidad:** **P2**.
- **Evidencia reproducible:** el test de integración real
  `StationAlertPersistenceTests.test_station_alert_without_route_id_is_persisted_with_madrid_stop_catalog`
  pasó contra Postgres y prueba que `stopId=60104` basta para aceptar el aviso.
  La observación canónica conserva `affected_stop_ids`, pero el `INSERT` y el
  esquema persisten solo `affected_route_ids` y `nucleo_prefixes`; no existe
  columna equivalente para las estaciones.
- **Archivo/símbolo/dato:** `packages/contracts/normalize.py::alerts_to_canonical`,
  `services/collector/collector.py:251-271`,
  `services/collector/db.py::insert_service_alert`,
  `infra/migrations/0001_init.up.sql::service_alert`.
- **Riesgo:** un aviso de estación se conserva como aviso de Madrid, pero ni el
  histórico ni futuras consultas pueden saber a qué estación afectaba. Se
  pierde información de fuente que ya se usó para decidir su relevancia.
- **Causa raíz:** el modelo de persistencia de alertas no incluye
  `affected_stop_ids`.
- **Alternativas:** (A) añadir `affected_stop_ids jsonb` con el mismo contrato
  de array; (B) normalizarlo en una tabla hija; (C) conservar solo la decisión
  de pertenencia al núcleo. C es el comportamiento actual.
- **Recomendación:** **A** para conservar fielmente el payload mínimo y poder
  atribuir avisos en una futura API/tablero, con migración y contrato explícitos.
- **Prueba de cierre:** persistir un aviso exclusivamente por `stopId`, leerlo
  desde la base/API y comprobar que el array contiene `60104`, sin convertirlo
  en `route_id` ni en una alerta global fabricada.

### AUD06-P2-002 — Las FKs de viaje existen, pero la ingesta no las usa

- **Identificador:** `AUD06-P2-002`.
- **Componente:** modelo PostgreSQL de rutas/viajes/estaciones y colector.
- **Severidad:** **P2** (deuda conocida, no corrupción observada).
- **Evidencia reproducible:** `pg_constraint` devolvió 15 claves foráneas:
  `route→network`, `trip→{service_date,route}`, `trip_stop→{trip,station}` y
  observaciones→`source_ingestion_run`/`trip`. Sin embargo,
  `insert_vehicle_position_observation` e
  `insert_trip_update_observation` no incluyen `trip_id`; la propia migración
  0002 documenta que esa columna sigue sin poblarse. Las FKs estáticas son
  correctas y se aplican cuando hay valor, pero no validan el enlace operativo
  `source_trip_id`→GTFS en la tabla caliente.
- **Archivo/símbolo/dato:** `infra/migrations/0001_init.up.sql`,
  `infra/migrations/0002_api_batch_indexes.up.sql`,
  `services/collector/db.py`.
- **Riesgo:** una consulta SQL que asuma `trip_id` poblado obtiene ausencia,
  no una infracción; la integridad de la identidad en vivo depende de la
  resolución en memoria de `Topology`. API y snapshotter ya siguen esa vía,
  por eso no elevo el caso a P1.
- **Causa raíz:** el feed en vivo llega antes de la conciliación con GTFS y el
  alcance eligió resolverlo en memoria.
- **Alternativas:** (A) materializar el enlace durante ingesta; (B) mantener
  resolución en memoria y declarar `trip_id` como campo de integración futura;
  (C) eliminar la FK nullable. B es la decisión actual documentada.
- **Recomendación:** **B** a corto plazo, pero añadir una métrica de porcentaje
  resoluble y no construir consultas nuevas sobre `trip_id` hasta materializarlo.
- **Prueba de cierre:** si se adopta A, exigir `trip_id IS NOT NULL` para cada
  observación cuyo `source_trip_id` exista en la versión GTFS del día; si se
  mantiene B, exigir que el endpoint no haga ningún JOIN SQL por `trip_id`.

### AUD06-DESCARTADO-001 — `SKIPPED` no se convierte en una omisión fabricada

- **Identificador:** `AUD06-DESCARTADO-001`.
- **Componente:** parsing GTFS-RT y tablero de estación.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** las dos capturas reales del replay contienen 49
  actualizaciones `SKIPPED` cada una. La normalización selecciona el primer
  `stopId` no `SKIPPED`; `BOARD_LIMITATIONS` declara expresamente que no se
  persiste evidencia por parada y que el tablero no afirma que una parada
  concreta fue omitida. La suite de 103 pruebas incluye los contratos de
  `next_stop_id` y el tablero.
- **Archivo/símbolo/dato:** `packages/contracts/normalize.py:60-72`,
  `apps/api/snapshot.py:82-91,788-854`.
- **Riesgo auditado:** que el sistema marcara una estación como saltada a partir
  de una relación de viaje, o que transformase ausencia en `SKIPPED`.
- **Causa raíz:** no aplica; la limitación se conserva y se publica.
- **Alternativas:** inferir una omisión por parada (no aceptable sin dato) o
  guardar todas las `stopTimeUpdate` reales (mejora futura).
- **Recomendación:** mantener la redacción actual; si se necesita detalle por
  parada, almacenar el campo de fuente antes de cambiar la UI.
- **Prueba de cierre:** ya satisfecha para las fixtures 1532/1533; repetirla
  con cada nueva forma observada del feed.

### AUD06-DESCARTADO-002 — Índices de 0002, OpenAPI y políticas de caché coinciden con lo declarado

- **Identificador:** `AUD06-DESCARTADO-002`.
- **Componente:** `0002_api_batch_indexes`, FastAPI/OpenAPI y endpoints
  `/catalog`/`/snapshot`.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** los tres planes reales usan los tres índices
  nuevos (§2); `app.openapi()` es idéntico byte-estructuralmente al JSON
  congelado, ambos con 15 paths; GET catálogo respondió 304 con ETag, y
  snapshot respondió `Cache-Control: no-store`.
- **Archivo/símbolo/dato:** `infra/migrations/0002_api_batch_indexes.up.sql`,
  `apps/api/main.py::{catalog,live_snapshot}`, `apps/api/openapi.json`.
- **Riesgo auditado:** regresión N+1/Seq Scan, divergencia de contrato o
  cachear un estado operativo viejo.
- **Causa raíz:** no aplica; no se reprodujo divergencia.
- **Alternativas/recomendación:** conservar el test de igualdad OpenAPI y los
  `EXPLAIN` de regresión con una cardinalidad representativa; los planes de
  este informe son una evidencia de elegibilidad de índice, no un benchmark de
  carga de producción.
- **Prueba de cierre:** satisfecha en la base desechable.

### AUD06-NO-VERIFICADO-001 — 823 s de supervisión no valida operación 24/7

- **Identificador:** `AUD06-NO-VERIFICADO-001`.
- **Componente:** operación prolongada, coste y recuperación.
- **Severidad:** **NO VERIFICADO** como afirmación de estabilidad 24/7.
- **Evidencia reproducible:** `mp-021-coste-colector-continuo.md` mide 21
  ciclos/823,2 s (13 min 43 s) y correctamente los llama una ventana local, no
  24/7. En esta auditoría, contra el contenedor propio, se hizo `docker restart
  aud06-postgis` con el supervisor y el colector reales: éste terminó con
  código 75 tras 27 s, el supervisor esperó 5 s, abrió una conexión nueva y
  las ejecuciones pasaron de 3.007 a 3.016 (dos ciclos completos posteriores).
- **Archivo/símbolo/dato:** `services/collector/__main__.py`,
  `infra/operate/supervise-collector.sh`,
  `docs/evidence/mp-021-coste-colector-continuo.md`.
- **Riesgo:** una ráfaga corta y un único reinicio no detectan fugas lentas de
  memoria/descriptores, acumulación de conexiones o transacciones, errores
  repetidos con backoff máximo, renovaciones TLS/DNS, particiones de red,
  agotamiento de disco/retención, cambios de feed ni drift de reloj/NTP/DST.
  El RSS de 18,6 MB y ≈19 MB/día son medidas/proyecciones útiles, no una
  demostración de estabilidad durante días.
- **Causa raíz:** no es un defecto de código probado; falta el host persistente
  y la ventana de varios días que definen el estado "24/7 verificado".
- **Alternativas:** (A) mantener la denominación honesta de operación local
  supervisada; (B) llamar 24/7 a la ráfaga; (C) contratar/autorizar un host y
  medir durante varios días. B queda descartada.
- **Recomendación:** **A** hasta que el propietario autorice C. Instrumentar
  uptime, reinicios, lag de poll, edad de fuente, RSS/FD, espacio libre y
  resultado del archivo; fijar un SLO y conservar evidencia continua de al
  menos 24 h (preferiblemente 72 h) antes de promover la afirmación.
- **Prueba de cierre:** una ejecución persistente autorizada con métricas y
  alertas, sin huecos no explicados y con recuperación ensayada ante al menos
  pérdida de BD/red, que cubra el umbral declarado. No se satisface con 823 s.

## Histórico e integridad de exportación

Los tests reales de `snapshotter` que pasaron incluyen doble exportación
byte-idéntica, preservación de día existente si la hot table queda vacía, y los
dos puntos de caída del intercambio `.quarantine/` + doble `rename`. El log de
prueba mostró tanto «restaurado ... desde la cuarentena» como «descartada la
cuarentena sobrante». Esto sostiene idempotencia y recuperación del archivo;
no convierte la proyección de **≈19 MB/día** (199.989 B de una ventana de
823,2 s, extrapolados por MP-021) en volumen diario observado.

## Límites explícitos

- No se ejecutó una ventana propia de 24/72 h: hacerlo requeriría un host
  persistente y la autorización de coste/licencia que el repositorio reserva al
  propietario.
- Los planes de índice se obtuvieron sobre cardinalidad sintética aislada;
  prueban el acceso correcto, no latencia p95 bajo tráfico público.
- La API no persiste una coordenada renderizada ni trata `snapshot_id` como
  orden; los tests de caducidad confirman que, al detener la ingesta y agotar
  horizonte, las posiciones quedan `stale_frozen` y no rejuvenecidas.

## Revisión independiente (contexto nuevo) — 2026-11-23

**Revisor:** Claude (Sonnet 5) · contexto nuevo, sin memoria de la ejecución de Codex.
**Entorno:** contenedor desechable propio `aud06-review-postgis`,
`postgis/postgis:17-3.5`, publicado en `127.0.0.1:5799` (nunca `127.0.0.1:5433`,
confirmado por `grep` del DSN antes de cada ejecución). `0001_init.up.sql` y
`0002_api_batch_indexes.up.sql` aplicados desde cero. Contenedor eliminado al
cerrar la revisión. **Alcance global:** el revisor no tocó la base compartida,
pero la ejecución original de AUD-06 sí tuvo el incidente divulgado arriba:
los runs 3090–3095 llevaron sus recuentos de `668/484/3/120/0` a
`895/646/8/126/8` en `127.0.0.1:5433`, sin posterior borrado o alteración.

**Veredicto: APPROVED.** Los cuatro puntos del encargo se reprodujeron de
forma independiente y el informe de Codex resultó preciso en cada uno:

1. **AUD06-P1-001 (race de `build_snapshot`).** Reproducido con un guion
   propio (no el de Codex, que no quedó en el repo): se monkeypatcheó
   `apps.api.db.latest_vehicle_histories` para insertar el punto de carrera
   exacto que describe el informe -- entre la lectura de vehículos (ya vacía)
   y la lectura del marcador de revisión -- y una segunda conexión real de
   `psycopg` confirmó un ciclo de ingesta completo en ese hueco. Resultado
   propio: `{'vehicles_total': 0, 'revision_sequence': 1,
   'contains_race_vehicle': False}` mientras una tercera conexión de
   verificación confirmaba `max(source_ingestion_run.id) == 1` y el vehículo
   de la carrera persistido. Confirma exactamente el mecanismo descrito:
   `psycopg.connect()` sin aislamiento explícito deja la transacción de
   lectura en `READ COMMITTED`, con snapshot nuevo por sentencia, así que
   `revision_marker()` (la última consulta) puede ver un commit posterior a
   `latest_vehicle_histories()` (la primera). La causa raíz, el riesgo y las
   alternativas A/B/C del informe son correctos.
2. **Los 103 tests.** Confirmado el conteo y el resultado `OK`. Primera
   ejecución propia: 3 fallos -- pero por contaminación de **mi propia**
   sonda de carrera (el `INSERT` de verificación quedó confirmado con
   `autocommit=True` en la misma base). Tras `TRUNCATE ... RESTART IDENTITY
   CASCADE` sobre las tablas afectadas, segunda ejecución limpia: `Ran 103
   tests in 28.115s` / `OK (skipped=4)`. El conteo exacto, el resultado `OK`
   y los 4 `skipped` coinciden con lo declarado por Codex; el tiempo total
   difiere (18,7 s vs 28,1 s) pero es variación de máquina/carga, no una
   discrepancia de resultado.
3. **Recuperación del supervisor tras reinicio de PostgreSQL.** Reproducido
   con el supervisor y el colector reales (`infra/operate/supervise-collector.sh`
   + `python -m services.collector`) contra feeds GTFS-RT de Renfe en vivo y
   mi base desechable (`COLLECTOR_POLL_INTERVAL_SECONDS=5`). Tras
   `docker restart aud06-review-postgis` con el colector en marcha: el
   proceso terminó con código **75** (`EXIT_DATABASE_LOST`) a los 20 s de
   iniciado el reinicio; el supervisor registró el código, esperó exactamente
   **5 s** de backoff y relanzó el colector, que abrió una conexión nueva y
   continuó ingiriendo con éxito (`run_id` siguió avanzando de forma
   contigua tras el reinicio). Coincide con la afirmación de Codex
   (código 75, backoff de 5 s, conexión nueva, ciclos posteriores
   completos) y con el mecanismo documentado en el docstring de
   `services/collector/__main__.py`.
4. **Hallazgos P2.** Ambos confirmados por inspección directa de código y
   esquema, sin necesidad de PostgreSQL:
   - `AUD06-P2-001`: `ServiceAlert.affected_stop_ids` existe en el modelo
     canónico (`packages/contracts/canonical.py:122`) y se usa para decidir
     relevancia de núcleo (`services/collector/collector.py:255`), pero
     `service_alert` (`infra/migrations/0001_init.up.sql:127-140`) solo
     tiene columnas `affected_route_ids`/`nucleo_prefixes`; `INSERT INTO
     service_alert` (`services/collector/db.py:171-196`) no incluye ninguna
     columna de estaciones. Confirmado.
   - `AUD06-P2-002`: `vehicle_position_observation.trip_id` y
     `trip_update_observation.trip_id` son FKs nullable reales hacia
     `trip(id)` (`infra/migrations/0001_init.up.sql:83-84,111-112`), y el
     comentario de la migración 0002 documenta explícitamente que
     `trip_id` sigue sin poblarse. `insert_vehicle_position_observation` e
     `insert_trip_update_observation` (`services/collector/db.py`) en
     efecto no incluyen `trip_id` en su `INSERT`. Confirmado.
5. **El límite "823 s no prueba 24/7".** No se intentó una ventana larga
   propia (fuera de alcance de esta revisión y del mismo encargo de Codex);
   se verificó que el informe etiqueta correctamente esa cifra como no
   representativa de operación continua y no la usa para sostener ninguna
   afirmación de estabilidad -- juicio correcto, no una omisión.

**Nota metodológica:** el primer intento de reproducir el punto 2 dio tres
fallos reales causados por mi propio script de la prueba 1 (que confirmó una
fila con `autocommit=True` sobre la base desechable). Antes de atribuir esa
discrepancia al informe de Codex, se limpió la base y se repitió la
ejecución completa, que dio `OK`. Se señala explícitamente porque un revisor
menos cuidadoso habría reportado un falso `CHANGES_REQUESTED` por
contaminación propia de la base, no por un defecto real del informe
auditado.

No se han encontrado afirmaciones no verificables, cifras infladas ni
razonamiento incorrecto en `BACKEND_OPERATIONS_AUDIT.md`. No se ha modificado
código de producto durante esta revisión.
