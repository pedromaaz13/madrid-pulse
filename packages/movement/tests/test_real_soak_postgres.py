"""Validación de solo lectura contra las 668 observaciones reales de MP-007."""

from __future__ import annotations

import unittest
from collections import defaultdict
from pathlib import Path

from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import build_corridor, load_relation_geometry_json
from packages.gtfs import load_feed
from packages.movement import MovementEngine
from tests.postgres import connect_disposable_or_skip

ROOT = Path(__file__).parents[3]


class RealSoakMovementIntegrationTests(unittest.TestCase):
    def test_real_soak_rows_are_map_matched_read_only_without_changing_counts(self) -> None:
        conn = connect_disposable_or_skip()
        self.addCleanup(conn.close)
        # El soak real de MP-007 (668 filas) es una captura puntual, irrepetible,
        # de los feeds en vivo de Renfe -- solo existe en la base local de
        # desarrollo, nunca en una base fresca (p. ej. CI, ver MP-015). `skip`,
        # no `fail`, cuando no está presente: no es un fallo de este código.
        before = conn.execute("SELECT count(*) FROM vehicle_position_observation").fetchone()[0]
        if before != 668:
            raise unittest.SkipTest(
                f"soak real de MP-007 no presente en esta base ({before} filas, se esperaban 668) "
                "-- normal en una base fresca sin el histórico local de desarrollo"
            )
        topology = load_feed(
            ROOT / "tests" / "fixtures" / "gtfs_c5_real",
            network_id="10",
            short_name="C5",
        )
        corridor = build_corridor(
            load_relation_geometry_json(
                ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"
            )
        )
        engine = MovementEngine(topology, corridor)
        rows = conn.execute(
            """
            SELECT source_vehicle_id, source_trip_id, observed_at, latitude, longitude,
                   current_status, current_stop_id, speed_kmh, bearing, raw_vehicle_label,
                   payload_hash
            FROM vehicle_position_observation
            ORDER BY observed_at, id
            """
        ).fetchall()
        near_corridor = 0
        matched_by_vehicle: dict[str, list[tuple[object, float]]] = defaultdict(list)
        for row in rows:
            observation = VehiclePositionObservation(
                source_vehicle_id=row[0], source_trip_id=row[1], observed_at=row[2],
                latitude=row[3], longitude=row[4], current_status=row[5],
                current_stop_id=row[6], speed_kmh=row[7], bearing=row[8],
                raw_vehicle_label=row[9], payload_hash=row[10],
            )
            match = engine.map_match(observation)
            if match is not None and match.distance_from_track_m <= 200.0:
                near_corridor += 1
                matched_by_vehicle[observation.source_vehicle_id].append(
                    (observation.observed_at, match.physical_arc_m)
                )
        after = conn.execute("SELECT count(*) FROM vehicle_position_observation").fetchone()[0]
        conn.rollback()

        self.assertEqual(before, 668)
        self.assertEqual(len(rows), 668)
        self.assertEqual(after, before)
        self.assertGreater(near_corridor, 0)
        matched_speeds = []
        for positions in matched_by_vehicle.values():
            for (left_at, left_arc), (right_at, right_arc) in zip(positions, positions[1:]):
                elapsed = (right_at - left_at).total_seconds()
                if elapsed > 0:
                    matched_speeds.append(abs(right_arc - left_arc) / elapsed * 3.6)
        self.assertTrue(matched_speeds)
        self.assertLess(max(matched_speeds), engine.thresholds.unusable_jump_speed_kmh)
        print(
            f"real soak read-only: rows={before}, near_corridor={near_corridor}, "
            f"max_map_matched_jump_kmh={max(matched_speeds):.1f}, after={after}"
        )


if __name__ == "__main__":
    unittest.main()
