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
`ways` consecutivos no comparten extremo, se registra como `ChainGap` **y**
se cierra el tramo continuo en curso: `Corridor.segments` guarda cada tramo
real por separado, nunca uno fabricado que atraviese el hueco. (Hallazgo de
la revisión de Codex: una primera versión registraba el `ChainGap` pero
seguía concatenando ambos `ways` en una única `polyline`, de modo que
`project_station` devolvía una proyección fabricada sobre el hueco —
corregido, con test de regresión sobre un hueco sintético.) `polyline`/
`node_chain` se conservan solo para inspección; todo cálculo geométrico usa
`segments`.

`Corridor.project_station` proyecta una coordenada real (de una estación
GTFS, por ejemplo) sobre cada tramo continuo del corredor con distancia
Haversine real, sin depender de `shapely`/`pyproj`: la proyección
punto-segmento usa un plano local equirrectangular por consulta, suficiente
para el margen de error (metros) que exige un prototipo de corredor de
pocas decenas de km.

## Catálogo Madrid por patrón y sentido (MP-018)

`packages.geo.catalog` conserva `Corridor`/`build_corridor`/`ChainGap` como
primitivas y añade el índice que faltaba: cada entrada representa un patrón
GTFS completo, no una línea comercial. El GTFS real verificado no trae
`direction_id`; el sentido se identifica sin inventarlo mediante la secuencia
ordenada de paradas. `PatternIdentity.pattern_id` deriva de
`route_id + stop_ids`, y `direction_key` expone origen→destino para inspección.

`packages.geo.madrid` declara únicamente relaciones OSM descargadas y con
SHA-256 verificado. `build_madrid_corridor_catalog` recorre **todos** los
patrones de `packages.gtfs.catalog`, comprueba continuidad, distancia de cada
estación (umbral 150 m) y orden monótono antes de asignar un corredor. El resto
queda `pending`; una ambigüedad conocida queda `partial`. No se asigna por
parecido del nombre de línea.

Matriz del GTFS congelado de Hito 3 (`103` patrones / `12` líneas):

| Estado | Patrones | Significado operativo |
|---|---:|---|
| `validated` | 28 | C4 (5), C4a (8), C4b sentido Colmenar→Parla (3) y C5 (12); corredor continuo, paradas cercanas y en orden |
| `partial` | 3 | dos variantes C5 de 7 paradas sin relación propia (DEC-025) y una C4b de 14 paradas que omite Nuevos Ministerios |
| `pending` | 72 | no se descargó/verificó corredor para ese patrón y sentido; incluye el sentido Parla→Colmenar de C4b tras dos 502 reales de Overpass |

La tabla completa, con fuente, versión, estado y motivo por patrón, está en
`docs/evidence/mp-018-corridor-coverage.csv`. Se regenera de forma
reproducible (el ZIP oficial queda fuera de Git por DEC-023):

```sh
python3 -m packages.geo.tools.export_madrid_catalog \
  --gtfs data/hito-03/replay/fomento_transit.zip \
  --fixtures tests/fixtures \
  --out docs/evidence/mp-018-corridor-coverage.csv
```

### Contrato mínimo raw → map-matched

`CorridorCatalog.match_position` conserva siempre `raw_lat/raw_lon`. Si el
patrón está `validated`, devuelve `PositionMatch` con `projection`,
`progress_m`, `geometry_version` y `distance_from_raw_m` (el residuo real de
la proyección). En un corredor `partial`/`pending`, devuelve `RAW` sin
proyección fabricada; si el punto de origen falta, devuelve `UNLOCATED` y
mantiene las coordenadas como `None`. La posición de presentación
(`rendered`) y el contrato snapshot/API completo pertenecen a MP-019.

### C4 y vía compartida real

Las relaciones reales C4 descargadas se documentan en
`tests/fixtures/osm_c4_real/MANIFEST.md`. C4a está disponible en ambos
sentidos (`11332`/`9174510`) y C4b Colmenar→Parla en `9174511`; todas encadenan
sin huecos. `9174510` (C4a hacia Parla) y `9174511` (C4b hacia Parla)
comparten 77 IDs literales de `way` de vía OSM: confirma tronco físico común,
no solo estaciones compartidas en el GTFS.

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
  tiene relación OSM propia**. Su variante base de 6 estaciones (sin
  Atocha) es, confirmado por comparación literal de IDs, una subsecuencia
  **contigua** real de paradas de la ruta larga — no solo "proyecta en el
  mismo corredor". Una variante real distinta del mismo `route_id` (7
  estaciones, con Atocha antepuesta a Villaverde Alto) proyecta en orden
  monótono sobre el mismo corredor pero **no** es contigua: omite las 4
  paradas intermedias reales entre Atocha y Villaverde Alto (hallazgo de la
  revisión de Codex — "monótono" y "subsegmento contiguo" no son lo mismo,
  y se comprueban como afirmaciones separadas en los tests). En ningún caso
  se fabrica una geometría separada para la ruta corta.
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
