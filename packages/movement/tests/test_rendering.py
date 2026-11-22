"""Capa `rendered` de MP-019 (ADR-0014) sobre geometría y horario reales.

Las observaciones son **sintéticas y así etiquetadas** (`raw_vehicle_label`),
construidas sobre el corredor OSM real de C5 y el horario GTFS real de la
fixture congelada: mismo criterio que `test_engine.py` de MP-012. No se
presenta ninguna como captura de Renfe.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import build_corridor, load_relation_geometry_json, point_at_arc_length
from packages.gtfs import load_feed
from packages.movement import (
    AnchorSample,
    CoordinateSpace,
    MovementEngine,
    ProgressEnvelope,
    RenderedPosition,
    RenderingMethod,
    build_trip_schedule,
    render_from_movement,
    render_raw_anchor,
    render_unlocated,
)

ROOT = Path(__file__).parents[3]
GTFS_FIXTURE = ROOT / "tests" / "fixtures" / "gtfs_c5_real"
OSM_FIXTURE = ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"
SERVICE_DATE = date(2026, 11, 19)
MADRID = ZoneInfo("Europe/Madrid")
GEOMETRY_VERSION = "osm-relation:3418150@sha256:test"
PATTERN_ID = "gtfs-pattern:test"


def _instant(seconds: float) -> datetime:
    midnight = datetime.combine(SERVICE_DATE, time.min, tzinfo=MADRID).astimezone(timezone.utc)
    return midnight + timedelta(seconds=seconds)


class RenderedPositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = load_feed(GTFS_FIXTURE, network_id="10", short_name="C5")
        cls.corridor = build_corridor(load_relation_geometry_json(OSM_FIXTURE))
        cls.trip_id = "1022J19502C5"
        cls.engine = MovementEngine(cls.topology, cls.corridor)
        cls.schedule = build_trip_schedule(cls.topology, cls.corridor, cls.trip_id)
        cls.polyline = list(cls.corridor.segments[0])
        cls.thresholds = cls.engine.thresholds
        # Índices reales del horario: un punto en marcha y la llegada a
        # Madrid-Atocha (`stop_id` 18000), que tiene una espera real de 60 s.
        cls.moving_index = 5
        cls.dwell_index = next(
            index
            for index, (left, right) in enumerate(zip(cls.schedule.points, cls.schedule.points[1:]))
            if abs(right.progress_m - left.progress_m) < 1.0 and right.seconds > left.seconds
        )

    def observation(self, *, at: datetime, progress_m: float) -> VehiclePositionObservation:
        lat, lon = point_at_arc_length(self.polyline, self.schedule.physical_arc(progress_m))
        return VehiclePositionObservation(
            source_vehicle_id="rendering-test",
            source_trip_id=self.trip_id,
            observed_at=at,
            latitude=lat,
            longitude=lon,
            raw_vehicle_label="synthetic deterministic rendering test",
            payload_hash="a" * 64,
        )

    def movement_at(self, index: int, *, age_s: float = 5.0):
        point = self.schedule.points[index]
        anchor_at = _instant(point.seconds)
        now = anchor_at + timedelta(seconds=age_s)
        latest = self.observation(at=anchor_at, progress_m=point.progress_m)
        movement = self.engine.position(
            trip_id=self.trip_id,
            service_date=SERVICE_DATE,
            calculated_at=now,
            latest=latest,
        )
        return movement, anchor_at, now

    def render(self, movement, display_at: datetime, **kwargs) -> RenderedPosition:
        return render_from_movement(
            movement,
            schedule=self.schedule,
            corridor=self.corridor,
            service_date=SERVICE_DATE,
            display_at=display_at,
            pattern_id=PATTERN_ID,
            geometry_version=GEOMETRY_VERSION,
            thresholds=self.thresholds,
            **kwargs,
        )

    # -- avance continuo sin fabricar observaciones -------------------------

    def test_presentation_advances_inside_the_observed_window(self) -> None:
        """El motor mantiene fija la observación hasta `observed_max_age_s=60`;
        eso es exactamente lo que MP-019 debe resolver sin tocar esa semántica.
        `position.mode` sigue siendo `observed`, pero `rendered` avanza."""
        movement, anchor_at, now = self.movement_at(self.moving_index)
        self.assertEqual(movement.position_mode.value, "observed")

        first = self.render(movement, now)
        later = self.render(movement, now + timedelta(seconds=20))
        self.assertEqual(first.rendering_method, RenderingMethod.EXTRAPOLATED_FROM_LAST_ANCHOR)
        self.assertGreater(later.progress_m, first.progress_m)
        # El ancla publicada es la observación real, no el frame dibujado.
        self.assertEqual(first.anchor_observed_at, anchor_at)
        self.assertEqual(later.anchor_observed_at, anchor_at)
        self.assertEqual(first.last_confirmed_at, anchor_at)

    def test_envelope_is_monotone_and_bounded_by_its_own_ceiling(self) -> None:
        movement, _, now = self.movement_at(self.moving_index)
        rendered = self.render(movement, now)
        envelope = rendered.progress_envelope
        self.assertIsNotNone(envelope)
        previous = envelope.progress_m_at_reference
        for offset in range(0, 600, 10):
            value = envelope.progress_at(now + timedelta(seconds=offset))
            self.assertGreaterEqual(value, previous)
            self.assertLessEqual(value, envelope.max_progress_m)
            previous = value
        # Evaluarla en el pasado nunca retrocede por detrás del ancla.
        self.assertEqual(
            envelope.progress_at(now - timedelta(hours=1)), envelope.progress_m_at_reference
        )

    def test_envelope_speed_never_exceeds_the_physical_threshold(self) -> None:
        movement, _, now = self.movement_at(self.moving_index)
        envelope = self.render(movement, now).progress_envelope
        self.assertLessEqual(
            envelope.speed_mps, self.thresholds.max_estimated_speed_kmh / 3.6 + 1e-9
        )

    def test_scheduled_dwell_holds_the_train_at_the_anchor(self) -> None:
        """Una espera real del horario (60 s en Madrid-Atocha) retiene el
        progreso: `anchor` mientras dura, con causa, y avance después."""
        movement, anchor_at, now = self.movement_at(self.dwell_index)
        during = self.render(movement, anchor_at + timedelta(seconds=20))
        after = self.render(movement, anchor_at + timedelta(seconds=90))
        self.assertEqual(during.rendering_method, RenderingMethod.ANCHOR)
        self.assertIn("espera programada", during.reason)
        self.assertIsNotNone(during.progress_envelope.dwell_until)
        self.assertEqual(during.progress_m, movement.anchor_progress_m)
        self.assertEqual(after.rendering_method, RenderingMethod.EXTRAPOLATED_FROM_LAST_ANCHOR)
        self.assertGreater(after.progress_m, during.progress_m)

    # -- los seis métodos ---------------------------------------------------

    def test_anchor_when_display_instant_equals_the_anchor(self) -> None:
        movement, anchor_at, _ = self.movement_at(self.moving_index)
        rendered = self.render(movement, anchor_at)
        self.assertEqual(rendered.rendering_method, RenderingMethod.ANCHOR)
        self.assertEqual(rendered.progress_m, movement.anchor_progress_m)
        self.assertEqual(rendered.anchor_age_s, 0.0)

    def test_interpolated_only_between_two_real_anchors(self) -> None:
        """`interpolated_between_known_anchors` exige ancla futura: solo con
        retraso de presentación declarado. En directo, sin ancla futura, el
        método es `extrapolated_from_last_anchor`, nunca `interpolated`."""
        movement, anchor_at, now = self.movement_at(self.moving_index)
        previous_point = self.schedule.points[self.moving_index - 1]
        previous_anchor = AnchorSample(
            observed_at=_instant(previous_point.seconds),
            progress_m=previous_point.progress_m,
        )
        middle = previous_anchor.observed_at + (anchor_at - previous_anchor.observed_at) / 2
        interpolated = self.render(movement, middle, previous_anchor=previous_anchor)
        self.assertEqual(
            interpolated.rendering_method, RenderingMethod.INTERPOLATED_BETWEEN_KNOWN_ANCHORS
        )
        self.assertGreater(interpolated.progress_m, previous_anchor.progress_m)
        self.assertLess(interpolated.progress_m, movement.anchor_progress_m)

        live = self.render(movement, now, previous_anchor=previous_anchor)
        self.assertEqual(live.rendering_method, RenderingMethod.EXTRAPOLATED_FROM_LAST_ANCHOR)

    def test_stale_frozen_freezes_at_the_anchor_without_envelope(self) -> None:
        movement, anchor_at, now = self.movement_at(
            self.moving_index, age_s=self.thresholds.stale_after_s + 30
        )
        self.assertEqual(movement.position_mode.value, "stale")
        rendered = self.render(movement, now)
        self.assertEqual(rendered.rendering_method, RenderingMethod.STALE_FROZEN)
        self.assertIsNone(rendered.progress_envelope)
        self.assertIsNone(rendered.valid_until)
        self.assertEqual(rendered.progress_m, movement.anchor_progress_m)
        self.assertEqual(rendered.last_confirmed_at, anchor_at)

    def test_horizon_exhausted_freezes_even_with_a_fresh_anchor(self) -> None:
        movement, anchor_at, now = self.movement_at(self.moving_index)
        beyond = anchor_at + timedelta(seconds=self.thresholds.stale_after_s + 1)
        rendered = self.render(movement, beyond)
        self.assertEqual(rendered.rendering_method, RenderingMethod.STALE_FROZEN)
        self.assertEqual(rendered.progress_m, movement.anchor_progress_m)
        self.assertIn("horizonte", rendered.reason)

    def test_schedule_only_has_no_anchor_and_says_so(self) -> None:
        now = _instant(self.schedule.points[self.moving_index].seconds)
        movement = self.engine.position(
            trip_id=self.trip_id, service_date=SERVICE_DATE, calculated_at=now
        )
        self.assertEqual(movement.position_mode.value, "scheduled")
        self.assertIsNone(movement.anchor_progress_m)
        rendered = self.render(movement, now + timedelta(seconds=30))
        self.assertEqual(rendered.rendering_method, RenderingMethod.SCHEDULE_ONLY)
        self.assertEqual(rendered.coordinate_space, CoordinateSpace.SCHEDULE)
        self.assertIsNone(rendered.last_confirmed_at)
        self.assertIsNone(rendered.geometry_version)
        self.assertEqual(rendered.geometry_candidate_version, GEOMETRY_VERSION)

    def test_raw_anchor_never_claims_a_projection(self) -> None:
        """Patrón sin corredor validado: GPS bruto etiquetado, sin envolvente
        (sin longitud de arco no hay avance defendible) y con la versión de
        geometría publicada como *candidata* -- nota abierta por MP-018."""
        observed_at = _instant(18_000)
        rendered = render_raw_anchor(
            raw_lat=40.4,
            raw_lon=-3.7,
            observed_at=observed_at,
            calculated_at=observed_at + timedelta(seconds=5),
            display_at=observed_at + timedelta(seconds=5),
            pattern_id=PATTERN_ID,
            geometry_candidate_version=GEOMETRY_VERSION,
            reason="corredor pending: sin geometría OSM descargada",
        )
        self.assertEqual(rendered.rendering_method, RenderingMethod.ANCHOR)
        self.assertEqual(rendered.coordinate_space, CoordinateSpace.RAW)
        self.assertIsNone(rendered.geometry_version)
        self.assertEqual(rendered.geometry_candidate_version, GEOMETRY_VERSION)
        self.assertIsNone(rendered.progress_m)
        self.assertIsNone(rendered.progress_envelope)
        self.assertIsNone(rendered.confidence_index)

    def test_raw_anchor_freezes_when_it_outlives_the_staleness_threshold(self) -> None:
        observed_at = _instant(18_000)
        rendered = render_raw_anchor(
            raw_lat=40.4,
            raw_lon=-3.7,
            observed_at=observed_at,
            calculated_at=observed_at + timedelta(seconds=400),
            display_at=observed_at + timedelta(seconds=400),
            pattern_id=PATTERN_ID,
            geometry_candidate_version=None,
            reason="corredor pending",
        )
        self.assertEqual(rendered.rendering_method, RenderingMethod.STALE_FROZEN)
        self.assertEqual(rendered.anchor_age_s, 400.0)

    def test_unlocated_publishes_no_coordinate(self) -> None:
        now = _instant(18_000)
        rendered = render_unlocated(
            calculated_at=now,
            display_at=now,
            pattern_id=PATTERN_ID,
            geometry_candidate_version=None,
            reason="posición raw ausente",
            observed_at=now - timedelta(seconds=10),
        )
        self.assertEqual(rendered.rendering_method, RenderingMethod.UNLOCATED)
        self.assertIsNone(rendered.latitude)
        self.assertIsNone(rendered.longitude)
        self.assertIsNone(rendered.coordinate_space)
        self.assertEqual(rendered.anchor_age_s, 10.0)

    # -- invariantes del contrato ------------------------------------------

    def test_geometry_version_is_rejected_outside_map_matched_space(self) -> None:
        now = _instant(18_000)
        with self.assertRaisesRegex(ValueError, "geometry_version solo es lícito"):
            RenderedPosition(
                rendering_method=RenderingMethod.ANCHOR,
                coordinate_space=CoordinateSpace.RAW,
                latitude=40.4,
                longitude=-3.7,
                progress_m=None,
                pattern_id=PATTERN_ID,
                geometry_version=GEOMETRY_VERSION,
                geometry_candidate_version=None,
                confidence_index=None,
                calculated_at=now,
                display_at=now,
                valid_until=None,
                last_confirmed_at=None,
                anchor_observed_at=None,
                anchor_age_s=None,
                anchor_distance_from_raw_m=None,
                progress_envelope=None,
                reason=None,
            )

    def test_unlocated_with_a_coordinate_is_rejected(self) -> None:
        now = _instant(18_000)
        with self.assertRaisesRegex(ValueError, "unlocated no puede publicar coordenada"):
            replace(
                render_unlocated(
                    calculated_at=now,
                    display_at=now,
                    pattern_id=None,
                    geometry_candidate_version=None,
                    reason="sin posición",
                ),
                latitude=40.0,
                longitude=-3.0,
            )

    def test_envelope_rejects_a_backward_rule(self) -> None:
        now = _instant(18_000)
        with self.assertRaisesRegex(ValueError, "nunca retrocede"):
            ProgressEnvelope(
                reference_at=now,
                progress_m_at_reference=100.0,
                speed_mps=-1.0,
                max_progress_m=200.0,
                horizon_s=60.0,
                dwell_until=None,
            )
        with self.assertRaisesRegex(ValueError, "max_progress_m no puede quedar"):
            ProgressEnvelope(
                reference_at=now,
                progress_m_at_reference=100.0,
                speed_mps=1.0,
                max_progress_m=50.0,
                horizon_s=60.0,
                dwell_until=None,
            )

    def test_anchor_progress_requires_an_observation(self) -> None:
        movement, _, now = self.movement_at(self.moving_index)
        with self.assertRaisesRegex(ValueError, "ancla incoherente"):
            replace(movement, observed_at=None)

    def test_rendered_and_legacy_position_share_the_same_anchor(self) -> None:
        """El anexo exige conservar `position.mode` por compatibilidad; esta
        prueba impide que las dos vistas se separen en silencio."""
        movement, anchor_at, now = self.movement_at(self.moving_index, age_s=90)
        self.assertEqual(movement.position_mode.value, "estimated")
        rendered = self.render(movement, now)
        self.assertEqual(rendered.anchor_observed_at, movement.observed_at)
        self.assertEqual(rendered.anchor_observed_at, anchor_at)
        self.assertEqual(rendered.calculated_at, movement.calculated_at)


if __name__ == "__main__":
    unittest.main()
