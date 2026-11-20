"""Carga de topología/geometría en memoria, una sola vez por proceso."""

from __future__ import annotations

from dataclasses import dataclass

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


def load_network(config: ApiConfig) -> LoadedNetwork:
    topology = load_feed(
        config.gtfs_fixture_dir, network_id=config.network_id, short_name=config.short_name
    )
    geometry = load_relation_geometry_json(config.osm_relation_path)
    corridor = build_corridor(geometry)
    engine = MovementEngine(topology, corridor)
    return LoadedNetwork(
        topology=topology,
        corridor=corridor,
        engine=engine,
        corridor_network_id=config.network_id,
        corridor_line_id=config.short_name,
    )
