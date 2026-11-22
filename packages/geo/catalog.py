"""Catálogo trazable de corredores OSM por patrón GTFS ordenado.

Renfe no publica ``direction_id`` en el GTFS observado. Por eso el sentido
no se inventa: forma parte de la identidad del patrón como secuencia ordenada
de ``stop_id`` (origen, destino y paradas intermedias).
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Iterable

from packages.gtfs import Catalog as GtfsCatalog
from packages.gtfs import RoutePattern, Topology

from .corridor import Corridor, build_corridor
from .geometry import Projection
from .overpass import load_relation_geometry_json


class CoverageStatus(StrEnum):
    VALIDATED = "validated"
    PARTIAL = "partial"
    PENDING = "pending"


class PositionResolution(StrEnum):
    MAP_MATCHED = "map_matched"
    RAW = "raw"
    UNLOCATED = "unlocated"


@dataclass(frozen=True)
class PatternIdentity:
    """Identidad estable: ``route_id`` + secuencia ordenada (sentido real)."""

    pattern_id: str
    route_id: str
    stop_ids: tuple[str, ...]
    origin_stop_id: str
    destination_stop_id: str
    direction_key: str

    @classmethod
    def from_pattern(cls, pattern: RoutePattern) -> PatternIdentity:
        if not pattern.stop_ids:
            raise ValueError("un patrón de corredor necesita al menos una parada")
        canonical = "\0".join((pattern.route_id, *pattern.stop_ids)).encode()
        digest = hashlib.sha256(canonical).hexdigest()[:20]
        origin, destination = pattern.stop_ids[0], pattern.stop_ids[-1]
        return cls(
            pattern_id=f"gtfs-pattern:{digest}",
            route_id=pattern.route_id,
            stop_ids=pattern.stop_ids,
            origin_stop_id=origin,
            destination_stop_id=destination,
            direction_key=f"{origin}>{destination}",
        )


@dataclass(frozen=True)
class GeometrySourceSpec:
    relation_id: int
    path: Path
    sha256: str
    captured_at: str
    route_ids: frozenset[str]
    attribution: str = "© OpenStreetMap contributors (ODbL-1.0)"


@dataclass(frozen=True)
class PatternCaveat:
    route_id: str
    stop_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CorridorCoverage:
    line_id: str
    identity: PatternIdentity
    trip_count: int
    status: CoverageStatus
    reason: str
    relation_id: int | None = None
    geometry_version: str | None = None
    source_captured_at: str | None = None
    attribution: str | None = None
    max_stop_distance_m: float | None = None
    corridor: Corridor | None = None

    @property
    def can_map_match(self) -> bool:
        return self.status is CoverageStatus.VALIDATED and self.corridor is not None


@dataclass(frozen=True)
class PositionMatch:
    """Salida mínima raw→matched para MP-019, sin posición renderizada."""

    resolution: PositionResolution
    pattern_id: str
    raw_lat: float | None
    raw_lon: float | None
    projection: Projection | None
    progress_m: float | None
    distance_from_raw_m: float | None
    geometry_version: str | None
    reason: str | None


@dataclass(frozen=True)
class _LoadedSource:
    spec: GeometrySourceSpec
    corridor: Corridor
    geometry_version: str


@dataclass(frozen=True)
class CorridorCatalog:
    gtfs_version: str
    entries: tuple[CorridorCoverage, ...]

    def __post_init__(self) -> None:
        by_pattern = {entry.identity.pattern_id: entry for entry in self.entries}
        if len(by_pattern) != len(self.entries):
            raise ValueError("pattern_id duplicado en catálogo de corredores")
        object.__setattr__(self, "_by_pattern", by_pattern)
        object.__setattr__(
            self,
            "_by_route_and_stops",
            {(entry.identity.route_id, entry.identity.stop_ids): entry for entry in self.entries},
        )

    def coverage_for(self, pattern: RoutePattern) -> CorridorCoverage:
        return self._by_route_and_stops[(pattern.route_id, pattern.stop_ids)]

    def entry(self, pattern_id: str) -> CorridorCoverage | None:
        return self._by_pattern.get(pattern_id)

    def match_position(
        self, pattern_id: str, *, raw_lat: float | None, raw_lon: float | None
    ) -> PositionMatch:
        entry = self._by_pattern.get(pattern_id)
        if raw_lat is None or raw_lon is None:
            return PositionMatch(
                resolution=PositionResolution.UNLOCATED,
                pattern_id=pattern_id,
                raw_lat=raw_lat,
                raw_lon=raw_lon,
                projection=None,
                progress_m=None,
                distance_from_raw_m=None,
                geometry_version=entry.geometry_version if entry else None,
                reason="posición raw ausente",
            )
        if entry is None:
            return _raw_fallback(pattern_id, raw_lat, raw_lon, None, "patrón desconocido")
        if not entry.can_map_match:
            return _raw_fallback(
                pattern_id,
                raw_lat,
                raw_lon,
                entry.geometry_version,
                f"corredor {entry.status.value}: {entry.reason}",
            )
        assert entry.corridor is not None
        projection, progress_m = entry.corridor.project_station(raw_lat, raw_lon)
        return PositionMatch(
            resolution=PositionResolution.MAP_MATCHED,
            pattern_id=pattern_id,
            raw_lat=raw_lat,
            raw_lon=raw_lon,
            projection=projection,
            progress_m=progress_m,
            distance_from_raw_m=projection.distance_m,
            geometry_version=entry.geometry_version,
            reason=None,
        )

    def to_csv(self) -> str:
        output = StringIO(newline="")
        writer = csv.DictWriter(
            output,
            lineterminator="\n",
            fieldnames=(
                "gtfs_version",
                "line_id",
                "pattern_id",
                "route_id",
                "direction_key",
                "origin_stop_id",
                "destination_stop_id",
                "stop_count",
                "trip_count",
                "status",
                "reason",
                "relation_id",
                "geometry_version",
                "source_captured_at",
            ),
        )
        writer.writeheader()
        for entry in self.entries:
            writer.writerow(
                {
                    "gtfs_version": self.gtfs_version,
                    "line_id": entry.line_id,
                    "pattern_id": entry.identity.pattern_id,
                    "route_id": entry.identity.route_id,
                    "direction_key": entry.identity.direction_key,
                    "origin_stop_id": entry.identity.origin_stop_id,
                    "destination_stop_id": entry.identity.destination_stop_id,
                    "stop_count": len(entry.identity.stop_ids),
                    "trip_count": entry.trip_count,
                    "status": entry.status.value,
                    "reason": entry.reason,
                    "relation_id": entry.relation_id or "",
                    "geometry_version": entry.geometry_version or "",
                    "source_captured_at": entry.source_captured_at or "",
                }
            )
        return output.getvalue()


def _raw_fallback(
    pattern_id: str,
    raw_lat: float,
    raw_lon: float,
    geometry_version: str | None,
    reason: str,
) -> PositionMatch:
    return PositionMatch(
        resolution=PositionResolution.RAW,
        pattern_id=pattern_id,
        raw_lat=raw_lat,
        raw_lon=raw_lon,
        projection=None,
        progress_m=None,
        distance_from_raw_m=None,
        geometry_version=geometry_version,
        reason=reason,
    )


def _load_source(spec: GeometrySourceSpec) -> _LoadedSource:
    actual = hashlib.sha256(spec.path.read_bytes()).hexdigest()
    if actual != spec.sha256:
        raise ValueError(
            f"checksum inesperado para relación {spec.relation_id}: {actual} != {spec.sha256}"
        )
    geometry = load_relation_geometry_json(spec.path)
    if geometry.relation_id != spec.relation_id:
        raise ValueError(
            f"la fixture {spec.path} contiene relación {geometry.relation_id}, no {spec.relation_id}"
        )
    return _LoadedSource(
        spec=spec,
        corridor=build_corridor(geometry),
        geometry_version=f"osm-relation:{spec.relation_id}@sha256:{actual}",
    )


def build_corridor_catalog(
    gtfs_catalog: GtfsCatalog,
    topology: Topology,
    *,
    sources: Iterable[GeometrySourceSpec],
    caveats: Iterable[PatternCaveat] = (),
    max_station_distance_m: float = 150.0,
) -> CorridorCatalog:
    """Cruza todos los patrones GTFS con fuentes reales, dejando el resto pending.

    Una fuente solo se considera para los ``route_id`` declarados. Además se
    verifica empíricamente que todas las estaciones proyecten cerca y en orden
    monótono. Nunca se elige un corredor solo porque una línea tenga un nombre
    parecido ni se crea una recta entre tramos separados.
    """
    loaded = tuple(_load_source(spec) for spec in sources)
    caveat_by_pattern = {(item.route_id, item.stop_ids): item for item in caveats}
    stops = {stop.stop_id: (stop.latitude, stop.longitude) for stop in topology.stops}
    entries: list[CorridorCoverage] = []

    for line in gtfs_catalog.lines:
        for pattern in line.patterns:
            identity = PatternIdentity.from_pattern(pattern)
            candidates: list[tuple[float, _LoadedSource]] = []
            partial_candidates: list[tuple[float, _LoadedSource, str]] = []
            for source in loaded:
                if pattern.route_id not in source.spec.route_ids:
                    continue
                if not source.corridor.is_continuous:
                    partial_candidates.append(
                        (
                            float("inf"),
                            source,
                            f"relación {source.spec.relation_id} tiene {len(source.corridor.gaps)} hueco(s)",
                        )
                    )
                    continue
                projections: list[tuple[Projection, float]] = []
                missing = [stop_id for stop_id in pattern.stop_ids if stop_id not in stops]
                if missing:
                    partial_candidates.append(
                        (float("inf"), source, f"paradas GTFS ausentes: {missing}")
                    )
                    continue
                for stop_id in pattern.stop_ids:
                    projections.append(source.corridor.project_station(*stops[stop_id]))
                distances = [projection.distance_m for projection, _ in projections]
                arcs = [arc for _, arc in projections]
                if max(distances) > max_station_distance_m:
                    partial_candidates.append(
                        (
                            max(distances),
                            source,
                            f"relación {source.spec.relation_id}: estación a {max(distances):.1f} m",
                        )
                    )
                    continue
                if arcs != sorted(arcs):
                    partial_candidates.append(
                        (
                            max(distances),
                            source,
                            f"relación {source.spec.relation_id}: estaciones fuera de orden",
                        )
                    )
                    continue
                candidates.append((max(distances), source))

            if not candidates:
                if partial_candidates:
                    max_distance, source, reason = min(
                        partial_candidates, key=lambda item: item[0]
                    )
                    entries.append(
                        CorridorCoverage(
                            line_id=line.short_name,
                            identity=identity,
                            trip_count=pattern.trip_count,
                            status=CoverageStatus.PARTIAL,
                            reason=reason,
                            relation_id=source.spec.relation_id,
                            geometry_version=source.geometry_version,
                            source_captured_at=source.spec.captured_at,
                            attribution=source.spec.attribution,
                            max_stop_distance_m=(
                                max_distance if max_distance != float("inf") else None
                            ),
                            corridor=source.corridor,
                        )
                    )
                    continue
                entries.append(
                    CorridorCoverage(
                        line_id=line.short_name,
                        identity=identity,
                        trip_count=pattern.trip_count,
                        status=CoverageStatus.PENDING,
                        reason="sin geometría OSM descargada para este patrón/sentido",
                    )
                )
                continue

            max_distance, source = min(candidates, key=lambda item: item[0])
            caveat = caveat_by_pattern.get((pattern.route_id, pattern.stop_ids))
            status = CoverageStatus.PARTIAL if caveat else CoverageStatus.VALIDATED
            reason = (
                caveat.reason
                if caveat
                else "corredor OSM continuo; estaciones GTFS cercanas y en orden"
            )
            entries.append(
                CorridorCoverage(
                    line_id=line.short_name,
                    identity=identity,
                    trip_count=pattern.trip_count,
                    status=status,
                    reason=reason,
                    relation_id=source.spec.relation_id,
                    geometry_version=source.geometry_version,
                    source_captured_at=source.spec.captured_at,
                    attribution=source.spec.attribution,
                    max_stop_distance_m=max_distance,
                    corridor=source.corridor,
                )
            )

    return CorridorCatalog(gtfs_version=gtfs_catalog.gtfs_version, entries=tuple(entries))


def shared_track_way_ids(left: GeometrySourceSpec, right: GeometrySourceSpec) -> frozenset[int]:
    """Ways OSM de vía literalmente compartidos por dos relaciones reales."""
    left_geometry = load_relation_geometry_json(left.path)
    right_geometry = load_relation_geometry_json(right.path)
    tracks = lambda geometry: {  # noqa: E731
        ref
        for kind, ref, role in geometry.member_refs
        if kind == "way" and role == ""
    }
    return frozenset(tracks(left_geometry) & tracks(right_geometry))
