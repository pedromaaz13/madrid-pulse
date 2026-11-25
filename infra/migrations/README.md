# Migraciones PostgreSQL/PostGIS

Las migraciones son SQL plano, numeradas y emparejadas como `NNNN_nombre.up.sql`
y `NNNN_nombre.down.sql`. Se usa SQL plano porque MP-006 solo necesita una
migración inicial, permite auditar exactamente el DDL y evita introducir un
framework antes de que exista una aplicación que lo necesite. La contrapartida es
que el operador debe controlar explícitamente qué rollback ejecuta; un futuro
runner deberá registrar versiones aplicadas.

El Compose monta este directorio como `/migrations` (solo lectura). Después de
levantar el servicio según `infra/docker/README.md`, aplicar todas las migraciones
en orden:

```bash
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml exec -T postgres \
  sh -eu -c 'for migration in /migrations/*.up.sql; do psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration"; done'
```

Revertir la última migración (hoy `0004_run_recency`):

```bash
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml exec -T postgres \
  psql -v ON_ERROR_STOP=1 -U madrid_pulse -d madrid_pulse -f /migrations/0004_run_recency.down.sql
```

**0004_run_recency.** Calcula una vez la clasificación retroactiva de los runs
existentes y la asigna a las inserciones mediante trigger. Añade índices para
las lecturas por vehículo, viaje/run y started_at. Revertirla elimina esa
clasificación. Reaplicar el up conserva marcas existentes; después de un down
el backfill usa la tolerancia inicial de 2 s. Antes de cambiar el esquema de
una base persistente, conserva una copia si necesitas recuperar sus valores.

**0003_anchor_profile.** Añade la procedencia de movimiento del run. Un up
repetido conserva las huellas. El down elimina las huellas históricas;
al reaplicar up no se pueden reconstruir a partir del catálogo actual. Las
observaciones afectadas retienen en el ancla desde el primer fotograma.

`0002_api_batch_indexes` (MP-019) añade únicamente dos índices medidos con
`EXPLAIN (ANALYZE, BUFFERS)` -- no cambia tablas, columnas ni datos, así que su
rollback es seguro y solo degrada el rendimiento de las lecturas por lote de la
API (ver `docs/evidence/mp-019-explain-y-bench.md`). Revertir `0001_init`
sigue siendo la operación destructiva:

```bash
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml exec -T postgres \
  psql -v ON_ERROR_STOP=1 -U madrid_pulse -d madrid_pulse -f /migrations/0001_init.down.sql
```

El rollback elimina todas las tablas e índices de aplicación, pero conserva las
extensiones PostGIS que la propia imagen aprovisiona antes de ejecutar la
migración (`postgis_topology` y `postgis_tiger_geocoder` dependen de `postgis`).
No se usa `DROP EXTENSION ... CASCADE` porque borraría infraestructura que la
migración no creó.

## Correspondencia con el contrato canónico

Cuando `docs/DATA_MODEL.md` y `packages/contracts/canonical.py` usan nombres
distintos, manda el contrato canónico:

- `source_ingestion_run.entity_count` (no `entities_count`) y
  `source_timestamp` corresponden a `FeedHealth`.
- `vehicle_position_observation` conserva `latitude`, `longitude`,
  `raw_vehicle_label`, `nucleo_prefix` y `nucleo_name`; `geom` se genera en la
  base a partir de las coordenadas y queda `NULL` cuando ambas faltan.
- `trip_update_observation` incluye `next_stop_id` y `nucleo_prefix`.
- `service_alert.affected_route_ids` (no `affected_routes`) y el campo derivado
  `nucleo_prefixes` coinciden con `ServiceAlert`.

Las columnas de trazabilidad de persistencia (`received_at`, `trip_id` e
`ingestion_run_id`) no forman parte del objeto de fuente y se completan en la
operación de ingesta. `source_feed_version` materializa el versionado inmutable
que exige la sección "Versionado GTFS" de `DATA_MODEL.md` y evita que
`service_date.gtfs_version_id` sea una referencia sin destino.
