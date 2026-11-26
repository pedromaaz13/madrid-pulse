# MP-036 · Reconstrucción del ancla de movimiento

Implementación en `ee92097` sobre `4bc8612`. Ejecutor del despacho Codex
`gpt-6.2-sol` · high, sin escalado. Entrega para revisión independiente.
**FR-01 sigue abierto.**

## Selección y procedencia

La API lee el tramo consecutivo del viaje actual por vehículo, en orden
`observed_at DESC, id DESC`. El motor lo recorre del comienzo al final y
aplica los umbrales existentes contra la última muestra aceptada. Un salto
rechazado conserva el ancla anterior y su hora GPS, edad, run, estado de
parada y distancia a la vía. Una muestra posterior coherente puede pasar a
ser el ancla, aunque una intermedia haya sido rechazada. El bloque `raw`
conserva las coordenadas, huella y relojes de la última observación del
operador. `map_matched` sigue describiendo la proyección de ese GPS y
`rendered` indica el ancla observada o el método derivado. La interpolación
con búfer usa dos anclas aceptadas. La muestra auxiliar de zona de MP-025a
sigue siendo la muestra GPS previa admisible por run.

`MADRID_PULSE_ANCHOR_HISTORY_DEPTH` vale **256** por defecto, admite
**2 a 1024**, e incluye la observación más nueva. PostgreSQL lee hasta
`depth + 1` filas usando `vehicle_position_vehicle_time_idx`. Una fila
de otro viaje delimita el inicio de la racha. Si la fila adicional sigue
en el mismo viaje, el contexto necesario para decidir si la primera
muestra vale como ancla quedó fuera de la lectura. El motor usa el horario,
con `quality.flags = ["anchor_history_truncated"]` y sin posición
confirmada. La mayor secuencia vehículo/viaje en el dump completo fue
228 filas, por lo que la cota cubre esa población. Una circulación con
un ID reutilizado, sin un cambio de viaje intermedio y con más de 256
filas elegibles puede activar esta degradación. La configuración por sí
sola no permite reconstruir un historial de longitud arbitraria.

El lote ampliado se pide solo para vehículos cuyo viaje tiene un corredor
validado en el snapshot. Lee con la misma cota de run y la misma
transacción `REPEATABLE READ READ ONLY` de MP-026b. En replay ambas lecturas
aplican `started_at <= at` y `observed_at <= observed_through`. El tablero
solo necesita el avistamiento bruto por viaje. La proyección del corredor
usa cajas de segmentos y longitudes de arco acumuladas sobre el catálogo
inmutable. Cada candidato se proyecta con la función preexistente, con
desempate por orden de segmento. La huella de geometría y umbrales se
transmite una vez por run dentro del lote.

## Evidencia y custodia

La fixture versionada contiene seis posiciones de la jornada 1
para `20231` y `20793`, más el subconjunto del GTFS que permite resolver
sus dos viajes. Conserva las huellas de origen y del extracto.
Los timestamps se conservan en UTC. Datos de Renfe Operadora, CC BY 4.0.
La geometría proviene de las fixtures de OpenStreetMap ya versionadas.
[Manifiesto](../../../tests/fixtures/mp036/manifest.json) ·
[Renfe Data](https://data.renfe.com/) ·
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) ·
[© OpenStreetMap contributors, ODbL](https://www.openstreetmap.org/copyright).

El clasificador reutiliza las ventanas y el aislamiento de MP-025b
(`9587b3e`, PR #13). Evalúa en `max(observed_at, started_at)` tanto B
como C por cada A→B→A consecutiva del mismo vehículo y viaje, con
`display_lag_s=0`. Comprueba que ambas filas son las que el snapshot
publica como `raw` y exige unicidad de su timestamp para identificar el
ancla. Las vistas temporales de sesión limitan a un vehículo y mantienen
sus observaciones, actualizaciones y runs elegibles. La detección usa
`rendered.last_confirmed_at` de producción. La clasificación describe la
selección de la API, sin inferir desplazamiento físico del tren.

## Clasificación de las 416 tríadas

| Resultado al volver C | Base `4bc8612` | Corrección `ee92097` |
|---|---:|---:|
| B vuelve como ancla tras haberse rechazado | 6 | 0 |
| Se conserva B, aceptada desde su primera aparición | 44 | 44 |
| Se acepta C, el GPS de retorno | 104 | 115 |
| El motor queda sin ancla confirmada | 5 | 0 |
| El patrón no tiene motor aplicable en estos fotogramas | 257 | 257 |
| **Total** | **416** | **416** |

En la base, el arnés registró **55/416** invocaciones del fallback con B
como muestra aislada. En 44 B ya era válida, en 6 reapareció tras un
rechazo, y en 5 el propio fallback acabó sin ancla confirmada. Las
**361/416** restantes siguieron otra rama. Hubo 159/416 tríadas evaluadas
por el motor y 257/416 con publicación bruta fuera de su cobertura. Los
seis casos incluyen `20231` y `20793`, más `19547`, `20215`, `20229` y
`20233`. Las dos secuencias confirmadas en MP-025b también se reproducen
con el extracto mínimo. [Salida del clasificador](CLASSIFICATION.txt).

## Verificación

- **RED esperado.** Nueve pruebas, nueve fallos de aserción en `4bc8612`
  con solo las pruebas y fixtures nuevas superpuestas. Las dos posiciones
  de retorno recuperaron los relojes intermedios `06:21:52Z` y `08:46:51Z`.
- **GREEN.** 332 casos de los módulos de CI en un checkout temporal de
  `ee92097` sobre el esquema limpio marcado. 314 pasaron y los mismos 18
  quedaron omitidos. Las nueve regresiones quedaron en verde.
- **PASS.** `check_docs.py`, las 36 pruebas de gobernanza, el OpenAPI
  regenerado comparado byte a byte y la compilación Python. Ruff con las
  reglas `E4,E7,E9,F` pasó en los archivos Python modificados. La ejecución
  con todas las reglas por defecto de Ruff 0.16.0 señaló diagnósticos de
  estilo heredados en los módulos de producción, 46 frente a 49 en la base.
- **PASS.** Frontend en el checkout temporal, Node 22.13.1. `npm ci` en modo
  offline, lint, typecheck, 110 pruebas y build. Vite emitió un aviso por
  tamaño de un chunk.
- **PASS.** 700 proyecciones de fixtures C4 y C5 idénticas al cálculo
  exhaustivo previo, incluida la longitud de arco y el índice de segmento.
  [Ejecuciones](VERIFY.txt).

## Rendimiento

Se usó el mismo SQL de carga de MP-026b sobre 300 000 runs, 100 000
posiciones, 100 000 actualizaciones y 100 vehículos. Cada versión hizo
10 calentamientos y 60 peticiones de TestClient por endpoint, con la
misma base, reloj y apertura de conexión por petición. En la repetición
secuencial, todas devolvieron HTTP 200.

| Endpoint | Base p50 / p95 (ms) | Corrección p50 / p95 (ms) |
|---|---:|---:|
| Snapshot | 211,41 / 271,73 | 248,37 / 267,98 |
| Tablero | 169,89 / 206,04 | 152,61 / 162,68 |

Medido alrededor de la lectura ampliada, con conversión de filas a Python,
el lote añadido costó **45,65 ms p50 y 52,86 ms p95** para el viaje con
corredor de la carga sintética. La primera pareja coincidió con carga
concurrente del host. Los p95 del snapshot fueron 2 677,83 ms en la base y
940,08 ms con el cambio. Los p95 del tablero fueron 2 042,12 y 728,22 ms.
La diferencia medida del tablero refleja variabilidad entre ejecuciones.
Su camino de lectura sigue usando el avistamiento por viaje.

Como referencia adicional, en un fotograma de la jornada 1 la consulta
pidió un lote para 142 de los 360 vehículos visibles. El constructor en
memoria y sus lecturas tardaron 788–951 ms en cuatro llamadas calientes y
2 923 ms en la primera, con la caché de horarios todavía vacía. Esa sonda
usa el constructor directamente y un único reloj de la captura.
[Comandos y resultados completos](BENCH.txt).

## Reproducción

Preparación offline con la imagen local `postgis/postgis:17-3.5`, puerto
`127.0.0.1:5459`, esquema `public`, rol propietario local `mp_test`.
Cada base se marcó `madrid-pulse:disposable`. La suite usa `mp036_ci`,
el benchmark `mp036_bench` y el clasificador `mp036_capture`. Los comandos
de restauración y los DSN de prueba están en [Ejecución](RUN.md).
