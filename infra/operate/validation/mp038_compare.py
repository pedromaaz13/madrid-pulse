"""Compare the GPS, confirmed anchor and presentation traces independently."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

from packages.movement.rendering import ProgressEnvelope

from .metrics import distribution, exclusion, gate

VARIANTS = ("baseline", "correction")
CASES = {
    "20414": ("06:16:30", "06:18:40"),
    "20418": ("06:31:30", "06:33:40"),
    "20752": ("07:43:50", "07:46:00"),
    "20231": ("06:21:29", "06:23:50"),
    "20793": ("08:46:05", "08:49:10"),
}
INPUT_KEYS = (
    "vehicle",
    "trip",
    "observed",
    "visible",
    "status",
    "stop",
    "digest",
    "run",
    "raw_xy",
)


def gps_speed(a, b, horizon):
    if a is None or b is None:
        return None, "missing_gps"
    seconds = (b.observed - a.observed).total_seconds()
    if seconds == 0:
        return None, "zero_gps_interval"
    if not 0 < seconds <= horizon:
        return None, "outside_gps_interval"
    if (a.trip, a.day) != (b.trip, b.day) or a.projected is None or b.projected is None:
        return None, "incomparable_gps"
    return abs(b.projected - a.projected) * 3.6 / seconds, None


def labels(state, a, b, frozen, speed_limit, horizon):
    speed, _ = gps_speed(a, b, horizon)
    plausibility = (
        "speed_unavailable"
        if speed is None
        else "le_160"
        if speed <= speed_limit
        else "gt_160"
    )
    streak = (
        ("frozen" if frozen else "no_streak")
        if frozen is not None
        else "streak_unavailable"
    )
    return (
        "global",
        f"state/{state}",
        f"speed/{plausibility}",
        f"streak/{streak}",
        f"cross/{state}/{plausibility}/{streak}",
    )


def parsed(record):
    fields = dict(record)
    for key in ("observed", "visible"):
        fields[key] = datetime.fromisoformat(fields[key])
    for key in ("plan", "effective_plan"):
        envelope = fields.get(key)
        fields[key] = None
        if envelope:
            envelope = dict(envelope)
            for stamp in ("reference_at", "dwell_until", "cap_reached_at"):
                value = envelope[stamp]
                envelope[stamp] = datetime.fromisoformat(value) if value else None
            fields[key] = ProgressEnvelope(**envelope)
    fields.setdefault("effective_anchor_at", None)
    fields.setdefault("effective_frozen_m", None)
    return SimpleNamespace(**fields)


def same_gps_circulation(a, b):
    return a.trip == b.trip and (not a.day or not b.day or a.day == b.day)


def same_circulation(before, after):
    return (before["trip"], before["day"]) == (after["trip"], after["day"])


def confirmed(frame, identities):
    if frame["confirmed_m"] is None or frame["confirmed_at"] is None:
        return None
    key = (frame["trip"], frame["confirmed_at"])
    hashes = identities.get(key, set())
    if len(hashes) != 1:
        raise ValueError(
            f"Identidad de ancla irresoluble: {key}, {len(hashes)} huellas"
        )
    return (frame["confirmed_at"], next(iter(hashes)))


def anchor_delta(old, new):
    if old == new:
        return "same"
    if old is None or new is None:
        return "gained" if old is None else "lost"
    if old[0] == new[0]:
        return "different_hash"
    return "newer" if old[0] < new[0] else "older"


def presentation(before, after):
    if before is None or after is None:
        return None, "not_visible_in_both_ticks"
    if not same_circulation(before, after):
        return None, "different_circulation"
    if before["shown_m"] is None or after["shown_m"] is None:
        return None, "no_map_matched_progress"
    if not before["geometry"] or before["geometry"] != after["geometry"]:
        return None, "different_geometry"
    return after["shown_m"] - before["shown_m"], None


def summarize(samples):
    by_label = defaultdict(list)
    for tag, value, case in samples:
        for label in tag:
            by_label[label].append((value, case))
    result = {}
    for label, values in by_label.items():
        magnitudes = [abs(value) for value, _ in values]
        result[label] = {
            **distribution(magnitudes),
            "gt_200": sum(value > 200 for value in magnitudes),
            "gt_5000": sum(value > 5000 for value in magnitudes),
            "negative": sum(value < 0 for value, _ in values),
            "worst": max(values, key=lambda row: abs(row[0])),
        }
    return result


def magnitude_change(old, new):
    if old == new:
        return "same"
    return "increased" if new > old else "decreased"


def gps_repeated(a, b):
    if (
        a is None
        or not same_gps_circulation(a, b)
        or a.raw_xy is None
        or b.raw_xy is None
    ):
        return None
    return a.raw_xy == b.raw_xy


def threshold_crossing(old, new):
    if old <= 200 < new:
        return "crossed_above_200"
    if new <= 200 < old:
        return "crossed_at_or_below_200"
    return None


def paired_flow(counts, tags, old, new):
    old, new = abs(old), abs(new)
    direction = magnitude_change(old, new)
    crossing = threshold_crossing(old, new)
    for tag in tags:
        counts[tag][direction] += 1
        if crossing:
            counts[tag][crossing] += 1
    return direction, crossing


class RetainedAnchorDiscrepancy:
    def __init__(self):
        self.samples = {variant: [] for variant in VARIANTS}
        self.flows = defaultdict(Counter)
        self.exclusions = Counter()
        self.cases = []
        self.baseline_candidates = []
        self.prediction_sources = Counter()

    def add(self, a, b, c, tags, segment):
        old = a.plan.progress_at(b.observed) - b.projected
        self.baseline_candidates.append(abs(old))
        if not c.previous_anchor_used:
            self.exclusions["no_retained_anchor"] += 1
            return
        if c.effective_plan is not None:
            predicted = c.effective_plan.progress_at(b.observed)
            source = "envelope"
        elif c.effective_frozen_m is not None:
            predicted = c.effective_frozen_m
            source = "frozen"
        else:
            self.exclusions["no_effective_envelope_or_frozen_progress"] += 1
            return
        self.prediction_sources[source] += 1

        repeated = gps_repeated(a, b)
        next_gps = (
            "unknown" if repeated is None else "frozen" if repeated else "changed"
        )
        tags = (*tags, f"next_gps/{next_gps}")
        new = predicted - b.projected
        paired_flow(self.flows, tags, old, new)
        case = {
            "segment": segment,
            "vehicle": a.vehicle,
            "a": a.observed.isoformat(),
            "b": b.observed.isoformat(),
            "retained_anchor_at": c.effective_anchor_at,
            "correction_prediction_source": source,
            "a_projected_m": a.projected,
            "b_projected_m": b.projected,
            "raw_xy_a": a.raw_xy,
            "raw_xy_b": b.raw_xy,
            "baseline_minus_gps_m": old,
            "correction_minus_gps_m": new,
            "strata": tags,
        }
        self.cases.append(case)
        for variant, value in zip(VARIANTS, (old, new)):
            self.samples[variant].append((tags, value, case))

    def result(self):
        return {
            "candidate_pairs": len(self.baseline_candidates),
            "baseline_all_candidates": {
                **distribution(self.baseline_candidates),
                "gt_200": sum(value > 200 for value in self.baseline_candidates),
            },
            "prediction_sources": self.prediction_sources,
            "exclusions": self.exclusions,
            "strata": {key: summarize(values) for key, values in self.samples.items()},
            "flows": self.flows,
            "cases": self.cases,
        }


def compare_gps(segments, horizon, speed_limit):
    metrics = {name: [] for name in (*VARIANTS, "common_baseline", "common_correction")}
    excluded, paired = Counter(), defaultdict(Counter)
    retained = RetainedAnchorDiscrepancy()
    available_plans = Counter()
    for index, (before, after) in enumerate(segments, start=1):
        for vehicle, old_group in before.items():
            new_group = after[vehicle]
            frozen = None
            for (a, b), (c, d) in zip(
                pairwise(old_group), pairwise(new_group), strict=True
            ):
                tags = labels(a.status, a, b, frozen, speed_limit, horizon)
                frozen = gps_repeated(a, b)
                reasons = tuple(exclusion(x, y, horizon) for x, y in ((a, b), (c, d)))
                if a.plan is not None and c.plan is not None:
                    available_plans["both"] += 1
                    if a.plan != c.plan:
                        available_plans["different"] += 1
                if reasons == (None, "sin_plan_del_ancla"):
                    retained.add(a, b, c, tags, index)
                if reasons == (None, None):
                    errors = [
                        abs(left.plan.progress_at(right.observed) - right.projected)
                        for left, right in ((a, b), (c, d))
                    ]
                    for tag in tags:
                        paired[tag][magnitude_change(*errors)] += 1
                for name, reason, (left, right) in zip(
                    VARIANTS, reasons, ((a, b), (c, d))
                ):
                    if reason:
                        excluded[(name, reason)] += 1
                        continue
                    forecast = left.plan.progress_at(right.observed)
                    case = {
                        "segment": index,
                        "vehicle": vehicle,
                        "a": left.observed.isoformat(),
                        "b": right.observed.isoformat(),
                        "gps_progress_m": right.projected,
                        "predicted_m": forecast,
                        "b_previous_anchor_used": right.previous_anchor_used,
                    }
                    sample = (tags, forecast - right.projected, case)
                    metrics[name].append(sample)
                    if reasons == (None, None):
                        metrics[f"common_{name}"].append(sample)
                excluded[("pair_eligibility", str(reasons))] += 1
    return {
        "exclusions": {
            f"{name}/{reason}": count for (name, reason), count in excluded.items()
        },
        "strata": {name: summarize(samples) for name, samples in metrics.items()},
        "paired_magnitude_change": paired,
        "own_plans_available": available_plans,
        "retained_anchor_discrepancy": retained.result(),
    }


def row_index(groups):
    rows, identities, streaks = {}, defaultdict(lambda: defaultdict(set)), {}
    for vehicle, group in groups.items():
        prev = None
        for a in group:
            key = (vehicle, a.trip, a.observed.isoformat(), a.digest)
            rows[key] = a
            identities[vehicle][(a.trip, a.observed.isoformat())].add(a.digest)
            streaks[key] = gps_repeated(prev, a)
            prev = a
    return rows, identities, streaks


def frame_raw_key(vid, frame):
    return vid, frame["trip"], frame["raw_at"], frame["raw_hash"]


def compare_frames(segments, groups, horizon, speed_limit):
    anchors, transitions, exclusions = (
        defaultdict(Counter),
        defaultdict(Counter),
        Counter(),
    )
    jumps = {name: [] for name in (*VARIANTS, "common_baseline", "common_correction")}
    paired, reacquisition_strata = defaultdict(Counter), defaultdict(Counter)
    deltas, reanchors, cases, recovery_seen = [], [], [], set()
    presentation_extremes = {}
    threshold_cases = []
    by_vehicle = defaultdict(Counter)
    exclusive = {variant: [] for variant in VARIANTS}
    exclusive_reasons = {variant: Counter() for variant in VARIANTS}
    unknown_speed = defaultdict(Counter)
    for index, ((baseline, correction), (gps, _)) in enumerate(
        zip(segments, groups), start=1
    ):
        rows, identities, streaks = row_index(gps)
        prior = {}
        for (clock, old_frames), (_, new_frames) in zip(
            baseline, correction, strict=True
        ):
            for vid in sorted(old_frames.keys() | new_frames.keys() | prior.keys()):
                frames = (old_frames.get(vid), new_frames.get(vid))
                previous = prior.get(vid, (None, None))
                exemplar = frames[0] or frames[1]
                active = exemplar or previous[0] or previous[1]
                key = frame_raw_key(vid, active)
                b = rows[key]
                prev = previous[0] or previous[1]
                prev_key = frame_raw_key(vid, prev) if prev else None
                a = rows.get(prev_key)
                tags = labels(
                    a.status if a else b.status,
                    a,
                    b,
                    streaks.get(prev_key),
                    speed_limit,
                    horizon,
                )
                _, speed_reason = gps_speed(a, b, horizon)
                case = {
                    "segment": index,
                    "vehicle": vid,
                    "tick": clock,
                    "raw_at": b.observed.isoformat(),
                }
                if frames[0] is not None and frames[1] is not None:
                    if (*frame_raw_key(vid, frames[0]), frames[0]["day"]) != (
                        *frame_raw_key(vid, frames[1]),
                        frames[1]["day"],
                    ):
                        raise ValueError(
                            f"El replay no selecciona la misma entrada: {case}"
                        )
                    ids = [confirmed(f, identities[vid]) for f in frames]
                    reason = (
                        "no_confirmed_anchor"
                        if ids == [None, None]
                        else anchor_delta(*ids)
                    )
                    if speed_reason and reason != "no_confirmed_anchor":
                        unknown_speed["anchor"][speed_reason] += 1
                    for tag in tags:
                        anchors[tag]["candidate_frames"] += 1
                        anchors[tag][reason] += 1
                    if reason not in ("same", "no_confirmed_anchor"):
                        deltas.append(
                            {
                                **case,
                                "change": reason,
                                "baseline": frames[0],
                                "correction": frames[1],
                                "identities": ids,
                            }
                        )
                elif exemplar:
                    exclusions["anchor_unpaired_frame"] += 1

                values = [presentation(p, f) for p, f in zip(previous, frames)]
                if all(value is not None for value, _ in values):
                    if speed_reason:
                        unknown_speed["presentation_common"][speed_reason] += 1
                    old_jump, new_jump = (value for value, _ in values)
                    direction, crossing = paired_flow(paired, tags, old_jump, new_jump)
                    delta_m = abs(new_jump) - abs(old_jump)
                    counts = by_vehicle[vid]
                    counts["pairs"] += 1
                    counts[direction] += 1
                    counts["baseline_gt_200"] += abs(old_jump) > 200
                    counts["correction_gt_200"] += abs(new_jump) > 200
                    counts["net_magnitude_delta_m"] += delta_m
                    if direction != "same":
                        detail = {
                            **case,
                            "strata": tags,
                            "delta_m": delta_m,
                            "baseline_jump_m": old_jump,
                            "correction_jump_m": new_jump,
                            "baseline_before": previous[0],
                            "baseline_after": frames[0],
                            "correction_before": previous[1],
                            "correction_after": frames[1],
                        }
                        extreme = presentation_extremes.get(direction)
                        if extreme is None or abs(delta_m) > abs(extreme["delta_m"]):
                            presentation_extremes[direction] = detail
                        if crossing:
                            counts[crossing] += 1
                            threshold_cases.append({**detail, "crossing": crossing})
                elif (values[0][0] is None) != (values[1][0] is None):
                    present = int(values[0][0] is None)
                    other = 1 - present
                    variant = VARIANTS[present]
                    other_reason = values[other][1]
                    exclusive_reasons[variant][other_reason] += 1
                    detail = {
                        **case,
                        "strata": tags,
                        "jump_m": values[present][0],
                        "other_exclusion": other_reason,
                        "baseline_before": previous[0],
                        "baseline_after": frames[0],
                        "correction_before": previous[1],
                        "correction_after": frames[1],
                    }
                    exclusive[variant].append((tags, values[present][0], detail))
                for name, (value, reason), p, f in zip(
                    VARIANTS, values, previous, frames
                ):
                    if p is not None or f is not None:
                        exclusions[f"{name}/{reason or 'comparable'}"] += 1
                    if value is not None:
                        sample = (tags, value, {**case, "before": p, "after": f})
                        jumps[name].append(sample)
                        if all(other is not None for other, _ in values):
                            jumps[f"common_{name}"].append(sample)
                    if p and f and same_circulation(p, f):
                        # Compare confirmed timestamps within each variant. Their identity
                        # was resolved above for every paired frame with confirmed progress.
                        old = (
                            p["confirmed_at"] if p["confirmed_m"] is not None else None
                        )
                        new = (
                            f["confirmed_at"] if f["confirmed_m"] is not None else None
                        )
                        what = anchor_delta(
                            (old,) if old else None, (new,) if new else None
                        )
                        for tag in tags:
                            transitions[tag][
                                f"{name}/{what if old or new else 'no_anchor'}"
                            ] += 1
                    if f and "anchor_reacquired" in f["flags"]:
                        event = (
                            name,
                            index,
                            vid,
                            f["raw_at"],
                            f["raw_hash"],
                            f["confirmed_at"],
                        )
                        if event not in recovery_seen:
                            recovery_seen.add(event)
                            for tag in tags:
                                reacquisition_strata[tag][name] += 1
                            reanchors.append(
                                {**case, "variant": name, "before": p, "after": f}
                            )
                if vid in CASES and CASES[vid][0] <= clock[11:19] <= CASES[vid][1]:
                    cases.append(
                        {
                            **case,
                            "baseline": frames[0],
                            "correction": frames[1],
                            "jumps_m": [v for v, _ in values],
                        }
                    )
            prior = {
                vid: (old_frames.get(vid), new_frames.get(vid))
                for vid in old_frames.keys() | new_frames.keys()
            }
    return {
        "anchor_strata": anchors,
        "anchor_transitions": transitions,
        "exclusions": exclusions,
        "anchor_differences": deltas,
        "additional_anchor_age_s": distribution(
            [
                (
                    datetime.fromisoformat(entry["identities"][0][0])
                    - datetime.fromisoformat(entry["identities"][1][0])
                ).total_seconds()
                for entry in deltas
                if entry["change"] == "older"
            ]
        ),
        "paired_presentation_extremes": presentation_extremes,
        "paired_presentation_threshold_cases": threshold_cases,
        "paired_presentation_increases_by_vehicle": {
            vid: counts
            for vid, counts in by_vehicle.items()
            if counts["correction_gt_200"] > counts["baseline_gt_200"]
        },
        "exclusive_presentation": {
            variant: {
                "strata": summarize(samples),
                "other_exclusions": exclusive_reasons[variant],
                "cases": [case for _, _, case in samples],
            }
            for variant, samples in exclusive.items()
        },
        "unknown_frame_speed": unknown_speed,
        "reacquisition_strata": reacquisition_strata,
        "paired_presentation_magnitude_change": paired,
        "reanchors": reanchors,
        "case_frames": cases,
        "presentation_strata": {
            name: summarize(samples) for name, samples in jumps.items()
        },
    }


def compare(baseline, correction):
    inputs = (
        "manifest_sha256",
        "dump_sha256",
        "gtfs_version",
        "catalog_version",
        "thresholds",
    )
    if any(baseline[key] != correction[key] for key in inputs):
        raise ValueError("Las dos revisiones tienen entradas distintas")
    thresholds = baseline["thresholds"]
    horizon, speed_limit = (
        thresholds["stale_after_s"],
        thresholds["max_estimated_speed_kmh"],
    )
    if speed_limit != 160:
        raise ValueError(
            "El estudio fija el tope de plausibilidad de producción en 160 km/h"
        )
    paired_groups, paired_frames = [], []
    for old, new in zip(baseline["segments"], correction["segments"], strict=True):
        if old["rows"].keys() != new["rows"].keys() or [t for t, _ in old["ticks"]] != [
            t for t, _ in new["ticks"]
        ]:
            raise ValueError("El calendario o la población del replay difiere")
        groups = []
        for part in (old, new):
            groups.append(
                {
                    vid: sorted(
                        (parsed(row) for row in rr), key=lambda r: (r.observed, r.run)
                    )
                    for vid, rr in part["rows"].items()
                }
            )
        for vehicle, group in groups[0].items():
            for a, b in zip(group, groups[1][vehicle], strict=True):
                if any(getattr(a, k) != getattr(b, k) for k in INPUT_KEYS):
                    raise ValueError(
                        f"El replay no contiene las mismas filas: {vehicle}, {a.observed}"
                    )
                if (a.day, a.matched_row, a.corridor, a.projected) != (
                    b.day,
                    b.matched_row,
                    b.corridor,
                    b.projected,
                ):
                    raise ValueError(
                        f"El contexto y la proyección no coinciden: {vehicle}, {a.observed}"
                    )
        paired_groups.append(groups)
        paired_frames.append((old["ticks"], new["ticks"]))
    gps = compare_gps(paired_groups, horizon, speed_limit)
    changed_fields = sorted(
        key
        for key, value in baseline["replay"].items()
        if value != correction["replay"][key]
    )
    historical = {}
    for name, trace in zip(VARIANTS, (baseline, correction)):
        result = trace["replay"]
        observed = gps["strata"][name]["global"]
        if any(observed[key] != expected for key, expected in result["jumps"].items()):
            raise ValueError(f"El cálculo H1 no coincide con el arnés original: {name}")
        historical[name] = {
            **{
                key: result[key]
                for key in (
                    "rows",
                    "pairs",
                    "vehicles",
                    "covered_vehicles",
                    "frames",
                    "gate",
                    "jumps",
                    "excluded",
                    "separacion",
                    "jump_tail",
                    "departures",
                    "m7_retenciones",
                    "jumps_by_state",
                    "h1_strata",
                    "frozen_rewind_m",
                    "latency_s",
                )
            },
            "gate": gate(observed),
        }
    return {
        "inputs": {
            **{key: baseline[key] for key in inputs},
            "heads": dict(zip(VARIANTS, (baseline["head"], correction["head"]))),
            "module_origins": {
                name: trace["module_origins"]
                for name, trace in zip(VARIANTS, (baseline, correction))
            },
        },
        "mp025b": historical,
        "mp025b_changed_fields": changed_fields,
        "gps": gps,
        **compare_frames(paired_frames, paired_groups, horizon, speed_limit),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("correction", type=Path)
    parser.add_argument("streaks", type=Path)
    args = parser.parse_args()
    result = compare(
        json.loads(args.baseline.read_text()), json.loads(args.correction.read_text())
    )
    result["mp036_streaks"] = json.loads(args.streaks.read_text())
    print(
        json.dumps(
            result, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False
        )
    )


if __name__ == "__main__":
    main()
