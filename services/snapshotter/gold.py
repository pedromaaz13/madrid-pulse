"""Agregado "silver/gold inicial" sobre el Parquet crudo ya exportado.

**Historia de esta limitación:** `docs/DATA_MODEL.md` define
`daily_line_metrics` (por `route_id`) y `station_daily_metrics` (por
`station_id`) como las tablas gold objetivo. En MP-009 ninguna de las dos era
computable: la resolución `trip_id` -> `route_id` y `stop_id` -> `station_id`
contra el GTFS estático estaba asignada a MP-010 (ver ADR-0009), que no era
dependencia de MP-009. Por eso este módulo empezó calculando solo un resumen
diario **por núcleo** (`build_nucleo_daily_summary`, dimensión ya resuelta por
`packages/contracts/nucleo.py`, verificada en MP-003).

Con MP-010→MP-014 ya `DONE`, esa resolución existe de verdad
(`packages.gtfs.Topology`) — `build_line_daily_metrics` y
`build_station_daily_metrics` (MP-015) la usan para completar el agregado
gold real, documentado con sus propios límites (ver DEC-033 en
`docs/DECISIONS.md`): `trips_scheduled` usa únicamente `calendar.txt`
(día de la semana + rango `start_date`/`end_date`), sin `calendar_dates.txt`
(no parseado por `packages.gtfs`) — un servicio con excepción de calendario
puntual no se refleja todavía. `station_daily_metrics` solo calcula
`observations_count` (vía `current_stop_id`, campo real confirmado en MP-003
idéntico al `stop_id` de GTFS estático); `data_quality_events_count` queda
deliberadamente fuera porque `data_quality_event.entity_ref` solo referencia
`source_vehicle_id`/`source_trip_id`, nunca una parada — atribuirlo a una
estación exigiría inventar un cruce por proximidad temporal no verificado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import duckdb

from packages.gtfs import Topology


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


_WEEKDAY_ATTRS = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)


@dataclass(frozen=True)
class GoldThresholds:
    """Punto de partida calibrable, no verdad de diseño (mismo criterio que
    `packages.quality.engine.QualityThresholds`). `on_time_threshold_seconds`
    no tiene todavía ningún dato real de puntualidad de Cercanías Madrid con
    el que calibrarse; 300s (5 min) es un orden de magnitud razonable para
    cercanías, a revisar en cuanto exista histórico suficiente."""

    on_time_threshold_seconds: float = 300.0


def _scheduled_trip_ids_by_route(topology: Topology, service_date: date) -> dict[str, set[str]]:
    """Resuelve qué `trip_id` están programados para `service_date` por `route_id`.

    Usa únicamente `calendar.txt` (día de la semana dentro de `[start_date,
    end_date]`); `calendar_dates.txt` no está parseado por `packages.gtfs`
    (ver docstring del módulo) -- una excepción puntual de calendario no se
    refleja todavía aquí.
    """
    weekday_attr = _WEEKDAY_ATTRS[service_date.weekday()]
    active_service_ids = {
        service.service_id
        for service in topology.calendar
        if getattr(service, weekday_attr)
        and datetime.strptime(service.start_date, "%Y%m%d").date()
        <= service_date
        <= datetime.strptime(service.end_date, "%Y%m%d").date()
    }
    by_route: dict[str, set[str]] = {}
    for trip in topology.trips:
        if trip.service_id in active_service_ids:
            by_route.setdefault(trip.route_id, set()).add(trip.trip_id)
    return by_route


def build_line_daily_metrics(
    raw_output_dir: Path,
    service_date: date,
    gold_output_dir: Path,
    topology: Topology,
    thresholds: GoldThresholds = GoldThresholds(),
) -> GoldSummaryResult:
    """Calcula `daily_line_metrics` (docs/DATA_MODEL.md) a partir del Parquet
    crudo ya exportado y de la topología GTFS estática cargada.

    `trips_with_delay_data` cuenta un trip si CUALQUIERA de sus
    `trip_update_observation` del día tuvo `delay_coverage='reported'`;
    `on_time_pct_of_covered` usa el retraso **más reciente reportado** de
    ese trip como su veredicto del día (ver docstring del módulo para el
    umbral). Ambos porcentajes son `numeric(5,2)` en escala `0..100`, igual
    que `infra/migrations/0001_init.up.sql` y `docs/DATA_CONTRACTS.md`
    (hallazgo de la revisión de Codex: la primera versión de esta función
    calculaba una fracción `0..1`, inconsistente con el esquema real).
    `delay_coverage_pct` nunca es `NULL` para una fila emitida (toda fila
    tiene por construcción `trips_scheduled >= 1`, ver `scheduled_trips`
    más abajo); `on_time_pct_of_covered` sí es `NULL` (nunca `0`) cuando
    `trips_with_delay_data = 0` -- dato ausente, no cero
    (docs/DATA_QUALITY.md).
    """
    con = duckdb.connect()
    try:
        tu_dir = raw_output_dir / "raw" / "trip_update_observation" / f"date={service_date}"
        tu_source = _parquet_glob_or_empty(
            con,
            tu_dir,
            "NULL::VARCHAR AS source_trip_id, NULL::INTEGER AS delay_seconds, "
            "NULL::VARCHAR AS delay_coverage, NULL::TIMESTAMPTZ AS observed_at",
        )

        scheduled_by_route = _scheduled_trip_ids_by_route(topology, service_date)
        con.execute("CREATE TEMP TABLE scheduled_trips (route_id VARCHAR, trip_id VARCHAR)")
        rows = [
            (route_id, trip_id)
            for route_id, trip_ids in scheduled_by_route.items()
            for trip_id in trip_ids
        ]
        if rows:
            con.executemany("INSERT INTO scheduled_trips VALUES (?, ?)", rows)

        output_path = gold_output_dir / "gold" / "daily_line_metrics" / f"date={service_date}"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / "part.parquet"

        query = f"""
        WITH trip_reports AS (
            SELECT
                source_trip_id,
                bool_or(delay_coverage = 'reported') AS has_reported_delay,
                arg_max(delay_seconds, observed_at) FILTER (WHERE delay_coverage = 'reported')
                    AS latest_reported_delay_seconds
            FROM {tu_source}
            GROUP BY source_trip_id
        )
        SELECT
            $service_date AS service_date,
            s.route_id AS route_id,
            count(DISTINCT s.trip_id) AS trips_scheduled,
            count(DISTINCT CASE WHEN r.has_reported_delay THEN s.trip_id END) AS trips_with_delay_data,
            CASE WHEN count(DISTINCT s.trip_id) = 0 THEN NULL
                 ELSE round(
                     100.0 * count(DISTINCT CASE WHEN r.has_reported_delay THEN s.trip_id END)::DOUBLE
                          / count(DISTINCT s.trip_id),
                     2
                 )
            END AS delay_coverage_pct,
            CASE WHEN count(DISTINCT CASE WHEN r.has_reported_delay THEN s.trip_id END) = 0 THEN NULL
                 ELSE round(
                     100.0 * count(DISTINCT CASE
                          WHEN r.has_reported_delay
                               AND abs(r.latest_reported_delay_seconds) <= $on_time_threshold
                          THEN s.trip_id
                      END)::DOUBLE
                          / count(DISTINCT CASE WHEN r.has_reported_delay THEN s.trip_id END),
                     2
                 )
            END AS on_time_pct_of_covered
        FROM scheduled_trips s
        LEFT JOIN trip_reports r ON r.source_trip_id = s.trip_id
        GROUP BY s.route_id
        """
        con.execute(
            f"COPY ({query}) TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)",
            {
                "service_date": service_date.isoformat(),
                "on_time_threshold": thresholds.on_time_threshold_seconds,
            },
        )
        (row_count,) = con.execute(f"SELECT count(*) FROM read_parquet('{output_file}')").fetchone()
        return GoldSummaryResult(row_count=row_count, output_path=output_path)
    finally:
        con.close()


def build_station_daily_metrics(
    raw_output_dir: Path, service_date: date, gold_output_dir: Path, topology: Topology
) -> GoldSummaryResult:
    """Calcula `station_daily_metrics.observations_count` (docs/DATA_MODEL.md)
    a partir de `vehicle_position_observation.current_stop_id` -- campo real,
    confirmado idéntico al `stop_id` del GTFS estático en MP-003. No calcula
    `data_quality_events_count` (ver docstring del módulo): atribuirlo a una
    estación exigiría un cruce no verificado.
    """
    con = duckdb.connect()
    try:
        vp_dir = raw_output_dir / "raw" / "vehicle_position_observation" / f"date={service_date}"
        vp_source = _parquet_glob_or_empty(con, vp_dir, "NULL::VARCHAR AS current_stop_id")

        con.execute("CREATE TEMP TABLE valid_stations (station_id VARCHAR)")
        stop_ids = [(stop.stop_id,) for stop in topology.stops]
        if stop_ids:
            con.executemany("INSERT INTO valid_stations VALUES (?)", stop_ids)

        output_path = gold_output_dir / "gold" / "station_daily_metrics" / f"date={service_date}"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / "part.parquet"

        query = f"""
        SELECT
            $service_date AS service_date,
            v.current_stop_id AS station_id,
            count(*) AS observations_count
        FROM {vp_source} v
        JOIN valid_stations st ON st.station_id = v.current_stop_id
        WHERE v.current_stop_id IS NOT NULL
        GROUP BY v.current_stop_id
        """
        con.execute(
            f"COPY ({query}) TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)",
            {"service_date": service_date.isoformat()},
        )
        (row_count,) = con.execute(f"SELECT count(*) FROM read_parquet('{output_file}')").fetchone()
        return GoldSummaryResult(row_count=row_count, output_path=output_path)
    finally:
        con.close()
