"""AC-S1…S4, T2/T3/T5. Referencias independientes del arnés MP-024."""

from dataclasses import replace
import inspect
import json
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from packages.movement import AnchorSample
from packages.movement import schedule as schedules
from packages.movement.rendering import _envelope

DATA = Path(__file__).resolve().parents[3] / "tests/fixtures/mp025a"


def envelope(case):
    stops = case["stops"]
    points = tuple(schedules.SchedulePoint(**p) for p in case["points"])
    args = {}
    if hasattr(schedules, "StopOccurrence"):
        args["stops"] = tuple(
            schedules.StopOccurrence(
                s["stop_id"], s["index"], s["progress_m"], s["arrival_s"], s["departure_s"]
            )
            for s in stops
        )
    schedule = schedules.TripSchedule(points, stops[-1]["progress_m"], True, **args)
    at = datetime.fromisoformat(case["anchor"])
    options = {}
    if "status" in inspect.signature(_envelope).parameters:
        options = dict(status=case["status"], stop_id=case["stop_id"], canceled=case["canceled"])
        if case["entry"]:
            options["previous_anchor"] = AnchorSample(
                datetime.fromisoformat(case["entry"]), case["a"]
            )
    return _envelope(
        schedule=schedule,
        service_date=date.fromisoformat(case["service_date"]),
        anchor_at=at,
        anchor_progress_m=case["a"],
        horizon_end=at + timedelta(seconds=180),
        max_speed_mps=160 / 3.6,
        **options,
    )


class SyntheticStops(unittest.TestCase):
    def test_reference_plans(self):
        for c in json.loads((DATA / "synthetic.json").read_text()):
            with self.subTest(case=c["case"]):
                plan = envelope(c)
                want = c["expected"]
                self.assertAlmostEqual(plan.max_progress_m, want["max_progress"], delta=1e-6)
                self.assertAlmostEqual(plan.speed_mps, want["speed"], delta=1e-12)
                self.assertEqual(
                    plan.dwell_until,
                    datetime.fromisoformat(want["dwell"]) if want["dwell"] else None,
                )
                self.assertEqual(
                    (
                        plan.hold_reason,
                        plan.dwell_basis,
                        plan.coherent,
                        plan.cap_kind,
                        plan.cap_stop_id,
                    ),
                    (want["hold"], want["basis"], want["coherent"], want["kind"], want["cap"]),
                )
                if want["coherent"] is False:
                    fallback = envelope({**c, "status": None, "stop_id": None})
                    self.assertEqual(
                        replace(plan, coherent=None, envelope_id=None),
                        replace(fallback, envelope_id=None),
                    )
                if plan.cap_reached_at:
                    self.assertEqual(plan.progress_at(plan.cap_reached_at), plan.max_progress_m)

    def test_python_matches_versioned_ms_fixture(self):
        self.assertEqual(samples(), json.loads((DATA / "frames.json").read_text()))


def samples():
    result = []
    for c in json.loads((DATA / "synthetic.json").read_text()):
        # Ejercita truncamiento a ms también con entrada original submilisegundo.
        c["anchor"] = (
            datetime.fromisoformat(c["anchor"]) + timedelta(microseconds=700)
        ).isoformat()
        env = envelope(c)
        instants = {env.reference_at + timedelta(seconds=s) for s in (0, 30, 90, 180)}
        for t in (env.dwell_until, env.cap_reached_at):
            if t:
                instants.update(t + timedelta(milliseconds=ms) for ms in (-1, 0, 1))
        from apps.api.schemas import ProgressEnvelopeOut

        payload = ProgressEnvelopeOut.model_validate(env, from_attributes=True).model_dump(
            mode="json"
        )
        result.append(
            dict(
                case=c["case"],
                envelope=payload,
                frames=[
                    [round(t.timestamp() * 1000), env.progress_at(t), env.phase(t)]
                    for t in sorted(instants)
                ],
            )
        )
    return result
