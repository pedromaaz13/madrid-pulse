"""Histórico consultable **por circulación** (MP-021).

`daily_line_metrics` y `station_daily_metrics` (MP-015, `gold.py`) agregan el
día por ruta y por estación. Ninguna de las dos responde la pregunta que abre
el histórico desde Live: *"esta circulación concreta -- este vehículo, en este
viaje, en este día de servicio -- qué hizo"*. Este módulo calcula ese grano.

**Identidad.** La misma que fijaron MP-017/MP-019/MP-020 y que viaja en la URL
del frontend (`?train=&trip=&sd=`): vehículo + viaje + día de servicio, nunca
`vehicle_id` a secas (un mismo tren encadena servicios distintos el mismo
día). Por eso una fila de este mart se puede abrir en Live y al revés, sin
traducir ninguna clave.

**Los huecos son filas, no ausencias.** El mart es la unión completa de dos
conjuntos, y cada fila dice a cuál pertenece:

- `scheduled`: el viaje figura en el GTFS estático para ese día de servicio,
  aplicando `calendar.txt` + `calendar_dates.txt` (vía
  `services.snapshotter.gold.scheduled_trip_ids_by_route`).
- `observed`: existe al menos una `vehicle_position_observation` real de ese
  vehículo en ese viaje. Es **cobertura de posición**, no "sabemos algo del
  viaje": el operador puede publicar una actualización de viaje sin que haya
  ninguna posición GPS.

Una circulación observada cuyo `trip_id` no está en el calendario de ese día
aparece con `scheduled=false, observed=true`: una observación real no se oculta
porque el calendario no la esperase -- se marca como lo que es, un viaje
observado fuera de programación (o un desajuste real entre feed en vivo y GTFS
estático, que es precisamente lo que un histórico debe dejar ver).

**No todo lo que no se ve es un hueco: `coverage` (MP-021, segunda ronda).**
La primera versión de este mart clasificaba como "programada sin observar"
cualquier viaje sin posición, y afirmaba que todas sus métricas eran `NULL`.
Las dos cosas eran falsas, y la revisión de Codex las encontró en el Parquet
real del `2026-11-20`: tres viajes (`1023V20865C5`, `1023V21340C10`,
`1023V21748C2`) salían como huecos con `trip_updates_count = 1` y
`delay_reported_count = 0`. Al mirar el origen, los tres tenían una
`trip_update_observation` real con `schedule_relationship = 'CANCELED'` y
ninguna posición: **Renfe había anulado ese servicio**. No eran un fallo de
captura nuestro; eran un hecho operativo que el operador nos comunicó, y
contarlos como hueco de cobertura culpaba a nuestro colector de un tren que
nunca salió. `apps/api/snapshot.py` ya trataba la cancelación como ciudadana de
primera (ETA `trip_canceled`, MP-019); este mart la ignoraba.

`coverage` clasifica cada fila en **una sola** categoría, por orden de
prioridad, para que ningún consumidor tenga que rederivarla:

| `coverage` | Qué significa |
|---|---|
| `unscheduled` | Observada, pero su `trip_id` no está en el calendario del día |
| `observed` | Programada y con al menos una posición real |
| `canceled` | Programada, sin posición, y el operador la declaró `CANCELED`: el tren no circuló |
| `operator_only` | Programada, sin posición, pero con actualización de viaje: el operador la conocía y nunca la localizamos |
| `unobserved` | Programada y **ni una sola señal**: el hueco de cobertura de verdad |

`canceled` se publica además como columna booleana propia, porque una
circulación puede estar anulada *y* tener posiciones (dato real y llamativo que
no debe quedar escondido bajo una categoría).

**Qué es `NULL` y qué es un cero medido.** La regla no es "todo `NULL` si no se
observó", que era la afirmación equivocada; es **cada métrica junto al
denominador que la sostiene**:

- métricas de posición (`positions_count`, `first_observed_at`,
  `last_observed_at`, `distinct_stops_observed`, `last_current_status`) son
  `NULL` exactamente cuando `observed = false`;
- métricas de actualización de viaje (`trip_updates_count`,
  `delay_reported_count`) son `NULL` exactamente cuando no hubo ninguna
  actualización. Si la hubo, `delay_reported_count = 0` es un **cero medido**
  -- hubo actualización y no traía retraso -- y no un dato ausente; es
  justamente lo que ocurre con una cancelación, porque el feed real no publica
  `delay` cuando `scheduleRelationship` es `CANCELED` (ver
  `packages/contracts/raw.py`);
- `latest_reported_delay_seconds` y `on_time` son `NULL` cuando
  `delay_reported_count` es `NULL` o `0`: sin muestra no hay veredicto, nunca
  `false`.

Como `gold.py`, lee únicamente el Parquet ya exportado (nunca vuelve a
PostgreSQL) y escribe con `ORDER BY` explícito, para que reprocesar el mismo
día produzca un fichero byte-idéntico.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb

from packages.gtfs import Topology

from .gold import GoldSummaryResult, GoldThresholds, _parquet_glob_or_empty, scheduled_trip_ids_by_route

MART_NAME = "circulation_daily_history"


@dataclass(frozen=True)
class ScheduledTripRow:
    """Fila de contexto programado de un viaje, tal como la necesita el mart.

    Los cuatro campos de horario son `None` cuando el viaje no tiene
    `stop_times` -- ver `scheduled_trip_rows`.
    """

    route_id: str
    line_short_name: str
    trip_id: str
    headsign: str
    first_stop_id: str | None
    first_departure_time: str | None
    last_stop_id: str | None
    last_arrival_time: str | None


def scheduled_trip_rows(topology: Topology, service_date: date) -> list[ScheduledTripRow]:
    """Contexto programado de cada viaje del día: ruta, línea, cabecera y extremos.

    **Un viaje sin `stop_times` sigue siendo una fila**, con sus cuatro campos
    de horario en `None`. Es la misma regla que gobierna todo el mart: lo que
    no se puede situar se marca, no se descarta. Omitirlo tendría una
    consecuencia concreta y mala -- el día tendría dos denominadores distintos:
    `daily_line_metrics.trips_scheduled` cuenta esos viajes (su `trip_id` puede
    aparecer perfectamente en el feed en vivo, que no depende de
    `stop_times.txt`) y este mart no los contaría. Medido con el ZIP oficial
    del `2026-11-20`: 5 viajes huérfanos reales (`1023V17120C8b`,
    `1023V17128C8b`, `1023V17130C8b`, `1023V17134C8b`, `1023V17707C5`) hacían
    que la misma pantalla mostrase 1304 programados en una tabla y 1299 en
    otra.

    Nota sobre MP-017: `packages.gtfs.scheduled_trip_instances_for_date` sí los
    omite, y con razón -- allí una instancia **es** una ocurrencia situada en el
    tiempo, y fabricarle horas sería inventar. Aquí no se inventa nada: la fila
    existe con el horario explícitamente ausente. `validate_topology` ya los
    señala como huérfanos.
    """
    by_route = scheduled_trip_ids_by_route(topology, service_date)
    short_names = {route.route_id: route.short_name for route in topology.routes}
    headsigns = {trip.trip_id: trip.headsign for trip in topology.trips}
    rows: list[ScheduledTripRow] = []
    for route_id, trip_ids in by_route.items():
        for trip_id in trip_ids:
            times = topology.stop_times_for_trip(trip_id)
            rows.append(
                ScheduledTripRow(
                    route_id=route_id,
                    line_short_name=short_names.get(route_id, ""),
                    trip_id=trip_id,
                    headsign=headsigns.get(trip_id, ""),
                    first_stop_id=times[0].stop_id if times else None,
                    first_departure_time=times[0].departure_time if times else None,
                    last_stop_id=times[-1].stop_id if times else None,
                    last_arrival_time=times[-1].arrival_time if times else None,
                )
            )
    return rows


def build_circulation_daily_history(
    raw_output_dir: Path,
    service_date: date,
    gold_output_dir: Path,
    topology: Topology,
    thresholds: GoldThresholds = GoldThresholds(),
) -> GoldSummaryResult:
    """Calcula `circulation_daily_history` del día (ver docstring del módulo)."""
    con = duckdb.connect()
    try:
        vp_dir = raw_output_dir / "raw" / "vehicle_position_observation" / f"date={service_date}"
        tu_dir = raw_output_dir / "raw" / "trip_update_observation" / f"date={service_date}"
        vp_source = _parquet_glob_or_empty(
            con,
            vp_dir,
            "NULL::VARCHAR AS source_vehicle_id, NULL::VARCHAR AS source_trip_id, "
            "NULL::TIMESTAMPTZ AS observed_at, NULL::VARCHAR AS current_stop_id, "
            "NULL::VARCHAR AS current_status",
        )
        tu_source = _parquet_glob_or_empty(
            con,
            tu_dir,
            "NULL::VARCHAR AS source_trip_id, NULL::INTEGER AS delay_seconds, "
            "NULL::VARCHAR AS delay_coverage, NULL::TIMESTAMPTZ AS observed_at, "
            "NULL::VARCHAR AS schedule_relationship",
        )

        con.execute(
            """
            CREATE TEMP TABLE scheduled_trips (
                route_id VARCHAR, line_short_name VARCHAR, trip_id VARCHAR, headsign VARCHAR,
                first_stop_id VARCHAR, first_departure_time VARCHAR,
                last_stop_id VARCHAR, last_arrival_time VARCHAR
            )
            """
        )
        rows = scheduled_trip_rows(topology, service_date)
        if rows:
            con.executemany(
                "INSERT INTO scheduled_trips VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        row.route_id, row.line_short_name, row.trip_id, row.headsign,
                        row.first_stop_id, row.first_departure_time,
                        row.last_stop_id, row.last_arrival_time,
                    )
                    for row in rows
                ],
            )

        output_path = gold_output_dir / "gold" / MART_NAME / f"date={service_date}"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / "part.parquet"

        # `observed_circulations` es el grano de identidad real: una fila por
        # (vehículo, viaje). `trip_delays` se agrega por viaje porque
        # `trip_update_observation` no trae `source_vehicle_id` -- el retraso lo
        # publica el operador contra el VIAJE, no contra el tren, y repetirlo en
        # cada vehículo del mismo viaje sería atribuir un dato que la fuente no
        # da por vehículo.
        query = f"""
        WITH observed_circulations AS (
            SELECT
                source_vehicle_id,
                source_trip_id,
                count(*) AS positions_count,
                min(observed_at) AS first_observed_at,
                max(observed_at) AS last_observed_at,
                count(DISTINCT current_stop_id) AS distinct_stops_observed,
                arg_max(current_status, observed_at) AS last_current_status
            FROM {vp_source}
            WHERE source_vehicle_id IS NOT NULL AND source_trip_id IS NOT NULL
            GROUP BY source_vehicle_id, source_trip_id
        ),
        trip_delays AS (
            SELECT
                source_trip_id,
                count(*) AS trip_updates_count,
                count(*) FILTER (WHERE delay_coverage = 'reported') AS delay_reported_count,
                arg_max(delay_seconds, observed_at) FILTER (WHERE delay_coverage = 'reported')
                    AS latest_reported_delay_seconds,
                -- Una sola actualización que declare CANCELED basta para que el
                -- viaje quede anulado: el operador no la retira publicando
                -- después otra sin esa marca.
                bool_or(upper(coalesce(schedule_relationship, '')) = 'CANCELED') AS canceled
            FROM {tu_source}
            WHERE source_trip_id IS NOT NULL
            GROUP BY source_trip_id
        )
        SELECT
            $service_date AS service_date,
            coalesce(s.route_id, '') AS route_id,
            coalesce(s.line_short_name, '') AS line_short_name,
            coalesce(s.trip_id, o.source_trip_id) AS trip_id,
            o.source_vehicle_id AS vehicle_id,
            (s.trip_id IS NOT NULL) AS scheduled,
            (o.source_vehicle_id IS NOT NULL) AS observed,
            s.headsign AS headsign,
            s.first_stop_id AS scheduled_first_stop_id,
            s.first_departure_time AS scheduled_first_departure_time,
            s.last_stop_id AS scheduled_last_stop_id,
            s.last_arrival_time AS scheduled_last_arrival_time,
            o.positions_count AS positions_count,
            o.first_observed_at AS first_observed_at,
            o.last_observed_at AS last_observed_at,
            o.distinct_stops_observed AS distinct_stops_observed,
            o.last_current_status AS last_current_status,
            d.trip_updates_count AS trip_updates_count,
            d.delay_reported_count AS delay_reported_count,
            d.latest_reported_delay_seconds AS latest_reported_delay_seconds,
            CASE
                WHEN coalesce(d.delay_reported_count, 0) = 0 THEN NULL
                ELSE abs(d.latest_reported_delay_seconds) <= $on_time_threshold
            END AS on_time,
            -- `NULL` cuando no hay ninguna actualización de viaje: no es que no
            -- esté anulada, es que no lo sabemos.
            d.canceled AS canceled,
            CASE
                WHEN s.trip_id IS NULL THEN 'unscheduled'
                WHEN o.source_vehicle_id IS NOT NULL THEN 'observed'
                WHEN coalesce(d.canceled, FALSE) THEN 'canceled'
                WHEN d.trip_updates_count IS NOT NULL THEN 'operator_only'
                ELSE 'unobserved'
            END AS coverage
        FROM scheduled_trips s
        FULL OUTER JOIN observed_circulations o ON o.source_trip_id = s.trip_id
        LEFT JOIN trip_delays d ON d.source_trip_id = coalesce(s.trip_id, o.source_trip_id)
        ORDER BY line_short_name, route_id, trip_id, vehicle_id NULLS LAST
        """
        con.execute(
            f"COPY ({query}) TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)",
            {
                "service_date": service_date.isoformat(),
                "on_time_threshold": thresholds.on_time_threshold_seconds,
            },
        )
        (row_count,) = con.execute(
            f"SELECT count(*) FROM read_parquet('{output_file}')"
        ).fetchone()
        return GoldSummaryResult(row_count=row_count, output_path=output_path)
    finally:
        con.close()
