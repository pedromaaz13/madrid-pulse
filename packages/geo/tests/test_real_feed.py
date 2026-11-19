from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from packages.geo import build_corridor, corridor, geometry, load_relation_geometry_json, overpass
from packages.geo.overpass import RelationGeometry
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


def _shortest_pattern(validation, route_id: str) -> tuple[str, ...]:
    candidates = [p.stop_ids for p in validation.patterns if p.route_id == route_id]
    return min(candidates, key=len)


def _contiguous_subsequence_index(haystack: tuple[str, ...], needle: tuple[str, ...]) -> int | None:
    """Índice donde ``needle`` aparece como subcadena CONTIGUA de ``haystack``.

    Distinto (y más estricto) que "proyecta en orden monótono": una lista de
    paradas puede proyectar monótonamente sobre un corredor y aun así omitir
    paradas intermedias reales — eso no es un subsegmento contiguo. Ver
    hallazgo de la revisión de Codex en MP-011 (10T0047C5, variante con
    Atocha).
    """
    span = len(needle)
    for start in range(len(haystack) - span + 1):
        if haystack[start : start + span] == needle:
            return start
    return None


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

    def test_short_route_base_pattern_is_contiguous_subsegment_of_long_corridor(self) -> None:
        """La variante de 6 estaciones de 10T0047C5 (Villaverde Alto↔Fuenlabrada,
        sin pasar por Atocha) no tiene relación OSM propia. Hallazgo de
        MP-011: es, en el orden real del GTFS, una subsecuencia CONTIGUA de
        paradas del patrón largo (10T0017C5) — no solo "proyecta en orden",
        sino que ninguna parada intermedia real queda fuera. No se fabrica
        una geometría separada: se reutiliza el corredor de 10T0017C5.
        """
        long_pattern = _longest_pattern(self.validation, "10T0017C5")
        base_pattern = _shortest_pattern(self.validation, "10T0047C5")
        self.assertEqual(len(base_pattern), 6)
        index = _contiguous_subsequence_index(long_pattern, base_pattern)
        self.assertIsNotNone(index, f"{base_pattern} no es subsecuencia contigua de {long_pattern}")

        corr = self.corridors[RELATION_IDS["10T0017C5"]]
        arcs = [corr.project_station(*self.stations[stop_id])[1] for stop_id in base_pattern]
        self.assertEqual(arcs, sorted(arcs))
        for stop_id in base_pattern:
            lat, lon = self.stations[stop_id]
            projection, _ = corr.project_station(lat, lon)
            self.assertLessEqual(projection.distance_m, MAX_STATION_DISTANCE_M)

    def test_short_route_atocha_variant_is_monotonic_but_not_contiguous(self) -> None:
        """Hallazgo real de la revisión de Codex en MP-011: la variante de 7
        estaciones de 10T0047C5 (con Atocha delante de Villaverde Alto)
        proyecta en orden monótono sobre el mismo corredor que la ruta larga,
        pero NO es una subsecuencia contigua de paradas — omite las cuatro
        paradas intermedias reales entre Atocha y Villaverde Alto (Méndez
        Álvaro, Doce de Octubre, Orcasitas, Puente Alcocer). "Monótono" y
        "subsegmento contiguo" son afirmaciones distintas; esta prueba evita
        que se confundan de nuevo en la documentación.
        """
        long_pattern = _longest_pattern(self.validation, "10T0017C5")
        variant = _longest_pattern(self.validation, "10T0047C5")
        self.assertEqual(len(variant), 7)
        self.assertIsNone(_contiguous_subsequence_index(long_pattern, variant))

        corr = self.corridors[RELATION_IDS["10T0017C5"]]
        arcs = [corr.project_station(*self.stations[stop_id])[1] for stop_id in variant]
        self.assertEqual(arcs, sorted(arcs))

    def test_gap_between_disconnected_ways_is_not_fabricated_as_track(self) -> None:
        """Regresión del hallazgo bloqueante de la revisión de Codex en MP-011.

        Dos ``ways`` sintéticos sin nodo extremo compartido deben producir un
        ``ChainGap`` Y, sobre todo, ``Corridor.segments`` debe mantenerlos
        separados: proyectar un punto situado exactamente en el centro del
        hueco (equidistante de ambos extremos reales) nunca debe devolver
        ``distance_m`` cercano a 0 — eso significaría que la geometría trató
        el hueco como vía real, exactamente el bug reproducido por Codex.
        """
        # way A: (40.00,-3.80) -> (40.01,-3.80); way B (desconectado):
        # (40.05,-3.80) -> (40.06,-3.80). Separación real ~4,4 km.
        geometry_obj = RelationGeometry(
            relation_id=999999,
            tags={"name": "sintética — hueco de prueba"},
            nodes={
                1: (40.00, -3.80),
                2: (40.01, -3.80),
                3: (40.05, -3.80),
                4: (40.06, -3.80),
            },
            ways={101: (1, 2), 102: (3, 4)},
            member_refs=(("way", 101, ""), ("way", 102, "")),
        )
        corr = build_corridor(geometry_obj)
        self.assertEqual(len(corr.gaps), 1)
        self.assertFalse(corr.is_continuous)
        self.assertEqual(len(corr.segments), 2)

        # Punto equidistante de ambos extremos reales (centro del hueco real).
        midpoint_lat = (40.01 + 40.05) / 2
        projection, _ = corr.project_station(midpoint_lat, -3.80)
        min_real_gap_m = geometry.haversine_m(40.01, -3.80, 40.05, -3.80) / 2
        self.assertGreater(
            projection.distance_m,
            min_real_gap_m * 0.9,
            f"distancia fabricada ({projection.distance_m:.1f} m) — el hueco se trató como vía real",
        )

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
