# analytics/duckdb

Motor analítico local (DuckDB) sobre los Parquet particionados. Implementado
en `services/snapshotter/` (MP-009, ampliado en MP-015) — ver
`analytics/dbt/README.md` para el detalle de capas (raw → gold por
núcleo/línea/estación) y `docs/DATA_MODEL.md` para el esquema objetivo.

No hay código propio en este directorio: DuckDB se usa embebido, sin
servicio, directamente desde `services/snapshotter/gold.py` y
`services/snapshotter/export.py` (ver DEC-021 — un único motor, sin
`pandas`/`pyarrow` añadidos).
