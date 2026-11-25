"""Base admisible por run y exclusión entre dos procesos de polling reales."""

import os
import selectors
import subprocess
import sys
import unittest
from datetime import timedelta

from apps.api import db, snapshot
from apps.api.gtfs_source import load_network
from packages.contracts.canonical import TripUpdateObservation
from services.collector import db as writer
from tests.e2e import test_stop_state as real
from tests.postgres import connect_disposable_or_skip


class StopStateDatabase(unittest.TestCase):
    def setUp(self):
        self.conn = connect_disposable_or_skip()
        self.addCleanup(self.conn.close)

    def test_exclusive_collectors(self):
        # Ambos procesos usan la entrada normal. Sustituye solo el polling de red.
        script = """
import sys
from services.collector import __main__ as collector
def offline(*args, **kwargs):
    print("poll",flush=True)
    sys.stdin.readline()
    raise SystemExit(0)
collector.run_cycle = offline
collector.main()
"""
        args = [sys.executable, "-c", script]
        env = dict(os.environ, MADRID_PULSE_GTFS_SOURCE="")
        with subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env
        ) as first:
            try:
                with selectors.DefaultSelector() as sel:
                    sel.register(first.stdout, selectors.EVENT_READ)
                    self.assertTrue(sel.select(15))
                self.assertEqual(first.stdout.readline().strip(), "poll")
                other = subprocess.run(
                    args, input="", capture_output=True, text=True, env=env, timeout=15
                )
                self.assertNotEqual(other.returncode, 0)
                self.assertIn("otro colector activo", other.stderr)
                self.assertEqual(other.stdout, "")
            finally:
                first.communicate("\n", timeout=10)
        self.assertEqual(
            subprocess.run(
                args, input="", capture_output=True, text=True, env=env, timeout=15
            ).returncode,
            0,
        )

    def run_id(self, feed, at):
        return writer.insert_ingestion_run(
            self.conn,
            feed_name=feed,
            source_timestamp=at,
            started_at=at,
            finished_at=at,
            status="ok",
            entity_count=1,
            payload_hash="c" * 64,
        )

    def prepare(self):
        # Espacio de prueba independiente de los runs anteriores de la suite.
        for table in (
            "source_ingestion_run",
            "trip_update_observation",
            "vehicle_position_observation",
        ):
            self.conn.execute(f"CREATE TEMP TABLE {table} (LIKE public.{table} INCLUDING ALL)")
        # LIKE INCLUDING ALL copia índices y columnas pero omite los triggers.
        self.conn.execute("""CREATE TRIGGER classify_ingestion BEFORE INSERT ON source_ingestion_run
                             FOR EACH ROW EXECUTE FUNCTION classify_ingestion_run()""")
        real.RealStops.setUpClass()
        self.net = real.RealStops.network
        self.pos = real.RealStops.second
        self.at = self.pos["19667"].observed_at
        self.conn.execute(
            "SELECT set_config('madrid_pulse.anchor_profile',%s,true)",
            (self.net.anchor_profile(self.net.engine.thresholds),),
        )

    def anchors(self):
        run_id = self.run_id("vehicle_positions", self.at)
        for p in self.pos.values():
            writer.insert_vehicle_position_observation(
                self.conn, p, received_at=self.at, ingestion_run_id=run_id
            )

    def update(self, run_id, obs_offset, status):
        for p in self.pos.values():
            obs = TripUpdateObservation(
                source_trip_id=p.source_trip_id,
                observed_at=self.at + timedelta(seconds=obs_offset),
                schedule_relationship=status,
                delay_coverage="missing",
                payload_hash=p.payload_hash,
            )
            writer.insert_trip_update_observation(
                self.conn, obs, received_at=self.at, ingestion_run_id=run_id
            )

    def frames(self, offset, *, replay=False, restart=False):
        at = self.at + timedelta(seconds=offset)
        network = load_network(real.RealStops.config) if restart else self.net
        resolver = network.service_date_resolver(at)
        histories = db.latest_vehicle_histories(
            self.conn, as_of=at, observed_through=at if replay else None
        )
        return {
            h.source_vehicle_id: snapshot.build_vehicle_entry(
                network, real.RealStops.config, h, None, at, at, resolver
            )
            for h in histories
        }

    def test_f1_availability_changes(self):
        self.prepare()
        scenarios = (
            [],
            [(20, 20, "CANCELED")],
            [(181, 20, "CANCELED")],
            [(60, 60, "CANCELED"), (150, 150, "SCHEDULED")],
            [(-300, -300, "CANCELED")],
            [(-86400, -86400, "CANCELED")],
            [(-5, -700, "CANCELED")],
        )
        for events in scenarios:
            with self.subTest(events=events):
                self.conn.execute("SAVEPOINT scenario")
                frames = {}
                ids = {}
                for age in sorted({0, 179, 180, 181, 400, *[e[0] for e in events]}):
                    for visible, observed, status in events:
                        if age == visible:
                            self.update(
                                self.run_id("trip_updates", self.at + timedelta(seconds=age)),
                                observed,
                                status,
                            )
                    if age < 0:
                        continue
                    if age == 0:
                        self.anchors()
                    frame = self.frames(age, restart=age == 400)
                    self.assertEqual(len(frame), 44)
                    for vid, item in frame.items():
                        r = item.rendered
                        if age == 0:
                            ids[vid] = r.progress_envelope.envelope_id
                        if r.progress_envelope:
                            self.assertEqual(r.progress_envelope.envelope_id, ids[vid])
                            self.assertEqual(
                                r.progress_envelope.hold_reason == "trip_canceled",
                                events == [(-300, -300, "CANCELED")],
                            )
                        if age in (181, 400):
                            self.assertEqual(r.frozen_basis, "authorized_envelope_end")
                            self.assertEqual(r.progress_m, frames[180][vid].rendered.progress_m)
                        known = [e for e in events if e[0] <= age and e[1] >= -600]
                        self.assertEqual(
                            item.schedule_relationship, known[-1][2] if known else None
                        )
                    frames[age] = frame
                self.conn.execute("ROLLBACK TO SAVEPOINT scenario")

    def test_retroactive_run(self):
        self.prepare()
        self.run_id("alerts", self.at - timedelta(seconds=5))
        retro = self.run_id("trip_updates", self.at - timedelta(seconds=10))
        self.anchors()
        before = self.frames(99.5)
        self.update(retro, -10, "CANCELED")
        live, replay = self.frames(100), self.frames(100, replay=True)
        self.assertTrue(
            all(
                item.rendered.progress_m >= before[v].rendered.progress_m
                for v, item in live.items()
            )
        )
        rewind = max(
            before[v].rendered.progress_m - item.rendered.progress_m for v, item in replay.items()
        )
        self.assertAlmostEqual(rewind, 1310.66, delta=0.01)
