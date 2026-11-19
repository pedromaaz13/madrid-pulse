"""Exportación de las tablas "hot" de PostgreSQL a Parquet particionado ("frío").

Usa DuckDB como único motor: su extensión `postgres` lee directamente de
PostgreSQL (sin duplicar lógica de acceso a datos del colector) y su soporte
nativo de Parquet escribe los ficheros particionados con compresión ZSTD. No
se introduce `pandas`/`pyarrow` como dependencias separadas -- DuckDB ya
cubre ambas necesidades (ver ADR-0003: "consumido vía DuckDB/dbt").

Partición temporal: `docs/DATA_MODEL.md` fija `service_date` en
**Europe/Madrid, no UTC** -- un timestamp UTC de madrugada puede pertenecer
al día de servicio SIGUIENTE en hora local (España está en CET/UTC+1 en
noviembre). Por eso la partición `date=`/`hour=` se calcula siempre
convirtiendo el timestamp a `Europe/Madrid` antes de particionar, nunca
sobre el valor UTC crudo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

MADRID_TZ = ZoneInfo("Europe/Madrid")

# Tabla -> columna de tiempo usada para filtrar por día de servicio y particionar.
RAW_TABLES: dict[str, str] = {
    "vehicle_position_observation": "observed_at",
    "trip_update_observation": "observed_at",
    "service_alert": "active_period_start",
    "source_ingestion_run": "started_at",
    "data_quality_event": "occurred_at",
}


def service_date_utc_bounds(service_date: date) -> tuple[datetime, datetime]:
    """Límites `[inicio, fin)` en UTC del día de servicio `service_date` (Europe/Madrid)."""
    start_local = datetime.combine(service_date, time.min, tzinfo=MADRID_TZ)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(ZoneInfo("UTC")), end_local.astimezone(ZoneInfo("UTC"))


@dataclass(frozen=True)
class ExportResult:
    table: str
    row_count: int
    output_path: Path


def _connect_with_postgres(database_url: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{database_url}' AS pg (TYPE POSTGRES, READ_ONLY)")
    return con


def export_raw_table(
    con: duckdb.DuckDBPyConnection,
    table: str,
    time_column: str,
    service_date: date,
    output_dir: Path,
) -> ExportResult:
    """Exporta las filas de `table` del día de servicio dado a Parquet particionado.

    El filtro de rango usa los límites UTC reales del día Europe/Madrid; la
    columna de partición `date`/`hour` se deriva por separado, convertida a
    hora local, para que el nombre del directorio coincida con el día de
    servicio real aunque el timestamp almacenado sea UTC.
    """
    utc_start, utc_end = service_date_utc_bounds(service_date)
    table_output_dir = output_dir / "raw" / table

    (count,) = con.execute(
        f"""
        SELECT count(*) FROM pg.public.{table}
        WHERE {time_column} >= ? AND {time_column} < ?
        """,
        (utc_start, utc_end),
    ).fetchone()

    if count > 0:
        table_output_dir.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"""
            COPY (
                SELECT *,
                    strftime({time_column} AT TIME ZONE 'Europe/Madrid', '%Y-%m-%d') AS date,
                    strftime({time_column} AT TIME ZONE 'Europe/Madrid', '%H') AS hour
                FROM pg.public.{table}
                WHERE {time_column} >= ? AND {time_column} < ?
            ) TO '{table_output_dir}'
            (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (date, hour), OVERWRITE_OR_IGNORE)
            """,
            (utc_start, utc_end),
        )
    return ExportResult(table=table, row_count=count, output_path=table_output_dir)


def export_service_date(
    database_url: str, service_date: date, output_dir: Path
) -> list[ExportResult]:
    """Exporta las cinco tablas "hot" para un día de servicio completo."""
    con = _connect_with_postgres(database_url)
    try:
        return [
            export_raw_table(con, table, time_column, service_date, output_dir)
            for table, time_column in RAW_TABLES.items()
        ]
    finally:
        con.close()
