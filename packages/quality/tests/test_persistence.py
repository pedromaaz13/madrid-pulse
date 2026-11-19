"""Integración real con PostgreSQL; toda inserción termina en rollback."""

from __future__ import annotations

import unittest
from pathlib import Path
from datetime import datetime, timezone

import psycopg

from packages.contracts.canonical import VehiclePositionObservation
from packages.quality import db as quality_db
from packages.quality.engine import QualityEvent
from services.collector import db as collector_db
from services.collector.config import CollectorConfig
from services.collector.collector import run_cycle
from services.collector.config import FeedConfig
from services.collector.http_client import RetryPolicy

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def _connect_or_skip() -> psycopg.Connection:
    try:
        return psycopg.connect(CollectorConfig().database_url, autocommit=False, connect_timeout=3)
    except psycopg.OperationalError as exc:
        raise unittest.SkipTest(f"PostgreSQL local no disponible: {exc}")


class QualityPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)

    def test_event_and_vehicle_flags_are_persisted_atomically(self) -> None:
        now = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        run_id = collector_db.insert_ingestion_run(
            self.conn,
            feed_name="vehicle_positions",
            source_timestamp=now,
            started_at=now,
            finished_at=now,
            status="ok",
            entity_count=1,
            payload_hash="b" * 64,
        )
        obs = VehiclePositionObservation(
            source_vehicle_id="quality-test-vehicle",
            source_trip_id="100R15055C5",
            observed_at=now,
            latitude=40.4,
            longitude=-3.7,
            raw_vehicle_label="synthetic quality persistence test",
            payload_hash="c" * 64,
        )
        event = QualityEvent(
            occurred_at=now,
            entity_type="vehicle_position",
            entity_ref=obs.source_vehicle_id,
            flag="implausible_speed",
            details={"synthetic": True},
            applies_to_observation=True,
        )
        collector_db.insert_vehicle_position_observation(
            self.conn,
            obs,
            received_at=now,
            ingestion_run_id=run_id,
            quality_flags=quality_db.observation_flags([event]),
        )
        quality_db.insert_quality_events(self.conn, [event])

        flags = self.conn.execute(
            "SELECT quality_flags FROM vehicle_position_observation WHERE ingestion_run_id = %s",
            (run_id,),
        ).fetchone()[0]
        stored = self.conn.execute(
            "SELECT flag, details FROM data_quality_event WHERE entity_ref = %s",
            (obs.source_vehicle_id,),
        ).fetchone()
        self.assertEqual(flags, ["implausible_speed"])
        self.assertEqual(stored[0], "implausible_speed")
        self.assertEqual(stored[1], {"synthetic": True})

    def test_collector_marks_feed_only_after_long_identical_window(self) -> None:
        """La deduplicación normal del primer intervalo no es una anomalía."""
        body = (FIXTURES_DIR / "vehicle_positions.json").read_bytes()
        feed = FeedConfig("vehicle_positions", "https://example.invalid/vehicle_positions.json")
        policy = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=1.0)
        first_time = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
        second_time = datetime(2026, 11, 20, 10, 3, 1, tzinfo=timezone.utc)

        first = run_cycle(
            feed,
            self.conn,
            policy,
            fetcher=lambda url, timeout: body,
            now=lambda: first_time,
        )
        normal_count = self.conn.execute(
            "SELECT count(*) FROM data_quality_event "
            "WHERE flag = 'duplicate_snapshot' AND entity_ref = 'feed:vehicle_positions' "
            "AND occurred_at = %s",
            (first_time,),
        ).fetchone()[0]
        second = run_cycle(
            feed,
            self.conn,
            policy,
            fetcher=lambda url, timeout: body,
            now=lambda: second_time,
        )
        frozen_count = self.conn.execute(
            "SELECT count(*) FROM data_quality_event "
            "WHERE flag = 'duplicate_snapshot' AND entity_ref = 'feed:vehicle_positions' "
            "AND occurred_at = %s",
            (second_time,),
        ).fetchone()[0]

        self.assertEqual((first.status, second.status), ("ok", "ok"))
        self.assertEqual(normal_count, 0)
        self.assertEqual(frozen_count, 1)


if __name__ == "__main__":
    unittest.main()
