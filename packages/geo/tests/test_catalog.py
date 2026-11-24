from __future__ import annotations

import csv
import hashlib
import io
import unittest
from collections import Counter
from pathlib import Path

from packages.geo import (
    CoverageStatus,
    PositionResolution,
    build_corridor_catalog,
    shared_track_way_ids,
)
from packages.geo.madrid import build_madrid_corridor_catalog, madrid_source_specs
from packages.gtfs import RoutePattern, build_catalog, load_feed


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
OFFICIAL_GTFS = REPO_ROOT / "data" / "hito-03" / "replay" / "fomento_transit.zip"


class MadridGeometryFixtureTests(unittest.TestCase):
    """Evidencia OSM versionada que también corre en CI sin el ZIP GTFS."""

    def test_c4_relations_chain_without_gaps_and_match_manifest_checksums(self) -> None:
        from packages.geo import build_corridor, load_relation_geometry_json

        for spec in madrid_source_specs(FIXTURES):
            if spec.relation_id not in {11332, 9174510, 9174511}:
                continue
            with self.subTest(relation_id=spec.relation_id):
                self.assertEqual(hashlib.sha256(spec.path.read_bytes()).hexdigest(), spec.sha256)
                corridor = build_corridor(load_relation_geometry_json(spec.path))
                self.assertTrue(corridor.is_continuous, corridor.gaps)
                self.assertGreater(len(corridor.polyline), 800)

    def test_shared_track_is_literal_not_only_shared_station_names(self) -> None:
        specs = {item.relation_id: item for item in madrid_source_specs(FIXTURES)}
        shared = shared_track_way_ids(specs[9174510], specs[9174511])
        self.assertEqual(len(shared), 77)
        self.assertIn(9870265, shared)

    def test_ordered_stop_sequence_is_the_direction_identity(self) -> None:
        forward = RoutePattern("route", ("A", "B", "C"), 1)
        reverse = RoutePattern("route", ("C", "B", "A"), 1)
        from packages.geo import PatternIdentity

        left = PatternIdentity.from_pattern(forward)
        right = PatternIdentity.from_pattern(reverse)
        self.assertNotEqual(left.pattern_id, right.pattern_id)
        self.assertEqual(left.direction_key, "A>C")
        self.assertEqual(right.direction_key, "C>A")


@unittest.skipUnless(OFFICIAL_GTFS.is_file(), "ZIP GTFS oficial completo no presente localmente")
class MadridCorridorCatalogRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = load_feed(OFFICIAL_GTFS, network_id="10")
        gtfs_version = f"sha256:{hashlib.sha256(OFFICIAL_GTFS.read_bytes()).hexdigest()}"
        cls.gtfs_catalog = build_catalog(cls.topology, gtfs_version=gtfs_version)
        cls.catalog = build_madrid_corridor_catalog(
            cls.gtfs_catalog, cls.topology, fixtures_root=FIXTURES
        )

    def test_matrix_covers_every_pattern_and_all_twelve_lines(self) -> None:
        expected_patterns = sum(len(line.patterns) for line in self.gtfs_catalog.lines)
        self.assertEqual(len(self.catalog.entries), expected_patterns)
        self.assertEqual(expected_patterns, 103)
        self.assertEqual(
            {entry.line_id for entry in self.catalog.entries},
            {"C1", "C2", "C3", "C4", "C4a", "C4b", "C5", "C7", "C8a", "C8b", "C9", "C10"},
        )
        self.assertEqual(
            Counter(entry.status for entry in self.catalog.entries),
            {
                CoverageStatus.VALIDATED: 28,
                CoverageStatus.PARTIAL: 3,
                CoverageStatus.PENDING: 72,
            },
        )

    def test_c4_branch_relations_are_real_continuous_and_cover_both_directions(self) -> None:
        c4a = [entry for entry in self.catalog.entries if entry.line_id == "C4a"]
        self.assertEqual(len(c4a), 8)
        self.assertTrue(all(entry.status is CoverageStatus.VALIDATED for entry in c4a))
        self.assertEqual({entry.relation_id for entry in c4a}, {11332, 9174510})
        self.assertTrue(all(entry.corridor and entry.corridor.is_continuous for entry in c4a))
        self.assertTrue(all((entry.max_stop_distance_m or 999) < 50 for entry in c4a))

    def test_shared_c4a_c4b_trunk_is_confirmed_by_literal_osm_way_ids(self) -> None:
        specs = {item.relation_id: item for item in madrid_source_specs(FIXTURES)}
        # Ambas relaciones circulan hacia Parla. Coincidir en 77 way IDs de
        # vía demuestra infraestructura literal común, no solo estaciones con
        # el mismo nombre/coordenada.
        shared = shared_track_way_ids(specs[9174510], specs[9174511])
        self.assertEqual(len(shared), 77)
        self.assertIn(9870265, shared)

    def test_known_problematic_patterns_are_partial_not_silently_validated(self) -> None:
        partial = [entry for entry in self.catalog.entries if entry.status is CoverageStatus.PARTIAL]
        self.assertEqual(len(partial), 3)
        self.assertEqual(
            {(entry.line_id, entry.identity.route_id, len(entry.identity.stop_ids)) for entry in partial},
            {("C5", "10T0047C5", 7), ("C5", "10T0048C5", 7), ("C4b", "10T0015C4b", 14)},
        )
        self.assertTrue(all(not entry.can_map_match for entry in partial))

    def test_real_but_unusable_geometry_is_partial_not_pending(self) -> None:
        source = next(item for item in madrid_source_specs(FIXTURES) if item.relation_id == 11332)
        strict = build_corridor_catalog(
            self.gtfs_catalog,
            self.topology,
            sources=(source,),
            max_station_distance_m=1.0,
        )
        covered_route = [
            entry
            for entry in strict.entries
            if entry.identity.route_id in source.route_ids
        ]
        self.assertTrue(covered_route)
        self.assertTrue(all(entry.status is CoverageStatus.PARTIAL for entry in covered_route))
        self.assertTrue(all(entry.relation_id == source.relation_id for entry in covered_route))

    def test_projection_exposes_distance_from_raw_and_geometry_version(self) -> None:
        entry = next(
            item
            for item in self.catalog.entries
            if item.line_id == "C4a" and item.status is CoverageStatus.VALIDATED
        )
        stop = next(stop for stop in self.topology.stops if stop.stop_id == entry.identity.stop_ids[0])
        matched = self.catalog.match_position(
            entry.identity.pattern_id, raw_lat=stop.latitude, raw_lon=stop.longitude
        )
        self.assertEqual(matched.resolution, PositionResolution.MAP_MATCHED)
        self.assertIsNotNone(matched.projection)
        self.assertEqual(matched.distance_from_raw_m, matched.projection.distance_m)
        self.assertLess(matched.distance_from_raw_m, 150)
        self.assertEqual(matched.geometry_version, entry.geometry_version)
        self.assertIsNotNone(matched.progress_m)

    def test_partial_pending_and_missing_raw_have_honest_fallbacks(self) -> None:
        partial = next(item for item in self.catalog.entries if item.status is CoverageStatus.PARTIAL)
        pending = next(item for item in self.catalog.entries if item.status is CoverageStatus.PENDING)
        for entry in (partial, pending):
            with self.subTest(status=entry.status):
                fallback = self.catalog.match_position(
                    entry.identity.pattern_id, raw_lat=40.4, raw_lon=-3.7
                )
                self.assertEqual(fallback.resolution, PositionResolution.RAW)
                self.assertIsNone(fallback.projection)
                self.assertIsNone(fallback.distance_from_raw_m)
                self.assertIn(entry.status.value, fallback.reason)
        unlocated = self.catalog.match_position(
            pending.identity.pattern_id, raw_lat=None, raw_lon=None
        )
        self.assertEqual(unlocated.resolution, PositionResolution.UNLOCATED)
        self.assertIsNone(unlocated.projection)

    def test_csv_export_is_complete_and_carries_provenance(self) -> None:
        rows = tuple(csv.DictReader(io.StringIO(self.catalog.to_csv())))
        self.assertEqual(len(rows), len(self.catalog.entries))
        self.assertTrue(all(row["gtfs_version"] == self.catalog.gtfs_version for row in rows))
        self.assertTrue(all(row["status"] in {"validated", "partial", "pending"} for row in rows))
        sourced = [row for row in rows if row["status"] != "pending"]
        self.assertTrue(all(row["geometry_version"].startswith("osm-relation:") for row in sourced))
        self.assertTrue(all(row["source_captured_at"] for row in sourced))

if __name__ == "__main__":
    unittest.main()
