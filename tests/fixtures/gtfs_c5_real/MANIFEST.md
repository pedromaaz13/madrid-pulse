# Fixture GTFS estática real C5 (MP-010)

- Fuente: Renfe Operadora, `Fichero_CER` (GTFS estático nacional).
- URL: `https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip`
- Descarga: `2026-11-19`.
- Timestamp de las entradas observado dentro del ZIP: `2026-11-19 04:09`.
- SHA-256 del ZIP fuente: `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e`.
- Licencia: Creative Commons Attribution 4.0 (`CC BY 4.0`) + condiciones de Renfe Data.
- Atribución: Origen de los datos: Renfe Operadora — Horarios cercanías (`Fichero_CER`). Datos reducidos por Madrid Pulse; Renfe no respalda ni patrocina este servicio.

El ZIP completo medía 15,7 MB comprimido y 297.803.958 bytes extraído;
`stop_times.txt` representaba 273.499.656 bytes. No se versiona porque cambia
con la publicación operativa y duplicaría un artefacto grande de upstream. La
fixture conserva datos reales, no sintéticos: las cinco rutas cuyo prefijo de
red es `10` y nombre corto `C5`; el primer `trip_id` lexicográfico de cada
patrón distinto de paradas por ruta (incluido un representante de una variante
sin `stop_times`); y todas las paradas, calendarios y shapes referenciados.

Comando reproducible (la selección de línea es configuración, no lógica):

```sh
python3 -m packages.gtfs.tools.reduce_fixture \
  /tmp/fomento_transit.zip tests/fixtures/gtfs_c5_real \
  --network-id 10 --short-name C5
```

## Contenido reducido

| Fichero | Filas de datos | SHA-256 |
|---|---:|---|
| `routes.txt` | 5 | `0c044d3b7a799b5d644be3f3b963bbdaf165ca1daef1afd6c30421dfa2eb3486` |
| `trips.txt` | 15 | `4e18ba444d10a5a54e6c3985ef005e41b35487c126a2417ff40898975f469dc3` |
| `stops.txt` | 23 | `fa77b60ee6ac6561de903fb5d18a6f7e65682466bf55b92344f62c3bc855f6c8` |
| `stop_times.txt` | 168 | `53cdd888e87f289c0bd45b60acbb0eeb69982a230a084d0cbfdf73d7bd383c1f` |
| `shapes.txt` | 630 | `351c20eb08295d788f85bf518d258fd881d7773cde4e6c94faa50eef8099676d` |
| `calendar.txt` | 4 | `652bc1240824e03366ed2edf8b6d44104913f8cf1ed232d6fe2ea54d0e37d498` |

## Hallazgos preservados

- `trips.txt` de Renfe no contiene columna `direction_id`; no se añade a la fixture.
- La ruta `10T0035C5` contiene trips pero carece de `stop_times` en el feed completo; el representante huérfano se conserva para impedir que el parser invente su recorrido.
- Las rutas `10T0017C5`/`10T0018C5` y `10T0047C5`/`10T0048C5` contienen patrones inversos reales de `stop_sequence`.
