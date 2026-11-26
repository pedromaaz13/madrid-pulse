import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from packages.movement.rendering import ProgressEnvelope

from .metrics import Anchor, distribution, exclusion, gate


class Metrics(unittest.TestCase):
    def test_quantiles(self):
        self.assertIsNone(distribution([])["p50"])
        self.assertEqual(distribution([10])["max"], 10)
        result = distribution([0, 0, 0, 400])
        self.assertEqual(result["p50"], 0)
        self.assertAlmostEqual(result["p90"], 280)

    def test_sample_gate(self):
        self.assertEqual(gate(distribution([0] * 499)), "insuficiente")
        self.assertEqual(gate(distribution([200] * 500)), "cumple_umbral_mediana")
        self.assertEqual(gate(distribution([201] * 500)), "incumple_umbral_mediana")

    def test_consecutive_pair(self):
        t = datetime(2026, 1, 2, tzinfo=timezone.utc)
        plan = ProgressEnvelope(t, 0, 1, 180, 180, None)
        a = Anchor(
            "1",
            "trip",
            t,
            t,
            "IN_TRANSIT_TO",
            "s",
            "h",
            1,
            day="2026-01-02",
            corridor=True,
            projected=0,
            plan=plan,
            matched_row=True,
        )
        b = replace(a, observed=t + timedelta(seconds=180), projected=90)
        self.assertIsNone(exclusion(a, b, 180))
        self.assertEqual(abs(a.plan.progress_at(b.observed) - b.projected), 90)
        for changes, expected in [
            ({"trip": "2"}, "otra_circulacion"),
            ({"day": "2026-01-03"}, "otra_circulacion"),
            ({"observed": t}, "empate_reloj"),
            ({"observed": t + timedelta(seconds=181)}, "intervalo_largo"),
            ({"matched_row": False}, "fila_no_seleccionada"),
            ({"corridor": False}, "sin_corredor"),
            ({"projected": None}, "sin_proyeccion_valida"),
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(exclusion(a, replace(b, **changes), 180), expected)
        self.assertEqual(exclusion(replace(a, plan=None), b, 180), "sin_plan_del_ancla")


class SegmentWindows(unittest.TestCase):
    def test_closed_left_observation_and_independent_restart(self):
        from .segments import windows

        base = datetime(2026, 11, 26, 6, tzinfo=timezone.utc)
        first, left, right, end = (
            base + timedelta(seconds=seconds) for seconds in (0, 2100, 5673, 10800)
        )
        manifest = {
            "period": {"start_utc": first.isoformat(), "end_utc": end.isoformat()},
            "coverage_by_feed": {
                "vehicle_positions": {
                    "gaps_over_60_seconds": [
                        {"from_utc": left.isoformat(), "to_utc": right.isoformat()}
                    ]
                }
            },
        }
        spans = windows(manifest)
        self.assertEqual(
            spans, [(first, left + timedelta(microseconds=1)), (right, end)]
        )
        inside = left + timedelta(seconds=1)
        self.assertFalse(any(a <= inside < b for a, b in spans))
        manifest["coverage_by_feed"]["vehicle_positions"]["gaps_over_60_seconds"] = []
        self.assertEqual(windows(manifest), [(first, end)])


class DepartureLatency(unittest.TestCase):
    def test_rejected_then_confirmed_or_reverted(self):
        from .metrics import first_departure_frame

        t = datetime(2026, 11, 26, 6, tzinfo=timezone.utc)
        a = Anchor(
            "v",
            "trip",
            t,
            t,
            "STOPPED_AT",
            "s",
            "a",
            1,
            day="2026-11-26",
            plan=ProgressEnvelope(t, 100, 0, 100, 180, None),
        )
        b = replace(
            a, observed=t + timedelta(seconds=30), visible=t + timedelta(seconds=40)
        )
        old = (b.visible, a.trip, a.day, t, 100, 100)
        at = b.visible + timedelta(seconds=30)
        confirmed = (at, a.trip, a.day, b.observed, 130, 130)
        reverted = (at, a.trip, a.day, at, 100, 100)
        self.assertEqual(first_departure_frame([old, confirmed], a, b), at)
        self.assertIsNone(first_departure_frame([old, reverted, confirmed], a, b))
