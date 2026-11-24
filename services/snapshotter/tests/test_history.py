"""Tests del histórico por circulación (MP-021, `services/snapshotter/history.py`).

Lo que se fija aquí es exactamente el criterio de aceptación de la tarea sobre
huecos y denominadores:

- un servicio programado del que no se vio ninguna posición **aparece** en el
  mart, con `observed=false` y sus métricas de observación en `NULL` -- nunca
  en `0`, que significaría "se observó cero veces" (docs/DATA_QUALITY.md);
- una circulación realmente observada cuyo `trip_id` no está en el calendario
  de ese día **no se descarta**: se marca `scheduled=false`;
- `on_time` es `NULL` mientras no haya ni un retraso reportado, y
  `delay_reported_count` -- su denominador -- viaja siempre con ella;
- la identidad del grano es vehículo + viaje, no `vehicle_id` a secas.

Sin PostgreSQL: se escribe Parquet crudo sintético en el mismo layout que
produce `export.py`, igual que `test_gold.py`. La idempotencia contra una base
real vive en `test_idempotency.py`.
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
from services.snapshotter.gold import GoldThresholds, scheduled_trip_ids_by_route
from services.snapshotter.history import build_circulation_daily_history

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gtfs_c5_real"
# Mismo día que `test_gold.py`: el servicio `1022J` de la fixture solo está
# activo el 2026-11-19, así que el calendario es determinista.
SERVICE_DATE = date(2026, 11, 19)
SCHEDULED_TRIP_ID = "1022J19502C5"
SCHEDULED_ROUTE_ID = "10T0017C5"
STOP_ID = "35607"

_POSITION_TYPES = {
    "source_vehicle_id": "VARCHAR",
    "source_trip_id": "VARCHAR",
    "observed_at": "TIMESTAMPTZ",
    "current_stop_id": "VARCHAR",
    "current_status": "VARCHAR",
}
_TRIP_UPDATE_TYPES = {
    "source_trip_id": "VARCHAR",
    "delay_seconds": "INTEGER",
    "delay_coverage": "VARCHAR",
    "observed_at": "TIMESTAMPTZ",
    "schedule_relationship": "VARCHAR",
}


def _write_parquet(directory: Path, rows: list[dict], types: dict[str, str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    columns = list(rows[0].keys())
    con = duckdb.connect()
    try:
        con.execute(
            f"CREATE TEMP TABLE _staging ({', '.join(f'{c} {types[c]}' for c in columns)})"
        )
        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        for row in rows:
            con.execute(f"INSERT INTO _staging VALUES ({placeholders})", [row[c] for c in columns])
        con.execute(f"COPY _staging TO '{directory / 'part.parquet'}' (FORMAT PARQUET)")
    finally:
        con.close()


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 19, hour, minute, tzinfo=timezone.utc)


class CirculationHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
        self.raw_dir = Path(tempfile.mkdtemp(prefix="mp021_history_"))
        self.addCleanup(lambda: shutil.rmtree(self.raw_dir, ignore_errors=True))

    def _positions_dir(self) -> Path:
        return self.raw_dir / "raw" / "vehicle_position_observation" / f"date={SERVICE_DATE}"

    def _trip_updates_dir(self) -> Path:
        return self.raw_dir / "raw" / "trip_update_observation" / f"date={SERVICE_DATE}"

    def _write_positions(self, rows: list[dict]) -> None:
        _write_parquet(self._positions_dir(), rows, _POSITION_TYPES)

    def _write_trip_updates(self, rows: list[dict]) -> None:
        _write_parquet(self._trip_updates_dir(), rows, _TRIP_UPDATE_TYPES)

    def _build(self, thresholds: GoldThresholds = GoldThresholds()):
        return build_circulation_daily_history(
            self.raw_dir, SERVICE_DATE, self.raw_dir, self.topology, thresholds
        )

    # Los dos instantes se leen como texto ISO: materializar un `TIMESTAMPTZ`
    # como `datetime` exigiría `pytz`, que no es dependencia del proyecto (misma
    # razón que `apps/api/history.py::_utc_iso`). Lo que se comprueba aquí es si
    # son `NULL` o no, no su representación.
    _TS_AS_TEXT = (
        "strftime(first_observed_at AT TIME ZONE 'UTC', '%Y-%m-%dT%H:%M:%SZ') "
        "AS first_observed_at, "
        "strftime(last_observed_at AT TIME ZONE 'UTC', '%Y-%m-%dT%H:%M:%SZ') AS last_observed_at"
    )

    def _rows(self, output_path: Path, where: str = "TRUE") -> list[dict]:
        con = duckdb.connect()
        try:
            cursor = con.execute(
                f"SELECT * REPLACE ({self._TS_AS_TEXT}) "
                f"FROM read_parquet('{output_path}/part.parquet') WHERE {where}"
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            con.close()

    # -- huecos ------------------------------------------------------------

    def test_a_canceled_trip_is_not_counted_as_a_coverage_gap(self) -> None:
        """Hallazgo de la revisión de Codex, con el caso real reproducido.

        En el Parquet real del `2026-11-20` había tres viajes
        (`1023V20865C5`, `1023V21340C10`, `1023V21748C2`) clasificados como
        hueco de cobertura con `trip_updates_count = 1` y
        `delay_reported_count = 0`. El origen: una `trip_update_observation`
        real con `schedule_relationship = 'CANCELED'` y ninguna posición.
        Renfe había **anulado** esos servicios; contarlos como hueco culpaba a
        nuestro colector de trenes que nunca salieron.
        """
        self._write_trip_updates(
            [
                {
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "delay_seconds": None,
                    "delay_coverage": "missing",
                    "observed_at": _at(9),
                    "schedule_relationship": "CANCELED",
                }
            ]
        )
        result = self._build()
        (row,) = self._rows(result.output_path, f"trip_id = '{SCHEDULED_TRIP_ID}'")

        self.assertEqual(row["coverage"], "canceled", "una anulación no es un hueco de cobertura")
        self.assertTrue(row["canceled"])
        self.assertTrue(row["scheduled"])
        self.assertFalse(row["observed"], "no hubo posición, y eso sigue siendo cierto")

        # Métricas de POSICIÓN: ausentes, porque no se observó ninguna.
        self.assertIsNone(row["positions_count"])
        self.assertIsNone(row["first_observed_at"])
        # Métricas del OPERADOR: hubo actualización, así que son recuentos
        # reales. El `0` es un cero MEDIDO -- la actualización no traía retraso,
        # que es lo que el feed hace con una cancelación -- no un dato ausente.
        self.assertEqual(row["trip_updates_count"], 1)
        self.assertEqual(row["delay_reported_count"], 0)
        # Y sin muestra de retraso no se emite veredicto.
        self.assertIsNone(row["on_time"])
        self.assertIsNone(row["latest_reported_delay_seconds"])

    def test_a_trip_update_without_position_and_without_cancellation_is_operator_only(self) -> None:
        """El otro caso de «sin posición pero con información»: el operador
        publicó un parte del viaje y nunca llegó una posición. No es un hueco
        total ni una anulación: es un hueco de **posición**."""
        self._write_trip_updates(
            [
                {
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "delay_seconds": 120,
                    "delay_coverage": "reported",
                    "observed_at": _at(9),
                    "schedule_relationship": "SCHEDULED",
                }
            ]
        )
        result = self._build()
        (row,) = self._rows(result.output_path, f"trip_id = '{SCHEDULED_TRIP_ID}'")
        self.assertEqual(row["coverage"], "operator_only")
        self.assertFalse(row["canceled"])
        self.assertFalse(row["observed"])
        self.assertIsNone(row["positions_count"], "sin posición sigue siendo ausencia, no cero")
        # Aquí sí hay retraso reportado, así que el veredicto es legítimo.
        self.assertEqual(row["delay_reported_count"], 1)
        self.assertTrue(row["on_time"])

    def test_every_row_classifies_into_exactly_one_coverage_category(self) -> None:
        """Invariante estructural: `coverage` particiona el mart."""
        self._write_positions(
            [
                {
                    "source_vehicle_id": "19502",
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "observed_at": _at(8),
                    "current_stop_id": STOP_ID,
                    "current_status": "STOPPED_AT",
                },
                {
                    "source_vehicle_id": "99999",
                    "source_trip_id": "trip-fuera-de-calendario",
                    "observed_at": _at(10),
                    "current_stop_id": STOP_ID,
                    "current_status": "IN_TRANSIT_TO",
                },
            ]
        )
        result = self._build()
        rows = self._rows(result.output_path)
        valid = {"observed", "canceled", "operator_only", "unobserved", "unscheduled"}
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["coverage"], valid)
            # La categoría tiene que ser coherente con las banderas de las que
            # se deriva, o un consumidor que confíe en una u otra discreparía.
            if row["coverage"] == "observed":
                self.assertTrue(row["scheduled"] and row["observed"])
            elif row["coverage"] == "unscheduled":
                self.assertTrue(row["observed"] and not row["scheduled"])
            else:
                self.assertTrue(row["scheduled"] and not row["observed"])
            if row["coverage"] == "unobserved":
                self.assertIsNone(row["trip_updates_count"], "un hueco real no tiene ni parte")

    def test_a_scheduled_trip_never_observed_is_a_row_with_nulls_not_zeros(self) -> None:
        result = self._build()
        rows = self._rows(result.output_path, f"trip_id = '{SCHEDULED_TRIP_ID}'")
        self.assertEqual(len(rows), 1, "el servicio programado debe tener su fila aunque no se viese")
        row = rows[0]
        self.assertTrue(row["scheduled"])
        self.assertFalse(row["observed"])
        self.assertIsNone(row["vehicle_id"], "no hay vehículo porque no se vio ninguno")
        self.assertEqual(
            row["coverage"], "unobserved", "sin ninguna señal, el hueco es total"
        )
        self.assertIsNone(row["canceled"], "sin parte del operador no se sabe si está anulada")
        for column in (
            "positions_count",
            "first_observed_at",
            "last_observed_at",
            "distinct_stops_observed",
            "trip_updates_count",
            "delay_reported_count",
            "latest_reported_delay_seconds",
            "on_time",
        ):
            self.assertIsNone(
                row[column],
                f"{column} debe ser NULL en una circulación no observada, nunca 0/false",
            )
        # El contexto programado sí está: el hueco se puede situar en el día.
        self.assertEqual(row["route_id"], SCHEDULED_ROUTE_ID)
        self.assertEqual(row["line_short_name"], "C5")
        self.assertEqual(row["scheduled_first_stop_id"], STOP_ID)
        self.assertNotEqual(row["scheduled_first_departure_time"], "")

    def test_the_day_denominator_matches_the_one_daily_line_metrics_uses(self) -> None:
        """Los dos marts del mismo día no pueden discrepar en el denominador.

        `daily_line_metrics.trips_scheduled` y las filas `scheduled` de este
        mart cuentan lo mismo: los viajes que el calendario programa ese día.
        Hallazgo real de MP-021 mirando la pantalla de Explore: omitir aquí los
        viajes sin `stop_times` hacía que la misma vista publicase 1304
        programados en una tabla y 1299 en otra con el ZIP oficial del
        2026-11-20.
        """
        result = self._build()
        scheduled_rows = self._rows(result.output_path, "scheduled")
        expected = {
            trip_id
            for trip_ids in scheduled_trip_ids_by_route(self.topology, SERVICE_DATE).values()
            for trip_id in trip_ids
        }
        self.assertEqual({row["trip_id"] for row in scheduled_rows}, expected)
        self.assertGreater(len(expected), 0)

    def test_a_trip_without_stop_times_is_a_row_with_no_schedule_not_a_dropped_row(self) -> None:
        """Un viaje huérfano (sin `stop_times`) se marca, no se descarta."""
        topology = Topology(
            routes=(Route("10T9999C9", "C9", "Línea sintética", 2, "000000", "ffffff"),),
            trips=(
                Trip("10T9999C9", "WEEKDAY", "trip-con-horario", "Destino", 1, "", "shape-1"),
                Trip("10T9999C9", "WEEKDAY", "trip-huerfano", "Destino", 1, "", "shape-1"),
            ),
            stops=(Stop("90001", "Origen", 40.0, -3.0, 1), Stop("90002", "Destino", 40.1, -3.1, 1)),
            stop_times=(
                StopTime("trip-con-horario", "08:00:00", "08:00:00", "90001", 1),
                StopTime("trip-con-horario", "08:30:00", "08:30:00", "90002", 2),
            ),
            shape_points=(),
            calendar=(
                CalendarService(
                    "WEEKDAY", True, True, True, True, True, False, False, "20260101", "20261231"
                ),
            ),
            calendar_dates=(),
        )
        monday = date(2026, 11, 23)
        result = build_circulation_daily_history(self.raw_dir, monday, self.raw_dir, topology)
        rows = {
            row["trip_id"]: row
            for row in self._rows(result.output_path)
        }
        self.assertEqual(set(rows), {"trip-con-horario", "trip-huerfano"})
        orphan = rows["trip-huerfano"]
        self.assertTrue(orphan["scheduled"])
        self.assertIsNone(orphan["scheduled_first_departure_time"])
        self.assertIsNone(orphan["scheduled_first_stop_id"])
        self.assertIsNotNone(rows["trip-con-horario"]["scheduled_first_departure_time"])

    def test_an_observed_circulation_outside_the_calendar_is_kept_and_flagged(self) -> None:
        self._write_positions(
            [
                {
                    "source_vehicle_id": "99999",
                    "source_trip_id": "trip-fuera-de-calendario",
                    "observed_at": _at(10),
                    "current_stop_id": STOP_ID,
                    "current_status": "IN_TRANSIT_TO",
                }
            ]
        )
        result = self._build()
        rows = self._rows(result.output_path, "trip_id = 'trip-fuera-de-calendario'")
        self.assertEqual(len(rows), 1, "una observación real no se descarta por no estar programada")
        self.assertFalse(rows[0]["scheduled"])
        self.assertTrue(rows[0]["observed"])
        self.assertEqual(rows[0]["vehicle_id"], "99999")
        self.assertEqual(rows[0]["positions_count"], 1)

    # -- identidad ---------------------------------------------------------

    def test_the_grain_is_vehicle_plus_trip_not_vehicle_alone(self) -> None:
        self._write_positions(
            [
                {
                    "source_vehicle_id": "19502",
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "observed_at": _at(8),
                    "current_stop_id": STOP_ID,
                    "current_status": "STOPPED_AT",
                },
                {
                    "source_vehicle_id": "19502",
                    "source_trip_id": "trip-siguiente-del-mismo-tren",
                    "observed_at": _at(12),
                    "current_stop_id": STOP_ID,
                    "current_status": "IN_TRANSIT_TO",
                },
            ]
        )
        result = self._build()
        rows = self._rows(result.output_path, "vehicle_id = '19502'")
        self.assertEqual(
            len(rows), 2, "un mismo vehículo en dos viajes son dos circulaciones, no una"
        )
        self.assertEqual({row["trip_id"] for row in rows}, {SCHEDULED_TRIP_ID, "trip-siguiente-del-mismo-tren"})

    def test_two_vehicles_on_the_same_trip_are_two_rows(self) -> None:
        self._write_positions(
            [
                {
                    "source_vehicle_id": vehicle,
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "observed_at": _at(8),
                    "current_stop_id": STOP_ID,
                    "current_status": "STOPPED_AT",
                }
                for vehicle in ("19502", "19503")
            ]
        )
        result = self._build()
        rows = self._rows(result.output_path, f"trip_id = '{SCHEDULED_TRIP_ID}'")
        self.assertEqual({row["vehicle_id"] for row in rows}, {"19502", "19503"})
        for row in rows:
            self.assertTrue(row["scheduled"], "ambos viajes siguen estando programados")

    # -- puntualidad y su denominador -------------------------------------

    def _observe_with_delays(self, delays: list[tuple[int, int, str]]) -> None:
        """`delays`: `(hora, segundos_de_retraso, cobertura)`."""
        self._write_positions(
            [
                {
                    "source_vehicle_id": "19502",
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "observed_at": _at(8),
                    "current_stop_id": STOP_ID,
                    "current_status": "STOPPED_AT",
                }
            ]
        )
        self._write_trip_updates(
            [
                {
                    "source_trip_id": SCHEDULED_TRIP_ID,
                    "delay_seconds": seconds,
                    "delay_coverage": coverage,
                    "observed_at": _at(hour),
                    "schedule_relationship": "SCHEDULED",
                }
                for hour, seconds, coverage in delays
            ]
        )

    def test_on_time_is_null_when_no_delay_was_ever_reported(self) -> None:
        self._observe_with_delays([(9, 0, "missing")])
        result = self._build()
        (row,) = self._rows(result.output_path, "vehicle_id = '19502'")
        self.assertEqual(row["trip_updates_count"], 1)
        self.assertEqual(row["delay_reported_count"], 0, "hubo una actualización, sin retraso reportado")
        self.assertIsNone(
            row["latest_reported_delay_seconds"], "sin reporte no hay retraso que publicar"
        )
        self.assertIsNone(row["on_time"], "sin denominador, on_time debe ser NULL, nunca false")

    def test_on_time_uses_the_latest_reported_delay_against_the_threshold(self) -> None:
        self._observe_with_delays([(9, 900, "reported"), (10, 60, "reported")])
        result = self._build()
        (row,) = self._rows(result.output_path, "vehicle_id = '19502'")
        self.assertEqual(row["delay_reported_count"], 2)
        self.assertEqual(row["latest_reported_delay_seconds"], 60)
        self.assertTrue(row["on_time"], "el último reporte (60s) está dentro del umbral de 300s")

    def test_a_delay_beyond_the_threshold_is_not_on_time(self) -> None:
        self._observe_with_delays([(9, 600, "reported")])
        result = self._build()
        (row,) = self._rows(result.output_path, "vehicle_id = '19502'")
        self.assertFalse(row["on_time"])
        self.assertEqual(row["delay_reported_count"], 1)

    def test_no_row_ever_has_a_verdict_without_its_denominator(self) -> None:
        """Invariante del mart completo, no de una fila elegida a mano."""
        self._observe_with_delays([(9, 60, "reported")])
        result = self._build()
        for row in self._rows(result.output_path):
            if row["on_time"] is not None:
                self.assertIsNotNone(row["delay_reported_count"])
                self.assertGreaterEqual(row["delay_reported_count"], 1)
            if row["positions_count"] is not None:
                self.assertGreaterEqual(row["positions_count"], 1)
                self.assertTrue(row["observed"])

    # -- calendario y determinismo ----------------------------------------

    def test_a_calendar_exception_changes_the_set_of_scheduled_circulations(self) -> None:
        topology = Topology(
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
            calendar_dates=(CalendarException("WEEKDAY", "20261123", exception_type=2),),
        )
        monday = date(2026, 11, 23)
        with_exception = build_circulation_daily_history(
            self.raw_dir, monday, self.raw_dir, topology
        )
        self.assertEqual(
            with_exception.row_count,
            0,
            "el único servicio del día está suprimido por calendar_dates: no hay circulación programada",
        )

    def test_rebuilding_the_mart_is_byte_identical_and_ordered(self) -> None:
        self._write_positions(
            [
                {
                    "source_vehicle_id": f"1950{index}",
                    "source_trip_id": SCHEDULED_TRIP_ID if index == 0 else f"trip-{index}",
                    "observed_at": _at(8, index),
                    "current_stop_id": STOP_ID,
                    "current_status": "STOPPED_AT",
                }
                for index in range(8)
            ]
        )
        first = self._build()
        digest = hashlib.sha256((first.output_path / "part.parquet").read_bytes()).hexdigest()
        rows = self._rows(first.output_path)
        self.assertGreater(len(rows), 1)
        keys = [
            (row["line_short_name"], row["route_id"], row["trip_id"], row["vehicle_id"] or "￿")
            for row in rows
        ]
        self.assertEqual(keys, sorted(keys), "el mart no sale en orden determinista")
        second = self._build()
        self.assertEqual(first.row_count, second.row_count)
        self.assertEqual(
            digest,
            hashlib.sha256((second.output_path / "part.parquet").read_bytes()).hexdigest(),
            "recalcular el mart con la misma entrada dio otro fichero",
        )


if __name__ == "__main__":
    unittest.main()
