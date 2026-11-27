import hashlib
import importlib
import inspect
import json
import signal
import subprocess
import time
import unittest
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import capture_manifest as cm

supervisor = importlib.import_module("run-session")
PROFILE = '["sha256:synthetic",{},{}]'
START = datetime(2026, 11, 26, 8, tzinfo=timezone.utc)


class Clock:
    def __init__(self, start, steps, interrupt):
        self.wall = start
        self.active = 0
        self.steps = steps
        self.interrupt = interrupt

    def utcnow(self):
        return self.wall

    def monotonic(self):
        return self.active

    def sleep(self, seconds):
        self.active += seconds
        self.wall += timedelta(seconds=seconds + self.steps.get(self.active, 0))
        if self.active == self.interrupt:
            signal.raise_signal(signal.SIGINT)


class Collector:
    pid = 42

    def __init__(self, forced):
        self.forced = forced
        self.returncode = None
        self.actions = []

    def poll(self):
        return self.returncode

    def send_signal(self, signum):
        self.actions.append(signum)

    def wait(self, timeout=None):
        self.actions.append(timeout)
        if self.forced and timeout is not None:
            raise subprocess.TimeoutExpired("collector", timeout)
        self.returncode = -signal.SIGKILL if self.forced else 0

    def kill(self):
        self.actions.append(signal.SIGKILL)


class CaptureSupervisorTest(unittest.TestCase):
    def setUp(self):
        scratch = self.enterContext(TemporaryDirectory())
        self.directory = Path(scratch)
        self.archive = self.directory / "input.zip"
        self.archive.write_bytes(b"synthetic GTFS")
        self.initial = {
            "profile": {"anchor_profile": PROFILE},
            "gtfs": {
                "valid_from": "2026-11-26",
                "valid_until": "2026-11-26",
                "collector_source": str(self.archive),
                "sha256": "b93ae1dcc5b22940a369fd59288e308d1cf5691fd567962c498270c159cf16f1",
            },
        }
        # Compartir el hash conocido también con el supervisor anterior.
        self.initial["gtfs"]["gtfs_version"] = "sha256:" + self.initial["gtfs"]["sha256"]

    def simulate(self, *, start=START, minutes=2, cap=360, threshold=120, steps=None,
                 absent=(), failed=(), interrupt=None, forced=False, log="", holder=None,
                 manifest_failure=False):
        clock = Clock(start, steps or {}, interrupt)
        collector = Collector(forced)
        collected = []
        observed = set()
        args = SimpleNamespace(minutes=minutes, max_civil_minutes=cap,
                               gap_seconds=threshold, smoke=False)

        @contextmanager
        def progress():
            def read():
                at = clock.active
                if at % 30 or at in observed or at in absent:
                    return []
                observed.add(at)
                round_rows = [
                    {
                        "id": len(collected) + i + 1,
                        "feed_name": feed,
                        "started_at": clock.wall,
                        "finished_at": clock.wall,
                        "status": "error" if at in failed and i == 1 else "ok",
                        "anchor_profile": PROFILE,
                        "is_retroactive": False,
                    }
                    for i, feed in enumerate(cm.FEEDS)
                ]
                collected.extend(round_rows)
                return round_rows
            yield read

        def launch(_argv, *, stdout, **_kwargs):
            stdout.write(log)
            return collector

        def manifest(directory, metadata, session):
            if manifest_failure:
                raise RuntimeError("synthetic database failure")
            errors, unexpected = cm.log_counts(directory / "collector.log")
            return cm.build_manifest(
                metadata, session, collected, {"source_ingestion_run": len(collected)},
                0, {}, errors, unexpected,
            )

        replacements = {
            "time": clock,
            "utcnow": clock.utcnow,
            "open_progress": progress,
            "read_manifest": manifest,
            "dump_database": lambda _: {"path": "capture.dump", "sha256": "test"},
            "lock_holder": lambda: holder,
            "lock_available": lambda: holder is None,
            "write_manifest": lambda _: None,
            "SOURCE": self.archive,
        }
        with ExitStack() as stack:
            for name, replacement in replacements.items():
                stack.enter_context(patch.object(supervisor, name, replacement, create=True))
            stack.enter_context(patch.object(supervisor.subprocess, "Popen", side_effect=launch))
            result = supervisor.supervise(self.directory, args, self.initial)
        session = json.loads((self.directory / "session.json").read_text())
        return result, session, collector.actions

    def test_two_hours_effective_with_59_minute_suspension(self):
        started = time.perf_counter()
        result, session, actions = self.simulate(minutes=120, steps={3601: 59 * 60})
        runtime = time.perf_counter() - started
        self.assertEqual(result, 0)
        self.assertEqual(session["stop_reason"], "effective_target")
        self.assertEqual(session["effective_coverage_s"], 7200)
        self.assertEqual(session["civil_duration_s"], 10770)
        self.assertEqual(session["suspension_gaps"], [{
            "from_utc": (START + timedelta(seconds=3600)).isoformat(),
            "to_utc": (START + timedelta(seconds=7141)).isoformat(),
            "seconds": 3541, "kind": "clock_discontinuity", "wall_minus_monotonic_s": 3540,
        }])
        self.assertEqual([gap["seconds"] for gap in session["cycle_gaps"]], [3570])
        self.assertEqual([segment["seconds"] for segment in session["coverage_segments"]], [3600, 3600])
        manifest = json.loads((self.directory / "manifest.json").read_text())
        self.assertEqual(manifest["manifest_version"], 2)
        self.assertEqual(manifest["session"], session)
        self.assertEqual(manifest["period"]["effective_coverage_s"], 7200)
        self.assertEqual(manifest["period"]["civil_duration_s"], 10770)
        self.assertEqual(actions, [signal.SIGINT, 15])
        self.assertLess(runtime, 60)
        print(f"Simulación MP-028: 7200 s efectivos, 10770 s civiles, suspensión de 3540 s "
              f"y hueco de ciclos de 3570 s; {runtime:.3f} s reales; salida 0")

    def test_long_cycle_gap_without_clock_step(self):
        result, session, _ = self.simulate(absent=(30, 60, 90, 120))
        self.assertEqual(result, 0)
        self.assertEqual(session["effective_coverage_s"], 120)
        self.assertEqual(session["civil_duration_s"], 270)
        self.assertEqual([gap["seconds"] for gap in session["cycle_gaps"]], [150])
        self.assertEqual(session["suspension_gaps"], [])
        self.assertEqual(session["coverage_segments"][0]["from_utc"],
                         (START + timedelta(seconds=150)).isoformat())

    def test_clock_step_breaks_coverage_even_below_cycle_gap_threshold(self):
        result, session, _ = self.simulate(steps={61: 20})
        self.assertEqual(result, 0)
        self.assertEqual(session["civil_duration_s"], 170)
        self.assertEqual(session["cycle_gaps"], [])
        self.assertEqual([segment["seconds"] for segment in session["coverage_segments"]], [60, 60])

    def test_round_with_feed_error_breaks_coverage(self):
        result, session, _ = self.simulate(failed=(60,))
        self.assertEqual(result, 0)
        self.assertEqual(session["civil_duration_s"], 180)
        self.assertEqual([segment["seconds"] for segment in session["coverage_segments"]], [30, 90])

    def test_civil_limit_after_clock_jump_stops_incomplete(self):
        result, session, actions = self.simulate(cap=3, steps={61: 180})
        self.assertEqual(result, 1)
        self.assertEqual(session["stop_reason"], "civil_limit")
        self.assertEqual(session["civil_duration_s"], 241)
        self.assertEqual(session["effective_coverage_s"], 60)
        self.assertEqual(actions, [signal.SIGINT, 15])
        self.assertEqual([gap["seconds"] for gap in session["cycle_gaps"]], [181])

    def test_sigint_stops_collector_and_records_incomplete_session(self):
        result, session, actions = self.simulate(interrupt=35)
        self.assertEqual(result, 1)
        self.assertEqual(session["stop_reason"], "SIGINT")
        self.assertEqual(session["effective_coverage_s"], 30)
        self.assertFalse(session["forced_stop"])
        self.assertEqual(actions, [signal.SIGINT, 15])

    def test_force_stop_after_sigint_timeout_is_incomplete(self):
        result, session, actions = self.simulate(forced=True)
        self.assertEqual(result, 1)
        self.assertEqual(session["stop_reason"], "effective_target")
        self.assertTrue(session["forced_stop"])
        self.assertEqual(actions, [signal.SIGINT, 15, signal.SIGKILL, None])

    def test_gtfs_expires_at_local_midnight(self):
        start = START.replace(hour=22, minute=59, second=15)
        result, session, actions = self.simulate(start=start)
        self.assertEqual(result, 1)
        self.assertEqual(session["stop_reason"], "gtfs_out_of_validity")
        self.assertEqual(session["effective_coverage_s"], 30)
        self.assertEqual(session["civil_duration_s"], 45)
        self.assertEqual(actions, [signal.SIGINT, 15])

    def test_unexplained_error_makes_target_incomplete(self):
        result, session, _ = self.simulate(log="2026-11-26 08:00:01,000 ERROR Fallo desconocido\n")
        self.assertEqual(result, 1)
        self.assertEqual(session["stop_reason"], "effective_target")
        self.assertEqual(session["unexplained_errors"], ["unclassified_error"])

    def test_failed_final_query_keeps_coverage_and_marks_database_metrics_unknown(self):
        result, session, _ = self.simulate(steps={61: 20}, manifest_failure=True)
        self.assertEqual(result, 1)
        self.assertEqual(session["closure_errors"], ["manifest_failed"])
        manifest = json.loads((self.directory / "manifest.json").read_text())
        self.assertIsNone(manifest["coverage_by_feed"])
        self.assertEqual(manifest["session"]["suspension_gaps"], session["suspension_gaps"])

    def test_orphan_lock_refuses_to_start_and_identifies_holder(self):
        with self.assertRaisesRegex(RuntimeError, r"PID 123.*collector pid=456.*SIGINT"):
            self.simulate(holder={"backend_pid": 123, "client_port": 65432,
                                  "application_name": "mp028-capture collector pid=456"})
        self.assertFalse((self.directory / "collector.log").exists())

    def test_gtfs_archive_is_content_addressed_and_keeps_old_versions(self):
        with patch.object(supervisor, "CAPTURE", self.directory), patch.object(
            supervisor, "SOURCE", self.archive,
        ):
            first = self.archive_gtfs()
            self.assertEqual(self.archive_gtfs(), first)
            self.archive.write_bytes(b"synthetic second GTFS")
            second = self.archive_gtfs()
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), b"synthetic GTFS")
        self.assertEqual(first.stem, self.initial["gtfs"]["sha256"])

    def archive_gtfs(self):
        # El arnés también ejecuta el camino de archivado de a5ddc9b.
        if "version" in inspect.signature(supervisor.preserve_gtfs).parameters:
            version = "sha256:" + hashlib.sha256(self.archive.read_bytes()).hexdigest()
            return self.directory / supervisor.preserve_gtfs(version)
        return supervisor.preserve_gtfs(self.archive)

    def test_gtfs_archive_never_replaces_an_existing_path(self):
        target = self.directory / "gtfs" / (self.initial["gtfs"]["sha256"] + ".zip")

        def copy(source, destination):
            destination.write_bytes(source.read_bytes())
            target.write_bytes(b"already exists")

        with (patch.object(supervisor, "CAPTURE", self.directory),
              patch.object(supervisor, "SOURCE", self.archive),
              patch("shutil.copyfile", side_effect=copy),
              self.assertRaisesRegex(RuntimeError, "SHA-256")):
            self.archive_gtfs()
        self.assertEqual(target.read_bytes(), b"already exists")


if __name__ == "__main__":
    unittest.main()
