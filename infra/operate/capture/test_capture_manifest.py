import json
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import capture_manifest
from capture_manifest import (
    build_manifest,
    collect,
    log_counts,
    profile_digest,
    summarize,
    write_json,
)


class CaptureManifestTest(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 25, 23, tzinfo=timezone.utc)
        self.end = self.start + timedelta(seconds=180)
        self.profile = '["sha256:gtfs",{},{}]'

    def run_row(self, feed, at, status="ok", *, profile=True, retroactive=False):
        return {
            "feed_name": feed,
            "started_at": self.start + timedelta(seconds=at),
            "status": status,
            "anchor_profile": self.profile if profile else None,
            "is_retroactive": retroactive,
        }

    def test_coverage_uses_errors_and_unexpected_attempts_and_includes_edges(self):
        runs = [
            self.run_row("vehicle_positions", 0),
            self.run_row("vehicle_positions", 60),
            self.run_row("vehicle_positions", 90, "error"),
            self.run_row("vehicle_positions", 150),
            self.run_row("alerts", 61, "partial"),
            self.run_row("alerts", 70),
            self.run_row("alerts", 110),
        ]
        result = summarize(runs, self.start, self.end, self.profile, Counter(trip_updates=1))
        coverage = result["coverage_by_feed"]
        self.assertEqual(result["cycles"], {"feed_attempts": 8, "poll_rounds_started": 4})
        self.assertEqual(coverage["vehicle_positions"]["ok_pct"], 75)
        self.assertEqual(coverage["vehicle_positions"]["error"], 1)
        self.assertEqual(coverage["trip_updates"]["ok_pct"], 0)
        self.assertEqual(coverage["trip_updates"]["persisted_attempts"], 0)
        self.assertEqual(coverage["alerts"]["partial"], 1)
        self.assertEqual(coverage["alerts"]["ok_pct"], 66.667)
        self.assertEqual([gap["seconds"] for gap in coverage["vehicle_positions"]["gaps_over_60_seconds"]], [90])
        self.assertEqual([gap["seconds"] for gap in coverage["alerts"]["gaps_over_60_seconds"]], [70, 70])
        self.assertEqual([gap["seconds"] for gap in coverage["trip_updates"]["gaps_over_60_seconds"]], [180])

    def test_manifest_writes_runtime_provenance_and_preserves_absent_coverage(self):
        metadata = {
            "head": "synthetic",
            "collector": {"poll_interval_seconds": 30},
            "gtfs": {"sha256": "synthetic"},
            "geometry_catalog_version": "sha256:geometry",
            "profile": {"anchor_profile": self.profile},
            "migrations": [{"name": "0001_init.up.sql"}],
        }
        session = {"started_at_utc": self.start.isoformat(), "finished_at_utc": self.end.isoformat()}
        runs = [
            self.run_row("vehicle_positions", 0),
            self.run_row("vehicle_positions", 31, profile=False, retroactive=True),
        ]
        manifest = build_manifest(
            metadata, session, runs, {"vehicle_position_observation": 7},
            2, {"stale": 3}, Counter(http_retry_failure=1), Counter(),
        )
        self.assertEqual(manifest["period"]["start_europe_madrid"], "2026-11-26T00:00:00+01:00")
        self.assertEqual(manifest["period"]["duration_seconds"], 180)
        self.assertEqual(manifest["hot_rows"]["vehicle_position_observation"], 7)
        self.assertEqual(manifest["distinct_vehicles"], 2)
        self.assertEqual(manifest["quality"]["flags"], {"stale": 3})
        self.assertEqual(manifest["errors_by_type"], {"http_retry_failure": 1})
        self.assertEqual(manifest["quality"]["run_profiles"], {
            "missing": 1, "matching": 1, "recorded_sha256": {profile_digest(self.profile): 1},
            "retroactive": 1,
        })
        self.assertIsNone(manifest["coverage_by_feed"]["alerts"]["ok_pct"])
        with TemporaryDirectory() as directory:
            target = Path(directory) / "manifest.json"
            write_json(target, manifest)
            self.assertEqual(json.loads(target.read_text()), manifest)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_log_errors_are_classified_and_payload_text_is_ignored(self):
        with TemporaryDirectory() as directory:
            log = Path(directory) / "collector.log"
            log.write_text(
                "2026-11-25 23:00:00,000 WARNING fetch_with_retry: intento 1/4 falló\n"
                "2026-11-25 23:00:01,000 ERROR run_cycle: alerts falló: agotados 4 intentos contra URL\n"
                "2026-11-25 23:00:02,000 ERROR run_cycle: alerts falló: validación\n"
                "2026-11-25 23:00:03,000 ERROR Ciclo inesperadamente fallido para alerts\n"
                "2026-11-25 23:00:04,000 ERROR Conexión con PostgreSQL perdida durante alerts\n"
                "2026-11-25 23:00:05,000 WARNING Geometría sin verificar; se conserva el GPS\n"
                "    ERROR run_cycle: línea dentro de un cuerpo\n"
            )
            errors, unexpected = log_counts(log)
        self.assertEqual(errors, {
            "http_retry_failure": 1, "fetch_exhausted": 1, "feed_validation": 1,
            "unexpected_cycle_failure": 1, "database_lost": 1, "geometry_unverified": 1,
        })
        self.assertEqual(unexpected, {"alerts": 1})

    def test_collect_scopes_observations_by_run_and_events_by_utc_window(self):
        run = {"id": 32, **self.run_row("vehicle_positions", 1)}
        conn = Mock()
        conn.execute.side_effect = [
            Mock(**{"fetchall.return_value": [run]}),
            Mock(**{"fetchone.return_value": {"rows": 5, "vehicles": 2}}),
            Mock(**{"fetchone.return_value": {"rows": 4}}),
            Mock(**{"fetchone.return_value": {"rows": 3}}),
            Mock(**{"fetchall.return_value": [{"flag": "stale", "rows": 2}]}),
        ]
        runs, rows, vehicles, flags = collect(conn, self.start, self.end)
        first, *counts, last = [call.args for call in conn.execute.call_args_list]
        self.assertIn("started_at >= %s AND started_at < %s", first[0])
        self.assertEqual(first[1], (self.start, self.end))
        for sql, args in counts:
            self.assertIn("ingestion_run_id = ANY", sql)
            self.assertEqual(args, ([32],))
        self.assertIn("occurred_at >= %s AND occurred_at < %s", last[0])
        self.assertEqual(last[1], (self.start, self.end))
        self.assertEqual(runs, [run])
        self.assertEqual(rows, {
            "source_ingestion_run": 1, "vehicle_position_observation": 5,
            "trip_update_observation": 4, "service_alert": 3, "data_quality_event": 2,
        })
        self.assertEqual((vehicles, flags), (2, {"stale": 2}))

    def test_dump_is_checksummed_idempotent_and_refuses_to_overwrite(self):
        def dump(argv, *, stdout, check, timeout):
            self.assertIn("PGOPTIONS=-c default_transaction_read_only=on", argv)
            self.assertIn("--format=custom", argv)
            stdout.write(b"abc")

        with TemporaryDirectory() as directory, patch(
            "subprocess.run", side_effect=dump,
        ) as command:
            directory = Path(directory)
            evidence = capture_manifest.dump_database(directory)
            self.assertEqual(evidence["sha256"],
                             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            self.assertEqual(capture_manifest.dump_database(directory), evidence)
            self.assertEqual(command.call_count, 1)
            (directory / evidence["checksum_path"]).write_text("wrong")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                capture_manifest.dump_database(directory)
            self.assertEqual((directory / evidence["checksum_path"]).read_text(), "wrong")
            self.assertEqual((directory / evidence["path"]).read_bytes(), b"abc")


if __name__ == "__main__":
    unittest.main()
