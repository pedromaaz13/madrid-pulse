"""Tests de contrato de la API contra la fixture reducida y PostgreSQL real.

Usa deliberadamente la fixture reducida de MP-010 (no el GTFS completo
~298 MB, DEC-023): rápido, reproducible sin red, y es exactamente el
escenario donde la mayoría de los `trip_id` reales del soak (otras líneas
del núcleo, DEC-020) NO resuelven -- el caso más importante a probar es que
la API responde con `None` honesto, nunca con un dato fabricado.
"""

from __future__ import annotations

import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault(
    "MADRID_PULSE_GTFS_SOURCE", str(ROOT / "tests" / "fixtures" / "gtfs_c5_real")
)
os.environ.setdefault(
    "MADRID_PULSE_OSM_RELATION",
    str(ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"),
)

from apps.api import db, service  # noqa: E402
from apps.api.config import ApiConfig  # noqa: E402
from apps.api.gtfs_source import load_network  # noqa: E402
from apps.api.main import app  # noqa: E402
from packages.contracts.canonical import VehiclePositionObservation  # noqa: E402

VALID_MODES = {"observed", "estimated", "stale", "scheduled"}


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_stations_endpoint_matches_real_gtfs_fixture(self) -> None:
        response = self.client.get("/api/v1/stations")
        self.assertEqual(response.status_code, 200)
        stations = response.json()
        self.assertEqual(len(stations), 23)
        ids = {item["station_id"] for item in stations}
        self.assertIn("18000", ids)  # Madrid-Atocha Cercanías

    def test_station_detail_404_for_unknown_id(self) -> None:
        response = self.client.get("/api/v1/stations/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_lines_endpoint_groups_five_c5_route_variants(self) -> None:
        response = self.client.get("/api/v1/lines")
        self.assertEqual(response.status_code, 200)
        lines = response.json()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["line_id"], "C5")
        self.assertEqual(len(lines[0]["route_ids"]), 5)

    def test_line_detail_404_for_unknown_id(self) -> None:
        response = self.client.get("/api/v1/lines/C9")
        self.assertEqual(response.status_code, 404)

    def test_health_endpoint_reports_real_feed_runs(self) -> None:
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        feeds = response.json()["feeds"]
        self.assertTrue(feeds)
        for feed in feeds:
            self.assertIn(feed["status"], {"ok", "stale", "error", "unknown"})
            self.assertGreaterEqual(feed["data_age_s"], 0)
            self.assertGreaterEqual(feed["rejected"], 0)

    def test_live_vehicles_never_fabricates_route_for_unresolvable_trip(self) -> None:
        """Hallazgo real: la mayoría de los vehículos del soak de MP-007
        pertenecen a otras líneas del núcleo (DEC-020, confirmado con el GTFS
        completo: C1/C3/C4a/C4b/C8b) y no resuelven contra la fixture
        reducida de C5. La API debe devolverlos con campos `None` honestos,
        nunca con un `route_id`/posición inventados."""
        response = self.client.get("/api/v1/live/vehicles")
        self.assertEqual(response.status_code, 200)
        vehicles = response.json()
        self.assertEqual(len(vehicles), 24)  # 24 vehículos distintos del soak real
        for vehicle in vehicles:
            if vehicle["route_id"] is None:
                self.assertIsNone(vehicle["line"])
                self.assertIsNone(vehicle["position"])
            else:
                self.assertIn(vehicle["position"]["mode"], VALID_MODES)
                self.assertIsNotNone(vehicle["line"])
            # El dato crudo siempre está presente, se conozca o no la línea.
            self.assertIsNotNone(vehicle["observation"]["reported_at"])
            self.assertIn(vehicle["delay"]["coverage"], {"reported", "missing"})
            if vehicle["delay"]["coverage"] == "missing":
                self.assertIsNone(vehicle["delay"]["seconds"])

    def test_live_vehicle_detail_404_for_unknown_vehicle_id(self) -> None:
        response = self.client.get("/api/v1/live/vehicles/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_live_vehicle_detail_matches_list_entry(self) -> None:
        listing = self.client.get("/api/v1/live/vehicles").json()
        sample = listing[0]
        detail = self.client.get(f"/api/v1/live/vehicles/{sample['vehicle_id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["trip_id"], sample["trip_id"])
        self.assertEqual(detail.json()["route_id"], sample["route_id"])


class ResolvedTripEndToEndTests(unittest.TestCase):
    """Prueba de extremo a extremo con un trip que SÍ existe en la fixture
    reducida (``1022J19502C5``, ``10T0017C5``), sin depender del GTFS
    completo (~298 MB, no versionado -- DEC-023). Construye la observación
    directamente en lugar de insertarla en PostgreSQL: valida la capa de
    servicio (resolución + map-matching + motor de movimiento), no el
    acceso a datos, ya cubierto por los tests de PostgreSQL real de
    MP-007/MP-012."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.network = load_network(ApiConfig.from_env())

    def test_known_trip_resolves_to_real_line_and_position(self) -> None:
        trip = next(
            t for t in self.network.topology.trips if t.trip_id == "1022J19502C5"
        )
        self.assertEqual(trip.route_id, "10T0017C5")
        station = next(iter(self.network.topology.stops))
        now = datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc)
        observation = VehiclePositionObservation(
            source_vehicle_id="test-vehicle",
            source_trip_id="1022J19502C5",
            observed_at=now - timedelta(seconds=10),
            latitude=station.latitude,
            longitude=station.longitude,
            raw_vehicle_label="contract test",
            payload_hash="c" * 64,
        )
        history = db.VehicleHistory(
            source_vehicle_id="test-vehicle",
            latest=db.ObservedRow(position=observation, received_at=now - timedelta(seconds=5)),
            previous=None,
        )
        result = service.vehicle_to_out(self.network, history, None, now)
        self.assertEqual(result.route_id, "10T0017C5")
        self.assertEqual(result.line, "C5")
        self.assertIsNotNone(result.position)
        self.assertEqual(result.position.mode, "observed")
        self.assertEqual(result.quality.stale, False)


if __name__ == "__main__":
    unittest.main()
