import unittest
from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace

from packages.movement.model import MovementThresholds
from packages.movement.rendering import AnchorSample
from packages.movement.schedule import StopOccurrence, TripSchedule, service_day_instant

from .contradictions import ENVELOPE, alternatives, handoff, summarize


class Policies(unittest.TestCase):
    def setUp(self):
        self.day = date(2026, 11, 26)
        self.t = service_day_instant(self.day, 4200)
        self.stops = (
            StopOccurrence("origen", 1, 0, 3600, 3600),
            StopOccurrence("medio", 2, 1000, 4000, 4000),
            StopOccurrence("fin", 3, 3500, 4500, 4500),
        )
        self.inputs = {
            "schedule": TripSchedule((), 3500, True, self.stops),
            "service_date": self.day,
            "anchor_at": self.t,
            "anchor_progress_m": 1050,
            "horizon_end": self.t + timedelta(seconds=180),
            "max_speed_mps": 160 / 3.6,
            "thresholds": MovementThresholds(),
            "status": "INCOMING_AT",
            "stop_id": "medio",
        }

    def evaluate(self, **changes):
        inputs = self.inputs | changes
        return alternatives(ENVELOPE(**inputs), inputs)

    def prior(self, progress, age=40):
        return AnchorSample(self.t - timedelta(seconds=age), progress)

    def test_r4_at_zone_boundary_and_finite_r8(self):
        plans = self.evaluate(previous_anchor=self.prior(949))
        self.assertNotIn("gps_en_zona", plans)
        self.assertEqual(plans["control"].hold_reason, "operator_incoming_at")
        self.assertIsNone(plans["sin_r4"].hold_reason)
        self.assertEqual(plans["r4_r8"].hold_reason, "schedule_stop_zone")
        self.assertEqual(plans["r4_r8"].dwell_until, self.t + timedelta(seconds=30))
        self.assertEqual(plans["r4_dos_gps"], plans["r4_r8"])
        for prior in (None, self.prior(950), self.prior(949, 181), self.prior(949, 0)):
            with self.subTest(prior=prior):
                plans = self.evaluate(previous_anchor=prior)
                self.assertIs(plans["r4_dos_gps"], plans["control"])

    def test_bypass_respects_terminal_predeparture_and_incoherence(self):
        for changes, expected in (
            ({"anchor_progress_m": 3500, "stop_id": "fin"}, "terminal"),
            (
                {
                    "anchor_at": service_day_instant(self.day, 3590),
                    "anchor_progress_m": 0,
                    "stop_id": "origen",
                },
                "before_first_departure",
            ),
        ):
            with self.subTest(expected=expected):
                plans = self.evaluate(**changes)
                self.assertEqual(plans["control"].hold_reason, "operator_incoming_at")
                self.assertEqual(plans["sin_r4"].hold_reason, expected)
        for changes in (
            {"stop_id": "desconocida"},
            {"stop_id": None},
            {"anchor_progress_m": 1050.01},
            {"canceled": True},
            {"versions_match": False},
        ):
            plans = self.evaluate(**changes)
            self.assertTrue(all(p is plans["control"] for p in plans.values()))

    def test_stopped_guard_holds_the_confirmed_gps_and_preserves_contradiction(self):
        plans = self.evaluate(
            status="STOPPED_AT",
            anchor_progress_m=2000,
            previous_anchor=self.prior(1000),
        )
        guarded = plans["parada_previa"]
        self.assertGreater(plans["control"].speed_mps, 0)
        self.assertFalse(guarded.coherent)
        self.assertEqual(guarded.progress_at(self.t + timedelta(seconds=180)), 2000)
        self.assertEqual(guarded.hold_reason, "incoherent_stop_prior_gps")

    def test_stopped_guard_includes_tau_and_gps_previo_uses_the_sample(self):
        plans = self.evaluate(
            status="STOPPED_AT",
            anchor_progress_m=2000,
            previous_anchor=self.prior(1050),
        )
        for policy, expected in (("parada_previa", 2000), ("gps_previo", 1050)):
            with self.subTest(policy=policy):
                plan = plans[policy]
                self.assertFalse(plan.coherent)
                self.assertEqual(plan.speed_mps, 0)
                self.assertEqual(plan.progress_at(self.t), expected)
                self.assertEqual(
                    plan.progress_at(self.t + timedelta(seconds=180)), expected
                )

    def test_stopped_guard_requires_unique_stop_and_a_fresh_prior_in_zone(self):
        repeated = TripSchedule(
            (),
            3500,
            True,
            (
                *self.stops[:2],
                StopOccurrence("medio", 3, 2000, 4300, 4300),
                replace(self.stops[-1], stop_sequence=4),
            ),
        )
        for changes in (
            {"schedule": repeated},
            {"stop_id": None},
            {"stop_id": "desconocida"},
            {"previous_anchor": None},
            {"previous_anchor": self.prior(1000, 181)},
            {"previous_anchor": self.prior(1050.01)},
            {"canceled": True},
            {"versions_match": False},
            {"anchor_progress_m": 1050},
        ):
            with self.subTest(changes=changes):
                changes = {
                    "status": "STOPPED_AT",
                    "anchor_progress_m": 2400,
                    "previous_anchor": self.prior(1000),
                } | changes
                plans = self.evaluate(**changes)
                self.assertIs(plans["parada_previa"], plans["control"])
                self.assertIs(plans["gps_previo"], plans["control"])


class Metrics(unittest.TestCase):
    def test_streak_keeps_only_consecutive_same_coordinates_and_trip(self):
        from .contradictions import coordinate_streaks

        t = service_day_instant(date(2026, 11, 26), 3600)
        samples = [
            SimpleNamespace(
                trip=trip,
                day="2026-11-26",
                raw_xy=xy,
                observed=t + timedelta(seconds=i * 20),
            )
            for i, (trip, xy) in enumerate(
                (
                    ("t", (1, 2)),
                    ("t", (1, 2)),
                    ("t", (1, 2)),
                    ("otra", (1, 2)),
                    ("otra", None),
                    ("otra", (1, 2)),
                    ("otra", (1, 2)),
                )
            )
        ]
        self.assertEqual(
            [coordinate_streaks(samples)[id(a)] for a in samples],
            [0, 20, 40, 0, 0, 0, 20],
        )

    def test_speed_and_frozen_strata_include_absolute_speed_and_tau_boundary(self):
        from .contradictions import m7_strata

        def pair(delta, frozen, opportunity="M7"):
            return {
                "a": {"status": "INCOMING_AT"},
                "observed_delta_m": delta,
                "interval_s": 9,
                "frozen_a_s": frozen,
                "opportunity": opportunity,
                "policies": {"control": {"retained": opportunity == "M7"}},
            }

        strata = m7_strata([pair(400, 0), pair(401, 20), pair(-401, 20, None)], 160)
        self.assertEqual(len(strata["plausible/sin_racha"]["oportunidades_m7"]), 1)
        implausible = strata["sobre_tope/con_racha"]
        self.assertEqual(len(implausible["todos_h1"]), 2)
        self.assertEqual(len(implausible["oportunidades_m7"]), 1)
        self.assertEqual(len(implausible["retenciones_control"]), 1)

    def test_endpoint_uses_explicit_dsn_and_keeps_replay_guard(self):
        from .contradictions import validate_endpoint

        validate_endpoint(
            "postgresql://u:p@127.0.0.1:5472/otra", "replay", "replay", ""
        )
        for url, environment in (
            ("postgresql://u:p@127.0.0.1:5466/captura", "replay"),
            ("postgresql://u:p@127.0.0.1/db", "replay"),
            ("postgresql://u:p@127.0.0.1:5468/", "replay"),
            ("postgresql://u:p@externo:5468/db", "replay"),
            ("postgresql://u:p@127.0.0.1:5468/db?hostaddr=8.8.8.8", "replay"),
            ("postgresql://u:p@127.0.0.1:5468/db", "live"),
        ):
            with (
                self.subTest(url=url, environment=environment),
                self.assertRaises(ValueError),
            ):
                validate_endpoint(url, environment, "replay", "")

    def test_handoff_uses_presented_progress_and_checks_effective_anchor(self):
        day = date(2026, 11, 26)
        t = service_day_instant(day, 3600)
        a = SimpleNamespace(observed=t)
        b = SimpleNamespace(
            observed=t + timedelta(seconds=180), visible=t + timedelta(seconds=190)
        )
        before = SimpleNamespace(stamp=a.observed, geometry="g", trip="t", day=day)
        after = SimpleNamespace(
            stamp=b.observed, geometry="g", trip="t", day=day, shown={"control": 250}
        )
        plan = SimpleNamespace(
            reference_at=t,
            horizon_s=180,
            progress_at=lambda at: 100 + (at - t).total_seconds(),
        )
        self.assertEqual(handoff(a, b, before, after, plan, "control"), -30)
        after.stamp = a.observed
        self.assertIsNone(handoff(a, b, before, after, plan, "control"))
        after.stamp, after.geometry = b.observed, "otra"
        self.assertIsNone(handoff(a, b, before, after, plan, "control"))

    def test_censored_latency_and_rejected_handoff_keep_separate_denominators(self):
        rows = [
            {
                "retained": True,
                "latency_s": 7.0,
                "handoff_m": -201.0,
                "gps_error_m": 500.0,
                "advance_m": 0.0,
            },
            {
                "retained": True,
                "latency_s": None,
                "handoff_m": None,
                "gps_error_m": 501.0,
                "advance_m": 0.0,
            },
            {
                "retained": False,
                "latency_s": None,
                "handoff_m": 0.0,
                "gps_error_m": 0.0,
                "advance_m": 0.0,
            },
        ]
        pairs = [
            {
                "policies": {"control": r},
                "opportunity": "M7" if i < 2 else None,
                "observed_delta_m": 400 if i < 2 else 0,
                "a": {"raw_xy": (1.0, 2.0)},
                "b": {
                    "raw_xy": (3.0, 4.0) if i < 2 else (1.0, 2.0),
                    "previous_anchor_used": i == 1,
                },
            }
            for i, r in enumerate(rows)
        ]
        result = summarize([], pairs, "control")
        self.assertEqual(result["opportunities"], 2)
        self.assertEqual(result["retained"], 2)
        self.assertEqual(result["retained_previous_anchor_used"], 1)
        self.assertEqual(result["latency_s"]["n"], 1)
        self.assertEqual(result["latency_unresolved"], 1)
        self.assertEqual(result["handoff_abs_m"]["n"], 2)
        self.assertEqual(result["handoff_backwards"], 1)
        self.assertEqual(result["gps_error_m"]["n"], 3)
        self.assertEqual(result["identical_gps_pairs"], 1)
