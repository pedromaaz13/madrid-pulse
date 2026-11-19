# GTFS estático de Renfe

Parser en streaming de `routes.txt`, `trips.txt`, `stops.txt`,
`stop_times.txt`, `shapes.txt` y `calendar.txt`. Acepta el ZIP oficial o un
directorio extraído y filtra genéricamente por `route_id`, `network_id` y/o
`short_name`; no hay identificadores de línea embebidos en la lógica.

```python
from packages.gtfs import load_feed, validate_topology

topology = load_feed("fomento_transit.zip", network_id="10", short_name="C5")
route_id = topology.resolve_trip_route_id("1021X20869C5")
sequences = topology.resolve_stop_sequences("1021X20869C5", "35002")
validation = validate_topology(topology)
```

`resolve_trip_route_id` hace el `JOIN` literal verificado en MP-003. Para un
trip `ADDED` ausente de `trips.txt`, acepta opcionalmente su `routeId` explícito
del GTFS-RT si existe en el catálogo; nunca lo infiere del texto del vehículo.

## Fuente y fixture

El ZIP completo no se versiona: pesa ~15,7 MB comprimido y ~298 MB extraído,
incluido un `stop_times.txt` de ~273 MB, y Renfe lo actualiza. Los tests usan
una reducción real y trazable en `tests/fixtures/gtfs_c5_real/`: un trip por
cada patrón distinto de paradas observado y uno por variante huérfana, junto
con todas sus rutas, paradas, calendarios y shapes. Se regenera así:

```sh
curl -fL -o /tmp/fomento_transit.zip \
  https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip
python3 -m packages.gtfs.tools.reduce_fixture \
  /tmp/fomento_transit.zip tests/fixtures/gtfs_c5_real \
  --network-id 10 --short-name C5
```

La licencia y atribución del dato son `CC BY 4.0`; ver
`docs/legal/DATA_SOURCES.md`, `docs/legal/ATTRIBUTION.md` y el manifiesto de la
fixture.

## Pruebas

```sh
python3 -m unittest discover -s packages/gtfs/tests -p 'test_*.py' -v
```

El GTFS real observado no contiene `direction_id` en `trips.txt`. La verdad de
fuente disponible para dirección es el orden de `stop_sequence` y el
`shape_id`; el validador expone patrones ordenados y no inventa esa columna.
