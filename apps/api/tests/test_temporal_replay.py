"""Regresiones HTTP de FR-02 y FR-19 con ingesta real y datos versionados."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api import gtfs_source, main, snapshot
from services.collector.collector import run_cycle
from services.collector.config import FeedConfig
from services.collector.http_client import RetryPolicy
from tests.postgres import connect_disposable_or_skip

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
FIRST = "2026-11-19T03:58:04Z"
SECOND = "2026-11-19T03:59:21Z"
BETWEEN = "2026-11-19T03:58:10Z"
BEFORE = "2026-11-19T03:58:03Z"


class TemporalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        # run_cycle usa transacciones propias. Una ya abierta las convierte
        # en savepoints y permite revertir todos los cortes después de probar.
        self.conn.execute("SELECT 1")
        main.app.dependency_overrides[main.get_connection] = lambda: self.conn
        self.addCleanup(main.app.dependency_overrides.clear)
        self.enterContext(patch.dict(os.environ, {
            "MADRID_PULSE_MODE": "replay",
            "MADRID_PULSE_GTFS_SOURCE": str(FIXTURES / "gtfs_c5_real"),
            "MADRID_PULSE_NETWORK_ID": "10",
            "MADRID_PULSE_SHORT_NAME": "C5",
            "MADRID_PULSE_FEED_STALE_AFTER_S": "180",
            "MADRID_PULSE_GTFS_EXPIRING_DAYS": "2",
        }))

    def _ingest(self, feed: str, file: str, instant: str) -> None:
        blob = (FIXTURES / "mp026a" / f"{file}.json").read_bytes()
        result = run_cycle(
            FeedConfig(feed, f"https://example.invalid/{feed}"),
            self.conn,
            RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=5.0),
            fetcher=lambda url, timeout: blob,
            now=lambda: datetime.fromisoformat(instant),
        )
        self.assertEqual(result.status, "ok", result.error)

    def _both_cuts(self) -> None:
        self._ingest("vehicle_positions", "first-vehicles", FIRST)
        self._ingest("trip_updates", "first-delays", FIRST)
        self._ingest("vehicle_positions", "second-vehicles", SECOND)
        self._ingest("trip_updates", "second-delays", SECOND)

    def _get(self, client: TestClient, endpoint: str, at: str | None = None) -> dict:
        response = client.get(f"/api/v1/{endpoint}", params={"at": at} if at else None)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _feed(self, body: dict, name: str = "vehicle_positions") -> dict:
        return next(feed for feed in body["feeds"] if feed["feed_name"] == name)

    def test_snapshot_uses_first_ingestion_and_its_observations(self) -> None:
        self._both_cuts()
        with TestClient(main.app) as client:
            snapshot_at = self._get(client, "snapshot", BETWEEN)
            at_second_cut = self._get(client, "snapshot", SECOND)
        feed = self._feed(snapshot_at)
        self.assertEqual(
            (feed["status"], feed["source_timestamp"], feed["data_age_s"], feed["poll_age_s"]),
            ("ok", "2026-11-19T03:58:02Z", 8, 6),
        )
        vehicles = {vehicle["vehicle_id"]: vehicle for vehicle in snapshot_at["vehicles"]}
        self.assertEqual(set(vehicles), {"mp026a-existing"})
        vehicle = vehicles["mp026a-existing"]
        self.assertEqual(vehicle["timestamps"]["gps_observed_at"], "2026-11-19T03:58:00Z")
        self.assertEqual(vehicle["delay"]["seconds"], 20)
        self.assertLess(snapshot_at["revision"]["sequence"], at_second_cut["revision"]["sequence"])
        self.assertEqual(self._feed(at_second_cut)["poll_age_s"], 0)
        self.assertEqual(at_second_cut["counts"]["vehicles_total"], 2)

    def test_health_and_snapshot_use_same_clock(self) -> None:
        self._both_cuts()
        with TestClient(main.app) as client:
            health_at = self._get(client, "health", BETWEEN)
            snapshot_at = self._get(client, "snapshot", BETWEEN)
        self.assertEqual(health_at["feeds"], snapshot_at["feeds"])
        self.assertEqual(self._feed(health_at)["source_timestamp"], "2026-11-19T03:58:02Z")
        self.assertEqual(self._feed(health_at)["poll_age_s"], 6)

    def test_before_first_ingestion_is_declared_without_ages(self) -> None:
        self._both_cuts()
        with TestClient(main.app) as client:
            snapshot_at = self._get(client, "snapshot", BEFORE)
            for endpoint in ("snapshot", "health"):
                with self.subTest(endpoint=endpoint):
                    feed = self._feed(self._get(client, endpoint, BEFORE))
                    self.assertEqual(feed["status"], "unknown")
                    self.assertIsNone(feed["source_timestamp"])
                    self.assertIsNone(feed["data_age_s"])
                    self.assertIsNone(feed["poll_age_s"])
                    self.assertEqual(feed["reason"], "no_ingestion_at_or_before_clock")
        self.assertEqual(snapshot_at["vehicles"], [])
        self.assertIsNone(snapshot_at["revision"]["sequence"])
        degradation = next(entry for entry in snapshot_at["degraded"] if entry["resource"] == "vehicles")
        self.assertIsNone(degradation["poll_age_s"])

    def test_future_source_timestamp_has_its_own_reason(self) -> None:
        self._ingest("vehicle_positions", "future-header", FIRST)
        with TestClient(main.app) as client:
            for endpoint in ("snapshot", "health"):
                with self.subTest(endpoint=endpoint):
                    feed = self._feed(self._get(client, endpoint, BETWEEN))
                    self.assertEqual(feed["status"], "unknown")
                    self.assertEqual(feed["source_timestamp"], "2026-11-19T03:59:21Z")
                    self.assertIsNone(feed["data_age_s"])
                    self.assertEqual(feed["poll_age_s"], 6)
                    self.assertEqual(feed["reason"], "source_timestamp_in_future")

    def test_board_excludes_delays_from_future_ingestions(self) -> None:
        self._both_cuts()
        with TestClient(main.app) as client:
            board = self._get(client, "stations/35607/board", BETWEEN)
        entry = next(entry for entry in board["entries"] if entry["trip_id"] == "1022J19502C5")
        self.assertEqual(entry["departure"]["delay_seconds"], 20)

    def _configure_live(self) -> None:
        # El catálogo live rechaza fixtures dentro del repo. Copiar al sandbox
        # y extender el último servicio permite probar el límite del 19/12.
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "gtfs"
        shutil.copytree(FIXTURES / "gtfs_c5_real", root)
        calendar = root / "calendar.txt"
        calendar.write_text(calendar.read_text().replace("20261206,20261206", "20261206,20261219"))
        self.enterContext(patch.dict(os.environ, {
            "MADRID_PULSE_MODE": "live",
            "MADRID_PULSE_GTFS_SOURCE": str(root),
        }))

    def _clock(self, instant: str) -> None:
        clock = datetime.fromisoformat(instant)

        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.astimezone(tz)

        self.enterContext(patch.object(main, "now_utc", return_value=clock))
        self.enterContext(patch.object(gtfs_source, "datetime", FrozenDatetime))
        self.enterContext(patch.object(snapshot, "datetime", FrozenDatetime))

    def test_live_gtfs_validity_changes_after_startup_and_invalidates_catalog_cache(self) -> None:
        self._configure_live()
        self._clock("2026-12-10T12:00:00Z")
        with TestClient(main.app) as client:
            catalog = client.get("/api/v1/catalog")
            self.assertEqual(catalog.status_code, 200)
            etag = catalog.headers["etag"]
            catalog_version = catalog.json()["catalog_version"]
            for instant, expected, reason in (
                ("2026-12-16T22:59:59Z", "valid", None),
                ("2026-12-16T23:00:00Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-18T12:00:00Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-19T22:59:59Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-19T23:00:00Z", "expired", "gtfs_validity_ended"),
                ("2026-12-20T12:00:00Z", "expired", "gtfs_validity_ended"),
            ):
                self._clock(instant)
                for endpoint in ("health", "catalog", "snapshot"):
                    with self.subTest(instant=instant, endpoint=endpoint):
                        body = self._get(client, endpoint)
                        self.assertEqual(body.get("gtfs_status"), expected)
                        self.assertEqual(body.get("gtfs_status_reason"), reason)
                if expected != "valid":
                    with self.subTest(instant=instant, endpoint="conditional catalog"):
                        self._assert_catalog_cache(client, etag, catalog_version, expected)

    def _assert_catalog_cache(
        self, client: TestClient, old_etag: str, catalog_version: str, expected: str
    ) -> None:
        refreshed = client.get("/api/v1/catalog", headers={"If-None-Match": old_etag})
        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(refreshed.json()["catalog_version"], catalog_version)
        self.assertEqual(refreshed.json()["gtfs_status"], expected)
        fresh_etag = refreshed.headers["etag"]
        unchanged = client.get("/api/v1/catalog", headers={"If-None-Match": fresh_etag})
        self.assertEqual(unchanged.status_code, 304)

    def test_replay_gtfs_validity_uses_at_instead_of_wall_clock(self) -> None:
        self._clock("2026-12-20T12:00:00Z")
        with TestClient(main.app) as client:
            for at, expected in (
                ("2026-11-18T12:00:00Z", "not_yet_valid"),
                ("2026-11-19T12:00:00Z", "valid"),
                ("2026-12-07T12:00:00Z", "expired"),
            ):
                for endpoint in ("health", "catalog", "snapshot"):
                    with self.subTest(at=at, endpoint=endpoint):
                        self.assertEqual(self._get(client, endpoint, at).get("gtfs_status"), expected)

    def test_live_http_still_rejects_an_explicit_at(self) -> None:
        self._configure_live()
        self._clock("2026-12-18T12:00:00Z")
        with TestClient(main.app) as client:
            for endpoint in ("snapshot", "stations/35607/board"):
                with self.subTest(endpoint=endpoint):
                    response = client.get(f"/api/v1/{endpoint}", params={"at": BETWEEN})
                    self.assertEqual(response.status_code, 400)

    def test_live_startup_still_rejects_an_expired_source(self) -> None:
        self._configure_live()
        self._clock("2026-12-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "GTFS fuera de vigencia para live"):
            with TestClient(main.app):
                pass
