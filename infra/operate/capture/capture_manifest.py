"""Genera el manifiesto de MP-028 a partir de PostgreSQL y la bitácora local."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
FEEDS = ("vehicle_positions", "trip_updates", "alerts")
OBSERVATIONS = ("vehicle_position_observation", "trip_update_observation", "service_alert")
DATABASE_URL = "postgresql://mp028_capture:mp028_capture_local@127.0.0.1:5466/mp028_capture"


def utcnow():
    return datetime.now(timezone.utc)


def write_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def profile_digest(profile):
    return "sha256:" + hashlib.sha256(profile.encode()).hexdigest()


def log_counts(log_path):
    errors = Counter()
    unexpected = Counter()
    for line in log_path.read_text(errors="replace").splitlines():
        # Contar mensajes del colector, sin copiar cuerpos ni texto de excepciones.
        record = re.match(r"^\d{4}-\d{2}-\d{2} [\d:,]+ (WARNING|ERROR) (.*)", line)
        if not record:
            continue
        message = record[2]
        if message.startswith("fetch_with_retry:"):
            errors["http_retry_failure"] += 1
        elif message.startswith("run_cycle:"):
            kind = "fetch_exhausted" if "agotados " in message else "feed_validation"
            errors[kind] += 1
        elif message.startswith("Ciclo inesperadamente fallido para "):
            unexpected[message.rsplit(" ", 1)[-1]] += 1
            errors["unexpected_cycle_failure"] += 1
        elif message.startswith("Conexión con PostgreSQL perdida"):
            errors["database_lost"] += 1
        elif message.startswith("Geometría sin verificar"):
            errors["geometry_unverified"] += 1
    return errors, unexpected


def summarize(runs, start, end, expected_profile, unexpected):
    coverage = {}
    for feed in FEEDS:
        attempts = [run for run in runs if run["feed_name"] == feed]
        successful = [run for run in attempts if run["status"] == "ok"]
        points = [start, *sorted(run["started_at"] for run in successful), end]
        gaps = [
            {"from_utc": left.isoformat(), "to_utc": right.isoformat(), "seconds": duration}
            for left, right in pairwise(points)
            if (duration := (right - left).total_seconds()) > 60
        ]
        total = len(attempts) + unexpected[feed]
        coverage[feed] = {
            "attempts": total,
            "persisted_attempts": len(attempts),
            "ok": len(successful),
            "error": sum(run["status"] == "error" for run in attempts),
            "partial": sum(run["status"] == "partial" for run in attempts),
            "unexpected": unexpected[feed],
            "ok_pct": round(100 * len(successful) / total, 3) if total else None,
            "gaps_over_60_seconds": gaps,
        }
    return {
        "coverage_by_feed": coverage,
        "cycles": {
            "feed_attempts": sum(feed["attempts"] for feed in coverage.values()),
            "poll_rounds_started": coverage[FEEDS[0]]["attempts"],
        },
        "run_profiles": {
            "missing": sum(run["anchor_profile"] is None for run in runs),
            "matching": sum(run["anchor_profile"] == expected_profile for run in runs),
            "recorded_sha256": dict(Counter(
                profile_digest(run["anchor_profile"]) for run in runs if run["anchor_profile"]
            )),
            "retroactive": sum(run["is_retroactive"] for run in runs),
        },
    }


def collect(conn, start, end):
    window = (start, end)
    runs = conn.execute("""
        SELECT id, feed_name, started_at, status, anchor_profile, is_retroactive
        FROM source_ingestion_run
        WHERE started_at >= %s AND started_at < %s AND feed_name IN ('vehicle_positions', 'trip_updates', 'alerts')
        ORDER BY id
    """, window).fetchall()
    ids = [run["id"] for run in runs]
    rows = {"source_ingestion_run": len(ids)}
    for table in OBSERVATIONS:
        distinct = ", count(DISTINCT source_vehicle_id) AS vehicles" if table == OBSERVATIONS[0] else ""
        counts = conn.execute(
            f"SELECT count(*) AS rows{distinct} FROM {table} WHERE ingestion_run_id = ANY(%s::bigint[])",
            (ids,),
        ).fetchone()
        rows[table] = counts["rows"]
        if table == OBSERVATIONS[0]:
            vehicles = counts["vehicles"]
    quality = conn.execute("""
        SELECT flag, count(*) AS rows FROM data_quality_event
        WHERE occurred_at >= %s AND occurred_at < %s GROUP BY flag ORDER BY flag
    """, window).fetchall()
    rows["data_quality_event"] = sum(flag["rows"] for flag in quality)
    return runs, rows, vehicles, {flag["flag"]: flag["rows"] for flag in quality}


def build_manifest(metadata, session, runs, rows, vehicles, flags, errors, unexpected):
    start = datetime.fromisoformat(session["started_at_utc"])
    end = datetime.fromisoformat(session["finished_at_utc"])
    measured = summarize(runs, start, end, metadata["profile"]["anchor_profile"], unexpected)
    profiles = measured.pop("run_profiles")
    return {
        "manifest_version": 1,
        **metadata,
        "session": session,
        "period": {
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "start_europe_madrid": start.astimezone(MADRID).isoformat(),
            "end_europe_madrid": end.astimezone(MADRID).isoformat(),
            "duration_seconds": (end - start).total_seconds(),
        },
        **measured,
        "errors_by_type": dict(errors),
        "hot_rows": rows,
        "distinct_vehicles": vehicles,
        "quality": {"flags": flags, "run_profiles": profiles},
    }


def write_manifest(directory):
    import psycopg
    from psycopg.rows import dict_row

    metadata = json.loads((directory / "metadata.json").read_text())
    session = json.loads((directory / "session.json").read_text())
    start = datetime.fromisoformat(session["started_at_utc"])
    end = datetime.fromisoformat(session["finished_at_utc"])
    errors, unexpected = log_counts(directory / "collector.log")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        measured = collect(conn, start, end)
    manifest = build_manifest(metadata, session, *measured, errors, unexpected)
    write_json(directory / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    write_manifest(parser.parse_args().directory)
