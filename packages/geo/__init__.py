"""Geometría ferroviaria derivada de OpenStreetMap (ODbL)."""

from .corridor import ChainGap, Corridor, build_corridor, corridor_length_m
from .geometry import Projection, arc_length_to, haversine_m, project_point_to_polyline
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
    "OverpassError",
    "Projection",
    "RelationGeometry",
    "arc_length_to",
    "build_corridor",
    "corridor_length_m",
    "fetch_relation_geometry",
    "find_route_relations",
    "haversine_m",
    "load_relation_geometry_json",
    "project_point_to_polyline",
]
