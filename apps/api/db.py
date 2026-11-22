"""Lecturas de PostgreSQL para la API — nunca escribe (colector aparte)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from packages.contracts.canonical import TripUpdateObservation, VehiclePositionObservation


@dataclass(frozen=True)
class ObservedRow:
    """Observación canónica más ``received_at``, que el modelo Pydantic no
    conserva (solo ``observed_at``, el timestamp reportado por la fuente)."""

    position: VehiclePositionObservation
    received_at: datetime


@dataclass(frozen=True)
class VehicleHistory:
    source_vehicle_id: str
    latest: ObservedRow
    previous: ObservedRow | None


def _row_to_observed(row: dict) -> ObservedRow:
    position = VehiclePositionObservation(
        source_vehicle_id=row["source_vehicle_id"],
        source_trip_id=row["source_trip_id"],
        observed_at=row["observed_at"].astimezone(timezone.utc),
        latitude=row["latitude"],
        longitude=row["longitude"],
        current_status=row["current_status"],
        current_stop_id=row["current_stop_id"],
        speed_kmh=row["speed_kmh"],
        bearing=row["bearing"],
        raw_vehicle_label=row["raw_vehicle_label"],
        payload_hash=row["payload_hash"],
    )
    return ObservedRow(position=position, received_at=row["received_at"].astimezone(timezone.utc))


def latest_vehicle_histories(conn: psycopg.Connection) -> list[VehicleHistory]:
    """Las dos observaciones más recientes de cada vehículo distinto visto.

    Sin corte de edad: un vehículo con último dato muy antiguo se devuelve
    igualmente -- es responsabilidad del motor de movimiento (MP-012)
    clasificarlo como `stale`/`scheduled`, no de esta capa ocultarlo.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT source_vehicle_id, source_trip_id, observed_at, received_at,
                   latitude, longitude, current_status, current_stop_id,
                   speed_kmh, bearing, raw_vehicle_label, payload_hash,
                   row_number() OVER (
                       PARTITION BY source_vehicle_id ORDER BY observed_at DESC, id DESC
                   ) AS rank
            FROM vehicle_position_observation
            """
        )
        by_vehicle: dict[str, list[dict]] = {}
        for row in cur.fetchall():
            by_vehicle.setdefault(row["source_vehicle_id"], []).append(row)

    histories: list[VehicleHistory] = []
    for vehicle_id, rows in by_vehicle.items():
        rows.sort(key=lambda item: item["rank"])
        latest = _row_to_observed(rows[0])
        previous = _row_to_observed(rows[1]) if len(rows) > 1 else None
        histories.append(
            VehicleHistory(source_vehicle_id=vehicle_id, latest=latest, previous=previous)
        )
    return histories


def vehicle_history(conn: psycopg.Connection, source_vehicle_id: str) -> VehicleHistory | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT source_vehicle_id, source_trip_id, observed_at, received_at,
                   latitude, longitude, current_status, current_stop_id,
                   speed_kmh, bearing, raw_vehicle_label, payload_hash
            FROM vehicle_position_observation
            WHERE source_vehicle_id = %s
            ORDER BY observed_at DESC, id DESC
            LIMIT 2
            """,
            (source_vehicle_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return None
    latest = _row_to_observed(rows[0])
    previous = _row_to_observed(rows[1]) if len(rows) > 1 else None
    return VehicleHistory(source_vehicle_id=source_vehicle_id, latest=latest, previous=previous)


def latest_trip_update(
    conn: psycopg.Connection, source_trip_id: str
) -> TripUpdateObservation | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT source_trip_id, observed_at, schedule_relationship, delay_seconds,
                   delay_coverage, next_stop_id, payload_hash
            FROM trip_update_observation
            WHERE source_trip_id = %s
            ORDER BY observed_at DESC, id DESC
            LIMIT 1
            """,
            (source_trip_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return TripUpdateObservation(
        source_trip_id=row["source_trip_id"],
        observed_at=row["observed_at"].astimezone(timezone.utc),
        schedule_relationship=row["schedule_relationship"],
        delay_seconds=row["delay_seconds"],
        delay_coverage=row["delay_coverage"],
        next_stop_id=row["next_stop_id"],
        payload_hash=row["payload_hash"],
    )


@dataclass(frozen=True)
class FeedRunSample:
    feed_name: str
    source_timestamp: datetime | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    entity_count: int | None
    payload_hash: str


def recent_ingestion_runs(conn: psycopg.Connection, *, per_feed_limit: int = 50) -> list[FeedRunSample]:
    """Las ejecuciones más recientes por feed, para calcular frescura y estabilidad del hash."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT feed_name, source_timestamp, started_at, finished_at, status, entity_count, payload_hash,
                   row_number() OVER (PARTITION BY feed_name ORDER BY started_at DESC) AS rank
            FROM source_ingestion_run
            """
        )
        rows = [row for row in cur.fetchall() if row["rank"] <= per_feed_limit]
    return [
        FeedRunSample(
            feed_name=row["feed_name"],
            source_timestamp=(
                row["source_timestamp"].astimezone(timezone.utc)
                if row["source_timestamp"] is not None else None
            ),
            started_at=row["started_at"].astimezone(timezone.utc),
            finished_at=(
                row["finished_at"].astimezone(timezone.utc)
                if row["finished_at"] is not None else None
            ),
            status=row["status"],
            entity_count=row["entity_count"],
            payload_hash=row["payload_hash"],
        )
        for row in rows
    ]
