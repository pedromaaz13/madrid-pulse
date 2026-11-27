"""Ejecuta y supervisa una sesión de captura en primer plano."""

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager, suppress
from datetime import date
from pathlib import Path

from capture_coverage import DEFAULT_GAP_S, DEFAULT_MAX_CIVIL_MINUTES, Coverage
from capture_manifest import (
    DATABASE_URL,
    MADRID,
    UNEXPLAINED_ERRORS,
    dump_database,
    file_sha256,
    manifest_summary,
    profile_digest,
    read_manifest,
    utcnow,
    write_json,
)

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/matu/Documents/DATA/madrid-pulse")
CAPTURE = MAIN / "data/capture"
SOURCE = MAIN / "data/gtfs_static/fomento_transit.zip"
SMOKE_SHA256 = "58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e"
ADVISORY_LOCK = 1297101395
CHILD = """from services.collector.__main__ import main
import os
os.environ["PGAPPNAME"] = f"mp028-capture collector pid={os.getpid()}"
try:
    main()
except KeyboardInterrupt:
    pass
"""
LOCK_PROBE = """from services.collector import __main__

def never_poll(*args, **kwargs):
    raise SystemExit("El proceso de prueba alcanzó el bucle de polling")

__main__.run_cycle = never_poll
__main__.main()
"""


def configure(source):
    # Limitar libpq y la configuración de ingesta a la base y al perfil del protocolo.
    for name in tuple(os.environ):
        if name.startswith(("PG", "COLLECTOR_", "MADRID_PULSE_")):
            os.environ.pop(name)
    os.environ.update(
        MADRID_PULSE_ENV="live",
        MADRID_PULSE_DATABASE_URL=DATABASE_URL,
        MADRID_PULSE_GTFS_SOURCE=str(source),
        COLLECTOR_POLL_INTERVAL_SECONDS="30",
        MADRID_PULSE_MODE="live",
        MADRID_PULSE_SHORT_NAME="",
        TZ="UTC",
    )
    time.tzset()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))


def metadata(source, archive):
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
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5,
                         options="-c statement_timeout=5000") as conn:
        migrations = conn.execute(
            "SELECT name, sha256, applied_at FROM mp028_capture.migration ORDER BY name"
        ).fetchall()
    expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / "infra/migrations").glob("*.up.sql")}
    if {row["name"]: row["sha256"] for row in migrations} != expected:
        raise RuntimeError("Las migraciones de la base no coinciden con el worktree")
    for row in migrations:
        row["applied_at"] = row["applied_at"].isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"]))
    return {
        "head": head,
        "worktree_dirty": dirty,
        "collector": {
            "head": head,
            "branch": branch or None,
            "worktree_dirty": dirty,
            "profile_version": profile_digest(profile),
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
            "source": str(source),
            "collector_source": str(archive),
            "local_archive": str(archive.relative_to(CAPTURE)),
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


def lock_holder():
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5,
                         options="-c statement_timeout=3000") as conn:
        return conn.execute("""
            SELECT l.pid AS backend_pid, a.application_name, a.client_port
            FROM pg_locks l LEFT JOIN pg_stat_activity a ON a.pid = l.pid
            WHERE l.locktype = 'advisory' AND l.granted
              AND l.database = (SELECT oid FROM pg_database WHERE datname = current_database())
              AND l.classid = 0 AND l.objid = %s::oid AND l.objsubid = 1
        """, (ADVISORY_LOCK,)).fetchone()


def require_free_lock():
    holder = lock_holder()
    if holder is not None:
        raise RuntimeError(
            f"Bloqueo del colector {ADVISORY_LOCK} retenido: backend PostgreSQL "
            f"PID {holder['backend_pid']}, aplicación {holder['application_name']!r}, "
            f"puerto cliente {holder['client_port']}. Identifica el PID local del colector "
            "y envíale SIGINT tras verificarlo; consulta CAPTURE_PROTOCOL.md."
        )


def preserve_gtfs(source):
    digest = file_sha256(source)
    archive = CAPTURE / "gtfs"
    archive.mkdir(exist_ok=True)
    target = archive / f"{digest}.zip"
    if not target.exists():
        with tempfile.TemporaryDirectory(dir=archive) as scratch:
            temporary = Path(scratch) / target.name
            shutil.copyfile(source, temporary)
            if file_sha256(temporary) != digest:
                raise RuntimeError("El ZIP cambió durante la preparación")
            temporary.chmod(0o400)
            with suppress(FileExistsError):
                target.hardlink_to(temporary)
    if file_sha256(target) != digest:
        raise RuntimeError("La copia local de GTFS no coincide con su SHA-256")
    return target


def smoke_lock(directory):
    result = subprocess.run(
        [sys.executable, "-c", LOCK_PROBE], capture_output=True,
        text=True, timeout=15, check=False,
    )
    (directory / "collector-lock.log").write_text(result.stdout + result.stderr)
    return {
        "exit_code": result.returncode,
        "competing_collector_rejected": (
            result.returncode == 1 and "Ya hay otro colector activo" in result.stderr
        ),
    }


@contextmanager
def open_progress():
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(
        DATABASE_URL, row_factory=dict_row, connect_timeout=5, autocommit=True,
        options="-c default_transaction_read_only=on -c statement_timeout=3000",
    ) as conn:
        cursor = conn.execute(
            "SELECT coalesce(max(id), 0) AS id FROM source_ingestion_run"
        ).fetchone()["id"]

        def read():
            nonlocal cursor
            rows = conn.execute("""
                SELECT id, feed_name, started_at, finished_at, status, anchor_profile
                FROM source_ingestion_run
                WHERE id > %s AND feed_name IN ('vehicle_positions', 'trip_updates', 'alerts')
                ORDER BY id
            """, (cursor,)).fetchall()
            if rows:
                cursor = rows[-1]["id"]
            return rows

        yield read


def watch(process, directory, session, coverage, args, gtfs, read, stopped):
    valid_from = date.fromisoformat(gtfs["valid_from"])
    valid_until = date.fromisoformat(gtfs["valid_until"])

    def stop_reason():
        if coverage.sample(utcnow(), time.monotonic()):
            return "wall_clock_reversed"
        if stopped():
            return stopped()
        if process.poll() is not None:
            return "collector_exit"
        if not valid_from <= coverage.wall.astimezone(MADRID).date() <= valid_until:
            return "gtfs_out_of_validity"
        if (coverage.wall - coverage.started).total_seconds() >= args.max_civil_minutes * 60:
            return "civil_limit"
        return None

    while True:
        if reason := stop_reason():
            return reason
        if args.smoke and "lock_probe" not in session:
            if lock_holder() is not None:
                session["lock_probe"] = smoke_lock(directory)
                if not session["lock_probe"]["competing_collector_rejected"]:
                    return "lock_probe_failed"
            elif time.monotonic() - session["started_monotonic"] >= 30:
                return "lock_probe_failed"
        runs = read()
        if reason := stop_reason():
            return reason
        for run in runs:
            coverage.record(run)
        if coverage.effective >= args.minutes * 60:
            return "effective_target"
        time.sleep(1)


def stop_collector(process):
    if process.poll() is not None:
        return False
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=15)
        return False
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return True


def collector_lock_released(pid):
    for _ in range(3):
        holder = lock_holder()
        if holder is None:
            return True
        if holder["application_name"] != f"mp028-capture collector pid={pid}":
            return False
        time.sleep(0.25)
    return lock_holder() is None


def finalize(directory, initial, session, process, coverage, reason):
    errors = session["closure_errors"]

    def attempt(label, operation):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - conservar la evidencia aunque falle una operación de cierre.
            errors.append(label)
            print(f"{label}: {exc}", file=sys.stderr)
            return None

    forced = attempt("collector_shutdown_failed", lambda: stop_collector(process))
    if coverage.sample(utcnow(), time.monotonic()):
        errors.append("wall_clock_reversed_during_shutdown")
    if (reason == "effective_target"
        and coverage.wall.astimezone(MADRID).date() > date.fromisoformat(initial["gtfs"]["valid_until"])):
        reason = "gtfs_out_of_validity"
    session.update(
        coverage.fields(),
        finished_at_utc=coverage.wall.isoformat(), stop_reason=reason,
        collector_exit_code=process.returncode, forced_stop=forced,
        completed=False,
    )
    write_json(directory / "session.json", session)
    unchanged = attempt("gtfs_verification_failed", lambda: (
        file_sha256(Path(initial["gtfs"]["collector_source"])) == initial["gtfs"]["sha256"]
    ))
    session["gtfs_unchanged"] = unchanged
    if unchanged is False:
        errors.append("gtfs_hash_mismatch")
    released = attempt("database_lock_check_failed", lambda: collector_lock_released(process.pid))
    session["database_lock_released"] = released
    if released and process.returncode is not None:
        session["raw_dump"] = attempt("pg_dump_failed", lambda: dump_database(directory))
    elif released is False:
        errors.append("database_lock_held")
    write_json(directory / "session.json", session)
    manifest = attempt("manifest_failed", lambda: read_manifest(directory, initial, session))
    if manifest is None:
        manifest = {
            **manifest_summary(initial, session),
            **dict.fromkeys(("coverage_by_feed", "cycles", "errors_by_type", "hot_rows",
                             "distinct_vehicles", "quality")),
        }
    else:
        unexplained = UNEXPLAINED_ERRORS.intersection(manifest["errors_by_type"])
        profiles = manifest["quality"]["run_profiles"]
        if profiles["matching"] != manifest["hot_rows"]["source_ingestion_run"]:
            unexplained.add("collector_profile_mismatch")
        session["unexplained_errors"] = sorted(unexplained)
        session["completed"] = (
            reason == "effective_target" and process.returncode == 0 and forced is False
            and (session["kind"] != "smoke" or session.get("lock_probe", {}).get(
                "competing_collector_rejected", False))
            and not errors and not unexplained and not coverage.profile_mismatches
            and bool(session.get("raw_dump"))
        )
    attempt("manifest_write_failed", lambda: write_json(directory / "manifest.json", manifest))
    if errors:
        session["completed"] = False
    write_json(directory / "session.json", session)
    print(f"Fin: {reason}; cobertura efectiva {coverage.effective:.3f} s"
          f"; civil {session['civil_duration_s']:.3f} s; "
          f"{'completa' if session['completed'] else 'incompleta'}", flush=True)
    return int(not session["completed"])


def supervise(directory, args, initial):
    require_free_lock()
    stop_signal = None

    def stop(signum, _frame):
        nonlocal stop_signal
        stop_signal = signal.Signals(signum).name

    handlers = {signum: signal.signal(signum, stop)
                for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    started = utcnow()
    started_monotonic = time.monotonic()
    coverage = Coverage(
        started, started_monotonic, args.gap_seconds, initial["profile"]["anchor_profile"],
    )
    session = {
        "started_at_utc": started.isoformat(),
        "started_monotonic": started_monotonic,
        "planned_minutes": args.minutes,
        "effective_target_s": args.minutes * 60,
        "max_civil_duration_s": args.max_civil_minutes * 60,
        "cycle_gap_threshold_s": args.gap_seconds,
        "supervisor_pid": os.getpid(),
        "kind": "smoke" if args.smoke else "session",
        "closure_errors": [],
    }
    process = None
    reason = "supervisor_error"
    try:
        with (directory / "collector.log").open("w") as log, open_progress() as read:
            if stop_signal:
                reason = stop_signal
            else:
                process = subprocess.Popen(
                    [sys.executable, "-c", CHILD], stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                session["collector_pid"] = process.pid
                write_json(directory / "session.json", session)
                reason = watch(process, directory, session, coverage, args, initial["gtfs"],
                               read, lambda: stop_signal)
    except Exception as exc:  # noqa: BLE001 - cualquier error de supervisión exige parar el colector.
        reason = "supervisor_error"
        session["supervisor_error"] = type(exc).__name__
        print(f"Error de supervisión: {exc}", file=sys.stderr)
    finally:
        try:
            if process is not None:
                result = finalize(directory, initial, session, process, coverage, reason)
            else:
                coverage.sample(utcnow(), time.monotonic())
                session.update(coverage.fields(), finished_at_utc=coverage.wall.isoformat(),
                               stop_reason=reason, completed=False)
                write_json(directory / "session.json", session)
                result = 1
        finally:
            for signum, handler in handlers.items():
                signal.signal(signum, handler)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("minutes", type=int, help="objetivo de cobertura efectiva en minutos")
    parser.add_argument("--max-civil-minutes", type=int, help="tope de duración civil en minutos")
    parser.add_argument("--gap-seconds", type=int, default=DEFAULT_GAP_S)
    parser.add_argument("--gtfs-source", type=Path, default=SOURCE)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.minutes < 1 or (args.smoke and not 5 <= args.minutes <= 10):
        parser.error("El objetivo efectivo debe ser positivo y de 5 a 10 min para --smoke")
    if args.max_civil_minutes is None:
        args.max_civil_minutes = 15 if args.smoke else DEFAULT_MAX_CIVIL_MINUTES
    if args.max_civil_minutes < 1 or args.gap_seconds < 1:
        parser.error("El tope civil y el umbral de hueco deben ser positivos")
    source = args.gtfs_source.resolve()
    os.umask(0o077)
    CAPTURE.mkdir(parents=True, exist_ok=True)
    with (CAPTURE / ".mp028.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "Ya hay un supervisor de captura activo; consulta CAPTURE_PROTOCOL.md.\n")
        try:
            archive = preserve_gtfs(source)
            if args.smoke and archive.stem != SMOKE_SHA256:
                raise RuntimeError("El SHA-256 del ZIP no coincide con el documentado en MP-003.")
            configure(archive)
            subprocess.run(["bash", str(ROOT / "infra/operate/capture/prepare-db.sh")], check=True)
            require_free_lock()
            initial = metadata(source, archive)
            if initial["gtfs"]["sha256"] != archive.stem:
                raise RuntimeError("El ZIP archivado cambió durante la preparación")
        except Exception as exc:  # noqa: BLE001 - mostrar el motivo del rechazo en la CLI.
            parser.exit(1, f"Preparación de captura rechazada: {exc}\n")
        day = CAPTURE / utcnow().astimezone(MADRID).date().isoformat()
        day.mkdir(exist_ok=True)
        prefix = "smoke" if args.smoke else "session"
        index = 1
        while (day / f"{prefix}-{index}").exists():
            index += 1
        directory = day / f"{prefix}-{index}"
        directory.mkdir()
        write_json(directory / "metadata.json", initial)
        print(f"Captura en {directory}", flush=True)
        try:
            return supervise(directory, args, initial)
        except RuntimeError as exc:
            parser.exit(1, f"Captura rechazada: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
