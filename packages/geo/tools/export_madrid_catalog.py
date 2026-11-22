"""Exporta la matriz MP-018 desde un GTFS oficial y fixtures OSM verificadas."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from packages.geo.madrid import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtfs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    digest = hashlib.sha256(args.gtfs.read_bytes()).hexdigest()
    topology = load_feed(args.gtfs, network_id="10")
    gtfs_catalog = build_catalog(topology, gtfs_version=f"sha256:{digest}")
    catalog = build_madrid_corridor_catalog(
        gtfs_catalog, topology, fixtures_root=args.fixtures
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(catalog.to_csv(), encoding="utf-8")
    print(f"{args.out}: {len(catalog.entries)} patrones")


if __name__ == "__main__":
    main()
