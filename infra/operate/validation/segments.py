"""Aislar el historial visible a producción mediante vistas temporales de sesión."""

from datetime import datetime, timedelta

from psycopg import sql


def windows(manifest):
    start, end = (
        datetime.fromisoformat(manifest["period"][key])
        for key in ("start_utc", "end_utc")
    )
    spans = []
    for gap in manifest["coverage_by_feed"]["vehicle_positions"][
        "gaps_over_60_seconds"
    ]:
        left, right = (
            datetime.fromisoformat(gap[key]) for key in ("from_utc", "to_utc")
        )
        if not start <= left < right <= end:
            raise ValueError("Hueco de posiciones fuera del periodo u orden incorrecto")
        # La consulta SQL del arnés usa un extremo superior exclusivo.
        spans.append((start, left + timedelta(microseconds=1)))
        start = right
    return [*spans, (start, end)]


def isolate(conn, start, end, after_gap):
    # Los ids de runs no se suponen contiguos. También se filtra el GPS previo
    # y la relación base por run que lee producción sin JOIN al historial visible.
    bounds = sql.SQL("started_at >= {} AND started_at < {}").format(
        sql.Literal(start), sql.Literal(end)
    )
    conn.execute(
        sql.SQL(
            "CREATE OR REPLACE TEMP VIEW source_ingestion_run AS "
            "SELECT * FROM public.source_ingestion_run WHERE {}"
        ).format(bounds)
    )
    for name in ("vehicle_position_observation", "trip_update_observation"):
        source = sql.Identifier(name)
        stamp = (
            sql.SQL(" AND observed_at >= {}").format(sql.Literal(start))
            if after_gap
            else sql.SQL("")
        )
        conn.execute(
            sql.SQL(
                "CREATE OR REPLACE TEMP VIEW {} AS SELECT * FROM public.{} "
                "WHERE ingestion_run_id IN (SELECT id FROM pg_temp.source_ingestion_run){}"
            ).format(source, source, stamp)
        )
