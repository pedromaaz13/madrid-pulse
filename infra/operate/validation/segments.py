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


def check_segment(conn, start, end, after_gap):
    """Contrastar las vistas con las filas originales; comprueba faltantes y extras."""
    for table in ("vehicle_position_observation", "trip_update_observation"):
        query = sql.SQL("""
            WITH expected AS (
                SELECT v.id FROM public.{table} v JOIN public.source_ingestion_run r
                  ON r.id=v.ingestion_run_id
                WHERE r.started_at >= %s AND r.started_at < %s
                  AND (NOT %s OR v.observed_at >= %s)
            ), actual AS (SELECT id FROM pg_temp.{table})
            SELECT EXISTS ((SELECT * FROM expected EXCEPT SELECT * FROM actual)
                  UNION ALL (SELECT * FROM actual EXCEPT SELECT * FROM expected))
        """).format(table=sql.Identifier(table))
        if conn.execute(query, (start, end, after_gap, start)).fetchone()[0]:
            raise ValueError(f"Población incorrecta en el segmento: {table}")
