# MP-036 · Reconstrucción del ancla de movimiento

Delta `121c438` sobre la entrega revisada `a7e01b8` y base original
`4bc8612`. Ejecutor del despacho Codex `gpt-6.2-sol` · high, sin escalado.
Queda la verificación independiente de este delta.
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
con búfer usa dos anclas aceptadas y se interrumpe en el salto de
reanclaje. La muestra auxiliar para inferir entrada en zona de MP-025a es
la fila GPS previa del mismo viaje admisible por run y reloj. Puede ser
una muestra rechazada para movimiento. Solo se usa si la proyección
pasa las comprobaciones de vía y zona de parada. Esa muestra auxiliar
queda fuera de la selección de anclas y de la interpolación.

`MADRID_PULSE_ANCHOR_REACQUIRE_SAMPLES` configura el número K de muestras
consecutivas. Por defecto K = **2**. `0` desactiva el reanclaje y se aceptan
valores de 2 a 1024. Cada candidata debe estar en vía, tener un reloj
posterior al del ancla y superar el umbral existente de rechazo por
retroceso respecto al ancla. El tramo de confirmación exige reloj
estrictamente creciente, progreso no decreciente, coordenadas distintas
entre todas sus muestras y velocidad plausible entre cada par vecino
según el filtro existente. Una ruptura reinicia la racha con la
candidata actual si satisface el primer filtro. La vuelta exacta A→B→A
reinicia la racha aunque A también hubiese sido rechazada. Al llegar a K se publica
la primera muestra de esa racha, con su hora y procedencia. La última
fila conserva sus señales frente al ancla previa y añade
`anchor_reacquired` en ese fotograma. El reanclaje corta la velocidad
entre anclas y se reconstruye con el historial admisible por petición.

`MADRID_PULSE_ANCHOR_HISTORY_DEPTH` vale **256** por defecto, admite
**2 a 1024**, e incluye la observación más nueva. PostgreSQL lee hasta
`depth + 1` filas usando `vehicle_position_vehicle_time_idx`. Una fila
de otro viaje delimita el inicio de la racha. Si la fila adicional sigue
en el mismo viaje, el contexto necesario para decidir si la primera
muestra vale como ancla quedó fuera de la lectura. El motor usa el horario,
con `quality.flags = ["anchor_history_truncated"]` y sin posición
confirmada. Las secuencias de la jornada 1 están censuradas por el inicio,
el hueco y el fin de la captura. El máximo observado de 228 filas entre
todos los viajes es un límite inferior de su posible longitud completa.
Con la cadencia mediana de 38 s, 256 filas corresponden a unos 162 minutos.
Queda medir cuántas circulaciones superan esa cota en una jornada completa
cuando esté disponible la jornada 2 de MP-028.

La frontera se identifica por `source_trip_id`. En el GTFS de la captura,
450/450 filas del calendario tienen una sola fecha de servicio. Los
identificadores de viaje del feed incluyen ese servicio, por ejemplo
`1022J`, `1029J` y `1036J` para el mismo tren en jueves distintos. El
algoritmo depende de que una misma combinación vehículo/viaje identifique
una circulación de ese día. La reutilización futura de IDs requeriría
revisar esta suposición.

El snapshot y el listado legado amplían solo los viajes consecutivos con
corredor validado. El listado y detalle legado proyectan sobre el corredor
de su patrón y dejan `position` nulo si el patrón carece de corredor
utilizable. El snapshot elige el ancla de presentación y trae en un único
lote su perfil, cancelación base y GPS previo de zona. Las lecturas y la
selección comparten la transacción `REPEATABLE READ READ ONLY`.
En replay se aplican `started_at <= at` y `observed_at <= observed_through`.
El recorte adicional dentro de las LATERAL de cancelación y GPS previo
es defensivo para runs antedatados o fuera de orden. El tablero conserva
la lectura del avistamiento bruto por viaje. Las proyecciones de vía usan
`PolylineProjector` y el catálogo inmutable de la primera entrega.

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

| Resultado al volver C | Base `4bc8612` | Antes y después del delta |
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

## Alcance más allá de A→B→A

`impact.py frames` usa el constructor real de snapshot con `display_lag_s=0`
en 80 instantes de 07:40 a 08:59 UTC, separados por 60 s. Compara
`last_confirmed_at` para el mismo reloj y vehículo con la base original
`4bc8612`. `impact.py samples` usa el motor de cada revisión sobre cada
prefijo visible del viaje. Hay 12 160 filas con corredor y 12 146 con
proyección. Para comparar con la revisión, las rachas descriptivas
cuentan rechazos en vía entre aceptaciones y omiten las filas sin
proyección admisible. La regla de reanclaje de producción sí exige
muestras consecutivas, incluyendo ese corte.

| Medición frente a `4bc8612` | Antes de B1 | Después de B1 |
|---|---:|---:|
| Vehículo-fotogramas con hora de ancla distinta | 413/26 601 | 411/26 601 |
| Ancla más antigua / más joven / transición con nulo | 401 / 8 / 4 | 399 / 8 / 4 |
| Máxima antigüedad adicional | 398 s | 398 s |
| Muestras aceptadas en la base que quedan rechazadas | 227 | 223 |
| Rachas de al menos dos rechazos en vía | 111 | 111 |
| Rachas idénticas que después se recuperan cerca del ancla original | 104 | 104 |
| Rachas idénticas totales, incluidas tres sin recuperación en el corte | 107 | 107 |
| Rachas idénticas preexistentes con evento de reanclaje | 0 | 0 |

El efecto principal es retener el ancla ante los rechazos en vez de
seguir inmediatamente las coordenadas del operador. Esa retención ayuda
cuando el GPS vuelve congelado a una coordenada repetida y puede mantener
una posición errónea cuando el ancla anterior era el dato equivocado.
La coincidencia de coordenadas identifica el patrón del feed. La verdad
de terreno sobre el tren sigue sin verificarse. B1 cambia solo dos
vehículo-fotogramas de esa cuadrícula frente a `a7e01b8`.

| Racha de la revisión | Efecto con K = 2 |
|---|---|
| 20414, 06:17:10 UTC | Retenía el ancla anterior. La muestra de las 06:17:52 confirma el nuevo ancla de las 06:17:10, a 25 215 m. |
| 20418, 06:32:10 UTC | Retenía el ancla anterior. La muestra de las 06:32:52 confirma el nuevo ancla de las 06:32:10, a 16 187 m. |
| 20752, 07:44:52 UTC | Sigue en el ancla de las 07:44:10. Las dos muestras rechazadas cambian de 17 659 a 39 595 m en 18 s, unos 4 387 km/h. El filtro vigente impide el reanclaje. |

El motor también reancló `19588` en `07:56:30Z` al observar la muestra de
`07:57:10Z`. Los tres eventos describen decisiones del algoritmo.
[Resultados de alcance](DELTA_IMPACT.txt).

## Verificación del delta

- **RED esperado.** El módulo contra `a7e01b8` ejecutó 16 casos. Cinco
  pruebas nuevas fallaron por aserción. Las dos guardas de rango y frontera
  ya pasaban. La guarda de A→B→A con A también rechazada falló contra
  el primer delta `713b8a0` y quedó verde con `121c438`.
- **GREEN.** Los módulos Python de CI en un checkout de `121c438` ejecutaron
  339 casos, con 321 pasados y las mismas 18 omisiones. Pasaron las siete
  pruebas nuevas y los dos casos reales de la fixture anterior.
- **PASS.** `check_docs.py`, las 36 pruebas de gobernanza, OpenAPI regenerado
  idéntico byte a byte y compilación Python. Ruff pasó con `E4,E7,E9,F`
  en los Python modificados.
- **PASS.** Lint, typecheck, 110 pruebas y build del frontend en checkout
  temporal con dependencias offline. Vite emitió un aviso por tamaño de chunk.
  [Salidas del delta](DELTA_VERIFY.txt).

## Rendimiento

Mismo SQL de MP-026b, con 300 000 runs, 100 000 posiciones, 100 000
actualizaciones y 100 vehículos. El benchmark HTTP hace 10 calentamientos
y 60 peticiones por endpoint, con una conexión por petición y reloj fijo.
La variante truncada conserva la carga inicial. La variante completa
representa un cambio de viaje de V1 con 100 filas del viaje actual,
posiciones sobre la vía de la fixture C5 y las mismas cardinalidades.

| Caso | Base p50 / p95 (ms) | Antes del delta p50 / p95 (ms) | Después del delta p50 / p95 (ms) |
|---|---:|---:|---:|
| Snapshot, truncado | 209,75 / 226,47 | 247,06 / 274,79 | 207,26 / 227,19 |
| Tablero, truncado | 153,94 / 170,31 | 153,84 / 176,29 | 158,10 / 180,36 |
| Snapshot, completo | 208,88 / 228,11 | 216,86 / 247,92 | 204,45 / 226,10 |
| Tablero, completo | 153,80 / 168,44 | 154,18 / 172,68 | 154,20 / 172,92 |

La primera entrega subía el p95 del snapshot truncado un 21 % en la
repetición del revisor, 228,91→277,69 ms. Aquí se reprodujo un aumento
del 21 % con esa revisión. La diferencia 271,73→267,98 ms del informe
anterior quedaba dentro del ruido entre ejecuciones.

El lote ampliado truncado pasó de 45,99 / 51,07 ms a **11,92 / 16,40 ms**
p50/p95, con cero consultas de metadatos de ancla. En la variante
completa, el lote pasó de 16,55 / 19,78 ms a **8,09 / 14,38 ms**. La
consulta separada de metadatos de la fila elegida costó **5,05 / 6,63 ms**.

| Sonda de captura real, mediana caliente de cinco llamadas | Base (ms) | Antes del delta (ms) | Después del delta (ms) |
|---|---:|---:|---:|
| Snapshot 06:22:35 UTC, 193 vehículos | 442,35 | 254,40 | 158,05 |
| Snapshot 08:47:40 UTC, 360 vehículos | 860,40 | 835,61 | 461,03 |
| Listado legado 08:47:40 UTC, 360 vehículos | 3 889,62 | 1 606,50 | 337,15 |

La primera mejora en fotogramas reales coincide con la incorporación de
`PolylineProjector` en la entrega anterior. A las 08:47:40 el lote del
snapshot pasó de 482,66 a 160,52 ms y el nuevo lote de metadatos costó
12,38 ms para 142 anclas efectivas. El listado legado pasó de ampliar
358 a 141 vehículos. El primer snapshot de la primera sonda tardó
1 213,34 ms en frío. Los tiempos de tablero varían entre ejecuciones.
[Salidas completas del benchmark](DELTA_BENCH.txt).

## Reproducción

Preparación offline con la imagen local `postgis/postgis:17-3.5`, puerto
`127.0.0.1:5459`, esquema `public`, rol propietario local `mp_test`.
Cada base se marcó `madrid-pulse:disposable`. La suite usa `mp036_ci`,
el benchmark `mp036_bench` y el clasificador `mp036_capture`. Los comandos
de restauración y los DSN de prueba están en [Ejecución](RUN.md).
