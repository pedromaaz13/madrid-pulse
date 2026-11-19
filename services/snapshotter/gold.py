"""Agregado "silver/gold inicial" sobre el Parquet crudo ya exportado.

**Limitación de alcance deliberada:** `docs/DATA_MODEL.md` define
`daily_line_metrics` (por `route_id`) y `station_daily_metrics` (por
`station_id`) como las tablas gold objetivo. Ninguna de las dos es
computable todavía: la resolución `trip_id` -> `route_id` y `stop_id` ->
`station_id` contra el GTFS estático está asignada explícitamente a MP-010
(ver ADR-0009), que NO es una dependencia de MP-009 ni está hecho. Rellenar
esas columnas ahora exigiría inventar una resolución no verificada, lo que
viola el principio de `AGENTS.md` de no inventar comportamiento.

En su lugar, este módulo calcula un resumen diario **por núcleo** (dimensión
ya resuelta por `packages/contracts/nucleo.py`, verificada en MP-003), como
primer paso real hacia el agregado completo. Cuando MP-010 resuelva
`route_id`/`station_id`, este módulo debe extenderse para escribir también
`daily_line_metrics`/`station_daily_metrics`, no sustituirse sin motivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class GoldSummaryResult:
    row_count: int
    output_path: Path


def _parquet_glob_or_empty(con: duckdb.DuckDBPyConnection, directory: Path, columns: str) -> str:
    """`read_parquet(glob)` si existen ficheros bajo `directory`, o un SELECT vacío con las
    mismas columnas en caso contrario (para que los JOIN/UNION no fallen por ausencia de datos
    ese día -- un día sin alertas, por ejemplo, es válido, no un error)."""
    if any(directory.glob("**/*.parquet")):
        return f"read_parquet('{directory}/**/*.parquet')"
    return f"(SELECT {columns} WHERE FALSE)"


def build_nucleo_daily_summary(
    raw_output_dir: Path, service_date: date, gold_output_dir: Path
) -> GoldSummaryResult:
    """Agrega los Parquet crudos del día en un resumen diario por núcleo.

    Lee únicamente lo ya exportado a `raw/` (no vuelve a tocar PostgreSQL),
    para que el agregado gold sea reproducible a partir del propio histórico
    frío, igual que exige el contrato de replay de esta tarea.
    """
    con = duckdb.connect()
    try:
        vp_dir = raw_output_dir / "raw" / "vehicle_position_observation" / f"date={service_date}"
        tu_dir = raw_output_dir / "raw" / "trip_update_observation" / f"date={service_date}"
        dqe_dir = raw_output_dir / "raw" / "data_quality_event" / f"date={service_date}"

        vp_source = _parquet_glob_or_empty(
            con, vp_dir, "NULL::VARCHAR AS nucleo_prefix, NULL::VARCHAR AS source_vehicle_id"
        )
        tu_source = _parquet_glob_or_empty(
            con, tu_dir, "NULL::VARCHAR AS nucleo_prefix, NULL::VARCHAR AS source_trip_id"
        )
        dqe_source = _parquet_glob_or_empty(con, dqe_dir, "NULL::VARCHAR AS flag")

        output_path = gold_output_dir / "gold" / "nucleo_daily_summary" / f"date={service_date}"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / "part.parquet"

        query = f"""
        WITH vehicle_positions AS (
            SELECT nucleo_prefix, count(*) AS positions_count,
                   count(DISTINCT source_vehicle_id) AS distinct_vehicles
            FROM {vp_source}
            GROUP BY nucleo_prefix
        ),
        trip_updates AS (
            SELECT nucleo_prefix, count(*) AS trip_updates_count,
                   count(DISTINCT source_trip_id) AS distinct_trips
            FROM {tu_source}
            GROUP BY nucleo_prefix
        ),
        quality_events_total AS (
            SELECT count(*) AS quality_events_count FROM {dqe_source}
        )
        SELECT
            $service_date AS service_date,
            coalesce(v.nucleo_prefix, t.nucleo_prefix) AS nucleo_prefix,
            coalesce(v.positions_count, 0) AS positions_count,
            coalesce(v.distinct_vehicles, 0) AS distinct_vehicles,
            coalesce(t.trip_updates_count, 0) AS trip_updates_count,
            coalesce(t.distinct_trips, 0) AS distinct_trips,
            (SELECT quality_events_count FROM quality_events_total) AS quality_events_count_total
        FROM vehicle_positions v
        FULL OUTER JOIN trip_updates t USING (nucleo_prefix)
        WHERE coalesce(v.nucleo_prefix, t.nucleo_prefix) IS NOT NULL
        """
        con.execute(
            f"COPY ({query}) TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)",
            {"service_date": service_date.isoformat()},
        )
        (row_count,) = con.execute(f"SELECT count(*) FROM read_parquet('{output_file}')").fetchone()
        return GoldSummaryResult(row_count=row_count, output_path=output_path)
    finally:
        con.close()
