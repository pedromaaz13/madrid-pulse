"""Prueba de integración sobre el volcado restaurado de la jornada 1."""

import json
import os
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from packages.database import database_settings_from_env
from tests.postgres import connect_disposable_or_skip

from .segments import check_segment, isolate, windows


class SegmentIsolation(unittest.TestCase):
    def setUp(self):
        manifest_path = os.environ.get("MP025B_SEGMENT_TEST_MANIFEST")
        if not manifest_path:
            self.skipTest("Falta MP025B_SEGMENT_TEST_MANIFEST (jornada 1 restaurada)")
        url, environment = database_settings_from_env()
        endpoint = urlsplit(url)
        self.assertEqual(
            (
                endpoint.hostname,
                endpoint.port,
                endpoint.path,
                endpoint.query,
                environment,
            ),
            ("127.0.0.1", 5456, "/mp025b", "", "replay"),
        )
        self.conn = connect_disposable_or_skip()
        self.addCleanup(self.conn.close)
        manifest = json.loads(Path(manifest_path).read_text())
        self.before, self.after = windows(manifest)

    def test_isolate_filters_visible_runs_and_gps_at_restart(self):
        for after_gap, (start, end), expected in (
            (False, self.before, 9340),
            (True, self.after, 20167),
        ):
            with self.subTest(after_gap=after_gap):
                isolate(self.conn, start, end, after_gap)
                check_segment(self.conn, start, end, after_gap)
                positions, early_gps = self.conn.execute(
                    """
                    SELECT count(*), count(*) FILTER (WHERE v.observed_at < %s)
                    FROM pg_temp.vehicle_position_observation v
                    JOIN pg_temp.source_ingestion_run r ON r.id=v.ingestion_run_id
                    WHERE r.started_at >= %s AND r.started_at < %s
                    """,
                    (start, start, end),
                ).fetchone()
                self.assertEqual(positions, expected)
                if after_gap:
                    self.assertEqual(early_gps, 0)
                    excluded = self.conn.execute(
                        """
                        SELECT count(*) FROM public.vehicle_position_observation v
                        JOIN pg_temp.source_ingestion_run r ON r.id=v.ingestion_run_id
                        WHERE v.observed_at < %s
                        """,
                        (start,),
                    ).fetchone()[0]
                    self.assertEqual(excluded, 135)
                else:
                    self.assertGreater(early_gps, 0)

    def test_check_segment_detects_missing_and_extra_rows(self):
        start, end = self.after
        with self.conn.transaction(force_rollback=True):
            isolate(self.conn, start, end, after_gap=True)
            self.conn.execute("""
                CREATE OR REPLACE TEMP VIEW vehicle_position_observation AS
                SELECT * FROM public.vehicle_position_observation WHERE FALSE
            """)
            with self.assertRaisesRegex(ValueError, "vehicle_position_observation"):
                check_segment(self.conn, start, end, after_gap=True)
        with self.conn.transaction(force_rollback=True):
            isolate(self.conn, start, end, after_gap=True)
            self.conn.execute("""
                CREATE OR REPLACE TEMP VIEW trip_update_observation AS
                SELECT * FROM public.trip_update_observation
            """)
            with self.assertRaisesRegex(ValueError, "trip_update_observation"):
                check_segment(self.conn, start, end, after_gap=True)
