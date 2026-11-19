"""Validación estructural y patrones de recorrido observados en GTFS."""

from __future__ import annotations

from dataclasses import dataclass

from .parser import Topology


@dataclass(frozen=True)
class RoutePattern:
    route_id: str
    stop_ids: tuple[str, ...]
    trip_count: int


@dataclass(frozen=True)
class TopologyValidation:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    patterns: tuple[RoutePattern, ...]
    orphan_trip_ids: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_topology(topology: Topology) -> TopologyValidation:
    """Valida referencias, orden y geometría sin inventar ``direction_id``.

    El feed real de Renfe observado en MP-010 no contiene esa columna en
    ``trips.txt``. La dirección disponible como verdad de fuente es, por tanto,
    el patrón ordenado de ``stop_sequence`` y el ``shape_id`` de cada trip.
    """
    errors: list[str] = []
    warnings: list[str] = []
    routes = {item.route_id for item in topology.routes}
    stops = {item.stop_id for item in topology.stops}
    services = {item.service_id for item in topology.calendar}
    shape_ids = {item.shape_id for item in topology.shape_points}
    patterns: dict[tuple[str, tuple[str, ...]], int] = {}
    orphan_trip_ids: list[str] = []

    for trip in topology.trips:
        if trip.route_id not in routes:
            errors.append(f"trip {trip.trip_id}: route_id desconocido {trip.route_id}")
        if trip.service_id not in services:
            errors.append(f"trip {trip.trip_id}: service_id desconocido {trip.service_id}")
        if trip.shape_id not in shape_ids:
            errors.append(f"trip {trip.trip_id}: shape_id desconocido {trip.shape_id}")
        times = topology.stop_times_for_trip(trip.trip_id)
        if not times:
            orphan_trip_ids.append(trip.trip_id)
            continue
        sequences = [item.stop_sequence for item in times]
        if any(right <= left for left, right in zip(sequences, sequences[1:])):
            errors.append(f"trip {trip.trip_id}: stop_sequence no es estrictamente creciente")
        unknown = sorted({item.stop_id for item in times if item.stop_id not in stops})
        if unknown:
            errors.append(f"trip {trip.trip_id}: stop_id desconocidos {unknown}")
        pattern = tuple(item.stop_id for item in times)
        key = (trip.route_id, pattern)
        patterns[key] = patterns.get(key, 0) + 1

    points_by_shape: dict[str, list[int]] = {}
    for point in topology.shape_points:
        points_by_shape.setdefault(point.shape_id, []).append(point.sequence)
    for shape_id, sequences in points_by_shape.items():
        ordered = sorted(sequences)
        if len(set(ordered)) != len(ordered):
            errors.append(f"shape {shape_id}: shape_pt_sequence duplicado")
        if ordered != sequences:
            errors.append(f"shape {shape_id}: puntos fuera de orden en la fuente")

    if orphan_trip_ids:
        warnings.append(
            f"{len(orphan_trip_ids)} trip(s) sin stop_times en la fuente; no se inventa recorrido"
        )
    route_patterns = tuple(
        RoutePattern(route_id=route_id, stop_ids=stop_ids, trip_count=count)
        for (route_id, stop_ids), count in sorted(patterns.items())
    )
    return TopologyValidation(
        errors=tuple(errors),
        warnings=tuple(warnings),
        patterns=route_patterns,
        orphan_trip_ids=tuple(sorted(orphan_trip_ids)),
    )
