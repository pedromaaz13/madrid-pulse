"""python -m infra.operate.validation.replay MANIFEST DUMP > resultado.json"""

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from apps.api.snapshot import build_snapshot, build_station_board, coverage_for_trip
from packages.database import require_disposable_database
from packages.movement.profile import anchor_profile
from packages.movement.rendering import ProgressEnvelope
from packages.movement.schedule import service_day_instant

from .metrics import Anchor, distribution, exclusion, gate


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identify(a, v, network, limits):
    if not v or v.raw.payload_hash != a.digest or v.raw.gps_observed_at != a.observed:
        return
    a.matched_row = True
    a.day = v.service_date
    coverage = coverage_for_trip(network, v.trip_id, v.route_id)
    engine = network.engine_for(coverage) if coverage else None
    a.corridor = engine is not None
    m = v.map_matched
    if not engine or not m or m.distance_from_raw_m > limits.off_track_distance_m:
        return
    schedule = engine.trip_schedule(a.trip)
    a.projected = schedule.directed_progress(m.progress_m)
    r = v.rendered
    if r.anchor_observed_at != a.observed or r.coordinate_space != "map_matched":
        return
    if r.progress_envelope:
        a.plan = ProgressEnvelope(**r.progress_envelope.model_dump())
    if r.stop_state:
        a.coherent = r.stop_state.coherent
    stops = schedule.stops
    declared = min(
        (s for s in stops if s.stop_id == a.stop),
        key=lambda s: (abs(s.progress_m - a.projected), s.stop_sequence),
        default=None,
    )
    if not declared:
        return
    gap = declared.progress_m - a.projected
    radius = limits.stop_zone_radius_m
    if a.status == "STOPPED_AT":
        if abs(gap) > radius:
            a.classification = "fuera_zona_declarada"
        elif declared == stops[0]:
            departure = service_day_instant(
                date.fromisoformat(a.day), declared.departure_s
            )
            a.classification = (
                "pre_salida"
                if a.observed < departure
                else "origen_tras_salida_programada"
            )
        else:
            a.classification = "terminal" if declared == stops[-1] else "intermedia"
    elif gap < -radius:
        a.classification = "pasada_mas_1km" if gap < -1000 else "pasada"
    elif abs(gap) <= radius:
        a.classification = "en_zona"
    else:
        following = next(
            (s for s in stops if s.progress_m > a.projected + radius), None
        )
        a.classification = "siguiente" if declared == following else "posterior"


def analyze(conn, network, config, manifest):
    start, end = (
        datetime.fromisoformat(manifest["period"][k]) for k in ("start_utc", "end_utc")
    )
    limits = config.thresholds
    records = conn.execute(
        """
        SELECT source_vehicle_id,source_trip_id,observed_at,greatest(observed_at,started_at),
               current_status,current_stop_id,v.payload_hash,ingestion_run_id
        FROM vehicle_position_observation v JOIN source_ingestion_run r ON r.id=v.ingestion_run_id
        WHERE started_at >= %s AND started_at < %s ORDER BY source_vehicle_id,observed_at,v.id
    """,
        (start, end),
    ).fetchall()
    groups = defaultdict(list)
    arrivals = defaultdict(list)
    for row in records:
        a = Anchor(*row)
        groups[a.vehicle].append(a)
        arrivals[a.visible].append(a)
    if (len(records), len(groups)) != (
        manifest["hot_rows"]["vehicle_position_observation"],
        manifest["distinct_vehicles"],
    ):
        raise ValueError("La restauración no concuerda con la población del manifiesto")
    ticks = {end} | {t for t in arrivals if t <= end}
    stale = timedelta(seconds=limits.stale_after_s)
    for anchors in groups.values():
        for i, a in enumerate(anchors):
            expiry = a.observed + stale
            successor = anchors[i + 1].visible if i + 1 < len(anchors) else end
            after = expiry + timedelta(milliseconds=1)
            if a.visible <= expiry and after < min(successor, end):
                ticks.update((expiry, after))
    cancels = conn.execute(
        """
        SELECT u.source_trip_id,greatest(u.observed_at,r.started_at)
        FROM trip_update_observation u JOIN source_ingestion_run r ON r.id=u.ingestion_run_id
        WHERE r.started_at >= %s AND r.started_at < %s AND u.schedule_relationship='CANCELED'
    """,
        (start, end),
    ).fetchall()
    cancel_times = defaultdict(list)
    for trip, at in cancels:
        cancel_times[at].append(trip)
        if at <= end:
            ticks.add(at)
    provenance, cancellations, board_counts = Counter(), Counter(), Counter()
    cohort = {a.digest for anchors in groups.values() for a in anchors}
    visible_progress = {}
    recovery, rewinds = [], []
    prior = {}
    for at in sorted(ticks):
        vehicles = {
            v.vehicle_id: v
            for v in build_snapshot(conn, network, config, at, display_lag_s=0).vehicles
        }
        for trip in cancel_times[at]:
            entries = [v for v in vehicles.values() if v.trip_id == trip]
            key = (
                "sin_vehiculo"
                if not entries
                else "señalizada"
                if all(v.schedule_relationship == "CANCELED" for v in entries)
                else "sin_señal"
            )
            cancellations[key] += 1
            calls = network.topology.stop_times_for_trip(trip)
            entries = []
            for station in sorted({call.stop_id for call in calls}):
                board = build_station_board(conn, network, config, station, at)
                entries.extend(e for e in board.entries if e.trip_id == trip)
            board_counts["llamadas_visibles"] += len(entries)
            board_counts["llamadas_señalizadas"] += sum(
                e.schedule_relationship == "CANCELED" for e in entries
            )
            board_counts["filas_sin_llamada_visible"] += not entries
        for a in arrivals[at]:
            vehicle = vehicles.get(a.vehicle)
            identify(a, vehicle, network, limits)
            if a.matched_row and vehicle.rendered.coordinate_space == "map_matched":
                visible_progress[a.digest] = vehicle.rendered.progress_m
        for vid, v in vehicles.items():
            if v.raw.payload_hash not in cohort:
                continue
            r = v.rendered
            env = r.progress_envelope
            state = r.stop_state
            provenance[
                "/".join(
                    str(x)
                    for x in (
                        r.rendering_method,
                        r.coordinate_space,
                        env.hold_reason if env else None,
                        r.frozen_basis,
                        state.operator_status if state else None,
                    )
                )
            ] += 1
            old = prior.get(vid)
            if old and old.trip_id == v.trip_id and old.service_date == v.service_date:
                p = old.rendered
                if (
                    p.progress_m is not None
                    and r.progress_m is not None
                    and p.geometry_version == r.geometry_version
                    and r.geometry_version
                ):
                    if (
                        r.rendering_method == "stale_frozen"
                        and p.anchor_observed_at == r.anchor_observed_at
                        and p.valid_until == p.display_at
                    ):
                        rewinds.append(max(0, p.progress_m - r.progress_m))
                    if (
                        p.rendering_method == "stale_frozen"
                        and r.anchor_observed_at != p.anchor_observed_at
                    ):
                        recovery.append(abs(r.progress_m - p.progress_m))
            prior[vid] = v

    excluded, states, costs, strata = Counter(), Counter(), Counter(), defaultdict(list)
    jumps, latency, adverse = [], [], []
    unavailable = []
    intervals = []
    departure_events = []
    trips = set()
    covered = set()
    for vid, anchors in groups.items():
        for a in anchors:
            trips.add(a.trip)
            if a.corridor:
                covered.add(a.trip)
            speed = (
                "sin_plan"
                if not a.plan
                else "positiva"
                if a.plan.speed_mps > 0
                else "cero"
            )
            states[f"{a.status}/{a.classification}/{a.coherent}/{speed}"] += 1
        for a, b in pairwise(anchors):
            intervals.append((b.observed - a.observed).total_seconds())
            reason = exclusion(a, b, limits.stale_after_s)
            if reason:
                excluded[reason] += 1
                if reason == "sin_plan_del_ancla":
                    unavailable.append([vid, a.observed.isoformat(), a.status])
                continue
            forecast = a.plan.progress_at(b.observed)
            jump = abs(forecast - b.projected)
            jumps.append(jump)
            strata[f"{a.status}/{a.classification}/{a.coherent}"].append(jump)
            displacement = b.projected - a.projected
            if a.status in ("IN_TRANSIT_TO", "INCOMING_AT") and displacement >= 100:
                costs["transito_avance_100m"] += 1
                costs["transito_retenido_100m"] += (
                    forecast == a.plan.progress_m_at_reference
                )
            if jump > 200:
                adverse.append(
                    {
                        "vehicle": vid,
                        "at": b.observed.isoformat(),
                        "jump_m": jump,
                        "displacement_m": displacement,
                        "predicted_m": forecast - a.plan.progress_m_at_reference,
                        "status": a.status,
                        "hold": a.plan.hold_reason,
                        "classification": a.classification,
                        "plan_nuevo": b.plan is not None,
                    }
                )
            if a.status == "STOPPED_AT":
                costs["pares_stopped"] += 1
                if displacement > 0:
                    costs["avance_positivo"] += 1
                    if forecast == a.plan.progress_m_at_reference:
                        costs["retenida"] += 1
                        costs["retenida_100m"] += displacement >= 100
                        if b.plan and visible_progress[b.digest] != a.plan.progress_at(
                            min(b.visible, a.observed + stale)
                        ):
                            delay = (b.visible - b.observed).total_seconds()
                            latency.append(delay)
                            departure_events.append(
                                [vid, b.observed.isoformat(), delay]
                            )
                        else:
                            costs["latencia_no_evaluable"] += 1
    cycles = conn.execute(
        """SELECT count(*), count(*) FILTER (WHERE EXISTS
      (SELECT 1 FROM vehicle_position_observation v WHERE v.ingestion_run_id=r.id))
      FROM source_ingestion_run r WHERE feed_name='vehicle_positions' AND started_at >= %s AND started_at < %s""",
        (start, end),
    ).fetchone()
    return {
        "rows": len(records),
        "vehicles": len(groups),
        "trips": len(trips),
        "covered_trips": len(covered),
        "covered_vehicles": sum(
            any(a.corridor for a in group) for group in groups.values()
        ),
        "gps_cycles": cycles,
        "feeds": manifest["coverage_by_feed"],
        "states": states,
        "frames": len(ticks),
        "provenance": provenance,
        "pairs": len(records) - len(groups),
        "excluded": excluded,
        "jumps": distribution(jumps),
        "gate": gate(distribution(jumps)),
        "adverse": adverse,
        "jumps_by_state": {k: distribution(v) for k, v in strata.items()},
        "departures": costs,
        "latency_s": distribution(latency),
        "frozen_rewind_m": distribution(rewinds),
        "recovery_m": distribution(recovery),
        "canceled_rows": len(cancels),
        "canceled": cancellations,
        "board": board_counts,
        "unavailable": unavailable,
        "intervals_s": distribution(intervals),
        "departure_events": departure_events,
    }


def main():
    manifest_path, dump = map(Path, sys.argv[1:])
    manifest = json.loads(manifest_path.read_text())
    config = ApiConfig.from_env()
    url = urlsplit(config.database_dsn)
    if (url.hostname, url.port, url.path, config.mode, config.short_name) != (
        "127.0.0.1",
        5456,
        "/mp025b",
        "replay",
        "",
    ) or url.query:
        raise ValueError("Se requiere replay local MP-025b con núcleo completo")
    network = load_network(config)
    profile = anchor_profile(
        network.gtfs_version, network.corridor_catalog, config.thresholds
    )
    if (
        network.catalog_version != manifest["catalog_version"]
        or profile != manifest["profile"]["anchor_profile"]
    ):
        raise ValueError("Catálogo o perfil distinto al de captura")
    with psycopg.connect(
        config.database_dsn,
        autocommit=True,
        options="-c default_transaction_read_only=on",
    ) as conn:
        require_disposable_database(conn)
        result = analyze(conn, network, config, manifest)
    result.update(
        head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        manifest_sha256=sha(manifest_path),
        dump_sha256=sha(dump),
        gtfs_version=network.gtfs_version,
        period=manifest["period"],
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
