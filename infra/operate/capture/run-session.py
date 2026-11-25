#!/usr/bin/env python3
"""Ejecuta y supervisa una sesión de captura en primer plano."""

import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from capture_manifest import DATABASE_URL, MADRID, profile_digest, utcnow, write_json, write_manifest

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/matu/Documents/DATA/madrid-pulse")
CAPTURE = MAIN / "data/capture"
SOURCE = MAIN / "data/gtfs_static/fomento_transit.zip"
ADVISORY_LOCK = 1297101395
CHILD = """from services.collector.__main__ import main
try:
    main()
except KeyboardInterrupt:
    pass
"""


def configure():
    # Limitar libpq y la configuración de ingesta a la base y al perfil del protocolo.
    for name in tuple(os.environ):
        if name.startswith(("PG", "COLLECTOR_", "MADRID_PULSE_")):
            os.environ.pop(name)
    os.environ.update(
        MADRID_PULSE_ENV="live",
        MADRID_PULSE_DATABASE_URL=DATABASE_URL,
        MADRID_PULSE_GTFS_SOURCE=str(SOURCE),
        COLLECTOR_POLL_INTERVAL_SECONDS="30",
        MADRID_PULSE_MODE="live",
        MADRID_PULSE_SHORT_NAME="",
        TZ="UTC",
    )
    time.tzset()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))


def metadata():
    import psycopg
    from psycopg.rows import dict_row

    from apps.api.config import ApiConfig
    from apps.api.gtfs_source import load_network
    from services.collector.config import CollectorConfig

    config = CollectorConfig.from_env()
    api = ApiConfig.from_env()
    network = load_network(api)
    profile = network.anchor_profile(api.thresholds)
    version, thresholds, geometries = json.loads(profile)
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        migrations = conn.execute(
            "SELECT name, sha256, applied_at FROM mp028_capture.migration ORDER BY name"
        ).fetchall()
    expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / "infra/migrations").glob("*.up.sql")}
    if {row["name"]: row["sha256"] for row in migrations} != expected:
        raise RuntimeError("Las migraciones de la base no coinciden con el worktree")
    for row in migrations:
        row["applied_at"] = row["applied_at"].isoformat()
    return {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"])),
        "collector": {
            "environment": config.environment,
            "target": {"host": "127.0.0.1", "port": 5466, "database": "mp028_capture"},
            "feeds": {feed.name: feed.url for feed in config.feeds},
            "poll_interval_seconds": config.poll_interval_seconds,
            "request_timeout_seconds": config.request_timeout_seconds,
            "max_retries": config.max_retries,
            "backoff_base_seconds": config.backoff_base_seconds,
            "retro_tolerance_seconds": 2,
        },
        "gtfs": {
            "source": str(SOURCE),
            "sha256": version.split(":")[1],
            "gtfs_version": version,
            "valid_from": network.gtfs_valid_from.isoformat(),
            "valid_until": network.gtfs_valid_until.isoformat(),
        },
        "geometry_catalog_version": network.geometry_catalog_version,
        "geometry_version_by_pattern": geometries,
        "catalog_version": network.catalog_version,
        "profile": {
            "name": "P-024",
            "thresholds": thresholds,
            "sha256": profile_digest(profile),
            "anchor_profile": profile,
        },
        "migrations": migrations,
    }


def lock_available():
    import psycopg

    with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
        return conn.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK,)).fetchone()[0]


def smoke_lock(process, directory, stopped):
    probe = {"competing_collector_rejected": False}
    for _ in range(30):
        if process.poll() is not None or stopped():
            break
        if not lock_available():
            result = subprocess.run(
                [sys.executable, "-m", "services.collector"], capture_output=True,
                text=True, timeout=15, check=False,
            )
            (directory / "collector-lock.log").write_text(result.stdout + result.stderr)
            probe["exit_code"] = result.returncode
            probe["competing_collector_rejected"] = (
                result.returncode == 1 and "Ya hay otro colector activo" in result.stderr
            )
            break
        time.sleep(1)
    return probe


def supervise(directory, args, initial):
    from packages.movement.profile import source_version

    if not lock_available():
        raise RuntimeError("Ya hay un colector activo en la base de captura")
    stop_signal = None

    def stop(signum, _frame):
        nonlocal stop_signal
        stop_signal = signal.Signals(signum).name

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    started = utcnow()
    session = {
        "started_at_utc": started.isoformat(),
        "planned_minutes": args.minutes,
        "supervisor_pid": os.getpid(),
        "kind": "smoke" if args.smoke else "session",
    }
    with (directory / "collector.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, "-c", CHILD], stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        deadline = time.monotonic() + args.minutes * 60
        session["collector_pid"] = process.pid
        reason = "collector_exit"
        forced = False
        try:
            write_json(directory / "session.json", session)
            if args.smoke:
                session["lock_probe"] = smoke_lock(process, directory, lambda: stop_signal)
                if not session["lock_probe"]["competing_collector_rejected"] and not stop_signal:
                    raise RuntimeError("Fallo de la prueba de bloqueo de colector")
            while process.poll() is None:
                if stop_signal or time.monotonic() >= deadline:
                    reason = stop_signal or "duration_elapsed"
                    break
                time.sleep(min(1, max(0, deadline - time.monotonic())))
        except Exception:
            reason = "supervisor_error"
            raise
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    forced = True
                    process.kill()
                    process.wait()
            session.update(
                finished_at_utc=utcnow().isoformat(), stop_reason=reason,
                collector_exit_code=process.returncode, forced_stop=forced,
            )
            # Persistir el cierre incluso si ya no se puede consultar PostgreSQL.
            write_json(directory / "session.json", session)
            session["gtfs_unchanged"] = SOURCE.is_file() and source_version(SOURCE) == initial["gtfs"]["gtfs_version"]
            session["database_lock_released"] = lock_available()
            write_json(directory / "session.json", session)
            write_manifest(directory)
    return int(not (
        reason == "duration_elapsed" and process.returncode == 0 and not forced
        and session["gtfs_unchanged"] and session["database_lock_released"]
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("minutes", type=int)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.minutes < 1 or (args.smoke and not 5 <= args.minutes <= 10):
        parser.error("La duración debe ser positiva y de 5 a 10 min para --smoke")
    configure()
    os.umask(0o077)
    CAPTURE.mkdir(parents=True, exist_ok=True)
    with (CAPTURE / ".mp028.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "Ya hay un supervisor de captura activo.\n")
        subprocess.run(["bash", str(ROOT / "infra/operate/capture/prepare-db.sh")], check=True)
        initial = metadata()
        if args.smoke and (
            initial["gtfs"]["valid_from"], initial["gtfs"]["valid_until"]
        ) != ("2026-11-20", "2026-12-19"):
            parser.exit(1, "La vigencia del GTFS no coincide con la autorizada para el smoke.\n")
        day = CAPTURE / utcnow().astimezone(MADRID).date().isoformat()
        day.mkdir(exist_ok=True)
        directory = day / "smoke"
        if not args.smoke:
            index = 1
            while (day / f"session-{index}").exists():
                index += 1
            directory = day / f"session-{index}"
        directory.mkdir()
        write_json(directory / "metadata.json", initial)
        print(f"Captura en {directory}", flush=True)
        return supervise(directory, args, initial)


if __name__ == "__main__":
    raise SystemExit(main())
