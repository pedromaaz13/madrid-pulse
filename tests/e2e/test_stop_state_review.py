"""Contraejemplos de la revisión de MP-025a."""

from dataclasses import replace
from datetime import timedelta
import unittest
from unittest.mock import patch
import os

from services.collector import __main__ as collector
from packages.movement.profile import profile_matches
from tests.postgres import connect_disposable_or_skip

from apps.api import db, snapshot
from tests.e2e import test_stop_state as real
from tests.e2e import test_stop_state_db as integration


class ReviewCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        real.RealStops.setUpClass()
        cls.network = real.RealStops.network

    def test_phase_before_reference(self):
        from packages.movement import ProgressEnvelope

        at = real.RealStops.second["19667"].observed_at
        self.assertEqual(
            ProgressEnvelope(at, 10, 1, 20, 10, None).phase(at - timedelta(milliseconds=1)),
            "hold:null",
        )

    def test_unknown_profile_never_rewinds(self):
        for profile in (None, "version-distinta"):
            for vid, pos in real.RealStops.second.items():
                row = db.ObservedRow(
                    pos, pos.observed_at, ingestion_run_id=100, anchor_profile=profile
                )
                hist = db.VehicleHistory(vid, row, None)
                for age in (0, 179, 180, 181):
                    at = pos.observed_at + timedelta(seconds=age)
                    rendered = snapshot.build_vehicle_entry(
                        self.network,
                        real.RealStops.config,
                        hist,
                        None,
                        at,
                        at,
                        self.network.service_date_resolver(at),
                    ).rendered
                    self.assertEqual(rendered.progress_m, rendered.last_confirmed_progress_m)
                    self.assertEqual(rendered.frozen_basis, "anchor_version_changed")
                    if age <= 180:
                        self.assertEqual(
                            rendered.progress_envelope.hold_reason, "anchor_version_changed"
                        )

    def test_collector_without_gtfs_holds_from_first_frame(self):
        pos = real.RealStops.second["19667"]
        with connect_disposable_or_skip():
            pass

        def offline(feed, conn, policy, **kwargs):
            profile = conn.execute(
                "SELECT current_setting('madrid_pulse.anchor_profile',true)"
            ).fetchone()[0]
            self.assertIsNone(profile)
            row = db.ObservedRow(pos, pos.observed_at, ingestion_run_id=1, anchor_profile=profile)
            history = db.VehicleHistory(pos.source_vehicle_id, row, None)
            for age in (179, 180, 181):
                now = pos.observed_at + timedelta(seconds=age)
                frame = snapshot.build_vehicle_entry(
                    self.network,
                    real.RealStops.config,
                    history,
                    None,
                    now,
                    now,
                    self.network.service_date_resolver(now),
                ).rendered
                self.assertEqual(frame.progress_m, frame.last_confirmed_progress_m)
                self.assertEqual(frame.frozen_basis, "anchor_version_changed")
            raise SystemExit(0)

        with (
            patch.dict(os.environ, MADRID_PULSE_GTFS_SOURCE=""),
            patch.object(collector, "run_cycle", offline),
        ):
            with (
                self.assertLogs(collector.logger, level="WARNING") as logged,
                self.assertRaises(SystemExit) as exc,
            ):
                collector.main()
            self.assertEqual(exc.exception.code, 0)
            self.assertIn("Sin GTFS", str(logged.output))

    def test_profile_compares_only_the_selected_pattern(self):
        config = real.RealStops.config
        from apps.api.gtfs_source import load_network

        filtered = load_network(replace(config, short_name="C5"))
        with (
            connect_disposable_or_skip() as conn,
            patch.dict(os.environ, MADRID_PULSE_SHORT_NAME=""),
        ):
            collector._load_madrid_stop_ids(str(config.gtfs_fixture_dir), conn)
            stored = conn.execute(
                "SELECT current_setting('madrid_pulse.anchor_profile')"
            ).fetchone()[0]
        pos = real.RealStops.second["19667"]
        route = filtered.topology.resolve_trip_route_id(pos.source_trip_id)
        coverage = snapshot.coverage_for_trip(filtered, pos.source_trip_id, route)
        self.assertTrue(
            profile_matches(
                stored,
                filtered.gtfs_version,
                coverage.identity.pattern_id,
                coverage.geometry_version,
                config.thresholds,
            )
        )
        self.assertFalse(
            profile_matches(
                stored,
                filtered.gtfs_version,
                coverage.identity.pattern_id,
                "otra-geometría",
                config.thresholds,
            )
        )

    def test_tolerance_for_clock_steps(self):
        sandbox = integration.StopStateDatabase()
        sandbox.setUp()
        self.addCleanup(sandbox.doCleanups)
        sandbox.prepare()
        sandbox.conn.execute("SELECT set_config('madrid_pulse.retro_tolerance_s','3.5',true)")
        sandbox.run_id("alerts", sandbox.at)
        for seconds, expected in [(3.5, False), (3.501, True)]:
            run = sandbox.run_id("trip_updates", sandbox.at - timedelta(seconds=seconds))
            self.assertEqual(
                sandbox.conn.execute(
                    "SELECT is_retroactive FROM source_ingestion_run WHERE id=%s", (run,)
                ).fetchone()[0],
                expected,
            )

    def test_expired_cancellation_without_gps(self):
        sandbox = integration.StopStateDatabase()
        sandbox.setUp()
        self.addCleanup(sandbox.doCleanups)
        sandbox.prepare()
        sandbox.pos = {
            "20849": sandbox.pos["20849"].model_copy(update=dict(latitude=None, longitude=None))
        }
        for offset in (-86400, -601, -600):
            with self.subTest(offset=offset):
                sandbox.conn.execute("SAVEPOINT trip_day")
                sandbox.update(
                    sandbox.run_id("trip_updates", sandbox.at + timedelta(seconds=offset)),
                    offset,
                    "CANCELED",
                )
                sandbox.anchors()
                train = sandbox.frames(0)["20849"]
                self.assertEqual(
                    train.schedule_relationship, "CANCELED" if offset == -600 else None
                )
                self.assertEqual(
                    train.rendered.rendering_method,
                    "unlocated" if offset == -600 else "schedule_only",
                )
                board = snapshot.build_station_board(
                    sandbox.conn,
                    self.network,
                    real.RealStops.config,
                    "35609",
                    sandbox.at,
                    lookback_s=300,
                )
                entry = next(call for call in board.entries if call.trip_id == train.trip_id)
                self.assertEqual(entry.schedule_relationship, train.schedule_relationship)
                self.assertEqual(entry.departure.reason == "trip_canceled", offset == -600)
                sandbox.conn.execute("ROLLBACK TO SAVEPOINT trip_day")
