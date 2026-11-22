# MP-019 — Corrección de los dos hallazgos de aritmética temporal (evidencia ejecutada)

Hallazgos reales de la auditoría de OpenAI Codex sobre la primera entrega de
MP-019. Los dos son errores de aritmética de día de servicio —la misma familia
que el proyecto ya corrigió en MP-009 (huso del exportador, DEC-021) y MP-013
(`service_date` en UTC en vez de Europe/Madrid)—, así que se documentan con el
número reproducido, no con una descripción.

## Hallazgo 1 — `service_instant` no era la inversa de `service_seconds` en los cambios de hora

### Qué estaba mal

La primera versión sumaba los segundos del día de servicio **después** de
convertir la medianoche local a UTC, es decir sobre un único desplazamiento
fijo. En los dos días en que Europe/Madrid cambia de hora, el desplazamiento
real cambia a mitad del día de servicio y la suma se desviaba una hora exacta.

Reproducido antes de corregir (hora GTFS `03:30:00` = 12 600 s):

| Día de servicio | Resultado anterior | Esperado |
|---|---|---|
| `2026-03-29` (adelanto, día de 23 h) | `2026-03-29T04:30:00+02:00` | `2026-03-29T03:30:00+02:00` |
| `2026-10-25` (atraso, día de 25 h) | `2026-10-25T02:30:00+01:00` | `2026-10-25T03:30:00+01:00` |

La ida y vuelta tampoco cerraba: `service_seconds` del instante devuelto daba
`16 200` y `9 000` en vez de `12 600`.

### Causa raíz

`service_seconds` calculaba la diferencia entre dos `datetime` *aware* con el
**mismo** `tzinfo`. Python resuelve ese caso de forma naive (ignora el huso), de
modo que la función era en realidad aritmética de **reloj de pared** y daba el
resultado correcto *por accidente*. Al escribir la inversa con aritmética sobre
UTC se eligió, sin saberlo, un modelo temporal distinto, y las dos funciones
dejaron de ser inversas exactamente en esos dos días.

### Corrección

Una sola implementación del día de servicio, en
`packages/movement/schedule.py`, explícita sobre el modelo de reloj de pared en
**ambas** direcciones:

- `service_seconds(at, service_date)`: resta en espacio naive, con la intención
  escrita en el código en vez de delegada en una regla implícita de Python.
- `service_day_instant(service_date, seconds)` (nueva): suma los segundos en
  espacio de reloj de pared y **localiza después**, por lo que cada fecha aplica
  su desplazamiento real. Admite `seconds >= 86 400`.
- `apps/api/snapshot.py::service_instant` delega en ella: la API y el motor de
  movimiento ya no pueden divergir.

Verificado tras corregir:

```text
2026-03-29: 2026-03-29T03:30:00+02:00  (ida y vuelta -> 12600.0)
2026-10-25: 2026-10-25T03:30:00+01:00  (ida y vuelta -> 12600.0)
```

### Dos casos límite resueltos de forma deliberada

- **Hora inexistente.** El `2026-03-29` el reloj local salta de 02:00 a 03:00;
  ese reloj de pared no existe. Se resuelve con el desplazamiento previo al
  salto (`fold=0`), lo que equivale a desplazar la hora una hora hacia delante,
  y la ida y vuelta devuelve `seconds + 3600` en esa franja. Comprobado sobre el
  feed oficial: **0 valores** en `02:xx` y `02:xx+24h` (`26:xx`) sobre
  3,5 M de `stop_times`, así que el operador real nunca publica un horario ahí.
- **Hora ambigua.** El `2026-10-25` el reloj repite 02:00–03:00. Se toma la
  **primera** ocurrencia, coherente con `service_seconds`, que no puede
  distinguirlas.

### Regresión añadida

`packages.movement.tests.test_rendering.ServiceDayArithmeticTests`:

- los dos casos exactos del hallazgo, ida y vuelta incluida;
- **barrido minuto a minuto de 00:00 a 28:00** en las dos fechas de cambio de
  hora, sus vísperas y un día normal (1 680 instantes × 5 fechas), exigiendo
  igualdad exacta salvo en la franja inexistente, donde se exige el
  desplazamiento documentado de exactamente 3 600 s;
- `24:05` y `25:09` (el máximo real del feed) caen en el día civil siguiente;
- la hora ambigua toma la primera ocurrencia;
- un `datetime` naive sigue rechazándose.

## Hallazgo 2 — la fecha de servicio se elegía por reloj civil y perdía los viajes `24:xx`

### Qué estaba mal

`_service_date` devolvía la fecha civil de Europe/Madrid. A las `00:02` del
21 de noviembre, un viaje del día de servicio del **20** con paradas a las
`24:00`/`24:05` se resolvía contra el 21.

Reproducido antes de corregir, con el ZIP oficial y el trip real
`1023V20533C4` (línea C4, `23:50` → `24:32`, patrón `validated` contra la
relación OSM `11332`):

```text
now = 2026-11-21T00:02:00+01:00
_service_date(now) = 2026-11-21
service_seconds(now, 2026-11-21) =    120   -> progreso por horario =     30.4 m
service_seconds(now, 2026-11-20) =  86520   -> progreso por horario =  12553.1 m

posicion con service_date=21 (BUG): scheduled    30.4 m  40.24109 -3.76925
posicion con service_date=20 (OK) : scheduled 12553.1 m  40.32866 -3.72470
distancia entre ambas: 10445 m
```

**10,4 km de error** en la posición publicada, y además la circulación se
marcaba `expired` porque su `service_id` (`1023V`) no está programado el 21.

No es un caso marginal: el ZIP oficial tiene **742 circulaciones del núcleo
Madrid** con alguna hora `24:xx` (18 196 valores `24:xx` y 196 `25:xx`).

### Corrección

`apps/api/service.py::ServiceDateResolver` resuelve la fecha de servicio **por
circulación**, no por reloj:

1. **Ventana de ambigüedad derivada del dato, no inventada.**
   `extended_service_horizon_s(topology)` es el máximo `arrival`/`departure`
   del GTFS cargado menos 86 400 s. Con el núcleo Madrid completo son
   **3 180 s** (máximo real `24:53`); con la fixture de regresión, 1 920 s
   (`24:32`); con una fixture sin horas extendidas, `0.0`, y entonces no existe
   ninguna ventana y el comportamiento es idéntico al anterior.
2. **Se comprueba primero el día anterior.** Dentro de la ventana, los
   candidatos son `(día anterior, día civil)` en ese orden.
3. **Nunca se fabrica una pertenencia.** Un día candidato solo se admite si el
   `service_id` del viaje está realmente programado en él *y* si el instante
   actual cae dentro del horario publicado de ese viaje. Si ningún candidato lo
   contiene, se conserva la fecha civil, exactamente como antes.

La fecha resuelta se usa para la posición **y** para `circulation_status`, de
modo que las dos no pueden contradecirse. El tablero cruza los dos días
candidatos y cada entrada publica su propio `service_date`.

Verificado tras corregir, con el ZIP oficial:

```text
horizonte extendido del ZIP real: 3180.0 s
a las 00:02 del 21 -> primary=2026-11-21  candidates=(2026-11-20, 2026-11-21)
  for_trip(1023V20533C4) -> 2026-11-20      (viaje 24:xx en curso)
  for_trip(1023V19940C1) -> 2026-11-20      (viaje 24:00/24:05)
  for_trip(1024S19799C1) -> 2026-11-21      (servicio del 21: no retrocede)
a las 02:00 del 21 -> candidates=(2026-11-21,)   for_trip(1023V20533C4) -> 2026-11-21
```

Tablero de Chamartín (`17000`) a las `00:02` del 21, con el ZIP completo:

```text
service_date: 2026-11-21 | considerados: ['2026-11-20', '2026-11-21']
entradas por día de servicio: {'2026-11-20': 23, '2026-11-21': 2}
  1023V19940C1  sd=2026-11-20  C1  24:00 -> 2026-11-21T00:00:00+01:00  eta=schedule
  1023V20533C4  sd=2026-11-20  C4  24:32 -> 2026-11-21T00:32:00+01:00  eta=schedule
```

Antes de la corrección esas **23 llamadas del día de servicio anterior eran
invisibles** en el tablero.

### Fixture real nueva, sin tocar la aprobada

`tests/fixtures/gtfs_c5_real/` no contiene ninguna hora `24:xx` (su máximo es
`23:53`), así que no servía para la regresión. Ampliarla habría cambiado su
SHA-256 y con él el `gtfs_version` del que dependen la matriz de cobertura ya
aprobada de MP-018 (comparada byte a byte) y varias aserciones de MP-010/MP-017.

Se añade por eso una fixture **independiente**,
`tests/fixtures/gtfs_24h_real/`, con dos circulaciones extraídas literalmente
del ZIP oficial y su manifiesto completo (fuente, URL, SHA-256 del ZIP,
licencia `CC BY 4.0`, atribución y comando reproducible), más la herramienta
genérica `packages.gtfs.tools.extract_trips_fixture` (los `trip_id` son
argumentos, sin identificadores en la lógica). Queda registrada en
`docs/legal/ATTRIBUTION.md` y `docs/legal/DATA_SOURCES.md`.

### Regresión añadida

`apps.api.tests.test_snapshot_contract`:

- `ExtendedHoursAfterMidnightTests`: el horizonte sale del feed (1 920 s para
  esta fixture); a las `00:02` los dos viajes `24:xx` resuelven al día de
  servicio anterior; a las `02:00` la ventana se cierra; un viaje diurno del
  día nuevo **no** retrocede; sin servicio programado en ningún candidato no se
  fabrica pertenencia; la posición correcta supera los 12 km de progreso
  mientras la fecha civil lo sitúa por debajo de 100 m, con **más de 10 km de
  separación** entre ambas; y la entrada del snapshot publica
  `service_date = 2026-11-20` con `circulation_status = active`.
- `ExtendedHoursBoardTests`: la llamada `24:00` aparece con su propio
  `service_date` y su instante absoluto `2026-11-21T00:00:00+01:00`; también la
  de `24:05`; ninguna llamada se duplica entre los dos días candidatos; y fuera
  de la ventana el tablero vuelve a considerar solo el día civil.

## Coste medido de la corrección

Mismo equipo y método que `mp-019-explain-y-bench.md` (Apple M1, 8 GB,
PostgreSQL 17.5, `TestClient` en proceso, conexión reutilizada):

| Endpoint | Núcleo completo, 05:20 (un día candidato) | Núcleo completo, 00:02 (dos días candidatos) |
|---|---:|---:|
| `GET /api/v1/snapshot` | p50 8,42 / p95 23,32 ms | p50 9,62 / p95 13,81 ms |
| `GET /api/v1/stations/{id}/board` | p50 7,96 / p95 10,39 ms | p50 9,62 / p95 24,19 ms |
| `GET /api/v1/catalog` | p50 0,54 ms | p50 0,46 ms |

El peor caso del tablero (dos días de servicio cruzados, justo después de
medianoche) cuesta ~1,7 ms más de p50; los índices de llamadas programadas se
memoizan por fecha, así que ese coste se paga una vez por día de servicio. No
se introdujo ninguna consulta nueva: las formas de las consultas SQL no han
cambiado y los planes `EXPLAIN` del documento anterior siguen vigentes, lo que
confirman además los tests de conteo de `execute`.

## Matriz de evidencia reejecutada al completo

| Comprobación | Resultado |
|---|---|
| Suite exacta de CI contra la base de desarrollo | **222/222 OK, sin ningún `skip`**; recuentos `668/484/3/120/0` idénticos antes y después; soak `rows=668, near_corridor=177, after=668` |
| Suite exacta de CI contra PostGIS **fresco** con `0001`+`0002` desde cero | **222 ejecutados, OK con 5 `skip` explícitos** (soak irrepetible de MP-007, DEC-035) |
| Frontend con **Node 22.13.1** (versión que fija CI) | `npm ci` sin vulnerabilidades, lint, typecheck, **5/5 tests**, build con worker MapLibre `550754` bytes |
| Replay de tres snapshots sobre capturas reales `1532`/`1533` | invariantes de nuevo en verde; ver `mp-019-tres-snapshots-replay.md` |
| `EXPLAIN` y p50/p95 | sin cambios de forma de consulta; nuevas cifras arriba y en `mp-019-explain-y-bench.md` |
