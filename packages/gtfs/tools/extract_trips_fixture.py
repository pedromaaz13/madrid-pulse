"""Extrae del GTFS oficial una fixture real con los `trip_id` indicados.

Uso:
  python -m packages.gtfs.tools.extract_trips_fixture SOURCE.zip DEST TRIP_ID [TRIP_ID ...]

Complementa `reduce_fixture`, que selecciona un representante por patrón de
paradas: aquí la selección la decide quien llama, porque hay casos concretos
—una circulación con horas `24:xx`, un refuerzo, una variante problemática—
que no son el primer representante lexicográfico de su patrón y que aun así
hay que poder versionar como dato real para una prueba de regresión.

No contiene ningún identificador de línea ni de viaje: los `trip_id` son
argumentos, igual que `reduce_fixture` recibe la red y el nombre corto como
configuración (ADR-0011). Conserva todas las dependencias necesarias para que
`packages.gtfs.load_feed` parsee el resultado: rutas, paradas, horarios,
shapes y calendarios realmente referenciados, sin inventar ninguna fila.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from zipfile import ZipFile

from .reduce_fixture import FILES, _read


def extract(source: Path, destination: Path, trip_ids: list[str]) -> dict[str, int]:
    wanted = set(trip_ids)
    with ZipFile(source) as archive:
        trip_fields, trips = _read(
            archive, "trips.txt", keep=lambda row: row["trip_id"] in wanted
        )
        found = {row["trip_id"] for row in trips}
        missing = sorted(wanted - found)
        if missing:
            raise SystemExit(f"trip_id no encontrados en {source}: {missing}")
        route_ids = {row["route_id"] for row in trips}
        shape_ids = {row["shape_id"] for row in trips}
        service_ids = {row["service_id"] for row in trips}
        stop_time_fields, times = _read(
            archive, "stop_times.txt", keep=lambda row: row["trip_id"] in wanted
        )
        stop_ids = {row["stop_id"] for row in times}
        route_fields, routes = _read(
            archive, "routes.txt", keep=lambda row: row["route_id"] in route_ids
        )
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
        "trips.txt": trips,
        "stops.txt": stops,
        "stop_times.txt": times,
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
    return {name: len(rows) for name, rows in selected.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("trip_ids", nargs="+")
    args = parser.parse_args()
    counts = extract(args.source, args.destination, args.trip_ids)
    for name, count in counts.items():
        print(f"{name}: {count} filas")


if __name__ == "__main__":
    main()
