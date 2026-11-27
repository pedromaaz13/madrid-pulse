"""Jornada 1. Genera trazas locales o compara las de tres revisiones."""
import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from itertools import groupby
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from urllib.parse import urlsplit


def trace(output, kind):
    from psycopg.rows import dict_row

    from apps.api import db
    from apps.api.config import ApiConfig
    from apps.api.gtfs_source import load_network
    from apps.api.snapshot import build_snapshot, coverage_for_trip
    from tests.postgres import connect_disposable_or_skip

    config = ApiConfig.from_env()
    url = urlsplit(config.database_dsn)
    if (url.hostname, url.port, url.path, config.mode, config.short_name) != (
        "127.0.0.1", 5459, "/mp036_capture", "replay", "",
    ):
        raise ValueError("Se requiere la copia desechable y el catálogo completo de la jornada 1")
    network = load_network(config)
    start = datetime.fromisoformat("2026-11-26T07:40:00+00:00")
    with connect_disposable_or_skip() as conn:
        if kind == "frames":
            frames = {}
            for tick in range(80):
                clock = start + timedelta(minutes=tick)
                began = perf_counter()
                snap = build_snapshot(conn, network, config, clock, display_lag_s=0)
                frames[clock.isoformat()] = [
                    round((perf_counter() - began) * 1000, 2),
                    {v.vehicle_id: [v.rendered.last_confirmed_at, v.rendered.rendering_method]
                     for v in snap.vehicles},
                ]
            output.write_text(json.dumps(frames, default=datetime.isoformat))
            return

        conn.row_factory = dict_row
        rows = conn.execute("""
            SELECT v.*, greatest(v.observed_at, r.started_at) AS visible_at
            FROM vehicle_position_observation v JOIN source_ingestion_run r ON r.id=v.ingestion_run_id
            ORDER BY v.source_vehicle_id, v.observed_at, v.id
        """).fetchall()
        results = []
        for vid, series in groupby(rows, key=lambda row: row["source_vehicle_id"]):
            for trip, episode in groupby(series, key=lambda row: row["source_trip_id"]):
                route = network.topology.resolve_trip_route_id(trip)
                coverage = coverage_for_trip(network, trip, route)
                engine = network.engine_for(coverage) if coverage else None
                if engine is None:
                    continue
                # Memoización local de proyecciones puras en el arnés. Se conserva
                # el motor de producción y se reconstruye cada prefijo desde cero.
                original = engine.map_match
                matches = {}

                def memoized(obs):
                    xy = obs.latitude, obs.longitude
                    if xy not in matches:
                        matches[xy] = original(obs)
                    return matches[xy]

                episode = list(episode)
                with patch.object(engine, "map_match", memoized):
                    for index, row in enumerate(episode):
                        at = row["visible_at"]
                        visible = [
                            item for item in episode[:index + 1] if item["visible_at"] <= at
                        ]
                        history = [db._row_to_observed(item).position for item in visible]
                        latest = history[-1]
                        match = engine.map_match(latest)
                        previous = history[-2] if len(history) > 1 else None
                        kwargs = {}
                        if hasattr(config, "anchor_history_depth"):
                            depth = config.anchor_history_depth
                            kwargs = dict(earlier=history[:-2][-(depth - 2):][::-1] if depth > 2 else (),
                                          history_truncated=len(history) > depth)
                        movement = engine.position(
                            trip_id=trip, service_date=network.service_date_resolver(at).for_trip(trip),
                            calculated_at=at, latest=latest, previous=previous, **kwargs,
                        )
                        results.append([
                            row["id"], vid, trip, episode[0]["id"], latest.observed_at,
                            [latest.latitude, latest.longitude],
                            match is not None and match.distance_from_track_m <= config.thresholds.off_track_distance_m,
                            movement.anchor_payload_hash == latest.payload_hash
                            and movement.observed_at == latest.observed_at,
                            movement.observed_at, movement.anchor_progress_m,
                            any(a.flag == "anchor_reacquired" for a in movement.anomalies),
                            engine.trip_schedule(trip).directed_progress(match.physical_arc_m) if match else None,
                        ])
        output.write_text(json.dumps(results, default=datetime.isoformat))


def compare(kind, paths):
    baseline, before, after = [json.loads(p.read_text()) for p in paths]
    if kind == "frames":
        for label, variant in (("pre B1", before), ("post B1", after), ("delta B1", after)):
            reference = before if label == "delta B1" else baseline
            counts, transitions = Counter(), Counter()
            max_retained = 0
            for clock, (_, base) in reference.items():
                current = variant[clock][1]
                assert base.keys() == current.keys()
                counts["total"] += len(base)
                for vid, (old, old_method) in base.items():
                    new, new_method = current[vid]
                    if old == new:
                        continue
                    counts["changed"] += 1
                    transitions[f"{old_method} → {new_method}"] += 1
                    if old is None or new is None:
                        counts["null_transition"] += 1
                    elif old > new:
                        counts["older"] += 1
                        max_retained = max(max_retained, (datetime.fromisoformat(old)
                                                           - datetime.fromisoformat(new)).total_seconds())
                    else:
                        counts["newer"] += 1
            print(label, dict(counts), "max_older_s", max_retained, dict(transitions))
        return

    base = {row[0]: row for row in baseline}
    new = {row[0]: row for row in after}
    assert base.keys() == new.keys() == {row[0] for row in before}
    for label, cohort in (("pre B1", before), ("post B1", after)):
        counts = Counter(total=len(cohort))
        counts["positioned"] = sum(r[11] is not None for r in cohort)
        counts["base_accepted_now_rejected"] = sum(base[r[0]][7] and not r[7] for r in cohort)
        counts["reacquire_events"] = sum(r[10] for r in cohort)
        for row in cohort:
            if row[10]:
                print(label, "reanclaje", row[1], row[4], row[8], round(row[9]), "m")
        for _, series in groupby(cohort, key=lambda r: r[3]):
            # Como en la revisión, las filas sin posición admisible no
            # cuentan como rechazos en vía ni terminan una racha descriptiva.
            positioned = (r for r in series if r[6])
            groups = [(accepted, list(rows)) for accepted, rows in groupby(positioned, key=lambda r: r[7])]
            for index, (accepted, rows) in enumerate(groups):
                if not accepted and len(rows) >= 2 and rows[0][9] is not None:
                    counts["streaks_on_track"] += 1
                    if len({tuple(r[5]) for r in rows}) == 1:
                        counts["identical_streaks"] += 1
                        counts["identical_streaks_with_reacquire"] += any(new[r[0]][10] for r in rows)
                        if index + 1 < len(groups):
                            end = groups[index + 1][1][0][11]
                            if abs(end - rows[0][9]) < abs(end - rows[-1][11]):
                                counts["identical_then_near_anchor"] += 1
                    if rows[0][1] in {"20414", "20418", "20752"}:
                        condensed = [(r[4][11:19], round(r[11]), r[8][11:19] if r[8] else None,
                                      new[r[0]][8][11:19] if new[r[0]][8] else None, new[r[0]][10])
                                     for r in rows]
                        print(label, rows[0][1], "GPS, m, ancla, ancla post B1, evento", condensed)
        print(label, dict(counts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("frames", "samples"))
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    if len(args.paths) == 1:
        trace(args.paths[0], args.kind)
    elif len(args.paths) == 3:
        compare(args.kind, args.paths)
    else:
        parser.error("Indica un destino para trazar o tres trazas para comparar")
