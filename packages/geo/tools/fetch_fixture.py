"""Descarga y congela una fixture real de geometría OSM para tests.

Uso:
  python -m packages.geo.tools.fetch_fixture DEST --relation ID [--relation ID ...]

No contiene nombres de línea: los ids de relación son configuración pasada
por quien invoca el script (ver ``docs/STATUS.md``/``MANIFEST.md`` para los
usados en MP-011), no literales embebidos en la lógica de este módulo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.geo.overpass import fetch_relation_geometry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--relation", type=int, action="append", required=True, dest="relations")
    args = parser.parse_args()

    args.dest.mkdir(parents=True, exist_ok=True)
    for relation_id in args.relations:
        geometry = fetch_relation_geometry(relation_id)
        payload = {
            "relation_id": geometry.relation_id,
            "tags": dict(geometry.tags),
            "nodes": {str(key): list(value) for key, value in geometry.nodes.items()},
            "ways": {str(key): list(value) for key, value in geometry.ways.items()},
            "member_refs": [list(item) for item in geometry.member_refs],
        }
        out_path = args.dest / f"relation_{relation_id}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        print(f"{out_path}: {len(geometry.nodes)} nodos, {len(geometry.ways)} ways")


if __name__ == "__main__":
    main()
