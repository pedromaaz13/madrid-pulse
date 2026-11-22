"""Parser y resolución de topología GTFS estática de Renfe."""

from .catalog import (
    OPERATOR,
    Catalog,
    LineVariant,
    ScheduledTripInstance,
    build_catalog,
    scheduled_service_ids_for_date,
    scheduled_trip_instances_for_date,
)
from .parser import (
    CalendarException,
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
    "OPERATOR",
    "Catalog",
    "CalendarException",
    "CalendarService",
    "GtfsSchemaError",
    "LineVariant",
    "Route",
    "RoutePattern",
    "ScheduledTripInstance",
    "ShapePoint",
    "Stop",
    "StopTime",
    "Topology",
    "TopologyValidation",
    "Trip",
    "build_catalog",
    "load_feed",
    "scheduled_service_ids_for_date",
    "scheduled_trip_instances_for_date",
    "validate_topology",
]
