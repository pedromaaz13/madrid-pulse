"""Test de replay real (MP-009): un día exportado se reconstruye sin pérdida.

A diferencia de los tests de integración de MP-007/MP-008 (que aíslan con
`rollback()` dentro de la misma conexión), este test necesita que DuckDB --
con su propia conexión `libpq` independiente vía `ATTACH ... (TYPE POSTGRES)`
-- vea los datos insertados. PostgreSQL es MVCC: una transacción no
comprometida en una conexión es invisible para otra conexión. Por eso aquí
se compromete (`commit()`) la fila de prueba y se borra explícitamente al
terminar (`try/finally`), en vez de depender de un `rollback()`.

Se usa un `service_date` de prueba muy alejado de cualquier fecha real
(`2099-01-01`) para que nunca colisione con datos reales del colector.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import json

import duckdb
import psycopg

from packages.contracts.canonical import ServiceAlert
from packages.gtfs import load_feed
from services.collector import db as collector_db
from services.collector.config import CollectorConfig
from services.snapshotter.config import SnapshotterConfig
from services.snapshotter.export import export_service_date
from services.snapshotter.gold import (
    build_line_daily_metrics,
    build_nucleo_daily_summary,
    build_station_daily_metrics,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gtfs_c5_real"

TEST_SERVICE_DATE = date(2099, 1, 1)
# 10:00 UTC del 1-enero-2099 cae en el mismo día en Europe/Madrid (CET, sin
# ambigüedad de medianoche) -- deliberado para que este test no dependa de
# la conversión de huso horario, que ya tiene su propio test en `export.py`.
TEST_OBSERVED_AT = datetime(2099, 1, 1, 10, 0, tzinfo=timezone.utc)
# Deliberadamente MUY lejos de TEST_SERVICE_DATE: regresión directa del
# hallazgo real de la revisión de Codex en MP-009 (la primera entrega de esta
# tarea particionaba `service_alert` por `active_period_start`, por lo que
# alertas realmente ingeridas un día desaparecían si su vigencia caía en otra
# fecha). El alert de este test debe aparecer en el export de
# `TEST_SERVICE_DATE` PESE a que su `active_period_start` sea esta fecha.
TEST_ALERT_ACTIVE_PERIOD_START = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _connect_or_skip() -> psycopg.Connection:
    try:
        return psycopg.connect(CollectorConfig().database_url, autocommit=False, connect_timeout=3)
    except psycopg.OperationalError as exc:
        raise unittest.SkipTest(f"PostgreSQL local no disponible: {exc}")


class ExportReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        self.addCleanup(self.conn.close)
        self.output_dir = Path(tempfile.mkdtemp(prefix="mp009_replay_"))
        self.addCleanup(lambda: shutil.rmtree(self.output_dir, ignore_errors=True))
        self._cleanup_queries: list[tuple[str, tuple]] = []
        self.addCleanup(self._delete_test_rows)

    def _delete_test_rows(self) -> None:
        with self.conn.transaction():
            for query, params in reversed(self._cleanup_queries):
                self.conn.execute(query, params)

    def _insert_known_day(self) -> dict[str, int]:
        """Inserta un pequeño conjunto de filas reales-forma, COMPROMETIDAS, para
        `TEST_SERVICE_DATE`. Devuelve los recuentos esperados por tabla."""
        with self.conn.transaction():
            run_id = collector_db.insert_ingestion_run(
                self.conn,
                feed_name="vehicle_positions",
                source_timestamp=TEST_OBSERVED_AT,
                started_at=TEST_OBSERVED_AT,
                finished_at=TEST_OBSERVED_AT,
                status="ok",
                entity_count=2,
                payload_hash="1" * 64,
            )
            self._cleanup_queries.append(
                ("DELETE FROM source_ingestion_run WHERE id = %s", (run_id,))
            )

            for i in range(2):
                self.conn.execute(
                    """
                    INSERT INTO vehicle_position_observation
                        (observed_at, received_at, source_vehicle_id, source_trip_id,
                         latitude, longitude, raw_vehicle_label, nucleo_prefix, nucleo_name,
                         payload_hash, ingestion_run_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        TEST_OBSERVED_AT,
                        TEST_OBSERVED_AT,
                        f"replay-test-vehicle-{i}",
                        f"replay-test-trip-{i}",
                        40.4 + i * 0.01,
                        -3.7,
                        f"replay test {i}",
                        "10",
                        "Madrid",
                        f"{i}" * 64,
                        run_id,
                    ),
                )
            self._cleanup_queries.append(
                (
                    "DELETE FROM vehicle_position_observation WHERE ingestion_run_id = %s",
                    (run_id,),
                )
            )

            self.conn.execute(
                """
                INSERT INTO trip_update_observation
                    (observed_at, received_at, source_trip_id, delay_coverage,
                     nucleo_prefix, payload_hash, ingestion_run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    TEST_OBSERVED_AT,
                    TEST_OBSERVED_AT,
                    "replay-test-trip-0",
                    "missing",
                    "10",
                    "2" * 64,
                    run_id,
                ),
            )
            self._cleanup_queries.append(
                ("DELETE FROM trip_update_observation WHERE ingestion_run_id = %s", (run_id,))
            )

            alert = ServiceAlert(
                source_alert_id="replay-test-alert-0",
                active_period_start=TEST_ALERT_ACTIVE_PERIOD_START,
                affected_route_ids=["10T0047C5"],
                description_text="aviso de prueba de replay",
                description_language="es",
                payload_hash="3" * 64,
            )
            collector_db.insert_service_alert(self.conn, alert, ingestion_run_id=run_id)
            self._cleanup_queries.append(
                ("DELETE FROM service_alert WHERE ingestion_run_id = %s", (run_id,))
            )

            self.conn.execute(
                """
                INSERT INTO data_quality_event (occurred_at, entity_type, entity_ref, flag, details)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    TEST_OBSERVED_AT,
                    "vehicle_position",
                    "replay-test-vehicle-0",
                    "stale",
                    json.dumps({"synthetic": True}),
                ),
            )
            self._cleanup_queries.append(
                (
                    "DELETE FROM data_quality_event WHERE entity_ref = %s",
                    ("replay-test-vehicle-0",),
                )
            )
        return {
            "vehicle_position_observation": 2,
            "trip_update_observation": 1,
            "service_alert": 1,
            "data_quality_event": 1,
        }

    def test_exported_day_reconstructs_the_same_rows_without_loss(self) -> None:
        expected_counts = self._insert_known_day()

        config = SnapshotterConfig.from_env()
        results = export_service_date(config.database_url, TEST_SERVICE_DATE, self.output_dir)
        results_by_table = {r.table: r for r in results}

        for table, expected in expected_counts.items():
            self.assertEqual(
                results_by_table[table].row_count,
                expected,
                f"{table}: recuento exportado no coincide con lo insertado",
            )

        con = duckdb.connect()
        try:
            vp_path = results_by_table["vehicle_position_observation"].output_path
            exported_vehicle_ids = {
                row[0]
                for row in con.execute(
                    f"SELECT source_vehicle_id FROM read_parquet('{vp_path}/**/*.parquet')"
                ).fetchall()
            }
            self.assertEqual(
                exported_vehicle_ids, {"replay-test-vehicle-0", "replay-test-vehicle-1"}
            )

            tu_path = results_by_table["trip_update_observation"].output_path
            exported_trip_ids = [
                row[0]
                for row in con.execute(
                    f"SELECT source_trip_id FROM read_parquet('{tu_path}/**/*.parquet')"
                ).fetchall()
            ]
            self.assertEqual(exported_trip_ids, ["replay-test-trip-0"])

            # Regresión directa del hallazgo de Codex: el alert aparece en el
            # día en que se INGIRIÓ (TEST_SERVICE_DATE), no en el día de su
            # `active_period_start` (2020-01-01, un año completamente distinto).
            sa_path = results_by_table["service_alert"].output_path
            exported_alert_ids = [
                row[0]
                for row in con.execute(
                    f"SELECT source_alert_id FROM read_parquet('{sa_path}/**/*.parquet')"
                ).fetchall()
            ]
            self.assertEqual(exported_alert_ids, ["replay-test-alert-0"])

            dqe_path = results_by_table["data_quality_event"].output_path
            exported_flags = [
                row[0]
                for row in con.execute(
                    f"SELECT flag FROM read_parquet('{dqe_path}/**/*.parquet')"
                ).fetchall()
            ]
            self.assertEqual(exported_flags, ["stale"])
        finally:
            con.close()

    def test_gold_summary_matches_raw_export_without_touching_postgres_again(self) -> None:
        self._insert_known_day()
        config = SnapshotterConfig.from_env()
        export_service_date(config.database_url, TEST_SERVICE_DATE, self.output_dir)

        gold = build_nucleo_daily_summary(self.output_dir, TEST_SERVICE_DATE, self.output_dir)
        self.assertEqual(gold.row_count, 1)

        con = duckdb.connect()
        try:
            row = con.execute(
                f"SELECT nucleo_prefix, positions_count, distinct_vehicles, trip_updates_count "
                f"FROM read_parquet('{gold.output_path}/part.parquet')"
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row, ("10", 2, 2, 1))

    def test_line_and_station_daily_metrics_resolve_against_real_export(self) -> None:
        """Replay real de `build_line_daily_metrics`/`build_station_daily_metrics`
        (MP-015). Usa una `Topology` sintética mínima -- no la fixture real
        completa -- para que el calendario resuelva contra `TEST_SERVICE_DATE`
        (2099-01-01), deliberadamente alejada de cualquier fecha real, en vez
        de insertar filas sintéticas en la partición real de 2026 (ver nota
        del módulo sobre por qué este fichero nunca usa una fecha real)."""
        from packages.gtfs import CalendarService, Route, Stop, Trip, Topology

        topology = Topology(
            routes=(Route("10T0017C5", "C5", "Humanes-Atocha", 2, "", ""),),
            trips=(Trip("10T0017C5", "replay-cal", "replay-test-trip-0", "", 2, "", ""),),
            stops=(Stop("replay-stop-0", "Estación de prueba", 40.4, -3.7, 1),),
            stop_times=(),
            shape_points=(),
            calendar=(
                CalendarService(
                    service_id="replay-cal",
                    monday=True, tuesday=True, wednesday=True, thursday=True,
                    friday=True, saturday=True, sunday=True,
                    start_date="20981231", end_date="20990102",
                ),
            ),
        )

        with self.conn.transaction():
            run_id = collector_db.insert_ingestion_run(
                self.conn,
                feed_name="vehicle_positions",
                source_timestamp=TEST_OBSERVED_AT,
                started_at=TEST_OBSERVED_AT,
                finished_at=TEST_OBSERVED_AT,
                status="ok",
                entity_count=1,
                payload_hash="4" * 64,
            )
            self._cleanup_queries.append(
                ("DELETE FROM source_ingestion_run WHERE id = %s", (run_id,))
            )
            self.conn.execute(
                """
                INSERT INTO vehicle_position_observation
                    (observed_at, received_at, source_vehicle_id, source_trip_id,
                     latitude, longitude, current_stop_id, raw_vehicle_label,
                     nucleo_prefix, nucleo_name, payload_hash, ingestion_run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    TEST_OBSERVED_AT, TEST_OBSERVED_AT, "replay-test-vehicle-gold",
                    "replay-test-trip-0", 40.4, -3.7, "replay-stop-0",
                    "replay gold test", "10", "Madrid", "5" * 64, run_id,
                ),
            )
            self._cleanup_queries.append(
                (
                    "DELETE FROM vehicle_position_observation WHERE ingestion_run_id = %s",
                    (run_id,),
                )
            )
            self.conn.execute(
                """
                INSERT INTO trip_update_observation
                    (observed_at, received_at, source_trip_id, delay_seconds,
                     delay_coverage, nucleo_prefix, payload_hash, ingestion_run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    TEST_OBSERVED_AT, TEST_OBSERVED_AT, "replay-test-trip-0", 45,
                    "reported", "10", "6" * 64, run_id,
                ),
            )
            self._cleanup_queries.append(
                ("DELETE FROM trip_update_observation WHERE ingestion_run_id = %s", (run_id,))
            )

        config = SnapshotterConfig.from_env()
        export_service_date(config.database_url, TEST_SERVICE_DATE, self.output_dir)

        line_gold = build_line_daily_metrics(self.output_dir, TEST_SERVICE_DATE, self.output_dir, topology)
        station_gold = build_station_daily_metrics(
            self.output_dir, TEST_SERVICE_DATE, self.output_dir, topology
        )

        con = duckdb.connect()
        try:
            line_row = con.execute(
                f"SELECT route_id, trips_scheduled, trips_with_delay_data, on_time_pct_of_covered "
                f"FROM read_parquet('{line_gold.output_path}/part.parquet')"
            ).fetchone()
            station_row = con.execute(
                f"SELECT station_id, observations_count "
                f"FROM read_parquet('{station_gold.output_path}/part.parquet')"
            ).fetchone()
        finally:
            con.close()

        self.assertEqual(line_row, ("10T0017C5", 1, 1, 1.0))
        self.assertEqual(station_row, ("replay-stop-0", 1))


if __name__ == "__main__":
    unittest.main()
