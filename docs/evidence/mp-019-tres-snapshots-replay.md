# MP-019 — Tres snapshots (normal / parcial / congelado) sobre capturas reales

Evidencia **ejecutada**, no descrita. Reproducible con
`apps/api/tools/replay_three_snapshots.py` (comando exacto en su docstring).

## Condiciones

| Dimensión | Valor |
|---|---|
| Capturas | `1532` y `1533` del kit de Hito 3 (`data/hito-03/replay/`), reales de Renfe, `sha256` en `manifest.json`. Cabeceras: `1532` = `2026-11-20T14:32:04Z`, `1533` = `2026-11-20T14:33:21Z` (77 s de separación) |
| GTFS | ZIP completo congelado del kit (`fomento_transit.zip`, `sha256:c5b40823…`), núcleo Madrid completo: 42 `route_id`, 12 líneas, 103 patrones |
| Geometría | fixtures OSM reales de MP-011/MP-018 (28 patrones `validated`, 3 `partial`, 72 `pending`) |
| PostgreSQL | contenedor **fresco y desechable** (`postgis/postgis:17-3.5`, `127.0.0.1:5434`), migraciones `0001` + `0002` aplicadas desde cero. No se tocó la base de desarrollo |
| Ingesta | colector real (`services.collector.collector.run_cycle`) con `fetcher` inyectado, mismo patrón que `tests/e2e/test_replay.py`. No se llamó a Renfe |
| Reloj | controlado y explícito (modo `replay`), no la hora del sistema |

## Ingesta real

```text
  ingest 1532/vehicle_positions: entities=463 inserted=119 deduped=0 skipped=344
  ingest 1532/trip_updates:      entities=469 inserted=122 deduped=0 skipped=347
  ingest 1532/alerts:            entities=72  inserted=4   deduped=0 skipped=68
  ingest 1533/vehicle_positions: entities=468 inserted=121 deduped=0 skipped=347
  ingest 1533/trip_updates:      entities=474 inserted=77  deduped=47 skipped=350
  ingest 1533/alerts:            entities=73  inserted=0   deduped=4  skipped=69
```

Los `119` / `121` vehículos de Madrid y los `skipped` por núcleo coinciden con
los recuentos congelados del kit (MP-016). La deduplicación de `1533` es real:
47 actualizaciones de viaje idénticas no se reinsertan (ADR-0010) y **no**
resetean la edad del dato.

## A — Snapshot normal (tras `1532`)

```json
{
 "generated_at": "2026-11-20T14:32:14+00:00",
 "snapshot_id": "sha256:e1f921b37bd69ea871c11d8fc1e8b9b16363225aaef6585b1477a12f8922104d",
 "revision": {"scope": "pg:<system_identifier del contenedor>", "sequence": 3},
 "vehicles_total": 119,
 "rendering_methods": {"anchor": 75, "extrapolated_from_last_anchor": 44},
 "coordinate_spaces": {"map_matched": 44, "raw": 75},
 "with_operator_delay": 119, "without_operator_delay": 0,
 "feeds": {"alerts": "ok", "trip_updates": "ok", "vehicle_positions": "ok"},
 "degraded": []
}
```

Lectura honesta: **44 de 119** circulaciones tienen coordenada `map_matched`
porque solo 28 de los 103 patrones tienen corredor OSM validado tras MP-018.
Las otras 75 publican su GPS **bruto etiquetado** (`coordinate_space: "raw"`,
`rendering_method: "anchor"`), sin envolvente de progreso y sin
`geometry_version` — no se proyectan sobre un corredor ajeno ni se les inventa
un avance. Ninguna desaparece del snapshot.

## B — Snapshot normal (tras `1533`)

```json
{
 "generated_at": "2026-11-20T14:33:31+00:00",
 "snapshot_id": "sha256:510314e39f5f28ad54edf0b0fc04291ea164fbd8c47dbcdba74158d2a7ecf351",
 "revision": {"scope": "pg:<system_identifier del contenedor>", "sequence": 6},
 "vehicles_total": 122,
 "rendering_methods": {"anchor": 78, "extrapolated_from_last_anchor": 44},
 "coordinate_spaces": {"map_matched": 44, "raw": 78},
 "feeds": {"alerts": "ok", "trip_updates": "ok", "vehicle_positions": "ok"},
 "degraded": []
}
```

`sequence` 3 → 6 dentro del **mismo** `scope`; `snapshot_id` distinto porque el
contenido cambió. 122 vehículos: los 119 de `1532` más 3 que solo aparecen en
`1533`; ninguno se pierde al llegar la captura nueva.

### Movimiento real entre las dos capturas

**13 circulaciones map-matcheadas avanzaron** de verdad en los 77 s entre
capturas (muestra de 5):

| `vehicle_id` | Línea | `progress_m` 1532 | `progress_m` 1533 | `distance_from_raw_m` | Método | `speed_mps` de la envolvente |
|---|---|---:|---:|---:|---|---:|
| 19656 | C5 | 39 595,0 | 41 198,7 | 4,2 | `extrapolated_from_last_anchor` | 22,04 |
| 19660 | C5 | 30 046,5 | 33 092,8 | 1,7 | `extrapolated_from_last_anchor` | 13,96 |
| 19664 | C5 | 24 805,7 | 26 272,1 | 0,4 | `extrapolated_from_last_anchor` | 14,07 |
| 19670 | C5 | 5 739,1 | 7 371,1 | 2,3 | `extrapolated_from_last_anchor` | 17,62 |
| 19671 | C5 | 29 746,8 | 31 950,8 | 20,8 | `extrapolated_from_last_anchor` | 6,78 |

El avance publicado es progreso sobre la **longitud de arco** del patrón, con
`distance_from_raw_m` real (0,4–20,8 m del eje OSM) y una velocidad de
envolvente dentro de los límites físicos de `MovementThresholds`
(`max_estimated_speed_kmh = 160` → 44,4 m/s). La etiqueta es
`extrapolated_from_last_anchor` y no `interpolated_between_known_anchors`
porque en cada snapshot no existe ancla futura: es estimación declarada, no
interpolación observada.

## C — Snapshot parcial: `trip_updates` devuelve JSON inválido

```text
  ciclo trip_updates: status=error error=1 validation error for RawTripUpdatesFeed
                                          Invalid JSON: key must be a string...
```

```json
{
 "generated_at": "2026-11-20T14:34:46+00:00",
 "revision": {"scope": "pg:<system_identifier del contenedor>", "sequence": 7},
 "vehicles_total": 122,
 "rendering_methods": {"anchor": 78, "extrapolated_from_last_anchor": 44},
 "with_operator_delay": 122,
 "feeds": {"alerts": "ok", "trip_updates": "error", "vehicle_positions": "ok"},
 "degraded": [{"resource": "delays_and_eta", "status": "error"}]
}
```

- El snapshot **no se vacía**: siguen las 122 circulaciones.
- Se degrada **solo** el recurso afectado (`delays_and_eta`); `vehicles` y
  `alerts` siguen `ok`.
- Los 122 retrasos del operador siguen publicados con su `observed_at` y su
  edad reales: el último resultado válido sobrevive al fallo del feed, con
  aviso visible, y no se rejuvenece.

## D — Snapshot congelado: colector detenido, reloj +1 h

```json
{
 "generated_at": "2026-11-20T15:33:21+00:00",
 "revision": {"scope": "pg:<system_identifier del contenedor>", "sequence": 7},
 "vehicles_total": 122,
 "rendering_methods": {"stale_frozen": 122},
 "coordinate_spaces": {"map_matched": 44, "raw": 78},
 "feeds": {"alerts": "stale", "trip_updates": "error", "vehicle_positions": "stale"},
 "degraded": [
   {"resource": "alerts", "status": "stale"},
   {"resource": "delays_and_eta", "status": "error"},
   {"resource": "vehicles", "status": "stale"}
 ]
}
```

Las 122 pasan a `stale_frozen`: congeladas **en el ancla**, sin envolvente de
progreso y sin `valid_until`. `revision.sequence` se queda en 7 porque no entró
ninguna ejecución de ingesta nueva — la revisión **no avanza sola con el
reloj**, que es exactamente lo que evita rotular como nuevo un dato viejo.

## Invariantes comprobadas en la propia ejecución

```json
{
 "revision_monotonica_en_ambito": true,
 "snapshot_id_declarado_no_ordenable": true,
 "parcial_no_vacia_vehiculos": true,
 "parcial_degrada_solo_el_recurso_afectado": true,
 "congelado_conserva_el_ultimo_dato": true,
 "congelado_no_rejuvenece": true,
 "congelado_todo_stale_frozen_o_schedule": true
}
```

`congelado_no_rejuvenece` compara `gps_observed_at` de cada vehículo entre el
snapshot B y el D: ninguno cambió pese a los 60 minutos transcurridos y a los
sondeos posteriores de otros feeds.

## Recuentos finales del contenedor desechable

`vehicle_position_observation / trip_update_observation / service_alert /
source_ingestion_run / data_quality_event` = **240 / 199 / 4 / 7 / 2**.

Los valores absolutos de `revision.scope`, `snapshot_id` y `sequence` cambian
entre ejecuciones porque el ámbito es el `system_identifier` del clúster
—distinto en cada contenedor desechable— y porque los `id` de
`source_ingestion_run` no son contiguos cuando un ciclo falla. Lo que se
comprueba, y lo que el contrato promete, es la **relación** entre ellos:
monotonía dentro del mismo ámbito e identidad estable ante el mismo contenido.

Los 2 `data_quality_event` los generó el motor de calidad de MP-008 sobre las
capturas reales; no son fallos de esta tarea. La base de desarrollo
(`127.0.0.1:5433`) conservó `668 / 484 / 3 / 120 / 0` antes y después, sin
residuo.

## Nota de proceso sobre el contenedor fresco

Primera ejecución de la suite completa contra un contenedor recién creado:
2 errores `psycopg.OperationalError: server closed the connection unexpectedly`.
**No era un fallo del repositorio**: el `entrypoint` de la imagen arranca un
servidor temporal para `initdb`, lo apaga y arranca el definitivo, y
`pg_isready` ya responde con el temporal. Esperando la línea
`ready to accept connections` **posterior** a
`PostgreSQL init process complete`, la suite completa pasa en verde
(206 tests, 5 `skip` explícitos) de forma repetida. Queda registrado porque
cualquiera que repita esta evidencia se topará con lo mismo.
