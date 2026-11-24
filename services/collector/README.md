# services/collector

Colector idempotente de los feeds GTFS-RT de Renfe (MP-007). Sondea
`vehicle_positions.json`, `trip_updates.json` y `alerts.json`, normaliza cada
entidad al contrato canónico (`packages/contracts/`), filtra a Madrid y
persiste en PostgreSQL/PostGIS (`infra/migrations/`, MP-006) evitando
duplicar filas para una entidad sin cambios reales entre polls.

## Ejecutar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
# Si es la primera vez: aplicar infra/migrations/0001_init.up.sql (ver su README)
python3 -m services.collector
```

Variables de entorno (todas opcionales, con los valores por defecto de
`config.py`): `COLLECTOR_POLL_INTERVAL_SECONDS` (30), `COLLECTOR_REQUEST_TIMEOUT_SECONDS`
(10), `COLLECTOR_MAX_RETRIES` (3), `COLLECTOR_BACKOFF_BASE_SECONDS` (1),
`MADRID_PULSE_DATABASE_URL` (apunta al Postgres local de MP-006 en el puerto `5433`).

## Diseño

- **`http_client.py`** — `fetch_with_retry`: reintentos con backoff exponencial
  (`backoff_base * 2**intento`) y timeout configurable. Solo `urllib` de la
  librería estándar.
- **`collector.py`** — `run_cycle(feed, conn, retry_policy)`: un ciclo completo
  (fetch → parse → filtro de alcance → dedupe → persist), con el ciclo entero
  comprometido como una sola transacción (`conn.transaction()`). Un fallo de
  red tras agotar reintentos o una respuesta que no valida se registra como
  `source_ingestion_run.status = 'error'` (con el hash de los bytes recibidos)
  y el ciclo termina sin relanzar la excepción. Un feed válido con cero
  entidades sigue siendo `ok`; un fallo parcial nunca borra observaciones
  previamente persistidas.
- **`db.py`** — capa de acceso a PostgreSQL. Las funciones de inserción NO
  abren su propia transacción (ver nota en el módulo: hacerlo con una conexión
  de larga duración produce commits parciales o filas que nunca se
  comprometen); el límite de transacción vive únicamente en `run_cycle`.
- **Deduplicación** (ADR-0010/DEC-013): se compara el `payload_hash` de cada
  entidad contra el de la última fila almacenada para su misma clave de
  entidad de origen. Si coincide, no se inserta una fila nueva.
- **Filtro de alcance** (ADR-0008/ADR-0001): se descartan entidades cuyo
  `nucleo_prefix` no sea `10` (Madrid). **Limitación conocida** (DEC-020): esto
  no acota todavía a la línea C5 específicamente — eso exige resolver
  `trip_id` → `route_id` vía el GTFS estático, trabajo asignado a MP-010.

## Hallazgos reales del feed en vivo (no cubiertos por las fixtures de MP-004)

Documentados en detalle en `docs/research/MP-003-probe-findings.md` §10 y en
las adendas de ADR-0008/ADR-0009:

- Trenes de refuerzo con `trip_id` formato `SPECIAL_<núcleo>_<resto>` (sin
  prefijo numérico directo) y `scheduleRelationship: "ADDED"`, sin viaje
  correspondiente en `trips.txt`.
- `stopTimeUpdate[].arrival` puede no traer `delay` (solo `time`).

## Tests

```bash
python3 -m unittest services.collector.tests.test_http_client      # sin red, sin BD
python3 -m unittest services.collector.tests.test_collector_cycle  # requiere el Postgres de MP-006 levantado
```

`test_collector_cycle` se salta (`unittest.SkipTest`) si no puede conectar a
la base local -- no falla el conjunto si el contenedor no está levantado.
