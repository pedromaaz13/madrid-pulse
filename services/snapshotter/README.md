# services/snapshotter

Exportador histórico (MP-009): mueve datos de PostgreSQL ("hot", MP-006) a
Parquet particionado comprimido con ZSTD ("frío", ADR-0003), y calcula un
resumen gold inicial.

## Ejecutar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Prepara la base del ejemplo según la guía enlazada.
MADRID_PULSE_ENV=replay \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
  python3 -m services.snapshotter 2026-11-19
```

`MADRID_PULSE_DATABASE_URL` y `MADRID_PULSE_ENV` son obligatorias.
`SNAPSHOTTER_OUTPUT_DIR` elige el destino (por defecto `data/parquet`).
En `test` y `replay` se exige la marca de base desechable antes de modificar
el archivo. Consulta la [guía de aislamiento](../../docs/operations/DATABASE_ISOLATION.md).

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
- **Capa gold** (`gold.py`): tres agregados, partición `date=YYYY-MM-DD`.
  - `build_nucleo_daily_summary` (MP-009): resumen diario **por núcleo**
    (`nucleo_prefix`, resuelto y verificado en MP-003).
  - `build_line_daily_metrics`/`build_station_daily_metrics` (MP-015):
    `daily_line_metrics`/`station_daily_metrics` reales (docs/DATA_MODEL.md),
    resolviendo `trip_id`→`route_id`/`stop_id`→`station_id` contra
    `packages.gtfs.Topology` — la resolución que bloqueaba esto desde MP-009
    (DEC-021/DEC-027) ya existe de verdad desde MP-010→MP-014. Límites
    documentados en DEC-033: `trips_scheduled` solo usa `calendar.txt` (sin
    `calendar_dates.txt`); el umbral de puntualidad es calibrable, no
    medido; `station_daily_metrics` no incluye `data_quality_events_count`
    (sin atribución real a una parada todavía).

## Test de replay

`services/snapshotter/tests/test_export_replay.py` inserta un día de prueba
conocido (COMPROMETIDO, no con `rollback()` -- DuckDB usa su propia conexión
`libpq` y no vería una transacción sin comprometer), lo exporta, y verifica
que el Parquet resultante reproduce exactamente las filas insertadas sin
pérdida. Limpia sus propias filas al terminar (`try/finally`), nunca
`rollback()`.

```bash
python3 -m unittest services.snapshotter.tests.test_export         # puro, sin BD
python3 -m unittest services.snapshotter.tests.test_gold           # puro, sin BD (fixture GTFS real)
MADRID_PULSE_ENV=test \
MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse \
  python3 -m unittest services.snapshotter.tests.test_export_replay
```
