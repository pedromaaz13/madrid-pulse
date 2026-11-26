"""Re-evaluate the MP-036 full-dump prefix cohort alongside the segmented replay."""

import argparse
import json
from collections import Counter
from itertools import groupby
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from apps.api import db
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from apps.api.snapshot import coverage_for_trip
from packages.database import require_disposable_database
from packages.movement.profile import anchor_profile

from .mp038_trace import check_target, memoized_projections
from .replay import sha


def sample_episode(rows, engine, network, config):
    positions = [(row, db._row_to_observed(row).position) for row in rows]
    schedule = engine.trip_schedule(rows[0]["source_trip_id"])
    depth = getattr(config, "anchor_history_depth", None)
    for index, (row, latest) in enumerate(positions):
        at = row["visible_at"]
        history = [pos for raw, pos in positions[:index] if raw["visible_at"] <= at]
        kwargs = (
            {}
            if depth is None
            else {
                "earlier": history[-(depth - 1) : -1][::-1],
                "history_truncated": len(history) + 1 > depth,
            }
        )
        movement = engine.position(
            trip_id=latest.source_trip_id,
            service_date=network.service_date_resolver(at).for_trip(
                latest.source_trip_id
            ),
            calculated_at=at,
            latest=latest,
            previous=history[-1] if history else None,
            **kwargs,
        )
        match = engine.map_match(latest)
        yield {
            "id": row["id"],
            "vehicle": row["source_vehicle_id"],
            "trip": row["source_trip_id"],
            "at": latest.observed_at,
            "visible_at": at,
            "xy": [latest.latitude, latest.longitude],
            "episode": rows[0]["id"],
            "on_track": match is not None
            and match.distance_from_track_m <= config.thresholds.off_track_distance_m,
            "gps_m": schedule.directed_progress(match.physical_arc_m)
            if match
            else None,
            "accepted": (movement.anchor_payload_hash, movement.observed_at)
            == (latest.payload_hash, latest.observed_at),
            "anchor_at": movement.observed_at,
            "anchor_m": movement.anchor_progress_m,
            "reacquired": any(
                a.flag == "anchor_reacquired" for a in movement.anomalies
            ),
        }


def samples(manifest_path):
    config = ApiConfig.from_env()
    check_target(config)
    manifest = json.loads(manifest_path.read_text())
    network = load_network(config)
    if (
        network.catalog_version,
        anchor_profile(
            network.gtfs_version, network.corridor_catalog, config.thresholds
        ),
    ) != (manifest["catalog_version"], manifest["profile"]["anchor_profile"]):
        raise ValueError("Catálogo o perfil distinto al de captura")
    with (
        memoized_projections(),
        psycopg.connect(
            config.database_dsn,
            autocommit=True,
            options="-c default_transaction_read_only=on",
        ) as conn,
    ):
        require_disposable_database(conn)
        conn.row_factory = dict_row
        rows = conn.execute("""
            SELECT v.*, greatest(v.observed_at, r.started_at) AS visible_at
            FROM public.vehicle_position_observation v JOIN public.source_ingestion_run r
              ON r.id=v.ingestion_run_id
            ORDER BY v.source_vehicle_id, v.observed_at, v.id
        """)
        result = []
        for _, series in groupby(rows, key=lambda row: row["source_vehicle_id"]):
            for trip, episode in groupby(series, key=lambda row: row["source_trip_id"]):
                route = network.topology.resolve_trip_route_id(trip)
                coverage = coverage_for_trip(network, trip, route)
                engine = network.engine_for(coverage) if coverage else None
                if engine is not None:
                    result.extend(
                        sample_episode(list(episode), engine, network, config)
                    )
    return {"manifest_sha256": sha(manifest_path), "rows": result}


def frozen_runs(baseline, correction):
    old = {row["id"]: row for row in baseline}
    new = {row["id"]: row for row in correction}
    if old.keys() != new.keys():
        raise ValueError("Poblaciones distintas en los prefijos")
    result = {}
    for name, cohort in (("baseline", baseline), ("correction", correction)):
        counts = Counter(
            rows=len(cohort), positioned=sum(r["gps_m"] is not None for r in cohort)
        )
        counts["accepted"] = sum(r["accepted"] for r in cohort)
        counts["reacquired"] = sum(r["reacquired"] for r in cohort)
        runs = []
        for _, episode in groupby(cohort, key=lambda row: row["episode"]):
            on_track = (row for row in episode if row["on_track"])
            groups = [
                list(g) for _, g in groupby(on_track, key=lambda row: row["accepted"])
            ]
            for index, group in enumerate(groups):
                first, last = group[0], group[-1]
                if first["accepted"] or len(group) < 2 or first["anchor_m"] is None:
                    continue
                counts["on_track_rejection_runs"] += 1
                if any(row["xy"] != first["xy"] for row in group):
                    continue
                following = groups[index + 1][0] if index + 1 < len(groups) else None
                near = (
                    (
                        abs(following["gps_m"] - first["anchor_m"])
                        < abs(following["gps_m"] - last["gps_m"])
                    )
                    if following
                    else None
                )
                ids = [row["id"] for row in group]
                runs.append(
                    {
                        "vehicle": first["vehicle"],
                        "trip": first["trip"],
                        "n": len(group),
                        "then_near_original_anchor": near,
                        "baseline": [old[i] for i in ids],
                        "correction": [new[i] for i in ids],
                    }
                )
        result[name] = {
            "counts": counts,
            "identical": len(runs),
            "runs": runs,
            "then_near_original_anchor": sum(
                run["then_near_original_anchor"] is True for run in runs
            ),
            "without_next_accepted": sum(
                run["then_near_original_anchor"] is None for run in runs
            ),
            "reacquired_in_baseline": sum(
                any(row["reacquired"] for row in run["baseline"]) for run in runs
            ),
            "reacquired_in_correction": sum(
                any(row["reacquired"] for row in run["correction"]) for run in runs
            ),
            "events": [row for row in cohort if row["reacquired"]],
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    if len(args.paths) == 1:
        output = samples(*args.paths)
    elif len(args.paths) == 2:
        old, new = (json.loads(path.read_text()) for path in args.paths)
        if old["manifest_sha256"] != new["manifest_sha256"]:
            raise ValueError("Manifiestos distintos")
        output = frozen_runs(old["rows"], new["rows"])
    else:
        parser.error("Indica el manifiesto para trazar o dos trazas para comparar")
    print(
        json.dumps(
            output, sort_keys=True, default=lambda d: d.isoformat(), allow_nan=False
        )
    )


if __name__ == "__main__":
    main()
