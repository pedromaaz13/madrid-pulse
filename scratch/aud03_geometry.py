#!/usr/bin/env python3
"""Diagnóstico reproducible para AUD-03; no modifica datos de producto."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.geo import (
    CoverageStatus,
    arc_length_to,
    build_corridor,
    corridor_length_m,
    load_relation_geometry_json,
    project_point_to_polyline,
    haversine_m,
    RelationGeometry,
)
from packages.geo.madrid import build_madrid_corridor_catalog, madrid_source_specs
from packages.gtfs import build_catalog, load_feed


GTFS = ROOT / "data/hito-03/replay/fomento_transit.zip"
FIXTURES = ROOT / "tests/fixtures"


def load():
    topology = load_feed(GTFS, network_id="10")
    version = f"sha256:{hashlib.sha256(GTFS.read_bytes()).hexdigest()}"
    gtfs_catalog = build_catalog(topology, gtfs_version=version)
    corridor_catalog = build_madrid_corridor_catalog(
        gtfs_catalog, topology, fixtures_root=FIXTURES
    )
    return topology, gtfs_catalog, corridor_catalog


def source_diagnostics(topology):
    stops = {stop.stop_id: (stop.latitude, stop.longitude) for stop in topology.stops}
    result = {}
    for spec in madrid_source_specs(FIXTURES):
        actual = hashlib.sha256(spec.path.read_bytes()).hexdigest()
        geometry = load_relation_geometry_json(spec.path)
        corridor = build_corridor(geometry)
        result[spec.relation_id] = (spec, actual, corridor)
    return stops, result


def evaluate(corridor, stop_ids, stops, threshold=150.0):
    projections = [corridor.project_station(*stops[stop_id]) for stop_id in stop_ids]
    distances = [projection.distance_m for projection, _ in projections]
    arcs = [arc for _, arc in projections]
    return max(distances), arcs == sorted(arcs), tuple(distances), tuple(arcs)


def longest_covered_run(corridor, stop_ids, stops, threshold=150.0):
    """Mayor subsecuencia contigua cercana y monótona sobre una relación."""
    projections = [corridor.project_station(*stops[stop_id]) for stop_id in stop_ids]
    best = (0, 0, 0)
    for left in range(len(projections)):
        previous = None
        for right in range(left, len(projections)):
            projection, arc = projections[right]
            if projection.distance_m > threshold or (previous is not None and arc < previous):
                break
            previous = arc
            if right + 1 - left > best[0]:
                best = (right + 1 - left, left, right + 1)
    count, left, right = best
    return count, tuple(stop_ids[left:right])


def representative_shapes(topology):
    by_key = {}
    for trip in topology.trips:
        stop_ids = tuple(item.stop_id for item in topology.stop_times_for_trip(trip.trip_id))
        if stop_ids:
            by_key.setdefault((trip.route_id, stop_ids), trip.shape_id)
    points = defaultdict(list)
    for point in topology.shape_points:
        points[point.shape_id].append((point.sequence, (point.latitude, point.longitude)))
    return by_key, {
        shape_id: [coordinate for _, coordinate in sorted(values)]
        for shape_id, values in points.items()
    }


def pattern_length(entry, topology, shape_by_pattern, shape_points, stops):
    if len(entry.identity.stop_ids) < 2:
        return 0.0, 0.0, True
    shape_id = shape_by_pattern[(entry.identity.route_id, entry.identity.stop_ids)]
    polyline = shape_points[shape_id]
    projections = [
        project_point_to_polyline(*stops[stop_id], polyline)
        for stop_id in entry.identity.stop_ids
    ]
    arcs = [arc_length_to(polyline, projection) for projection in projections]
    max_distance = max(projection.distance_m for projection in projections)
    monotonic = arcs == sorted(arcs) or arcs == sorted(arcs, reverse=True)
    return abs(arcs[-1] - arcs[0]) if monotonic else 0.0, max_distance, monotonic


def summary():
    topology, _, catalog = load()
    stops, sources = source_diagnostics(topology)
    shape_by_pattern, shape_points = representative_shapes(topology)

    totals = defaultdict(float)
    unique_stops = defaultdict(set)
    classes = Counter()
    reusable = []
    reused_runs = defaultdict(lambda: [0, 0, set()])
    rows = []
    for entry in catalog.entries:
        status = entry.status.value
        length_m, shape_distance_m, shape_monotonic = pattern_length(
            entry, topology, shape_by_pattern, shape_points, stops
        )
        chord_m = sum(
            haversine_m(*stops[left], *stops[right])
            for left, right in zip(entry.identity.stop_ids, entry.identity.stop_ids[1:])
        )
        totals[(status, "patterns")] += 1
        totals[(status, "trips")] += entry.trip_count
        totals[(status, "station_calls")] += entry.trip_count * len(entry.identity.stop_ids)
        totals[(status, "pattern_m")] += length_m
        totals[(status, "scheduled_m")] += length_m * entry.trip_count
        totals[(status, "chord_m")] += chord_m
        totals[(status, "scheduled_chord_m")] += chord_m * entry.trip_count
        if shape_monotonic and shape_distance_m <= 150:
            totals[(status, "reliable_shape_patterns")] += 1
            totals[(status, "reliable_shape_m")] += length_m
        unique_stops[status].update(entry.identity.stop_ids)

        if entry.status is CoverageStatus.VALIDATED:
            continue

        viable = []
        runs = []
        for relation_id, (_, _, corridor) in sources.items():
            max_distance, monotonic, _, _ = evaluate(
                corridor, entry.identity.stop_ids, stops
            )
            if max_distance <= 150 and monotonic:
                viable.append((relation_id, max_distance))
            count, stop_run = longest_covered_run(
                corridor, entry.identity.stop_ids, stops
            )
            runs.append((count, relation_id, stop_run))
        runs.sort(reverse=True)
        if runs[0][0] >= 2:
            key = (runs[0][1], runs[0][2])
            reused_runs[key][0] += 1
            reused_runs[key][1] += entry.trip_count
            reused_runs[key][2].add(entry.line_id)

        if entry.status is CoverageStatus.PARTIAL:
            cause = "caveat_explicita_pese_a_geometria_valida"
        elif len(entry.identity.stop_ids) < 2:
            cause = "patron_degenerado_una_parada"
        elif entry.identity.route_id == "10T0016C4b":
            cause = "fuente_direccional_9174512_no_congelada"
        elif viable:
            cause = "allowlist_route_id_excluye_geometria_reutilizable"
        else:
            cause = "sin_fuente_osm_suficiente_en_fixture"
        classes[cause] += 1
        if viable:
            reusable.append((entry.identity.pattern_id, viable))
        rows.append(
            {
                "line": entry.line_id,
                "route": entry.identity.route_id,
                "pattern": entry.identity.pattern_id,
                "direction": entry.identity.direction_key,
                "stops": len(entry.identity.stop_ids),
                "trips": entry.trip_count,
                "status": status,
                "cause": cause,
                "viable_relations": ";".join(
                    f"{relation_id}:{distance:.1f}m"
                    for relation_id, distance in sorted(viable)
                ),
                "best_reused_run": (
                    f"{runs[0][1]}:{runs[0][0]}/{len(entry.identity.stop_ids)}:"
                    + ">".join(runs[0][2])
                ),
                "shape_length_km": f"{length_m / 1000:.3f}",
                "shape_max_stop_distance_m": f"{shape_distance_m:.1f}",
                "shape_monotonic": shape_monotonic,
                "chord_length_km": f"{chord_m / 1000:.3f}",
            }
        )

    print("SOURCE_CHECKS")
    for relation_id, (spec, actual, corridor) in sorted(sources.items()):
        print(
            relation_id,
            "sha_ok", actual == spec.sha256,
            "relation_ok", corridor.relation_id == relation_id,
            "gaps", len(corridor.gaps),
            "track_km", f"{corridor_length_m(corridor)/1000:.3f}",
        )
    print("CAUSES", dict(classes))
    print("REUSABLE_FULL", len(reusable))
    print("REUSED_RUNS")
    for (relation_id, stop_run), (patterns, trips, lines) in sorted(
        reused_runs.items(), key=lambda item: (-item[1][1], -item[1][0], item[0])
    ):
        print(
            relation_id, ">".join(stop_run),
            "patterns", patterns, "trips", trips, "lines", "/".join(sorted(lines)),
        )
    statuses = ("validated", "partial", "pending")
    for metric in (
        "patterns", "trips", "station_calls", "chord_m", "scheduled_chord_m",
        "pattern_m", "scheduled_m", "reliable_shape_patterns", "reliable_shape_m",
    ):
        denominator = sum(totals[(status, metric)] for status in statuses)
        print("METRIC", metric, "total", denominator)
        for status in statuses:
            value = totals[(status, metric)]
            print(" ", status, value, f"{100*value/denominator:.6f}%" if denominator else "n/a")
    all_stops = set().union(*(unique_stops[status] for status in statuses))
    print("UNIQUE_STOPS", len(all_stops))
    for status in statuses:
        print(" ", status, len(unique_stops[status]), f"{100*len(unique_stops[status])/len(all_stops):.6f}%")
    print("NONVALID_ROWS")
    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)


def live_c4b():
    """Contraste puntual de la relación opuesta que MP-018 no congeló."""
    relation_id = 9174512
    request = urllib.request.Request(
        f"https://api.openstreetmap.org/api/0.6/relation/{relation_id}/full.json",
        headers={"User-Agent": "madrid-pulse-aud03/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = response.read()
    payload = json.loads(body)
    elements = payload["elements"]
    relation = next(
        item for item in elements
        if item["type"] == "relation" and item["id"] == relation_id
    )
    geometry = RelationGeometry(
        relation_id=relation_id,
        tags=relation.get("tags", {}),
        nodes={
            item["id"]: (item["lat"], item["lon"])
            for item in elements if item["type"] == "node"
        },
        ways={
            item["id"]: tuple(item["nodes"])
            for item in elements if item["type"] == "way"
        },
        member_refs=tuple(
            (member["type"], member["ref"], member.get("role", ""))
            for member in relation.get("members", ())
        ),
    )
    corridor = build_corridor(geometry)
    topology, _, catalog = load()
    stops = {stop.stop_id: (stop.latitude, stop.longitude) for stop in topology.stops}
    print(
        "RELATION", relation_id,
        "version", relation.get("version"),
        "timestamp", relation.get("timestamp"),
        "sha256", hashlib.sha256(body).hexdigest(),
        "name", relation.get("tags", {}).get("name"),
    )
    print(
        "GEOMETRY", "nodes", len(geometry.nodes), "ways", len(geometry.ways),
        "gaps", len(corridor.gaps), "track_km", f"{corridor_length_m(corridor)/1000:.3f}",
    )
    for entry in catalog.entries:
        if entry.identity.route_id != "10T0016C4b":
            continue
        max_distance, monotonic, _, arcs = evaluate(
            corridor, entry.identity.stop_ids, stops
        )
        print(
            entry.identity.pattern_id, entry.identity.direction_key,
            "trips", entry.trip_count, "stops", len(entry.identity.stop_ids),
            "max_m", f"{max_distance:.1f}", "monotonic", monotonic,
            "arc_km", f"{(arcs[-1]-arcs[0])/1000:.3f}",
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("summary", "live-c4b"))
    args = parser.parse_args()
    if args.command == "summary":
        summary()
    elif args.command == "live-c4b":
        live_c4b()


if __name__ == "__main__":
    main()
