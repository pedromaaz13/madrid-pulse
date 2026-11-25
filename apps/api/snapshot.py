"""Snapshot coherente, catálogo cacheable y tablero de estación — ADR-0014.

Tres responsabilidades separadas a propósito:

1. **Catálogo** (`build_catalog_payload`): líneas, patrones, estaciones y
   geometría con su cobertura honesta. Inmutable por proceso, versionado,
   cacheable con `ETag`. No contiene ni un dato operativo.
2. **Snapshot operativo** (`build_snapshot`): lo que cambia con cada sondeo.
   Ligero, referencia el catálogo por versión, publica `raw`/`map_matched`/
   `rendered` con procedencia, identidad `snapshot_id` separada de una revisión
   ordenable solo dentro de su ámbito, y la degradación por recurso.
3. **Tablero** (`build_station_board`): servicios programados del día de
   servicio (calendario + excepciones + `stop_times`) cruzados con
   actualizaciones del operador y observaciones. Nunca "trenes cercanos".

Ninguna de las tres escribe en PostgreSQL ni archiva una coordenada
`rendered` como observación de origen.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import psycopg

from packages.contracts.canonical import TripUpdateObservation
from packages.geo import CorridorCoverage, CoverageStatus, PositionResolution, corridor_length_m
from packages.gtfs import OPERATOR, scheduled_trip_instances_for_date
from packages.movement import (
    AnchorSample,
    MovementPosition,
    RenderedPosition,
    RenderingMethod,
    parse_gtfs_time,
    render_from_movement,
    render_raw_anchor,
    render_unlocated,
    service_day_instant,
)

from . import db, service
from .config import ApiConfig
from .gtfs_source import LoadedNetwork
from .schemas import (
    BoardCoverageOut,
    BoardEntryOut,
    CatalogGeometryOut,
    CatalogLineOut,
    CatalogOut,
    CatalogRefOut,
    CoordinateOut,
    CoverageSummaryOut,
    EtaOut,
    GtfsStatus,
    GtfsValidityOut,
    MapMatchedOut,
    PatternGeometryOut,
    PatternOut,
    PatternStationOut,
    PositionOut,
    ProgressEnvelopeOut,
    QualityOut,
    RawPositionOut,
    RenderedOut,
    SnapshotCountsOut,
    SnapshotDegradationOut,
    SnapshotDelayOut,
    SnapshotOut,
    SnapshotRevisionOut,
    SnapshotVehicleOut,
    StationBoardOut,
    StationOut,
    VehicleTimestampsOut,
)

MADRID = ZoneInfo("Europe/Madrid")

RAW_POSITION_SOURCE = "renfe_gtfs_rt_vehicle_position"

TRIP_LEVEL_DELAY_APPROXIMATION = "trip_level_delay_applied_to_all_stops"

BOARD_LIMITATIONS = (
    "El modelo canónico no persiste `stop_time_update` por parada (solo "
    "`next_stop_id`, el primer no-SKIPPED): no existe evidencia directa de "
    "`SKIPPED` por parada y el tablero no afirma que una parada concreta fue "
    "omitida. `relative_to_operator_next` es una señal derivada, declarada.",
    "El `delay` del feed es de nivel viaje; aplicarlo a cada parada es una "
    "aproximación declarada en `approximation`, no una predicción por parada.",
    "No se introduce ningún modelo predictivo propio: `eta_method` nunca es un "
    "cálculo distinto de horario o horario+retraso del operador.",
    "La conversión de horas GTFS a instantes UTC es la inversa exacta de "
    "`packages.movement.schedule.service_seconds` (segundos reales desde la "
    "medianoche local de la fecha de servicio), no la convención GTFS "
    "`mediodía menos 12 h`: en el día de cambio de hora ambas difieren.",
)


# --------------------------------------------------------------------------
# Catálogo cacheable
# --------------------------------------------------------------------------


def build_catalog_payload(
    network: LoadedNetwork, validity: GtfsValidityOut
) -> CatalogOut:
    geometries: dict[str, CatalogGeometryOut] = {}
    lines: list[CatalogLineOut] = []
    stops_by_id = {stop.stop_id: stop for stop in network.topology.stops}
    counts = {status: 0 for status in CoverageStatus}

    coverage_by_line: dict[str, list[CorridorCoverage]] = {}
    for entry in network.corridor_catalog.entries:
        coverage_by_line.setdefault(entry.line_id, []).append(entry)
        counts[entry.status] += 1

    for line in network.catalog.lines:
        patterns: list[PatternOut] = []
        for entry in coverage_by_line.get(line.short_name, ()):
            if (
                entry.can_map_match
                and entry.geometry_version is not None
                and entry.geometry_version not in geometries
                and entry.corridor is not None
                and entry.relation_id is not None
            ):
                geometries[entry.geometry_version] = CatalogGeometryOut(
                    geometry_version=entry.geometry_version,
                    relation_id=entry.relation_id,
                    attribution=entry.attribution or "",
                    source_captured_at=entry.source_captured_at,
                    length_m=corridor_length_m(entry.corridor),
                    segments=[
                        [CoordinateOut(lat=lat, lon=lon) for lat, lon in segment]
                        for segment in entry.corridor.segments
                    ],
                )
            stations: list[PatternStationOut] = []
            for index, stop_id in enumerate(entry.identity.stop_ids, start=1):
                stop = stops_by_id.get(stop_id)
                if stop is None:
                    continue
                distance_along_m: float | None = None
                if entry.can_map_match and entry.corridor is not None:
                    _, distance_along_m = entry.corridor.project_station(
                        stop.latitude, stop.longitude
                    )
                stations.append(
                    PatternStationOut(
                        station_id=stop.stop_id,
                        name=stop.name,
                        lat=stop.latitude,
                        lon=stop.longitude,
                        stop_sequence=index,
                        distance_along_m=distance_along_m,
                    )
                )
            patterns.append(
                PatternOut(
                    pattern_id=entry.identity.pattern_id,
                    route_id=entry.identity.route_id,
                    direction_key=entry.identity.direction_key,
                    origin_stop_id=entry.identity.origin_stop_id,
                    destination_stop_id=entry.identity.destination_stop_id,
                    stop_ids=list(entry.identity.stop_ids),
                    trip_count=entry.trip_count,
                    geometry=PatternGeometryOut(
                        status=entry.status.value,
                        reason=entry.reason,
                        geometry_version=entry.geometry_version,
                        relation_id=entry.relation_id,
                        max_stop_distance_m=entry.max_stop_distance_m,
                        source_captured_at=entry.source_captured_at,
                        attribution=entry.attribution,
                        can_map_match=entry.can_map_match,
                    ),
                    stations=stations,
                )
            )
        lines.append(
            CatalogLineOut(
                line_id=line.short_name,
                network_id=line.network_id,
                operator=OPERATOR,
                route_ids=list(line.route_ids),
                patterns=patterns,
            )
        )

    return CatalogOut(
        **validity.model_dump(),
        catalog_version=network.catalog_version,
        gtfs_version=network.gtfs_version,
        geometry_catalog_version=network.geometry_catalog_version,
        gtfs_valid_from=network.gtfs_valid_from.isoformat(),
        gtfs_valid_until=network.gtfs_valid_until.isoformat(),
        mode=network.mode,  # type: ignore[arg-type]
        operator=OPERATOR,
        lines=lines,
        stations=[
            StationOut(
                station_id=stop.stop_id, name=stop.name, lat=stop.latitude, lon=stop.longitude
            )
            for stop in sorted(network.topology.stops, key=lambda item: item.stop_id)
        ],
        geometries=sorted(geometries.values(), key=lambda item: item.geometry_version),
        coverage=CoverageSummaryOut(
            total_patterns=len(network.corridor_catalog.entries),
            validated=counts[CoverageStatus.VALIDATED],
            partial=counts[CoverageStatus.PARTIAL],
            pending=counts[CoverageStatus.PENDING],
        ),
    )


def catalog_ref(network: LoadedNetwork) -> CatalogRefOut:
    return CatalogRefOut(
        catalog_version=network.catalog_version,
        gtfs_version=network.gtfs_version,
        geometry_catalog_version=network.geometry_catalog_version,
    )


# --------------------------------------------------------------------------
# Resolución de patrón y posición
# --------------------------------------------------------------------------


def coverage_for_trip(
    network: LoadedNetwork, trip_id: str, route_id: str | None
) -> CorridorCoverage | None:
    """Patrón catalogado de una circulación viva, por identidad real.

    La identidad es ``route_id`` + secuencia ordenada de ``stop_id`` del
    ``trip_id`` (MP-018 no inventa ``direction_id`` porque el GTFS de Renfe no
    lo publica). Un refuerzo sin trip estático, o un trip ausente de la fixture
    cargada, devuelve ``None``.
    """
    if route_id is None:
        return None
    times = network.topology.stop_times_for_trip(trip_id)
    if not times:
        return None
    stop_ids = tuple(item.stop_id for item in times)
    return network.corridor_catalog.coverage_for_stops(route_id, stop_ids)


def _legacy_position(movement: MovementPosition | None) -> PositionOut | None:
    if movement is None:
        return None
    return PositionOut(
        lat=movement.latitude,
        lon=movement.longitude,
        mode=movement.position_mode.value,
        confidence=movement.confidence,
    )


def _envelope_out(rendered: RenderedPosition) -> ProgressEnvelopeOut | None:
    envelope = rendered.progress_envelope
    if envelope is None:
        return None
    return ProgressEnvelopeOut(
        reference_at=envelope.reference_at,
        progress_m_at_reference=envelope.progress_m_at_reference,
        speed_mps=envelope.speed_mps,
        max_progress_m=envelope.max_progress_m,
        horizon_s=envelope.horizon_s,
        dwell_until=envelope.dwell_until,
    )


def _rendered_out(rendered: RenderedPosition) -> RenderedOut:
    return RenderedOut(
        rendering_method=rendered.rendering_method.value,  # type: ignore[arg-type]
        coordinate_space=(
            rendered.coordinate_space.value if rendered.coordinate_space is not None else None
        ),
        lat=rendered.latitude,
        lon=rendered.longitude,
        progress_m=rendered.progress_m,
        pattern_id=rendered.pattern_id,
        geometry_version=rendered.geometry_version,
        geometry_candidate_version=rendered.geometry_candidate_version,
        confidence_index=rendered.confidence_index,
        calculated_at=rendered.calculated_at,
        display_at=rendered.display_at,
        valid_until=rendered.valid_until,
        last_confirmed_at=rendered.last_confirmed_at,
        anchor_observed_at=rendered.anchor_observed_at,
        anchor_age_s=rendered.anchor_age_s,
        anchor_distance_from_raw_m=rendered.anchor_distance_from_raw_m,
        progress_envelope=_envelope_out(rendered),
        reason=rendered.reason,
    )


def _delay_out(
    trip_update: TripUpdateObservation | None, now: datetime, *, max_age_s: float
) -> SnapshotDelayOut:
    if trip_update is None:
        return SnapshotDelayOut(
            seconds=None,
            coverage="missing",
            observed_at=None,
            age_s=None,
            source=None,
            expired=False,
            approximation=None,
        )
    age_s = max(0.0, (now - trip_update.observed_at).total_seconds())
    reported = trip_update.delay_coverage == "reported"
    return SnapshotDelayOut(
        seconds=trip_update.delay_seconds,
        coverage=trip_update.delay_coverage,
        observed_at=trip_update.observed_at,
        age_s=age_s,
        source="operator_trip_update" if reported else None,
        expired=reported and age_s > max_age_s,
        approximation=TRIP_LEVEL_DELAY_APPROXIMATION if reported else None,
    )


def _render_vehicle(
    network: LoadedNetwork,
    history: db.VehicleHistory,
    coverage: CorridorCoverage | None,
    movement: MovementPosition | None,
    service_date: date,
    now: datetime,
    display_at: datetime,
) -> tuple[RenderedPosition, MapMatchedOut | None]:
    latest = history.latest.position
    pattern_id = coverage.identity.pattern_id if coverage is not None else None
    candidate_version = coverage.geometry_version if coverage is not None else None
    engine = network.engine_for(coverage) if coverage is not None else None

    match = None
    if pattern_id is not None:
        match = network.corridor_catalog.match_position(
            pattern_id, raw_lat=latest.latitude, raw_lon=latest.longitude
        )
    map_matched: MapMatchedOut | None = None
    if (
        match is not None
        and match.resolution is PositionResolution.MAP_MATCHED
        and match.projection is not None
        and match.progress_m is not None
        and match.geometry_version is not None
        and match.distance_from_raw_m is not None
    ):
        map_matched = MapMatchedOut(
            resolution="map_matched",
            lat=match.projection.lat,
            lon=match.projection.lon,
            progress_m=match.progress_m,
            distance_from_raw_m=match.distance_from_raw_m,
            pattern_id=pattern_id or "",
            geometry_version=match.geometry_version,
        )

    if movement is not None and engine is not None and coverage is not None:
        assert coverage.corridor is not None
        schedule = engine.trip_schedule(latest.source_trip_id)
        previous_anchor: AnchorSample | None = None
        if (
            display_at < latest.observed_at
            and history.previous is not None
            and history.previous.position.source_trip_id == latest.source_trip_id
        ):
            previous_match = engine.map_match(history.previous.position)
            if previous_match is not None:
                previous_anchor = AnchorSample(
                    observed_at=history.previous.position.observed_at,
                    progress_m=schedule.directed_progress(previous_match.physical_arc_m),
                )
        rendered = render_from_movement(
            movement,
            schedule=schedule,
            corridor=coverage.corridor,
            service_date=service_date,
            display_at=display_at,
            pattern_id=pattern_id,
            geometry_version=coverage.geometry_version,
            thresholds=engine.thresholds,
            previous_anchor=previous_anchor,
            anchor_distance_from_raw_m=(
                map_matched.distance_from_raw_m if map_matched is not None else None
            ),
        )
        return rendered, map_matched

    if latest.latitude is not None and latest.longitude is not None:
        reason = (
            match.reason
            if match is not None and match.reason
            else "patrón no catalogado en el GTFS cargado: GPS bruto etiquetado"
        )
        return (
            render_raw_anchor(
                raw_lat=latest.latitude,
                raw_lon=latest.longitude,
                observed_at=latest.observed_at,
                calculated_at=now,
                display_at=display_at,
                pattern_id=pattern_id,
                geometry_candidate_version=candidate_version,
                reason=reason,
            ),
            map_matched,
        )

    return (
        render_unlocated(
            calculated_at=now,
            display_at=display_at,
            pattern_id=pattern_id,
            geometry_candidate_version=candidate_version,
            reason=(
                match.reason
                if match is not None and match.reason
                else "sin posición bruta y sin corredor utilizable"
            ),
            observed_at=latest.observed_at,
        ),
        map_matched,
    )


def build_vehicle_entry(
    network: LoadedNetwork,
    config: ApiConfig,
    history: db.VehicleHistory,
    trip_update: TripUpdateObservation | None,
    now: datetime,
    display_at: datetime,
    resolver: service.ServiceDateResolver,
) -> SnapshotVehicleOut:
    latest = history.latest.position
    source_trip_id = latest.source_trip_id
    # Por circulación, no por reloj civil: un viaje `24:xx` del día de servicio
    # anterior sigue siendo suyo tras la medianoche (ver `ServiceDateResolver`).
    service_date = resolver.for_trip(source_trip_id)
    route_id = network.topology.resolve_trip_route_id(source_trip_id)
    route = (
        network.topology.resolve_trip_route(source_trip_id, explicit_route_id=route_id)
        if route_id
        else None
    )
    coverage = coverage_for_trip(network, source_trip_id, route_id)
    movement = (
        _movement_for(network, coverage, history, route_id, now, service_date)
        if route_id
        else None
    )
    rendered, map_matched = _render_vehicle(
        network, history, coverage, movement, service_date, now, display_at
    )

    stale = rendered.rendering_method in (
        RenderingMethod.STALE_FROZEN,
        RenderingMethod.SCHEDULE_ONLY,
        RenderingMethod.UNLOCATED,
    )
    flags = [anomaly.flag for anomaly in movement.anomalies] if movement is not None else []

    return SnapshotVehicleOut(
        vehicle_id=history.source_vehicle_id,
        trip_id=source_trip_id,
        route_id=route_id,
        line=route.short_name if route is not None else None,
        pattern_id=coverage.identity.pattern_id if coverage is not None else None,
        circulation_status=service._circulation_status(  # type: ignore[arg-type]
            network, source_trip_id, route_id, resolver.scheduled_service_ids(service_date)
        ),
        service_date=service_date.isoformat(),
        schedule_relationship=(
            trip_update.schedule_relationship if trip_update is not None else None
        ),
        timestamps=VehicleTimestampsOut(
            gps_observed_at=latest.observed_at,
            received_at=history.latest.received_at,
            feed_published_at=history.latest.feed_published_at,
            snapshot_generated_at=now,
            display_at=display_at,
        ),
        raw=RawPositionOut(
            lat=latest.latitude,
            lon=latest.longitude,
            source=RAW_POSITION_SOURCE,
            gps_observed_at=latest.observed_at,
            payload_hash=latest.payload_hash,
        ),
        map_matched=map_matched,
        rendered=_rendered_out(rendered),
        position=_legacy_position(movement),
        delay=_delay_out(trip_update, now, max_age_s=config.operator_delay_max_age_s),
        quality=QualityOut(stale=stale, flags=flags),
    )


def _movement_for(
    network: LoadedNetwork,
    coverage: CorridorCoverage | None,
    history: db.VehicleHistory,
    route_id: str,
    now: datetime,
    service_date: date,
) -> MovementPosition | None:
    engine = network.engine_for(coverage) if coverage is not None else None
    if engine is None:
        return None
    latest = history.latest.position
    previous = (
        history.previous.position
        if history.previous is not None
        and history.previous.position.source_trip_id == latest.source_trip_id
        else None
    )
    try:
        return engine.position(
            trip_id=latest.source_trip_id,
            service_date=service_date,
            calculated_at=now,
            latest=latest,
            previous=previous,
            explicit_route_id=route_id,
        )
    except ValueError:
        # Horario no resoluble sobre este corredor: se publica `raw`/`unlocated`
        # con causa, nunca una posición inventada.
        return None


# --------------------------------------------------------------------------
# Snapshot operativo
# --------------------------------------------------------------------------

def _degradations(health) -> list[SnapshotDegradationOut]:
    result: list[SnapshotDegradationOut] = []
    for feed in health.feeds:
        if feed.status == "ok":
            continue
        if feed.reason == "no_ingestion_at_or_before_clock":
            reason = f"sin ingesta para {feed.feed_name} hasta el instante de la petición"
        elif feed.reason == "source_timestamp_in_future":
            reason = f"la marca de origen de {feed.feed_name} es posterior al reloj de la petición"
        else:
            reason = (
                f"feed {feed.feed_name} en estado {feed.status}: se conserva el último "
                "resultado válido con su edad real, no se vacía el recurso ni se "
                "rejuvenece el dato"
            )
        result.append(
            SnapshotDegradationOut(
                resource=service.FEED_RESOURCES.get(feed.feed_name, feed.feed_name),
                feed_name=feed.feed_name,
                status=feed.status,
                reason=reason,
                last_valid_source_timestamp=(
                    None if feed.reason == "source_timestamp_in_future" else feed.source_timestamp
                ),
                data_age_s=feed.data_age_s,
                poll_age_s=feed.poll_age_s,
            )
        )
    return sorted(result, key=lambda item: (item.resource, item.feed_name or ""))


def _snapshot_identity(
    network: LoadedNetwork,
    marker: db.RevisionMarker,
    histories: list[db.VehicleHistory],
    trip_updates: dict[str, TripUpdateObservation],
    health,
    *,
    gtfs_status: GtfsStatus | None = None,
) -> str:
    """Identidad de **contenido**, no marca de tiempo.

    Dos snapshots generados en instantes distintos sobre exactamente los mismos
    datos tienen el mismo `snapshot_id`; por eso no es ordenable y por eso la
    ordenación vive en `revision`. No entra ni `generated_at` ni `display_at`.
    """
    digest = hashlib.sha256()
    digest.update(network.catalog_version.encode())
    if gtfs_status is not None:
        digest.update(f"\0{gtfs_status}\0".encode())
    digest.update(f"\0{marker.scope}\0{marker.sequence}\0".encode())
    for history in sorted(histories, key=lambda item: item.source_vehicle_id):
        digest.update(
            f"{history.source_vehicle_id}\0{history.latest.position.payload_hash}"
            f"\0{history.latest.position.observed_at.isoformat()}\0".encode()
        )
    for trip_id in sorted(trip_updates):
        digest.update(f"{trip_id}\0{trip_updates[trip_id].payload_hash}\0".encode())
    for feed in sorted(health.feeds, key=lambda item: item.feed_name):
        digest.update(f"{feed.feed_name}\0{feed.status}\0{feed.source_timestamp}\0".encode())
    return "sha256:" + digest.hexdigest()


def resolve_clock(config: ApiConfig, network: LoadedNetwork, at: datetime | None) -> datetime:
    """Reloj del snapshot: `at` solo se acepta en modo replay.

    En `live` un `at` arbitrario permitiría falsificar edades; se rechaza con
    `ValueError` (la capa HTTP lo convierte en 400). En `replay` el reloj
    explícito es exactamente lo que exige el anexo ("Replay con reloj y fecha
    propios") y la respuesta siempre publica el instante usado.
    """
    if at is None:
        return datetime.now(timezone.utc)
    if network.mode != "replay":
        raise ValueError("el parámetro 'at' solo se admite en modo replay")
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("'at' debe incluir zona horaria explícita (UTC recomendado)")
    return at.astimezone(timezone.utc)


def build_snapshot(
    conn: psycopg.Connection,
    network: LoadedNetwork,
    config: ApiConfig,
    now: datetime,
    *,
    display_lag_s: float | None = None,
) -> SnapshotOut:
    lag = config.display_lag_s if display_lag_s is None else display_lag_s
    display_at = now - timedelta(seconds=lag)
    resolver = network.service_date_resolver(now)

    validity = network.gtfs_validity(now, expiring_days=config.gtfs_expiring_days)
    histories = db.latest_vehicle_histories(conn, as_of=now)
    trip_updates = db.latest_trip_updates(
        conn,
        [history.latest.position.source_trip_id for history in histories],
        observed_after=service._trip_update_cutoff(now),
        as_of=now,
    )
    health = service.feed_health(conn, now, stale_after_s=config.feed_stale_after_s)
    marker = db.revision_marker(conn, as_of=now)

    vehicles = [
        build_vehicle_entry(
            network,
            config,
            history,
            trip_updates.get(history.latest.position.source_trip_id),
            now,
            display_at,
            resolver,
        )
        for history in sorted(histories, key=lambda item: item.source_vehicle_id)
    ]

    by_method: dict[str, int] = {}
    by_space: dict[str, int] = {}
    for vehicle in vehicles:
        method = vehicle.rendered.rendering_method
        by_method[method] = by_method.get(method, 0) + 1
        space = vehicle.rendered.coordinate_space or "none"
        by_space[space] = by_space.get(space, 0) + 1
    snapshot_id = _snapshot_identity(
        network, marker, histories, trip_updates, health, gtfs_status=validity.gtfs_status
    )
    return SnapshotOut(
        **validity.model_dump(),
        snapshot_id=snapshot_id,
        revision=SnapshotRevisionOut(
            scope=marker.scope,
            scope_source=marker.scope_source,  # type: ignore[arg-type]
            sequence=marker.sequence,
            generated_at=now,
            tiebreak=snapshot_id,
        ),
        mode=network.mode,  # type: ignore[arg-type]
        catalog_ref=catalog_ref(network),
        generated_at=now,
        display_at=display_at,
        feeds=health.feeds,
        degraded=_degradations(health),
        vehicles=vehicles,
        counts=SnapshotCountsOut(
            vehicles_total=len(vehicles),
            by_rendering_method=dict(sorted(by_method.items())),  # type: ignore[arg-type]
            by_coordinate_space=dict(sorted(by_space.items())),  # type: ignore[arg-type]
            with_operator_delay=sum(
                1 for vehicle in vehicles if vehicle.delay.coverage == "reported"
            ),
            without_operator_delay=sum(
                1 for vehicle in vehicles if vehicle.delay.coverage == "missing"
            ),
        ),
    )


# --------------------------------------------------------------------------
# Tablero de estación
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BoardCall:
    trip_id: str
    route_id: str
    line: str | None
    network_id: str | None
    headsign: str
    destination_stop_id: str
    stop_sequence: int
    arrival_time: str | None
    departure_time: str | None
    arrival_s: float | None
    departure_s: float | None
    stop_ids: tuple[str, ...]


def board_index(network: LoadedNetwork, service_date: date) -> dict[str, tuple[BoardCall, ...]]:
    """Índice `station_id` → llamadas programadas del día de servicio.

    Se construye una vez por fecha de servicio y se memoiza: es catálogo
    derivado (depende solo del GTFS cargado y de la fecha), no estado
    operativo. Parte de `scheduled_trip_instances_for_date`, la enumeración
    real de servicios programados -- no del fallback `scheduled` del motor,
    que solo resuelve un `trip_id` ya observado.
    """
    cached = network._board_indexes.get(service_date)
    if cached is not None:
        return cached
    routes_by_id = {route.route_id: route for route in network.topology.routes}
    index: dict[str, list[BoardCall]] = {}
    for instance in scheduled_trip_instances_for_date(network.topology, service_date):
        times = network.topology.stop_times_for_trip(instance.trip_id)
        stop_ids = tuple(item.stop_id for item in times)
        route = routes_by_id.get(instance.route_id)
        for position, item in enumerate(times, start=1):
            index.setdefault(item.stop_id, []).append(
                BoardCall(
                    trip_id=instance.trip_id,
                    route_id=instance.route_id,
                    line=route.short_name if route is not None else None,
                    network_id=instance.network_id,
                    headsign=instance.headsign,
                    destination_stop_id=instance.last_stop_id,
                    stop_sequence=position,
                    arrival_time=item.arrival_time or None,
                    departure_time=item.departure_time or None,
                    arrival_s=_gtfs_seconds(item.arrival_time),
                    departure_s=_gtfs_seconds(item.departure_time),
                    stop_ids=stop_ids,
                )
            )
    result = {
        station_id: tuple(
            sorted(calls, key=lambda call: (call.departure_s or call.arrival_s or 0.0))
        )
        for station_id, calls in index.items()
    }
    network._board_indexes[service_date] = result
    return result


def _gtfs_seconds(value: str | None) -> float | None:
    if not value:
        return None
    return parse_gtfs_time(value)


def service_instant(service_date: date, seconds: float | None) -> datetime | None:
    """Instante UTC de una hora GTFS, o `None` si la hora no existe en la fuente.

    Delega en `packages.movement.schedule.service_day_instant`, la **única**
    implementación de la aritmética del día de servicio: así la API y el motor
    de movimiento no pueden divergir en los días de cambio de hora, que es
    exactamente lo que ocurrió con la primera versión de MP-019 (ver el
    docstring de `service_seconds`).
    """
    if seconds is None:
        return None
    return service_day_instant(service_date, seconds)


def _relative_to_operator_next(
    call: BoardCall, next_stop_id: str | None
) -> tuple[str | None, str | None]:
    if next_stop_id is None:
        return None, None
    if next_stop_id not in call.stop_ids:
        return "unknown", next_stop_id
    next_index = call.stop_ids.index(next_stop_id) + 1
    if call.stop_sequence < next_index:
        return "before", next_stop_id
    if call.stop_sequence == next_index:
        return "at", next_stop_id
    return "after", next_stop_id


def build_eta(
    *,
    scheduled_at: datetime | None,
    trip_update: TripUpdateObservation | None,
    now: datetime,
    max_age_s: float,
    relative: str | None,
) -> EtaOut:
    canceled = (
        trip_update is not None
        and (trip_update.schedule_relationship or "").upper() == "CANCELED"
    )
    delay_observed_at = trip_update.observed_at if trip_update is not None else None
    delay_age_s = (
        max(0.0, (now - trip_update.observed_at).total_seconds())
        if trip_update is not None
        else None
    )
    reported = trip_update is not None and trip_update.delay_coverage == "reported"
    delay_seconds = trip_update.delay_seconds if reported else None

    if canceled:
        return EtaOut(
            method="unavailable",
            scheduled_at=scheduled_at,
            eta_at=None,
            delay_seconds=delay_seconds,
            delay_observed_at=delay_observed_at,
            delay_age_s=delay_age_s,
            approximation=None,
            reason="trip_canceled",
        )
    if scheduled_at is None:
        return EtaOut(
            method="unavailable",
            scheduled_at=None,
            eta_at=None,
            delay_seconds=delay_seconds,
            delay_observed_at=delay_observed_at,
            delay_age_s=delay_age_s,
            approximation=None,
            reason="schedule_time_missing",
        )
    if relative == "before":
        return EtaOut(
            method="unavailable",
            scheduled_at=scheduled_at,
            eta_at=None,
            delay_seconds=delay_seconds,
            delay_observed_at=delay_observed_at,
            delay_age_s=delay_age_s,
            approximation=None,
            reason="passed_or_skipped_per_operator_next_stop",
        )
    if reported and delay_age_s is not None and delay_age_s <= max_age_s:
        assert delay_seconds is not None
        return EtaOut(
            method="operator_delay_on_schedule",
            scheduled_at=scheduled_at,
            eta_at=scheduled_at + timedelta(seconds=delay_seconds),
            delay_seconds=delay_seconds,
            delay_observed_at=delay_observed_at,
            delay_age_s=delay_age_s,
            approximation=TRIP_LEVEL_DELAY_APPROXIMATION,
            reason=None,
        )
    if reported:
        return EtaOut(
            method="schedule",
            scheduled_at=scheduled_at,
            eta_at=scheduled_at,
            delay_seconds=delay_seconds,
            delay_observed_at=delay_observed_at,
            delay_age_s=delay_age_s,
            approximation=None,
            reason="operator_delay_expired",
        )
    return EtaOut(
        method="schedule",
        scheduled_at=scheduled_at,
        eta_at=scheduled_at,
        delay_seconds=None,
        delay_observed_at=delay_observed_at,
        delay_age_s=delay_age_s,
        approximation=None,
        reason=(
            "no_operator_delay_reported"
            if scheduled_at >= now
            else "no_operator_delay_reported;scheduled_time_already_elapsed"
        ),
    )


def build_station_board(
    conn: psycopg.Connection,
    network: LoadedNetwork,
    config: ApiConfig,
    station_id: str,
    now: datetime,
    *,
    lookback_s: float = 600.0,
    lookahead_s: float = 7200.0,
    limit: int = 20,
    display_lag_s: float | None = None,
) -> StationBoardOut | None:
    stop = next(
        (item for item in network.topology.stops if item.stop_id == station_id), None
    )
    if stop is None:
        return None
    lag = config.display_lag_s if display_lag_s is None else display_lag_s
    display_at = now - timedelta(seconds=lag)
    resolver = network.service_date_resolver(now)
    service_date = resolver.primary

    # Los días de servicio candidatos se derivan de la **ventana completa**
    # solicitada, no del instante `now`: una llamada `24:xx` del día anterior
    # sigue dentro de `lookback_s` después de que el horizonte del feed deje de
    # alcanzar `now`, y una llamada `00:0x` del día siguiente puede caer dentro
    # de `lookahead_s` antes de la medianoche. Calcularlos con `now` perdía las
    # dos (tercer hallazgo de la revisión de MP-019, ver
    # `service_dates_covering`). Cada llamada se convierte a instante absoluto
    # con su propio día de servicio, así que la ventana basta para
    # seleccionarlas y ninguna aparece dos veces.
    window_start = now - timedelta(seconds=lookback_s)
    window_end = now + timedelta(seconds=lookahead_s)
    candidates = resolver.dates_covering(window_start, window_end)
    selected: list[tuple[datetime, date, BoardCall]] = []
    for candidate in candidates:
        for call in board_index(network, candidate).get(station_id, ()):
            reference = service_instant(candidate, call.departure_s or call.arrival_s)
            if reference is None:
                continue
            if window_start <= reference <= window_end:
                selected.append((reference, candidate, call))
    selected.sort(key=lambda item: (item[0], item[2].trip_id))
    visible = selected[:limit]

    trip_ids = [call.trip_id for _, _, call in visible]
    trip_updates = db.latest_trip_updates(
        conn, trip_ids, observed_after=service._trip_update_cutoff(now), as_of=now
    )
    observed = db.vehicles_for_trips(conn, trip_ids, as_of=now)
    marker = db.revision_marker(conn, as_of=now)
    health = service.feed_health(conn, now, stale_after_s=config.feed_stale_after_s)

    entries: list[BoardEntryOut] = []
    for _, call_service_date, call in visible:
        trip_update = trip_updates.get(call.trip_id)
        next_stop_id = trip_update.next_stop_id if trip_update is not None else None
        relative, operator_next = _relative_to_operator_next(call, next_stop_id)
        arrival_at = service_instant(call_service_date, call.arrival_s)
        departure_at = service_instant(call_service_date, call.departure_s)
        sighting = observed.get(call.trip_id)
        entries.append(
            BoardEntryOut(
                trip_id=call.trip_id,
                service_date=call_service_date.isoformat(),
                route_id=call.route_id,
                line=call.line,
                network_id=call.network_id,
                operator=OPERATOR,
                headsign=call.headsign,
                destination_stop_id=call.destination_stop_id,
                stop_sequence=call.stop_sequence,
                scheduled_arrival_time=call.arrival_time,
                scheduled_departure_time=call.departure_time,
                scheduled_arrival_at=arrival_at,
                scheduled_departure_at=departure_at,
                arrival=build_eta(
                    scheduled_at=arrival_at,
                    trip_update=trip_update,
                    now=now,
                    max_age_s=config.operator_delay_max_age_s,
                    relative=relative,
                ),
                departure=build_eta(
                    scheduled_at=departure_at,
                    trip_update=trip_update,
                    now=now,
                    max_age_s=config.operator_delay_max_age_s,
                    relative=relative,
                ),
                circulation_source="observed" if sighting is not None else "scheduled_only",
                vehicle_id=sighting.source_vehicle_id if sighting is not None else None,
                position_available=(
                    sighting is not None and sighting.has_position
                ),
                schedule_relationship=(
                    trip_update.schedule_relationship if trip_update is not None else None
                ),
                operator_next_stop_id=operator_next,
                relative_to_operator_next=relative,  # type: ignore[arg-type]
            )
        )

    with_delay = sum(1 for entry in entries if entry.departure.delay_seconds is not None)
    snapshot_id = _snapshot_identity(network, marker, [], trip_updates, health)
    return StationBoardOut(
        station_id=stop.stop_id,
        name=stop.name,
        service_date=service_date.isoformat(),
        service_dates_considered=[item.isoformat() for item in candidates],
        mode=network.mode,  # type: ignore[arg-type]
        generated_at=now,
        display_at=display_at,
        revision=SnapshotRevisionOut(
            scope=marker.scope,
            scope_source=marker.scope_source,  # type: ignore[arg-type]
            sequence=marker.sequence,
            generated_at=now,
            tiebreak=snapshot_id,
        ),
        catalog_ref=catalog_ref(network),
        entries=entries,
        coverage=BoardCoverageOut(
            scheduled_calls=len(selected),
            returned=len(entries),
            observed_circulations=sum(
                1 for entry in entries if entry.circulation_source == "observed"
            ),
            with_operator_delay=with_delay,
            eta_from_operator=sum(
                1 for entry in entries if entry.departure.method == "operator_delay_on_schedule"
            ),
            eta_from_schedule=sum(
                1 for entry in entries if entry.departure.method == "schedule"
            ),
            eta_unavailable=sum(
                1 for entry in entries if entry.departure.method == "unavailable"
            ),
            operator_delay_coverage_pct=(
                round(100.0 * with_delay / len(entries), 2) if entries else None
            ),
        ),
        limitations=list(BOARD_LIMITATIONS),
    )
