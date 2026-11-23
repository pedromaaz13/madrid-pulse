# DATA_CONTRACTS.md

Estado: **parcialmente implementada en MP-013** (`apps/api/`, OpenAPI en `apps/api/openapi.json`). Ningún ejemplo de este documento es una respuesta real de Renfe, CRTM ni de ningún proyecto de terceros — **todos los JSON de ejemplo son sintéticos** y están marcados como tales; reflejan la forma del contrato, no un payload observado. Los endpoints `live`/`lines`/`stations`/`health` están implementados y probados contra datos reales (PostgreSQL + GTFS/OSM). Los endpoints `history`/`metrics` siguen como propuesta — ver "Endpoints diferidos" más abajo.

## Discrepancia a reconciliar (antes de MP-013)

`deep-research-report.md` propone:

```text
GET /api/v1/live/vehicles
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines
GET /api/v1/lines/{line_id}
GET /api/v1/stations/{station_id}
GET /api/v1/history/lines/{line_id}
GET /api/v1/history/trips/{trip_id}
GET /api/v1/quality/feeds
GET /api/v1/metrics/lines/{line_id}
GET /api/v1/metrics/stations/{station_id}
```

`MADRID_PULSE_BRIEF_INICIAL.md` propone un subconjunto distinto:

```text
GET /api/v1/health
GET /api/v1/live/trains
GET /api/v1/trains/{train_id}
GET /api/v1/stations
GET /api/v1/history/trains
```

**Decisión de trabajo confirmada en MP-013 (ADR-0005):** la nomenclatura `vehicles` del informe completo (más alineada con GTFS-RT, donde la entidad es el vehículo, no "el tren" como concepto de negocio) y la fusión de `/api/v1/health` del brief con `/api/v1/quality/feeds` del informe completo, ya que cubren el mismo propósito de observabilidad de fuente.

## Endpoints implementados (MP-013)

```text
GET /api/v1/health                     -- salud real por feed (source_ingestion_run)
GET /api/v1/live/vehicles               -- todos los vehículos vistos, map-matched vía MP-012
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines
GET /api/v1/lines/{line_id}
GET /api/v1/stations
GET /api/v1/stations/{station_id}
```

### Geometría real de línea (extensión aditiva MP-014)

`LineOut` incorpora `geometry`, nullable. Cuando el proceso tiene un corredor
OSM asociado exactamente al par `(network_id, line_id)`, contiene:

- `segments`: lista de polilíneas continuas, cada coordenada como `{lat, lon}`.
  Los segmentos permanecen separados: nunca se concatenan atravesando un hueco
  real de `packages.geo.Corridor.segments`.
- `stations`: paradas GTFS proyectadas con `Corridor.project_station`, ordenadas
  por `distance_along_m` sobre el corredor cargado.

Si no hay corredor asociado a una línea, `geometry` es `null`; la API nunca
fabrica una forma conectando estaciones. La asociación actual sigue siendo
honesta con `LoadedNetwork`: un único corredor configurado mediante
`network_id`/`short_name`, sin literales de línea en la lógica (DEC-031).

Forma abreviada del contrato (valores omitidos deliberadamente):

```json
{
  "line_id": "<short_name resuelto>",
  "network_id": "<network_id resuelto>",
  "route_ids": ["<route_id completo>"],
  "geometry": {
    "segments": [[{"lat": 0.0, "lon": 0.0}]],
    "stations": [{
      "station_id": "<stop_id>",
      "name": "<stop_name>",
      "lat": 0.0,
      "lon": 0.0,
      "distance_along_m": 0.0
    }]
  }
}
```

Este ejemplo describe únicamente la forma del contrato; no representa una
geometría, estación ni identificador reales.

## Endpoints de snapshot/catálogo/tablero (MP-019, [ADR-0014](adr/0014-snapshot-and-temporal-contract.md))

```text
GET /api/v1/catalog                     -- catálogo cacheable (ETag/304), versionado por GTFS + geometría
GET /api/v1/snapshot                    -- snapshot operativo ligero (no-store)
GET /api/v1/stations/{station_id}/board -- tablero por servicios + calendario + actualizaciones
```

Son **aditivos**: ningún campo ni endpoint anterior cambia de nombre, tipo o
significado, así que `/api/v1` conserva la compatibilidad y no se abre `/v2`.
El esquema congelado está en `apps/api/openapi.json`.

### Separación catálogo / snapshot

`GET /api/v1/catalog` contiene solo lo inmutable por proceso: líneas, patrones
(`pattern_id` = `route_id` + secuencia ordenada de paradas, MP-018), estaciones,
cobertura geométrica `validated`/`partial`/`pending` y la geometría física
publicada **una sola vez** en `geometries[]` y referenciada por
`geometry_version` desde cada patrón (dos líneas con tramo compartido no
duplican la polilínea). Se versiona con `catalog_version`, derivado de
`gtfs_version` **y** `geometry_catalog_version`, y se sirve con `ETag`;
`If-None-Match` devuelve `304`. Un patrón sin corredor validado publica
`distance_along_m: null` en sus estaciones — no se estima una longitud de arco
que no existe.

`GET /api/v1/snapshot` contiene solo lo operativo y se sirve con
`Cache-Control: no-store`, para que ningún dato viejo se rotule como nuevo.
Referencia el catálogo por versión (`catalog_ref`), no lo reenvía.

### Identidad vs revisión ordenable

```json
{
  "snapshot_id": "sha256:<hash de contenido>",
  "snapshot_id_is_sortable": false,
  "revision": {
    "scope": "pg:<system_identifier>",
    "scope_source": "database_system_identifier",
    "sequence": 8,
    "generated_at": "2026-11-20T14:34:46Z",
    "tiebreak": "sha256:<hash de contenido>"
  }
}
```

`snapshot_id` es **identidad de contenido**: dos snapshots generados en
instantes distintos sobre los mismos datos comparten id. Ordenar hashes o UUID
como si fueran secuencias está prohibido por contrato, y el propio payload lo
declara.

Regla de contrato para el cliente: con `scope` igual, ordenar por `sequence`
y descartar toda respuesta de `sequence` menor; con `sequence` igual,
desempatar por `generated_at` y luego por `tiebreak`. Con `scope` **distinto**,
no comparar secuencias: es una discontinuidad (restauración, otro clúster), no
un rebobinado. `sequence` es `max(source_ingestion_run.id)` considerado:
monotónica de verdad, sobrevive a reinicios del proceso de API y **no avanza
con el reloj** — si el colector se detiene, no avanza.

### Las tres coordenadas, separadas

Por circulación el snapshot publica tres bloques distintos, nunca fundidos:

- `raw`: lo que publicó la fuente, sin retoque, con `gps_observed_at` y
  `payload_hash`. Ausente es `null`, nunca `(0, 0)`.
- `map_matched`: **solo** cuando hubo proyección real sobre un patrón validado
  (`resolution: "map_matched"`), con `progress_m`, `distance_from_raw_m` y
  `geometry_version`. Si no la hubo, el bloque entero es `null`.
- `rendered`: la coordenada de presentación, con `rendering_method`,
  `coordinate_space` (`map_matched` / `raw` / `schedule`), `confidence_index`
  (índice heurístico **no calibrado**, no una probabilidad), los instantes
  separados y, cuando procede, la `progress_envelope`.

`geometry_version` solo es lícito en `rendered` cuando
`coordinate_space == "map_matched"`; en un fallback bruto se publica
`geometry_candidate_version`, que identifica la geometría candidata/contextual
y **no** acredita que haya habido map-matching. El modelo lo valida en
construcción.

`position` (los cuatro estados de [ADR-0004](adr/0004-position-model.md)) se
conserva sin cambios por compatibilidad. `rendered` es la autoridad de
presentación; ambos derivan del mismo ancla, publicado en
`rendered.anchor_observed_at`.

### Los cinco instantes

`timestamps` separa `gps_observed_at`, `received_at`, `feed_published_at`,
`snapshot_generated_at` y `display_at`. La hora de un sondeo exitoso nunca se
usa como edad de un dato de origen antiguo, y `feed_published_at` es `null`
cuando la ejecución de ingesta no registró cabecera — nunca `received_at` en su
lugar.

### `rendering_method` y la envolvente de progreso

| Método | Significado |
|---|---|
| `anchor` | La coordenada publicada **es** el ancla (sin avance: `display_at == reference_at`, o el horario no autoriza avanzar todavía, o hay espera programada). |
| `interpolated_between_known_anchors` | `display_at` cae entre dos anclas reales. Solo con retraso de presentación declarado; jamás en directo. |
| `extrapolated_from_last_anchor` | Hay ancla pasada y no hay ancla futura: avance acotado por horario, topología y límites físicos. Caso normal del directo. |
| `schedule_only` | Sin observación utilizable: posición derivada solo del horario. |
| `stale_frozen` | El ancla superó `stale_after_s` o se agotó el horizonte: congelada **en el ancla**, sin envolvente y sin `valid_until`. |
| `unlocated` | No se puede publicar coordenada defendible. La circulación sigue en lista/tablero, no en el mapa. |

La `progress_envelope` es una sola expresión, válida para
`reference_at <= t <= rendered.valid_until`:

```text
t0 = dwell_until or reference_at
progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0), max_progress_m)
```

El cliente la convierte en coordenada **sobre la longitud de arco** del patrón
que ya tiene del catálogo; nunca interpola lat/lon en recta entre estaciones.
`speed_mps == 0` es avance nulo declarado, no dato ausente; `dwell_until` es
una espera programada real durante la que el progreso se mantiene. Un patrón
sin corredor validado **no** recibe envolvente: sin longitud de arco no hay
avance defendible.

Limitación declarada: tras la espera del propio ancla la envolvente usa una
sola tasa media hasta el fin del horizonte, así que no reproduce esperas
*intermedias* dentro de él — publicarlas exigiría el array de puntos futuros
que el encargo de MP-019 prohíbe.

### ETA con procedencia, nunca fabricada

```text
eta_method = schedule | operator_delay_on_schedule | unavailable
```

| Caso | `method` | `eta_at` | `reason` |
|---|---|---|---|
| Sin dato de operador | `schedule` | horario planificado | `no_operator_delay_reported` |
| Retraso del operador vigente | `operator_delay_on_schedule` | horario + retraso | — (con `approximation`) |
| Retraso del operador caducado | `schedule` | horario planificado | `operator_delay_expired` |
| Viaje cancelado | `unavailable` | `null` | `trip_canceled` |
| Parada anterior a la próxima del operador | `unavailable` | `null` | `passed_or_skipped_per_operator_next_stop` |
| Sin hora de horario | `unavailable` | `null` | `schedule_time_missing` |

`scheduled_at` se conserva siempre que exista, incluso cuando la ETA no está
disponible. El `delay` del feed es de nivel viaje: aplicarlo a cada parada se
publica marcado como `approximation: "trip_level_delay_applied_to_all_stops"`,
nunca en silencio. No se introduce ningún modelo predictivo propio.

### Día de servicio GTFS: resuelto por circulación, no por reloj civil

Cada circulación del snapshot publica su propio `service_date`, y cada entrada
del tablero el suyo (`BoardEntryOut.service_date`), que tras medianoche puede
ser el **día anterior** al civil: un viaje con horas `24:xx`/`25:xx` sigue
perteneciendo al día de servicio en que empezó. `StationBoardOut` publica
además `service_dates_considered` con los días realmente cruzados.

Esos días se derivan de la **ventana completa** del tablero
(`lookback_s`/`lookahead_s`), no del instante de consulta: una llamada `24:xx`
del día anterior sigue dentro de la retrospectiva pedida después de que el
horizonte del feed deje de alcanzar el instante actual, y las primeras llamadas
del día siguiente pueden caer dentro de la anticipación antes de la medianoche.
Las entradas se ordenan por **instante absoluto**, así que mezclar dos días de
servicio no altera el orden.

La ventana de ambigüedad tras medianoche sale del propio feed —el máximo
`arrival`/`departure` del GTFS cargado menos 24 h— y nunca de una constante:
con el núcleo Madrid completo son 3 180 s (máximo real `24:53`); con un feed sin
horas extendidas es `0.0` y no existe ventana. Dentro de ella se comprueba
**primero** el día anterior, y un día candidato solo se acepta si el
`service_id` del viaje está realmente programado en él *y* el instante actual
cae dentro de su horario publicado; si ningún candidato lo contiene, se conserva
la fecha civil. Nunca se fabrica una pertenencia.

`circulation_status` se evalúa contra el calendario de **ese** día resuelto, de
modo que una circulación `24:xx` en curso es `active` y no `expired`.

Las horas GTFS se convierten a instantes con
`packages.movement.schedule.service_day_instant`, la **única** implementación de
esta aritmética, inversa exacta de `service_seconds`: el día de servicio se mide
sobre el reloj de pared de Europe/Madrid, de modo que los dos días del año en
que cambia la hora tienen 23 o 25 horas reales sin desplazar los horarios
publicados. Dos casos límite documentados: una hora de reloj que no existe
(adelanto) se resuelve con el desplazamiento previo al salto y una hora ambigua
(atraso) toma su primera ocurrencia.

### Recuentos sin ambigüedad

`counts` publica **dos particiones independientes y exactas** de
`vehicles_total`: `by_rendering_method` (cómo se obtuvo la coordenada) y
`by_coordinate_space` (a qué espacio pertenece). Son cortes distintos de lo
mismo —una circulación congelada sobre el corredor cuenta en `stale_frozen` y
en `map_matched` a la vez— y cada diccionario suma exactamente
`vehicles_total`. No se mezclan los dos criterios en un mismo contador, y las
claves ausentes son ausencia de casos, no `0` artificiales.

### Tablero de estación

Se calcula con `packages.gtfs.catalog.scheduled_trip_instances_for_date`
(calendario + `calendar_dates` + `stop_times`, horas `24:xx` incluidas) cruzado
con `trip_update` y observaciones — **no** con "trenes cercanos" por
proximidad. `circulation_source` distingue `scheduled_only` (programado por
GTFS, sin observación: nunca se presenta como Live confirmado) de `observed`.
`coverage.operator_delay_coverage_pct` es `null` cuando el denominador es cero:
un porcentaje sin muestra no es `0.0` (DEC-009).

`limitations[]` declara expresamente lo que el modelo canónico no soporta: el
`stop_time_update` por parada no está persistido (solo `next_stop_id`, el
primer no-`SKIPPED`), así que no hay evidencia directa de `SKIPPED` por parada;
`relative_to_operator_next` es una señal derivada y declarada, no esa
evidencia.

### Reloj explícito de replay

`/api/v1/snapshot` y el tablero aceptan `?at=<ISO-8601 con zona>` **solo en
modo replay**; en `live` se rechaza con `400`, porque un instante arbitrario
permitiría falsificar edades. La respuesta siempre publica `generated_at` y
`display_at` realmente usados, además de `mode`.

## Histórico frío (`/api/v1/history/*`, MP-021)

Recursos **nuevos**, no una extensión de los de MP-019: se sirven desde el
Parquet que escribe `services/snapshotter` leyéndolo con DuckDB en solo
lectura, sin tocar PostgreSQL. `/api/v1/snapshot` y `/api/v1/catalog`
(ADR-0014) quedan exactamente como estaban. Ver
[ADR-0015](adr/0015-cold-archive-and-history-contract.md).

```text
GET /api/v1/history/days                                    -- días archivados, con sus denominadores
GET /api/v1/history/lines?service_date=                     -- daily_line_metrics del día
GET /api/v1/history/stations?service_date=&limit=           -- station_daily_metrics del día
GET /api/v1/history/circulations?service_date=&line=&only=  -- circulation_daily_history, filtrable
    only = all | observed | unobserved | canceled | operator_only | unscheduled
GET /api/v1/history/circulations/{vehicle_id}/{trip_id}?service_date=   -- detalle + observaciones crudas
```

Reglas que el contrato garantiza:

- **La identidad es la de Live.** La ruta de detalle usa vehículo + viaje + día
  de servicio, los mismos tres valores que lleva la URL del frontend
  (`?train=&trip=&sd=`), para que ir de Live al histórico y volver no requiera
  traducir ninguna clave. Un viaje programado sin observar se direcciona con
  `vehicle_id` = `-`, porque no tiene vehículo.
- **Ningún porcentaje viaja sin su denominador.** `delay_coverage_pct` va
  siempre con `trips_scheduled`, y `on_time_pct_of_covered` con
  `trips_with_delay_data`. Este último es `null` -- nunca `0.0` -- cuando no
  hay muestra (DEC-009).
- **Los huecos son datos, no ausencias — y una anulación no es un hueco.**
  `coverage` clasifica cada circulación en una sola categoría y
  `/history/days` publica un recuento por cada una
  (`circulations_unobserved`, `circulations_canceled`,
  `circulations_operator_only`, `circulations_unscheduled`), de modo que las
  cinco particionan el día. `only=unobserved` devuelve el hueco **real** (ni
  posición ni parte del operador); un servicio que el operador declaró
  `CANCELED` sale por `only=canceled`, porque el tren no circuló y atribuirlo
  a un fallo de captura sería culpar al colector de algo que no hizo.
- **`NULL` y cero medido no son lo mismo.** Las métricas de posición son
  `null` exactamente cuando `observed` es `false`; las de parte del operador,
  cuando no hubo ninguno. `delay_reported_count: 0` con
  `trip_updates_count >= 1` es un cero **medido** — hubo parte y no traía
  retraso — y es el caso normal de una cancelación, porque el feed no publica
  `delay` cuando `scheduleRelationship` es `CANCELED`.
- **Un día no archivado responde `404`**, con el comando que lo archivaría en
  el detalle del error -- nunca un día vacío con métricas a cero, que se leería
  como "ese día no hubo servicio".
- **`truncated`** declara que una lista alcanzó el límite de consulta, para que
  nadie tome una lista recortada por el total del día.

### Endpoints diferidos (propuesta, no implementada)

```text
GET /api/v1/metrics/lines/{line_id}
GET /api/v1/metrics/stations/{station_id}
```

**Actualizado en MP-015 (DEC-033) y MP-021 (DEC-040):** `daily_line_metrics`/`station_daily_metrics` se calculan de verdad desde MP-015 en `services/snapshotter/gold.py` (diferidas desde MP-009, DEC-021, hasta que la resolución `route_id`/`station_id` existiera), y desde MP-021 **sí** están expuestas, por `/api/v1/history/lines` y `/api/v1/history/stations`. Lo que sigue sin implementarse son los `metrics/*` de arriba, pensados como series por línea/estación a lo largo de varios días; con dos días archivados no hay serie que publicar todavía.

Todos bajo versionado explícito `/api/v1/`; un cambio incompatible de contrato requiere `/api/v2/`, nunca una mutación silenciosa de `/v1/`.

## Ejemplo sintético — vehículo en vivo

**Este ejemplo es sintético, generado para ilustrar el contrato. No representa una respuesta real de Renfe ni de Madrid Pulse.**

```json
{
  "vehicle_id": "renfe:cercanias-madrid:SYNTHETIC-0001",
  "trip_id": "SYNTHETIC-TRIP-0001",
  "line": "C5",
  "position": {
    "lat": 40.3501,
    "lon": -3.8312,
    "mode": "observed",
    "confidence": 1.0
  },
  "delay": {
    "seconds": 184,
    "coverage": "reported"
  },
  "observation": {
    "reported_at": "2026-11-18T09:00:00Z",
    "received_at": "2026-11-18T09:00:03Z",
    "age_s": 12
  },
  "quality": {
    "stale": false,
    "flags": []
  },
  "circulation_status": "active"
}
```

### Campos obligatorios de frescura/calidad

Toda respuesta de vehículo en vivo **debe** incluir:

- `position.mode`: uno de `observed | estimated | stale | scheduled` (ver `docs/DATA_QUALITY.md`).
- `position.confidence`: `0.0`–`1.0`, decreciente con la edad del dato.
- `observation.age_s`: segundos desde la última observación real.
- `delay.coverage`: `reported | missing` — nunca se omite ni se sustituye por `0` cuando no hay dato.
- `quality.flags`: lista de flags activos (puede estar vacía, nunca ausente).
- `circulation_status` (MP-017): uno de `active | expired | unresolved` — separa "¿el `service_id` de este viaje está programado para la fecha de servicio actual?" de `quality.stale` (que solo mide antigüedad del GPS). `unresolved` cuando el `route_id` no resuelve; nunca se fabrica `active`/`expired` sin resolución real.

### Ejemplo sintético — salud de feed (`/api/v1/health`)

```json
{
  "feeds": [
    {
      "feed_name": "vehicle_positions",
      "status": "ok",
      "source_timestamp": "2026-11-18T09:00:00Z",
      "data_age_s": 8,
      "poll_age_s": 2,
      "unchanged_for_s": 0,
      "entities": 42,
      "rejected": 0
    },
    {
      "feed_name": "trip_updates",
      "status": "stale",
      "source_timestamp": "2026-11-18T08:58:10Z",
      "data_age_s": 118,
      "poll_age_s": 4,
      "unchanged_for_s": 118,
      "entities": 0,
      "rejected": 0
    }
  ],
  "mode": "live",
  "gtfs_version": "sha256:ejemplo-sintetico",
  "gtfs_valid_from": "2026-11-18",
  "gtfs_valid_until": "2026-12-06"
}
```

Este patrón de observabilidad por feed está inspirado conceptualmente en el modelo público de Valfiguer (`ok/stale/data_age_s/unchanged_for_s`), **reimplementado de forma independiente** — no se consume su API ni se copia su código.

### Ejemplo sintético — métricas de línea con cobertura explícita

```json
{
  "line": "C5",
  "service_date": "2026-11-17",
  "trips_scheduled": 120,
  "trips_with_delay_data": 94,
  "delay_coverage_pct": 78.3,
  "on_time_pct_of_covered": 87.2,
  "disclaimer": "on_time_pct_of_covered se calcula solo sobre los viajes con dato de retraso disponible (delay_coverage_pct)."
}
```

**Regla no negociable:** nunca se publica un porcentaje de puntualidad sin su `coverage` asociado en el mismo payload, para evitar que "87% de puntualidad" se interprete como representativo de todo el servicio cuando solo cubre el 78% de los viajes.

## Versionado y metadatos de snapshot

Cuando exista publicación de snapshots en CDN (post-MP-007), cada snapshot debe incluir:

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-11-18T09:00:10Z",
  "source_feed_runs": ["<ingestion_run_id>", "..."],
  "data": { "...": "..." }
}
```

`schema_version` sigue versionado semántico independiente del versionado de la URL de la API (`/v1/`), porque un snapshot estático puede evolucionar su esquema interno sin requerir un cambio de ruta de API.
