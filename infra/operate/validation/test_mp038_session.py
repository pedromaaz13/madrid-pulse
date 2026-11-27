"""Test the arrival-based additions to MP-038 without a database."""

import unittest
from datetime import UTC, datetime, timedelta

from .mp038_session import (
    classify_aba,
    group_statistics,
    quantization,
    vehicle_operations,
)

BASE = datetime(2026, 11, 27, 8, tzinfo=UTC)
LIMITS = {"stale_after_s": 180, "max_estimated_speed_kmh": 160}


def stamp(offset):
    return (BASE + timedelta(seconds=offset)).isoformat()


def row(offset, point):
    return {
        "vehicle": "v",
        "trip": "t",
        "day": "2026-11-27",
        "observed": stamp(offset),
        "visible": stamp(offset + 1),
        "status": "INCOMING_AT",
        "digest": str(offset),
        "raw_xy": [point, -3],
        "projected": point * 100.0,
        "run": offset + 1,
    }


def frame(record, anchor, *, flags=(), space="map_matched"):
    return {
        "trip": record["trip"],
        "day": record["day"],
        "raw_at": record["observed"],
        "raw_hash": record["digest"],
        "confirmed_at": stamp(anchor) if anchor is not None else None,
        "confirmed_m": 100.0 if anchor is not None and space == "map_matched" else None,
        "flags": flags,
        "coordinate_space": space,
    }


def series(records, frames, indices=(0, 1, 2)):
    return [
        (i, r["visible"], f) for i, r, f in zip(indices, records, frames, strict=True)
    ]


class SessionComparisonTests(unittest.TestCase):
    def test_rejection_recovers_when_a_later_gps_is_accepted(self):
        a, b, c = row(0, 1), row(20, 2), row(45, 2)
        records = (a, b, c)
        frames = [frame(a, 0), frame(b, 0), frame(c, 45)]
        counts, ages, holds, promotions = vehicle_operations(
            series(records, frames), records, 1, LIMITS
        )
        self.assertEqual(counts["raw_not_accepted"], 1)
        self.assertEqual([f["age_s"] for f in ages], [1, 21, 1])
        self.assertEqual(holds[0]["duration_s"], 25)
        self.assertEqual(holds[0]["outcome"], "new_gps_accepted")
        self.assertEqual(promotions, [])

    def test_a_gap_censors_the_active_hold_at_its_last_frame(self):
        records = (row(0, 1), row(20, 2), row(45, 2))
        a, b, c = records
        frames = [frame(a, 0), frame(b, 0), frame(c, 45)]
        _, _, holds, _ = vehicle_operations(
            series(records, frames, (0, 1, 3)), records, 1, LIMITS
        )
        self.assertEqual(holds[0]["outcome"], "not_visible")
        self.assertEqual(holds[0]["duration_s"], 0)
        self.assertTrue(holds[0]["censored"])
        stats = group_statistics(holds, "duration_s", prolonged_after=180)["global"]
        self.assertEqual(stats["time_to_recovery_s"]["n"], 0)

    def test_exact_aba_distinguishes_reappearance_from_accepting_c(self):
        a, b, c = row(0, 1), row(20, 2), row(45, 1)
        for anchor, expected in ((20, "resurrected"), (45, "return_accepted")):
            with self.subTest(anchor=anchor):
                trace = {
                    "rows": {"v": [c, a, b]},
                    "ticks": [
                        [r["visible"], {"v": f}]
                        for r, f in zip(
                            (a, b, c), (frame(a, 0), frame(b, 0), frame(c, anchor))
                        )
                    ],
                }
                counts, cases = classify_aba(trace)
                self.assertEqual(counts, {expected: 1})
                self.assertEqual(cases[0]["confirmed_c"], stamp(anchor))

    def test_guarded_promotion_is_separate_from_unflagged_fallback(self):
        records = (row(0, 1), row(20, 2), row(45, 3))
        a, b, c = records
        for flags, expected in (
            ((), "unflagged_promotion"),
            (("anchor_reacquired",), "guarded_reanchor"),
        ):
            with self.subTest(flags=flags):
                frames = [frame(a, 0), frame(b, 0), frame(c, 20, flags=flags)]
                _, _, holds, promotions = vehicle_operations(
                    series(records, frames), records, 1, LIMITS
                )
                self.assertEqual(holds[0]["outcome"], expected)
                self.assertEqual(len(promotions), 1)
                self.assertEqual(promotions[0]["guarded"], bool(flags))

    def test_raw_fallback_timestamp_does_not_count_as_a_confirmed_track_anchor(self):
        records = (row(0, 1), row(20, 2), row(45, 2))
        a, b, c = records
        frames = [frame(a, 0, space="raw"), frame(b, 20, space="raw"), frame(c, 45)]
        _, ages, holds, _ = vehicle_operations(
            series(records, frames), records, 1, LIMITS
        )
        self.assertEqual([e["raw_at"] for e in ages], [c["observed"]])
        self.assertEqual(holds, [])

    def test_quantization_counts_rows_only_from_supplied_segments(self):
        segments = [{"rows": {str(i): [row(0, 1), row(1, 1)] for i in range(3)}}]
        counts = quantization(segments)
        self.assertEqual(counts["distinct_coordinates"], 1)
        self.assertEqual(counts["rows_on_coordinates_shared_by_at_least_3_vehicles"], 6)
        self.assertEqual(counts["consecutive_identical"], 3)


if __name__ == "__main__":
    unittest.main()
