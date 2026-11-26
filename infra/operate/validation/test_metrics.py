import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from .metrics import Anchor, distribution, exclusion, gate
from packages.movement.rendering import ProgressEnvelope


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
            (dict(trip="2"), "otra_circulacion"),
            (dict(day="2026-01-03"), "otra_circulacion"),
            (dict(observed=t), "empate_reloj"),
            (dict(observed=t + timedelta(seconds=181)), "intervalo_largo"),
            (dict(matched_row=False), "fila_no_seleccionada"),
            (dict(corridor=False), "sin_corredor"),
            (dict(projected=None), "sin_proyeccion_valida"),
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(exclusion(a, replace(b, **changes), 180), expected)
        self.assertEqual(exclusion(replace(a, plan=None), b, 180), "sin_plan_del_ancla")
