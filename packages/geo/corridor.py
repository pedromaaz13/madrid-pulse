"""Corredor ferroviario continuo a partir de una relación OSM de ruta.

Encadena los ``ways`` de vía (``role=""``) en el orden declarado por la
relación, uniendo por nodo compartido en los extremos. No asume que el
orden de ``members`` sea correcto: si dos ``ways`` consecutivos no comparten
extremo, se registra como ``gap`` en vez de fabricar una unión inexistente.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from .geometry import PolylineProjector, Projection, haversine_m
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
    """Secuencia de ``node_id`` de TODOS los ``ways`` de vía, en el orden
    declarado por la relación. Solo para inspección/depuración: cuando hay
    huecos, NO representa un recorrido físico continuo — usar ``segments``
    para cualquier cálculo geométrico (proyección, longitud)."""
    polyline: tuple[tuple[float, float], ...]
    """``(lat, lon)`` de ``node_chain``, mismo orden e índice. Mismo aviso
    que ``node_chain``: no usar para proyección/longitud si hay huecos."""
    segments: tuple[tuple[tuple[float, float], ...], ...]
    """Tramos realmente continuos del corredor (sin fabricar unión a través
    de un hueco). Con ``gaps`` vacío, es una tupla de un único tramo igual
    a ``polyline``. Toda proyección/longitud se calcula sobre ``segments``,
    nunca interpolando entre dos tramos distintos."""
    gaps: tuple[ChainGap, ...]
    stop_node_ids: tuple[int, ...]
    """Nodos con ``role=stop`` en la relación, en el orden declarado."""

    @property
    def is_continuous(self) -> bool:
        return not self.gaps

    @cached_property
    def _segment_projectors(self) -> tuple[PolylineProjector, ...]:
        return tuple(PolylineProjector(segment) for segment in self.segments if len(segment) >= 2)

    def project_station(self, lat: float, lon: float) -> tuple[Projection, float]:
        """Proyecta una coordenada real sobre el corredor.

        Evalúa cada tramo continuo (``segments``) por separado y devuelve la
        proyección de distancia real mínima junto con su longitud de arco
        **local al tramo que la contiene** — nunca una distancia fabricada
        atravesando un hueco real entre dos tramos desconectados.
        """
        best: Projection | None = None
        best_arc = 0.0
        for projector in self._segment_projectors:
            candidate, arc = projector.project(lat, lon)
            if best is None or candidate.distance_m < best.distance_m:
                best, best_arc = candidate, arc
        if best is None:
            raise ValueError("el corredor no tiene ningún tramo geométrico válido")
        return best, best_arc


def build_corridor(geometry: RelationGeometry) -> Corridor:
    track_way_ids = [
        ref for (kind, ref, role) in geometry.member_refs if kind == "way" and role == TrackRole.TRACK
    ]
    stop_node_ids = tuple(
        ref for (kind, ref, role) in geometry.member_refs if kind == "node" and role == TrackRole.STOP
    )

    segments_nodes: list[list[int]] = []
    gaps: list[ChainGap] = []
    current: list[int] = []
    previous_end: int | None = None
    for index, way_id in enumerate(track_way_ids):
        way_nodes = geometry.ways[way_id]
        if previous_end is None:
            current = list(way_nodes)
        elif way_nodes[0] == previous_end:
            current.extend(way_nodes[1:])
        elif way_nodes[-1] == previous_end:
            current.extend(reversed(way_nodes[:-1]))
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
            segments_nodes.append(current)
            current = list(way_nodes)
        previous_end = current[-1] if current else None
    if current:
        segments_nodes.append(current)

    full_chain = tuple(node_id for segment in segments_nodes for node_id in segment)
    segments = tuple(
        tuple(geometry.nodes[node_id] for node_id in segment) for segment in segments_nodes
    )
    polyline = tuple(geometry.nodes[node_id] for node_id in full_chain)
    return Corridor(
        relation_id=geometry.relation_id,
        name=geometry.tags.get("name", ""),
        node_chain=full_chain,
        polyline=polyline,
        segments=segments,
        gaps=tuple(gaps),
        stop_node_ids=stop_node_ids,
    )


def corridor_length_m(corridor: Corridor) -> float:
    """Longitud real total: suma solo dentro de cada tramo continuo, nunca
    a través de un hueco entre tramos distintos."""
    total = 0.0
    for segment in corridor.segments:
        for (lat1, lon1), (lat2, lon2) in zip(segment, segment[1:]):
            total += haversine_m(lat1, lon1, lat2, lon2)
    return total
