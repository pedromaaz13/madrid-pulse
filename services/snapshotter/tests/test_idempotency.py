"""Idempotencia real del archivo frío (MP-021), contra PostgreSQL de verdad.

El criterio de aceptación de MP-021 es explícito: *reprocesar el mismo día de
servicio dos veces produce el mismo resultado*. Estos tests lo ejercitan con
una base real -- exportar, volver a exportar, y comparar hash a hash -- en vez
de leer el código y suponerlo.

Los tres casos que fallaban antes de MP-021 y que estas pruebas fijan como
regresión:

1. **Particiones fantasma.** `OVERWRITE_OR_IGNORE` deja intactas las
   particiones que la nueva ejecución ya no produce. Con la tabla hot purgada
   o corregida, el archivo seguía devolviendo filas que ya no existen en el
   origen (`test_rows_removed_from_the_hot_table_do_not_survive_in_the_archive`).
2. **Reproceso destructivo.** `OVERWRITE` a secas borra la raíz entera:
   reexportar un día se llevaba por delante los demás días ya archivados
   (`test_reprocessing_one_day_does_not_touch_another_archived_day`).
3. **Origen vacío que borra el archivo.** La tabla hot se purga por diseño
   (DEC-011): 0 filas calientes no es prueba de que el día no tuviera
   observaciones (`test_an_empty_hot_table_never_erases_an_already_archived_day`).

Como `test_export_replay.py`, se usan fechas de servicio muy alejadas de
cualquier dato real y las filas se comprometen (DuckDB abre su propia conexión
`libpq`, así que no vería una transacción sin comprometer) y se borran en
`tearDown`.
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import psycopg

from packages.gtfs import load_feed
from services.collector.config import CollectorConfig
from services.snapshotter.config import SnapshotterConfig
from services.snapshotter.export import export_service_date
from services.snapshotter.gold import (
    build_line_daily_metrics,
    build_nucleo_daily_summary,
    build_station_daily_metrics,
)
from services.snapshotter.history import build_circulation_daily_history

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gtfs_c5_real"

# `2099-02-02` y `2099-02-03`: dos días consecutivos tan lejanos a cualquier
# dato real que no pueden colisionar, y distintos del `2099-01-01` que ya usa
# `test_export_replay.py` (ambos tests pueden correr en la misma base).
DAY_A = date(2099, 2, 2)
DAY_B = date(2099, 2, 3)
# Dos horas locales distintas del mismo día para que el export produzca DOS
# particiones `hour=` -- condición necesaria para detectar la partición
# fantasma del caso (1).
EARLY = datetime(2099, 2, 2, 9, 0, tzinfo=timezone.utc)
LATE = datetime(2099, 2, 2, 12, 0, tzinfo=timezone.utc)
DAY_B_AT = datetime(2099, 2, 3, 9, 0, tzinfo=timezone.utc)

REAL_TRIP_ID = "1022J19502C5"
"""Viaje real de la fixture GTFS reducida; su servicio (`1022J`) solo está
activo el 2026-11-19, así que en 2099 no está programado. Se usa igualmente
como `source_trip_id` para que el mart por circulación tenga una fila
observada real sobre la que comparar hashes."""


def _connect_or_skip() -> psycopg.Connection:
    try:
        return psycopg.connect(
            CollectorConfig.from_env().database_url, autocommit=False, connect_timeout=3
        )
    except psycopg.OperationalError as exc:
        raise unittest.SkipTest(f"PostgreSQL local no disponible: {exc}")


def _inventory(root: Path) -> dict[str, str]:
    """Ruta relativa -> SHA-256 de cada Parquet bajo `root`.

    Compara el archivo completo, no solo los recuentos: un reproceso que
    cambiase el contenido o el orden de las filas daría el mismo recuento y
    otro hash.
    """
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.parquet"))
    }


def _row_counts(root: Path, table: str) -> int:
    directory = root / "raw" / table
    if not any(directory.glob("**/*.parquet")):
        return 0
    con = duckdb.connect()
    try:
        (count,) = con.execute(
            f"SELECT count(*) FROM read_parquet('{directory}/**/*.parquet')"
        ).fetchone()
        return count
    finally:
        con.close()


class ArchiveIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        self.addCleanup(self.conn.close)
        self.output_dir = Path(tempfile.mkdtemp(prefix="mp021_idem_"))
        self.addCleanup(lambda: shutil.rmtree(self.output_dir, ignore_errors=True))
        self.config = SnapshotterConfig.from_env()
        self.topology = load_feed(FIXTURE_DIR, network_id="10", short_name="C5")
        self.addCleanup(self._delete_test_rows)
        self.run_ids: list[int] = []

    def _delete_test_rows(self) -> None:
        with self.conn.transaction():
            self.conn.execute(
                "DELETE FROM vehicle_position_observation WHERE source_vehicle_id LIKE 'mp021-%'"
            )
            self.conn.execute(
                "DELETE FROM trip_update_observation WHERE source_trip_id LIKE 'mp021-%'"
            )
            if self.run_ids:
                self.conn.execute(
                    "DELETE FROM source_ingestion_run WHERE id = ANY(%s)", (self.run_ids,)
                )

    def _insert_position(self, observed_at: datetime, vehicle_id: str, trip_id: str) -> None:
        """Una observación comprometida, con `payload_hash` derivado de su propia
        identidad para no chocar con la clave única de deduplicación."""
        with self.conn.transaction():
            row = self.conn.execute(
                """
                INSERT INTO source_ingestion_run
                    (feed_name, source_timestamp, started_at, finished_at, status,
                     entity_count, payload_hash)
                VALUES ('vehicle_positions', %s, %s, %s, 'ok', 1, %s)
                RETURNING id
                """,
                (
                    observed_at,
                    observed_at,
                    observed_at,
                    hashlib.sha256(f"run-{vehicle_id}-{observed_at}".encode()).hexdigest(),
                ),
            ).fetchone()
            assert row is not None
            run_id = row[0]
            self.run_ids.append(run_id)
            self.conn.execute(
                """
                INSERT INTO vehicle_position_observation
                    (observed_at, received_at, source_vehicle_id, source_trip_id,
                     latitude, longitude, current_stop_id, raw_vehicle_label,
                     nucleo_prefix, nucleo_name, payload_hash, ingestion_run_id)
                VALUES (%s, %s, %s, %s, 40.4, -3.7, '35607', %s, '10', 'Madrid', %s, %s)
                """,
                (
                    observed_at,
                    observed_at,
                    vehicle_id,
                    trip_id,
                    vehicle_id,
                    hashlib.sha256(f"vp-{vehicle_id}-{observed_at}".encode()).hexdigest(),
                    run_id,
                ),
            )
            self.conn.execute(
                """
                INSERT INTO trip_update_observation
                    (observed_at, received_at, source_trip_id, delay_seconds, delay_coverage,
                     nucleo_prefix, payload_hash, ingestion_run_id)
                VALUES (%s, %s, %s, 60, 'reported', '10', %s, %s)
                """,
                (
                    observed_at,
                    observed_at,
                    trip_id,
                    hashlib.sha256(f"tu-{trip_id}-{observed_at}".encode()).hexdigest(),
                    run_id,
                ),
            )

    def _process(self, service_date: date) -> None:
        """Un ciclo completo igual que `python -m services.snapshotter <fecha>`."""
        export_service_date(self.config.database_url, service_date, self.output_dir)
        build_nucleo_daily_summary(self.output_dir, service_date, self.output_dir)
        build_line_daily_metrics(self.output_dir, service_date, self.output_dir, self.topology)
        build_station_daily_metrics(self.output_dir, service_date, self.output_dir, self.topology)
        build_circulation_daily_history(
            self.output_dir, service_date, self.output_dir, self.topology
        )

    # -- caso principal del criterio de aceptación -------------------------

    def test_reprocessing_the_same_service_day_twice_is_byte_identical(self) -> None:
        self._insert_position(EARLY, "mp021-vehicle-a", f"mp021-{REAL_TRIP_ID}")
        self._insert_position(LATE, "mp021-vehicle-b", "mp021-trip-b")

        self._process(DAY_A)
        first = _inventory(self.output_dir)
        first_rows = _row_counts(self.output_dir, "vehicle_position_observation")

        self._process(DAY_A)
        second = _inventory(self.output_dir)

        self.assertEqual(
            sorted(first), sorted(second), "el reproceso cambió el conjunto de ficheros del archivo"
        )
        self.assertEqual(first, second, "el reproceso cambió el contenido de algún fichero")
        self.assertEqual(
            first_rows,
            _row_counts(self.output_dir, "vehicle_position_observation"),
            "el reproceso duplicó filas crudas",
        )
        self.assertEqual(first_rows, 2)
        # Los cuatro agregados tienen que estar en el inventario comparado:
        # si alguno dejase de escribirse, la comparación sería vacía y pasaría.
        for mart in (
            "nucleo_daily_summary",
            "daily_line_metrics",
            "station_daily_metrics",
            "circulation_daily_history",
        ):
            self.assertTrue(
                any(f"gold/{mart}/date={DAY_A.isoformat()}" in path for path in first),
                f"{mart} no se escribió: la comparación de hashes no lo cubriría",
            )

    # -- caso (1): particiones fantasma -----------------------------------

    def test_rows_removed_from_the_hot_table_do_not_survive_in_the_archive(self) -> None:
        self._insert_position(EARLY, "mp021-vehicle-a", "mp021-trip-a")
        self._insert_position(LATE, "mp021-vehicle-b", "mp021-trip-b")
        self._process(DAY_A)
        self.assertEqual(_row_counts(self.output_dir, "vehicle_position_observation"), 2)
        hours = sorted(
            path.name
            for path in (
                self.output_dir
                / "raw"
                / "vehicle_position_observation"
                / f"date={DAY_A.isoformat()}"
            ).iterdir()
        )
        self.assertEqual(len(hours), 2, f"se esperaban dos particiones horarias, hay {hours}")

        with self.conn.transaction():
            self.conn.execute(
                "DELETE FROM vehicle_position_observation WHERE source_vehicle_id = %s",
                ("mp021-vehicle-b",),
            )
        self._process(DAY_A)

        self.assertEqual(
            _row_counts(self.output_dir, "vehicle_position_observation"),
            1,
            "la fila eliminada del origen sobrevive en el archivo (partición fantasma)",
        )
        con = duckdb.connect()
        try:
            vehicles = {
                row[0]
                for row in con.execute(
                    f"SELECT DISTINCT source_vehicle_id FROM read_parquet("
                    f"'{self.output_dir}/raw/vehicle_position_observation/**/*.parquet')"
                ).fetchall()
            }
        finally:
            con.close()
        self.assertEqual(vehicles, {"mp021-vehicle-a"})

    # -- caso (2): el reproceso de un día no toca los demás ---------------

    def test_reprocessing_one_day_does_not_touch_another_archived_day(self) -> None:
        self._insert_position(EARLY, "mp021-vehicle-a", "mp021-trip-a")
        self._insert_position(DAY_B_AT, "mp021-vehicle-b", "mp021-trip-b")
        self._process(DAY_A)
        day_a_before = {
            path: digest
            for path, digest in _inventory(self.output_dir).items()
            if f"date={DAY_A.isoformat()}" in path
        }
        self.assertTrue(day_a_before, "el día A no se archivó: el test no probaría nada")

        self._process(DAY_B)
        self._process(DAY_B)

        day_a_after = {
            path: digest
            for path, digest in _inventory(self.output_dir).items()
            if f"date={DAY_A.isoformat()}" in path
        }
        self.assertEqual(
            day_a_before, day_a_after, "procesar otro día alteró o borró el día ya archivado"
        )
        self.assertEqual(_row_counts(self.output_dir, "vehicle_position_observation"), 2)

    # -- caso (3): origen vacío no borra el archivo -----------------------

    def test_an_empty_hot_table_never_erases_an_already_archived_day(self) -> None:
        self._insert_position(EARLY, "mp021-vehicle-a", "mp021-trip-a")
        self._process(DAY_A)
        before = _inventory(self.output_dir)
        self.assertEqual(_row_counts(self.output_dir, "vehicle_position_observation"), 1)

        with self.conn.transaction():
            self.conn.execute(
                "DELETE FROM vehicle_position_observation WHERE source_vehicle_id LIKE 'mp021-%'"
            )
        results = export_service_date(self.config.database_url, DAY_A, self.output_dir)
        actions = {result.table: result.action for result in results}

        self.assertEqual(
            actions["vehicle_position_observation"],
            "preserved_existing",
            "un origen vacío debe conservar el archivo, no vaciarlo",
        )
        self.assertEqual(
            _row_counts(self.output_dir, "vehicle_position_observation"),
            1,
            "el archivo permanente se vació porque la tabla hot estaba purgada",
        )
        raw_before = {k: v for k, v in before.items() if k.startswith("raw/")}
        raw_after = {k: v for k, v in _inventory(self.output_dir).items() if k.startswith("raw/")}
        self.assertEqual(raw_before, raw_after)

    def test_a_day_absent_from_both_hot_and_archive_reports_absent_not_zero(self) -> None:
        results = export_service_date(self.config.database_url, DAY_B, self.output_dir)
        self.assertEqual(
            {result.action for result in results},
            {"absent"},
            "un día sin datos ni archivo previo debe reportarse como ausente",
        )
        self.assertEqual(_inventory(self.output_dir), {})


if __name__ == "__main__":
    unittest.main()
