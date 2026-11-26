import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from apps.api.schemas import ProgressEnvelopeOut
from packages.movement.model import MovementThresholds
from packages.movement.rendering import ProgressEnvelope
from packages.movement.schedule import StopOccurrence, TripSchedule, service_day_instant

from .metrics import (
    Anchor,
    distribution,
    exclusion,
    gate,
    jump_strata,
    jump_tail,
    movement_opportunity,
)
from .replay import identify


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

    def test_h1_stratifies_advance_and_operator_status(self):
        t = datetime(2026, 1, 2, tzinfo=timezone.utc)
        a = Anchor(
            "v",
            "trip",
            t,
            t,
            "IN_TRANSIT_TO",
            "s",
            "h",
            1,
            projected=500,
            raw_xy=(40.0, -3.0),
        )
        still = replace(a, projected=500.5)
        self.assertEqual(
            set(jump_strata(a, still)),
            {
                "desplazamiento_inferior_1m",
                "gps_identico",
                "in_transit_to",
            },
        )
        for delta, advances in ((99.9, False), (100.0, True), (-100.0, False)):
            with self.subTest(delta=delta):
                moving = replace(a, projected=500 + delta, raw_xy=(40.1, -3.0))
                labels = set(jump_strata(a, moving))
                self.assertIn("in_transit_to", labels)
                self.assertNotIn("gps_identico", labels)
                self.assertEqual("avance_dirigido_100m" in labels, advances)
                self.assertEqual(
                    "desplazamiento_absoluto_100m" in labels, abs(delta) >= 100
                )
        self.assertNotIn(
            "in_transit_to", set(jump_strata(replace(a, status="STOPPED_AT"), still))
        )
        self.assertEqual(
            gate(distribution([0] * 600 + [300] * 500)), "cumple_umbral_mediana"
        )
        self.assertEqual(gate(distribution([300] * 500)), "incumple_umbral_mediana")

    def test_tail_excludes_a_second_gps_replaced_by_an_older_anchor(self):
        tail = jump_tail([(200, False), (5000, False), (5001, True)])
        self.assertEqual(tail["todos"]["mayores_200m"], 2)
        self.assertEqual(tail["todos"]["mayores_5000m"], 1)
        self.assertEqual(tail["sin_rechazo"]["max"], 5000)
        self.assertEqual(tail["sin_rechazo"]["mayores_5000m"], 0)
        self.assertEqual(tail["segundo_rechazado"]["n"], 1)

    def test_m7_and_stopped_departures_are_distinct(self):
        for status, displacement, expected in (
            ("IN_TRANSIT_TO", 100, "M7"),
            ("INCOMING_AT", 100, "M7"),
            ("INCOMING_AT", 99.9, None),
            ("IN_TRANSIT_TO", -100, None),
            ("STOPPED_AT", 100, "salida"),
            ("STOPPED_AT", 0.1, "salida"),
            ("STOPPED_AT", 0, None),
            ("STOPPED_AT", -100, None),
            (None, 100, None),
        ):
            with self.subTest(status=status, displacement=displacement):
                self.assertEqual(movement_opportunity(status, displacement), expected)


class Identify(unittest.TestCase):
    def setUp(self):
        self.stops = (
            StopOccurrence("origin", 1, 0, 0, 3600),
            StopOccurrence("mid", 2, 500, 4500, 4530),
            StopOccurrence("terminal", 3, 2000, 5400, 5400),
        )
        self.schedule = TripSchedule((), 2000, True, self.stops)
        self.t = service_day_instant(date(2026, 1, 2), 3600)
        self.anchor = Anchor("v", "trip", self.t, self.t, "STOPPED_AT", "mid", "h", 1)
        self.network = SimpleNamespace(
            engine_for=lambda _: SimpleNamespace(trip_schedule=lambda _: self.schedule),
        )
        self.limits = MovementThresholds()
        coverage = patch(
            "infra.operate.validation.replay.coverage_for_trip", return_value=object()
        )
        coverage.start()
        self.addCleanup(coverage.stop)

    def vehicle(self, anchor, progress, *, digest="h", gps_at=None, effective_at=None):
        return SimpleNamespace(
            raw=SimpleNamespace(
                payload_hash=digest, gps_observed_at=gps_at or anchor.observed
            ),
            service_date="2026-01-02",
            trip_id="trip",
            route_id="route",
            map_matched=SimpleNamespace(distance_from_raw_m=0, progress_m=progress),
            rendered=SimpleNamespace(
                anchor_observed_at=effective_at or anchor.observed,
                coordinate_space="map_matched",
                progress_envelope=ProgressEnvelopeOut(
                    reference_at=anchor.observed,
                    progress_m_at_reference=progress,
                    speed_mps=0,
                    max_progress_m=progress,
                    horizon_s=180,
                    dwell_until=None,
                    hold_reason=None,
                ),
                stop_state=SimpleNamespace(coherent=progress == 500),
            ),
        )

    def test_only_identifies_the_selected_raw_row_and_its_own_plan(self):
        for changes in ({"digest": "otra"}, {"gps_at": self.t - timedelta(seconds=1)}):
            a = replace(self.anchor)
            identify(a, self.vehicle(a, 500, **changes), self.network, self.limits)
            self.assertFalse(a.matched_row)
            self.assertIsNone(a.projected)
        a = replace(self.anchor)
        v = self.vehicle(a, 500, effective_at=self.t - timedelta(seconds=30))
        identify(a, v, self.network, self.limits)
        self.assertTrue(a.matched_row)
        self.assertEqual(a.projected, 500)
        self.assertTrue(a.previous_anchor_used)
        self.assertIsNone(a.plan)
        self.assertEqual(a.classification, "sin_clasificar")

    def test_stop_classification_at_departure_and_zone_boundaries(self):
        for status, stop, progress, seconds, expected in (
            ("STOPPED_AT", "origin", 0, -1, "pre_salida"),
            ("STOPPED_AT", "origin", 0, 0, "origen_tras_salida_programada"),
            ("STOPPED_AT", "mid", 550, 0, "intermedia"),
            ("STOPPED_AT", "mid", 550.1, 0, "fuera_zona_declarada"),
            ("STOPPED_AT", "terminal", 2000, 0, "terminal"),
            ("IN_TRANSIT_TO", "mid", 1500, 0, "pasada"),
            ("IN_TRANSIT_TO", "mid", 1500.1, 0, "pasada_mas_1km"),
            ("INCOMING_AT", "mid", 450, 0, "en_zona"),
            ("INCOMING_AT", "mid", 449.9, 0, "siguiente"),
        ):
            with self.subTest(
                status=status, stop=stop, progress=progress, seconds=seconds
            ):
                a = replace(
                    self.anchor,
                    status=status,
                    stop=stop,
                    observed=self.t + timedelta(seconds=seconds),
                )
                identify(a, self.vehicle(a, progress), self.network, self.limits)
                self.assertEqual(a.classification, expected)
                self.assertEqual(a.plan.progress_m_at_reference, progress)
                self.assertEqual(
                    a.declared_progress,
                    next(s.progress_m for s in self.stops if s.stop_id == stop),
                )


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
