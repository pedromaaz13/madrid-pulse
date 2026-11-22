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
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

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


class FeedClockTests(unittest.TestCase):
    def test_new_poll_of_old_payload_is_stale(self) -> None:
        now = datetime(2026, 11, 20, 14, 32, tzinfo=timezone.utc)
        published = now - timedelta(minutes=10)
        run = db.FeedRunSample(
            feed_name="vehicle_positions", source_timestamp=published,
            started_at=now, finished_at=now, status="ok", entity_count=1, payload_hash="a" * 64,
        )
        with patch.object(db, "recent_ingestion_runs", return_value=[run]):
            result = service.feed_health(None, now, stale_after_s=180).feeds[0]
        self.assertEqual((result.source_timestamp, result.data_age_s, result.status),
                         (published, 600, "stale"))
        self.assertEqual(result.poll_age_s, 0)

    def test_collector_stopped_is_visible_even_with_current_source_timestamp(self) -> None:
        now = datetime(2026, 11, 20, 14, 32, tzinfo=timezone.utc)
        run = db.FeedRunSample(
            feed_name="vehicle_positions", source_timestamp=now,
            started_at=now - timedelta(minutes=10), finished_at=now - timedelta(minutes=10),
            status="ok", entity_count=119, payload_hash="a" * 64,
        )
        with patch.object(db, "recent_ingestion_runs", return_value=[run]):
            result = service.feed_health(None, now, stale_after_s=180).feeds[0]
        self.assertEqual((result.data_age_s, result.poll_age_s, result.status), (0, 600, "stale"))


class RuntimeModeTests(unittest.TestCase):
    def test_live_mode_rejects_replay_fixture(self) -> None:
        config = replace(ApiConfig.from_env(), mode="live")
        with self.assertRaisesRegex(ValueError, "live no admite fixtures"):
            load_network(config)


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        # Hallazgo de MP-015: algunas aserciones de este fichero (contadores
        # exactos del soak real de MP-007, 24 vehículos/DEC-029) dependen de
        # ese histórico puntual, irrepetible, que solo existe en la base
        # local de desarrollo -- nunca en una base fresca (CI). `skip`
        # explícito en esos tests concretos, no en todo el fichero: el resto
        # usa solo la fixture GTFS reducida y sí es reproducible en CI.
        vehicles = self.client.get("/api/v1/live/vehicles").json()
        self._has_real_soak_dataset = len(vehicles) == 24

    def _require_real_soak_dataset(self) -> None:
        if not self._has_real_soak_dataset:
            raise unittest.SkipTest(
                "soak real de MP-007 (24 vehículos, DEC-029) no presente en esta base "
                "-- normal en una base fresca sin el histórico local de desarrollo"
            )

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

    def test_line_exposes_real_segmented_corridor_and_projected_station_order(self) -> None:
        line = self.client.get("/api/v1/lines/C5").json()
        geometry = line["geometry"]
        self.assertIsNotNone(geometry)
        network = load_network(ApiConfig.from_env())
        self.assertEqual(len(geometry["segments"]), len(network.corridor.segments))
        self.assertEqual(
            sum(len(segment) for segment in geometry["segments"]),
            sum(len(segment) for segment in network.corridor.segments),
        )
        self.assertTrue(all(len(segment) >= 2 for segment in geometry["segments"]))
        self.assertEqual(len(geometry["stations"]), 23)
        distances = [station["distance_along_m"] for station in geometry["stations"]]
        self.assertEqual(distances, sorted(distances))
        self.assertEqual(geometry["stations"][0]["name"], "Móstoles-El Soto")
        self.assertEqual(geometry["stations"][-1]["name"], "Humanes")

    def test_line_detail_404_for_unknown_id(self) -> None:
        response = self.client.get("/api/v1/lines/C9")
        self.assertEqual(response.status_code, 404)

    def test_health_endpoint_reports_real_feed_runs(self) -> None:
        self._require_real_soak_dataset()
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        feeds = response.json()["feeds"]
        self.assertTrue(feeds)
        for feed in feeds:
            self.assertIn(feed["status"], {"ok", "stale", "error", "unknown"})
            self.assertGreaterEqual(feed["data_age_s"], 0)
            self.assertGreaterEqual(feed["rejected"], 0)
            self.assertGreaterEqual(feed["poll_age_s"], 0)
        runtime = response.json()
        self.assertEqual(runtime["mode"], "replay")
        self.assertTrue(runtime["gtfs_version"].startswith("sha256:"))
        self.assertLessEqual(runtime["gtfs_valid_from"], runtime["gtfs_valid_until"])

    def test_live_vehicles_always_report_raw_observation_age(self) -> None:
        """Hallazgo bloqueante de la revisión de Codex: antes `age_s` solo se
        rellenaba cuando el motor de movimiento resolvía una posición, dejando
        `None` para los vehículos reales que no son C5 aunque sí sabemos
        cuándo se observaron. La edad de la observación cruda es siempre
        calculable a partir de su propio timestamp."""
        self._require_real_soak_dataset()
        response = self.client.get("/api/v1/live/vehicles")
        vehicles = response.json()
        unresolved = [v for v in vehicles if v["route_id"] is None]
        self.assertTrue(unresolved, "la fixture reducida debe dejar vehículos reales sin resolver")
        for vehicle in unresolved:
            self.assertIsNotNone(vehicle["observation"]["age_s"])
            self.assertGreaterEqual(vehicle["observation"]["age_s"], 0)

    def test_live_vehicles_never_fabricates_route_for_unresolvable_trip(self) -> None:
        """Hallazgo real: la mayoría de los vehículos del soak de MP-007
        pertenecen a otras líneas del núcleo (DEC-020, confirmado con el GTFS
        completo: 19 de C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 más 1 trip de
        refuerzo sin resolver) y no resuelven contra la fixture reducida de
        C5. La API debe devolverlos con campos `None` honestos, nunca con un
        `route_id`/posición inventados."""
        self._require_real_soak_dataset()
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
        self._require_real_soak_dataset()
        listing = self.client.get("/api/v1/live/vehicles").json()
        sample = listing[0]
        detail = self.client.get(f"/api/v1/live/vehicles/{sample['vehicle_id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["trip_id"], sample["trip_id"])
        self.assertEqual(detail.json()["route_id"], sample["route_id"])


class ServiceDateTimezoneTests(unittest.TestCase):
    """Regresión del segundo hallazgo bloqueante de la revisión de Codex:
    una versión anterior pasaba la fecha UTC como ``service_date`` al motor
    de movimiento, pero ``packages.movement.schedule.service_seconds`` la
    interpreta como fecha de calendario Europe/Madrid (`docs/DATA_MODEL.md`).
    Cerca de medianoche ambas difieren en un día real. Mismo tipo de hallazgo
    que MP-009 ya documentó para el exportador histórico (DEC-021)."""

    def test_service_date_uses_europe_madrid_calendar_not_utc(self) -> None:
        # 2026-11-19T23:30Z = 2026-11-20T00:30 CET (invierno, UTC+1):
        # la fecha de servicio real ya es el día siguiente en Madrid.
        winter_utc = datetime(2026, 11, 19, 23, 30, tzinfo=timezone.utc)
        self.assertEqual(service._service_date(winter_utc), date(2026, 11, 20))
        self.assertNotEqual(service._service_date(winter_utc), winter_utc.date())

        # 2026-06-15T22:30Z = 2026-06-16T00:30 CEST (verano, UTC+2): mismo caso.
        summer_utc = datetime(2026, 6, 15, 22, 30, tzinfo=timezone.utc)
        self.assertEqual(service._service_date(summer_utc), date(2026, 6, 16))
        self.assertNotEqual(service._service_date(summer_utc), summer_utc.date())

        # Lejos de medianoche, ambas fechas coinciden.
        midday_utc = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(service._service_date(midday_utc), date(2026, 11, 19))


class VehicleTripChangeTests(unittest.TestCase):
    def test_previous_observation_from_another_trip_is_not_passed_to_engine(self) -> None:
        now = datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc)
        latest = VehiclePositionObservation(
            source_vehicle_id="same-vehicle", source_trip_id="new-trip", observed_at=now,
            latitude=40.4, longitude=-3.7, raw_vehicle_label="test", payload_hash="a" * 64,
        )
        previous = latest.model_copy(update={
            "source_trip_id": "old-trip", "observed_at": now - timedelta(minutes=5),
            "payload_hash": "b" * 64,
        })
        history = db.VehicleHistory(
            source_vehicle_id="same-vehicle",
            latest=db.ObservedRow(latest, now),
            previous=db.ObservedRow(previous, now - timedelta(minutes=5)),
        )
        network = Mock()
        network.engine.position.return_value = object()
        result = service._movement_position(network, history, "route", now)
        self.assertIsNotNone(result)
        self.assertIsNone(network.engine.position.call_args.kwargs["previous"])


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
