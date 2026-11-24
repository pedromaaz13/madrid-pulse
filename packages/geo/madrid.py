"""Fuentes OSM reales verificadas para el catálogo Madrid de MP-018."""

from __future__ import annotations

from pathlib import Path

from packages.gtfs import Catalog as GtfsCatalog
from packages.gtfs import Topology

from .catalog import (
    CorridorCatalog,
    GeometrySourceSpec,
    PatternCaveat,
    build_corridor_catalog,
)


def madrid_source_specs(fixtures_root: Path) -> tuple[GeometrySourceSpec, ...]:
    c5 = fixtures_root / "osm_c5_real"
    c4 = fixtures_root / "osm_c4_real"
    captured_at = "2026-11-22"
    return (
        GeometrySourceSpec(
            3418150,
            c5 / "relation_3418150.json",
            "79f9966b2b7f3fdcebf1f41083d13ff58de39a496eca80caeb274c9b9f4d375a",
            "2026-11-19",
            frozenset({"10T0017C5", "10T0047C5"}),
        ),
        GeometrySourceSpec(
            11331,
            c5 / "relation_11331.json",
            "ec9d7decaf8d452b267df965d154c66abc7eb33d2e7cc4991db8f4dcbcab2948",
            "2026-11-19",
            frozenset({"10T0018C5", "10T0048C5"}),
        ),
        GeometrySourceSpec(
            11332,
            c4 / "relation_11332.json",
            "0351d94fdb5fe70c7b61cf45e5550f6f115785ddcdadcd32f80b256b672a63d4",
            captured_at,
            frozenset({"10T0012C4", "10T0014C4a"}),
        ),
        GeometrySourceSpec(
            9174510,
            c4 / "relation_9174510.json",
            "e057b86b2b28a2d99d2e85f91657c6f34cb6f07295758b42e8ed643a326f1439",
            captured_at,
            frozenset({"10T0011C4", "10T0013C4a"}),
        ),
        GeometrySourceSpec(
            9174511,
            c4 / "relation_9174511.json",
            "986a41bfdd843fe674700abc53fd23d0c9742367d28b4f1fe162798315610e60",
            captured_at,
            frozenset({"10T0015C4b"}),
        ),
    )


def _known_caveats(gtfs_catalog: GtfsCatalog) -> tuple[PatternCaveat, ...]:
    caveats: list[PatternCaveat] = []
    for line in gtfs_catalog.lines:
        for pattern in line.patterns:
            if pattern.route_id in {"10T0047C5", "10T0048C5"} and len(pattern.stop_ids) == 7:
                caveats.append(
                    PatternCaveat(
                        pattern.route_id,
                        pattern.stop_ids,
                        "variante real sin relación OSM propia; omite paradas intermedias del corredor C5 (DEC-025)",
                    )
                )
            if pattern.route_id == "10T0015C4b" and len(pattern.stop_ids) == 14:
                caveats.append(
                    PatternCaveat(
                        pattern.route_id,
                        pattern.stop_ids,
                        "variante GTFS omite Nuevos Ministerios entre Chamartín y Sol; vía real continua, patrón ambiguo",
                    )
                )
    return tuple(caveats)


def build_madrid_corridor_catalog(
    gtfs_catalog: GtfsCatalog, topology: Topology, *, fixtures_root: Path
) -> CorridorCatalog:
    return build_corridor_catalog(
        gtfs_catalog,
        topology,
        sources=madrid_source_specs(fixtures_root),
        caveats=_known_caveats(gtfs_catalog),
    )
