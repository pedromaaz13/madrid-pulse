from __future__ import annotations

import inspect
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import build_corridor, load_relation_geometry_json, point_at_arc_length
from packages.gtfs import load_feed
from packages.movement import MovementEngine, MovementThresholds, PositionMode
from packages.movement import engine as engine_module
from packages.movement.schedule import build_trip_schedule, parse_gtfs_time, service_seconds

ROOT = Path(__file__).parents[3]
GTFS_FIXTURE = ROOT / "tests" / "fixtures" / "gtfs_c5_real"
OSM_FIXTURE = ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"
SERVICE_DATE = date(2026, 11, 19)


class MovementEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = load_feed(GTFS_FIXTURE, network_id="10", short_name="C5")
        cls.corridor = build_corridor(load_relation_geometry_json(OSM_FIXTURE))
        cls.trip_id = next(
            trip.trip_id
            for trip in cls.topology.trips
            if trip.route_id == "10T0017C5" and trip.trip_id.startswith("1022J")
        )
        cls.engine = MovementEngine(cls.topology, cls.corridor)
        cls.schedule = build_trip_schedule(cls.topology, cls.corridor, cls.trip_id)
        cls.polyline = list(cls.corridor.segments[0])

    def observation(
        self,
        *,
        at: datetime,
        progress_m: float,
        stop_id: str | None = None,
        vehicle_id: str = "movement-test",
    ) -> VehiclePositionObservation:
        physical = self.schedule.physical_arc(progress_m)
        lat, lon = point_at_arc_length(self.polyline, physical)
        return VehiclePositionObservation(
            source_vehicle_id=vehicle_id,
            source_trip_id=self.trip_id,
            observed_at=at,
            latitude=lat,
            longitude=lon,
            current_stop_id=stop_id,
            raw_vehicle_label="synthetic deterministic movement test",
            payload_hash="a" * 64,
        )

    def test_transitions_between_all_four_modes_and_confidence_decays(self) -> None:
        now = datetime(2026, 11, 19, 4, 5, tzinfo=timezone.utc)
        progress = self.schedule.points[2].progress_m
        observed = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
            latest=self.observation(at=now - timedelta(seconds=60), progress_m=progress),
        )
        estimated = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
            latest=self.observation(at=now - timedelta(seconds=61), progress_m=progress),
        )
        stale = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
            latest=self.observation(at=now - timedelta(seconds=181), progress_m=progress),
        )
        scheduled = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
        )

        self.assertEqual(observed.position_mode, PositionMode.OBSERVED)
        self.assertEqual(estimated.position_mode, PositionMode.ESTIMATED)
        self.assertEqual(stale.position_mode, PositionMode.STALE)
        self.assertEqual(scheduled.position_mode, PositionMode.SCHEDULED)
        self.assertGreater(observed.confidence, estimated.confidence)
        self.assertGreater(estimated.confidence, stale.confidence)
        self.assertGreater(stale.confidence, scheduled.confidence - 0.2)
        self.assertIsNone(scheduled.age_s)  # ausencia nunca se representa como cero
        self.assertNotEqual(observed.source, estimated.source)
        self.assertNotEqual(estimated.source, stale.source)

    def test_estimate_uses_schedule_offset_and_limits_speed_and_acceleration(self) -> None:
        latest_at = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        now = latest_at + timedelta(seconds=90)
        latest_progress = self.schedule.points[0].progress_m
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
            latest=self.observation(at=latest_at, progress_m=latest_progress),
        )
        max_distance = 160.0 / 3.6 * 90
        self.assertEqual(result.position_mode, PositionMode.ESTIMATED)
        self.assertGreaterEqual(result.progress_m, latest_progress)
        self.assertLessEqual(result.progress_m - latest_progress, max_distance)

    def test_station_skip_is_exposed_not_silently_corrected(self) -> None:
        times = self.topology.stop_times_for_trip(self.trip_id)
        previous_at = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        latest_at = previous_at + timedelta(minutes=5)
        previous = self.observation(
            at=previous_at,
            progress_m=self.schedule.points[0].progress_m,
            stop_id=times[0].stop_id,
        )
        latest = self.observation(
            at=latest_at,
            progress_m=self.schedule.points[3].progress_m,
            stop_id=times[3].stop_id,
        )
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=latest_at + timedelta(seconds=10),
            latest=latest,
            previous=previous,
        )
        flags = {item.flag for item in result.anomalies}
        self.assertIn("station_skip_anomaly", flags)
        self.assertEqual(result.position_mode, PositionMode.OBSERVED)

    def test_physically_impossible_jump_falls_back_to_last_plausible_with_flag(self) -> None:
        previous_at = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        previous = self.observation(
            at=previous_at, progress_m=self.schedule.points[0].progress_m
        )
        latest = self.observation(
            at=previous_at + timedelta(seconds=1),
            progress_m=self.schedule.points[-1].progress_m,
        )
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=latest.observed_at + timedelta(seconds=5),
            latest=latest,
            previous=previous,
        )
        self.assertEqual(result.position_mode, PositionMode.OBSERVED)
        self.assertIn("implausible_speed", {item.flag for item in result.anomalies})
        self.assertIsNotNone(result.age_s)

    def test_empirically_observed_feed_jump_range_is_not_rejected_as_impossible(self) -> None:
        previous_at = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        previous_progress = self.schedule.points[0].progress_m
        # 700 km/h durante 20 s: dentro del rango empírico 246--787 km/h del
        # soak, aunque no represente velocidad física continua del tren.
        latest_progress = previous_progress + 700.0 / 3.6 * 20.0
        previous = self.observation(at=previous_at, progress_m=previous_progress)
        latest = self.observation(
            at=previous_at + timedelta(seconds=20), progress_m=latest_progress
        )
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=latest.observed_at + timedelta(seconds=5),
            latest=latest,
            previous=previous,
        )
        self.assertEqual(result.position_mode, PositionMode.OBSERVED)
        self.assertNotIn("implausible_speed", {item.flag for item in result.anomalies})

    def test_large_backward_jump_is_flagged_and_not_used(self) -> None:
        previous_at = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        previous = self.observation(
            at=previous_at, progress_m=self.schedule.points[8].progress_m
        )
        latest = self.observation(
            at=previous_at + timedelta(seconds=20),
            progress_m=self.schedule.points[2].progress_m,
        )
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=latest.observed_at + timedelta(seconds=5),
            latest=latest,
            previous=previous,
        )
        self.assertEqual(result.position_mode, PositionMode.OBSERVED)
        self.assertIn("backward_jump", {item.flag for item in result.anomalies})

    def test_off_track_observation_is_flagged_and_not_presented_as_observed(self) -> None:
        now = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
        latest = VehiclePositionObservation(
            source_vehicle_id="off-track",
            source_trip_id=self.trip_id,
            observed_at=now,
            latitude=0.0,
            longitude=0.0,
            raw_vehicle_label="synthetic off-track test",
            payload_hash="b" * 64,
        )
        result = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now + timedelta(seconds=1),
            latest=latest,
        )
        self.assertEqual(result.position_mode, PositionMode.SCHEDULED)
        self.assertIn("off_track", {item.flag for item in result.anomalies})

    def test_thresholds_are_parameterized_and_line_identifier_is_not_in_engine(self) -> None:
        custom = MovementThresholds(observed_max_age_s=10, stale_after_s=20)
        self.assertEqual(custom.observed_max_age_s, 10)
        source = inspect.getsource(engine_module)
        self.assertNotIn('"C5"', source)
        self.assertNotIn("'C5'", source)

    def test_service_day_survives_local_midnight_and_gtfs_hours_over_24(self) -> None:
        after_midnight_utc = datetime(2026, 11, 20, 0, 30, tzinfo=timezone.utc)
        self.assertEqual(service_seconds(after_midnight_utc, SERVICE_DATE), 25.5 * 3600)
        self.assertEqual(parse_gtfs_time("25:30:00"), 25.5 * 3600)

    def test_calculation_timestamp_must_be_utc(self) -> None:
        with self.assertRaisesRegex(ValueError, "UTC"):
            self.engine.position(
                trip_id=self.trip_id,
                service_date=SERVICE_DATE,
                calculated_at=datetime(2026, 11, 19, 4, 0),
            )


if __name__ == "__main__":
    unittest.main()
