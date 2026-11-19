# Fixture de geometría OSM real C5 Madrid (MP-011)

- Fuente: OpenStreetMap, vía Overpass API (`https://overpass-api.de/api/interpreter`).
- Descarga: `2026-11-19`.
- Licencia: Open Data Commons Open Database License 1.0 (`ODbL-1.0`). Esta
  fixture es una base de datos derivada en el sentido de la ODbL — se
  distribuye bajo la misma licencia con atribución, independientemente de la
  licencia de código del repositorio (DEC-002, pendiente; ver DEC-024).
- Atribución: © OpenStreetMap contributors (`https://www.openstreetmap.org/copyright`).

Comando reproducible (el id de relación es configuración, no lógica):

```sh
python3 -m packages.geo.tools.fetch_fixture tests/fixtures/osm_c5_real \
  --relation 11331 --relation 3418148 --relation 3418149 --relation 3418150
```

## Relaciones descargadas

Las cuatro relaciones direccionales de `ref=C-5`/`network=Cercanías Madrid`,
agrupadas por el `route_master` `3418151` ("Móstoles-El Soto ⇄ Atocha ⇄
Fuenlabrada ⇄ Humanes") que no se descarga aquí porque no aporta geometría
propia (solo agrupa a las cuatro siguientes):

| Fichero | Relación | Nombre OSM | Nodos | `ways` |
|---|---:|---|---:|---:|
| `relation_11331.json` | 11331 | Tren C-5: Humanes → Atocha → Móstoles-El Soto | 753 | 106 |
| `relation_3418148.json` | 3418148 | Tren C-5: Fuenlabrada → Atocha → Móstoles-El Soto | 713 | 102 |
| `relation_3418149.json` | 3418149 | Tren C-5: Móstoles-El Soto → Atocha → Fuenlabrada | 760 | 94 |
| `relation_3418150.json` | 3418150 | Tren C-5: Móstoles-El Soto → Atocha → Humanes | 803 | 98 |

`ways` incluye tanto vía (`role=""`, 80-90 por relación) como andenes
(`role="platform"`, hasta 16 por relación); la geometría del corredor solo
encadena los de vía.

## Hallazgos preservados (ver también `packages/geo/README.md`)

- Las cuatro relaciones encadenan sin huecos (`ChainGap` vacío): sus `ways`
  de vía comparten extremo en el orden exacto declarado por la relación.
- Las 23 estaciones reales de C5 Madrid (ver `tests/fixtures/gtfs_c5_real/`)
  proyectan en orden monótono sobre su corredor correspondiente, a una
  distancia máxima real de 63,7 m del eje de vía.
- La ruta corta del GTFS (`10T0047C5`/`10T0048C5`, 6 estaciones) no tiene
  relación OSM dedicada: es un subsegmento contiguo real de la misma vía que
  usa la ruta larga, confirmado por proyección, no asumido.
- `3418148`/`3418149` ("Fuenlabrada → Atocha → Móstoles-El Soto") son la
  ruta larga truncada en Fuenlabrada (22 estaciones, sin llegar a Humanes) —
  no coinciden con el patrón de 6 estaciones de la ruta corta real; quedan
  como una variante documentada, no usada por el prototipo.
- `usage=main` en 30 `ways` de vía y `usage=branch` en 60: parte del
  corredor es troncal (uso potencialmente compartido con otras líneas de
  Cercanías), parte es ramal específico de C5. No verificado qué otras
  líneas comparten el tramo troncal — pregunta abierta, no una afirmación.
- "C5"/"C-5" existe en OSM como `ref` de líneas de Cercanías de Asturias,
  Sevilla, Cantabria y Valencia, además de Madrid — confirma en la fuente
  OSM la misma colisión de código de línea ya documentada en ADR-0008/
  DEC-017 sobre el GTFS de Renfe.
- El endpoint público de Overpass devolvió `502 Gateway Timeout` por
  capacidad en varios intentos reales de esta descarga; reintentos con
  pocos segundos de espera tuvieron éxito. No es un fallo del dato, es
  disponibilidad intermitente del servicio público — documentado para quien
  reproduzca esta fixture más adelante.
