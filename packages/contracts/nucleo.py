"""Disambiguación de núcleo de Cercanías por prefijo numérico.

Verificado empíricamente en MP-003 (docs/research/MP-003-probe-findings.md §3)
cruzando coordenadas lat/lon reales, `routeId` de alerts.json y
`routes.txt`/`trips.txt` del GTFS estático. Ver ADR-0008/DEC-017: el código de
línea (p. ej. "C5") NO es único entre núcleos -- el prefijo de 2 cifras de
`route_id`/`trip_id`/`service_id` sí lo es.

No se añaden prefijos nuevos aquí sin verificarlos contra datos reales.
"""

from __future__ import annotations

NUCLEOS: dict[str, str] = {
    "10": "Madrid",
    "20": "Asturias",
    "30": "Andalucía",
    "31": "Andalucía",
    "32": "Andalucía",
    "40": "Comunidad Valenciana / Murcia",
    "41": "Comunidad Valenciana / Murcia",
    "45": "Comunidad Valenciana / Murcia",
    "46": "Galicia / Cantabria",
    "47": "Galicia / Cantabria",
    "51": "Cataluña",
    "60": "País Vasco / Cantabria",
    "61": "País Vasco / Cantabria",
    "62": "País Vasco / Cantabria",
    "70": "Navarra",
}

MADRID_PREFIX = "10"


def nucleo_prefix(trip_or_route_id: str) -> str:
    """Prefijo de núcleo (2 primeras cifras) de un `trip_id` o `route_id` de Renfe.

    No valida que el prefijo sea conocido -- usar `nucleo_name` para eso.
    """
    return trip_or_route_id[:2]


def nucleo_name(prefix: str) -> str:
    """Nombre del núcleo para un prefijo, o 'desconocido' si no está verificado."""
    return NUCLEOS.get(prefix, "desconocido")


def is_madrid(trip_or_route_id: str) -> bool:
    """True si el `trip_id`/`route_id` pertenece al núcleo de Madrid (prefijo "10")."""
    return nucleo_prefix(trip_or_route_id) == MADRID_PREFIX
