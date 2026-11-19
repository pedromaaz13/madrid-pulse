"""Reglas puras para los cinco flags soportados por el esquema de MP-006.

Los umbrales son puntos de partida calibrables, no verdades de diseño. Se
concentran en :class:`QualityThresholds` para que puedan ajustarse con evidencia
de operación sin esconder números mágicos dentro de las reglas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Sequence

from packages.contracts.canonical import VehiclePositionObservation

EntityType = Literal["vehicle_position", "trip_update", "alert"]
QualityFlag = Literal[
    "stale", "implausible_speed", "missing_id", "duplicate_snapshot", "clock_anomaly"
]


@dataclass(frozen=True)
class QualityThresholds:
    # Puntos de partida a calibrar con el histórico real; no son contrato de la fuente.
    stale_after_seconds: float = 180.0
    implausible_speed_kmh: float = 200.0
    duplicate_snapshot_after_seconds: float = 180.0
    clock_drift_after_seconds: float = 300.0


@dataclass(frozen=True)
class QualityEvent:
    occurred_at: datetime
    entity_type: EntityType
    entity_ref: str
    flag: QualityFlag
    details: dict[str, Any] = field(default_factory=dict)
    applies_to_observation: bool = False


@dataclass(frozen=True)
class SnapshotObservation:
    """Una recepción del feed completo, no una entidad deduplicada."""

    payload_hash: str
    received_at: datetime


def _event(
    *,
    flag: QualityFlag,
    occurred_at: datetime,
    entity_type: EntityType,
    entity_ref: str,
    details: dict[str, Any],
    applies_to_observation: bool = False,
) -> QualityEvent:
    return QualityEvent(
        occurred_at=occurred_at,
        entity_type=entity_type,
        entity_ref=entity_ref or "<missing>",
        flag=flag,
        details=details,
        applies_to_observation=applies_to_observation,
    )


def check_stale(
    *,
    observed_at: datetime,
    received_at: datetime,
    entity_type: EntityType,
    entity_ref: str,
    thresholds: QualityThresholds = QualityThresholds(),
    applies_to_observation: bool = False,
) -> list[QualityEvent]:
    age_seconds = (received_at - observed_at).total_seconds()
    if age_seconds <= thresholds.stale_after_seconds:
        return []
    return [
        _event(
            flag="stale",
            occurred_at=received_at,
            entity_type=entity_type,
            entity_ref=entity_ref,
            details={
                "age_seconds": age_seconds,
                "threshold_seconds": thresholds.stale_after_seconds,
            },
            applies_to_observation=applies_to_observation,
        )
    ]


def check_missing_id(
    *,
    identifier: str | None,
    id_field: str,
    occurred_at: datetime,
    entity_type: EntityType,
    entity_ref: str = "<missing>",
    applies_to_observation: bool = False,
) -> list[QualityEvent]:
    if identifier is not None and identifier.strip():
        return []
    return [
        _event(
            flag="missing_id",
            occurred_at=occurred_at,
            entity_type=entity_type,
            entity_ref=entity_ref,
            details={"missing_field": id_field},
            applies_to_observation=applies_to_observation,
        )
    ]


def check_clock_anomaly(
    *,
    observed_at: datetime,
    received_at: datetime,
    previous_observed_at: datetime | None,
    entity_type: EntityType,
    entity_ref: str,
    thresholds: QualityThresholds = QualityThresholds(),
    applies_to_observation: bool = False,
) -> list[QualityEvent]:
    drift_seconds = abs((received_at - observed_at).total_seconds())
    regressed = previous_observed_at is not None and observed_at < previous_observed_at
    excessive_drift = drift_seconds > thresholds.clock_drift_after_seconds
    if not regressed and not excessive_drift:
        return []
    details: dict[str, Any] = {
        "drift_seconds": drift_seconds,
        "threshold_seconds": thresholds.clock_drift_after_seconds,
        "regressed": regressed,
    }
    if previous_observed_at is not None:
        details["previous_observed_at"] = previous_observed_at.isoformat()
    return [
        _event(
            flag="clock_anomaly",
            occurred_at=received_at,
            entity_type=entity_type,
            entity_ref=entity_ref,
            details=details,
            applies_to_observation=applies_to_observation,
        )
    ]


def _haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia de gran círculo; suficiente para una regla pura y distancias C5."""
    earth_radius_metres = 6_371_008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * earth_radius_metres * math.asin(math.sqrt(a))


def check_implausible_speed(
    *,
    current: VehiclePositionObservation,
    previous: VehiclePositionObservation | None,
    received_at: datetime,
    thresholds: QualityThresholds = QualityThresholds(),
) -> list[QualityEvent]:
    if previous is None or not current.has_position or not previous.has_position:
        return []
    elapsed_seconds = (current.observed_at - previous.observed_at).total_seconds()
    if elapsed_seconds <= 0:
        return []  # clock_anomaly informa este caso sin inventar una velocidad.
    assert current.latitude is not None and current.longitude is not None
    assert previous.latitude is not None and previous.longitude is not None
    distance_metres = _haversine_metres(
        previous.latitude, previous.longitude, current.latitude, current.longitude
    )
    speed_kmh = distance_metres / elapsed_seconds * 3.6
    if speed_kmh <= thresholds.implausible_speed_kmh:
        return []
    return [
        _event(
            flag="implausible_speed",
            occurred_at=received_at,
            entity_type="vehicle_position",
            entity_ref=current.source_vehicle_id,
            details={
                "calculated_speed_kmh": speed_kmh,
                "distance_metres": distance_metres,
                "elapsed_seconds": elapsed_seconds,
                "threshold_kmh": thresholds.implausible_speed_kmh,
            },
            applies_to_observation=True,
        )
    ]


def check_duplicate_snapshot(
    *,
    current: SnapshotObservation,
    consecutive_history: Sequence[SnapshotObservation],
    feed_name: str,
    entity_type: EntityType,
    thresholds: QualityThresholds = QualityThresholds(),
) -> list[QualityEvent]:
    """Marca un feed congelado, nunca una deduplicación normal entre dos polls.

    ``consecutive_history`` se espera de más reciente a más antiguo y la regla
    deja de recorrer en el primer hash distinto. Solo dispara si el contenido
    idéntico cubre la ventana calibrable completa.
    """
    matching = [current]
    for snapshot in consecutive_history:
        if snapshot.payload_hash != current.payload_hash:
            break
        matching.append(snapshot)
    unchanged_seconds = (current.received_at - matching[-1].received_at).total_seconds()
    if unchanged_seconds <= thresholds.duplicate_snapshot_after_seconds:
        return []
    return [
        _event(
            flag="duplicate_snapshot",
            occurred_at=current.received_at,
            entity_type=entity_type,
            entity_ref=f"feed:{feed_name}",
            details={
                "feed_name": feed_name,
                "unchanged_seconds": unchanged_seconds,
                "threshold_seconds": thresholds.duplicate_snapshot_after_seconds,
                "consecutive_polls": len(matching),
                "payload_hash": current.payload_hash,
            },
        )
    ]


def evaluate_vehicle_position(
    current: VehiclePositionObservation,
    *,
    received_at: datetime,
    previous: VehiclePositionObservation | None = None,
    thresholds: QualityThresholds = QualityThresholds(),
) -> list[QualityEvent]:
    """Compone las cuatro reglas que pueden aplicar a una posición concreta."""
    ref = current.source_vehicle_id
    events: list[QualityEvent] = []
    events += check_missing_id(
        identifier=current.source_vehicle_id,
        id_field="source_vehicle_id",
        occurred_at=received_at,
        entity_type="vehicle_position",
        entity_ref=ref,
        applies_to_observation=True,
    )
    events += check_missing_id(
        identifier=current.source_trip_id,
        id_field="source_trip_id",
        occurred_at=received_at,
        entity_type="vehicle_position",
        entity_ref=ref,
        applies_to_observation=True,
    )
    events += check_stale(
        observed_at=current.observed_at,
        received_at=received_at,
        entity_type="vehicle_position",
        entity_ref=ref,
        thresholds=thresholds,
        applies_to_observation=True,
    )
    events += check_clock_anomaly(
        observed_at=current.observed_at,
        received_at=received_at,
        previous_observed_at=previous.observed_at if previous else None,
        entity_type="vehicle_position",
        entity_ref=ref,
        thresholds=thresholds,
        applies_to_observation=True,
    )
    events += check_implausible_speed(
        current=current, previous=previous, received_at=received_at, thresholds=thresholds
    )
    return events
