"""Motor de movimiento transparente y parametrizable (MP-012) más la capa de
presentación `rendered` de MP-019 (ADR-0014), aditiva sobre el mismo motor."""

from .engine import MovementEngine
from .model import (
    MapMatch,
    MovementAnomaly,
    MovementPosition,
    MovementSource,
    MovementThresholds,
    PositionMode,
)
from .rendering import (
    AnchorSample,
    CoordinateSpace,
    ProgressEnvelope,
    RenderedPosition,
    RenderingMethod,
    render_from_movement,
    render_raw_anchor,
    render_unlocated,
)
from .schedule import (
    TripSchedule,
    build_trip_schedule,
    parse_gtfs_time,
    service_day_instant,
    service_seconds,
)

__all__ = [
    "AnchorSample",
    "CoordinateSpace",
    "MapMatch",
    "MovementAnomaly",
    "MovementEngine",
    "MovementPosition",
    "MovementSource",
    "MovementThresholds",
    "PositionMode",
    "ProgressEnvelope",
    "RenderedPosition",
    "RenderingMethod",
    "TripSchedule",
    "build_trip_schedule",
    "parse_gtfs_time",
    "service_day_instant",
    "render_from_movement",
    "render_raw_anchor",
    "render_unlocated",
    "service_seconds",
]
