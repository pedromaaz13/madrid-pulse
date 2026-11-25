"""AC-T6. Las pausas instrumentan funciones reales; PostgreSQL decide la visibilidad."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from hashlib import sha256
from threading import Barrier, Event
from unittest import TestCase
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.pq import TransactionStatus

from apps.api import db, main, snapshot
from apps.api.tests.test_snapshot_contract import ATOCHA, TRIP_ID, NetworkFixtureMixin, _instant
from packages.contracts.canonical import TripUpdateObservation
from services.collector import db as collector
from tests.postgres import connect_disposable_or_skip

NOW = _instant(5 * 3600 + 20 * 60)
SNAPSHOT = "snapshot"
BOARD = f"stations/{ATOCHA}/board"


class ConsistentResponses(NetworkFixtureMixin, TestCase):
    def setUp(self):
        self.writer = self.connection()
        self.run_ids = []
        self.addCleanup(self.delete_runs)
        self.client = self.enterContext(TestClient(main.app, raise_server_exceptions=False))

    def connection(self):
        conn = connect_disposable_or_skip()
        self.addCleanup(conn.close)
        return conn

    def delete_runs(self):
        self.writer.rollback()
        with self.writer.transaction():
            for table in ("vehicle_position_observation", "trip_update_observation", "source_ingestion_run"):
                column = "id" if table == "source_ingestion_run" else "ingestion_run_id"
                self.writer.execute(
                    sql.SQL("DELETE FROM {} WHERE {} = ANY(%s)").format(
                        sql.Identifier(table), sql.Identifier(column)
                    ),
                    (self.run_ids,),
                )

    def ingest(self, conn, feed, offset, *, vehicle_id=None, delay=None):
        at = NOW + timedelta(seconds=offset)
        payload_hash = sha256(f"AC-T6:{feed}:{at}:{vehicle_id}:{delay}".encode()).hexdigest()
        run = collector.insert_ingestion_run(
            conn, feed_name=feed, started_at=at, finished_at=at, source_timestamp=at,
            status="ok", entity_count=1, payload_hash=payload_hash,
        )
        self.run_ids.append(run)
        if vehicle_id is not None:
            collector.insert_vehicle_position_observation(
                conn, self.observation_on_corridor(
                    at=at, progress_m=self.schedule.points[5].progress_m, vehicle_id=vehicle_id
                ),
                received_at=at, ingestion_run_id=run, quality_flags=[],
            )
        if delay is not None:
            collector.insert_trip_update_observation(
                conn, TripUpdateObservation(
                    source_trip_id=TRIP_ID, observed_at=at, schedule_relationship="SCHEDULED",
                    delay_seconds=delay, delay_coverage="reported", next_stop_id=ATOCHA,
                    payload_hash=payload_hash,
                ),
                received_at=at, ingestion_run_id=run,
            )
        return run

    def fetch(self, path):
        response = self.client.get(f"/api/v1/{path}", params={"at": NOW.isoformat()})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def reference(self, conn, path):
        if path == SNAPSHOT:
            result = snapshot.build_snapshot(conn, self.network, self.config, NOW)
        else:
            result = snapshot.build_station_board(conn, self.network, self.config, ATOCHA, NOW)
        return result.model_dump(mode="json")

    def publication(self, body, path):
        if path == SNAPSHOT:
            return {
                row["vehicle_id"]: row["delay"]["seconds"] for row in body["vehicles"]
            }
        entry = next(row for row in body["entries"] if row["trip_id"] == TRIP_ID)
        return {entry["vehicle_id"]: entry["departure"]["delay_seconds"]}

    def test_empty_database_in_a_read_only_snapshot(self):
        self.assertEqual(self.writer.execute("SELECT count(*) FROM source_ingestion_run").fetchone(), (0,))
        self.writer.rollback()
        original = db.revision_marker
        readers = []

        def inspect(conn, **kwargs):
            readers.append(conn)
            return original(conn, **kwargs)

        with patch.object(db, "revision_marker", side_effect=inspect):
            snap, board = self.fetch(SNAPSHOT), self.fetch(BOARD)
        self.assertIsNone(snap["revision"]["sequence"])
        self.assertIsNone(board["revision"]["sequence"])
        self.assertEqual(snap["vehicles"], [])
        self.assertTrue(board["entries"])
        self.assertEqual({row["circulation_source"] for row in board["entries"]}, {"scheduled_only"})
        self.assertTrue(all(feed["status"] == "unknown" for feed in snap["feeds"]))
        self.assertEqual(len(readers), 2)
        self.assertTrue(all(conn.closed for conn in readers))

        # El constructor también cierra la transacción al devolver una respuesta
        # vacía, antes de que el llamador cierre su conexión.
        reader = self.connection()
        self.reference(reader, SNAPSHOT)
        self.assertEqual(reader.info.transaction_status, TransactionStatus.IDLE)

    def exercise_interleaving(self, path):
        with self.writer.transaction():
            anchor = self.ingest(self.writer, "vehicle_positions", -40, vehicle_id="act6-anchor")

        # Reserva n antes de que el otro escritor confirme n+1. Su commit
        # tardío satisface id <= sequence y pondría en evidencia un watermark solo.
        late = self.connection()
        lower = self.ingest(late, "trip_updates", -25, delay=120)
        with self.writer.transaction():
            upper = self.ingest(self.writer, "alerts", -20)
        self.assertLess(anchor, lower)
        self.assertEqual(upper, lower + 1)

        ref = self.connection()
        ref.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        ref.read_only = True
        marker = db.revision_marker
        vehicles_name = "latest_vehicle_histories" if path == SNAPSHOT else "vehicles_for_trips"
        vehicles = getattr(db, vehicles_name)
        updates = db.latest_trip_updates
        steps = []
        reference_state = {}

        def after_marker(conn, **kwargs):
            result = marker(conn, **kwargs)
            export = conn.execute("SELECT pg_export_snapshot()").fetchone()[0]
            ref.execute(sql.SQL("SET TRANSACTION SNAPSHOT {}").format(sql.Literal(export)))
            reference_state["snapshot"] = ref.execute("SELECT pg_current_snapshot()::text").fetchone()[0]
            reference_state["mode"] = conn.execute(
                "SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only')"
            ).fetchone()
            with self.writer.transaction():
                reference_state["higher"] = self.ingest(
                    self.writer, "vehicle_positions", -5, vehicle_id="act6-after-marker"
                )
            steps.append(("marker", result.sequence))
            return result

        def after_vehicles(conn, *args, **kwargs):
            result = vehicles(conn, *args, **kwargs)
            late.commit()
            steps.append(("vehicles", len(result)))
            return result

        def at_updates(conn, trip_ids, **kwargs):
            steps.append(("trip_updates", None))
            return updates(conn, trip_ids, **kwargs)

        with (
            patch.object(db, "revision_marker", side_effect=after_marker),
            patch.object(db, vehicles_name, side_effect=after_vehicles),
            patch.object(db, "latest_trip_updates", side_effect=at_updates),
        ):
            actual = self.fetch(path)

        expected = self.reference(ref, path)
        eligible = ref.execute(
            "SELECT id FROM source_ingestion_run WHERE started_at <= %s ORDER BY id", (NOW,)
        ).fetchall()
        provenance = ref.execute(
            """SELECT ingestion_run_id FROM vehicle_position_observation
               UNION ALL SELECT ingestion_run_id FROM trip_update_observation"""
        ).fetchall()
        fresh = self.fetch(path)
        self.assertEqual(fresh["revision"]["sequence"], reference_state["higher"])
        self.assertIn("act6-after-marker", self.publication(fresh, path))
        self.assertIn(120, self.publication(fresh, path).values())
        print(f"{path}: steps={steps}; reference={ref.info.backend_pid}, "
              f"snapshot={reference_state['snapshot']}; eligible={eligible}; "
              f"actual={self.publication(actual, path)}; reference={self.publication(expected, path)}")
        self.assertEqual(actual, expected)
        self.assertEqual(steps, [("marker", upper), ("vehicles", 1), ("trip_updates", None)])
        self.assertEqual(reference_state["mode"], ("repeatable read", "on"))
        self.assertEqual(actual["revision"]["sequence"], upper)
        self.assertEqual(eligible, [(anchor,), (upper,)])
        self.assertEqual(provenance, [(anchor,)])
        self.assertTrue(all(row[0] <= upper for row in eligible + provenance))
        self.assertEqual(self.publication(actual, path), {"act6-anchor": None})
        ref.rollback()

    def test_snapshot_matches_reference_during_both_commit_gaps(self):
        self.exercise_interleaving(SNAPSHOT)

    def test_board_matches_reference_during_both_commit_gaps(self):
        self.exercise_interleaving(BOARD)

    def test_aud06_two_runs_but_one_position_on_read_committed(self):
        with self.writer.transaction():
            first = self.ingest(self.writer, "vehicle_positions", -40, vehicle_id="aud06-first")
        original = db.latest_vehicle_histories

        def after_vehicles(conn, **kwargs):
            result = original(conn, **kwargs)
            with self.writer.transaction():
                second = self.ingest(self.writer, "vehicle_positions", -5, vehicle_id="aud06-second")
            self.assertGreater(second, first)
            return result

        with patch.object(db, "latest_vehicle_histories", side_effect=after_vehicles):
            mixed = self.fetch(SNAPSHOT)
        next_response = self.fetch(SNAPSHOT)
        print(f"AUD-06: en el hueco sequence={mixed['revision']['sequence']}, "
              f"posiciones={mixed['counts']['vehicles_total']}; siguiente sequence="
              f"{next_response['revision']['sequence']}, posiciones={next_response['counts']['vehicles_total']}")
        self.assertEqual(mixed["counts"]["vehicles_total"], 1)
        self.assertEqual(mixed["revision"]["sequence"], first)
        self.assertEqual(next_response["counts"]["vehicles_total"], 2)
        self.assertGreater(next_response["revision"]["sequence"], first)

    def test_same_sequence_accepts_a_lower_run_committed_later(self):
        with self.writer.transaction():
            self.ingest(self.writer, "vehicle_positions", -50, vehicle_id="act6-same-sequence")
        late = self.connection()
        lower = self.ingest(late, "trip_updates", -25, delay=120)
        with self.writer.transaction():
            upper = self.ingest(self.writer, "alerts", -15)
        self.assertEqual(upper, lower + 1)
        before = [self.fetch(path) for path in (SNAPSHOT, BOARD)]
        original = db.latest_trip_updates

        def after_updates(conn, trip_ids, **kwargs):
            result = original(conn, trip_ids, **kwargs)
            late.commit()
            return result

        with patch.object(db, "latest_trip_updates", side_effect=after_updates):
            in_flight = self.fetch(BOARD)
        after = [self.fetch(path) for path in (SNAPSHOT, BOARD)]
        self.assertEqual(in_flight, before[1])
        for path, older, newer in zip((SNAPSHOT, BOARD), before, after):
            self.assertEqual(older["revision"]["sequence"], upper)
            self.assertEqual(newer["revision"]["sequence"], upper)
            self.assertNotEqual(older["revision"]["tiebreak"], newer["revision"]["tiebreak"])
            self.assertEqual(self.publication(older, path), {"act6-same-sequence": None})
            self.assertEqual(self.publication(newer, path), {"act6-same-sequence": 120})

    def test_middle_of_response_errors_and_query_cancellation_close_the_transaction(self):
        for path, builder, statement in (
            (SNAPSHOT, "build_snapshot", "SELECT 1 / 0"),
            (BOARD, "build_station_board", "SELECT pg_sleep(1)"),
        ):
            original = getattr(snapshot, builder)
            finished = []

            def fail(conn, *args, **kwargs):
                conn.execute("SET LOCAL statement_timeout = '20ms'")
                conn.execute(statement)

            def inspect(conn, *args, **kwargs):
                try:
                    return original(conn, *args, **kwargs)
                finally:
                    finished.append((conn, conn.info.transaction_status))

            with (
                self.subTest(path=path),
                patch.object(db, "latest_trip_updates", side_effect=fail),
                patch.object(snapshot, builder, side_effect=inspect),
            ):
                response = self.client.get(f"/api/v1/{path}", params={"at": NOW.isoformat()})
                self.assertEqual(response.status_code, 500)
                self.assertEqual(len(finished), 1)
                conn, status = finished[0]
                self.assertTrue(conn.closed)
                self.assertEqual(status, TransactionStatus.IDLE)
            self.fetch(path)

    def test_concurrent_http_requests_are_independent(self):
        gate = Barrier(3)
        release = Event()
        marker = db.revision_marker
        readers = []

        def hold_old_requests(conn, **kwargs):
            result = marker(conn, **kwargs)
            readers.append(conn.info.backend_pid)
            gate.wait(timeout=10)
            if not release.wait(timeout=10):
                raise TimeoutError("escritura intercalada")
            return result

        with ThreadPoolExecutor(max_workers=2) as requests:
            try:
                with patch.object(db, "revision_marker", side_effect=hold_old_requests):
                    old = [requests.submit(self.fetch, path) for path in (SNAPSHOT, BOARD)]
                    gate.wait(timeout=10)
                    with self.writer.transaction():
                        run = self.ingest(self.writer, "alerts", -5)
                fresh = [self.fetch(path) for path in (SNAPSHOT, BOARD)]
            finally:
                release.set()
            before = [request.result(timeout=10) for request in old]
        self.assertEqual(len(set(readers)), 2)
        self.assertEqual([item["revision"]["sequence"] for item in before], [None, None])
        self.assertEqual([item["revision"]["sequence"] for item in fresh], [run, run])
        self.assertEqual(next(feed for feed in before[0]["feeds"] if feed["feed_name"] == "alerts")["status"],
                         "unknown")
        self.assertEqual(next(feed for feed in fresh[0]["feeds"] if feed["feed_name"] == "alerts")["status"],
                         "ok")
        # El tablero usa salud para el desempate. Una referencia vacía con
        # exactamente el mismo reloj debe conservar el desempate original.
        self.delete_runs()
        self.assertEqual(before[1], self.fetch(BOARD))

    def test_scope_fallback_keeps_the_callers_snapshot_and_role(self):
        reader = self.connection()
        reader.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        role = sql.Identifier("mp026b_scope_test")
        self.addCleanup(reader.rollback)
        reader.execute(sql.SQL("CREATE ROLE {}").format(role))
        reader.execute("REVOKE EXECUTE ON FUNCTION pg_catalog.pg_control_system() FROM PUBLIC")
        reader.execute(
            sql.SQL("GRANT SELECT ON source_ingestion_run, vehicle_position_observation, "
                    "trip_update_observation TO {}").format(role)
        )
        reader.execute(sql.SQL("SET LOCAL ROLE {}").format(role))
        before = reader.execute("SELECT pg_current_snapshot()::text").fetchone()
        self.assertEqual(
            self.reference(reader, SNAPSHOT)["revision"]["scope_source"], "database_oid"
        )
        self.assertEqual(reader.execute("SELECT current_user").fetchone(), ("mp026b_scope_test",))
        self.assertEqual(reader.execute("SELECT pg_current_snapshot()::text").fetchone(), before)
