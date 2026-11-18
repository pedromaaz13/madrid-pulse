# DATA_MODEL.md

Estado: **propuesta candidata, no implementada**. Existen dos formulaciones del modelo en la investigación original que no son idénticas; este documento las presenta ambas explícitamente y señala la reconciliación pendiente para MP-005/MP-006, en lugar de fabricar una versión "definitiva" no verificada.

## Dos modelos candidatos

### Modelo A — relacional directo (`deep-research-report.md`)

Entidades: `network`, `route`, `station`, `service_date`, `trip`, `trip_stop`, `vehicle_observation`. Más cercano a un esquema operacional simple, enfocado en servir el estado actual y el detalle reciente.

### Modelo B — dimensional/trazabilidad de fuente (`MADRID_PULSE_BRIEF_INICIAL.md`)

Entidades: `source_ingestion_run`, `source_feed_version`, `dim_station`, `dim_route`, `dim_service_trip`, `vehicle_position_observation`, `vehicle_position_clean`, `trip_update_observation`, `service_alert`, `daily_trip_quality`, `daily_station_metrics`, `snapshot_publication`. Más cercano a un esquema con trazabilidad explícita de ingesta y separación observación cruda / observación limpia.

**Decisión pendiente (a resolver en MP-005, documentar como ADR):** el Modelo B aporta trazabilidad de fuente (`source_ingestion_run`, `source_feed_version`) y separación explícita `*_observation` vs `*_clean` que el Modelo A no tiene; el Modelo A es más simple y cercano a lo que el informe completo usa para ejemplos de índices y claves. La propuesta de trabajo es **fusionar ambos**: usar la nomenclatura de trazabilidad de fuente del Modelo B sobre la estructura relacional simple del Modelo A. Esta fusión se detalla abajo como punto de partida, pero debe confirmarse en el ADR correspondiente antes de escribir migraciones (MP-006).

## Entidades propuestas (fusión de trabajo, pendiente de ADR)

```text
network
  id PK
  code UNIQUE
  name

route (dim_route)
  id PK
  network_id FK
  source_route_id          -- route_id COMPLETO del proveedor (p. ej. "10T0047C5"), NUNCA
                           -- el route_short_name en solitario — ver ADR-0008/DEC-017: "C5"
                           -- existe también en Asturias (20T0011C5) y Andalucía (30T0009C5)
                           -- en el mismo feed nacional de Renfe (verificado en MP-003).
  short_name               -- p. ej. "C5" — puede repetirse entre núcleos distintos, NO es único
  color
  nucleo_prefix            -- prefijo numérico de 2 cifras del route_id ("10"=Madrid, "20"=Asturias,
                           -- "30"/"31"/"32"=Andalucía, etc.) — disambiguador verificado en MP-003.
  UNIQUE(network_id, source_route_id)
  -- La C5 de Madrid tiene 5 source_route_id distintos (variantes de sentido/tramo):
  -- 10T0017C5, 10T0018C5, 10T0035C5, 10T0047C5, 10T0048C5. Por la restricción UNIQUE
  -- anterior, cada uno ocupa su PROPIA fila route.id (5 filas, no 1) — la agrupación como
  -- "la misma línea C5" se hace consultando por (network_id, short_name), nunca asumiendo
  -- un único route.id por línea comercial. Ver ADR-0008 (corregido tras hallazgo de Codex
  -- en la revisión de MP-003: la redacción anterior de este comentario era contradictoria
  -- con el propio UNIQUE de arriba).

station (dim_station)
  id PK
  source_stop_id
  name
  geom geography(Point,4326)

service_date
  date PK
  gtfs_version_id FK      -- versionado GTFS, ver abajo

trip (dim_service_trip)
  id PK
  service_date
  source_trip_id
  route_id FK
  direction_id
  start_time
  UNIQUE(service_date, source_trip_id)

trip_stop
  trip_id FK
  stop_sequence
  station_id FK
  scheduled_arrival
  scheduled_departure
  PRIMARY KEY(trip_id, stop_sequence)

source_ingestion_run (feed_run)
  id PK
  feed_name                -- vehicle_positions | trip_updates | alerts | gtfs_static
  started_at timestamptz
  finished_at timestamptz
  status                   -- ok | error | partial
  entities_count
  payload_hash

vehicle_position_observation (vehicle_observation)
  id bigint PK
  observed_at timestamptz   -- timestamp reportado por la fuente
  received_at timestamptz   -- timestamp de recepción propia
  source_vehicle_id
  source_trip_id
  trip_id FK nullable       -- resuelto contra GTFS estático; nullable si no resuelve
  geom geography(Point,4326)
  current_status
  current_stop_sequence
  speed_kmh
  bearing
  quality_flags jsonb
  payload_hash
  ingestion_run_id FK

trip_update_observation
  id bigint PK
  observed_at timestamptz
  received_at timestamptz
  source_trip_id
  trip_id FK nullable
  delay_seconds nullable    -- nullable, nunca 0 por defecto cuando no hay dato
  delay_coverage            -- reported | missing
  ingestion_run_id FK

service_alert
  id PK
  source_alert_id
  effect
  cause
  header_text
  description_text
  active_period_start timestamptz
  active_period_end timestamptz nullable
  affected_routes jsonb
  ingestion_run_id FK

daily_line_metrics (daily_trip_quality + agregado por línea)
  service_date
  route_id FK
  trips_scheduled
  trips_with_delay_data
  delay_coverage_pct        -- fracción con dato disponible, nunca implícita
  on_time_pct_of_covered     -- % puntual SOLO sobre los que tienen dato
  PRIMARY KEY(service_date, route_id)

station_daily_metrics (daily_station_metrics)
  service_date
  station_id FK
  observations_count
  data_quality_events_count
  PRIMARY KEY(service_date, station_id)

data_quality_event
  id PK
  occurred_at timestamptz
  entity_type               -- vehicle_position | trip_update | alert
  entity_ref
  flag                       -- stale | implausible_speed | missing_id | duplicate_snapshot | clock_anomaly
  details jsonb
```

## Claves e identificadores

- **`trip_id` interno** se construye como `(service_date, source_trip_id)` — nunca se asume que `source_trip_id` sea único entre fechas de servicio distintas.
- **`vehicle_id` / `train_id`** del feed en vivo son conceptos potencialmente distintos entre sí y de `trip_id` — ver `MADRID_PULSE_BRIEF_INICIAL.md` §4. No se asume equivalencia hasta validarlo empíricamente en MP-003.
- **`service_date`** es la fecha de servicio en **Europe/Madrid**, no UTC — un viaje nocturno puede cruzar la medianoche local y debe mantenerse en la fecha de servicio GTFS correspondiente, no en la fecha UTC del timestamp.
- Todos los `timestamptz` se almacenan en **UTC**; la conversión a `Europe/Madrid` ocurre solo en presentación o al resolver calendario de servicio GTFS.

## Deduplicación

- Clave de deduplicación propuesta: hash canónico (`payload_hash`) de los campos relevantes de una observación. Si Renfe repite exactamente el mismo payload en polls consecutivos, se almacena una sola fila (o se incrementa un contador `seen_count` si se decide conservarlo — pendiente de ADR en MP-007).
- La deduplicación nunca debe ocultar un cambio de `quality_flags` o de `current_status` aunque la posición geográfica no cambie.

## Versionado GTFS

- Cada carga de GTFS estático se registra como una versión (`gtfs_version_id`) con su fecha de publicación y checksum del fichero fuente.
- `service_date` enlaza con la versión GTFS vigente para esa fecha — necesario porque Renfe puede publicar actualizaciones de horarios que no son retroactivas.
- Nunca se sobrescribe una versión GTFS anterior; se referencia por versión para permitir reconstruir el histórico con el calendario vigente en su momento.

## Índices propuestos

```sql
(vehicle_position_observation observed_at DESC)
(vehicle_position_observation trip_id, observed_at DESC)
(vehicle_position_observation source_vehicle_id, observed_at DESC)
GIST(vehicle_position_observation.geom)
GIST(station.geom)
UNIQUE(ingestion_run_id, payload_hash)   -- según contrato de ingestión final (MP-006)
UNIQUE(trip.service_date, trip.source_trip_id)
UNIQUE(route.network_id, route.source_route_id)
```

## Retención (propuesta, no confirmada — ver DEC-004 en `docs/DECISIONS.md`)

| Tabla | Retención propuesta | Motor |
|---|---|---|
| `vehicle_position_observation` (detalle) | 7–14 días (rango a confirmar) | PostgreSQL hot |
| `trip_update_observation` | 30 días | PostgreSQL hot |
| `source_ingestion_run` | 90 días | PostgreSQL hot |
| `data_quality_event` | 180 días | PostgreSQL hot |
| `daily_line_metrics` / `station_daily_metrics` | Permanente | PostgreSQL + Parquet gold |
| Detalle crudo exportado | 12 meses (propuesta inicial, revisable) | Parquet / R2 |

Estos números son puntos de partida de la investigación, **no compromisos fijos**: deben confirmarse tras medir volumen real de ingesta (MP-007) y coste (MP-009).
