"""Funciones de normalización: raw -> canonical.

Cada función toma un modelo `raw.*Feed` ya parseado y devuelve modelos
`canonical.*` listos para persistir (MP-006/MP-007). No hacen peticiones de
red ni dependen de la base de datos -- son funciones puras, testeables sin
infraestructura.
"""

from __future__ import annotations

from packages.contracts.canonical import (
    FeedHealth,
    ServiceAlert,
    TripUpdateObservation,
    VehiclePositionObservation,
    canonical_payload_hash,
    epoch_to_utc,
)
from packages.contracts.raw import (
    RawAlertEntity,
    RawAlertsFeed,
    RawTripUpdateEntity,
    RawTripUpdatesFeed,
    RawVehiclePositionEntity,
    RawVehiclePositionsFeed,
)


def _entity_hash(entity: RawVehiclePositionEntity | RawTripUpdateEntity | RawAlertEntity) -> str:
    return canonical_payload_hash(entity.model_dump(mode="json", by_alias=True))


def vehicle_positions_to_canonical(
    feed: RawVehiclePositionsFeed,
) -> list[VehiclePositionObservation]:
    observations = []
    for entity in feed.entity:
        vehicle = entity.vehicle
        observations.append(
            VehiclePositionObservation(
                source_vehicle_id=vehicle.vehicle.id,
                source_trip_id=vehicle.trip.trip_id,
                observed_at=epoch_to_utc(vehicle.timestamp),
                latitude=vehicle.position.latitude if vehicle.position else None,
                longitude=vehicle.position.longitude if vehicle.position else None,
                current_status=vehicle.current_status,
                current_stop_id=vehicle.stop_id,
                raw_vehicle_label=vehicle.vehicle.label,
                payload_hash=_entity_hash(entity),
            )
        )
    return observations


def trip_updates_to_canonical(feed: RawTripUpdatesFeed) -> list[TripUpdateObservation]:
    feed_observed_at = epoch_to_utc(feed.header.timestamp)
    observations = []
    for entity in feed.entity:
        update = entity.trip_update
        next_stop_id = next(
            (stop.stop_id for stop in update.stop_time_update or []
             if stop.schedule_relationship != "SKIPPED"),
            None,
        )
        observations.append(
            TripUpdateObservation(
                source_trip_id=update.trip.trip_id,
                observed_at=feed_observed_at,
                schedule_relationship=update.trip.schedule_relationship,
                delay_seconds=update.delay,
                delay_coverage="reported" if update.delay is not None else "missing",
                next_stop_id=next_stop_id,
                payload_hash=_entity_hash(entity),
            )
        )
    return observations


def alerts_to_canonical(feed: RawAlertsFeed) -> list[ServiceAlert]:
    alerts = []
    for entity in feed.entity:
        alert = entity.alert
        first_translation = alert.description_text.translation[0]
        first_period = alert.active_period[0]
        alerts.append(
            ServiceAlert(
                source_alert_id=entity.id,
                active_period_start=epoch_to_utc(first_period.start),
                # `active_period_end` siempre es None aquí: el feed real nunca lo
                # emite (ver raw.py, RawActivePeriod -- no declara `end` porque no
                # se ha observado). El campo existe en ServiceAlert por si Renfe
                # empieza a emitirlo en el futuro, pero esta función no puede leer
                # algo que el modelo `raw` no modela.
                active_period_end=None,
                affected_route_ids=[
                    informed.route_id
                    for informed in alert.informed_entity
                    if informed.route_id is not None
                ],
                description_text=first_translation.text,
                description_language=first_translation.language,
                payload_hash=_entity_hash(entity),
            )
        )
    return alerts


def feed_health_from_raw(
    feed_name: str,
    feed: RawVehiclePositionsFeed | RawTripUpdatesFeed | RawAlertsFeed,
) -> FeedHealth:
    return FeedHealth(
        feed_name=feed_name,  # type: ignore[arg-type]
        source_timestamp=epoch_to_utc(feed.header.timestamp),
        entity_count=len(feed.entity),
    )
