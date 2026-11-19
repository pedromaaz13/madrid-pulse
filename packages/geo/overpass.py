"""Cliente mínimo de Overpass API para relaciones de ruta ferroviaria.

Genérico: recibe el id de relación o una consulta por etiquetas (``ref`` +
``network``); no contiene el nombre de ninguna línea concreta en la lógica.
Solo ``urllib`` de la librería estándar, igual que ``services/collector``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
USER_AGENT = "madrid-pulse-geo/1.0 (prototype; contact: pedromaaz13@gmail.com)"


class OverpassError(RuntimeError):
    """La consulta a Overpass falló o devolvió una respuesta no válida."""


@dataclass(frozen=True)
class RelationGeometry:
    relation_id: int
    tags: Mapping[str, str]
    nodes: Mapping[int, tuple[float, float]]
    """``node_id -> (lat, lon)``, incluye los nodos de los ``ways`` recursados."""
    ways: Mapping[int, tuple[int, ...]]
    """``way_id -> (node_id, ...)`` en el orden real de la geometría fuente."""
    member_refs: tuple[tuple[str, int, str], ...]
    """``(tipo, ref, role)`` en el orden declarado por la relación."""


def fetch_relation_geometry(
    relation_id: int, *, endpoint: str = DEFAULT_ENDPOINT, timeout_s: float = 90.0
) -> RelationGeometry:
    """Descarga una relación de ruta con sus ``ways``/``nodes`` recursados.

    El endpoint público de Overpass es intermitentemente limitado por
    capacidad (observado en MP-011): un fallo de servidor (502/429) debe
    propagarse como :class:`OverpassError`, nunca interpretarse como "la
    relación no existe".
    """
    query = f"""
[out:json][timeout:60];
rel({relation_id});
out body;
>;
out skel qt;
"""
    payload = _post(query, endpoint=endpoint, timeout_s=timeout_s)
    elements = payload.get("elements", [])
    relation = next((element for element in elements if element["type"] == "relation"), None)
    if relation is None:
        raise OverpassError(f"la respuesta no contiene la relación {relation_id}")

    nodes = {
        element["id"]: (element["lat"], element["lon"])
        for element in elements
        if element["type"] == "node" and "lat" in element
    }
    ways = {
        element["id"]: tuple(element["nodes"])
        for element in elements
        if element["type"] == "way"
    }
    member_refs = tuple(
        (member["type"], member["ref"], member.get("role", ""))
        for member in relation.get("members", [])
    )
    return RelationGeometry(
        relation_id=relation_id,
        tags=relation.get("tags", {}),
        nodes=nodes,
        ways=ways,
        member_refs=member_refs,
    )


def find_route_relations(
    *, ref: str, network: str, endpoint: str = DEFAULT_ENDPOINT, timeout_s: float = 90.0
) -> tuple[dict, ...]:
    """Busca relaciones ``type=route`` por ``ref``/``network`` (sin geometría).

    Solo devuelve etiquetas: útil para descubrir qué relaciones direccionales
    componen una línea antes de pedir su geometría completa una a una.
    """
    query = f"""
[out:json][timeout:60];
relation["type"="route"]["ref"="{ref}"]["network"="{network}"];
out tags;
"""
    payload = _post(query, endpoint=endpoint, timeout_s=timeout_s)
    return tuple(
        {"id": element["id"], "tags": element.get("tags", {})}
        for element in payload.get("elements", [])
        if element["type"] == "relation"
    )


def load_relation_geometry_json(path: Path) -> RelationGeometry:
    """Carga una geometría congelada por ``tools/fetch_fixture.py``.

    Contraparte de lectura de ``fetch_relation_geometry``, para tests
    reproducibles sin depender de la disponibilidad en vivo de Overpass
    (observada como intermitente por capacidad durante MP-011).
    """
    payload = json.loads(path.read_text())
    return RelationGeometry(
        relation_id=payload["relation_id"],
        tags=payload["tags"],
        nodes={int(key): tuple(value) for key, value in payload["nodes"].items()},
        ways={int(key): tuple(value) for key, value in payload["ways"].items()},
        member_refs=tuple(tuple(item) for item in payload["member_refs"]),
    )


def _post(query: str, *, endpoint: str, timeout_s: float) -> dict:
    request = urllib.request.Request(
        endpoint,
        data=query.encode("utf-8"),
        headers={"Accept": "*/*", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read()
    except urllib.error.URLError as exc:
        raise OverpassError(f"fallo de red contra Overpass: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OverpassError(
            f"respuesta no JSON de Overpass (probable límite de capacidad): {body[:200]!r}"
        ) from exc
