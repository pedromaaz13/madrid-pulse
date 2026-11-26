"""Matemática geométrica mínima sobre coordenadas WGS84.

Sin dependencias de terceros (ni ``shapely`` ni ``pyproj``): la precisión
necesaria para proyectar una estación sobre un corredor ferroviario de
decenas de kilómetros no exige una librería de proyección completa. Se usa
Haversine para distancias reales y una proyección equirrectangular local
(escalada por ``cos(lat)``) solo para la proyección punto-segmento, válida
en el rango de error que exige esta tarea (metros, no centímetros).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import accumulate, pairwise

_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia real en metros entre dos puntos WGS84."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class Projection:
    segment_index: int
    """Índice del punto que abre el segmento del corredor más cercano."""
    fraction: float
    """Posición dentro del segmento, 0.0 (inicio) a 1.0 (fin)."""
    distance_m: float
    """Distancia real (Haversine) desde el punto de consulta a la proyección."""
    lat: float
    lon: float


def _local_xy(lat: float, lon: float, *, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """Proyección equirrectangular local en metros, centrada en ``origin``."""
    scale = math.cos(math.radians(origin_lat))
    x = math.radians(lon - origin_lon) * scale * _EARTH_RADIUS_M
    y = math.radians(lat - origin_lat) * _EARTH_RADIUS_M
    return x, y


def project_point_to_polyline(
    lat: float, lon: float, polyline: list[tuple[float, float]]
) -> Projection:
    """Proyección punto-polilínea real, por mínima distancia Haversine.

    ``polyline`` es una lista ``(lat, lon)`` ordenada. Se evalúa cada
    segmento en un plano local propio (origen en el punto de consulta) para
    evitar acumular distorsión de proyección en corredores largos.
    """
    if len(polyline) < 2:
        raise ValueError("la polilínea necesita al menos dos puntos")

    best: Projection | None = None
    qx, qy = 0.0, 0.0  # el punto de consulta es el origen de su propio plano local
    for index in range(len(polyline) - 1):
        a_lat, a_lon = polyline[index]
        b_lat, b_lon = polyline[index + 1]
        ax, ay = _local_xy(a_lat, a_lon, origin_lat=lat, origin_lon=lon)
        bx, by = _local_xy(b_lat, b_lon, origin_lat=lat, origin_lon=lon)
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            fraction = 0.0
        else:
            fraction = ((qx - ax) * dx + (qy - ay) * dy) / length_sq
            fraction = max(0.0, min(1.0, fraction))
        px, py = ax + fraction * dx, ay + fraction * dy
        distance = math.hypot(px - qx, py - qy)
        if best is None or distance < best.distance_m:
            proj_lat = a_lat + fraction * (b_lat - a_lat)
            proj_lon = a_lon + fraction * (b_lon - a_lon)
            best = Projection(
                segment_index=index,
                fraction=fraction,
                distance_m=distance,
                lat=proj_lat,
                lon=proj_lon,
            )
    assert best is not None
    return best


def arc_length_to(polyline: list[tuple[float, float]], projection: Projection) -> float:
    """Distancia real acumulada (m) desde el inicio del corredor hasta la proyección."""
    total = 0.0
    for index in range(projection.segment_index):
        lat1, lon1 = polyline[index]
        lat2, lon2 = polyline[index + 1]
        total += haversine_m(lat1, lon1, lat2, lon2)
    lat_a, lon_a = polyline[projection.segment_index]
    total += haversine_m(lat_a, lon_a, projection.lat, projection.lon)
    return total


class PolylineProjector:
    """Acota la búsqueda con cajas de segmentos contiguos e indexa el arco."""

    def __init__(self, points: tuple[tuple[float, float], ...]) -> None:
        self._points = points
        self._arc_m = tuple(accumulate(
            (haversine_m(*first, *second) for first, second in pairwise(points)), initial=0.0
        ))
        self._blocks = []
        block_size = 16
        for start in range(0, len(points) - 1, block_size):
            span = list(points[start:start + block_size + 1])
            latitudes, longitudes = zip(*span)
            self._blocks.append(
                (min(latitudes), max(latitudes), min(longitudes), max(longitudes), start, span)
            )

    def project(self, lat: float, lon: float) -> tuple[Projection, float]:
        candidates = []
        for south, north, west, east, start, span in self._blocks:
            # Misma métrica local que la proyección exacta. La caja contiene
            # todos los segmentos del bloque, de modo que su distancia es
            # una cota inferior, incluso cuando el GPS queda fuera de la vía.
            x, y = _local_xy(
                min(max(lat, south), north), min(max(lon, west), east),
                origin_lat=lat, origin_lon=lon,
            )
            candidates.append((math.hypot(x, y), start, span))
        best = None
        for lower_bound, start, span in sorted(candidates):
            if best is not None and lower_bound > best.distance_m + 1e-8:
                break  # margen de redondeo para no descartar empates
            local = project_point_to_polyline(lat, lon, span)
            index = start + local.segment_index
            if best is None or (local.distance_m, index) < (best.distance_m, best.segment_index):
                best = replace(local, segment_index=index)
        assert best is not None
        arc = self._arc_m[best.segment_index] + haversine_m(
            *self._points[best.segment_index], best.lat, best.lon
        )
        return best, arc


def point_at_arc_length(
    polyline: list[tuple[float, float]], distance_m: float
) -> tuple[float, float]:
    """Localiza un punto a una distancia acumulada sobre una polilínea.

    La distancia se limita a los extremos. Esta es la operación inversa de
    :func:`arc_length_to` que necesita el motor de movimiento para convertir
    progreso escalar de nuevo a una coordenada *map-matched*.
    """
    if len(polyline) < 2:
        raise ValueError("la polilínea necesita al menos dos puntos")
    remaining = max(0.0, distance_m)
    for (lat1, lon1), (lat2, lon2) in zip(polyline, polyline[1:]):
        segment_m = haversine_m(lat1, lon1, lat2, lon2)
        if segment_m == 0:
            continue
        if remaining <= segment_m:
            fraction = remaining / segment_m
            return (
                lat1 + fraction * (lat2 - lat1),
                lon1 + fraction * (lon2 - lon1),
            )
        remaining -= segment_m
    return polyline[-1]
