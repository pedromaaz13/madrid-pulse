"""Contrato de `/api/v1/history/*` (MP-021).

Recursos **nuevos**: el contrato de MP-019 (`/api/v1/snapshot`,
`/api/v1/catalog`, `/api/v1/stations/{id}/board`) no se modifica, y el primer
test de este módulo lo fija como regresión.

Sin PostgreSQL y sin red: se construye un archivo frío real en un directorio
temporal (Parquet crudo sintético + los marts calculados por
`services/snapshotter/`) y se sirve a la API sustituyendo la dependencia
`get_archive`. Las observaciones son sintéticas y se etiquetan como tales en
`raw_vehicle_label`; ninguna se presenta como captura de Renfe.

Lo que se comprueba es el criterio de MP-021: ningún porcentaje ni veredicto
sale sin su denominador, ningún hueco se publica como `0`, y un día que no
está archivado responde `404` en vez de un día vacío con métricas a cero.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import duckdb
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("MADRID_PULSE_GTFS_SOURCE", str(ROOT / "tests" / "fixtures" / "gtfs_c5_real"))
os.environ.setdefault(
    "MADRID_PULSE_OSM_RELATION",
    str(ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"),
)

from apps.api import history  # noqa: E402
from apps.api.main import app, get_archive  # noqa: E402
from packages.gtfs import load_feed  # noqa: E402
from services.snapshotter.gold import (  # noqa: E402
    build_line_daily_metrics,
    build_nucleo_daily_summary,
    build_station_daily_metrics,
)
from services.snapshotter.history import build_circulation_daily_history  # noqa: E402

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gtfs_c5_real"
SERVICE_DATE = date(2026, 11, 19)
UNARCHIVED_DATE = date(2026, 11, 20)
OBSERVED_TRIP_ID = "1022J19502C5"
OBSERVED_ROUTE_ID = "10T0017C5"
OBSERVED_VEHICLE_ID = "19502"
CANCELED_TRIP_ID = "1022J19503C5"
"""Segundo viaje real de la misma ruta en la fixture, usado aquí como servicio
anulado por el operador (parte de viaje `CANCELED`, ninguna posición)."""
STOP_ID = "35607"

MP019_PATHS = (
    "/api/v1/catalog",
    "/api/v1/snapshot",
    "/api/v1/stations/{station_id}/board",
    "/api/v1/health",
)


def _build_archive(root: Path) -> None:
    """Archivo frío real de un día: Parquet crudo sintético + los cuatro marts."""
    positions_dir = root / "raw" / "vehicle_position_observation" / f"date={SERVICE_DATE}" / "hour=09"
    updates_dir = root / "raw" / "trip_update_observation" / f"date={SERVICE_DATE}" / "hour=09"
    positions_dir.mkdir(parents=True, exist_ok=True)
    updates_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    try:
        con.execute(
            """
            CREATE TEMP TABLE positions (
                observed_at TIMESTAMPTZ, received_at TIMESTAMPTZ,
                source_vehicle_id VARCHAR, source_trip_id VARCHAR,
                latitude DOUBLE, longitude DOUBLE, current_status VARCHAR,
                current_stop_id VARCHAR, speed_kmh DOUBLE, bearing DOUBLE,
                quality_flags VARCHAR, raw_vehicle_label VARCHAR, nucleo_prefix VARCHAR
            )
            """
        )
        for index, (minute, status) in enumerate(((5, "IN_TRANSIT_TO"), (7, "STOPPED_AT"))):
            con.execute(
                "INSERT INTO positions VALUES ($1, $1, $2, $3, $4, -3.7, $5, $6, NULL, NULL, "
                "'[]', 'sintético MP-021', '10')",
                [
                    datetime(2026, 11, 19, 9, minute, tzinfo=timezone.utc),
                    OBSERVED_VEHICLE_ID,
                    OBSERVED_TRIP_ID,
                    40.4 + index * 0.01,
                    status,
                    STOP_ID,
                ],
            )
        con.execute(f"COPY positions TO '{positions_dir / 'part.parquet'}' (FORMAT PARQUET)")

        con.execute(
            """
            CREATE TEMP TABLE updates (
                observed_at TIMESTAMPTZ, source_trip_id VARCHAR,
                delay_seconds INTEGER, delay_coverage VARCHAR, nucleo_prefix VARCHAR,
                schedule_relationship VARCHAR
            )
            """
        )
        con.execute(
            "INSERT INTO updates VALUES ($1, $2, 60, 'reported', '10', 'SCHEDULED')",
            [datetime(2026, 11, 19, 9, 6, tzinfo=timezone.utc), OBSERVED_TRIP_ID],
        )
        # Un servicio real anulado por el operador: tiene parte de viaje pero
        # ninguna posición. Es el caso que la revisión de Codex encontró mal
        # clasificado como hueco de cobertura.
        con.execute(
            "INSERT INTO updates VALUES ($1, $2, NULL, 'missing', '10', 'CANCELED')",
            [datetime(2026, 11, 19, 9, 4, tzinfo=timezone.utc), CANCELED_TRIP_ID],
        )
        con.execute(f"COPY updates TO '{updates_dir / 'part.parquet'}' (FORMAT PARQUET)")
    finally:
        con.close()

    topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
    build_nucleo_daily_summary(root, SERVICE_DATE, root)
    build_line_daily_metrics(root, SERVICE_DATE, root, topology)
    build_station_daily_metrics(root, SERVICE_DATE, root, topology)
    build_circulation_daily_history(root, SERVICE_DATE, root, topology)


class HistoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.archive_root = Path(tempfile.mkdtemp(prefix="mp021_api_history_"))
        _build_archive(cls.archive_root)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.archive_root, ignore_errors=True)

    def setUp(self) -> None:
        self.enterContext(patch.dict(os.environ, {
            "MADRID_PULSE_ENV": "test",
            "MADRID_PULSE_DATABASE_URL": "postgresql://unused@127.0.0.1:1/unused",
        }))
        self.enterContext(patch(
            "psycopg.connect", side_effect=AssertionError("El histórico no usa PostgreSQL"),
        ))
        archive = history.Archive(root=self.archive_root)
        app.dependency_overrides[get_archive] = lambda: archive
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    # -- el contrato de MP-019 sigue intacto -------------------------------

    def test_the_mp019_contract_is_untouched_and_history_is_purely_additive(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in MP019_PATHS:
            self.assertIn(path, paths, f"{path} desapareció del contrato: MP-021 no debe tocarlo")
        self.assertEqual(
            self.client.get("/api/v1/catalog").status_code,
            200,
            "el catálogo cacheable de MP-019 debe seguir respondiendo igual",
        )
        history_paths = {path for path in paths if path.startswith("/api/v1/history")}
        self.assertEqual(len(history_paths), 5, f"rutas de histórico encontradas: {history_paths}")

    # -- índice de días ----------------------------------------------------

    def test_day_index_publishes_the_denominators_of_each_archived_day(self) -> None:
        payload = self.client.get("/api/v1/history/days").json()
        self.assertEqual(payload["schema_version"], "history-1.0")
        self.assertEqual(payload["archive_root"], str(self.archive_root))
        (day,) = payload["days"]
        self.assertEqual(day["service_date"], SERVICE_DATE.isoformat())
        self.assertEqual(day["circulations_observed"], 1)
        self.assertGreaterEqual(day["circulations_scheduled"], 1)
        # El invariante general, válido también cuando hay circulaciones
        # observadas fuera del calendario: toda fila del mart es programada o
        # no programada, y de lo programado, lo no observado es el hueco.
        self.assertEqual(
            day["rows_total"],
            day["circulations_scheduled"] + day["circulations_unscheduled"],
        )
        # El denominador del día cierra contra las cuatro categorías en que se
        # reparte lo programado. La identidad de tres términos que había aquí
        # antes daba por supuesto que todo lo no observado era hueco, y por eso
        # no veía las anulaciones.
        self.assertEqual(
            day["circulations_scheduled"],
            (day["circulations_observed"] - day["circulations_unscheduled"])
            + day["circulations_canceled"]
            + day["circulations_operator_only"]
            + day["circulations_unobserved"],
            "el denominador del día tiene que cerrar",
        )
        self.assertEqual(day["circulations_unscheduled"], 0)
        # Y las cinco categorías particionan el día sin solaparse.
        self.assertEqual(
            day["rows_total"],
            (day["circulations_observed"] - day["circulations_unscheduled"])
            + day["circulations_canceled"]
            + day["circulations_operator_only"]
            + day["circulations_unobserved"]
            + day["circulations_unscheduled"],
        )
        self.assertEqual(
            day["circulations_canceled"], 1, "el servicio anulado debe contarse como anulado"
        )
        self.assertIsNotNone(day["first_observed_at"])

    # -- líneas: puntualidad con cobertura --------------------------------

    def test_line_metrics_always_carry_the_denominators_of_their_percentages(self) -> None:
        payload = self.client.get(
            "/api/v1/history/lines", params={"service_date": SERVICE_DATE.isoformat()}
        ).json()
        rows = {row["route_id"]: row for row in payload["lines"]}
        self.assertIn(OBSERVED_ROUTE_ID, rows)
        observed = rows[OBSERVED_ROUTE_ID]
        self.assertEqual(observed["line_short_name"], "C5")
        self.assertGreaterEqual(observed["trips_scheduled"], 1)
        self.assertEqual(observed["trips_with_delay_data"], 1)
        self.assertIsNotNone(observed["delay_coverage_pct"])
        self.assertEqual(observed["on_time_pct_of_covered"], 100.0)

        for row in payload["lines"]:
            if row["trips_with_delay_data"] == 0:
                self.assertIsNone(
                    row["on_time_pct_of_covered"],
                    f"{row['route_id']}: puntualidad sin muestra debe ser null, nunca 0",
                )
            self.assertGreaterEqual(
                row["trips_scheduled"],
                row["trips_with_delay_data"],
                "la cobertura no puede exceder su denominador",
            )

    # -- circulaciones y huecos -------------------------------------------

    def test_unobserved_filter_returns_the_coverage_gap_with_nulls(self) -> None:
        payload = self.client.get(
            "/api/v1/history/circulations",
            params={"service_date": SERVICE_DATE.isoformat(), "only": "unobserved"},
        ).json()
        self.assertEqual(payload["only"], "unobserved")
        self.assertGreater(payload["returned"], 0, "la fixture tiene más servicios que observaciones")
        for row in payload["circulations"]:
            self.assertTrue(row["scheduled"])
            self.assertFalse(row["observed"])
            self.assertIsNone(row["vehicle_id"])
            self.assertIsNone(row["positions_count"], "un hueco no se publica como 0 posiciones")
            self.assertIsNone(row["on_time"])
            self.assertEqual(row["coverage"], "unobserved")
            self.assertIsNone(
                row["trip_updates_count"],
                "un hueco REAL no tiene ni parte del operador; si lo tuviera, no es un hueco",
            )
            self.assertNotEqual(
                row["trip_id"],
                CANCELED_TRIP_ID,
                "un servicio anulado por el operador no puede salir en el filtro de huecos",
            )

        # La mayoría de los huecos sí se pueden situar en el día; los únicos
        # que no son los viajes huérfanos del GTFS (sin `stop_times`), que se
        # conservan con el horario explícitamente ausente para que el
        # denominador del día coincida con el de `daily_line_metrics`.
        with_schedule = [
            row
            for row in payload["circulations"]
            if row["scheduled_first_departure_time"] is not None
        ]
        self.assertTrue(
            with_schedule, "ningún hueco trae horario previsto: el contexto del día se perdió"
        )
        for row in with_schedule:
            self.assertIsNotNone(row["scheduled_first_stop_id"])

    def test_observed_filter_returns_the_real_circulation_with_its_identity(self) -> None:
        payload = self.client.get(
            "/api/v1/history/circulations",
            params={
                "service_date": SERVICE_DATE.isoformat(),
                "line": "C5",
                "only": "observed",
            },
        ).json()
        (row,) = payload["circulations"]
        self.assertEqual(row["vehicle_id"], OBSERVED_VEHICLE_ID)
        self.assertEqual(row["trip_id"], OBSERVED_TRIP_ID)
        self.assertEqual(row["service_date"], SERVICE_DATE.isoformat())
        self.assertEqual(row["positions_count"], 2)
        self.assertEqual(row["delay_reported_count"], 1)
        self.assertTrue(row["on_time"])

    def test_truncated_is_declared_when_the_limit_is_reached(self) -> None:
        payload = self.client.get(
            "/api/v1/history/circulations",
            params={"service_date": SERVICE_DATE.isoformat(), "limit": 1},
        ).json()
        self.assertEqual(payload["returned"], 1)
        self.assertTrue(payload["truncated"], "una lista recortada debe decirlo")

    def test_canceled_filter_separates_operator_cancellations_from_coverage_gaps(self) -> None:
        """Regresión directa del hallazgo: un servicio anulado por el operador
        no es un fallo de captura nuestro y no debe engordar el hueco."""
        payload = self.client.get(
            "/api/v1/history/circulations",
            params={"service_date": SERVICE_DATE.isoformat(), "only": "canceled"},
        ).json()
        self.assertEqual(payload["returned"], 1)
        (row,) = payload["circulations"]
        self.assertEqual(row["trip_id"], CANCELED_TRIP_ID)
        self.assertEqual(row["coverage"], "canceled")
        self.assertTrue(row["canceled"])
        self.assertFalse(row["observed"])
        # Posición ausente; parte del operador presente, con su cero medido.
        self.assertIsNone(row["positions_count"])
        self.assertEqual(row["trip_updates_count"], 1)
        self.assertEqual(row["delay_reported_count"], 0)
        self.assertIsNone(row["on_time"], "sin retraso reportado no hay veredicto")

    # -- detalle por identidad de Live ------------------------------------

    def test_detail_is_addressed_by_the_same_identity_live_uses(self) -> None:
        response = self.client.get(
            f"/api/v1/history/circulations/{OBSERVED_VEHICLE_ID}/{OBSERVED_TRIP_ID}",
            params={"service_date": SERVICE_DATE.isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["circulation"]["vehicle_id"], OBSERVED_VEHICLE_ID)
        self.assertEqual(len(payload["positions"]), 2)
        self.assertEqual(
            [item["current_status"] for item in payload["positions"]],
            ["IN_TRANSIT_TO", "STOPPED_AT"],
            "las observaciones deben venir en orden temporal",
        )
        self.assertEqual(len(payload["delays"]), 1)
        self.assertEqual(payload["delays"][0]["delay_coverage"], "reported")

    def test_detail_of_an_unobserved_scheduled_trip_has_no_fabricated_positions(self) -> None:
        gap = self.client.get(
            "/api/v1/history/circulations",
            params={"service_date": SERVICE_DATE.isoformat(), "only": "unobserved", "limit": 1},
        ).json()["circulations"][0]
        response = self.client.get(
            f"/api/v1/history/circulations/-/{gap['trip_id']}",
            params={"service_date": SERVICE_DATE.isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["circulation"]["observed"])
        self.assertEqual(payload["positions"], [])

    def test_an_unknown_identity_is_a_404_not_an_empty_circulation(self) -> None:
        response = self.client.get(
            "/api/v1/history/circulations/00000/no-existe",
            params={"service_date": SERVICE_DATE.isoformat()},
        )
        self.assertEqual(response.status_code, 404)

    # -- días y fechas inválidas ------------------------------------------

    def test_a_day_that_is_not_archived_is_a_404_not_a_day_with_zero_metrics(self) -> None:
        for path in (
            "/api/v1/history/lines",
            "/api/v1/history/stations",
            "/api/v1/history/circulations",
        ):
            with self.subTest(path=path):
                response = self.client.get(
                    path, params={"service_date": UNARCHIVED_DATE.isoformat()}
                )
                self.assertEqual(response.status_code, 404)
                self.assertIn("no está en el histórico archivado", response.json()["detail"])

    def test_a_malformed_service_date_is_rejected(self) -> None:
        response = self.client.get(
            "/api/v1/history/lines", params={"service_date": "ayer"}
        )
        self.assertEqual(response.status_code, 400)

    def test_station_metrics_are_ordered_by_observations(self) -> None:
        payload = self.client.get(
            "/api/v1/history/stations", params={"service_date": SERVICE_DATE.isoformat()}
        ).json()
        counts = [row["observations_count"] for row in payload["stations"]]
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertEqual(payload["returned"], len(payload["stations"]))


if __name__ == "__main__":
    unittest.main()
