# DATA_CONTRACTS.md

Estado: **parcialmente implementada en MP-013** (`apps/api/`, OpenAPI en `apps/api/openapi.json`). Ningún ejemplo de este documento es una respuesta real de Renfe, CRTM ni de ningún proyecto de terceros — **todos los JSON de ejemplo son sintéticos** y están marcados como tales; reflejan la forma del contrato, no un payload observado. Los endpoints `live`/`lines`/`stations`/`health` están implementados y probados contra datos reales (PostgreSQL + GTFS/OSM). Los endpoints `history`/`metrics` siguen como propuesta — ver "Endpoints diferidos" más abajo.

## Discrepancia a reconciliar (antes de MP-013)

`deep-research-report.md` propone:

```text
GET /api/v1/live/vehicles
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines
GET /api/v1/lines/{line_id}
GET /api/v1/stations/{station_id}
GET /api/v1/history/lines/{line_id}
GET /api/v1/history/trips/{trip_id}
GET /api/v1/quality/feeds
GET /api/v1/metrics/lines/{line_id}
GET /api/v1/metrics/stations/{station_id}
```

`MADRID_PULSE_BRIEF_INICIAL.md` propone un subconjunto distinto:

```text
GET /api/v1/health
GET /api/v1/live/trains
GET /api/v1/trains/{train_id}
GET /api/v1/stations
GET /api/v1/history/trains
```

**Decisión de trabajo confirmada en MP-013 (ADR-0005):** la nomenclatura `vehicles` del informe completo (más alineada con GTFS-RT, donde la entidad es el vehículo, no "el tren" como concepto de negocio) y la fusión de `/api/v1/health` del brief con `/api/v1/quality/feeds` del informe completo, ya que cubren el mismo propósito de observabilidad de fuente.

## Endpoints implementados (MP-013)

```text
GET /api/v1/health                     -- salud real por feed (source_ingestion_run)
GET /api/v1/live/vehicles               -- todos los vehículos vistos, map-matched vía MP-012
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines
GET /api/v1/lines/{line_id}
GET /api/v1/stations
GET /api/v1/stations/{station_id}
```

## Endpoints diferidos (propuesta, no implementada)

```text
GET /api/v1/history/lines/{line_id}
GET /api/v1/history/trips/{trip_id}
GET /api/v1/metrics/lines/{line_id}
GET /api/v1/metrics/stations/{station_id}
```

`daily_line_metrics`/`station_daily_metrics` siguen vacías: MP-009 las difirió explícitamente (DEC-021) y ninguna tarea posterior las ha poblado. Calcularlas de verdad —agregados reales sobre datos reales, nunca inventados— es un alcance propio que MP-013 no asumió; queda documentado para MP-015/Hito 3, no omitido en silencio (ver `apps/api/README.md` y ADR-0005).

Todos bajo versionado explícito `/api/v1/`; un cambio incompatible de contrato requiere `/api/v2/`, nunca una mutación silenciosa de `/v1/`.

## Ejemplo sintético — vehículo en vivo

**Este ejemplo es sintético, generado para ilustrar el contrato. No representa una respuesta real de Renfe ni de Madrid Pulse.**

```json
{
  "vehicle_id": "renfe:cercanias-madrid:SYNTHETIC-0001",
  "trip_id": "SYNTHETIC-TRIP-0001",
  "line": "C5",
  "position": {
    "lat": 40.3501,
    "lon": -3.8312,
    "mode": "observed",
    "confidence": 1.0
  },
  "delay": {
    "seconds": 184,
    "coverage": "reported"
  },
  "observation": {
    "reported_at": "2026-11-18T09:00:00Z",
    "received_at": "2026-11-18T09:00:03Z",
    "age_s": 12
  },
  "quality": {
    "stale": false,
    "flags": []
  }
}
```

### Campos obligatorios de frescura/calidad

Toda respuesta de vehículo en vivo **debe** incluir:

- `position.mode`: uno de `observed | estimated | stale | scheduled` (ver `docs/DATA_QUALITY.md`).
- `position.confidence`: `0.0`–`1.0`, decreciente con la edad del dato.
- `observation.age_s`: segundos desde la última observación real.
- `delay.coverage`: `reported | missing` — nunca se omite ni se sustituye por `0` cuando no hay dato.
- `quality.flags`: lista de flags activos (puede estar vacía, nunca ausente).

### Ejemplo sintético — salud de feed (`/api/v1/health`)

```json
{
  "feeds": [
    {
      "feed_name": "vehicle_positions",
      "status": "ok",
      "source_timestamp": "2026-11-18T09:00:00Z",
      "data_age_s": 8,
      "unchanged_for_s": 0,
      "entities": 42,
      "rejected": 0
    },
    {
      "feed_name": "trip_updates",
      "status": "stale",
      "source_timestamp": "2026-11-18T08:58:10Z",
      "data_age_s": 118,
      "unchanged_for_s": 118,
      "entities": 0,
      "rejected": 0
    }
  ]
}
```

Este patrón de observabilidad por feed está inspirado conceptualmente en el modelo público de Valfiguer (`ok/stale/data_age_s/unchanged_for_s`), **reimplementado de forma independiente** — no se consume su API ni se copia su código.

### Ejemplo sintético — métricas de línea con cobertura explícita

```json
{
  "line": "C5",
  "service_date": "2026-11-17",
  "trips_scheduled": 120,
  "trips_with_delay_data": 94,
  "delay_coverage_pct": 78.3,
  "on_time_pct_of_covered": 87.2,
  "disclaimer": "on_time_pct_of_covered se calcula solo sobre los viajes con dato de retraso disponible (delay_coverage_pct)."
}
```

**Regla no negociable:** nunca se publica un porcentaje de puntualidad sin su `coverage` asociado en el mismo payload, para evitar que "87% de puntualidad" se interprete como representativo de todo el servicio cuando solo cubre el 78% de los viajes.

## Versionado y metadatos de snapshot

Cuando exista publicación de snapshots en CDN (post-MP-007), cada snapshot debe incluir:

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-11-18T09:00:10Z",
  "source_feed_runs": ["<ingestion_run_id>", "..."],
  "data": { "...": "..." }
}
```

`schema_version` sigue versionado semántico independiente del versionado de la URL de la API (`/v1/`), porque un snapshot estático puede evolucionar su esquema interno sin requerir un cambio de ruta de API.
