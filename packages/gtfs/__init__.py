"""Parser y resolución de topología GTFS estática de Renfe."""

from .parser import (
    CalendarService,
    GtfsSchemaError,
    Route,
    ShapePoint,
    Stop,
    StopTime,
    Topology,
    Trip,
    load_feed,
)
from .topology import RoutePattern, TopologyValidation, validate_topology

__all__ = [
    "CalendarService",
    "GtfsSchemaError",
    "Route",
    "RoutePattern",
    "ShapePoint",
    "Stop",
    "StopTime",
    "Topology",
    "TopologyValidation",
    "Trip",
    "load_feed",
    "validate_topology",
]
