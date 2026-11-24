"""Regresiones del artefacto contractual de cierre MP-022."""

from __future__ import annotations

import unittest

from apps.api.tools.build_closure_matrix import COLUMNS, pct, percentile


class ClosureMatrixContractTests(unittest.TestCase):
    def test_columns_match_the_binding_acceptance_schema_exactly(self) -> None:
        self.assertEqual(
            COLUMNS,
            (
                "gtfs_version", "captured_at_utc", "line_id", "route_ids",
                "pattern_count", "scheduled_trip_instances", "feed_vehicle_observations",
                "resolved_trip_instances", "matched_positions", "drawable_positions",
                "position_age_p50_s", "position_age_p95_s", "route_coverage_numerator",
                "route_coverage_denominator", "route_coverage_pct",
                "geometry_validated_patterns", "geometry_total_patterns",
                "eta_covered_stops", "eta_eligible_stops", "unknown_reason_count",
                "caveats",
            ),
        )

    def test_zero_denominator_is_null_never_fabricated_zero_percent(self) -> None:
        self.assertIsNone(pct(0, 0))
        self.assertEqual(pct(7, 7), 100.0)

    def test_position_age_percentiles_are_null_without_observations(self) -> None:
        self.assertIsNone(percentile([], 0.50))
        self.assertEqual(percentile([10, 20, 30], 0.95), 30)


if __name__ == "__main__":
    unittest.main()
