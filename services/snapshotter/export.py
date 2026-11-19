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

Columna de observación por tabla: `vehicle_position_observation` y
`trip_update_observation` tienen su propio `observed_at`; `source_ingestion_run`
tiene `started_at`; `data_quality_event` tiene `occurred_at`. **`service_alert`
NO tiene ningún `observed_at`/`received_at` propio** -- su `active_period_start`
es la ventana de VIGENCIA del aviso (puede ser semanas antes o después del
día en que Madrid Pulse lo observó), no el momento en que se ingirió.
Hallazgo real de la revisión de Codex en MP-009: particionar `service_alert`
por `active_period_start` hacía que alertas realmente observadas el día X
desaparecieran del Parquet de ese día si su vigencia caía en otra fecha --
3 alertas reales quedaron fuera del export del 19-nov pese a haberse
ingerido ese mismo día. Corregido uniendo a `source_ingestion_run` (vía
`ingestion_run_id`) y usando `started_at` de esa ejecución como el momento
de observación real, igual que para el resto de tablas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass(frozen=True)
class TableSource:
    table: str
    from_clause: str  # FROM de la consulta; alias siempre "t" para la tabla principal
    time_expr: str  # expresión SQL del momento de observación real


# Las cinco tablas "hot", con la expresión que representa de verdad cuándo se
# observó cada fila (no necesariamente una columna propia -- ver docstring).
RAW_TABLE_SOURCES: dict[str, TableSource] = {
    "vehicle_position_observation": TableSource(
        table="vehicle_position_observation",
        from_clause="pg.public.vehicle_position_observation AS t",
        time_expr="t.observed_at",
    ),
    "trip_update_observation": TableSource(
        table="trip_update_observation",
        from_clause="pg.public.trip_update_observation AS t",
        time_expr="t.observed_at",
    ),
    "service_alert": TableSource(
        table="service_alert",
        from_clause=(
            "pg.public.service_alert AS t "
            "JOIN pg.public.source_ingestion_run AS r ON r.id = t.ingestion_run_id"
        ),
        time_expr="r.started_at",
    ),
    "source_ingestion_run": TableSource(
        table="source_ingestion_run",
        from_clause="pg.public.source_ingestion_run AS t",
        time_expr="t.started_at",
    ),
    "data_quality_event": TableSource(
        table="data_quality_event",
        from_clause="pg.public.data_quality_event AS t",
        time_expr="t.occurred_at",
    ),
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
    source: TableSource,
    service_date: date,
    output_dir: Path,
) -> ExportResult:
    """Exporta las filas de `source.table` del día de servicio dado a Parquet particionado.

    El filtro de rango usa los límites UTC reales del día Europe/Madrid sobre
    `source.time_expr` (el momento de observación REAL de la fila, no
    necesariamente una columna propia de esa tabla -- ver docstring del
    módulo); la columna de partición `date`/`hour` se deriva de la misma
    expresión, convertida a hora local.
    """
    utc_start, utc_end = service_date_utc_bounds(service_date)
    table_output_dir = output_dir / "raw" / source.table

    (count,) = con.execute(
        f"""
        SELECT count(*) FROM {source.from_clause}
        WHERE {source.time_expr} >= ? AND {source.time_expr} < ?
        """,
        (utc_start, utc_end),
    ).fetchone()

    if count > 0:
        table_output_dir.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"""
            COPY (
                SELECT t.*,
                    strftime({source.time_expr} AT TIME ZONE 'Europe/Madrid', '%Y-%m-%d') AS date,
                    strftime({source.time_expr} AT TIME ZONE 'Europe/Madrid', '%H') AS hour
                FROM {source.from_clause}
                WHERE {source.time_expr} >= ? AND {source.time_expr} < ?
            ) TO '{table_output_dir}'
            (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (date, hour), OVERWRITE_OR_IGNORE)
            """,
            (utc_start, utc_end),
        )
    return ExportResult(table=source.table, row_count=count, output_path=table_output_dir)


def export_service_date(
    database_url: str, service_date: date, output_dir: Path
) -> list[ExportResult]:
    """Exporta las cinco tablas "hot" para un día de servicio completo."""
    con = _connect_with_postgres(database_url)
    try:
        return [
            export_raw_table(con, source, service_date, output_dir)
            for source in RAW_TABLE_SOURCES.values()
        ]
    finally:
        con.close()
