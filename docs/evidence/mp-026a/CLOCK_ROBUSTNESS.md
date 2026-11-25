# MP-026a · Robustez temporal con reloj controlado

Base `7864c29`. Delta de pruebas `dd92247f36f87124bc182007e06ec19f7bd235b4`.
Las pruebas nuevas están en `apps.api.tests.test_temporal_replay`, que ya
forma parte de los 29 módulos del job Python de CI.

## Inventario

| Punto revisado | Reloj y control en la comprobación |
|---|---|
| `apps/api/main.py`, `now_utc` y `_replay_clock` | Health, catálogo, snapshot y tablero usan la pared cuando falta `at`. En replay, los cuatro usan el `at` normalizado a UTC si se indica. Listado y detalle de vehículos siempre usan la pared. El arnés sustituye `now_utc`. |
| `apps/api/snapshot.py`, `resolve_clock` | Conserva un reloj de pared para llamadas directas sin `at`. Con `at` valida zona y rango. El arnés sustituye la clase `datetime` de este módulo. |
| `apps/api/gtfs_source.py`, `load_network` y `LoadedNetwork.gtfs_validity` | El arranque live evalúa `datetime.now(MADRID)`. La vigencia durante la ejecución toma el reloj que entrega cada petición y lo convierte a fecha de Madrid. El arnés sustituye `datetime` para cubrir arranque y petición. |
| `apps/api/db.py` y `apps/api/service.py` | SQL recibe el corte de ingestas y, solo en replay, el de observaciones como parámetros. Health calcula las edades con ese mismo instante. La revisión también se acota por el instante de la API. |
| `services/collector/collector.py`, `_utcnow` y `run_cycle` | Algunos casos de colector ejercitan el reloj de pared por defecto. El lanzador de la matriz sustituye `datetime` en el colector. Los casos de replay, incluido el kit real, inyectan las horas de ingesta directamente en `run_cycle`. |
| `apps/api/tests/test_snapshot_contract.py`, `SnapshotPostgresTests.setUp` en la base | Usaba `datetime.now()` para construir sus propias filas. El lanzador parchea también ese módulo para auditar la dependencia del baseline. |
| PostgreSQL | El servidor mantiene su reloj y se registra una lectura de `now()`. El único valor por defecto de este tipo en las migraciones es `source_feed_version.created_at DEFAULT CURRENT_TIMESTAMP`. Ningún caso de la matriz lee ese campo ni comprueba el reloj SQL. Las filas de ingesta y de observaciones reciben tiempos explícitos desde Python. |

Búsqueda de inventario con `rg` sobre `apps/api`, `packages`, `services`,
`tests` e `infra/migrations` para `datetime.now`, `now_utc`,
`time.time`, `now()`, `CURRENT_TIMESTAMP`, `CURRENT_DATE` y
`clock_timestamp`. `perf_counter` se usa en el benchmark de API para
medir latencia. El reloj de JavaScript queda fuera de esta matriz
Python. Las marcas del logger y las duraciones de unittest reflejan
la ejecución local.

## Dependencias corregidas

El baseline completo con la pared fijada al `2027-01-15T12:00:00Z`
ejecutó 296 casos con cero fallos, cero errores y 18 skips.
La inspección encontró dependencias implícitas aunque esa ejecución
quedó verde. [Salida de baseline](clock/baseline-2027-01-15.txt).

- `SnapshotPostgresTests` ya construye todas sus filas respecto de
  `2026-11-25T12:00:00Z`. Antes solo el caso normal/parcial/congelado
  sobreescribía el reloj de pared con un instante fijo.
- `CatalogContractTests` fija su reloj, de modo que su pareja de
  peticiones `200`/ETag y `304` usa el mismo estado de vigencia.
  `ApiContractTests` fija el corte para las consultas sin `at` y
  para el detector del soak.
- Las pruebas live usan copias sin editar de la fixture C5. Se retiró
  la extensión temporal del calendario a diciembre 19 que hacía el
  arnés anterior. Se conservan las aserciones de transiciones de
  vigencia, causa, ETag, rechazo de `at` y arranque con GTFS vencido
  en las fechas reales de esa fixture. El caso del 19 se verifica
  aparte con el ZIP congelado.

El helper de reloj vive en `tests/clock.py`. Cada fila de la matriz
arranca un proceso Python. Cuando una prueba declara su propio tiempo,
su parche local tiene precedencia y se restaura al salir. El delta
funcional es de pruebas.

## Casos temporales

- La fixture `gtfs_c5_real/calendar.txt` cubre del 19 de noviembre al
  6 de diciembre de 2026. Con dos días de aviso, en live devuelve `expiring` el 5 y a las
  `22:59:59Z` del 6. Desde las `23:00:00Z` del 6 Madrid ya está en
  el día 7 y devuelve `expired`. Se verifica la transición en health,
  catálogo y snapshot con una misma API en ejecución.
- En replay con pared del 20 de diciembre o del 15 de enero, el
  instante `2026-11-20T14:32:10Z` sigue en vigencia para C5. Los casos
  incluyen un segundo antes del inicio, el primer segundo vigente,
  el último segundo vigente y el primero caducado. Snapshot declara
  `generated_at` igual al `at` enviado.
- La ingesta sintética del primer corte se comprueba un microsegundo
  antes de `started_at`, en el instante exacto y un microsegundo
  después. Health y snapshot coinciden. La edad de sondeo es
  respectivamente `null`, `0` y `0,000001 s`. En una base
  realmente vacía y con reloj posterior al vencimiento, los tres feeds
  están `unknown`, las edades y revisión son `null` y el listado está vacío.
- Los calendarios de vigencia bajo prueba quedan fuera de las
  transiciones DST. La matriz también ejecuta los casos existentes de
  primavera y otoño de Madrid en las ventanas del tablero y la aritmética
  de día de servicio, con fechas y horas explícitas.

## Matriz ejecutada

| Reloj de pared UTC | Casos | Fallos | Errores | Skips | Duración |
|---|---:|---:|---:|---:|---:|
| 2026-11-25 12:00 | 298 | 0 | 0 | 18 | 28.433 s |
| 2026-12-05 12:00 | 298 | 0 | 0 | 18 | 28.873 s |
| 2026-12-06 12:00 | 298 | 0 | 0 | 18 | 28.358 s |
| 2026-12-07 12:00 | 298 | 0 | 0 | 18 | 28.294 s |
| 2026-12-18 12:00 | 298 | 0 | 0 | 18 | 28.305 s |
| 2026-12-19 12:00 | 298 | 0 | 0 | 18 | 28.217 s |
| 2026-12-20 12:00 | 298 | 0 | 0 | 18 | 28.213 s |
| 2027-01-15 12:00 | 298 | 0 | 0 | 18 | 28.351 s |

Cada fila reúne los 296 casos de la base y dos nuevos. Los 18 skips
previstos son 13 por el ZIP completo ausente de su ruta de CI y cinco por
el soak MP-007 ausente en la base fresca. El kit real se comprobó aparte
después de la matriz. [Comando completo y salida por fila](clock/matrix.txt).

## ZIP real congelado

Los cortes `1532` y `1533` se ingirieron con los tiempos explícitos del
arnés de Hito 3. La sonda comprobó la ventana del ZIP, del 20 de noviembre
al 19 de diciembre, en health y catálogo. En snapshot comprobó
`generated_at` para cada petición. Las 63 respuestas HTTP fueron 200.

| Modo | Reloj de pared UTC | Instante evaluado UTC | Resultado en los tres endpoints |
|---|---|---|---|
| Replay | 2026-12-20 y 2027-01-15 | 2026-11-19 22:59:59 | `not_yet_valid` |
| Replay | 2026-12-20 y 2027-01-15 | 2026-11-19 23:00:00 | `valid` |
| Replay | 2026-12-20 y 2027-01-15 | 2026-11-20 14:32:10 | `valid` |
| Replay | 2026-12-20 y 2027-01-15 | 2026-12-19 22:59:59 | `expiring` |
| Replay | 2026-12-20 y 2027-01-15 | 2026-12-19 23:00:00 | `expired` |
| Live | 2026-12-19 22:59:59 | Reloj de pared | `expiring` |
| Live | 2026-12-19 23:00:00 | Reloj de pared | `expired` |
| Live | 2026-12-20 y 2027-01-15 | Reloj de pared | `expired` |

Las dos peticiones a las 23:00 UTC prueban la medianoche de Madrid.
Live se arrancó el 18 de diciembre y siguió atendiendo mientras su reloj
controlado cruzaba el vencimiento. El registro recoge también el
20 de diciembre como `at` y las consultas sin `at` en replay, que usan la
pared. [Comandos y respuestas](clock/replay-real.txt).

## Reproducción y alcance

Cada fila de la matriz ejecuta `python -m tests.run_ci_with_clock <ISO-8601>
<módulos>`. Los módulos salen del comando de unittest del job `python`
de `.github/workflows/ci.yml`. Los casos nuevos entran en ese mismo
comando de CI al vivir en el módulo de replay. El baseline se extrajo
con `git archive 7864c29` y recibió solo los dos módulos del arnés.

Se usó Python 3.12.3 del entorno existente y la extensión local
`postgres_scanner` de DuckDB ya instalada. La base aislada usó el DSN
`postgresql://mp026a_clock:mp026a_clock_local@127.0.0.1:5453/madrid_pulse`.
El contenedor propio `postgis/postgis:17-3.5` se inició con
`docker run --pull=never`. Se aplicaron las migraciones 0001 y 0002 y
se comprobó la marca `madrid-pulse:disposable`. Tras las comprobaciones se
eliminaron el contenedor, el volumen y los temporales de baseline y matriz.
[Transcripción de BD](clock/database.txt).

Se guardaron SHA-256 de las fixtures del replay, GTFS, OSM y el kit local,
además de los arneses. El ZIP y los cortes del kit se leen desde el archivo
congelado de Hito 3. [Checksums](clock/fixtures.sha256.txt).

`python scripts/governance/check_docs.py` devolvió código 0.
[Gobernanza](clock/governance.txt).

Orca identifica el modelo `gpt-6.2-sol` en el despacho
`ctx_e3572f8739cb`. El esfuerzo solicitado fue `high`. La verificación
se circunscribe a la API, a los módulos Python de CI en local y al
kit congelado. Quedan la revisión del delta por Claude Opus High y
la validación del despliegue, el proveedor en vivo y la UI.
