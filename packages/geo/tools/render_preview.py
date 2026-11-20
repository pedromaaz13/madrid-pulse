"""Genera un SVG de depuración: corredor OSM + estaciones GTFS proyectadas.

Uso:
  python -m packages.geo.tools.render_preview RELATION.json STOPS.txt STOP_ID[,STOP_ID...] OUT.html

No se guarda ningún render en el repositorio: es una herramienta para
reproducir la evidencia visual exigida por el criterio de aceptación de
MP-011 ("geometría renderizable y revisable visualmente"), no un artefacto
versionado.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from packages.geo import build_corridor, load_relation_geometry_json


def render(relation_path: Path, stops_path: Path, stop_ids: list[str], title: str) -> str:
    geometry = load_relation_geometry_json(relation_path)
    corridor = build_corridor(geometry)

    stops: dict[str, tuple[float, float, str]] = {}
    with stops_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            stops[row["stop_id"]] = (float(row["stop_lat"]), float(row["stop_lon"]), row["stop_name"])

    lats = [lat for lat, _ in corridor.polyline]
    lons = [lon for _, lon in corridor.polyline]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    width, height, pad = 1400, 1000, 60

    def to_xy(lat: float, lon: float) -> tuple[float, float]:
        x = pad + (lon - min_lon) / (max_lon - min_lon) * (width - 2 * pad)
        y = pad + (1 - (lat - min_lat) / (max_lat - min_lat)) * (height - 2 * pad)
        return x, y

    # Un <polyline> POR TRAMO continuo: si hubiera un hueco real entre dos
    # tramos, dibujar un único trazo con todos los puntos fabricaría
    # visualmente la misma unión inexistente que corrigió el hallazgo de
    # Codex en corridor.py (ChainGap registrado pero geometría fabricada).
    segment_paths = "".join(
        f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in (to_xy(lat, lon) for lat, lon in segment))}" '
        f'fill="none" stroke="#2c3e50" stroke-width="2.5"/>'
        for segment in corridor.segments
        if len(segment) >= 2
    )

    markers = []
    labels = []
    for stop_id in stop_ids:
        lat, lon, name = stops[stop_id]
        x, y = to_xy(lat, lon)
        markers.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#c0392b" stroke="white" stroke-width="1.5"/>')
        labels.append(f'<text x="{x + 7:.1f}" y="{y - 7:.1f}" font-size="11" font-family="sans-serif" fill="#222">{name}</text>')

    attribution = "Fuente: OpenStreetMap contributors (ODbL-1.0) · Renfe GTFS (CC BY 4.0) · Madrid Pulse, prototipo MP-011"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" fill="white"/>
<text x="{pad}" y="30" font-size="20" font-family="sans-serif" font-weight="bold">{title}</text>
<text x="{pad}" y="{height - 25}" font-size="12" font-family="sans-serif" fill="#555">{attribution}</text>
<polyline points="{path_points}" fill="none" stroke="#2c3e50" stroke-width="2.5"/>
{"".join(markers)}
{"".join(labels)}
</svg>"""
    return f"<!doctype html><html><body style='margin:0'>{svg}</body></html>"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("relation_json", type=Path)
    parser.add_argument("stops_txt", type=Path)
    parser.add_argument("stop_ids", help="lista de stop_id separada por comas, en orden")
    parser.add_argument("out_html", type=Path)
    parser.add_argument("--title", default="Madrid Pulse — corredor OSM + estaciones GTFS")
    args = parser.parse_args()

    html = render(args.relation_json, args.stops_txt, args.stop_ids.split(","), args.title)
    args.out_html.write_text(html)
    print(f"escrito {args.out_html} ({len(html)} bytes) — abrir en un navegador para inspeccionar")


if __name__ == "__main__":
    main()
