"""Contrato directo entre el motor de movimiento y la futura API MP-013."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class PositionMode(StrEnum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    STALE = "stale"
    SCHEDULED = "scheduled"


class MovementSource(StrEnum):
    VEHICLE_POSITION = "gtfs_rt_vehicle_position_map_matched"
    VEHICLE_POSITION_AND_SCHEDULE = "gtfs_rt_vehicle_position+gtfs_static_schedule"
    LAST_VEHICLE_POSITION = "last_gtfs_rt_vehicle_position_map_matched"
    SCHEDULE = "gtfs_static_schedule"


MovementFlag = str


@dataclass(frozen=True)
class MovementThresholds:
    """Umbrales operativos calibrables; no describen el contrato de Renfe.

    Los 60/180 s se mantienen tras MP-003: con una cadencia observada de
    20--22 s equivalen aproximadamente a 3 y 8 actualizaciones perdidas.
    ``unusable_jump_speed_kmh`` es deliberadamente distinto de la velocidad
    física de interpolación: el soak real produjo saltos de feed de hasta
    787 km/h que no deben confundirse con la velocidad real del tren.
    """

    observed_max_age_s: float = 60.0
    stale_after_s: float = 180.0
    off_track_distance_m: float = 200.0
    backward_jump_m: float = 250.0
    unusable_backward_jump_m: float = 1_000.0
    unusable_jump_speed_kmh: float = 900.0
    max_estimated_speed_kmh: float = 160.0
    max_estimated_acceleration_mps2: float = 1.2

    def __post_init__(self) -> None:
        if self.observed_max_age_s < 0 or self.stale_after_s <= self.observed_max_age_s:
            raise ValueError("stale_after_s debe ser mayor que observed_max_age_s >= 0")
        positive = (
            self.off_track_distance_m,
            self.backward_jump_m,
            self.unusable_backward_jump_m,
            self.unusable_jump_speed_kmh,
            self.max_estimated_speed_kmh,
            self.max_estimated_acceleration_mps2,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("todos los umbrales físicos deben ser positivos")
        if self.unusable_backward_jump_m < self.backward_jump_m:
            raise ValueError("el retroceso inutilizable no puede ser menor que el marcado")


@dataclass(frozen=True)
class MapMatch:
    latitude: float
    longitude: float
    physical_arc_m: float
    distance_from_track_m: float


@dataclass(frozen=True)
class MovementAnomaly:
    flag: MovementFlag
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MovementPosition:
    trip_id: str
    route_id: str
    latitude: float
    longitude: float
    progress_m: float
    position_mode: PositionMode
    confidence: float
    age_s: float | None
    source: MovementSource
    calculated_at: datetime
    observed_at: datetime | None
    anomalies: tuple[MovementAnomaly, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence debe estar entre 0 y 1")
        if self.age_s is not None and self.age_s < 0:
            raise ValueError("age_s no puede ser negativo")
