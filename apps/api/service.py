"""Lógica de negocio: combina PostgreSQL con packages.gtfs/geo/movement."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import psycopg

from packages.contracts.canonical import TripUpdateObservation
from packages.movement import MovementPosition, PositionMode

from . import db
from .gtfs_source import LoadedNetwork
from .schemas import (
    DelayOut,
    FeedHealthOut,
    HealthOut,
    LineOut,
    ObservationOut,
    PositionOut,
    QualityOut,
    StationOut,
    VehicleOut,
)

_MODE_VALUES = {mode.value for mode in PositionMode}
_MADRID = ZoneInfo("Europe/Madrid")


def _service_date(now: datetime) -> date:
    """Fecha de servicio GTFS: calendario de Europe/Madrid, nunca UTC directo.

    Hallazgo de la revisión de Codex: `packages.movement.schedule.service_seconds`
    ya interpreta `service_date` como una fecha de calendario Europe/Madrid (ver
    `docs/DATA_MODEL.md`: "service_date es la fecha de servicio en Europe/Madrid,
    no UTC"), pero una versión anterior le pasaba `now.astimezone(timezone.utc).date()`
    -- la fecha UTC. Cerca de medianoche (p. ej. `2026-11-19T23:30Z` = `2026-11-20
    00:30` CET) ambas difieren en un día, desplazando el horario esperado. Mismo
    tipo de hallazgo ya documentado para MP-009 (DEC-021, huso horario del
    exportador histórico).
    """
    return now.astimezone(_MADRID).date()


def _movement_position(
    network: LoadedNetwork,
    history: db.VehicleHistory,
    route_id: str,
    now: datetime,
) -> MovementPosition | None:
    try:
        return network.engine.position(
            trip_id=history.latest.position.source_trip_id,
            service_date=_service_date(now),
            calculated_at=now,
            latest=history.latest.position,
            previous=history.previous.position if history.previous is not None else None,
            explicit_route_id=route_id,
        )
    except ValueError:
        # Horario inválido (p. ej. trip sin >=2 stop_times resolubles en el
        # GTFS cargado) -- se expone sin posición, no se oculta el vehículo.
        return None


def vehicle_to_out(
    network: LoadedNetwork,
    history: db.VehicleHistory,
    trip_update: TripUpdateObservation | None,
    now: datetime,
) -> VehicleOut:
    source_trip_id = history.latest.position.source_trip_id
    route_id = network.topology.resolve_trip_route_id(source_trip_id)
    route = (
        network.topology.resolve_trip_route(source_trip_id, explicit_route_id=route_id)
        if route_id
        else None
    )

    movement = _movement_position(network, history, route_id, now) if route_id else None

    # La edad de la OBSERVACIÓN cruda es siempre calculable a partir de su
    # propio timestamp, se resuelva o no una posición -- hallazgo de la
    # revisión de Codex: antes solo se rellenaba cuando `movement` existía,
    # dejando `age_s=None` para los 20/24 vehículos reales que no son C5
    # aunque sí conocemos cuándo se observaron. `movement.age_s` puede
    # referirse a una muestra distinta (fallback recursivo a la última
    # observación plausible en engine.py); `age_s` de la respuesta describe
    # siempre `observation.reported_at`, no la posición mostrada.
    age_s = max(0.0, (now - history.latest.position.observed_at).total_seconds())

    position_out: PositionOut | None = None
    stale = True
    flags: list[str] = []
    if movement is not None:
        position_out = PositionOut(
            lat=movement.latitude,
            lon=movement.longitude,
            mode=movement.position_mode.value,
            confidence=movement.confidence,
        )
        stale = movement.position_mode in (PositionMode.STALE, PositionMode.SCHEDULED)
        flags = [anomaly.flag for anomaly in movement.anomalies]

    delay_seconds = None
    delay_coverage: str = "missing"
    if trip_update is not None:
        delay_seconds = trip_update.delay_seconds
        delay_coverage = trip_update.delay_coverage

    return VehicleOut(
        vehicle_id=history.source_vehicle_id,
        trip_id=source_trip_id,
        route_id=route_id,
        line=route.short_name if route is not None else None,
        position=position_out,
        delay=DelayOut(seconds=delay_seconds, coverage=delay_coverage),
        observation=ObservationOut(
            reported_at=history.latest.position.observed_at,
            received_at=history.latest.received_at,
            age_s=age_s,
        ),
        quality=QualityOut(stale=stale, flags=flags),
    )


def list_vehicles(conn: psycopg.Connection, network: LoadedNetwork, now: datetime) -> list[VehicleOut]:
    histories = db.latest_vehicle_histories(conn)
    result = []
    for history in histories:
        trip_update = db.latest_trip_update(conn, history.latest.position.source_trip_id)
        result.append(vehicle_to_out(network, history, trip_update, now))
    return result


def get_vehicle(
    conn: psycopg.Connection, network: LoadedNetwork, vehicle_id: str, now: datetime
) -> VehicleOut | None:
    history = db.vehicle_history(conn, vehicle_id)
    if history is None:
        return None
    trip_update = db.latest_trip_update(conn, history.latest.position.source_trip_id)
    return vehicle_to_out(network, history, trip_update, now)


def feed_health(conn: psycopg.Connection, now: datetime, *, stale_after_s: float) -> HealthOut:
    runs = db.recent_ingestion_runs(conn)
    by_feed: dict[str, list[db.FeedRunSample]] = {}
    for run in runs:
        by_feed.setdefault(run.feed_name, []).append(run)

    feeds: list[FeedHealthOut] = []
    for feed_name, samples in by_feed.items():
        samples.sort(key=lambda item: item.started_at, reverse=True)
        latest = samples[0]
        data_age_s = (now - latest.started_at).total_seconds()
        unchanged_for_s = 0.0
        for sample in samples[1:]:
            if sample.payload_hash != latest.payload_hash:
                break
            unchanged_for_s = (now - sample.started_at).total_seconds()
        if latest.status == "error":
            status = "error"
        elif data_age_s > stale_after_s:
            status = "stale"
        else:
            status = "ok"
        rejected = sum(1 for sample in samples if sample.status == "error")
        feeds.append(
            FeedHealthOut(
                feed_name=feed_name,
                status=status,
                source_timestamp=latest.started_at,
                data_age_s=data_age_s,
                unchanged_for_s=unchanged_for_s,
                entities=latest.entity_count,
                rejected=rejected,
            )
        )
    feeds.sort(key=lambda item: item.feed_name)
    return HealthOut(feeds=feeds)


def list_lines(network: LoadedNetwork) -> list[LineOut]:
    return [
        LineOut(
            line_id=short_name,
            network_id=network_id or "",
            route_ids=sorted(route.route_id for route in routes),
        )
        for (network_id, short_name), routes in sorted(network.topology.route_groups().items())
    ]


def get_line(network: LoadedNetwork, line_id: str) -> LineOut | None:
    for line in list_lines(network):
        if line.line_id == line_id:
            return line
    return None


def list_stations(network: LoadedNetwork) -> list[StationOut]:
    return [
        StationOut(station_id=stop.stop_id, name=stop.name, lat=stop.latitude, lon=stop.longitude)
        for stop in sorted(network.topology.stops, key=lambda item: item.stop_id)
    ]


def get_station(network: LoadedNetwork, station_id: str) -> StationOut | None:
    for stop in network.topology.stops:
        if stop.stop_id == station_id:
            return StationOut(
                station_id=stop.stop_id, name=stop.name, lat=stop.latitude, lon=stop.longitude
            )
    return None
