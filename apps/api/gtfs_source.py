"""Carga de topología/geometría en memoria, una sola vez por proceso."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from packages.geo import Corridor, build_corridor, load_relation_geometry_json
from packages.gtfs import Topology, load_feed
from packages.movement import MovementEngine

from .config import ApiConfig


@dataclass(frozen=True)
class LoadedNetwork:
    topology: Topology
    corridor: Corridor
    engine: MovementEngine
    corridor_network_id: str
    corridor_line_id: str
    mode: str
    gtfs_version: str
    gtfs_valid_from: date
    gtfs_valid_until: date


def _source_version(source: Path) -> str:
    digest = hashlib.sha256()
    if source.is_file():
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        for path in sorted(item for item in source.iterdir() if item.is_file()):
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def load_network(config: ApiConfig) -> LoadedNetwork:
    if config.mode not in {"live", "replay"}:
        raise ValueError("MADRID_PULSE_MODE debe ser 'live' o 'replay'")
    source = config.gtfs_fixture_dir.resolve()
    fixture_root = (Path(__file__).resolve().parents[2] / "tests" / "fixtures").resolve()
    if config.mode == "live" and source.is_relative_to(fixture_root):
        raise ValueError(
            "modo live no admite fixtures: define MADRID_PULSE_GTFS_SOURCE con el ZIP oficial"
        )
    topology = load_feed(
        config.gtfs_fixture_dir, network_id=config.network_id, short_name=config.short_name
    )
    geometry = load_relation_geometry_json(config.osm_relation_path)
    corridor = build_corridor(geometry)
    engine = MovementEngine(topology, corridor)
    parse_date = lambda value: datetime.strptime(value, "%Y%m%d").date()  # noqa: E731
    valid_from = min(parse_date(item.start_date) for item in topology.calendar)
    valid_until = max(parse_date(item.end_date) for item in topology.calendar)
    madrid_today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    if config.mode == "live" and not (valid_from <= madrid_today <= valid_until):
        raise ValueError(
            f"GTFS fuera de vigencia para live: {valid_from.isoformat()}..{valid_until.isoformat()}"
        )
    return LoadedNetwork(
        topology=topology,
        corridor=corridor,
        engine=engine,
        corridor_network_id=config.network_id,
        corridor_line_id=config.short_name,
        mode=config.mode,
        gtfs_version=_source_version(config.gtfs_fixture_dir),
        gtfs_valid_from=valid_from,
        gtfs_valid_until=valid_until,
    )
