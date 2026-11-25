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

from apps.api import main
from services.collector.collector import run_cycle
from services.collector.config import FeedConfig
from services.collector.http_client import RetryPolicy
from tests.clock import api_wall_clock
from tests.postgres import connect_disposable_or_skip

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
FIRST = "2026-11-19T03:58:04Z"
SECOND = "2026-11-19T03:59:21Z"
BETWEEN = "2026-11-19T03:58:10Z"
BEFORE = "2026-11-19T03:58:03Z"
CLOCK_ENDPOINTS = ("health", "catalog", "snapshot", "stations/35607/board")
GTFS_ENDPOINTS = ("health", "catalog", "snapshot")


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

    def test_ingestion_is_eligible_at_the_exact_clock(self) -> None:
        self._ingest("vehicle_positions", "first-vehicles", FIRST)
        self._clock("2027-01-15T12:00:00Z")
        with TestClient(main.app) as client:
            for at, poll_age, vehicles in (
                ("2026-11-19T03:58:03.999999Z", None, 0),
                (FIRST, 0, 1),
                ("2026-11-19T03:58:04.000001Z", 0.000001, 1),
            ):
                with self.subTest(at=at):
                    health = self._get(client, "health", at)
                    body = self._get(client, "snapshot", at)
                    self.assertEqual(health["feeds"], body["feeds"])
                    self.assertEqual(self._feed(body)["poll_age_s"], poll_age)
                    self.assertEqual(body["counts"]["vehicles_total"], vehicles)

    def test_empty_database_declares_missing_feeds_after_gtfs_expiry(self) -> None:
        self.assertEqual(self.conn.execute("SELECT count(*) FROM source_ingestion_run").fetchone(), (0,))
        self._clock("2027-01-15T12:00:00Z")
        with TestClient(main.app) as client:
            health = self._get(client, "health")
            body = self._get(client, "snapshot")
        self.assertEqual(body["gtfs_status"], "expired")
        self.assertEqual(health["feeds"], body["feeds"])
        self.assertCountEqual(
            [feed["feed_name"] for feed in body["feeds"]],
            ["vehicle_positions", "trip_updates", "alerts"],
        )
        for feed in body["feeds"]:
            self.assertEqual(feed["status"], "unknown")
            self.assertEqual(feed["reason"], "no_ingestion_at_or_before_clock")
            self.assertIsNone(feed["data_age_s"])
            self.assertIsNone(feed["poll_age_s"])
        self.assertEqual(body["vehicles"], [])
        self.assertIsNone(body["revision"]["sequence"])

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

    def test_extreme_replay_clocks_are_rejected_on_every_surface(self) -> None:
        with TestClient(main.app, raise_server_exceptions=False) as client:
            for at in (
                "0001-01-01T00:00:00Z",
                "0001-01-01T00:30:00+01:00",
                "9999-12-31T23:59:59Z",
                "9999-12-31T23:30:00-01:00",
            ):
                for endpoint in CLOCK_ENDPOINTS:
                    with self.subTest(at=at, endpoint=endpoint):
                        reply = client.get(f"/api/v1/{endpoint}", params={"at": at})
                        self.assertEqual(reply.status_code, 400, reply.text)
                        self.assertIn("'at' fuera del rango", reply.json()["detail"])
            # En los bordes admitidos se puede calcular incluso la ventana
            # máxima del tablero sin desbordar los días de servicio.
            for at in ("0001-01-04T00:00:00Z", "9999-12-28T23:59:59Z"):
                with self.subTest(at=at, endpoint="board"):
                    reply = client.get(
                        "/api/v1/stations/35607/board",
                        params={"at": at, "lookback_s": 7200, "lookahead_s": 86400},
                    )
                    self.assertEqual(reply.status_code, 200, reply.text)

    def test_vehicle_list_and_detail_exclude_future_ingestions(self) -> None:
        self._both_cuts()
        self._clock(BETWEEN)
        with TestClient(main.app) as client:
            listing = self._get(client, "live/vehicles")
            detail = self._get(client, "live/vehicles/mp026a-existing")
            future = client.get("/api/v1/live/vehicles/mp026a-second-only")
        self.assertEqual(future.status_code, 404)
        self.assertEqual(listing, [detail])
        self.assertEqual(detail["observation"]["reported_at"], "2026-11-19T03:58:00Z")
        self.assertEqual(detail["delay"]["seconds"], 20)

    def test_snapshot_marks_each_nonvalid_gtfs_state_as_degraded(self) -> None:
        with TestClient(main.app) as client:
            for at, expected, reason in (
                ("2026-11-18T12:00:00Z", "unknown", "aún no ha entrado en vigencia"),
                ("2026-12-04T12:00:00Z", "stale", "vence el"),
                ("2026-12-07T12:00:00Z", "error", "venció el"),
                ("2026-11-19T12:00:00Z", None, None),
            ):
                with self.subTest(at=at):
                    body = self._get(client, "snapshot", at)
                    items = [item for item in body["degraded"] if item["resource"] == "gtfs"]
                    if expected is None:
                        self.assertEqual(items, [])
                        continue
                    self.assertEqual(len(items), 1)
                    item = items[0]
                    self.assertEqual(item["status"], expected)
                    self.assertIn(reason, item["reason"])
                    for absent in ("feed_name", "last_valid_source_timestamp", "data_age_s", "poll_age_s"):
                        self.assertIsNone(item[absent])

    def test_only_replay_filters_future_observation_timestamps(self) -> None:
        # Estos payloads tienen GPS y retrasos posteriores al sondeo simulado.
        self._ingest("vehicle_positions", "second-vehicles", FIRST)
        self._ingest("trip_updates", "second-delays", FIRST)
        clock = "2026-11-19T03:58:05Z"
        self._clock(clock)
        with TestClient(main.app) as client:
            self.assertEqual(self._get(client, "snapshot", clock)["vehicles"], [])
            board = self._get(client, "stations/35607/board", clock)
            entry = next(row for row in board["entries"] if row["trip_id"] == "1022J19502C5")
            self.assertEqual(entry["circulation_source"], "scheduled_only")
            self.assertIsNone(entry["departure"]["delay_seconds"])
        self._configure_live()
        with TestClient(main.app) as client:
            live = self._get(client, "snapshot")
            board = self._get(client, "stations/35607/board")
            detail = self._get(client, "live/vehicles/mp026a-existing")
            listing = self._get(client, "live/vehicles")
        vehicles = {row["vehicle_id"]: row for row in live["vehicles"]}
        self.assertIn("mp026a-existing", vehicles)
        vehicle = vehicles["mp026a-existing"]
        self.assertEqual(vehicle["timestamps"]["gps_observed_at"], "2026-11-19T03:58:08Z")
        self.assertEqual(vehicle["delay"]["seconds"], 80)
        entry = next(row for row in board["entries"] if row["trip_id"] == "1022J19502C5")
        self.assertEqual(entry["circulation_source"], "observed")
        self.assertEqual(entry["departure"]["delay_seconds"], 80)
        self.assertIn(detail, listing)
        self.assertEqual(detail["observation"]["reported_at"], "2026-11-19T03:58:08Z")
        self.assertEqual(detail["delay"]["seconds"], 80)

    def _configure_live(self) -> None:
        # El arranque live exige una ruta externa. Copiar la fixture íntegra
        # al sandbox permite probar sus fechas reales sin acceso a la red.
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "gtfs"
        shutil.copytree(FIXTURES / "gtfs_c5_real", root)
        self.enterContext(patch.dict(os.environ, {
            "MADRID_PULSE_MODE": "live",
            "MADRID_PULSE_GTFS_SOURCE": str(root),
        }))

    def _clock(self, instant: str) -> None:
        self.enterContext(api_wall_clock(datetime.fromisoformat(instant)))

    def test_live_gtfs_validity_changes_after_startup_and_invalidates_catalog_cache(self) -> None:
        self._configure_live()
        self._clock("2026-12-01T12:00:00Z")
        with TestClient(main.app) as client:
            catalog = client.get("/api/v1/catalog")
            self.assertEqual(catalog.status_code, 200)
            etag = catalog.headers["etag"]
            catalog_version = catalog.json()["catalog_version"]
            self.assertEqual(catalog.json()["gtfs_valid_until"], "2026-12-06")
            for instant, expected, reason in (
                ("2026-12-03T22:59:59Z", "valid", None),
                ("2026-12-03T23:00:00Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-05T12:00:00Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-06T22:59:59Z", "expiring", "gtfs_expiry_approaching"),
                ("2026-12-06T23:00:00Z", "expired", "gtfs_validity_ended"),
                ("2026-12-07T12:00:00Z", "expired", "gtfs_validity_ended"),
            ):
                self._clock(instant)
                for endpoint in GTFS_ENDPOINTS:
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
        for wall in ("2026-12-20T12:00:00Z", "2027-01-15T12:00:00Z"):
            with api_wall_clock(datetime.fromisoformat(wall)), TestClient(main.app) as client:
                for at, expected in (
                    ("2026-11-18T22:59:59Z", "not_yet_valid"),
                    ("2026-11-18T23:00:00Z", "valid"),
                    ("2026-11-20T14:32:10Z", "valid"),
                    ("2026-12-06T22:59:59Z", "expiring"),
                    ("2026-12-06T23:00:00Z", "expired"),
                    ("2026-12-07T12:00:00Z", "expired"),
                    (None, "expired"),
                ):
                    for endpoint in GTFS_ENDPOINTS:
                        with self.subTest(wall=wall, at=at, endpoint=endpoint):
                            body = self._get(client, endpoint, at)
                            self.assertEqual(body["gtfs_status"], expected)
                            if endpoint == "snapshot":
                                self.assertEqual(body["generated_at"], at or wall)

    def test_live_http_still_rejects_an_explicit_at(self) -> None:
        self._configure_live()
        self._clock("2026-12-05T12:00:00Z")
        with TestClient(main.app) as client:
            for endpoint in CLOCK_ENDPOINTS:
                with self.subTest(endpoint=endpoint):
                    response = client.get(f"/api/v1/{endpoint}", params={"at": BETWEEN})
                    self.assertEqual(response.status_code, 400)

    def test_live_startup_still_rejects_an_expired_source(self) -> None:
        self._configure_live()
        self._clock("2026-12-07T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "GTFS fuera de vigencia para live"):
            with TestClient(main.app):
                pass
