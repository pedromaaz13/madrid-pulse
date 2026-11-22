# apps/api — FastAPI v1 (MP-013)

API propia de Madrid Pulse bajo `/api/v1/*`, nunca un passthrough de Renfe/
CRTM (`docs/ARCHITECTURE.md`). Consume `packages/contracts`, `packages/gtfs`,
`packages/geo` y `packages/movement` ya construidos; no reimplementa
resolución de rutas, geometría ni el motor de movimiento.

## Endpoints implementados

```text
GET /api/v1/health                     -- salud real por feed (source_ingestion_run)
GET /api/v1/live/vehicles              -- todos los vehículos vistos, map-matched vía MP-012
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines                      -- agrupación (network_id, short_name) de packages.gtfs
GET /api/v1/lines/{line_id}
GET /api/v1/stations
GET /api/v1/stations/{station_id}
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

```sh
# Replay reproducible (fixture reducida, valor por defecto)
MADRID_PULSE_MODE=replay \
MADRID_PULSE_GTFS_SOURCE="$PWD/tests/fixtures/gtfs_c5_real" \
.venv/bin/uvicorn apps.api.main:app --port 8000

# Live: descargar primero el ZIP oficial y comprobar que sigue vigente
.venv/bin/python -m apps.api.tools.fetch_gtfs_static
MADRID_PULSE_MODE=live \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" \
.venv/bin/uvicorn apps.api.main:app --port 8000
```

Un arranque live con fixture, modo desconocido o catálogo vencido falla con
un diagnóstico explícito. `data_age_s` mide la edad de la cabecera publicada;
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

## Pruebas

```sh
.venv/bin/python -m unittest apps.api.tests.test_api_contract -v
```

Usa la fixture reducida (sin red) más PostgreSQL real para
`/api/v1/health` y `/api/v1/live/vehicles` (requiere el contenedor
`madrid-pulse` levantado). Un test adicional (`ResolvedTripEndToEndTests`)
construye una observación sintética para un trip real de la fixture
reducida y prueba la resolución de extremo a extremo (ruta, map-matching,
motor de movimiento) sin depender del GTFS completo.

## Ejecución local

```sh
.venv/bin/uvicorn apps.api.main:app --reload --port 8000
```

Requiere PostgreSQL levantado (`docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d`)
y, para vehículos C5 reales, el GTFS completo (sección anterior).
