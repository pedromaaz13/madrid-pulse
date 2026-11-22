"""Valida la normalización raw -> canonical contra las fixtures reales de MP-004."""

from __future__ import annotations

import json
import unittest
from datetime import timezone
from pathlib import Path

from packages.contracts.canonical import canonical_payload_hash
from packages.contracts.normalize import (
    alerts_to_canonical,
    feed_health_from_raw,
    trip_updates_to_canonical,
    vehicle_positions_to_canonical,
)
from packages.contracts.raw import RawAlertsFeed, RawTripUpdatesFeed, RawVehiclePositionsFeed

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


class SkippedStopTests(unittest.TestCase):
    def test_skipped_stops_without_arrival_are_not_next_calls(self) -> None:
        payload = load_fixture("trip_updates.json")
        update = payload["entity"][0]["tripUpdate"]
        skipped = {"stopId": "35606", "scheduleRelationship": "SKIPPED"}
        arrival = {"stopId": "18000", "arrival": {"time": "1795185124"}}
        for stops, expected in (([skipped, arrival], "18000"), ([skipped], None)):
            with self.subTest(stops=stops):
                update["stopTimeUpdate"] = stops
                feed = RawTripUpdatesFeed.model_validate(payload)
                self.assertEqual(trip_updates_to_canonical(feed)[0].next_stop_id, expected)


class VehiclePositionNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        feed = RawVehiclePositionsFeed.model_validate(load_fixture("vehicle_positions.json"))
        self.observations = vehicle_positions_to_canonical(feed)

    def test_every_observation_has_utc_timestamp(self) -> None:
        for obs in self.observations:
            self.assertEqual(obs.observed_at.tzinfo, timezone.utc)

    def test_nucleo_disambiguation_is_not_fooled_by_c5_label(self) -> None:
        """Equivalente, a nivel de contrato canónico, al test de colisión de MP-004:
        dos observaciones con la misma etiqueta de línea 'C5' deben distinguirse
        por nucleo_prefix, no confundirse en una sola 'línea C5'."""
        c5_observations = [o for o in self.observations if "C5" in o.raw_vehicle_label]
        self.assertGreaterEqual(len(c5_observations), 2)
        nucleos_presentes = {o.nucleo_prefix for o in c5_observations}
        self.assertGreater(len(nucleos_presentes), 1, "la fixture debe mezclar núcleos")

        madrid_c5 = [o for o in c5_observations if o.nucleo_prefix == "10"]
        self.assertTrue(madrid_c5)
        for obs in madrid_c5:
            self.assertEqual(obs.nucleo_name, "Madrid")

    def test_missing_position_is_none_not_zero(self) -> None:
        """Si una entidad no trae `position`, el canónico debe guardar None, nunca 0.0."""
        synthetic_without_position = {
            "header": {"gtfsRealtimeVersion": "2.0", "timestamp": "1700000000"},
            "entity": [
                {
                    "id": "VP_SYN-1",
                    "vehicle": {
                        "trip": {"tripId": "1021X00001C5"},
                        "currentStatus": "STOPPED_AT",
                        "timestamp": "1700000000",
                        "stopId": "99999",
                        "vehicle": {"id": "00001", "label": "C5-00001"},
                    },
                }
            ],
        }
        feed = RawVehiclePositionsFeed.model_validate(synthetic_without_position)
        observations = vehicle_positions_to_canonical(feed)
        self.assertEqual(len(observations), 1)
        obs = observations[0]
        self.assertIsNone(obs.latitude)
        self.assertIsNone(obs.longitude)
        self.assertFalse(obs.has_position)

    def test_speed_and_bearing_are_none_when_absent_from_source(self) -> None:
        # Documentado en canonical.py: Renfe no emite speed/bearing en los feeds
        # reales capturados -- deben quedar en None, nunca inventarse un 0.0.
        for obs in self.observations:
            self.assertIsNone(obs.speed_kmh)
            self.assertIsNone(obs.bearing)

    def test_payload_hash_is_deterministic_and_sensitive_to_content(self) -> None:
        entity_a = {"id": "X", "vehicle": {"a": 1, "b": 2}}
        entity_b = {"id": "X", "vehicle": {"b": 2, "a": 1}}  # mismas claves, distinto orden
        entity_c = {"id": "X", "vehicle": {"a": 1, "b": 3}}  # contenido distinto
        self.assertEqual(canonical_payload_hash(entity_a), canonical_payload_hash(entity_b))
        self.assertNotEqual(canonical_payload_hash(entity_a), canonical_payload_hash(entity_c))


class TripUpdateNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        feed = RawTripUpdatesFeed.model_validate(load_fixture("trip_updates.json"))
        self.observations = trip_updates_to_canonical(feed)

    def test_delay_coverage_reflects_absence_not_zero(self) -> None:
        cancelled = [o for o in self.observations if o.schedule_relationship == "CANCELED"]
        scheduled = [o for o in self.observations if o.schedule_relationship == "SCHEDULED"]
        self.assertTrue(cancelled)
        self.assertTrue(scheduled)
        for obs in cancelled:
            self.assertIsNone(obs.delay_seconds)
            self.assertEqual(obs.delay_coverage, "missing")
        for obs in scheduled:
            self.assertIsNotNone(obs.delay_seconds)
            self.assertEqual(obs.delay_coverage, "reported")

    def test_all_observations_share_feed_header_timestamp(self) -> None:
        timestamps = {obs.observed_at for obs in self.observations}
        self.assertEqual(len(timestamps), 1)


class AlertNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        feed = RawAlertsFeed.model_validate(load_fixture("alerts.json"))
        self.alerts = alerts_to_canonical(feed)

    def test_madrid_c5_alert_covers_exactly_the_five_known_route_variants(self) -> None:
        # Cruce con el hallazgo de MP-003: las 5 variantes de route_id de C5 Madrid.
        madrid_c5_alerts = [
            a
            for a in self.alerts
            if "10" in a.nucleo_prefixes
            and any(r.endswith("C5") for r in a.affected_route_ids)
        ]
        self.assertTrue(madrid_c5_alerts)
        route_ids = set(madrid_c5_alerts[0].affected_route_ids)
        self.assertEqual(
            route_ids,
            {"10T0017C5", "10T0018C5", "10T0035C5", "10T0047C5", "10T0048C5"},
        )


class FeedHealthTests(unittest.TestCase):
    def test_feed_health_reports_real_entity_count(self) -> None:
        feed = RawVehiclePositionsFeed.model_validate(load_fixture("vehicle_positions.json"))
        health = feed_health_from_raw("vehicle_positions", feed)
        self.assertEqual(health.entity_count, len(feed.entity))
        self.assertEqual(health.source_timestamp.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
