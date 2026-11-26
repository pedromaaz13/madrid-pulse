"""Regressions for the MP-038 evaluation, with no database dependency."""

import os
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from packages.movement.rendering import ProgressEnvelope

from .mp038_compare import anchor_delta, compare_frames, compare_gps, confirmed, labels
from .mp038_streaks import frozen_runs
from .mp038_trace import check_target

START = datetime(2026, 11, 26, 6, tzinfo=UTC)


def gps(second, progress, *, plan=True, rejected=False):
    at = START + timedelta(seconds=second)
    return SimpleNamespace(
        vehicle="v",
        observed=at,
        trip="t",
        day="2026-11-26",
        status="INCOMING_AT",
        matched_row=True,
        corridor=True,
        projected=progress,
        raw_xy=(40.0, -3.0 + progress / 100_000),
        digest=f"gps-{second}",
        previous_anchor_used=rejected,
        plan=ProgressEnvelope(at, progress, 0, progress, 180, None) if plan else None,
    )


def frame(raw, anchor, shown):
    return {
        "trip": raw.trip,
        "day": raw.day,
        "raw_at": raw.observed.isoformat(),
        "raw_hash": raw.digest,
        "confirmed_at": anchor.observed.isoformat(),
        "confirmed_m": anchor.projected,
        "shown_m": shown,
        "geometry": "G",
        "flags": [],
    }


class ComparableReplayTests(unittest.TestCase):
    def test_rejected_second_gps_stays_in_h1_and_missing_first_plan_is_counted(self):
        a = gps(0, 0)
        rejected = gps(30, 1000, plan=False, rejected=True)
        b = gps(30, 1000)
        c = gps(60, 1500)
        data = compare_gps([({"v": [a, b, c]}, {"v": [a, rejected, c]})], 180, 160)
        strata = data["strata"]
        self.assertEqual(strata["baseline"]["global"]["n"], 2)
        self.assertEqual(strata["correction"]["global"]["n"], 1)
        self.assertEqual(strata["common_correction"]["global"]["p50"], 1000)
        self.assertTrue(
            strata["common_correction"]["global"]["worst"][1]["b_previous_anchor_used"]
        )
        self.assertEqual(data["exclusions"]["correction/sin_plan_del_ancla"], 1)

    def test_gps_speed_threshold_is_inclusive_and_raw_ties_are_unknown(self):
        a, b = gps(0, 0), gps(9, 400)
        self.assertIn(
            "cross/INCOMING_AT/le_160/frozen", labels(a.status, a, b, True, 160, 180)
        )
        self.assertIn(
            "speed/gt_160", labels(a.status, a, gps(9, 400.1), False, 160, 180)
        )
        self.assertIn(
            "speed/speed_unavailable", labels(a.status, a, a, False, 160, 180)
        )

    def test_anchor_identity_is_distinct_from_presentation_and_raw(self):
        a, b = gps(0, 0), gps(30, 1000)
        retained = frame(b, a, 250)
        before = [
            [a.observed.isoformat(), {"v": frame(a, a, 0)}],
            [b.observed.isoformat(), {"v": frame(b, b, 1000)}],
        ]
        after = [before[0], [b.observed.isoformat(), {"v": retained}]]
        result = compare_frames([(before, after)], [({"v": [a, b]}, {})], 180, 160)
        self.assertEqual(result["anchor_strata"]["global"]["older"], 1)
        self.assertEqual(result["anchor_differences"][0]["identities"][1][1], "gps-0")
        self.assertEqual(
            result["presentation_strata"]["common_correction"]["global"]["p50"], 250
        )
        self.assertEqual(
            result["presentation_strata"]["common_baseline"]["global"]["p50"], 1000
        )
        self.assertEqual(
            result["paired_presentation_magnitude_change"]["global"]["decreased"], 1
        )

    def test_absent_frame_does_not_bridge_gap(self):
        a, b, c = gps(0, 0), gps(30, 1000), gps(60, 2000)
        ticks = [
            [a.observed.isoformat(), {"v": frame(a, a, 0)}],
            [b.observed.isoformat(), {}],
            [c.observed.isoformat(), {"v": frame(c, c, 2000)}],
        ]
        result = compare_frames([(ticks, ticks)], [({"v": [a, b, c]}, {})], 180, 160)
        self.assertEqual(result["presentation_strata"]["baseline"], {})
        self.assertEqual(result["exclusions"]["baseline/not_visible_in_both_ticks"], 3)

    def test_an_ambiguous_confirmed_timestamp_is_rejected(self):
        a = gps(0, 0)
        with self.assertRaisesRegex(ValueError, "irresoluble"):
            confirmed(frame(a, a, 0), {("t", a.observed.isoformat()): {"a", "b"}})
        self.assertEqual(anchor_delta(("time", "a"), ("time", "b")), "different_hash")

    def test_streak_cohort_uses_the_same_source_ids_in_both_variants(self):
        baseline, correction = [], []
        for index, (point, accepted) in enumerate(
            ((0, True), (10, False), (10, False), (0, True))
        ):
            row = {
                "vehicle": "v",
                "trip": "t",
                "episode": 1,
                "id": index,
                "xy": [point, 0],
                "gps_m": point,
                "on_track": True,
                "accepted": accepted,
                "anchor_m": 0,
                "reacquired": False,
            }
            baseline.append({**row, "accepted": True})
            correction.append(row)
        stats = frozen_runs(baseline, correction)
        self.assertEqual(stats["baseline"]["identical"], 0)
        self.assertEqual(stats["correction"]["identical"], 1)
        self.assertEqual(stats["correction"]["then_near_original_anchor"], 1)
        matched = stats["correction"]["runs"][0]
        self.assertEqual([row["id"] for row in matched["baseline"]], [1, 2])
        self.assertEqual([row["id"] for row in matched["correction"]], [1, 2])

    @patch.dict(os.environ, {"MADRID_PULSE_ENV": "replay"})
    def test_endpoint_requires_explicit_local_copy_without_libpq_overrides(self):
        config = SimpleNamespace(
            database_dsn="postgresql://mp_test@127.0.0.1:5470/mp038",
            mode="replay",
            short_name="",
        )
        check_target(config)
        for url in (
            "postgresql://localhost:5470/mp038",
            "postgresql://127.0.0.1/mp038",
            "postgresql://127.0.0.1:5470/wrong",
            "postgresql://127.0.0.1:5470/mp038?options=other",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                config.database_dsn = url
                check_target(config)


if __name__ == "__main__":
    unittest.main()
