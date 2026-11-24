# Fixture de geometría OSM real C4 Madrid (MP-018)

- Fuente: OpenStreetMap, vía Overpass API (`https://overpass-api.de/api/interpreter`).
- Descarga y verificación: `2026-11-22`.
- Licencia: Open Data Commons Open Database License 1.0 (`ODbL-1.0`). Esta
  fixture es una base de datos derivada y se distribuye bajo la misma licencia,
  separada de la licencia del código (DEC-024).
- Atribución: © OpenStreetMap contributors (`https://www.openstreetmap.org/copyright`).

Descubrimiento reproducible (las cuatro relaciones se publican con `ref=C-4`;
el ramal concreto está en `official_ref`):

```python
from packages.geo import find_route_relations
find_route_relations(ref="C-4", network="Cercanías Madrid")
```

Descarga reproducible:

```sh
python3 -m packages.geo.tools.fetch_fixture tests/fixtures/osm_c4_real \
  --relation 11332 --relation 9174510 --relation 9174511
```

Overpass devolvió un `HTTP 502 Bad Gateway` real al solicitar la cuarta
relación (`9174512`, C4b Parla→Colmenar) después de descargar las tres primeras.
Se reintentó y volvió a responder 502. No se interpreta como relación ausente:
ese sentido queda `pending` en la matriz, sin fabricar geometría.

## Relaciones descargadas

| Fichero | Relación | Sentido OSM | Nodos | `ways` | SHA-256 |
|---|---:|---|---:|---:|---|
| `relation_11332.json` | 11332 | C4a Parla → Alcobendas-S.S. de los Reyes | 880 | 92 | `0351d94fdb5fe70c7b61cf45e5550f6f115785ddcdadcd32f80b256b672a63d4` |
| `relation_9174510.json` | 9174510 | C4a Alcobendas-S.S. de los Reyes → Parla | 899 | 96 | `e057b86b2b28a2d99d2e85f91657c6f34cb6f07295758b42e8ed643a326f1439` |
| `relation_9174511.json` | 9174511 | C4b Colmenar Viejo → Parla | 1217 | 115 | `986a41bfdd843fe674700abc53fd23d0c9742367d28b4f1fe162798315610e60` |

Los tres corredores encadenan sin `ChainGap`. Las 8 variantes de patrón C4a
proyectan en su sentido correcto a menos de 50 m de la vía. La relación C4b
descargada cubre sus cuatro patrones Colmenar→Parla; el patrón real de 14
paradas omite Nuevos Ministerios entre Chamartín y Sol y queda `partial`, no
silenciosamente validado.

## Tramo compartido verificado

Las relaciones `9174510` (C4a Alcobendas→Parla) y `9174511` (C4b
Colmenar→Parla), ambas en el mismo sentido después de Cantoblanco, comparten
**77 IDs literales de `way` ferroviario OSM** (entre ellos `9870265`). Por
tanto comparten vía física en el tronco: no es una inferencia basada solo en
que el GTFS enumere las mismas estaciones. Las relaciones del sentido opuesto
usan la otra vía de la plataforma doble y no necesariamente comparten IDs de
`way`, como es esperable.
