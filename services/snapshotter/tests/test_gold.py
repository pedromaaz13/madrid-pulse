"""Tests puros (sin PostgreSQL) de la capa gold por línea/estación (MP-015).

Usa la fixture GTFS real reducida de MP-010 (`tests/fixtures/gtfs_c5_real/`)
y escribe Parquet crudo sintético directamente en el layout que produce
`services/snapshotter/export.py`, para probar `gold.py` sin depender de una
base de datos real -- el test de replay con PostgreSQL vive en
`test_export_replay.py`, igual que para `build_nucleo_daily_summary`.
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from packages.gtfs import (
    CalendarException,
    CalendarService,
    Route,
    Stop,
    StopTime,
    Topology,
    Trip,
    load_feed,
)
from services.snapshotter.gold import (
    GoldThresholds,
    build_line_daily_metrics,
    build_station_daily_metrics,
    scheduled_trip_ids_by_route,
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
        by_route = scheduled_trip_ids_by_route(self.topology, ACTIVE_SERVICE_DATE)
        self.assertIn(REAL_ROUTE_ID, by_route)
        self.assertIn(REAL_TRIP_ID, by_route[REAL_ROUTE_ID])

    def test_trip_absent_outside_its_single_day_service_window(self) -> None:
        by_route = scheduled_trip_ids_by_route(self.topology, INACTIVE_SERVICE_DATE)
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
        self.assertEqual(coverage_pct, 50.0)
        self.assertEqual(on_time_pct, 100.0, "el único trip con dato de retraso estuvo dentro del umbral")

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
        self.assertEqual(on_time_pct, 100.0, "el último reporte (30s, dentro del umbral) debe ganar sobre el primero (900s)")

    def test_percentages_match_the_real_0_100_schema_not_a_0_1_fraction(self) -> None:
        """Regresión directa del hallazgo de la revisión de Codex: la primera
        versión de `build_line_daily_metrics` calculaba `delay_coverage_pct`/
        `on_time_pct_of_covered` como fracción `0..1` (`0.5`/`1.0`), pero
        `infra/migrations/0001_init.up.sql` define ambas columnas como
        `numeric(5,2) CHECK (... BETWEEN 0 AND 100)` y `docs/DATA_CONTRACTS.md`
        las ejemplifica como `78.3`/`87.2`. Un valor `<= 1.0` aquí (salvo el
        caso real de cobertura/puntualidad cero) sería la regresión exacta
        que este test existe para atrapar."""
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

        result = build_line_daily_metrics(self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology)
        _, _, _, coverage_pct, on_time_pct = self._row_for_real_route(result.output_path)
        for name, value in (("delay_coverage_pct", coverage_pct), ("on_time_pct_of_covered", on_time_pct)):
            self.assertGreater(value, 1.0, f"{name}={value} parece una fracción 0..1, no un porcentaje 0..100")
            self.assertLessEqual(value, 100.0, f"{name}={value} excede el rango real 0..100")


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


class CalendarExceptionDenominatorTests(unittest.TestCase):
    """`trips_scheduled` -- el **denominador** de toda métrica de puntualidad
    del día -- tiene que respetar `calendar_dates.txt`.

    Era el límite (a) de DEC-033: `gold.py` reimplementaba el calendario a
    mano y solo leía `calendar.txt`, así que un servicio añadido o suprimido un
    día concreto no cambiaba el denominador. Desde MP-021 el calendario lo
    resuelve una sola implementación (`packages.gtfs.scheduled_service_ids_for_date`,
    MP-017), la misma que usa el tablero de estación. El ZIP oficial de Renfe no
    publica `calendar_dates.txt` (verificado en MP-017 y de nuevo en MP-021:
    `topology.calendar_dates` es `()` con el ZIP del kit), así que una topología
    sintética mínima es la única forma realista de probarlo hoy.
    """

    def _topology(self, calendar_dates: tuple[CalendarException, ...] = ()) -> Topology:
        return Topology(
            routes=(Route("10T9999C9", "C9", "Línea sintética", 2, "000000", "ffffff"),),
            trips=(Trip("10T9999C9", "WEEKDAY", "trip-weekday", "Destino", 1, "", "shape-1"),),
            stops=(Stop("90001", "Origen", 40.0, -3.0, 1), Stop("90002", "Destino", 40.1, -3.1, 1)),
            stop_times=(
                StopTime("trip-weekday", "08:00:00", "08:00:00", "90001", 1),
                StopTime("trip-weekday", "08:30:00", "08:30:00", "90002", 2),
            ),
            shape_points=(),
            calendar=(
                CalendarService(
                    "WEEKDAY", True, True, True, True, True, False, False, "20260101", "20261231"
                ),
            ),
            calendar_dates=calendar_dates,
        )

    def setUp(self) -> None:
        self.raw_dir = Path(tempfile.mkdtemp(prefix="mp021_calendar_"))
        self.addCleanup(lambda: shutil.rmtree(self.raw_dir, ignore_errors=True))

    def _trips_scheduled(self, topology: Topology, service_date: date) -> int | None:
        result = build_line_daily_metrics(self.raw_dir, service_date, self.raw_dir, topology)
        con = duckdb.connect()
        try:
            row = con.execute(
                f"SELECT trips_scheduled FROM read_parquet('{result.output_path}/part.parquet') "
                f"WHERE route_id = '10T9999C9'"
            ).fetchone()
        finally:
            con.close()
        return None if row is None else row[0]

    def test_exception_type_2_removes_the_trip_from_the_denominator(self) -> None:
        monday = date(2026, 11, 23)
        self.assertEqual(monday.weekday(), 0)
        self.assertEqual(self._trips_scheduled(self._topology(), monday), 1)
        suppressed = self._topology(
            calendar_dates=(CalendarException("WEEKDAY", "20261123", exception_type=2),)
        )
        self.assertIsNone(
            self._trips_scheduled(suppressed, monday),
            "un servicio suprimido ese día no debe contar en trips_scheduled",
        )

    def test_exception_type_1_adds_the_trip_to_the_denominator(self) -> None:
        saturday = date(2026, 11, 21)
        self.assertEqual(saturday.weekday(), 5)
        self.assertIsNone(
            self._trips_scheduled(self._topology(), saturday),
            "el servicio es de lunes a viernes: sin excepción no debe aparecer en sábado",
        )
        added = self._topology(
            calendar_dates=(CalendarException("WEEKDAY", "20261121", exception_type=1),)
        )
        self.assertEqual(
            self._trips_scheduled(added, saturday),
            1,
            "un servicio añadido ese día debe contar en trips_scheduled",
        )

    def test_scheduled_trip_ids_by_route_and_the_station_board_share_one_calendar(self) -> None:
        """Regresión de coherencia: el mart y el catálogo no pueden discrepar.

        Si alguien volviese a reimplementar el calendario dentro de `gold.py`,
        este test lo detectaría: ambos conjuntos se derivan de la misma
        función desde MP-021.
        """
        saturday = date(2026, 11, 21)
        topology = self._topology(
            calendar_dates=(CalendarException("WEEKDAY", "20261121", exception_type=1),)
        )
        from packages.gtfs import scheduled_trip_instances_for_date

        mart_trips = scheduled_trip_ids_by_route(topology, saturday)
        catalog_trips: dict[str, set[str]] = {}
        for instance in scheduled_trip_instances_for_date(topology, saturday):
            catalog_trips.setdefault(instance.route_id, set()).add(instance.trip_id)
        self.assertEqual(mart_trips, catalog_trips)


class GoldDeterminismTests(unittest.TestCase):
    """Recalcular un agregado sobre los mismos Parquet debe dar el mismo fichero.

    Hallazgo de MP-021: el conjunto de filas ya era el mismo, pero su **orden**
    no -- el `GROUP BY` paralelo de DuckDB no garantiza orden de salida, así que
    dos corridas consecutivas con la misma entrada producían ficheros con
    SHA-256 distintos (medido sobre el catálogo completo de Madrid del
    2026-11-20: 35 filas de línea, 69 de estación). Se comprueban las dos
    propiedades: el fichero es byte-idéntico al recalcularlo, y sus filas están
    en orden ascendente por la clave del mart (que es lo que el `ORDER BY`
    garantiza y lo que hace comparable un mart entre dos reprocesos).
    """

    def setUp(self) -> None:
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
        self.raw_dir = Path(tempfile.mkdtemp(prefix="mp021_determinism_"))
        self.addCleanup(lambda: shutil.rmtree(self.raw_dir, ignore_errors=True))
        vp_dir = self.raw_dir / "raw" / "vehicle_position_observation" / f"date={ACTIVE_SERVICE_DATE}"
        con = duckdb.connect()
        try:
            _write_parquet(
                con,
                vp_dir,
                [{"current_stop_id": stop.stop_id} for stop in self.topology.stops] * 2,
            )
        finally:
            con.close()

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256((path / "part.parquet").read_bytes()).hexdigest()

    def _column(self, output_path: Path, column: str) -> list:
        con = duckdb.connect()
        try:
            return [
                row[0]
                for row in con.execute(
                    f"SELECT {column} FROM read_parquet('{output_path}/part.parquet')"
                ).fetchall()
            ]
        finally:
            con.close()

    def test_line_metrics_are_byte_identical_and_ordered_by_route(self) -> None:
        first = build_line_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology
        )
        digest = self._digest(first.output_path)
        routes = self._column(first.output_path, "route_id")
        self.assertGreater(len(routes), 1, "con una sola fila el orden no probaría nada")
        self.assertEqual(routes, sorted(routes), "daily_line_metrics no sale ordenado por route_id")
        second = build_line_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology
        )
        self.assertEqual(digest, self._digest(second.output_path))

    def test_station_metrics_are_byte_identical_and_ordered_by_station(self) -> None:
        first = build_station_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology
        )
        digest = self._digest(first.output_path)
        stations = self._column(first.output_path, "station_id")
        self.assertGreater(len(stations), 1, "con una sola fila el orden no probaría nada")
        self.assertEqual(
            stations,
            sorted(stations),
            "station_daily_metrics no sale ordenado por station_id",
        )
        second = build_station_daily_metrics(
            self.raw_dir, ACTIVE_SERVICE_DATE, self.raw_dir, self.topology
        )
        self.assertEqual(digest, self._digest(second.output_path))


if __name__ == "__main__":
    unittest.main()
