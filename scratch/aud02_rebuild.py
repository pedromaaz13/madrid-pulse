#!/usr/bin/env python3
"""Reconstrucción independiente del GTFS Madrid para AUD-02.

Solo usa la biblioteca estándar y los CSV crudos del ZIP. No importa código
de ``packages.gtfs`` ni reutiliza sus tipos o algoritmos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile


def cleaned_rows(archive: ZipFile, name: str):
    with archive.open(name) as raw:
        decoded = (line.decode("utf-8-sig") for line in raw)
        for row in csv.DictReader(decoded):
            yield {
                (key or "").strip(): (value or "").strip()
                for key, value in row.items()
            }


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def gtfs_seconds(value: str) -> int:
    hours, minutes, seconds = map(int, value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_008.8 * 2 * math.asin(math.sqrt(h))


def load(zip_path: Path):
    with ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        routes = {
            row["route_id"]: row
            for row in cleaned_rows(archive, "routes.txt")
            if row["route_id"].startswith("10")
        }
        trips = {
            row["trip_id"]: row
            for row in cleaned_rows(archive, "trips.txt")
            if row["route_id"] in routes
        }
        by_trip: dict[str, list[tuple[int, str, str, str]]] = defaultdict(list)
        for row in cleaned_rows(archive, "stop_times.txt"):
            if row["trip_id"] in trips:
                by_trip[row["trip_id"]].append(
                    (
                        int(row["stop_sequence"]),
                        row["stop_id"],
                        row["arrival_time"],
                        row["departure_time"],
                    )
                )
        for values in by_trip.values():
            values.sort()
        stop_ids = {stop_id for values in by_trip.values() for _, stop_id, _, _ in values}
        stops = {
            row["stop_id"]: row
            for row in cleaned_rows(archive, "stops.txt")
            if row["stop_id"] in stop_ids
        }
        service_ids = {trip["service_id"] for trip in trips.values()}
        calendar = {
            row["service_id"]: row
            for row in cleaned_rows(archive, "calendar.txt")
            if row["service_id"] in service_ids
        }
        calendar_dates = (
            [row for row in cleaned_rows(archive, "calendar_dates.txt") if row["service_id"] in service_ids]
            if "calendar_dates.txt" in names
            else []
        )
        shape_ids = {trip["shape_id"] for trip in trips.values()}
        shapes: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
        for row in cleaned_rows(archive, "shapes.txt"):
            if row["shape_id"] in shape_ids:
                shapes[row["shape_id"]].append(
                    (int(row["shape_pt_sequence"]), float(row["shape_pt_lat"]), float(row["shape_pt_lon"]))
                )
        for values in shapes.values():
            values.sort()
    return routes, trips, by_trip, stops, calendar, calendar_dates, shapes


def build_patterns(routes, trips, by_trip):
    grouped = {}
    for trip_id, trip in trips.items():
        values = by_trip.get(trip_id, [])
        if not values:
            # Un trip sin stop_times no constituye un patrón ferroviario: se
            # contabiliza aparte como huérfano, igual que exige la semántica
            # GTFS (no se inventa una secuencia vacía como recorrido).
            continue
        sequence = tuple(item[1] for item in values)
        key = (trip["route_id"], sequence)
        pattern = grouped.setdefault(
            key,
            {
                "route_id": trip["route_id"],
                "stop_ids": sequence,
                "trip_count": 0,
                "service_ids": set(),
                "headsigns": Counter(),
                "shape_ids": Counter(),
                "first_times": [],
                "last_times": [],
            },
        )
        pattern["trip_count"] += 1
        pattern["service_ids"].add(trip["service_id"])
        pattern["headsigns"][trip["trip_headsign"]] += 1
        pattern["shape_ids"][trip["shape_id"]] += 1
        if values:
            pattern["first_times"].append(values[0][3] or values[0][2])
            pattern["last_times"].append(values[-1][2] or values[-1][3])
    return [grouped[key] for key in sorted(grouped)]


def station_name(stops, stop_id):
    return compact(stops[stop_id]["stop_name"])


def pattern_geometry(pattern, stops, shapes):
    shape_id = pattern["shape_ids"].most_common(1)[0][0]
    points = shapes[shape_id]
    nearest = []
    for stop_id in pattern["stop_ids"]:
        stop = stops[stop_id]
        coord = (float(stop["stop_lat"]), float(stop["stop_lon"]))
        candidates = [(haversine_m(coord, (lat, lon)), index) for index, (_, lat, lon) in enumerate(points)]
        nearest.append(min(candidates))
    indices = [index for _, index in nearest]
    increasing = all(right >= left for left, right in zip(indices, indices[1:]))
    decreasing = all(right <= left for left, right in zip(indices, indices[1:]))
    return {
        "shape_id": shape_id,
        "shape_variant_count": len(pattern["shape_ids"]),
        "monotonic": increasing or decreasing,
        "orientation": "forward" if increasing else ("reverse" if decreasing else "non-monotonic"),
        "max_stop_shape_m": max(distance for distance, _ in nearest),
        "nearest_indices": indices,
    }


def summary(zip_path: Path, routes, trips, by_trip, stops, calendar, calendar_dates, shapes, patterns):
    line_names = {row["route_short_name"] for row in routes.values()}
    all_times = [value for values in by_trip.values() for _, _, arrival, departure in values for value in (arrival, departure) if value]
    over_24_trip_ids = {
        trip_id
        for trip_id, values in by_trip.items()
        if any(gtfs_seconds(value) >= 86_400 for _, _, arrival, departure in values for value in (arrival, departure) if value)
    }
    services_by_route = defaultdict(set)
    for trip in trips.values():
        services_by_route[trip["route_id"]].add(trip["service_id"])
    print(json.dumps({
        "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "calendar_dates_present": bool(calendar_dates),
        "lines": len(line_names),
        "routes": len(routes),
        "trips": len(trips),
        "patterns": len(patterns),
        "stations": len(stops),
        "services": len(calendar),
        "stop_time_rows_madrid": sum(len(values) for values in by_trip.values()),
        "times_ge_24_values": sum(gtfs_seconds(value) >= 86_400 for value in all_times),
        "times_24_values": sum(86_400 <= gtfs_seconds(value) < 90_000 for value in all_times),
        "times_25_values": sum(90_000 <= gtfs_seconds(value) < 93_600 for value in all_times),
        "trips_with_ge_24": len(over_24_trip_ids),
        "maximum_time": max(all_times, key=gtfs_seconds),
        "orphan_trips": sum(trip_id not in by_trip for trip_id in trips),
        "missing_stops": len({sid for values in by_trip.values() for _, sid, _, _ in values} - stops.keys()),
        "missing_services": len({trip["service_id"] for trip in trips.values()} - calendar.keys()),
        "missing_shapes": len({trip["shape_id"] for trip in trips.values()} - shapes.keys()),
    }, indent=2, ensure_ascii=False))
    print("\nROUTES")
    for route_id, route in routes.items():
        route_patterns = [p for p in patterns if p["route_id"] == route_id]
        service_rows = [calendar[sid] for sid in services_by_route[route_id]]
        print("\t".join(map(str, [
            route["route_short_name"], route_id, compact(route["route_long_name"]),
            sum(p["trip_count"] for p in route_patterns), len(route_patterns), len(service_rows),
            min(row["start_date"] for row in service_rows), max(row["end_date"] for row in service_rows),
        ])))


def markdown_patterns(patterns, routes, stops, coverage_path: Path):
    with coverage_path.open(encoding="utf-8", newline="") as handle:
        coverage = {row["pattern_id"]: row for row in csv.DictReader(handle)}
    print("| Línea | `route_id` | Patrón | Sentido fuente | Viajes | Servicios | Secuencia real de estaciones | OSM declarado |")
    print("|---|---|---:|---|---:|---:|---|---|")
    current_route = None
    route_index = 0
    for pattern in patterns:
        route_id = pattern["route_id"]
        if route_id != current_route:
            current_route = route_id
            route_index = 0
        route_index += 1
        endpoint = f"{station_name(stops, pattern['stop_ids'][0])} → {station_name(stops, pattern['stop_ids'][-1])}"
        headsigns = ", ".join(f"{compact(name) or '∅'} ({count})" for name, count in pattern["headsigns"].most_common())
        sequence = " → ".join(f"`{sid}` {station_name(stops, sid)}" for sid in pattern["stop_ids"])
        canonical = "\0".join((route_id, *pattern["stop_ids"])).encode()
        pattern_id = f"gtfs-pattern:{hashlib.sha256(canonical).hexdigest()[:20]}"
        osm = coverage.get(pattern_id)
        osm_status = f"{osm['status']}" if osm else "AUSENTE"
        if osm and osm["relation_id"]:
            osm_status += f" (rel. {osm['relation_id']})"
        print(
            f"| {routes[route_id]['route_short_name']} | `{route_id}` | {route_index} | "
            f"{endpoint}; headsign {headsigns} | {pattern['trip_count']} | {len(pattern['service_ids'])} | "
            f"{sequence} | {osm_status} |"
        )


def markdown_routes(routes, trips, by_trip, calendar, patterns):
    all_service_ids = set(calendar)
    trips_by_route = defaultdict(list)
    for trip_id, trip in trips.items():
        trips_by_route[trip["route_id"]].append((trip_id, trip))
    print("| Línea | `route_id` | `route_long_name` crudo normalizado | Trips | Huérfanos | Patrones | Servicios |")
    print("|---|---|---|---:|---:|---:|---|")
    for route_id, route in routes.items():
        route_trips = trips_by_route[route_id]
        services = {trip["service_id"] for _, trip in route_trips}
        missing = sorted(all_service_ids - services)
        if len(services) == len(all_service_ids):
            service_text = "los 30 (`1023V`–`1052S`)"
        elif len(services) > 19:
            service_text = f"{len(services)}; todos salvo " + ", ".join(f"`{x}`" for x in missing)
        else:
            service_text = f"{len(services)}: " + ", ".join(f"`{x}`" for x in sorted(services))
        print(
            f"| {route['route_short_name']} | `{route_id}` | {compact(route['route_long_name']) or '∅'} | "
            f"{len(route_trips)} | {sum(trip_id not in by_trip for trip_id, _ in route_trips)} | "
            f"{sum(pattern['route_id'] == route_id for pattern in patterns)} | {service_text} |"
        )


def anomalies(patterns, routes, stops, shapes):
    exact = defaultdict(list)
    reverse = defaultdict(list)
    repeated = []
    backtracks = []
    long_hops = []
    shape_failures = []
    for index, pattern in enumerate(patterns, start=1):
        seq = pattern["stop_ids"]
        exact[seq].append(pattern["route_id"])
        reverse[min(seq, tuple(reversed(seq)))].append((pattern["route_id"], seq))
        if len(set(seq)) != len(seq):
            repeated.append((pattern["route_id"], seq))
        if any(a == c for a, _, c in zip(seq, seq[1:], seq[2:])):
            backtracks.append((pattern["route_id"], seq))
        for left, right in zip(seq, seq[1:]):
            a = (float(stops[left]["stop_lat"]), float(stops[left]["stop_lon"]))
            b = (float(stops[right]["stop_lat"]), float(stops[right]["stop_lon"]))
            distance = haversine_m(a, b)
            if distance > 20_000:
                long_hops.append((pattern["route_id"], left, right, round(distance)))
        geom = pattern_geometry(pattern, stops, shapes)
        if not geom["monotonic"] or geom["max_stop_shape_m"] > 1_000:
            shape_failures.append((pattern["route_id"], index, geom))
    print("EXACT_DUPLICATES")
    for seq, route_ids in exact.items():
        if len(set(route_ids)) > 1:
            print(sorted(set(route_ids)), " :: ", " -> ".join(seq))
    print("\nREPEATED_STOPS", len(repeated))
    print("BACKTRACK_A_B_A", len(backtracks))
    print("HOPS_OVER_20KM", long_hops)
    print("SHAPE_FAILURES", shape_failures)
    max_hop = max(
        (haversine_m(
            (float(stops[a]["stop_lat"]), float(stops[a]["stop_lon"])),
            (float(stops[b]["stop_lat"]), float(stops[b]["stop_lon"])),
        ), pattern["route_id"], a, b)
        for pattern in patterns for a, b in zip(pattern["stop_ids"], pattern["stop_ids"][1:])
    )
    print("MAX_HOP", max_hop)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("data/hito-03/replay/fomento_transit.zip"))
    parser.add_argument(
        "--coverage",
        type=Path,
        default=Path("docs/evidence/mp-018-corridor-coverage.csv"),
    )
    parser.add_argument("mode", choices=("summary", "routes", "patterns", "anomalies"))
    args = parser.parse_args()
    loaded = load(args.zip)
    patterns = build_patterns(*loaded[:3])
    if args.mode == "summary":
        summary(args.zip, *loaded, patterns)
    elif args.mode == "routes":
        markdown_routes(loaded[0], loaded[1], loaded[2], loaded[4], patterns)
    elif args.mode == "patterns":
        markdown_patterns(patterns, loaded[0], loaded[3], args.coverage)
    else:
        anomalies(patterns, loaded[0], loaded[3], loaded[6])


if __name__ == "__main__":
    main()
