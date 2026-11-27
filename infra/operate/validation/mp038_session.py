"""Operational comparison of the same snapshots emitted by MP-038."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from .metrics import distribution
from .mp038_compare import VARIANTS, compare, gps_repeated, labels, same_circulation
from .segments import windows


def audit_runs(conn, manifest):
    start, end = windows(manifest)[0][0], windows(manifest)[-1][1]
    feeds = {}
    all_ids = []
    for run, feed, at, status, retro in conn.execute(
        """SELECT id, feed_name, started_at, status, is_retroactive
        FROM public.source_ingestion_run WHERE started_at >= %s AND started_at < %s
        ORDER BY id""",
        (start, end),
    ):
        all_ids.append(run)
        info = feeds.setdefault(
            feed, {"ids": [], "status": {}, "retroactive": 0, "first": at}
        )
        info["ids"].append(run)
        info["status"][status] = info["status"].get(status, 0) + 1
        info["retroactive"] += retro
        info["last"] = at
    expected = manifest["coverage_by_feed"]
    if (
        set(feeds) != set(expected)
        or any(
            len(info["ids"]) != expected[feed]["persisted_attempts"]
            for feed, info in feeds.items()
        )
        or len(all_ids) != manifest["hot_rows"]["source_ingestion_run"]
    ):
        raise ValueError("Los runs restaurados difieren de la sesión del manifiesto")
    return {
        "period": manifest["period"],
        "collector_head": manifest["head"],
        "feeds": feeds,
        "first_id": all_ids[0],
        "last_id": all_ids[-1],
        "runs": len(all_ids),
        "excluded_runs": conn.execute(
            "SELECT count(*) FROM public.source_ingestion_run"
        ).fetchone()[0]
        - len(all_ids),
    }


ENGINE_SPACES = {"map_matched", "schedule"}


def at(value):
    return datetime.fromisoformat(value)


def exact_frame(frames, row):
    frame = frames.get(row["visible"], {}).get(row["vehicle"])
    return (
        frame
        if frame
        and (frame["raw_at"], frame["raw_hash"]) == (row["observed"], row["digest"])
        else None
    )


def aba_result(b, c, before, after):
    if before is None or after is None:
        return "superseded"
    if any(f["coordinate_space"] not in ENGINE_SPACES for f in (before, after)):
        return "no_engine"
    anchor = after["confirmed_at"]
    if anchor == b["observed"]:
        return "accepted_kept" if before["confirmed_at"] == anchor else "resurrected"
    if anchor == c["observed"]:
        return "return_accepted"
    return "no_confirmed_anchor" if anchor is None else "earlier_anchor"


def ordered(rows):
    return sorted(rows, key=lambda row: (row["observed"], row["run"]))


def classify_aba(segment):
    frames = dict(segment["ticks"])
    counts, cases = Counter(), []
    for vehicle, rows in segment["rows"].items():
        rows = ordered(rows)
        stamps = Counter(row["observed"] for row in rows)
        for a, b, c in zip(rows, rows[1:], rows[2:]):
            if not (
                a["trip"] == b["trip"] == c["trip"]
                and a["raw_xy"] is not None
                and b["raw_xy"] is not None
                and a["raw_xy"] == c["raw_xy"] != b["raw_xy"]
            ):
                continue
            if stamps[b["observed"]] != 1 or stamps[c["observed"]] != 1:
                raise ValueError(f"Timestamp de B o C ambiguo en tríada: {vehicle}")
            before, after = exact_frame(frames, b), exact_frame(frames, c)
            category = aba_result(b, c, before, after)
            counts[category] += 1
            cases.append(
                {
                    "vehicle": vehicle,
                    "trip": a["trip"],
                    "a": a["observed"],
                    "b": b["observed"],
                    "c": c["observed"],
                    "visible_c": c["visible"],
                    "confirmed_b": before["confirmed_at"] if before else None,
                    "confirmed_c": after["confirmed_at"] if after else None,
                    "category": category,
                }
            )
    return counts, cases


def quantization(segments):
    points, owners = Counter(), defaultdict(set)
    counts = Counter()
    for segment in segments:
        for vehicle, rows in segment["rows"].items():
            counts["rows"] += len(rows)
            previous = None
            for row in ordered(rows):
                xy = tuple(row["raw_xy"]) if row["raw_xy"] is not None else None
                if xy is not None:
                    points[xy] += 1
                    owners[xy].add(vehicle)
                    counts["with_coordinates"] += 1
                if (
                    previous
                    and previous["trip"] == row["trip"]
                    and xy is not None
                    and previous["raw_xy"] is not None
                ):
                    counts["consecutive_comparable"] += 1
                    counts["consecutive_identical"] += (
                        previous["raw_xy"] == row["raw_xy"]
                    )
                previous = row
    return {
        **counts,
        "distinct_coordinates": len(points),
        "coordinates_shared_by_at_least_3_vehicles": sum(
            len(v) >= 3 for v in owners.values()
        ),
        "rows_on_coordinates_shared_by_at_least_3_vehicles": sum(
            points[xy] for xy, vehicles in owners.items() if len(vehicles) >= 3
        ),
    }


def confirmed_stamp(frame):
    return frame["confirmed_at"] if frame["confirmed_m"] is not None else None


def finish_hold(hold, clock, outcome, frame=None):
    return {
        **hold,
        "end": clock,
        "duration_s": (at(clock) - at(hold["start"])).total_seconds(),
        "outcome": outcome,
        "next_anchor": confirmed_stamp(frame) if frame else None,
        "rejected_arrivals_span_s": (
            at(hold["last_rejected"]) - at(hold["start"])
        ).total_seconds(),
        "censored": outcome
        in {"end_of_segment", "not_visible", "different_circulation"},
    }


def hold_outcome(old, frame, consecutive, rejected):
    if not consecutive:
        return "not_visible"
    if not same_circulation(old, frame):
        return "different_circulation"
    anchor = confirmed_stamp(frame)
    if anchor == confirmed_stamp(old):
        return None
    if anchor is None:
        return "lost_confirmation"
    if "anchor_reacquired" in frame["flags"]:
        return "guarded_reanchor"
    if anchor == frame["raw_at"]:
        return "new_gps_accepted"
    if (frame["trip"], frame["day"], anchor) in rejected:
        return "unflagged_promotion"
    return "other_anchor_change"


def group_statistics(entries, sample_key, *, prolonged_after=None):
    groups = defaultdict(list)
    for item in entries:
        for label in item["strata"]:
            groups[label].append(item)
    result = {}
    for label, items in groups.items():
        values = [item[sample_key] for item in items]
        stats = {
            **distribution(values),
            "worst": max(items, key=lambda item: item[sample_key]),
        }
        if prolonged_after is not None:
            completed = [item for item in items if not item["censored"]]
            stats["time_to_recovery_s"] = distribution(
                [
                    item[sample_key]
                    for item in completed
                    if item["outcome"] in {"new_gps_accepted", "guarded_reanchor"}
                ]
            )
            stats["completed"] = distribution([item[sample_key] for item in completed])
            stats["outcomes"] = Counter(item["outcome"] for item in items)
            stats["gt_horizon"] = sum(value > prolonged_after for value in values)
            stats["gt_horizon_with_rejections_spanning_horizon"] = sum(
                item["rejected_arrivals_span_s"] > prolonged_after for item in items
            )
            stats["gt_horizon_duration"] = distribution(
                [value for value in values if value > prolonged_after]
            )
        result[label] = stats
    return result


def vehicle_operations(series, rows, segment, thresholds):
    horizon = thresholds["stale_after_s"]
    speed = thresholds["max_estimated_speed_kmh"]
    raw_rows, previous = {}, None
    raw_stamps = Counter((record["trip"], record["observed"]) for record in rows)
    for record in ordered(rows):
        row = SimpleNamespace(**{**record, "observed": at(record["observed"])})
        raw_rows[(record["observed"], row.digest)] = (
            record,
            labels(
                row.status, previous, row, gps_repeated(previous, row), speed, horizon
            ),
        )
        previous = row
    counts = Counter()
    ages, holds, promotions = [], [], []
    rejected = set()
    hold = None
    last_index, last_clock, last_frame = -2, None, None
    for index, clock, frame in series:
        key = (frame["raw_at"], frame["raw_hash"])
        record, strata = raw_rows[key]
        anchor = confirmed_stamp(frame)
        consecutive = last_index + 1 == index
        if anchor is not None:
            age = (at(clock) - at(anchor)).total_seconds()
            if age < 0:
                raise ValueError(f"Ancla futura en {record['vehicle']} a {clock}")
            ages.append(
                {
                    "segment": segment,
                    "vehicle": record["vehicle"],
                    "trip": frame["trip"],
                    "tick": clock,
                    "anchor": anchor,
                    "raw_at": frame["raw_at"],
                    "age_s": age,
                    "strata": strata,
                }
            )
        if hold is not None:
            outcome = hold_outcome(last_frame, frame, consecutive, rejected)
            if outcome:
                end_frame = (
                    frame
                    if consecutive and outcome != "different_circulation"
                    else None
                )
                holds.append(
                    finish_hold(
                        hold, clock if end_frame else last_clock, outcome, end_frame
                    )
                )
                hold = None
        identity = (frame["trip"], frame["day"], anchor)
        if identity in rejected and (
            not consecutive
            or not same_circulation(last_frame, frame)
            or confirmed_stamp(last_frame) != anchor
        ):
            # The same flag can be present on several snapshots of one observation.
            promotions.append(
                {
                    "segment": segment,
                    "vehicle": record["vehicle"],
                    "trip": frame["trip"],
                    "tick": clock,
                    "raw_at": frame["raw_at"],
                    "promoted": anchor,
                    "guarded": "anchor_reacquired" in frame["flags"],
                    "strata": strata,
                }
            )
            rejected.discard(identity)
        if record["visible"] == clock and frame["coordinate_space"] in ENGINE_SPACES:
            counts["engine_gps_arrivals"] += 1
            if anchor == frame["raw_at"]:
                counts["raw_accepted"] += 1
            else:
                if raw_stamps[(frame["trip"], frame["raw_at"])] == 1:
                    rejected.add((frame["trip"], frame["day"], frame["raw_at"]))
                else:
                    counts["promotion_identity_ambiguous"] += 1
                counts["raw_not_accepted"] += 1
                if anchor is None:
                    counts["without_anchor"] += 1
                elif "anchor_reacquired" in frame["flags"]:
                    counts["guarded_reanchor"] += 1
                else:
                    counts["older_anchor"] += 1
                    if hold is None:
                        hold = {
                            "segment": segment,
                            "vehicle": record["vehicle"],
                            "trip": frame["trip"],
                            "start": clock,
                            "first_rejected_at": frame["raw_at"],
                            "anchor": anchor,
                            "strata": strata,
                            "rejected_arrivals": 0,
                        }
                    hold["rejected_arrivals"] += 1
                    hold["last_rejected"] = clock
        last_index, last_clock, last_frame = index, clock, frame
    if hold is not None:
        holds.append(finish_hold(hold, last_clock, "end_of_segment"))
    return counts, ages, holds, promotions


def operational(trace):
    counts, aba_counts = Counter(), Counter()
    ages, holds, promotions, aba_cases = [], [], [], []
    total_frames = 0
    for index, segment in enumerate(trace["segments"], 1):
        series = defaultdict(list)
        for tick_index, (clock, frames) in enumerate(segment["ticks"]):
            for vehicle, frame in frames.items():
                series[vehicle].append((tick_index, clock, frame))
            total_frames += len(frames)
        for vehicle, rows in segment["rows"].items():
            local_counts, local_ages, local_holds, local_promotions = (
                vehicle_operations(series[vehicle], rows, index, trace["thresholds"])
            )
            counts.update(local_counts)
            ages.extend(local_ages)
            holds.extend(local_holds)
            promotions.extend(local_promotions)
        local_counts, local_cases = classify_aba(segment)
        aba_counts.update(local_counts)
        aba_cases.extend({**case, "segment": index} for case in local_cases)
    if len(aba_cases) != trace["replay"]["triples_aba"]:
        raise ValueError(
            "El clasificador y el replay discrepan en las tríadas candidatas"
        )
    return {
        "matched_gps_arrivals": counts,
        "all_vehicle_frames": total_frames,
        "age_excluded_no_confirmation": total_frames - len(ages),
        "ages": group_statistics(ages, "age_s"),
        "holds": group_statistics(
            holds, "duration_s", prolonged_after=trace["thresholds"]["stale_after_s"]
        ),
        "hold_cases": holds,
        "promotions": promotions,
        "aba": {"counts": aba_counts, "n": len(aba_cases), "cases": aba_cases},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("correction", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("streaks", type=Path)
    args = parser.parse_args()
    old, new = (
        json.loads(path.read_text()) for path in (args.baseline, args.correction)
    )
    result = compare(old, new)
    audits = [
        {k: v for k, v in trace["session_audit"].items() if k != "product"}
        for trace in (old, new)
    ]
    if audits[0] != audits[1] or new["session_audit"]["product"] != {
        "anchor_history_depth": 256,
        "anchor_reacquire_samples": 2,
    }:
        raise ValueError("Los runs de entrada o la configuración no coinciden")
    result["session_audit"] = audits[0]
    result["product_config"] = {
        name: trace["session_audit"]["product"]
        for name, trace in zip(VARIANTS, (old, new))
    }
    result["operational"] = {
        name: operational(trace) for name, trace in zip(VARIANTS, (old, new))
    }
    result["gps_quantization"] = quantization(old["segments"])
    if args.streaks.is_file():
        result["mp036_streaks"] = json.loads(args.streaks.read_text())
    with args.output.open("x") as stream:
        json.dump(
            result,
            stream,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        stream.write("\n")


if __name__ == "__main__":
    main()
