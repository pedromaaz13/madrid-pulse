"""Casos sintéticos controlados para anomalías no presentes en las fixtures.

Las fixtures reales de MP-004 aportan forma y rangos normales, pero no contienen
deliberadamente un tren a velocidad imposible, IDs vacíos ni un feed congelado
durante minutos. Los casos que disparan esas anomalías son sintéticos y están
marcados aquí para no presentarlos como observaciones reales (criterio MP-008).
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from packages.contracts.canonical import VehiclePositionObservation
from packages.quality.engine import (
    SnapshotObservation,
    check_clock_anomaly,
    check_duplicate_snapshot,
    check_implausible_speed,
    check_missing_id,
    check_stale,
)

UTC = timezone.utc
T0 = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def _vehicle(*, observed_at: datetime, latitude: float, longitude: float):
    return VehiclePositionObservation(
        source_vehicle_id="19705",
        source_trip_id="100R15055C5",
        observed_at=observed_at,
        latitude=latitude,
        longitude=longitude,
        raw_vehicle_label="C5 19705",
        payload_hash="a" * 64,
    )


class StaleRuleTests(unittest.TestCase):
    def test_synthetic_old_observation_triggers(self) -> None:
        events = check_stale(
            observed_at=T0,
            received_at=T0 + timedelta(seconds=181),
            entity_type="vehicle_position",
            entity_ref="19705",
        )
        self.assertEqual([event.flag for event in events], ["stale"])

    def test_recent_observation_does_not_trigger(self) -> None:
        events = check_stale(
            observed_at=T0,
            received_at=T0 + timedelta(seconds=30),
            entity_type="vehicle_position",
            entity_ref="19705",
        )
        self.assertEqual(events, [])


class ImplausibleSpeedRuleTests(unittest.TestCase):
    def test_synthetic_jump_triggers(self) -> None:
        previous = _vehicle(observed_at=T0, latitude=40.40, longitude=-3.70)
        current = _vehicle(
            observed_at=T0 + timedelta(seconds=10), latitude=40.50, longitude=-3.70
        )
        events = check_implausible_speed(
            current=current, previous=previous, received_at=current.observed_at
        )
        self.assertEqual([event.flag for event in events], ["implausible_speed"])
        self.assertGreater(events[0].details["calculated_speed_kmh"], 200)

    def test_plausible_movement_does_not_trigger(self) -> None:
        previous = _vehicle(observed_at=T0, latitude=40.4000, longitude=-3.7000)
        current = _vehicle(
            observed_at=T0 + timedelta(seconds=60), latitude=40.4050, longitude=-3.7000
        )
        self.assertEqual(
            check_implausible_speed(
                current=current, previous=previous, received_at=current.observed_at
            ),
            [],
        )


class MissingIdRuleTests(unittest.TestCase):
    def test_synthetic_whitespace_id_triggers(self) -> None:
        events = check_missing_id(
            identifier="  ",
            id_field="source_vehicle_id",
            occurred_at=T0,
            entity_type="vehicle_position",
        )
        self.assertEqual([event.flag for event in events], ["missing_id"])

    def test_present_id_does_not_trigger(self) -> None:
        self.assertEqual(
            check_missing_id(
                identifier="19705",
                id_field="source_vehicle_id",
                occurred_at=T0,
                entity_type="vehicle_position",
            ),
            [],
        )


class DuplicateSnapshotRuleTests(unittest.TestCase):
    def test_synthetic_feed_frozen_beyond_window_triggers(self) -> None:
        current = SnapshotObservation("a" * 64, T0 + timedelta(seconds=181))
        history = [SnapshotObservation("a" * 64, T0)]
        events = check_duplicate_snapshot(
            current=current,
            consecutive_history=history,
            feed_name="vehicle_positions",
            entity_type="vehicle_position",
        )
        self.assertEqual([event.flag for event in events], ["duplicate_snapshot"])

    def test_two_normal_consecutive_equal_polls_do_not_trigger(self) -> None:
        current = SnapshotObservation("a" * 64, T0 + timedelta(seconds=30))
        history = [SnapshotObservation("a" * 64, T0)]
        self.assertEqual(
            check_duplicate_snapshot(
                current=current,
                consecutive_history=history,
                feed_name="vehicle_positions",
                entity_type="vehicle_position",
            ),
            [],
        )


class ClockAnomalyRuleTests(unittest.TestCase):
    def test_synthetic_source_clock_regression_triggers(self) -> None:
        events = check_clock_anomaly(
            observed_at=T0,
            received_at=T0 + timedelta(seconds=20),
            previous_observed_at=T0 + timedelta(seconds=1),
            entity_type="vehicle_position",
            entity_ref="19705",
        )
        self.assertEqual([event.flag for event in events], ["clock_anomaly"])
        self.assertTrue(events[0].details["regressed"])

    def test_small_forward_clock_difference_does_not_trigger(self) -> None:
        self.assertEqual(
            check_clock_anomaly(
                observed_at=T0 + timedelta(seconds=20),
                received_at=T0 + timedelta(seconds=30),
                previous_observed_at=T0,
                entity_type="vehicle_position",
                entity_ref="19705",
            ),
            [],
        )

    def test_normal_utc_midnight_rollover_does_not_trigger(self) -> None:
        before_midnight = datetime(2026, 11, 19, 23, 59, 50, tzinfo=UTC)
        after_midnight = datetime(2026, 11, 20, 0, 0, 10, tzinfo=UTC)
        self.assertEqual(
            check_clock_anomaly(
                observed_at=after_midnight,
                received_at=after_midnight + timedelta(seconds=5),
                previous_observed_at=before_midnight,
                entity_type="trip_update",
                entity_ref="100R15055C5",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
