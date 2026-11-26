"""MP-036: regresión del ancla efectiva en snapshot y replay PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from apps.api import snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import point_at_arc_length
from services.collector import db as writer
from tests.postgres import connect_disposable_or_skip

DATA = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "mp036"
BASE = datetime.fromisoformat("2026-11-26T08:46:00+00:00")
TRIP = "1029J20793C5"
OTHER_TRIP = "1029J20231C4a"
VEHICLE = "mp036-synthetic"


class AnchorHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((DATA / "manifest.json").read_text())
        for name, digest in manifest["sha256"].items():
            if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != digest:
                raise AssertionError(f"Checksum de fixture incorrecto: {name}")
        cls.config = replace(ApiConfig.from_env(), gtfs_fixture_dir=DATA / "gtfs",
                             short_name="", mode="replay", display_lag_s=0)
        cls.network = load_network(cls.config)
        route_id = cls.network.topology.resolve_trip_route_id(TRIP)
        coverage = snapshot.coverage_for_trip(cls.network, TRIP, route_id)
        assert coverage is not None
        engine = cls.network.engine_for(coverage)
        assert engine is not None
        cls.engine = engine
        cls.schedule = engine.trip_schedule(TRIP)

    def setUp(self):
        self.conn = connect_disposable_or_skip()
        self.addCleanup(self.conn.close)
        self.conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        self.run_ids = []

    def insert(self, position, started_at, received_at, source_timestamp):
        run = writer.insert_ingestion_run(
            self.conn, feed_name="vehicle_positions", started_at=started_at,
            finished_at=received_at, source_timestamp=source_timestamp, status="ok",
            entity_count=1, payload_hash=position.payload_hash,
        )
        self.run_ids.append(run)
        writer.insert_vehicle_position_observation(
            self.conn, position, received_at=received_at, ingestion_run_id=run,
        )

    def synthetic(self, offset, progress, *, started=None, trip=TRIP):
        at = BASE + timedelta(seconds=offset)
        start = BASE + timedelta(seconds=offset if started is None else started)
        lat, lon = point_at_arc_length(
            list(self.engine.corridor.segments[0]), self.schedule.physical_arc(progress)
        )
        position = VehiclePositionObservation(
            source_vehicle_id=VEHICLE, source_trip_id=trip, observed_at=at,
            latitude=lat, longitude=lon, current_status="IN_TRANSIT_TO",
            raw_vehicle_label=VEHICLE,
            payload_hash=hashlib.sha256(f"{VEHICLE}:{trip}:{at}".encode()).hexdigest(),
        )
        self.insert(position, start, max(at, start), at)
        return position

    def frame(self, at, vehicle=VEHICLE, *, lag=0, config=None):
        result = snapshot.build_snapshot(
            self.conn, self.network, config or self.config, at, display_lag_s=lag
        )
        return next(row for row in result.vehicles if row.vehicle_id == vehicle)

    def assert_anchor(self, frame, observation, at):
        self.assertEqual(frame.rendered.coordinate_space, "map_matched")
        self.assertEqual(frame.rendered.last_confirmed_at, observation.observed_at)
        self.assertEqual(frame.rendered.anchor_observed_at, observation.observed_at)
        self.assertAlmostEqual(
            frame.rendered.anchor_age_s, (at - observation.observed_at).total_seconds()
        )

    def check_capture(self, vehicle, a_progress):
        rows = json.loads((DATA / "observations.json").read_text())[vehicle]
        samples = []
        for row in rows:
            started = datetime.fromisoformat(row.pop("started_at"))
            received = datetime.fromisoformat(row.pop("received_at"))
            stamp = datetime.fromisoformat(row.pop("source_timestamp"))
            position = VehiclePositionObservation.model_validate({**row, "raw_vehicle_label": vehicle})
            self.insert(position, started, received, stamp)
            samples.append((started, position, received, stamp))
        _, a, _, _ = samples[0]
        b_at, b, received, stamp = samples[1]
        b_frame = self.frame(b_at, vehicle)
        self.assert_anchor(b_frame, a, b_at)
        self.assertEqual(b_frame.raw.payload_hash, b.payload_hash)
        self.assertEqual(b_frame.raw.lat, b.latitude)
        self.assertEqual(b_frame.raw.lon, b.longitude)
        self.assertEqual(b_frame.timestamps.received_at, received)
        self.assertEqual(b_frame.timestamps.feed_published_at, stamp)
        self.assertAlmostEqual(b_frame.rendered.last_confirmed_progress_m, a_progress, places=5)
        c_at, c, _, _ = samples[2]
        c_frame = self.frame(c_at, vehicle)
        self.assert_anchor(c_frame, c, c_at)
        self.assertAlmostEqual(c_frame.rendered.last_confirmed_progress_m, a_progress, places=5)

    def test_capture_20231(self):
        self.check_capture("20231", 68.387400)

    def test_capture_20793(self):
        self.check_capture("20793", 12175.342547)

    def test_consecutive_rejections(self):
        a = self.synthetic(0, 1000)
        self.synthetic(1, 11000)
        b2 = self.synthetic(2, 11020)
        c = self.synthetic(3, 1000)
        frame = self.frame(b2.observed_at)
        self.assertEqual(frame.raw.payload_hash, b2.payload_hash)
        self.assertIn("implausible_speed", frame.quality.flags)
        self.assert_anchor(frame, a, b2.observed_at)
        self.assert_anchor(self.frame(c.observed_at), c, c.observed_at)

    def test_valid_recovery_after_rejection(self):
        self.synthetic(0, 3000)
        self.synthetic(1, 13000)
        b = self.synthetic(8, 2250)
        c = self.synthetic(16, 1500)
        # Dos pasos de −750 m. C es coherente con B, pero quedaría rechazado
        # por retroceso si se comparara con el ancla inicial a 3000 m.
        self.assert_anchor(self.frame(b.observed_at), b, b.observed_at)
        self.assert_anchor(self.frame(c.observed_at), c, c.observed_at)

    def test_trip_change_breaks_history_even_if_trip_id_repeats(self):
        self.synthetic(0, 24000)
        self.synthetic(1, 7000, trip=OTHER_TRIP)
        a = self.synthetic(2, 2000)
        b = self.synthetic(3, 12000)
        c = self.synthetic(4, 2000)
        self.assert_anchor(self.frame(a.observed_at), a, a.observed_at)
        self.assert_anchor(self.frame(b.observed_at), a, b.observed_at)
        self.assert_anchor(self.frame(c.observed_at), c, c.observed_at)

    def test_replay_applies_both_clocks_to_history(self):
        a = self.synthetic(0, 1000)
        b = self.synthetic(10, 11000, started=2)
        c = self.synthetic(20, 1000, started=30)
        before_b = BASE + timedelta(seconds=9)
        before_c_run = BASE + timedelta(seconds=29)
        self.assertEqual(self.frame(before_b).raw.payload_hash, a.payload_hash)
        frame = self.frame(before_c_run)
        self.assertEqual(frame.raw.payload_hash, b.payload_hash)
        self.assert_anchor(frame, a, before_c_run)
        visible = BASE + timedelta(seconds=30)
        self.assert_anchor(self.frame(visible), c, visible)

    def test_buffer_uses_only_accepted_interpolation_endpoints(self):
        self.conn.execute(
            "SELECT set_config('madrid_pulse.anchor_profile', %s, true)",
            (self.network.anchor_profile(self.config.thresholds),),
        )
        a = self.synthetic(0, 1000)
        self.synthetic(5, 11000)
        c = self.synthetic(20, 1100)
        frame = self.frame(c.observed_at, lag=10)
        self.assertEqual(frame.rendered.rendering_method, "interpolated_between_known_anchors")
        self.assertEqual(frame.rendered.last_confirmed_at, c.observed_at)
        self.assertAlmostEqual(frame.rendered.progress_m, 1050, places=1)
        self.assertEqual(frame.raw.payload_hash, c.payload_hash)
        self.assertNotEqual(frame.raw.payload_hash, a.payload_hash)

    def test_truncated_history_does_not_promote_first_visible_outlier(self):
        self.synthetic(0, 1000)
        self.synthetic(1, 11000)
        self.synthetic(2, 11025)
        c = self.synthetic(3, 11050)
        # El config anterior carece de la opción. Entonces se ejecuta con
        # su profundidad por defecto y se ve la misma regresión funcional.
        config = self.config
        if hasattr(config, "anchor_history_depth"):
            config = replace(config, anchor_history_depth=3)
        frame = self.frame(c.observed_at, config=config)
        self.assertEqual(frame.raw.payload_hash, c.payload_hash)
        self.assertEqual(frame.rendered.rendering_method, "schedule_only")
        self.assertIsNone(frame.rendered.last_confirmed_at)
        self.assertIn("anchor_history_truncated", frame.quality.flags)

    def test_restart_rebuilds_same_snapshot_in_two_processes(self):
        self.synthetic(0, 1000)
        self.synthetic(1, 11000)
        c = self.synthetic(2, 1000)
        self.conn.commit()
        self.addCleanup(self.delete_committed_runs)
        script = """
import sys
from fastapi.testclient import TestClient
from apps.api.main import app
with TestClient(app) as client:
    response = client.get('/api/v1/snapshot', params={'at': sys.argv[1], 'display_lag_s': 0})
    response.raise_for_status()
    print(response.text)
"""
        env = dict(os.environ, MADRID_PULSE_GTFS_SOURCE=str(DATA / "gtfs"),
                   MADRID_PULSE_SHORT_NAME="", MADRID_PULSE_MODE="replay")
        args = [sys.executable, "-c", script, c.observed_at.isoformat()]
        first, second = (
            subprocess.check_output(args, env=env, timeout=30) for _ in range(2)
        )
        self.assertEqual(first, second)
        frame = next(row for row in json.loads(first)["vehicles"] if row["vehicle_id"] == VEHICLE)
        self.assertEqual(datetime.fromisoformat(frame["rendered"]["last_confirmed_at"]), c.observed_at)

    def delete_committed_runs(self):
        with self.conn.transaction():
            self.conn.execute(
                "DELETE FROM vehicle_position_observation WHERE ingestion_run_id = ANY(%s)",
                (self.run_ids,),
            )
            self.conn.execute("DELETE FROM source_ingestion_run WHERE id = ANY(%s)", (self.run_ids,))
