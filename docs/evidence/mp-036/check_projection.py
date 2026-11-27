"""Comprueba la proyección indexada frente al recorrido exhaustivo anterior."""

from pathlib import Path
from random import Random

from packages.geo import build_corridor, load_relation_geometry_json
from packages.geo.geometry import arc_length_to, project_point_to_polyline

fix = Path("tests/fixtures")
rng = Random(36)
count = 0
for line in ("osm_c4_real", "osm_c5_real"):
    for path in sorted((fix / line).glob("relation_*.json")):
        corridor = build_corridor(load_relation_geometry_json(path))
        segments = [list(points) for points in corridor.segments if len(points) >= 2]
        for i in range(100):
            lat, lon = rng.choice(corridor.polyline)
            if i % 2:
                lat += rng.uniform(-0.05, 0.05)
                lon += rng.uniform(-0.05, 0.05)
            options = [(project_point_to_polyline(lat, lon, points), points) for points in segments]
            expected, points = min(options, key=lambda item: item[0].distance_m)
            assert corridor.project_station(lat, lon) == (expected, arc_length_to(points, expected)), (
                path, i,
            )
            count += 1
print(f"{count} proyecciones idénticas al recorrido exhaustivo")
