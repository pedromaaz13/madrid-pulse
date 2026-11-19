"""Disambiguación de núcleo de Cercanías por prefijo numérico.

Verificado empíricamente en MP-003 (docs/research/MP-003-probe-findings.md §3)
cruzando coordenadas lat/lon reales, `routeId` de alerts.json y
`routes.txt`/`trips.txt` del GTFS estático. Ver ADR-0008/DEC-017: el código de
línea (p. ej. "C5") NO es único entre núcleos -- el prefijo de 2 cifras de
`route_id`/`trip_id`/`service_id` sí lo es.

No se añaden prefijos nuevos aquí sin verificarlos contra datos reales.
"""

from __future__ import annotations

import re

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

# Hallazgo real de MP-007 (colector contra el feed en vivo, no en las muestras
# más pequeñas de MP-003/MP-004): existen trip_id de trenes de refuerzo con el
# formato `SPECIAL_<núcleo>_<resto>` (ej. "SPECIAL_10_91567C2"), SIN prefijo
# numérico al inicio -- `trip_or_route_id[:2]` daba "SP", que no es un núcleo
# válido y violaba el `CHECK` de MP-006. Verificado contra el GTFS estático
# real (fomento_transit.zip, MP-003): "SPECIAL_10_91567C2" NO aparece en
# `trips.txt` -- es un refuerzo añadido dinámicamente, sin viaje programado
# correspondiente. El núcleo embebido tras "SPECIAL_" sigue siendo real y
# fiable (viene del propio feed, no se infiere).
_SPECIAL_TRIP_PATTERN = re.compile(r"^SPECIAL_(\d{2})_")


def nucleo_prefix(trip_or_route_id: str) -> str:
    """Prefijo de núcleo (2 primeras cifras) de un `trip_id` o `route_id` de Renfe.

    Admite tanto el formato estándar (`"10T0047C5"` -> `"10"`) como el de
    trenes de refuerzo (`"SPECIAL_10_91567C2"` -> `"10"`, ver nota arriba).
    No valida que el prefijo sea conocido -- usar `nucleo_name` para eso.
    """
    special_match = _SPECIAL_TRIP_PATTERN.match(trip_or_route_id)
    if special_match:
        return special_match.group(1)
    return trip_or_route_id[:2]


def nucleo_name(prefix: str) -> str:
    """Nombre del núcleo para un prefijo, o 'desconocido' si no está verificado."""
    return NUCLEOS.get(prefix, "desconocido")


def is_madrid(trip_or_route_id: str) -> bool:
    """True si el `trip_id`/`route_id` pertenece al núcleo de Madrid (prefijo "10")."""
    return nucleo_prefix(trip_or_route_id) == MADRID_PREFIX
