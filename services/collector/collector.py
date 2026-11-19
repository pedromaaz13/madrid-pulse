"""Ciclo de polling: un feed -> fetch -> parse -> normalize -> filtro -> dedupe -> persist.

La deduplicación (DEC-013/DECISIONS.md) compara el `payload_hash` canónico de
cada entidad con el de la última fila almacenada para la misma clave de
entidad de origen (`source_vehicle_id` / `source_trip_id` / `source_alert_id`).
Si coinciden, la entidad no cambió desde el último poll y no se inserta una
fila nueva -- eso implementa literalmente "se almacena una sola fila" de
`docs/DATA_MODEL.md`, sin contador `seen_count` (deliberadamente fuera de
alcance de MP-007, ver ADR-0010).

Filtro de alcance: ADR-0008 ("Consecuencias") exige que el colector limite la
ingesta por prefijo de núcleo (`10` = Madrid), no por subcadena de línea. Las
entidades de otros núcleos se descartan antes de persistir (`skipped_count`).
**Limitación conocida, documentada explícitamente** (ver `docs/DECISIONS.md`
DEC-020): ADR-0001 (`Aceptado`) acota el MVP a la línea **C5** específicamente,
no a todo el núcleo de Madrid -- el filtro por núcleo aquí es una aproximación
conservadora y verificada (ADR-0008 lo pide explícitamente a este nivel), pero
NO excluye otras líneas de Madrid (C1-C4, C7-C10). Acotar a C5 exige resolver
`trip_id` contra `route_id` vía el GTFS estático, que ADR-0009 asigna
explícitamente a MP-010, no a MP-007.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import psycopg

from packages.contracts.nucleo import MADRID_PREFIX
from packages.contracts.normalize import (
    alerts_to_canonical,
    feed_health_from_raw,
    trip_updates_to_canonical,
    vehicle_positions_to_canonical,
)
from packages.contracts.raw import RawAlertsFeed, RawTripUpdatesFeed, RawVehiclePositionsFeed
from packages.quality import db as quality_db
from packages.quality.engine import (
    SnapshotObservation,
    check_clock_anomaly,
    check_duplicate_snapshot,
    check_missing_id,
    check_stale,
    evaluate_vehicle_position,
)
from services.collector import db
from services.collector.config import FeedConfig
from services.collector.http_client import Fetcher, RetryPolicy, default_fetcher, fetch_with_retry

logger = logging.getLogger(__name__)

NowFn = Callable[[], datetime]


@dataclass
class CycleResult:
    feed_name: str
    status: str  # "ok" | "error"
    entity_count: int | None
    inserted_count: int
    deduped_count: int
    skipped_count: int = 0  # fuera de alcance (núcleo distinto de Madrid, ADR-0008)
    error: str | None = None
    run_id: int | None = None  # id de `source_ingestion_run` (None en el camino de error)


_RAW_FEEDS = {
    "vehicle_positions": RawVehiclePositionsFeed,
    "trip_updates": RawTripUpdatesFeed,
    "alerts": RawAlertsFeed,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_cycle(
    feed: FeedConfig,
    conn: psycopg.Connection,
    retry_policy: RetryPolicy,
    fetcher: Fetcher = default_fetcher,
    now: NowFn = _utcnow,
) -> CycleResult:
    started_at = now()
    try:
        raw_body = fetch_with_retry(feed.url, retry_policy, fetcher=fetcher)
    except Exception as exc:  # noqa: BLE001 - se registra como ingestion_run fallido, no se relanza
        finished_at = now()
        with conn.transaction():
            db.insert_ingestion_run(
                conn,
                feed_name=feed.name,
                source_timestamp=None,
                started_at=started_at,
                finished_at=finished_at,
                status="error",
                entity_count=None,
                payload_hash=hashlib.sha256(b"").hexdigest(),
            )
        logger.error("run_cycle: %s falló tras reintentos: %s", feed.name, exc)
        return CycleResult(feed.name, "error", None, 0, 0, error=str(exc))

    raw_model = _RAW_FEEDS[feed.name]
    parsed = raw_model.model_validate_json(raw_body)
    health = feed_health_from_raw(feed.name, parsed)
    received_at = now()
    payload_hash = hashlib.sha256(raw_body).hexdigest()

    # Todo el ciclo (alta de `source_ingestion_run` + inserciones de entidades)
    # se compromete como una sola transacción: o se registra el ciclo completo
    # (ejecución + lo que se pudo persistir), o no se registra nada de él.
    with conn.transaction():
        snapshot_history = quality_db.recent_feed_snapshots(conn, feed.name)
        run_id = db.insert_ingestion_run(
            conn,
            feed_name=feed.name,
            source_timestamp=health.source_timestamp,
            started_at=started_at,
            finished_at=now(),
            status="ok",
            entity_count=health.entity_count,
            payload_hash=payload_hash,
        )

        snapshot_events = check_duplicate_snapshot(
            current=SnapshotObservation(payload_hash=payload_hash, received_at=received_at),
            consecutive_history=snapshot_history,
            feed_name=feed.name,
            entity_type={
                "vehicle_positions": "vehicle_position",
                "trip_updates": "trip_update",
                "alerts": "alert",
            }[feed.name],
        )
        quality_db.insert_quality_events(conn, snapshot_events)

        if feed.name == "vehicle_positions":
            inserted, deduped, skipped = _persist_vehicle_positions(
                conn, parsed, received_at, run_id
            )
        elif feed.name == "trip_updates":
            inserted, deduped, skipped = _persist_trip_updates(conn, parsed, received_at, run_id)
        else:
            inserted, deduped, skipped = _persist_alerts(conn, parsed, received_at, run_id)

    logger.info(
        "run_cycle: %s ok (run_id=%d, entidades=%d, insertadas=%d, dedup=%d, fuera_de_alcance=%d)",
        feed.name,
        run_id,
        health.entity_count,
        inserted,
        deduped,
        skipped,
    )
    return CycleResult(feed.name, "ok", health.entity_count, inserted, deduped, skipped, run_id=run_id)


def _persist_vehicle_positions(conn, parsed, received_at, run_id: int) -> tuple[int, int, int]:
    inserted = deduped = skipped = 0
    for obs in vehicle_positions_to_canonical(parsed):
        if obs.nucleo_prefix != MADRID_PREFIX:
            skipped += 1
            continue
        previous_hash = db.latest_payload_hash(
            conn, "vehicle_position_observation", obs.source_vehicle_id
        )
        if previous_hash == obs.payload_hash:
            deduped += 1
            continue
        previous = quality_db.latest_vehicle_position(conn, obs.source_vehicle_id)
        quality_events = evaluate_vehicle_position(
            obs, received_at=received_at, previous=previous
        )
        db.insert_vehicle_position_observation(
            conn,
            obs,
            received_at=received_at,
            ingestion_run_id=run_id,
            quality_flags=quality_db.observation_flags(quality_events),
        )
        quality_db.insert_quality_events(conn, quality_events)
        inserted += 1
    return inserted, deduped, skipped


def _persist_trip_updates(conn, parsed, received_at, run_id: int) -> tuple[int, int, int]:
    inserted = deduped = skipped = 0
    for obs in trip_updates_to_canonical(parsed):
        if obs.nucleo_prefix != MADRID_PREFIX:
            skipped += 1
            continue
        previous_hash = db.latest_payload_hash(conn, "trip_update_observation", obs.source_trip_id)
        if previous_hash == obs.payload_hash:
            deduped += 1
            continue
        previous_observed_at = quality_db.latest_observed_at(
            conn, "trip_update_observation", obs.source_trip_id
        )
        quality_events = check_missing_id(
            identifier=obs.source_trip_id,
            id_field="source_trip_id",
            occurred_at=received_at,
            entity_type="trip_update",
            entity_ref=obs.source_trip_id,
        )
        quality_events += check_stale(
            observed_at=obs.observed_at,
            received_at=received_at,
            entity_type="trip_update",
            entity_ref=obs.source_trip_id,
        )
        quality_events += check_clock_anomaly(
            observed_at=obs.observed_at,
            received_at=received_at,
            previous_observed_at=previous_observed_at,
            entity_type="trip_update",
            entity_ref=obs.source_trip_id,
        )
        db.insert_trip_update_observation(
            conn, obs, received_at=received_at, ingestion_run_id=run_id
        )
        quality_db.insert_quality_events(conn, quality_events)
        inserted += 1
    return inserted, deduped, skipped


def _persist_alerts(conn, parsed, received_at, run_id: int) -> tuple[int, int, int]:
    inserted = deduped = skipped = 0
    for alert in alerts_to_canonical(parsed):
        if MADRID_PREFIX not in alert.nucleo_prefixes:
            skipped += 1
            continue
        previous_hash = db.latest_payload_hash(conn, "service_alert", alert.source_alert_id)
        if previous_hash == alert.payload_hash:
            deduped += 1
            continue
        quality_events = check_missing_id(
            identifier=alert.source_alert_id,
            id_field="source_alert_id",
            occurred_at=received_at,
            entity_type="alert",
            entity_ref=alert.source_alert_id,
        )
        db.insert_service_alert(conn, alert, ingestion_run_id=run_id)
        quality_db.insert_quality_events(conn, quality_events)
        inserted += 1
    return inserted, deduped, skipped
