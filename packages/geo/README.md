# packages/geo

Geometría ferroviaria derivada de OpenStreetMap (`ODbL-1.0`). El motor de
movimiento (MP-012) vive en otro módulo — ver `docs/ARCHITECTURE.md`. **No se
copia la implementación de Via Península (AGPL-3.0)** — ver
`docs/adr/0006-licensing-policy.md`.

## Qué resuelve este paquete

OSM modela cada línea de Cercanías como una relación `type=route` por
sentido, agrupadas en un `route_master`. El parser es genérico: recibe un id
de relación o una consulta `ref`/`network`; ningún nombre de línea está
embebido en la lógica.

```python
from pathlib import Path
from packages.geo import load_relation_geometry_json, build_corridor

geometry = load_relation_geometry_json(Path("tests/fixtures/osm_c5_real/relation_3418150.json"))
corridor = build_corridor(geometry)
assert corridor.is_continuous  # encadena 90 "ways" de vía sin huecos

projection, arc_m = corridor.project_station(lat=40.3502269, lon=-3.8317018)  # Alcorcón
```

`build_corridor` encadena los `ways` con `role=""` (vía) en el orden
declarado por la relación, uniendo por nodo extremo compartido. Si dos
`ways` consecutivos no comparten extremo, se registra como `ChainGap` en vez
de fabricar una unión inexistente — ningún hueco real se oculta.

`Corridor.project_station` proyecta una coordenada real (de una estación
GTFS, por ejemplo) sobre la polilínea del corredor con distancia Haversine
real, sin depender de `shapely`/`pyproj`: la proyección punto-segmento usa un
plano local equirrectangular por consulta, suficiente para el margen de
error (metros) que exige un prototipo de corredor de pocas decenas de km.

## Fuente real y hallazgos de MP-011

Relación OSM `11331` ("Humanes → Atocha → Móstoles-El Soto") y sus tres
contrapartes direccionales (`3418148`, `3418149`, `3418150`), agrupadas por
el `route_master` `3418151` ("Móstoles-El Soto ⇄ Atocha ⇄ Fuenlabrada ⇄
Humanes"), `ref=C-5`, `network=Cercanías Madrid`. Fuente, fecha y checksums
en `tests/fixtures/osm_c5_real/MANIFEST.md` (DEC-024, ODbL).

- Las 23 estaciones reales de la ruta larga (GTFS `10T0017C5`/`10T0018C5`)
  proyectan de forma monótona sobre el corredor OSM correspondiente, con una
  distancia máxima de 63,7 m a la vía — compatible con el desplazamiento
  real del andén respecto al eje de la vía, no un error de correspondencia.
- La ruta corta (`10T0047C5`/`10T0048C5`, Villaverde Alto↔Fuenlabrada) **no
  tiene relación OSM propia**: sus estaciones son, en el orden real del
  GTFS, un subsegmento contiguo de la misma vía que usa la ruta larga —
  confirmado proyectando sobre el mismo corredor en vez de inventar una
  geometría separada.
- El `route_master` también agrupa `3418148`/`3418149` ("Fuenlabrada →
  Atocha → Móstoles-El Soto" y su inversa): topológicamente son la ruta
  larga truncada en Fuenlabrada (22 estaciones en vez de 23, sin llegar a
  Humanes). **Ninguna de las dos coincide con el patrón de 6 estaciones de
  la ruta corta real del GTFS** — quedan como una tercera variante real
  documentada, no usada por este prototipo porque MP-010 no encontró ningún
  `trip` con ese patrón exacto en el feed vivo.
- `10T0035C5` (8 `trips` sin `stop_times` en MP-010, huérfano de fuente) no
  se puede validar geométricamente — no se fabrica un recorrido para él.
- Los `ways` de vía llevan `usage=main` (30) o `usage=branch` (60): parte
  del corredor es trazado troncal (previsiblemente compartido con otras
  líneas de Cercanías por las estaciones Atocha/Méndez Álvaro) y parte es
  ramal específico de esta línea. No se verificó aquí qué otras líneas
  comparten exactamente el tramo troncal — queda como pregunta abierta para
  MP-012/Hito 3, no una afirmación sin evidencia.
- "C5" colisiona también en OSM entre núcleos distintos (`ref=C5` en
  Cercanías Asturias, Sevilla, Cantabria y Valencia, además del `ref=C-5` de
  Madrid) — el mismo patrón ya documentado en ADR-0008/DEC-017 para el GTFS
  de Renfe, ahora confirmado también en la fuente OSM.

## Evidencia visual

`packages/geo/tools/render_preview.py` genera un SVG de depuración
(corredor + estaciones proyectadas) sin guardar ningún render en el repo:

```sh
python3 -m packages.geo.tools.render_preview \
  tests/fixtures/osm_c5_real/relation_3418150.json \
  tests/fixtures/gtfs_c5_real/stops.txt \
  35607,35606,35610,35605,35604,35603,35602,35601,35600,35608,35609,18000,18003,35702,35703,35704,37001,35009,35001,35011,35010,35002,35012 \
  /tmp/corredor.html
```

Revisado en MP-011 abriendo el resultado en un navegador real (Chrome
DevTools MCP, captura de pantalla completa): la forma característica de la
C5 (ramal Humanes/Fuenlabrada confluyendo en Villaverde Alto, tronco hasta
Atocha/Embajadores, bajada por Aluche hacia Móstoles) es reconocible y las
23 estaciones caen exactamente sobre la vía, sin saltos ni estaciones
descolgadas del trazado.

## Disponibilidad de Overpass API

El endpoint público (`overpass-api.de`) devolvió `502 Gateway Timeout` por
capacidad en varios intentos reales durante esta tarea; los reintentos con
una breve espera tuvieron éxito. `fetch_relation_geometry` propaga esos
fallos como `OverpassError` en vez de interpretarlos como "la relación no
existe". Los tests usan la fixture congelada, no la red en vivo.
