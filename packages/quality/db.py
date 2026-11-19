"""Persistencia del motor de calidad, dentro de la transacción del colector."""

from __future__ import annotations

import json
from datetime import datetime

import psycopg

from packages.contracts.canonical import VehiclePositionObservation
from packages.quality.engine import QualityEvent, SnapshotObservation


def latest_vehicle_position(
    conn: psycopg.Connection, source_vehicle_id: str
) -> VehiclePositionObservation | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_vehicle_id, source_trip_id, observed_at, latitude, longitude,
                   current_status, current_stop_id, speed_kmh, bearing, raw_vehicle_label,
                   payload_hash
            FROM vehicle_position_observation
            WHERE source_vehicle_id = %s
            ORDER BY observed_at DESC, id DESC LIMIT 1
            """,
            (source_vehicle_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return VehiclePositionObservation(
        source_vehicle_id=row[0],
        source_trip_id=row[1],
        observed_at=row[2],
        latitude=row[3],
        longitude=row[4],
        current_status=row[5],
        current_stop_id=row[6],
        speed_kmh=row[7],
        bearing=row[8],
        raw_vehicle_label=row[9],
        payload_hash=row[10],
    )


def recent_feed_snapshots(
    conn: psycopg.Connection, feed_name: str, *, limit: int = 512
) -> list[SnapshotObservation]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT payload_hash, started_at
            FROM source_ingestion_run
            WHERE feed_name = %s AND status = 'ok'
            ORDER BY started_at DESC, id DESC LIMIT %s
            """,
            (feed_name, limit),
        )
        return [SnapshotObservation(payload_hash=row[0], received_at=row[1]) for row in cur]


_LATEST_TIME_QUERIES = {
    "trip_update_observation": (
        "SELECT observed_at FROM trip_update_observation WHERE source_trip_id = %s "
        "ORDER BY observed_at DESC, id DESC LIMIT 1"
    ),
    "service_alert": (
        "SELECT active_period_start FROM service_alert WHERE source_alert_id = %s "
        "ORDER BY active_period_start DESC, id DESC LIMIT 1"
    ),
}


def latest_observed_at(
    conn: psycopg.Connection, table: str, entity_ref: str
) -> datetime | None:
    query = _LATEST_TIME_QUERIES[table]
    with conn.cursor() as cur:
        cur.execute(query, (entity_ref,))
        row = cur.fetchone()
    return row[0] if row else None


def insert_quality_events(conn: psycopg.Connection, events: list[QualityEvent]) -> None:
    if not events:
        return
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO data_quality_event
                (occurred_at, entity_type, entity_ref, flag, details)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (
                    event.occurred_at,
                    event.entity_type,
                    event.entity_ref,
                    event.flag,
                    json.dumps(event.details),
                )
                for event in events
            ],
        )


def observation_flags(events: list[QualityEvent]) -> list[str]:
    """Flags únicos y estables que pertenecen a la observación concreta."""
    return list(dict.fromkeys(event.flag for event in events if event.applies_to_observation))
