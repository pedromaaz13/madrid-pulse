# Fixture GTFS estática real con horas `24:xx` (MP-019)

Datos **reales**, no sintéticos: dos circulaciones extraídas literalmente del
GTFS oficial congelado del kit de Hito 3, con todas sus dependencias.

- Fuente: Renfe Operadora, `Fichero_CER` (GTFS estático nacional).
- URL: `https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip`
- Copia congelada usada: `data/hito-03/replay/fomento_transit.zip` del kit de
  Hito 3 (fuera de Git), fecha de catálogo `2026-11-20`.
- SHA-256 del ZIP fuente: `c5b40823c5cacbec6d9a21d88ec0530d9604a6d4331df98c330e608f0bacb11e`
  (el mismo que declara `data/hito-03/replay/manifest.json`).
- Licencia: Creative Commons Attribution 4.0 (`CC BY 4.0`) + condiciones de Renfe Data.
- Atribución: Origen de los datos: Renfe Operadora — Horarios cercanías
  (`Fichero_CER`). Datos reducidos por Madrid Pulse; Renfe no respalda ni
  patrocina este servicio.

## Por qué existe esta fixture y no se amplía `gtfs_c5_real`

`tests/fixtures/gtfs_c5_real/` (DEC-023) no contiene **ninguna** hora `24:xx`:
su máximo es `23:53:00`. Hacía falta dato real con horas extendidas para probar
el hallazgo de la revisión de MP-019 (la fecha de servicio se resolvía por
reloj civil y descartaba los viajes `24:xx` del día anterior).

Ampliar la fixture C5 habría cambiado su SHA-256 y, con él, el `gtfs_version`
del que dependen la matriz de cobertura aprobada de MP-018
(`docs/evidence/mp-018-corridor-coverage.csv`, comparada byte a byte en
`packages.geo.tests.test_catalog`) y varias aserciones de MP-010/MP-017. Una
fixture nueva e independiente deja intacta toda esa evidencia ya revisada.

## Contenido

| Fichero | Filas de datos | SHA-256 |
|---|---:|---|
| `routes.txt` | 2 | `4c2d844fbc21ec93264056a8504be085e4737263019694a44db6723e012ef5b0` |
| `trips.txt` | 2 | `02836f6361cf803b9210191054b9989803ddb45dba10e4d6c41e34f0b85a6e87` |
| `stops.txt` | 13 | `6e60acece4f5db2677a4b044ce12406d53b0d8a89eeec1b71e0402bbdaa2f43d` |
| `stop_times.txt` | 14 | `b783aec2c9797af1ddd6c3318d5e6b0d76315934b0535cdbb202ed7b8156a69b` |
| `shapes.txt` | 479 | `f32d39ed3521b4bfafb992ccfb2ab8cb6b149190a548d33bfaef122079599ae6` |
| `calendar.txt` | 1 | `0357478b3b3383de506bee63c83e830590c294bc0a6dab16434e27d1e93af489` |

Las dos circulaciones comparten el `service_id` **`1023V`**, programado
exclusivamente el **viernes 2026-11-20** (`start_date` = `end_date` =
`20261120`), así que el día de servicio del escenario es inequívoco.

### `1023V19940C1` — línea C1, paradas en `24:00` y `24:05`

```text
001  17000  23:50:00
002  98003  23:54:00
003  98304  24:00:00
004  98305  24:05:00
```

Su patrón queda `pending` en el catálogo de corredores (MP-018 no descargó
geometría de C1), así que sirve para el tablero y la enumeración de servicios
programados **sin** geometría: el caso de "solo horario, sin GPS".

### `1023V20533C4` — línea C4, recorrido `23:50` → `24:32`

Diez paradas, de `37012` a `17000`. Su patrón es `validated` contra la relación
OSM real `11332` (fixture `osm_c4_real/`, MP-018), por lo que permite probar
posición y progreso reales a través de la medianoche sobre un corredor
verificado, no sobre un trazado inventado.

## Comando reproducible

Los `trip_id` son argumentos; la herramienta no contiene identificadores
(ADR-0011):

```sh
python3 -m packages.gtfs.tools.extract_trips_fixture \
  data/hito-03/replay/fomento_transit.zip tests/fixtures/gtfs_24h_real \
  1023V19940C1 1023V20533C4
```

## Hallazgos preservados

- El feed real publica `24:xx` (18 196 valores) y `25:xx` (196) y **ninguna**
  hora en `02:xx`/`26:xx`: la franja inexistente del adelanto de hora nunca se
  alcanza con este operador, lo que queda documentado en el docstring de
  `packages.movement.schedule.service_day_instant` en vez de asumido.
- 742 circulaciones del núcleo Madrid tienen alguna hora `24:xx` en ese ZIP; no
  son un caso marginal.
