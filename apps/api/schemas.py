"""Modelos de respuesta — conformes a docs/DATA_CONTRACTS.md."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PositionOut(BaseModel):
    lat: float
    lon: float
    mode: Literal["observed", "estimated", "stale", "scheduled"]
    confidence: float


class DelayOut(BaseModel):
    seconds: int | None
    coverage: Literal["reported", "missing"]


class ObservationOut(BaseModel):
    reported_at: datetime | None
    received_at: datetime | None
    age_s: float | None


class QualityOut(BaseModel):
    stale: bool
    flags: list[str]


class VehicleOut(BaseModel):
    vehicle_id: str
    trip_id: str
    route_id: str | None
    """``None`` cuando el ``trip_id`` en vivo no resuelve contra el GTFS
    estático cargado (p. ej. una fixture reducida sin ese trip) -- nunca se
    inventa un valor."""
    line: str | None
    position: PositionOut | None
    """``None`` cuando no hay suficiente información (route_id sin resolver)
    para map-matchear o calcular horario; la fila se devuelve igualmente con
    los datos crudos que sí se conocen, no se oculta."""
    delay: DelayOut
    observation: ObservationOut
    quality: QualityOut


class FeedHealthOut(BaseModel):
    feed_name: str
    status: Literal["ok", "stale", "error", "unknown"]
    source_timestamp: datetime | None
    data_age_s: float | None
    poll_age_s: float
    unchanged_for_s: float | None
    entities: int | None
    rejected: int


class HealthOut(BaseModel):
    feeds: list[FeedHealthOut]
    mode: Literal["live", "replay"] | None = None
    gtfs_version: str | None = None
    gtfs_valid_from: str | None = None
    gtfs_valid_until: str | None = None


class CoordinateOut(BaseModel):
    lat: float
    lon: float


class LineStationOut(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    distance_along_m: float


class LineGeometryOut(BaseModel):
    """Corredor OSM real: cada elemento de ``segments`` es continuo.

    Los tramos nunca deben concatenarse en el cliente, porque una separación
    entre ellos representa un hueco real de la geometría cargada.
    """

    segments: list[list[CoordinateOut]]
    stations: list[LineStationOut]


class LineOut(BaseModel):
    line_id: str
    network_id: str
    route_ids: list[str]
    geometry: LineGeometryOut | None


class StationOut(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
