"""Valida que los modelos `raw` parsean las fixtures reales de MP-004 sin red."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from packages.contracts.raw import (
    RawAlertsFeed,
    RawTripUpdatesFeed,
    RawVehiclePositionsFeed,
)

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


class RawParsingTests(unittest.TestCase):
    def test_vehicle_positions_fixture_parses(self) -> None:
        feed = RawVehiclePositionsFeed.model_validate(load_fixture("vehicle_positions.json"))
        self.assertEqual(feed.header.gtfs_realtime_version, "2.0")
        self.assertTrue(feed.entity)
        for entity in feed.entity:
            self.assertTrue(entity.vehicle.trip.trip_id)
            self.assertTrue(entity.vehicle.vehicle.label)

    def test_trip_updates_fixture_parses(self) -> None:
        feed = RawTripUpdatesFeed.model_validate(load_fixture("trip_updates.json"))
        self.assertTrue(feed.entity)
        relationships = {e.trip_update.trip.schedule_relationship for e in feed.entity}
        # La fixture de MP-004 documenta explícitamente SCHEDULED y CANCELED.
        self.assertIn("SCHEDULED", relationships)
        self.assertIn("CANCELED", relationships)
        for entity in feed.entity:
            update = entity.trip_update
            if update.trip.schedule_relationship == "CANCELED":
                self.assertIsNone(update.delay)
                self.assertIsNone(update.stop_time_update)
            else:
                self.assertIsNotNone(update.delay)
                self.assertTrue(update.stop_time_update)

    def test_alerts_fixture_parses(self) -> None:
        feed = RawAlertsFeed.model_validate(load_fixture("alerts.json"))
        self.assertTrue(feed.entity)
        for entity in feed.entity:
            alert = entity.alert
            self.assertTrue(alert.active_period)
            self.assertTrue(alert.informed_entity)
            self.assertTrue(alert.description_text.translation)

    def test_raw_model_ignores_unknown_fields_without_failing(self) -> None:
        """Un campo nuevo no verificado no debe romper el parseo (ver raw.py)."""
        payload = load_fixture("vehicle_positions.json")
        payload["entity"][0]["vehicle"]["unexpectedFutureField"] = "x"
        feed = RawVehiclePositionsFeed.model_validate(payload)
        self.assertTrue(feed.entity)


if __name__ == "__main__":
    unittest.main()
