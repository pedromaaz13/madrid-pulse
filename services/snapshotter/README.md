# services/snapshotter

Exportador histórico (MP-009): mueve datos de PostgreSQL ("hot", MP-006) a
Parquet particionado comprimido con ZSTD ("frío", ADR-0003), y calcula un
resumen gold inicial.

## Ejecutar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
python3 -m services.snapshotter 2026-11-19
```

`SNAPSHOTTER_OUTPUT_DIR` (por defecto `data/parquet`) y
`MADRID_PULSE_DATABASE_URL` son las únicas variables de entorno.

## Diseño

- **Un solo motor, DuckDB**, para leer PostgreSQL (extensión `postgres`,
  `ATTACH ... (TYPE POSTGRES, READ_ONLY)`) y escribir Parquet particionado
  (`COPY ... (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (...))`). No se
  introducen `pandas`/`pyarrow` como dependencias separadas -- DuckDB ya
  cubre ambas necesidades (ver ADR-0003).
- **Partición por día de servicio Europe/Madrid, no UTC.** `docs/DATA_MODEL.md`
  exige que `service_date` sea la fecha de servicio en hora local, no UTC.
  **Hallazgo real durante esta tarea:** los datos del soak test de MP-007
  (`23:31:42 UTC` del 18-nov) pertenecen al día de servicio **19-nov** en
  Europe/Madrid (CET, UTC+1 en noviembre) -- leer la fecha UTC directamente
  habría exportado esas filas al día equivocado. `export.py` convierte
  siempre a `Europe/Madrid` antes de calcular los límites del día y la
  partición `date=`/`hour=`. Ver `services/snapshotter/tests/test_export.py`
  para la regresión explícita, incluido el caso de horario de verano (CEST).
- **Capa raw**: las cinco tablas "hot" (`vehicle_position_observation`,
  `trip_update_observation`, `service_alert`, `source_ingestion_run`,
  `data_quality_event`) se exportan completas, particionadas
  `date=YYYY-MM-DD/hour=HH`.
- **Capa gold inicial** (`gold.py`): resumen diario **por núcleo**
  (`nucleo_prefix`, ya resuelto y verificado en MP-003), partición
  `date=YYYY-MM-DD`. **Limitación deliberada:** NO calcula
  `daily_line_metrics`/`station_daily_metrics` (por `route_id`/`station_id`)
  porque esa resolución depende de MP-010 (GTFS estático), que no es
  dependencia de MP-009. Documentado en el docstring de `gold.py` para no
  perderse cuando MP-010 esté hecho.

## Test de replay

`services/snapshotter/tests/test_export_replay.py` inserta un día de prueba
conocido (COMPROMETIDO, no con `rollback()` -- DuckDB usa su propia conexión
`libpq` y no vería una transacción sin comprometer), lo exporta, y verifica
que el Parquet resultante reproduce exactamente las filas insertadas sin
pérdida. Limpia sus propias filas al terminar (`try/finally`), nunca
`rollback()`.

```bash
python3 -m unittest services.snapshotter.tests.test_export         # puro, sin BD
python3 -m unittest services.snapshotter.tests.test_export_replay  # requiere PostgreSQL local
```
