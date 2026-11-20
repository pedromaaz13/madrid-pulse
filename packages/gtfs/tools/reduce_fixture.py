"""Reduce el GTFS oficial a un ejemplo real por patrón de paradas.

Uso:
  python -m packages.gtfs.tools.reduce_fixture SOURCE.zip DEST \
      --network-id 10 --short-name <nombre-corto>

No contiene nombres de línea: el alcance se pasa como configuración. Conserva
el primer trip lexicográfico de cada patrón observado y un trip representativo
por variante sin stop_times, además de todas sus dependencias.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

FILES = ("routes.txt", "trips.txt", "stops.txt", "stop_times.txt", "shapes.txt", "calendar.txt")


def _read(
    archive: ZipFile,
    name: str,
    *,
    keep: Callable[[dict[str, str]], bool] | None = None,
) -> tuple[list[str], list[dict[str, str]]]:
    import io

    with archive.open(name) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
        reader = csv.DictReader(text)
        fields = [(item or "").strip() for item in (reader.fieldnames or ())]
        rows = []
        for raw in reader:
            row = {(key or "").strip(): (value or "").strip() for key, value in raw.items()}
            if keep is None or keep(row):
                rows.append(row)
    return fields, rows


def reduce(source: Path, destination: Path, *, network_id: str, short_name: str) -> None:
    with ZipFile(source) as archive:
        route_fields, routes = _read(
            archive,
            "routes.txt",
            keep=lambda row: row["route_id"].startswith(network_id)
            and row["route_short_name"] == short_name,
        )
        route_ids = {row["route_id"] for row in routes}
        trip_fields, trips = _read(
            archive, "trips.txt", keep=lambda row: row["route_id"] in route_ids
        )
        trip_by_id = {row["trip_id"]: row for row in trips}
        stop_time_fields, relevant_times = _read(
            archive, "stop_times.txt", keep=lambda row: row["trip_id"] in trip_by_id
        )
        times_by_trip: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in relevant_times:
            times_by_trip[row["trip_id"]].append(row)

    representative: dict[tuple[str, tuple[str, ...]], str] = {}
    for trip in trips:
        pattern = tuple(
            row["stop_id"]
            for row in sorted(times_by_trip[trip["trip_id"]], key=lambda row: int(row["stop_sequence"]))
        )
        key = (trip["route_id"], pattern)
        representative[key] = min(representative.get(key, trip["trip_id"]), trip["trip_id"])
    selected_trip_ids = set(representative.values())
    selected_trips = [row for row in trips if row["trip_id"] in selected_trip_ids]
    selected_times = [row for row in relevant_times if row["trip_id"] in selected_trip_ids]
    stop_ids = {row["stop_id"] for row in selected_times}
    shape_ids = {row["shape_id"] for row in selected_trips}
    service_ids = {row["service_id"] for row in selected_trips}
    with ZipFile(source) as archive:
        stop_fields, stops = _read(
            archive, "stops.txt", keep=lambda row: row["stop_id"] in stop_ids
        )
        shape_fields, shapes = _read(
            archive, "shapes.txt", keep=lambda row: row["shape_id"] in shape_ids
        )
        calendar_fields, calendar = _read(
            archive, "calendar.txt", keep=lambda row: row["service_id"] in service_ids
        )
    selected = {
        "routes.txt": routes,
        "trips.txt": selected_trips,
        "stops.txt": stops,
        "stop_times.txt": selected_times,
        "shapes.txt": shapes,
        "calendar.txt": calendar,
    }
    fields = {
        "routes.txt": route_fields,
        "trips.txt": trip_fields,
        "stops.txt": stop_fields,
        "stop_times.txt": stop_time_fields,
        "shapes.txt": shape_fields,
        "calendar.txt": calendar_fields,
    }
    destination.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        with (destination / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields[name], lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected[name])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--network-id", required=True)
    parser.add_argument("--short-name", required=True)
    args = parser.parse_args()
    reduce(args.source, args.destination, network_id=args.network_id, short_name=args.short_name)


if __name__ == "__main__":
    main()
