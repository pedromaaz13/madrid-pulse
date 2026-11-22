"""Carga de topología/geometría/catálogos en memoria, una sola vez por proceso.

Todo lo que vive aquí es **catálogo**: inmutable para el proceso y versionado
(`gtfs_version`, `geometry_catalog_version`). El estado operativo -- lo que
cambia con cada sondeo -- nunca se guarda aquí; se lee de PostgreSQL en cada
peticion. Esa separación es la mitad de ADR-0014: el catálogo es cacheable y el
snapshot es ligero.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from packages.geo import (
    Corridor,
    CorridorCatalog,
    CorridorCoverage,
    build_corridor,
    build_madrid_corridor_catalog,
    load_relation_geometry_json,
)
from packages.gtfs import Catalog as GtfsCatalog
from packages.gtfs import Topology, build_catalog, load_feed
from packages.movement import MovementEngine, TripSchedule

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
    catalog: GtfsCatalog
    corridor_catalog: CorridorCatalog
    geometry_catalog_version: str
    catalog_version: str
    """ETag del catálogo completo: cambia si cambia el GTFS **o** la geometría."""

    _engines: dict[str, MovementEngine] = field(default_factory=dict, repr=False)
    _schedule_caches: dict[str, dict[str, TripSchedule]] = field(
        default_factory=dict, repr=False
    )
    _catalog_json: dict[str, bytes] = field(default_factory=dict, repr=False)
    """Payload del catálogo ya serializado, memoizado por `catalog_version`.

    Medido en MP-019: `/api/v1/catalog` no toca PostgreSQL, pero serializar la
    geometría real (79 KB con la fixture C5, 352 KB con el núcleo completo)
    costaba ~124 ms de p50 en **cada** petición. El contenido es inmutable por
    proceso por definición -- cambia solo si cambia `catalog_version`, y
    entonces el proceso ya cargó otro catálogo -- así que cachearlo no puede
    servir un dato viejo rotulado como nuevo.
    """

    _board_indexes: dict[date, dict[str, tuple]] = field(default_factory=dict, repr=False)
    """Índice de llamadas programadas por estación, memoizado por fecha de
    servicio. Es catálogo derivado (depende solo del GTFS cargado), no estado
    operativo: ninguna observación ni retraso entra aquí."""

    def engine_for(self, coverage: CorridorCoverage) -> MovementEngine | None:
        """Motor de MP-012 asociado al corredor de un patrón validado.

        Uno por `geometry_version`, no uno por patrón ni por vehículo: dos
        patrones que comparten relación OSM comparten motor y caché de
        horarios. Un patrón sin corredor validado devuelve `None` -- la capa
        de snapshot publica entonces `raw` etiquetado o `unlocated`, nunca una
        posición proyectada sobre un corredor ajeno.
        """
        if not coverage.can_map_match or coverage.geometry_version is None:
            return None
        assert coverage.corridor is not None
        if not coverage.corridor.is_continuous:
            return None
        existing = self._engines.get(coverage.geometry_version)
        if existing is not None:
            return existing
        cache = self._schedule_caches.setdefault(coverage.geometry_version, {})
        engine = MovementEngine(self.topology, coverage.corridor, schedule_cache=cache)
        self._engines[coverage.geometry_version] = engine
        return engine


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
    # `short_name` vacío = núcleo completo (MP-019): el snapshot de toda la red
    # de Cercanías Madrid necesita las 12 líneas, no una sola. Se conserva el
    # filtro por línea para el piloto/tests y se sigue leyendo de configuración,
    # nunca de un literal en el código (ADR-0011).
    topology = load_feed(
        config.gtfs_fixture_dir,
        network_id=config.network_id,
        short_name=config.short_name or None,
    )
    geometry = load_relation_geometry_json(config.osm_relation_path)
    corridor = build_corridor(geometry)
    engine = MovementEngine(topology, corridor, schedule_cache={})
    parse_date = lambda value: datetime.strptime(value, "%Y%m%d").date()  # noqa: E731
    valid_from = min(parse_date(item.start_date) for item in topology.calendar)
    valid_until = max(parse_date(item.end_date) for item in topology.calendar)
    madrid_today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    if config.mode == "live" and not (valid_from <= madrid_today <= valid_until):
        raise ValueError(
            f"GTFS fuera de vigencia para live: {valid_from.isoformat()}..{valid_until.isoformat()}"
        )
    gtfs_version = _source_version(config.gtfs_fixture_dir)
    catalog = build_catalog(topology, gtfs_version=gtfs_version)
    corridor_catalog = build_madrid_corridor_catalog(
        catalog, topology, fixtures_root=config.geometry_fixtures_root
    )
    # El CSV de cobertura de MP-018 incluye `geometry_version` de cada patrón,
    # así que su hash cambia ante cualquier cambio real de geometría o de
    # estado de cobertura; no se inventa un número de versión manual.
    geometry_catalog_version = "sha256:" + hashlib.sha256(
        corridor_catalog.to_csv().encode()
    ).hexdigest()
    catalog_version = "sha256:" + hashlib.sha256(
        f"{gtfs_version}\0{geometry_catalog_version}".encode()
    ).hexdigest()
    return LoadedNetwork(
        topology=topology,
        corridor=corridor,
        engine=engine,
        corridor_network_id=config.network_id,
        corridor_line_id=config.short_name,
        mode=config.mode,
        gtfs_version=gtfs_version,
        gtfs_valid_from=valid_from,
        gtfs_valid_until=valid_until,
        catalog=catalog,
        corridor_catalog=corridor_catalog,
        geometry_catalog_version=geometry_catalog_version,
        catalog_version=catalog_version,
    )
