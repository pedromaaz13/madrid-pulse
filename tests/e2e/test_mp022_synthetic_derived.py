"""E2E de aceptación MP-022 sobre una secuencia **sintética derivada**.

El nombre del módulo y el manifiesto distinguen deliberadamente esta prueba
de una captura congelada y de producción en vivo. Usa el motor, GTFS y OSM
reales del repositorio, pero fabrica el reloj y las observaciones; por tanto
prueba invariantes del producto, no precisión GPS de Renfe.
"""

from __future__ import annotations

import json
import unittest
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import build_corridor, load_relation_geometry_json, point_at_arc_length
from packages.gtfs import (
    CalendarException,
    CalendarService,
    Route,
    Stop,
    StopTime,
    Topology,
    Trip,
    load_feed,
    scheduled_trip_instances_for_date,
)
from packages.movement import (
    MovementEngine,
    RenderingMethod,
    build_trip_schedule,
    render_from_movement,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "mp022_synthetic" / "sequence.json"
MADRID = ZoneInfo("Europe/Madrid")


class SyntheticDerivedRecoveryAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.topology = load_feed(
            ROOT / cls.fixture["static_sources"]["gtfs"], network_id="10", short_name="C5"
        )
        cls.corridor = build_corridor(
            load_relation_geometry_json(ROOT / cls.fixture["static_sources"]["osm"])
        )
        cls.engine = MovementEngine(cls.topology, cls.corridor)
        cls.schedule = build_trip_schedule(
            cls.topology, cls.corridor, cls.fixture["trip_id"]
        )
        cls.service_date = date.fromisoformat(cls.fixture["service_date"])
        cls.polyline = list(cls.corridor.segments[0])

    def instant(self, seconds: float) -> datetime:
        midnight = datetime.combine(
            self.service_date, time.min, tzinfo=MADRID
        ).astimezone(timezone.utc)
        return midnight + timedelta(seconds=seconds)

    def observation(self, *, at: datetime, progress_m: float, suffix: str):
        lat, lon = point_at_arc_length(
            self.polyline, self.schedule.physical_arc(progress_m)
        )
        return VehiclePositionObservation(
            source_vehicle_id=self.fixture["vehicle_id"],
            source_trip_id=self.fixture["trip_id"],
            observed_at=at,
            latitude=lat,
            longitude=lon,
            raw_vehicle_label="MP-022 SYNTHETIC DERIVED — NOT RENFE CAPTURE",
            payload_hash=(suffix * 64)[:64],
        )

    def render(self, movement, at: datetime):
        return render_from_movement(
            movement,
            schedule=self.schedule,
            corridor=self.corridor,
            service_date=self.service_date,
            display_at=at,
            pattern_id="mp022:synthetic-derived",
            geometry_version="osm-relation:3418150@mp022-synthetic",
            thresholds=self.engine.thresholds,
        )

    def test_fixture_declares_that_it_is_neither_official_nor_live(self) -> None:
        self.assertEqual(
            self.fixture["classification"],
            "synthetic_derived_from_versioned_gtfs_and_osm",
        )
        self.assertIs(self.fixture["is_official_capture"], False)
        self.assertIs(self.fixture["is_live_production"], False)

    def test_gps_recovery_after_estimation_keeps_raw_matched_and_rendered_distinct(self) -> None:
        point = self.schedule.points[self.fixture["old_anchor_schedule_point_index"]]
        anchor_at = self.instant(point.seconds)
        old = self.observation(at=anchor_at, progress_m=point.progress_m, suffix="a")

        estimated_at = anchor_at + timedelta(seconds=self.fixture["estimated_after_s"])
        estimated = self.engine.position(
            trip_id=self.fixture["trip_id"],
            service_date=self.service_date,
            calculated_at=estimated_at,
            latest=old,
        )
        self.assertEqual(estimated.position_mode.value, "estimated")
        before = self.render(estimated, estimated_at)

        recovery_progress = min(
            max(item.progress_m for item in self.schedule.points),
            estimated.progress_m + self.fixture["recovery_ahead_of_estimate_m"],
        )
        recovery_at = anchor_at + timedelta(seconds=self.fixture["recovered_after_s"])
        recovered_raw = self.observation(
            at=recovery_at, progress_m=recovery_progress, suffix="b"
        )
        recovered = self.engine.position(
            trip_id=self.fixture["trip_id"],
            service_date=self.service_date,
            calculated_at=recovery_at + timedelta(seconds=1),
            latest=recovered_raw,
            previous=old,
        )
        after = self.render(recovered, recovery_at + timedelta(seconds=1))

        self.assertEqual(recovered.position_mode.value, "observed")
        self.assertEqual(after.anchor_observed_at, recovered_raw.observed_at)
        self.assertEqual(after.geometry_version, "osm-relation:3418150@mp022-synthetic")
        self.assertEqual(after.rendering_method, RenderingMethod.EXTRAPOLATED_FROM_LAST_ANCHOR)
        self.assertGreaterEqual(after.progress_m, before.progress_m)
        self.assertLessEqual(
            after.progress_m - before.progress_m,
            self.fixture["recovery_ahead_of_estimate_m"] + 30,
            "la corrección sintética sigue el mismo corredor y queda acotada; no salta de ramal",
        )

    def test_three_controlled_clocks_advance_then_freeze_at_the_horizon(self) -> None:
        point = self.schedule.points[self.fixture["old_anchor_schedule_point_index"]]
        anchor_at = self.instant(point.seconds)
        raw = self.observation(at=anchor_at, progress_m=point.progress_m, suffix="c")
        movement = self.engine.position(
            trip_id=self.fixture["trip_id"],
            service_date=self.service_date,
            calculated_at=anchor_at + timedelta(seconds=5),
            latest=raw,
        )
        rendered = self.render(movement, anchor_at + timedelta(seconds=5))
        envelope = rendered.progress_envelope
        self.assertIsNotNone(envelope)

        offsets = self.fixture["controlled_clock_offsets_s"]
        progress = [
            envelope.progress_at(anchor_at + timedelta(seconds=5 + value))
            for value in offsets
        ]
        self.assertGreater(progress[1], progress[0])
        self.assertEqual(progress[2], envelope.max_progress_m)
        self.assertLessEqual(
            envelope.speed_mps,
            self.engine.thresholds.max_estimated_speed_kmh / 3.6,
        )


class SyntheticCalendarBoundaryAcceptanceTests(unittest.TestCase):
    def test_removed_service_with_24xx_trip_never_leaks_into_the_wrong_day(self) -> None:
        """Puerta 2 de MP-022 en una fixture sintética explícita.

        El viaje cruza medianoche con `24:05`, pero una excepción tipo 2 lo
        elimina del día de servicio. No puede reaparecer por interpretarlo como
        viaje del día civil siguiente.
        """
        topology = Topology(
            routes=(Route("10TMP022C5", "C5", "Sintética", 2, "000000", "ffffff"),),
            trips=(
                Trip(
                    "10TMP022C5",
                    "REMOVED",
                    "mp022-24xx-removed",
                    "Destino sintético",
                    1,
                    "",
                    "shape-mp022",
                ),
            ),
            stops=(
                Stop("mp022-a", "Origen", 40.0, -3.0, 1),
                Stop("mp022-b", "Destino", 40.1, -3.1, 1),
            ),
            stop_times=(
                StopTime("mp022-24xx-removed", "23:55:00", "23:55:00", "mp022-a", 1),
                StopTime("mp022-24xx-removed", "24:05:00", "24:05:00", "mp022-b", 2),
            ),
            shape_points=(),
            calendar=(
                CalendarService(
                    "REMOVED",
                    True,
                    True,
                    True,
                    True,
                    True,
                    True,
                    True,
                    "20260101",
                    "20261231",
                ),
            ),
            calendar_dates=(CalendarException("REMOVED", "20261120", 2),),
        )
        self.assertEqual(
            scheduled_trip_instances_for_date(topology, date(2026, 11, 20)), ()
        )
        self.assertEqual(
            scheduled_trip_instances_for_date(topology, date(2026, 11, 21))[0].trip_id,
            "mp022-24xx-removed",
            "el día siguiente conserva su propia instancia; no hereda la excluida",
        )


if __name__ == "__main__":
    unittest.main()
