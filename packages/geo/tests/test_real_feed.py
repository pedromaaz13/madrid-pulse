from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from packages.geo import build_corridor, corridor, geometry, load_relation_geometry_json, overpass
from packages.gtfs import load_feed, validate_topology

FIXTURE_DIR = Path(__file__).parents[3] / "tests" / "fixtures" / "osm_c5_real"
GTFS_FIXTURE = Path(__file__).parents[3] / "tests" / "fixtures" / "gtfs_c5_real"

# La relación 3418150 ("Móstoles-El Soto → Atocha → Humanes") corre en el
# mismo sentido que el route_id 10T0017C5; la 11331 ("Humanes → Atocha →
# Móstoles-El Soto") en el sentido de 10T0018C5. Confirmado en MP-011
# proyectando las 23 estaciones reales y comprobando orden monótono.
RELATION_IDS = {
    "10T0017C5": 3418150,
    "10T0018C5": 11331,
}
MAX_STATION_DISTANCE_M = 150.0


def _load_corridor(relation_id: int):
    geom = load_relation_geometry_json(FIXTURE_DIR / f"relation_{relation_id}.json")
    return build_corridor(geom)


def _longest_pattern(validation, route_id: str) -> tuple[str, ...]:
    candidates = [p.stop_ids for p in validation.patterns if p.route_id == route_id]
    return max(candidates, key=len)


class RealCorridorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corridors = {rid: _load_corridor(rid) for rid in (11331, 3418148, 3418149, 3418150)}
        cls.topology = load_feed(GTFS_FIXTURE, network_id="10", short_name="C5")
        cls.validation = validate_topology(cls.topology)
        cls.stations = {
            stop.stop_id: (stop.latitude, stop.longitude) for stop in cls.topology.stops
        }

    def test_all_four_relations_chain_without_gaps(self) -> None:
        for relation_id, corr in self.corridors.items():
            with self.subTest(relation_id=relation_id):
                self.assertTrue(corr.is_continuous, f"gaps: {corr.gaps}")
                self.assertGreater(len(corr.polyline), 100)

    def _assert_pattern_monotonic(self, route_id: str, relation_id: int) -> list[float]:
        pattern = _longest_pattern(self.validation, route_id)
        corr = self.corridors[relation_id]
        arcs: list[float] = []
        for stop_id in pattern:
            lat, lon = self.stations[stop_id]
            projection, arc_m = corr.project_station(lat, lon)
            self.assertLessEqual(
                projection.distance_m,
                MAX_STATION_DISTANCE_M,
                f"{stop_id} a {projection.distance_m:.1f} m de la vía real (umbral {MAX_STATION_DISTANCE_M} m)",
            )
            arcs.append(arc_m)
        self.assertEqual(arcs, sorted(arcs), f"orden no monótono para {route_id}: {list(zip(pattern, arcs))}")
        return arcs

    def test_long_forward_route_matches_real_track_order(self) -> None:
        arcs = self._assert_pattern_monotonic("10T0017C5", RELATION_IDS["10T0017C5"])
        self.assertEqual(len(arcs), 23)

    def test_long_reverse_route_matches_real_track_order(self) -> None:
        arcs = self._assert_pattern_monotonic("10T0018C5", RELATION_IDS["10T0018C5"])
        self.assertEqual(len(arcs), 23)

    def test_short_route_is_contiguous_subsegment_of_long_corridor(self) -> None:
        """10T0047C5 (Villaverde Alto<->Fuenlabrada) no tiene relación OSM propia.

        Hallazgo de MP-011: sus estaciones son, en el orden real del GTFS,
        un subsegmento contiguo de la misma vía que usa la ruta larga. No se
        fabrica una geometría separada: se reutiliza el corredor de
        10T0017C5 y se confirma que el subsegmento corto proyecta de forma
        monótona dentro de él.
        """
        pattern = _longest_pattern(self.validation, "10T0047C5")
        corr = self.corridors[RELATION_IDS["10T0017C5"]]
        arcs = [corr.project_station(*self.stations[stop_id])[1] for stop_id in pattern]
        self.assertEqual(arcs, sorted(arcs))
        full_pattern_arcs = self._assert_pattern_monotonic("10T0017C5", RELATION_IDS["10T0017C5"])
        self.assertGreaterEqual(min(arcs), 0.0)
        self.assertLessEqual(max(arcs), max(full_pattern_arcs))

    def test_forward_and_reverse_relations_have_similar_length(self) -> None:
        forward_len = corridor.corridor_length_m(self.corridors[3418150])
        reverse_len = corridor.corridor_length_m(self.corridors[11331])
        self.assertLess(abs(forward_len - reverse_len) / forward_len, 0.01)

    def test_geometry_logic_does_not_embed_pilot_line_identifier(self) -> None:
        for module in (corridor, geometry, overpass):
            source = inspect.getsource(module)
            self.assertNotIn('"C5"', source)
            self.assertNotIn("'C5'", source)


if __name__ == "__main__":
    unittest.main()
