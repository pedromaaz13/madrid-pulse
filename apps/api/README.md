# apps/api — FastAPI v1 (MP-013, ampliada en MP-019)

API propia de Madrid Pulse bajo `/api/v1/*`, nunca un passthrough de Renfe/
CRTM (`docs/ARCHITECTURE.md`). Consume `packages/contracts`, `packages/gtfs`,
`packages/geo` y `packages/movement` ya construidos; no reimplementa
resolución de rutas, geometría ni el motor de movimiento.

## Endpoints implementados

```text
GET /api/v1/health                      -- salud real por feed (source_ingestion_run)
GET /api/v1/live/vehicles               -- todos los vehículos vistos, map-matched vía MP-012
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines                       -- agrupación (network_id, short_name) de packages.gtfs
GET /api/v1/lines/{line_id}
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/catalog                     -- MP-019: catálogo cacheable (ETag/304)
GET /api/v1/snapshot                    -- MP-019: snapshot operativo ligero (no-store)
GET /api/v1/stations/{station_id}/board -- MP-019: tablero por servicios+calendario+RT
```

Desde MP-014, cada `LineOut` incluye `geometry` nullable (DEC-031): los
`Corridor.segments` OSM reales permanecen separados para no puentear huecos y
las estaciones se proyectan con `Corridor.project_station` y se ordenan por
longitud de arco. La asociación se hace por el `network_id`/`short_name`
configurado; para cualquier línea sin corredor cargado se devuelve `null`,
nunca una geometría inventada conectando paradas.

OpenAPI generado y congelado en `apps/api/openapi.json` (regenerar con
`python -c "import json; from apps.api.main import app; json.dump(app.openapi(), open('apps/api/openapi.json','w'), indent=2, sort_keys=True)"`).

## Resolución genérica, sin literales de línea (ADR-0011)

`network_id`/`short_name` son configuración (`ApiConfig`, variables
`MADRID_PULSE_NETWORK_ID`/`MADRID_PULSE_SHORT_NAME`), nunca un literal `"C5"`
en la lógica. `/api/v1/lines` refleja lo que la topología cargada resuelva,
sea cual sea.

## Hallazgo real: la mayoría de los vehículos del soak no son C5

El colector de MP-007 filtra por núcleo (Madrid), no por línea (DEC-020). De
los 24 vehículos distintos del soak real, solo 4 pertenecen a C5
(`10T0017C5`/`10T0018C5`); 19 son otras líneas del núcleo Madrid (C1, C2, C3,
C4, C4a, C4b, C8a, C8b, C10) y 1 (`SPECIAL_10_91567C2`, refuerzo) no resuelve
contra ningún `route_id`, confirmado
contra el GTFS estático completo. `/api/v1/live/vehicles` devuelve los 24,
con `route_id`/`line`/`position` en `null` para los que no resuelven contra
la topología C5 cargada -- nunca se fabrica una línea o posición. Ver test
`test_live_vehicles_never_fabricates_route_for_unresolvable_trip`.

## GTFS estático completo para operación real

Los tests usan la fixture reducida de MP-010 (15 trips representativos,
suficiente para contrato/esquema). Para que `/api/v1/live/vehicles` resuelva
los vehículos C5 reales en ejecución local, hace falta el GTFS completo:

```sh
python -m apps.api.tools.fetch_gtfs_static
export MADRID_PULSE_GTFS_SOURCE=data/gtfs_static/fomento_transit.zip
```

`data/` está en `.gitignore`: el fichero (~298 MB extraído) no se versiona,
mismo motivo que DEC-023 en MP-010.

## Modos locales explícitos (MP-016)

La API no llama «Live» a una fixture en silencio. El modo replay usa datos
congelados y el modo live exige un ZIP ajeno a `tests/fixtures/` cuya ventana
de calendario incluya la fecha actual de Madrid. Ambos publican en
`/api/v1/health` el modo, el SHA-256 del catálogo y su vigencia.

Define `MADRID_PULSE_DATABASE_URL` y `MADRID_PULSE_ENV` según la
[guía de aislamiento](../../docs/operations/DATABASE_ISOLATION.md).
`MADRID_PULSE_MODE` sigue eligiendo cómo la API interpreta su fuente y su reloj.

```sh
# Replay reproducible (fixture reducida, valor por defecto)
MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
MADRID_PULSE_GTFS_SOURCE="$PWD/tests/fixtures/gtfs_c5_real" \
.venv/bin/uvicorn apps.api.main:app --port 8000

# Live: descargar primero el ZIP oficial y comprobar que sigue vigente
.venv/bin/python -m apps.api.tools.fetch_gtfs_static
MADRID_PULSE_ENV=live MADRID_PULSE_MODE=live \
MADRID_PULSE_DATABASE_URL='postgresql://rol:contraseña@db.interna:5432/madrid_pulse' \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" \
.venv/bin/uvicorn apps.api.main:app --port 8000
```

Un arranque live con fixture, modo desconocido o catálogo vencido falla con
un diagnóstico explícito. Durante la ejecución, `/health`, `/catalog` y
`/snapshot` publican `gtfs_status` y `gtfs_status_reason` al reloj de la
petición. `MADRID_PULSE_GTFS_EXPIRING_DAYS` fija el aviso (7 días por defecto,
incluido el último día de vigencia en Madrid). El catálogo sigue accesible
cuando vence, con estado `expired`. Consulta el
[procedimiento de refresco](../../docs/operations/GTFS_STATIC_REFRESH.md).

`data_age_s` mide la edad de la cabecera publicada;
`poll_age_s`, la edad del último intento del colector. Por ello un fichero viejo
recién descargado y un colector detenido se distinguen, y los feeds
`vehicle_positions`, `trip_updates` y `alerts` conservan estados separados.

## Una sola corriente de corredor cubre ambos sentidos de C5

`MovementEngine` exige un corredor continuo por instancia (ADR-0012). Se
carga uno solo (`relation_3418150.json`, "Móstoles-El Soto → Atocha →
Humanes") porque `packages.movement.schedule.build_trip_schedule` detecta
automáticamente el sentido de cada trip comparando el orden de sus paradas
contra el corredor (`forward = projected[-1] >= projected[0]`) -- no hace
falta un corredor por sentido. Verificado con los 4 vehículos C5 reales del
soak: tanto `10T0017C5` (sentido directo) como `10T0018C5` (inverso)
resuelven posición contra el mismo corredor.

## Deliberadamente fuera de alcance de esta tarea (no silenciado)

`docs/DATA_CONTRACTS.md` proponía también `history/lines/{line_id}`,
`history/trips/{trip_id}`, `metrics/lines/{line_id}` y
`metrics/stations/{station_id}`. **Actualizado en MP-015 (DEC-033):**
`daily_line_metrics`/`station_daily_metrics` ya se calculan de verdad
(`services/snapshotter/gold.py`) -- lo que sigue sin implementarse es
únicamente estos cuatro endpoints de esta API que los expondrían; no cabían
en esta tarea sin reescribir la capa de resolución GTFS fuera de este
módulo. Quedan como pendientes explícitos para Hito 3 si el propietario lo
prioriza, documentados en `docs/DATA_CONTRACTS.md`, no omitidos en
silencio.

## MP-019: catálogo cacheable, snapshot y tablero (ADR-0014)

El contrato completo está en `docs/DATA_CONTRACTS.md`; aquí solo lo operativo.

`GET /api/v1/catalog` publica líneas, patrones, estaciones, geometría y
cobertura. La versión estática `catalog_version` deriva de `gtfs_version` y
`geometry_catalog_version`. El `ETag` incorpora también el modo, el estado
de vigencia y la versión de esquema. La API memoiza el payload serializado
por ETag y devuelve `304` si coincide el `If-None-Match` del cliente.

`GET /api/v1/snapshot` publica lo operativo con `Cache-Control: no-store`:
`raw`/`map_matched`/`rendered` separados, los cinco instantes del anexo,
`snapshot_id` de identidad de contenido **declarado no ordenable** y el bloque
`revision` monotónico solo dentro de su `scope`.

`GET /api/v1/stations/{station_id}/board` se calcula con
`scheduled_trip_instances_for_date` (calendario + excepciones + `stop_times`),
nunca por proximidad geográfica.

Snapshot, tablero, health y catálogo aceptan `?at=` **solo en modo replay**
(en `live`, `400`). Se aceptan fechas UTC entre `0001-01-04` y
`9999-12-28` inclusive. Sin `at` usan el reloj real. Snapshot y health
declaran edades `null` cuando el feed aún carece de ingestas a ese instante.

```sh
curl -s 'http://127.0.0.1:8000/api/v1/snapshot?at=2026-11-20T14:32:14Z' | jq '.counts, .revision'
curl -s 'http://127.0.0.1:8000/api/v1/stations/18000/board?at=2026-11-20T14:32:14Z' | jq '.coverage'
curl -sI 'http://127.0.0.1:8000/api/v1/catalog' | grep -i etag
```

### Toda la red del núcleo, no una línea

`MADRID_PULSE_SHORT_NAME` vacío carga el núcleo completo (con el ZIP oficial:
42 `route_id`, 12 líneas, 95 paradas, 103 patrones). Con un valor, filtra a esa
línea — es el modo que usan los tests y el piloto. El filtro sigue siendo
configuración, nunca un literal en la lógica (ADR-0011).

```sh
MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME= \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" \
  .venv/bin/uvicorn apps.api.main:app --port 8000
```

### Día de servicio tras medianoche

La fecha de servicio **no** es la fecha civil: se resuelve por circulación
(`apps.api.service.ServiceDateResolver`). Dentro de la ventana que el propio
feed justifica —su máximo `arrival`/`departure` menos 24 h; 3 180 s con el ZIP
oficial, `0.0` con un feed sin horas extendidas— se comprueba primero si el
viaje sigue perteneciendo al día anterior por su horario `24:xx`. El snapshot
publica `service_date` por circulación y el tablero por entrada, además de
`service_dates_considered`.

Sin esto, a las `00:02` un viaje real del día anterior con paradas a las
`24:00`/`24:05` se situaba 10,4 km fuera de su posición y aparecía `expired`
(ver `docs/evidence/mp-019-dst-y-horas-extendidas.md`).

El tablero deriva sus días candidatos de la **ventana completa**
(`lookback_s`/`lookahead_s`), no del instante de consulta: con `now` a secas,
una llamada `24:xx` ocurrida un minuto antes desaparecía aunque se pidieran
600 s de retrospectiva, y las primeras llamadas del día siguiente se perdían
dentro de la anticipación.

### Variables nuevas

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `MADRID_PULSE_SHORT_NAME` | `C5` | vacío = núcleo completo |
| `MADRID_PULSE_GEOMETRY_FIXTURES_ROOT` | `tests/fixtures` | raíz de las fixtures OSM versionadas de MP-011/MP-018 |
| `MADRID_PULSE_OPERATOR_DELAY_MAX_AGE_S` | `600` | más allá de esa edad el retraso del operador se publica pero **no** se aplica a la ETA (`operator_delay_expired`) |
| `MADRID_PULSE_DISPLAY_LAG_S` | `0` | retraso de presentación declarado; con dos anclas reales habilita `interpolated_between_known_anchors` |

### Medición y evidencia reproducibles

```sh
export MADRID_PULSE_ENV=replay
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse
.venv/bin/python -m apps.api.tools.bench_snapshot --iterations 60 --at 2026-11-19T05:20:00Z
.venv/bin/python -m apps.api.tools.bench_snapshot --iterations 60 --reuse-connection
```

`--reuse-connection` aísla el coste del código de la API del de abrir la
conexión. Hallazgo abierto y documentado: con conexión por petición, ~66 ms de
cada respuesta son establecer la conexión PostgreSQL
(`get_connection` abre y cierra una por petición desde MP-013). Un pool es una
dependencia nueva y por tanto decisión del propietario; las dos columnas
medidas están en `docs/evidence/mp-019-explain-y-bench.md`.

`apps.api.tools.replay_three_snapshots` reproduce los tres snapshots
(normal/parcial/congelado) sobre las capturas reales `1532`/`1533` contra un
PostgreSQL desechable; resultado en
`docs/evidence/mp-019-tres-snapshots-replay.md`.

## Pruebas

```sh
MADRID_PULSE_ENV=test \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
  .venv/bin/python -m unittest apps.api.tests.test_api_contract -v
```

Usa la fixture reducida (sin red) más PostgreSQL real para
`/api/v1/health` y `/api/v1/live/vehicles` (requiere una base marcada como
desechable en `MADRID_PULSE_DATABASE_URL`). Un test adicional (`ResolvedTripEndToEndTests`)
construye una observación sintética para un trip real de la fixture
reducida y prueba la resolución de extremo a extremo (ruta, map-matching,
motor de movimiento) sin depender del GTFS completo.

## Ejecución local

```sh
MADRID_PULSE_ENV=dev \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
  .venv/bin/uvicorn apps.api.main:app --reload --port 8000
```

Requiere una `MADRID_PULSE_DATABASE_URL` explícita y, para vehículos C5 reales,
el GTFS completo (sección anterior).
