"""Corredor ferroviario continuo a partir de una relación OSM de ruta.

Encadena los ``ways`` de vía (``role=""``) en el orden declarado por la
relación, uniendo por nodo compartido en los extremos. No asume que el
orden de ``members`` sea correcto: si dos ``ways`` consecutivos no comparten
extremo, se registra como ``gap`` en vez de fabricar una unión inexistente.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import Projection, arc_length_to, haversine_m, project_point_to_polyline
from .overpass import RelationGeometry


class TrackRole:
    TRACK = ""
    STOP = "stop"
    PLATFORM = "platform"


@dataclass(frozen=True)
class ChainGap:
    """Dos ``ways`` de vía consecutivos en la relación no comparten extremo."""

    member_index: int
    way_id: int
    previous_end_node: int | None
    way_start_node: int
    way_end_node: int


@dataclass(frozen=True)
class Corridor:
    relation_id: int
    name: str
    node_chain: tuple[int, ...]
    """Secuencia de ``node_id`` del corredor, en el orden real de la vía."""
    polyline: tuple[tuple[float, float], ...]
    """``(lat, lon)`` de ``node_chain``, mismo orden e índice."""
    gaps: tuple[ChainGap, ...]
    stop_node_ids: tuple[int, ...]
    """Nodos con ``role=stop`` en la relación, en el orden declarado."""

    @property
    def is_continuous(self) -> bool:
        return not self.gaps

    def project_station(self, lat: float, lon: float) -> tuple[Projection, float]:
        """Proyecta una coordenada real sobre el corredor.

        Devuelve la proyección y su posición en metros desde el inicio del
        corredor (longitud de arco), útil para comprobar que el orden de
        estaciones de un GTFS coincide con el orden real de la vía.
        """
        projection = project_point_to_polyline(lat, lon, list(self.polyline))
        return projection, arc_length_to(list(self.polyline), projection)


def build_corridor(geometry: RelationGeometry) -> Corridor:
    track_way_ids = [
        ref for (kind, ref, role) in geometry.member_refs if kind == "way" and role == TrackRole.TRACK
    ]
    stop_node_ids = tuple(
        ref for (kind, ref, role) in geometry.member_refs if kind == "node" and role == TrackRole.STOP
    )

    chain: list[int] = []
    gaps: list[ChainGap] = []
    previous_end: int | None = None
    for index, way_id in enumerate(track_way_ids):
        way_nodes = geometry.ways[way_id]
        if previous_end is None:
            chain.extend(way_nodes)
        elif way_nodes[0] == previous_end:
            chain.extend(way_nodes[1:])
        elif way_nodes[-1] == previous_end:
            chain.extend(reversed(way_nodes[:-1]))
        else:
            gaps.append(
                ChainGap(
                    member_index=index,
                    way_id=way_id,
                    previous_end_node=previous_end,
                    way_start_node=way_nodes[0],
                    way_end_node=way_nodes[-1],
                )
            )
            chain.extend(way_nodes)
        previous_end = chain[-1] if chain else None

    polyline = tuple(geometry.nodes[node_id] for node_id in chain)
    return Corridor(
        relation_id=geometry.relation_id,
        name=geometry.tags.get("name", ""),
        node_chain=tuple(chain),
        polyline=polyline,
        gaps=tuple(gaps),
        stop_node_ids=stop_node_ids,
    )


def corridor_length_m(corridor: Corridor) -> float:
    total = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(corridor.polyline, corridor.polyline[1:]):
        total += haversine_m(lat1, lon1, lat2, lon2)
    return total
