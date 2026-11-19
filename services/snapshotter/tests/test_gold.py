"""Tests puros (sin PostgreSQL) de la capa gold por línea/estación (MP-015).

Usa la fixture GTFS real reducida de MP-010 (`tests/fixtures/gtfs_c5_real/`)
y escribe Parquet crudo sintético directamente en el layout que produce
`services/snapshotter/export.py`, para probar `gold.py` sin depender de una
base de datos real -- el test de replay con PostgreSQL vive en
`test_export_replay.py`, igual que para `build_nucleo_daily_summary`.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from packages.gtfs import load_feed
from services.snapshotter.gold import (
    GoldThresholds,
    _scheduled_trip_ids_by_route,
    build_line_daily_metrics,
    build_station_daily_metrics,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gtfs_c5_real"
# `1022J` (servicio del trip 1022J19502C5, ruta 10T0017C5) solo está activo
# el 2026-11-19 según calendar.txt de la fixture -- fecha elegida a propósito
# para que el test de calendario sea determinista.
ACTIVE_SERVICE_DATE = date(2026, 11, 19)
INACTIVE_SERVICE_DATE = date(2026, 11, 20)
REAL_TRIP_ID = "1022J19502C5"
REAL_ROUTE_ID = "10T0017C5"
REAL_STOP_ID = "35607"


_COLUMN_TYPES = {
    "source_trip_id": "VARCHAR",
    "delay_seconds": "INTEGER",
    "delay_coverage": "VARCHAR",
    "observed_at": "TIMESTAMPTZ",
    "current_stop_id": "VARCHAR",
}


def _write_parquet(con: duckdb.DuckDBPyConnection, directory: Path, rows: list[dict]) -> None:
    """Escribe Parquet crudo sintético con los mismos tipos de columna reales
    (ver `infra/migrations/0001_init.up.sql`), no todo `VARCHAR`, para que las
    comparaciones numéricas/temporales de `gold.py` se ejerciten de verdad."""
    directory.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    columns = list(rows[0].keys())
    column_defs = ", ".join(f"{c} {_COLUMN_TYPES[c]}" for c in columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    con.execute(f"CREATE TEMP TABLE _staging ({column_defs})")
    for row in rows:
        con.execute(f"INSERT INTO _staging VALUES ({placeholders})", [row[c] for c in columns])
    con.execute(f"COPY _staging TO '{directory / 'part.parquet'}' (FORMAT PARQUET)")
    con.execute("DROP TABLE _staging")


class ScheduledTripsByRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")

    def test_trip_active_on_its_single_day_service_window(self) -> None:
        by_route = _scheduled_trip_ids_by_route(self.topology, ACTIVE_SERVICE_DATE)
        self.assertIn(REAL_ROUTE_ID, by_route)
        self.assertIn(REAL_TRIP_ID, by_route[REAL_ROUTE_ID])

    def test_trip_absent_outside_its_single_day_service_window(self) -> None:
        by_route = _scheduled_trip_ids_by_route(self.topology, INACTIVE_SERVICE_DATE)
        self.assertNotIn(REAL_TRIP_ID, by_route.get(REAL_ROUTE_ID, set()))


class LineDailyMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
        self.raw_dir = Path(tempfile.mkdtemp(prefix="mp015_gold_"))
        self.addCleanup(lambda: shutil.rmtree(self.raw_dir, ignore_errors=True))

    def _trip_update_dir(self) -> Path:
        return self.raw_dir / "raw" / "trip_update_observation" / f"date={ACTIVE_SERVICE_DATE}"

    def _row_for_real_route(self, output_path: Path) -> tuple:
        con = duckdb.connect()
        try:
            return con.execute(
                f"SELECT route_id, trips_scheduled, trips_with_delay_data, delay_coverage_pct, "
                f"on_time_pct_of_covered FROM read_parquet('{output_path}/part.parquet') "
                f"WHERE route_id = '{REAL_ROUTE_ID}'"
            ).fetchone()
        finally:
            con.close()

    def test_scheduled_trip_with_no_observation_has_zero_coverage_not_null_scheduled(self) -> None:
        result = build_line_daily_metrics(self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology)
        self.assertGreaterEqual(result.row_count, 1, "la fixture reducida tiene más de una línea activa ese día")
        row = self._row_for_real_route(result.output_path)
        self.assertIsNotNone(row, f"{REAL_ROUTE_ID} debe tener fila propia en daily_line_metrics")
        route_id, trips_scheduled, trips_with_delay_data, coverage_pct, on_time_pct = row
        self.assertEqual(route_id, REAL_ROUTE_ID)
        self.assertGreaterEqual(trips_scheduled, 1)
        self.assertEqual(trips_with_delay_data, 0)
        self.assertEqual(coverage_pct, 0.0)
        self.assertIsNone(on_time_pct, "sin trips con dato de retraso, on_time_pct debe ser NULL, no 0")

    def test_reported_delay_within_threshold_counts_as_on_time(self) -> None:
        con = duckdb.connect()
        try:
            _write_parquet(
                con,
                self._trip_update_dir(),
                [
                    {
                        "source_trip_id": REAL_TRIP_ID,
                        "delay_seconds": 60,
                        "delay_coverage": "reported",
                        "observed_at": datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc),
                    }
                ],
            )
        finally:
            con.close()

        result = build_line_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology,
            thresholds=GoldThresholds(on_time_threshold_seconds=300.0),
        )
        _, trips_scheduled, trips_with_delay_data, coverage_pct, on_time_pct = self._row_for_real_route(result.output_path)
        # 10T0017C5 tiene 2 trips programados ese día en la fixture; solo uno
        # recibió un reporte de retraso -- coverage real es 1/2, no 1/1.
        self.assertEqual(trips_scheduled, 2)
        self.assertEqual(trips_with_delay_data, 1)
        self.assertEqual(coverage_pct, 0.5)
        self.assertEqual(on_time_pct, 1.0, "el único trip con dato de retraso estuvo dentro del umbral")

    def test_reported_delay_beyond_threshold_counts_as_not_on_time(self) -> None:
        con = duckdb.connect()
        try:
            _write_parquet(
                con,
                self._trip_update_dir(),
                [
                    {
                        "source_trip_id": REAL_TRIP_ID,
                        "delay_seconds": 900,
                        "delay_coverage": "reported",
                        "observed_at": datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc),
                    }
                ],
            )
        finally:
            con.close()

        result = build_line_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology,
            thresholds=GoldThresholds(on_time_threshold_seconds=300.0),
        )
        _, _, _, _, on_time_pct = self._row_for_real_route(result.output_path)
        self.assertEqual(on_time_pct, 0.0)

    def test_latest_report_of_the_day_wins_over_an_earlier_one(self) -> None:
        con = duckdb.connect()
        try:
            _write_parquet(
                con,
                self._trip_update_dir(),
                [
                    {
                        "source_trip_id": REAL_TRIP_ID,
                        "delay_seconds": 900,
                        "delay_coverage": "reported",
                        "observed_at": datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc),
                    },
                    {
                        "source_trip_id": REAL_TRIP_ID,
                        "delay_seconds": 30,
                        "delay_coverage": "reported",
                        "observed_at": datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc),
                    },
                ],
            )
        finally:
            con.close()

        result = build_line_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology,
        )
        _, _, _, _, on_time_pct = self._row_for_real_route(result.output_path)
        self.assertEqual(on_time_pct, 1.0, "el último reporte (30s, dentro del umbral) debe ganar sobre el primero (900s)")


class StationDailyMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
        self.raw_dir = Path(tempfile.mkdtemp(prefix="mp015_gold_station_"))
        self.addCleanup(lambda: shutil.rmtree(self.raw_dir, ignore_errors=True))

    def test_counts_observations_at_a_real_known_station(self) -> None:
        vp_dir = self.raw_dir / "raw" / "vehicle_position_observation" / f"date={ACTIVE_SERVICE_DATE}"
        con = duckdb.connect()
        try:
            _write_parquet(
                con,
                vp_dir,
                [
                    {"current_stop_id": REAL_STOP_ID},
                    {"current_stop_id": REAL_STOP_ID},
                    {"current_stop_id": None},  # sin stop actual: no debe contarse en ninguna estación
                ],
            )
        finally:
            con.close()

        result = build_station_daily_metrics(self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology)
        self.assertEqual(result.row_count, 1)
        con = duckdb.connect()
        try:
            row = con.execute(
                f"SELECT station_id, observations_count FROM read_parquet('{result.output_path}/part.parquet')"
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row, (REAL_STOP_ID, 2))

    def test_unknown_stop_id_outside_topology_is_not_fabricated_into_a_station(self) -> None:
        vp_dir = self.raw_dir / "raw" / "vehicle_position_observation" / f"date={ACTIVE_SERVICE_DATE}"
        con = duckdb.connect()
        try:
            _write_parquet(con, vp_dir, [{"current_stop_id": "not-a-real-stop-id"}])
        finally:
            con.close()

        result = build_station_daily_metrics(self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology)
        self.assertEqual(result.row_count, 0)

    def test_no_observations_produces_zero_rows_not_a_fabricated_zero_row(self) -> None:
        result = build_station_daily_metrics(self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology)
        self.assertEqual(result.row_count, 0)


if __name__ == "__main__":
    unittest.main()
