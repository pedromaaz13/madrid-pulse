"""Geometría ferroviaria derivada de OpenStreetMap (ODbL)."""

from .corridor import ChainGap, Corridor, build_corridor, corridor_length_m
from .catalog import (
    CorridorCatalog,
    CorridorCoverage,
    CoverageStatus,
    GeometrySourceSpec,
    PatternCaveat,
    PatternIdentity,
    PositionMatch,
    PositionResolution,
    build_corridor_catalog,
    shared_track_way_ids,
)
from .geometry import (
    Projection,
    arc_length_to,
    haversine_m,
    point_at_arc_length,
    project_point_to_polyline,
)
from .madrid import build_madrid_corridor_catalog, madrid_source_specs
from .overpass import (
    OverpassError,
    RelationGeometry,
    fetch_relation_geometry,
    find_route_relations,
    load_relation_geometry_json,
)

__all__ = [
    "ChainGap",
    "Corridor",
    "CorridorCatalog",
    "CorridorCoverage",
    "CoverageStatus",
    "GeometrySourceSpec",
    "OverpassError",
    "Projection",
    "PatternCaveat",
    "PatternIdentity",
    "PositionMatch",
    "PositionResolution",
    "RelationGeometry",
    "arc_length_to",
    "build_corridor",
    "build_corridor_catalog",
    "build_madrid_corridor_catalog",
    "corridor_length_m",
    "fetch_relation_geometry",
    "find_route_relations",
    "haversine_m",
    "load_relation_geometry_json",
    "madrid_source_specs",
    "point_at_arc_length",
    "project_point_to_polyline",
    "shared_track_way_ids",
]
