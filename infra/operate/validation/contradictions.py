"""Comparación fuera de producción, sobre el mismo replay segmentado de MP-025b."""

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from itertools import pairwise
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

import psycopg

from apps.api import snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from packages.database import (
    SHARED_DEV_PORT,
    database_settings_from_env,
    require_disposable_database,
)
from packages.geo import haversine_m
from packages.movement import rendering
from packages.movement.profile import anchor_profile

from . import replay
from .metrics import (
    distribution,
    exclusion,
    first_departure_frame,
    movement_opportunity,
)
from .segments import windows

POLICIES = ("control", "sin_r4", "r4_r8", "r4_dos_gps", "parada_previa", "gps_previo")
SAME_FIX_M = 1  # Estrato de MP-025b, no se usa para decidir.
JUMP_M = 200  # Umbral descriptivo de MP-025b.
SHARED_VEHICLES = 3  # Estrato descriptivo de coordenadas compartidas.


def alternatives(envelope, inputs):
    """Usa el constructor real para R5/R8. Cambia solo la decisión experimental."""
    plans = dict.fromkeys(POLICIES, envelope)
    reason = envelope.hold_reason
    status = inputs.get("status")
    if reason != "operator_incoming_at" and not (
        status == "STOPPED_AT" and envelope.coherent is False and envelope.speed_mps > 0
    ):
        return plans
    radius = inputs["thresholds"].stop_zone_radius_m
    stops = [s for s in inputs["schedule"].stops if s.stop_id == inputs["stop_id"]]
    anchor = inputs["anchor_progress_m"]
    declared = min(
        stops, key=lambda s: (abs(s.progress_m - anchor), s.stop_sequence), default=None
    )
    prior = inputs.get("previous_anchor")
    age = (inputs["anchor_at"] - prior.observed_at).total_seconds() if prior else None
    fresh = age is not None and 0 < age <= inputs["thresholds"].stale_after_s

    if reason == "operator_incoming_at":
        # Invariante de R4, comprobado antes de formar los contrafactuales.
        if declared is None or abs(declared.progress_m - anchor) > radius:
            raise ValueError("R4 sin confirmación del GPS efectivo")
        plans["sin_r4"] = ENVELOPE(**(inputs | {"status": "IN_TRANSIT_TO"}))
        plans["r4_r8"] = ENVELOPE(**(inputs | {"status": None}))
        if fresh and abs(declared.progress_m - prior.progress_m) > radius:
            plans["r4_dos_gps"] = plans["r4_r8"]
    elif (
        len(stops) == 1
        and fresh
        and abs(declared.progress_m - prior.progress_m) <= radius
    ):
        plans["parada_previa"] = replace(
            envelope,
            speed_mps=0,
            max_progress_m=envelope.progress_m_at_reference,
            dwell_until=None,
            hold_reason="incoherent_stop_prior_gps",
            cap_stop_id=None,
            cap_kind=None,
            cap_reached_at=None,
            dwell_basis=None,
            envelope_id=None,
        )
        plans["gps_previo"] = replace(
            plans["parada_previa"],
            progress_m_at_reference=prior.progress_m,
            max_progress_m=prior.progress_m,
        )
    return plans


ENVELOPE = rendering._envelope


@dataclass(frozen=True)
class Frame:
    at: datetime
    trip: str
    day: str
    stamp: datetime | None
    confirmed: float | None
    geometry: str | None
    shown: dict[str, float | None]
    method: str
    flags: tuple[str, ...]
    effective_status: str | None
    effective_stop: str | None


class Trace:
    """Instrumenta las llamadas de MP-025b, sin modificar sus resultados."""

    def __init__(self):
        self.groups = defaultdict(list)
        self.frames = defaultdict(list)
        self.plans = {}
        self.own_plans = {}
        self.indices = {}
        self.raw_details = {}
        self.segment_frames = []

    def envelope(self, **inputs):
        control = ENVELOPE(**inputs)
        identity = inputs.get("identity", ())
        if len(identity) >= 3:
            key = (identity[2], inputs["anchor_at"])
            self.plans[key] = alternatives(control, inputs)
        return control

    def snapshot(self, *args, **kwargs):
        self.plans.clear()
        result = snapshot.build_snapshot(*args, **kwargs)
        at = args[3]
        self.segment_frames.append(at)
        for v in result.vehicles:
            r = v.rendered
            plans = self.plans.get((v.vehicle_id, r.anchor_observed_at))
            shown = dict.fromkeys(
                POLICIES, r.progress_m if r.geometry_version else None
            )
            if (
                plans
                and r.geometry_version
                and r.rendering_method
                in ("anchor", "extrapolated_from_last_anchor", "stale_frozen")
            ):
                for name, plan in plans.items():
                    if plan != plans["control"]:
                        shown[name] = plan.progress_at(
                            min(
                                at,
                                plan.reference_at + timedelta(seconds=plan.horizon_s),
                            )
                        )
            frame = Frame(
                at,
                v.trip_id,
                v.service_date,
                r.anchor_observed_at,
                r.last_confirmed_progress_m,
                r.geometry_version,
                shown,
                r.rendering_method,
                tuple(v.quality.flags),
                r.stop_state.operator_status if r.stop_state else None,
                r.stop_state.operator_stop_id if r.stop_state else None,
            )
            self.frames[v.vehicle_id].append(frame)
            self.indices[v.vehicle_id, at] = len(self.frames[v.vehicle_id]) - 1
            self.raw_details[v.vehicle_id, at] = (
                v.raw.payload_hash,
                v.map_matched.distance_from_raw_m if v.map_matched else None,
            )
        return result

    def identify(self, a, v, network, limits):
        replay_identify(a, v, network, limits)
        self.groups[a.vehicle].append(a)
        if a.plan is not None:
            plans = self.plans.get((a.vehicle, a.observed))
            if plans is None or plans["control"].envelope_id != a.plan.envelope_id:
                raise ValueError("Envolvente efectiva sin correspondencia en el arnés")
            self.own_plans[id(a)] = plans

    def finish_segment(self, horizon):
        anchors, pairs, excluded = [], [], Counter()
        for vid, group in sorted(self.groups.items()):
            group.sort(key=lambda a: a.observed)
            frames = self.frames[vid]
            streaks = coordinate_streaks(group)
            for i, a in enumerate(group):
                if a.plan:
                    following = group[i + 1] if i + 1 < len(group) else None
                    prior = group[i - 1] if i else None
                    anchors.append(anchor_row(self, a, prior, following, frames))
            for a, b in pairwise(group):
                reason = exclusion(a, b, horizon)
                if reason:
                    excluded[reason] += 1
                else:
                    pairs.append(pair_row(self, a, b, frames, streaks[id(a)]))
        return anchors, pairs, excluded


replay_identify = replay.identify


def coordinate_streaks(group):
    """Tiempo desde la primera muestra idéntica consecutiva en el segmento."""
    streaks = {}
    previous = None
    for a in group:
        if (
            previous is None
            or a.trip != previous.trip
            or (a.day and previous.day and a.day != previous.day)
            or a.raw_xy is None
            or a.raw_xy != previous.raw_xy
        ):
            start = a.observed
        streaks[id(a)] = (a.observed - start).total_seconds()
        previous = a
    return streaks


def raw_row(trace, a):
    index = trace.indices.get((a.vehicle, a.visible))
    frame = (
        trace.frames[a.vehicle][index] if index is not None and a.matched_row else None
    )
    raw = trace.raw_details.get((a.vehicle, a.visible))
    return {
        "gps_at": a.observed,
        "visible_at": a.visible,
        "run": a.run,
        "status": a.status,
        "stop": a.stop,
        "trip": a.trip,
        "day": a.day,
        "raw_xy": a.raw_xy,
        "payload_hash": a.digest,
        "projected_m": a.projected,
        "declared_m": a.declared_progress,
        "matched_row": a.matched_row,
        "previous_anchor_used": a.previous_anchor_used,
        "off_track_m": raw[1] if frame and raw[0] == a.digest else None,
        "frame": asdict(frame) if frame else None,
    }


def anchor_row(trace, a, prior, b, frames):
    plans = trace.own_plans[id(a)]
    start_index = trace.indices[a.vehicle, a.visible]
    end = trace.segment_frames[-1]
    replaced = False
    for frame in frames[start_index + 1 :]:
        if (frame.trip, frame.day, frame.stamp) != (a.trip, a.day, a.observed):
            end, replaced = frame.at, True
            break
    interval = {"from": a.visible, "until": end, "replacement_seen": replaced}
    values = {}
    for name, p in plans.items():
        initial = p.progress_m_at_reference
        valid_until = p.reference_at + timedelta(seconds=p.horizon_s)
        last = min(end, valid_until)
        values[name] = {
            "offset_from_effective_gps_m": initial
            - plans["control"].progress_m_at_reference,
            "speed_mps": p.speed_mps,
            "hold": p.hold_reason,
            "dwell_basis": p.dwell_basis,
            "moving_from": p.moving_from,
            "cap_reached_at": p.cap_reached_at,
            "advance_horizon_m": p.progress_at(valid_until) - initial,
            "advance_before_replacement_m": p.progress_at(last) - initial,
            "advance_after_first_frame_m": p.progress_at(last)
            - p.progress_at(min(a.visible, valid_until)),
            "moving_s_before_replacement": max(
                0,
                (
                    min(last, p.cap_reached_at or valid_until) - p.moving_from
                ).total_seconds(),
            )
            if p.speed_mps > 0
            else 0,
            "moving_s_after_first_frame": max(
                0,
                (
                    min(last, p.cap_reached_at or valid_until)
                    - max(a.visible, p.moving_from)
                ).total_seconds(),
            )
            if p.speed_mps > 0
            else 0,
            "effective_duration_s": (end - a.visible).total_seconds(),
        }
    return {
        "vehicle": a.vehicle,
        "a": raw_row(trace, a),
        "prior": raw_row(trace, prior) if prior is not None else None,
        "next": raw_row(trace, b) if b is not None else None,
        "class": a.classification,
        "coherent": a.coherent,
        "interval": interval,
        "policies": values,
    }


def handoff(a, b, before, after, plan, policy):
    """Diferencia firmada al cambiar la observación efectiva, en el mismo instante."""
    if (
        before is None
        or before.stamp != a.observed
        or after.stamp != b.observed
        or not after.geometry
        or before.geometry != after.geometry
        or after.shown[policy] is None
        or (before.trip, before.day) != (after.trip, after.day)
    ):
        return None
    end = plan.reference_at + timedelta(seconds=plan.horizon_s)
    return after.shown[policy] - plan.progress_at(min(b.visible, end))


def pair_row(trace, a, b, frames, frozen_a_s):
    plans = trace.own_plans[id(a)]
    index = trace.indices[b.vehicle, b.visible]
    after = frames[index]
    before = frames[index - 1] if index > 0 else None
    displacement = b.projected - a.projected
    opportunity = movement_opportunity(a.status, displacement)
    values = {}
    for name, plan in plans.items():
        predicted = plan.progress_at(b.observed)
        retained = opportunity is not None and predicted == plan.progress_m_at_reference
        release = None
        if retained:
            release = first_departure_frame(
                (
                    (f.at, f.trip, f.day, f.stamp, f.confirmed, f.shown[name])
                    for f in frames[index:]
                ),
                a,
                b,
            )
        values[name] = {
            "advance_m": predicted - plan.progress_m_at_reference,
            "gps_error_m": abs(b.projected - predicted),
            "handoff_m": handoff(a, b, before, after, plan, name),
            "retained": retained,
            "latency_s": (release - b.observed).total_seconds() if release else None,
            "release_at": release,
        }
    return {
        "vehicle": a.vehicle,
        "a": raw_row(trace, a),
        "b": raw_row(trace, b),
        "class": a.classification,
        "opportunity": opportunity,
        "interval_s": (b.observed - a.observed).total_seconds(),
        "frozen_a_s": frozen_a_s,
        "observed_delta_m": displacement,
        "policies": values,
    }


def summarize(anchors, pairs, name):
    rows = [p["policies"][name] for p in pairs]
    retained = [r for r in rows if r["retained"]]
    latency = [r["latency_s"] for r in retained if r["latency_s"] is not None]
    handoffs = [r["handoff_m"] for r in rows if r["handoff_m"] is not None]
    gps = [r["gps_error_m"] for r in rows]
    still = [
        p
        for p in pairs
        if abs(p["observed_delta_m"]) < SAME_FIX_M
        and p["a"]["raw_xy"] == p["b"]["raw_xy"]
    ]
    return {
        "anchors": len(anchors),
        "changed_plans": sum(
            a["policies"][name] != a["policies"]["control"] for a in anchors
        ),
        "positive_plans": sum(a["policies"][name]["speed_mps"] > 0 for a in anchors),
        "advanced_before_replacement": sum(
            a["policies"][name]["advance_before_replacement_m"] > 0 for a in anchors
        ),
        "opportunities": sum(p["opportunity"] is not None for p in pairs),
        "retained": len(retained),
        "retained_previous_anchor_used": sum(
            p["b"]["previous_anchor_used"] and p["policies"][name]["retained"]
            for p in pairs
        ),
        "latency_s": distribution(latency),
        "latency_unresolved": len(retained) - len(latency),
        "gps_error_m": distribution(gps),
        "gps_error_gt_200": sum(x > JUMP_M for x in gps),
        "handoff_abs_m": distribution(map(abs, handoffs)),
        "handoff_gt_200": sum(abs(x) > JUMP_M for x in handoffs),
        "handoff_backwards": sum(x < 0 for x in handoffs),
        "identical_gps_pairs": len(still),
        "advance_on_identical_gps": sum(
            p["policies"][name]["advance_m"] > 0 for p in still
        ),
        "advance_on_identical_gps_m": distribution(
            p["policies"][name]["advance_m"] for p in still
        ),
    }


def cohorts(anchors, pairs):
    stopped = [
        a
        for a in anchors
        if a["a"]["status"] == "STOPPED_AT"
        and a["coherent"] is False
        and a["policies"]["control"]["speed_mps"] > 0
    ]
    m7 = [
        p
        for p in pairs
        if p["opportunity"] == "M7" and p["policies"]["control"]["retained"]
    ]
    return stopped, m7


def m7_strata(pairs, top_speed_kmh):
    """Cruza velocidad aparente y racha previa sobre toda la población H1 de M7."""
    strata = {
        f"{speed}/{streak}": {
            "todos_h1": [],
            "oportunidades_m7": [],
            "retenciones_control": [],
        }
        for speed in ("plausible", "sobre_tope")
        for streak in ("sin_racha", "con_racha")
    }
    for pair in pairs:
        if pair["a"]["status"] not in ("INCOMING_AT", "IN_TRANSIT_TO"):
            continue
        speed = abs(pair["observed_delta_m"]) * 3.6 / pair["interval_s"]
        speed_stratum = "plausible" if speed <= top_speed_kmh else "sobre_tope"
        streak = "con_racha" if pair["frozen_a_s"] > 0 else "sin_racha"
        populations = strata[f"{speed_stratum}/{streak}"]
        populations["todos_h1"].append(pair)
        if pair["opportunity"] == "M7":
            populations["oportunidades_m7"].append(pair)
            if pair["policies"]["control"]["retained"]:
                populations["retenciones_control"].append(pair)
    for prefix, axis in (
        ("plausible", 0),
        ("sobre_tope", 0),
        ("sin_racha", 1),
        ("con_racha", 1),
    ):
        strata[prefix] = {
            population: [
                pair
                for key, groups in strata.items()
                if "/" in key and key.split("/")[axis] == prefix
                for pair in groups[population]
            ]
            for population in ("todos_h1", "oportunidades_m7", "retenciones_control")
        }
    return strata


def coordinate_counts(conn, period):
    start, end = (datetime.fromisoformat(period[k]) for k in ("start_utc", "end_utc"))
    rows = conn.execute(
        """
        WITH fixes AS (
            SELECT latitude, longitude, source_vehicle_id,
                   (r.started_at >= %s AND r.started_at < %s) AS in_session
            FROM public.vehicle_position_observation v
            JOIN public.source_ingestion_run r ON r.id = v.ingestion_run_id
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        )
        SELECT latitude, longitude, count(*), count(DISTINCT source_vehicle_id),
               count(*) FILTER (WHERE in_session),
               count(DISTINCT source_vehicle_id) FILTER (WHERE in_session)
        FROM fixes GROUP BY latitude, longitude ORDER BY latitude, longitude
        """,
        (start, end),
    ).fetchall()
    counts, summary = {}, {}
    for scope, n_col, vehicles_col in (("dump", 2, 3), ("session", 4, 5)):
        counts[scope] = {(r[0], r[1]): r[vehicles_col] for r in rows if r[n_col]}
        summary[scope] = {
            "coordinates": len(counts[scope]),
            "positioned_rows": sum(r[n_col] for r in rows),
            "shared_rows": sum(
                r[n_col] for r in rows if r[vehicles_col] >= SHARED_VEHICLES
            ),
        }
    return counts, summary


def nearest_stops(stopped, stops):
    """Contexto estático para A. La proximidad espacial no identifica el tren."""
    result = {}
    for case in stopped:
        a = case["a"]
        if a["stop"] not in result:
            result[a["stop"]] = {}
        lat_lon = a["raw_xy"]
        if lat_lon not in result[a["stop"]]:
            distance, stop_id, name = min(
                (haversine_m(*lat_lon, s.latitude, s.longitude), s.stop_id, s.name)
                for s in stops
            )
            result[a["stop"]][lat_lon] = {
                "raw_xy": lat_lon,
                "gtfs_stop": stop_id,
                "name": name,
                "distance_m": distance,
                "anchors": 0,
            }
        result[a["stop"]][lat_lon]["anchors"] += 1
    return {stop: list(points.values()) for stop, points in result.items()}


def stopped_deltas(stopped, pairs):
    starts, ends = {}, {}
    for p in pairs:
        for index, edge in ((starts, "a"), (ends, "b")):
            a = p[edge]
            index[p["vehicle"], a["run"], a["gps_at"]] = p
    changed = []
    for case in stopped:
        if case["policies"]["parada_previa"] == case["policies"]["control"]:
            continue
        a = case["a"]
        key = (case["vehicle"], a["run"], a["gps_at"])
        changed.append(
            {
                "vehicle": case["vehicle"],
                "gps_at": a["gps_at"],
                "arrival": ends.get(key),
                "departure": starts.get(key),
            }
        )
    return {
        "changed": changed,
        "prior_same_raw_xy": sum(
            c["prior"] is not None and c["prior"]["raw_xy"] == c["a"]["raw_xy"]
            for c in stopped
        ),
        "advance_before_replacement_total_m": {
            name: sum(
                c["policies"][name]["advance_before_replacement_m"] for c in stopped
            )
            for name in ("control", "parada_previa", "gps_previo")
        },
    }


def compare(conn, network, config, manifest):
    coordinates, quantization = coordinate_counts(conn, manifest["period"])
    traces = []

    def analyze_part(*args):
        trace = Trace()
        with (
            patch.object(rendering, "_envelope", trace.envelope),
            patch.object(replay, "build_snapshot", trace.snapshot),
            patch.object(replay, "identify", trace.identify),
        ):
            result = original_analyze(*args)
        traces.append(trace.finish_segment(config.thresholds.stale_after_s))
        return result

    original_analyze = replay.analyze
    with patch.object(replay, "analyze", analyze_part):
        spans = windows(manifest)
        baseline = replay.analyze_segments(conn, network, config, manifest, spans)
    anchors = [row for a, _, _ in traces for row in a]
    pairs = [row for _, p, _ in traces for row in p]
    excluded = sum((e for _, _, e in traces), Counter())
    stopped, m7 = cohorts(anchors, pairs)
    control = summarize(anchors, pairs, "control")
    if (len(stopped), len(m7), control["gps_error_m"], excluded) != (
        len(baseline["stopped_adverse"]),
        sum(baseline["m7_retenciones"].values()),
        baseline["jumps"],
        baseline["excluded"],
    ):
        raise ValueError("El control no concuerda con MP-025b")
    departures = [p for p in pairs if p["a"]["status"] == "STOPPED_AT"]
    stopped_control = summarize([], departures, "control")
    if (stopped_control["retained"], stopped_control["latency_s"]) != (
        baseline["departures"]["retenida"],
        baseline["latency_s"],
    ):
        raise ValueError("La latencia de salidas del control no concuerda con MP-025b")
    summary = {}
    strata = ("STOPPED_AT", "INCOMING_AT", "IN_TRANSIT_TO")
    for policy in POLICIES:
        summary[policy] = {
            "all": summarize(anchors, pairs, policy),
            **{
                status: summarize(
                    [a for a in anchors if a["a"]["status"] == status],
                    [p for p in pairs if p["a"]["status"] == status],
                    policy,
                )
                for status in strata
            },
            "stopped_positive_control": summarize(stopped, [], policy),
            "retained_m7_control": summarize([], m7, policy),
        }
    m7_breakdown = m7_strata(pairs, config.thresholds.max_estimated_speed_kmh)
    for scope, counts in coordinates.items():
        quantization[scope]["m7_retained_a_shared"] = sum(
            counts.get(p["a"]["raw_xy"], 0) >= SHARED_VEHICLES for p in m7
        )
        quantization[scope]["m7_retained_b_shared"] = sum(
            counts.get(p["b"]["raw_xy"], 0) >= SHARED_VEHICLES for p in m7
        )
    return {
        "population": {
            key: baseline[key] for key in ("rows", "pairs", "vehicles", "frames")
        },
        "states": baseline["states"],
        "excluded": excluded,
        "summary": summary,
        "stopped_cases": stopped,
        "m7_cases": m7,
        "m7_strata": {
            key: {
                population: {
                    policy: summarize([], group, policy) for policy in POLICIES
                }
                for population, group in populations.items()
            }
            for key, populations in m7_breakdown.items()
        },
        "m7_retained_apparent_speed_mps": distribution(
            p["observed_delta_m"] / p["interval_s"] for p in m7
        ),
        "m7_retained_prior_streak_s": distribution(
            p["frozen_a_s"] for p in m7 if p["frozen_a_s"] > 0
        ),
        "quantization": quantization,
        "stopped_fixed_points": nearest_stops(stopped, network.topology.stops),
        "stopped_deltas": stopped_deltas(stopped, pairs),
        "worst": {
            policy: {
                status: {
                    metric: max(
                        (
                            p
                            for p in pairs
                            if p["a"]["status"] == status
                            and p["policies"][policy][metric] is not None
                        ),
                        key=lambda p: abs(p["policies"][policy][metric]),
                        default=None,
                    )
                    for metric in ("gps_error_m", "handoff_m", "latency_s")
                }
                for status in strata
            }
            for policy in POLICIES
        },
    }


def validate_endpoint(dsn, environment, mode, short_name):
    url = urlsplit(dsn)
    if (
        (url.hostname, environment, mode, short_name)
        != ("127.0.0.1", "replay", "replay", "")
        or url.port in (None, SHARED_DEV_PORT, 5466)
        or not url.path.removeprefix("/")
        or url.query
        or url.fragment
    ):
        raise ValueError(
            "Se requiere replay del núcleo en un PostGIS local con puerto y base explícitos"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("dump", type=Path)
    args = parser.parse_args()
    digest = replay.sha(args.dump)
    if digest != args.dump.with_suffix(".dump.sha256").read_text().split()[0]:
        raise ValueError("SHA-256 incorrecto para el volcado")
    manifest = json.loads(args.manifest.read_text())
    config = ApiConfig.from_env()
    _, environment = database_settings_from_env()
    validate_endpoint(config.database_dsn, environment, config.mode, config.short_name)
    network = load_network(config)
    profile = anchor_profile(
        network.gtfs_version, network.corridor_catalog, config.thresholds
    )
    if network.catalog_version != manifest["catalog_version"] or (
        profile != manifest["profile"]["anchor_profile"]
    ):
        raise ValueError("Catálogo o perfil distinto al de captura")
    with psycopg.connect(
        config.database_dsn,
        autocommit=True,
        options="-c default_transaction_read_only=on",
    ) as conn:
        require_disposable_database(conn)
        result = compare(conn, network, config, manifest)
    result["inputs"] = {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "dump_sha256": digest,
        "manifest_sha256": replay.sha(args.manifest),
        "gtfs_sha256": replay.sha(config.gtfs_fixture_dir),
        "profile": profile,
    }
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
