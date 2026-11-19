from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from packages.gtfs import load_feed, validate_topology
from packages.gtfs import parser as parser_module

FIXTURE = Path(__file__).parents[3] / "tests" / "fixtures" / "gtfs_c5_real"
ROUTE_IDS = {
    "10T0017C5",
    "10T0018C5",
    "10T0035C5",
    "10T0047C5",
    "10T0048C5",
}


class RealRenfeFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = load_feed(FIXTURE, network_id="10", short_name="C5")
        cls.validation = validate_topology(cls.topology)

    def test_parses_all_six_real_tables(self) -> None:
        self.assertEqual({route.route_id for route in self.topology.routes}, ROUTE_IDS)
        self.assertEqual(len(self.topology.stops), 23)
        self.assertEqual({point.shape_id for point in self.topology.shape_points}, {"10_C5", "10_C5_INV"})
        self.assertGreater(len(self.topology.stop_times), 0)
        self.assertGreater(len(self.topology.calendar), 0)

    def test_groups_five_source_routes_without_collapsing_identity(self) -> None:
        groups = self.topology.route_groups()
        self.assertEqual(len(groups[("10", "C5")]), 5)
        self.assertEqual({route.route_id for route in groups[("10", "C5")]}, ROUTE_IDS)

    def test_real_station_orders_include_forward_and_reverse_full_route(self) -> None:
        patterns = {(item.route_id, item.stop_ids) for item in self.validation.patterns}
        forward = (
            "35607", "35606", "35610", "35605", "35604", "35603", "35602", "35601",
            "35600", "35608", "35609", "18000", "18003", "35702", "35703", "35704",
            "37001", "35009", "35001", "35011", "35010", "35002", "35012",
        )
        self.assertIn(("10T0017C5", forward), patterns)
        self.assertIn(("10T0018C5", tuple(reversed(forward))), patterns)

    def test_real_short_route_orders_are_reverse_pairs(self) -> None:
        patterns = {(item.route_id, item.stop_ids) for item in self.validation.patterns}
        short = ("37001", "35009", "35001", "35011", "35010", "35002")
        self.assertIn(("10T0047C5", short), patterns)
        self.assertIn(("10T0048C5", tuple(reversed(short))), patterns)

    def test_reports_source_orphan_instead_of_inventing_stops(self) -> None:
        orphan_routes = {
            trip.route_id
            for trip in self.topology.trips
            if trip.trip_id in self.validation.orphan_trip_ids
        }
        self.assertEqual(orphan_routes, {"10T0035C5"})
        self.assertTrue(self.validation.is_valid)
        self.assertIn("sin stop_times", self.validation.warnings[0])

    def test_live_trip_and_stop_resolution_are_literal(self) -> None:
        trip = next(
            trip
            for trip in self.topology.trips
            if trip.route_id == "10T0047C5" and self.topology.stop_times_for_trip(trip.trip_id)
        )
        self.assertEqual(self.topology.resolve_trip_route_id(trip.trip_id), "10T0047C5")
        first = self.topology.stop_times_for_trip(trip.trip_id)[0]
        self.assertEqual(self.topology.resolve_stop_sequences(trip.trip_id, first.stop_id), (first.stop_sequence,))
        self.assertIsNone(self.topology.resolve_trip_route_id("SPECIAL_10_unknown"))
        self.assertEqual(
            self.topology.resolve_trip_route_id(
                "SPECIAL_10_unknown", explicit_route_id="10T0047C5"
            ),
            "10T0047C5",
        )

    def test_parser_logic_does_not_embed_pilot_line_identifier(self) -> None:
        source = inspect.getsource(parser_module)
        self.assertNotIn('"C5"', source)
        self.assertNotIn("'C5'", source)


if __name__ == "__main__":
    unittest.main()
