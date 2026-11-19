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

    def test_feed_with_missing_entity_key_parses_as_empty_list(self) -> None:
        """Regresión (soak test de MP-007 contra el feed en vivo): una respuesta
        real de vehicle_positions.json omitió la clave `entity` por completo
        (0 vehículos activos), no un array vacío. El feed debe parsear sin error
        con `entity == []`, no rechazar el payload."""
        payload = load_fixture("vehicle_positions.json")
        header_only = {"header": payload["header"]}
        feed = RawVehiclePositionsFeed.model_validate(header_only)
        self.assertEqual(feed.entity, [])

    def test_raw_active_period_has_no_unobserved_end_field(self) -> None:
        """Regresión (2ª revisión de Codex en MP-005): `end` de GTFS-RT Alert.ActivePeriod
        no se ha observado nunca en una captura real -- `raw.py` no debe declararlo ni
        como campo opcional. Si una fixture futura confirma `end`, este test debe
        actualizarse entonces, no antes."""
        feed = RawAlertsFeed.model_validate(load_fixture("alerts.json"))
        for entity in feed.entity:
            for period in entity.alert.active_period:
                self.assertFalse(hasattr(period, "end"))
        # Un `end` presente en el JSON de origen debe ser ignorado (extra="ignore"),
        # no aceptado como atributo del modelo.
        payload = load_fixture("alerts.json")
        payload["entity"][0]["alert"]["activePeriod"][0]["end"] = "1700000000"
        feed_with_end = RawAlertsFeed.model_validate(payload)
        self.assertFalse(hasattr(feed_with_end.entity[0].alert.active_period[0], "end"))


if __name__ == "__main__":
    unittest.main()
