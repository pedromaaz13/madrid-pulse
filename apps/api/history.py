"""Lectura del histórico frío (Parquet) para `/api/v1/history/*` (MP-021).

Separación deliberada respecto al resto de la API:

- `service.py`/`snapshot.py` leen **estado operativo** de PostgreSQL en cada
  petición (lo que cambia con cada sondeo).
- este módulo lee **histórico ya cerrado** del archivo Parquet que produce
  `services/snapshotter/` (lo que ya no cambia), con DuckDB y en solo
  lectura. Nunca toca PostgreSQL ni la topología en memoria.

Por eso el histórico **no se añade al contrato de MP-019**: `/api/v1/snapshot`
y `/api/v1/catalog` quedan exactamente como están (ADR-0014) y el histórico
vive en recursos nuevos. Un día archivado es inmutable salvo reproceso
explícito, así que estos recursos se pueden cachear; el snapshot operativo
sigue siendo `no-store`.

**Huecos y denominadores.** Ninguna de estas funciones calcula un porcentaje
sin devolver a la vez el numerador y el denominador reales de los que sale, y
ninguna convierte un `NULL` en `0`. Un día cuyo archivo no existe devuelve
"no hay archivo de ese día", nunca un día con métricas a cero: la ausencia de
archivo no es ausencia de servicio (docs/DATA_QUALITY.md).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from services.snapshotter.history import MART_NAME

_DATE_PARTITION = re.compile(r"^date=(\d{4}-\d{2}-\d{2})$")

LINE_METRICS_MART = "daily_line_metrics"
STATION_METRICS_MART = "station_daily_metrics"
RAW_POSITIONS_TABLE = "vehicle_position_observation"
RAW_TRIP_UPDATES_TABLE = "trip_update_observation"


@dataclass(frozen=True)
class Archive:
    """Raíz del histórico frío en disco (`SNAPSHOTTER_OUTPUT_DIR`).

    No se carga nada en memoria al construirla: el archivo puede crecer cada
    día y la API no debe mantener una copia que envejezca en silencio. Cada
    consulta abre una conexión DuckDB en memoria, lee los Parquet que necesita
    y la cierra.
    """

    root: Path

    def mart_dir(self, mart: str, service_date: date) -> Path:
        return self.root / "gold" / mart / f"date={service_date.isoformat()}"

    def raw_dir(self, table: str, service_date: date) -> Path:
        return self.root / "raw" / table / f"date={service_date.isoformat()}"

    def available_service_dates(self) -> list[date]:
        """Días con mart de circulaciones realmente presente, de más reciente a más antiguo.

        Se enumera sobre el mart por circulación y no sobre `raw/`, porque es
        el mart el que el histórico sabe responder: un `raw/` exportado sin
        agregar todavía no es un día consultable, y anunciarlo como disponible
        daría una vista vacía sin explicación.
        """
        base = self.root / "gold" / MART_NAME
        if not base.is_dir():
            return []
        found: list[date] = []
        for child in base.iterdir():
            match = _DATE_PARTITION.match(child.name)
            if match is None or not child.is_dir():
                continue
            if not any(child.glob("**/*.parquet")):
                continue
            found.append(date.fromisoformat(match.group(1)))
        return sorted(found, reverse=True)

    def has_service_date(self, service_date: date) -> bool:
        directory = self.mart_dir(MART_NAME, service_date)
        return directory.is_dir() and any(directory.glob("**/*.parquet"))


def _rows(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    con = duckdb.connect()
    try:
        cursor = con.execute(query, params or {})
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        con.close()


def _glob(directory: Path) -> str:
    return f"read_parquet('{directory}/**/*.parquet')"


def _utc_iso(expr: str) -> str:
    """SQL que devuelve `expr` (un `TIMESTAMPTZ`) como texto ISO-8601 en UTC.

    DuckDB solo sabe materializar un `TIMESTAMP WITH TIME ZONE` como
    `datetime` de Python si `pytz` está instalado, y `pytz` no es dependencia
    del proyecto (`requirements.txt`) ni hace falta: la conversión explícita a
    UTC en SQL deja el valor en el único formato que el contrato admite --
    instante absoluto en UTC, con la conversión a Europe/Madrid reservada a la
    presentación (docs/DATA_MODEL.md). Pydantic parsea la cadena al `datetime`
    del esquema sin ambigüedad de zona.
    """
    return (
        f"CASE WHEN {expr} IS NULL THEN NULL ELSE "
        f"strftime({expr} AT TIME ZONE 'UTC', '%Y-%m-%dT%H:%M:%S.%fZ') END"
    )


def day_index(archive: Archive) -> list[dict[str, Any]]:
    """Resumen de cada día archivado: identidad del día y sus denominadores.

    Los cuatro recuentos son los denominadores que el frontend necesita para
    no presentar nunca una cobertura sin su base: cuántas circulaciones
    programadas tenía el día, cuántas se observaron de verdad, y cuántas
    quedaron sin observar (el hueco explícito).
    """
    summary: list[dict[str, Any]] = []
    for service_date in archive.available_service_dates():
        directory = archive.mart_dir(MART_NAME, service_date)
        # Los recuentos se derivan de `coverage`, que es una clasificación de
        # una sola categoría por fila (ver `services/snapshotter/history.py`):
        # así los cinco cierran contra `rows_total` sin solaparse. Antes
        # `circulations_unobserved` contaba como hueco de cobertura cualquier
        # viaje sin posición, incluidos los que el operador había **anulado** --
        # culpaba al colector de trenes que nunca salieron.
        (row,) = _rows(
            f"""
            SELECT
                count(*) AS rows_total,
                count(*) FILTER (WHERE scheduled) AS circulations_scheduled,
                count(*) FILTER (WHERE observed) AS circulations_observed,
                count(*) FILTER (WHERE coverage = 'unobserved') AS circulations_unobserved,
                count(*) FILTER (WHERE coverage = 'canceled') AS circulations_canceled,
                count(*) FILTER (WHERE coverage = 'operator_only') AS circulations_operator_only,
                count(*) FILTER (WHERE coverage = 'unscheduled') AS circulations_unscheduled,
                count(DISTINCT line_short_name) FILTER (WHERE line_short_name <> '') AS lines_present,
                {_utc_iso('min(first_observed_at)')} AS first_observed_at,
                {_utc_iso('max(last_observed_at)')} AS last_observed_at
            FROM {_glob(directory)}
            """
        )
        row["service_date"] = service_date.isoformat()
        summary.append(row)
    return summary


def line_metrics(
    archive: Archive, service_date: date, route_lines: Mapping[str, str]
) -> list[dict[str, Any]]:
    """`daily_line_metrics` del día, con su línea comercial resuelta.

    `delay_coverage_pct` y `on_time_pct_of_covered` llegan tal cual los
    calculó `gold.py` -- `on_time_pct_of_covered` es `NULL` (nunca `0`) si
    ningún viaje de esa ruta tuvo retraso reportado -- y viajan siempre junto
    a `trips_scheduled` y `trips_with_delay_data`, que son su denominador.

    `route_lines` es la correspondencia `route_id` -> `route_short_name` del
    catálogo GTFS ya cargado en memoria por la API, que es su fuente
    autoritativa: el mart por circulación no sirve para esto porque solo
    contiene rutas con viajes con `stop_times`, y una ruta programada cuyos
    viajes son huérfanos aparecería sin nombre de línea. Una `route_id` que el
    catálogo vigente no conoce se devuelve con `line_short_name` vacío -- no se
    inventa un nombre (puede ser una ruta de una versión anterior del GTFS, que
    no es retroactivo; ver docs/DATA_MODEL.md "Versionado GTFS").
    """
    metrics_dir = archive.mart_dir(LINE_METRICS_MART, service_date)
    if not (metrics_dir.is_dir() and any(metrics_dir.glob("**/*.parquet"))):
        return []
    rows = _rows(
        f"""
        SELECT
            route_id,
            trips_scheduled,
            trips_with_delay_data,
            delay_coverage_pct,
            on_time_pct_of_covered
        FROM {_glob(metrics_dir)}
        """
    )
    for row in rows:
        row["line_short_name"] = route_lines.get(row["route_id"], "")
    rows.sort(key=lambda row: (row["line_short_name"], row["route_id"]))
    return rows


def circulations(
    archive: Archive,
    service_date: date,
    *,
    line: str | None = None,
    only: str = "all",
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Circulaciones archivadas del día, filtrables por línea y por hueco.

    `only` selecciona por la categoría `coverage` del mart, que es única por
    fila:

    - `all`: todo lo que el día contiene.
    - `observed`: programadas con al menos una posición real.
    - `unobserved`: el **hueco de verdad** -- programadas sin posición y sin
      ninguna actualización de viaje.
    - `canceled`: programadas que el operador declaró `CANCELED`. No son un
      hueco de cobertura: el tren no circuló, y el feed nos lo dijo.
    - `operator_only`: programadas sin posición pero con actualización de
      viaje -- el operador las conocía y nunca las localizamos.
    - `unscheduled`: observadas cuyo `trip_id` no estaba en el calendario.

    El orden pone primero lo observado y, dentro, lo que más posiciones tiene:
    lo demás no se esconde (sigue siendo consultable por su categoría y
    contabilizado en `day_index`), pero la vista por omisión empieza por lo que
    de verdad se vio.
    """
    directory = archive.mart_dir(MART_NAME, service_date)
    if not (directory.is_dir() and any(directory.glob("**/*.parquet"))):
        return []
    clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if line is not None:
        clauses.append("line_short_name = $line")
        params["line"] = line
    if only in {"observed", "unobserved", "canceled", "operator_only", "unscheduled"}:
        clauses.append("coverage = $coverage")
        params["coverage"] = only
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return _rows(
        f"""
        SELECT
            service_date, route_id, line_short_name, trip_id, vehicle_id,
            scheduled, observed, canceled, coverage, headsign,
            scheduled_first_stop_id, scheduled_first_departure_time,
            scheduled_last_stop_id, scheduled_last_arrival_time,
            positions_count,
            {_utc_iso('first_observed_at')} AS first_observed_at,
            {_utc_iso('last_observed_at')} AS last_observed_at,
            distinct_stops_observed, last_current_status,
            trip_updates_count, delay_reported_count,
            latest_reported_delay_seconds, on_time
        FROM {_glob(directory)}
        {where}
        ORDER BY observed DESC, positions_count DESC NULLS LAST,
                 line_short_name, trip_id, vehicle_id NULLS LAST
        LIMIT $limit
        """,
        params,
    )


def circulation_detail(
    archive: Archive, service_date: date, vehicle_id: str, trip_id: str
) -> dict[str, Any] | None:
    """Una circulación concreta: su fila del mart más sus observaciones crudas.

    Es la consulta que cierra el recorrido Live -> History: la identidad que
    pide es exactamente la de la URL del frontend (`?train=&trip=&sd=`), sin
    traducir ninguna clave. Devuelve `None` si esa identidad no está en el
    archivo de ese día -- nunca una ficha vacía que parezca una circulación sin
    actividad.

    `vehicle_id` admite `None` como cadena vacía para consultar un viaje
    programado que nunca se observó: entonces no hay observaciones que
    devolver y `positions` es una lista vacía, con `observed=false` en la
    cabecera explicando por qué.
    """
    directory = archive.mart_dir(MART_NAME, service_date)
    if not (directory.is_dir() and any(directory.glob("**/*.parquet"))):
        return None
    vehicle_clause = (
        "vehicle_id IS NULL" if vehicle_id == "" else "vehicle_id = $vehicle_id"
    )
    params: dict[str, Any] = {"trip_id": trip_id}
    if vehicle_id != "":
        params["vehicle_id"] = vehicle_id
    header_rows = _rows(
        f"""
        SELECT
            service_date, route_id, line_short_name, trip_id, vehicle_id,
            scheduled, observed, canceled, coverage, headsign,
            scheduled_first_stop_id, scheduled_first_departure_time,
            scheduled_last_stop_id, scheduled_last_arrival_time,
            positions_count,
            {_utc_iso('first_observed_at')} AS first_observed_at,
            {_utc_iso('last_observed_at')} AS last_observed_at,
            distinct_stops_observed, last_current_status,
            trip_updates_count, delay_reported_count,
            latest_reported_delay_seconds, on_time
        FROM {_glob(directory)}
        WHERE trip_id = $trip_id AND {vehicle_clause}
        """,
        params,
    )
    if not header_rows:
        return None
    header = header_rows[0]

    positions: list[dict[str, Any]] = []
    raw_dir = archive.raw_dir(RAW_POSITIONS_TABLE, service_date)
    if vehicle_id != "" and raw_dir.is_dir() and any(raw_dir.glob("**/*.parquet")):
        positions = _rows(
            f"""
            SELECT {_utc_iso('observed_at')} AS observed_at,
                   {_utc_iso('received_at')} AS received_at,
                   latitude, longitude, current_status,
                   current_stop_id, speed_kmh, bearing, quality_flags
            FROM {_glob(raw_dir)}
            WHERE source_vehicle_id = $vehicle_id AND source_trip_id = $trip_id
            ORDER BY observed_at
            """,
            {"vehicle_id": vehicle_id, "trip_id": trip_id},
        )

    delays: list[dict[str, Any]] = []
    tu_dir = archive.raw_dir(RAW_TRIP_UPDATES_TABLE, service_date)
    if tu_dir.is_dir() and any(tu_dir.glob("**/*.parquet")):
        delays = _rows(
            f"""
            SELECT {_utc_iso('observed_at')} AS observed_at, delay_seconds, delay_coverage
            FROM {_glob(tu_dir)}
            WHERE source_trip_id = $trip_id
            ORDER BY observed_at
            """,
            {"trip_id": trip_id},
        )
    return {"circulation": header, "positions": positions, "delays": delays}


def station_metrics(
    archive: Archive, service_date: date, *, limit: int = 200
) -> list[dict[str, Any]]:
    """`station_daily_metrics` del día, de más observada a menos.

    Sigue sin incluir `data_quality_events_count` por la razón ya documentada
    en `services/snapshotter/gold.py` (DEC-033): `data_quality_event.entity_ref`
    nunca referencia una parada.
    """
    directory = archive.mart_dir(STATION_METRICS_MART, service_date)
    if not (directory.is_dir() and any(directory.glob("**/*.parquet"))):
        return []
    return _rows(
        f"""
        SELECT station_id, observations_count
        FROM {_glob(directory)}
        ORDER BY observations_count DESC, station_id
        LIMIT $limit
        """,
        {"limit": limit},
    )
