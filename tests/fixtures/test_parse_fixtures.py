"""Offline parsing and integrity tests for the frozen MP-004 fixtures."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parent
EXPECTED_SHA256 = {
    "vehicle_positions.json": "80af53436d5f94d18bd434caeefbf702391844846d3bc86c6ebf93d328da9883",
    "trip_updates.json": "78974c8543a2315315acb036eb72d5a2c8d792b10bcd11d725aebb917dc77bd4",
    "alerts.json": "cdd94af7bb7fa4d7a6fa894977abcf38cac2aed081a074d9b3377cc73750dfef",
}


def load_fixture(name: str) -> dict:
    """Load a fixture from disk; this module deliberately has no network code."""
    with (FIXTURE_DIR / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


class FrozenFixtureTests(unittest.TestCase):
    def test_sha256_integrity(self) -> None:
        for name, expected_hash in EXPECTED_SHA256.items():
            with self.subTest(fixture=name):
                payload = (FIXTURE_DIR / name).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), expected_hash)

    def test_common_gtfs_realtime_envelope(self) -> None:
        for name in EXPECTED_SHA256:
            with self.subTest(fixture=name):
                payload = load_fixture(name)
                self.assertEqual(payload["header"]["gtfsRealtimeVersion"], "2.0")
                self.assertTrue(str(payload["header"]["timestamp"]).isdigit())
                self.assertIsInstance(payload["entity"], list)
                self.assertTrue(payload["entity"])
                self.assertTrue(all(entity.get("id") for entity in payload["entity"]))

    def test_vehicle_positions_schema_and_madrid_coverage(self) -> None:
        entities = load_fixture("vehicle_positions.json")["entity"]
        madrid_entities = []
        for entity in entities:
            vehicle = entity["vehicle"]
            trip_id = vehicle["trip"]["tripId"]
            self.assertTrue(trip_id)
            self.assertIn(vehicle["currentStatus"], {"STOPPED_AT", "INCOMING_AT", "IN_TRANSIT_TO"})
            self.assertTrue(str(vehicle["timestamp"]).isdigit())
            self.assertTrue(vehicle["vehicle"]["id"])
            self.assertTrue(vehicle["vehicle"]["label"])
            position = vehicle["position"]
            self.assertIsInstance(position["latitude"], (int, float))
            self.assertIsInstance(position["longitude"], (int, float))
            if trip_id.startswith("10"):
                madrid_entities.append(entity)
        self.assertTrue(madrid_entities)

    def test_c5_label_alone_mixes_nuclei(self) -> None:
        entities = load_fixture("vehicle_positions.json")["entity"]
        naive_c5 = [
            entity
            for entity in entities
            if "C5" in entity["vehicle"]["vehicle"]["label"]
        ]
        madrid_c5 = [
            entity
            for entity in naive_c5
            if entity["vehicle"]["trip"]["tripId"].startswith("10")
        ]

        prefixes_selected_by_naive_filter = {
            entity["vehicle"]["trip"]["tripId"][:2] for entity in naive_c5
        }
        self.assertEqual(prefixes_selected_by_naive_filter, {"10", "20", "30", "40"})
        self.assertGreater(len(naive_c5), len(madrid_c5))
        self.assertTrue(madrid_c5)
        self.assertTrue(
            all(
                entity["vehicle"]["trip"]["tripId"].startswith("10")
                for entity in madrid_c5
            )
        )

    def test_trip_updates_schema_and_madrid_coverage(self) -> None:
        entities = load_fixture("trip_updates.json")["entity"]
        relationships = set()
        for entity in entities:
            update = entity["tripUpdate"]
            trip = update["trip"]
            self.assertTrue(trip["tripId"].startswith("10"))
            relationships.add(trip["scheduleRelationship"])
            if trip["scheduleRelationship"] == "SCHEDULED":
                self.assertIsInstance(update["delay"], int)
                self.assertTrue(update["stopTimeUpdate"])
                for stop_update in update["stopTimeUpdate"]:
                    self.assertTrue(stop_update["stopId"])
                    self.assertIsInstance(stop_update["arrival"]["delay"], int)
                    self.assertTrue(str(stop_update["arrival"]["time"]).isdigit())
            else:
                self.assertEqual(trip["scheduleRelationship"], "CANCELED")
        self.assertEqual(relationships, {"SCHEDULED", "CANCELED"})

    def test_alerts_schema_and_madrid_c5_routes(self) -> None:
        entities = load_fixture("alerts.json")["entity"]
        madrid_route_ids = set()
        for entity in entities:
            alert = entity["alert"]
            self.assertTrue(alert["activePeriod"])
            self.assertTrue(str(alert["activePeriod"][0]["start"]).isdigit())
            self.assertTrue(alert["informedEntity"])
            translations = alert["descriptionText"]["translation"]
            self.assertTrue(translations)
            self.assertTrue(translations[0]["text"])
            madrid_route_ids.update(
                informed["routeId"]
                for informed in alert["informedEntity"]
                if informed.get("routeId", "").startswith("10")
            )

        self.assertTrue(madrid_route_ids)
        self.assertEqual(
            {route_id for route_id in madrid_route_ids if route_id.endswith("C5")},
            {"10T0017C5", "10T0018C5", "10T0035C5", "10T0047C5", "10T0048C5"},
        )


if __name__ == "__main__":
    unittest.main()
