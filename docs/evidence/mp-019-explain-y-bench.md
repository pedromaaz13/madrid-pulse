# MP-019 — `EXPLAIN` y medición p50/p95 (evidencia ejecutada)

Todas las cifras de este documento son **medidas**, no presupuestos ni
objetivos. Donde el planificador de PostgreSQL elige un plan distinto del
esperado se dice expresamente, en vez de presentar el índice como si se usara.

## Equipo y dataset

| Dimensión | Valor real usado |
|---|---|
| Equipo | Apple M1, 8 GB RAM, macOS 26.6.2 (arm64) |
| Python | 3.12.3, `venv` local con `requirements.txt` del repositorio |
| PostgreSQL | 17.5 (imagen `postgis/postgis:17-3.5`, amd64 emulado sobre arm64) |
| Base de desarrollo | contenedor `madrid-pulse-postgres-1`, `127.0.0.1:5433`; recuentos `668 / 484 / 3 / 120 / 0` (`vehicle_position_observation` / `trip_update_observation` / `service_alert` / `source_ingestion_run` / `data_quality_event`) |
| Dataset A (catálogo) | fixture GTFS reducida versionada `tests/fixtures/gtfs_c5_real` (C5, 5 `route_id`, 23 paradas, 15 trips — DEC-023) |
| Dataset B (catálogo) | GTFS completo congelado del kit (`data/hito-03/replay/fomento_transit.zip`, `sha256:c5b40823…`, fuera de Git): núcleo Madrid completo, **42 `route_id` / 12 líneas / 95 paradas / 36 097 trips / 103 patrones** |
| Geometría | fixtures OSM reales de MP-011/MP-018 (`osm_c5_real`, `osm_c4_real`): 28 patrones `validated`, 3 `partial`, 72 `pending` |
| Medición | en proceso con `TestClient` (`apps/api/tools/bench_snapshot.py`), 60 iteraciones (dataset A) y 40 (dataset B) |

La medición en proceso **excluye** red y servidor ASGI a propósito: una cifra
que las incluya depende del host y no sirve para detectar una regresión del
backend. Reproducible con:

```sh
MADRID_PULSE_GTFS_SOURCE="$PWD/tests/fixtures/gtfs_c5_real" \
  .venv/bin/python -m apps.api.tools.bench_snapshot --iterations 60 --at 2026-11-19T05:20:00Z
MADRID_PULSE_GTFS_SOURCE="$PWD/data/hito-03/replay/fomento_transit.zip" MADRID_PULSE_SHORT_NAME= \
  .venv/bin/python -m apps.api.tools.bench_snapshot --iterations 40 --at 2026-11-20T05:20:00Z --reuse-connection
```

## 1. `EXPLAIN (ANALYZE, BUFFERS)` de las consultas por lote

### 1.1 `latest_trip_updates` — la consulta que elimina el N+1

Antes de la migración `0002` (`trip_update_observation` solo tenía su PK y el
`UNIQUE (ingestion_run_id, payload_hash)`):

```text
 Unique (actual rows=0 loops=1)
   Buffers: shared hit=20
   ->  Sort (actual rows=0 loops=1)
         Sort Key: source_trip_id, observed_at DESC, id DESC
         ->  Seq Scan on trip_update_observation (actual rows=0 loops=1)
               Filter: ((source_trip_id = ANY (...)) AND (observed_at >= ...))
               Rows Removed by Filter: 484
               Buffers: shared hit=11
 Execution Time: 2.417 ms
```

Después (`trip_update_observation_trip_observed_at_idx`):

```text
 Result (actual rows=0 loops=1)
   Buffers: shared hit=1 read=3
   ->  Unique (actual rows=0 loops=1)
         ->  Index Scan using trip_update_observation_trip_observed_at_idx
               on trip_update_observation (actual rows=0 loops=1)
               Index Cond: ((source_trip_id = ANY (...)) AND (observed_at >= ...))
 Execution Time: 2.617 ms
```

`Seq Scan` → `Index Scan` y 20 → 4 buffers. El tiempo absoluto no mejora porque
la tabla cabe en 11 páginas; lo que cambia es que el coste deja de crecer con
el histórico. **Esta consulta sustituye a 24 consultas individuales** con el
soak de MP-007 (una por vehículo) y a una por circulación en operación real.

### 1.2 `latest_vehicle_histories`

```text
 Incremental Sort (actual rows=48 loops=1)
   ->  WindowAgg (actual rows=48 loops=1)
         Run Condition: (row_number() OVER (?) <= 2)
         ->  Sort (actual rows=668 loops=1)
               ->  Hash Join (actual rows=668 loops=1)
                     ->  Seq Scan on vehicle_position_observation v (actual rows=668)
                     ->  Hash (actual rows=120) -> Seq Scan on source_ingestion_run r
 Execution Time: 7.356 ms
```

**Limitación declarada, no disimulada:** esta consulta recorre la tabla
caliente completa. No existe una dimensión de vehículos contra la que hacer un
`LATERAL` acotado, así que "las dos últimas observaciones de cada vehículo
visto" exige recorrer el histórico retenido. Es aceptable porque ADR-0003 fija
retención corta en el almacenamiento caliente, y ahora el filtro `rank <= 2`
se aplica **en SQL** (antes se traían todas las filas a Python). Si la
retención creciera, la solución correcta es acotar por ventana o materializar
el último estado por vehículo, no un índice.

### 1.3 `recent_ingestion_runs` — `LATERAL` acotado por feed

La versión anterior rankeaba la tabla entera con una ventana y descartaba el
exceso en Python. La nueva usa `LATERAL ... LIMIT`:

```text
 Nested Loop (actual rows=120 loops=1)
   Buffers: shared hit=15
   ->  HashAggregate (actual rows=3) -> Seq Scan on source_ingestion_run
   ->  Limit (actual rows=40 loops=3) -> Sort -> Seq Scan on source_ingestion_run run
```

Con `enable_seqscan = off` se comprueba que el índice nuevo **sí** cubre la
forma de la consulta (lo que importa a volumen real):

```text
 Nested Loop (actual rows=120 loops=1)
   Buffers: shared hit=6
   ->  Unique -> Index Only Scan using source_ingestion_run_feed_started_at_idx
                   (actual rows=120, Heap Fetches: 0)
   ->  Limit (actual rows=40 loops=3)
         ->  Index Only Scan using source_ingestion_run_feed_started_at_idx
               Index Cond: (feed_name = source_ingestion_run.feed_name)
               Heap Fetches: 0
```

15 → 6 buffers, `Index Only Scan` sin accesos al heap. Con 120 filas en 3
páginas el planificador prefiere `Seq Scan` y **hace bien**: no se presenta el
índice como si se usara hoy.

### 1.4 `vehicles_for_trips` (tablero)

Con el plan elegido a este volumen:

```text
 Unique (actual rows=2 loops=1)
   ->  Sort (actual rows=63) -> Seq Scan on vehicle_position_observation
         Filter: (source_trip_id = ANY (...))
         Rows Removed by Filter: 605
```

Con `enable_seqscan = off`, usando el índice nuevo:

```text
 Unique (actual rows=2 loops=1)
   ->  Sort (actual rows=63)
         ->  Bitmap Heap Scan on vehicle_position_observation
               Recheck Cond: (source_trip_id = ANY (...))
               Heap Blocks: exact=21
```

Hallazgo real de esta tarea: existía ya un índice de nombre parecido
(`vehicle_position_observation_trip_observed_at_idx`) pero sobre la clave ajena
`trip_id` (bigint), que **el colector no puebla**; no sirve para consultar por
`source_trip_id`. La migración `0002` añade el índice que la API necesita de
verdad.

## 2. p50/p95 medidos

### 2.1 Dataset A — fixture reducida C5, 60 iteraciones

Conexión por petición (comportamiento actual de la API):

| Endpoint | p50 (ms) | p95 (ms) | Bytes |
|---|---:|---:|---:|
| `GET /api/v1/catalog` | 0,65 | 1,79 | 79 279 |
| `GET /api/v1/snapshot` | 98,70 | 130,74 | 36 758 |
| `GET /api/v1/stations/18000/board` | 84,56 | 101,27 | 2 925 |
| `GET /api/v1/live/vehicles` | 82,68 | 99,15 | 7 866 |
| `GET /api/v1/health` | 68,91 | 76,10 | 749 |
| `GET /api/v1/catalog` con `If-None-Match` → `304` | 0,45 | 0,56 | 0 |

Conexión reutilizada (aísla el coste del código de la API):

| Endpoint | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `GET /api/v1/catalog` | 0,41 | 0,52 |
| `GET /api/v1/snapshot` | 8,73 | 17,76 |
| `GET /api/v1/stations/18000/board` | 4,83 | 6,71 |
| `GET /api/v1/live/vehicles` | 4,38 | 5,36 |
| `GET /api/v1/health` | 3,71 | 8,39 |

### 2.2 Dataset B — núcleo Madrid completo (42 rutas / 12 líneas / 103 patrones), 40 iteraciones

Reloj a las `05:20` locales: un único día de servicio candidato.

| Endpoint | p50 conexión/petición | p95 | p50 conexión reutilizada | p95 | Bytes |
|---|---:|---:|---:|---:|---:|
| `GET /api/v1/catalog` | 0,65 | 1,79 | 0,54 | 2,18 | 361 362 |
| `GET /api/v1/snapshot` | 98,73 | 114,23 | 8,42 | 23,32 | 35 526 |
| `GET /api/v1/stations/18000/board` | 93,44 | 119,44 | 7,96 | 10,39 | 22 301 |
| `GET /api/v1/live/vehicles` | 82,40 | 94,76 | 4,95 | 7,04 | 7 866 |
| `GET /api/v1/health` | 69,66 | 82,39 | 3,41 | 6,87 | 749 |

### 2.3 Dataset B a las `00:02` locales — peor caso: dos días de servicio candidatos

Tras la corrección del segundo hallazgo de la revisión, dentro de la ventana de
horas extendidas el tablero cruza el día de servicio anterior **y** el civil, y
la fecha de servicio se resuelve por circulación. Medido con conexión
reutilizada, 40 iteraciones, estación `17000`:

| Endpoint | p50 (ms) | p95 (ms) | Bytes |
|---|---:|---:|---:|
| `GET /api/v1/catalog` | 0,46 | 0,62 | 361 362 |
| `GET /api/v1/snapshot` | 9,62 | 13,81 | 35 526 |
| `GET /api/v1/stations/17000/board` | 9,62 | 24,19 | 16 096 |
| `GET /api/v1/live/vehicles` | 5,68 | 12,04 | 7 866 |
| `GET /api/v1/health` | 2,81 | 3,41 | 749 |

El peor caso cuesta ~1,7 ms más de p50 en el tablero y ~1,2 ms en el snapshot.
Los índices de llamadas programadas se memoizan por fecha de servicio, así que
el coste de construir el segundo se paga una vez por día. **No se añadió
ninguna consulta**: las formas SQL no cambiaron, los planes de la sección 1
siguen vigentes y los tests de conteo de `execute` lo confirman.

El snapshot pasa de 14 patrones (C5) a 103 patrones / 12 líneas **sin cambio
medible** (8,47 → 8,59 ms de p50 con conexión reutilizada): el coste depende de
los vehículos observados y de las consultas por lote, no del tamaño del
catálogo. El tablero sube de 4,67 a 6,65 ms porque el índice de llamadas
programadas del día de servicio es mayor; se construye **una vez** por fecha de
servicio y se memoiza, y ese coste de construcción es el que explica el p95 de
18,07 ms (primera iteración).

## 3. Dos hallazgos de rendimiento reales de esta tarea

### 3.1 El catálogo se reserializaba en cada petición (corregido)

`/api/v1/catalog` no consulta PostgreSQL, y aun así medía **p50 = 122,67 ms /
p95 = 150,60 ms** con la fixture C5 (79 KB de geometría) — idéntico con
conexión reutilizada, lo que localizó la causa: validar y serializar el mismo
payload inmutable en cada petición. Memoizarlo por `catalog_version`
(`LoadedNetwork._catalog_json`) lo baja a **p50 = 0,40 ms**, ~300×. No puede
servir un dato viejo rotulado como nuevo: si `catalog_version` cambiara, el
proceso habría cargado otro catálogo.

### 3.2 El coste dominante restante es abrir la conexión, no la consulta (abierto)

Con conexión por petición, `GET /api/v1/health` —749 bytes y una sola
consulta— mide 68,91 ms de p50; con conexión reutilizada, 2,45 ms. Es decir
**~66 ms de cada petición son establecer la conexión PostgreSQL**, no trabajo
útil: `apps/api/main.py::get_connection` abre y cierra una conexión por
petición desde MP-013.

Esto **no se corrige en MP-019** y se deja registrado como pendiente explícito,
no como deuda silenciosa: la solución estándar (`psycopg_pool`) es una
dependencia nueva y, por tanto, una decisión del propietario con su DEC
correspondiente (mismo criterio que DEC-019/DEC-030). Las cifras de este
documento publican ambas columnas para que la decisión se tome sobre datos
medidos y para que la comparación futura sea posible.

## 4. Ausencia de N+1, probada además por conteo de consultas

`apps/api/tests/test_snapshot_contract.py` envuelve la conexión real en un
contador de `execute` y comprueba que el número de consultas es **idéntico**
con 6 y con 18 vehículos (`test_snapshot_does_not_query_once_per_vehicle`,
`<= 8` consultas), que `/api/v1/live/vehicles` también perdió su N+1
(`<= 3` consultas, constantes entre 4 y 14 vehículos) y que el tablero no
consulta por fila (`test_board_does_not_query_once_per_entry`). El lote
devuelve además exactamente la misma fila que la consulta unitaria, incluido el
desempate `id DESC` de ADR-0010
(`test_batch_trip_updates_return_the_same_row_as_the_single_query`).
