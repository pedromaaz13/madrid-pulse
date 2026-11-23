# MP-022 — Matriz de cobertura del corte congelado 1533

Esta tabla es una vista legible del CSV canónico. El corte es una fixture congelada, **no producción en vivo**. La cobertura agregada se calcula como suma de numeradores / suma de denominadores; nunca como media de porcentajes por línea.

Cobertura de resolución ponderada: **121/121 (100.0%)**. Catálogo: **42 rutas / 103 patrones / 12 líneas**.

| Línea | Rutas | Patrones | Programados | GPS corte | Resueltos | Matched | Dibujables | Edad p50/p95 (s) | Cobertura ruta | Geometría | ETA estaciones | Motivos desconocidos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | 2 | 4 | 144 | 7 | 7 | 0 | 7 | 10.0/10.0 | 7/7 (100.0%) | 0/4 | 4/7 | 0 |
| C10 | 5 | 13 | 145 | 13 | 13 | 0 | 13 | 10.0/10.0 | 13/13 (100.0%) | 0/13 | 18/21 | 0 |
| C2 | 3 | 14 | 164 | 17 | 17 | 0 | 17 | 10.0/10.0 | 17/17 (100.0%) | 0/14 | 20/20 | 0 |
| C3 | 2 | 4 | 118 | 13 | 13 | 0 | 13 | 10.0/10.0 | 13/13 (100.0%) | 0/4 | 13/13 | 0 |
| C4 | 2 | 5 | 13 | 0 | 0 | 0 | 0 | null (sin GPS) | null (denominador 0) | 5/5 | 0/10 | 0 |
| C4a | 2 | 8 | 124 | 10 | 10 | 10 | 10 | 10.0/10.0 | 10/10 (100.0%) | 8/8 | 15/15 | 0 |
| C4b | 2 | 8 | 122 | 12 | 12 | 6 | 12 | 10.0/10.0 | 12/12 (100.0%) | 3/8 | 15/15 | 0 |
| C5 | 5 | 14 | 293 | 28 | 28 | 28 | 28 | 10.0/10.0 | 28/28 (100.0%) | 12/14 | 23/23 | 0 |
| C7 | 6 | 14 | 74 | 10 | 10 | 0 | 10 | 10.0/10.0 | 10/10 (100.0%) | 0/14 | 24/28 | 0 |
| C8a | 5 | 9 | 49 | 5 | 5 | 0 | 5 | 10.0/10.0 | 5/5 (100.0%) | 0/9 | 15/15 | 0 |
| C8b | 4 | 4 | 43 | 5 | 5 | 0 | 5 | 10.0/10.0 | 5/5 (100.0%) | 0/4 | 14/14 | 0 |
| C9 | 4 | 6 | 10 | 1 | 1 | 0 | 1 | 10.0/10.0 | 1/1 (100.0%) | 0/6 | 3/3 | 0 |

## Limitaciones por línea

- **C1:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/4 patrones map-matcheables; fallback raw/tablero; ETA parcial: 4/7 estaciones elegibles
- **C10:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/13 patrones map-matcheables; fallback raw/tablero; ETA parcial: 18/21 estaciones elegibles
- **C2:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/14 patrones map-matcheables; fallback raw/tablero
- **C3:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/4 patrones map-matcheables; fallback raw/tablero
- **C4:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; sin observaciones GPS en el corte; cobertura de ruta null; ETA parcial: 0/10 estaciones elegibles
- **C4a:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada
- **C4b:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 3/8 patrones map-matcheables; fallback raw/tablero
- **C5:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 12/14 patrones map-matcheables; fallback raw/tablero
- **C7:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/14 patrones map-matcheables; fallback raw/tablero; ETA parcial: 24/28 estaciones elegibles
- **C8a:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/9 patrones map-matcheables; fallback raw/tablero
- **C8b:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/4 patrones map-matcheables; fallback raw/tablero
- **C9:** corte congelado 1533; no es producción en vivo; ETA por actualización de viaje aplicada a paradas como aproximación declarada; geometría incompleta: 0/6 patrones map-matcheables; fallback raw/tablero

## Definiciones

- `scheduled_trip_instances`: instancias del día de servicio enumeradas con `calendar.txt` + `calendar_dates.txt` y `stop_times.txt`.
- `feed_vehicle_observations`: vehículos cuyo `observed_at` coincide exactamente con el corte 1533. Una observación anterior conservada no entra en este denominador.
- `resolved_trip_instances`: viajes observados del corte que resuelven contra el GTFS y están programados ese día.
- `drawable_positions`: coordenada defendible para mostrar; puede ser GPS `raw` cuando no existe geometría validada. No equivale a map matching.
- `eta_covered_stops`: estaciones distintas alcanzadas por viajes con actualización de retraso disponible. El retraso es de nivel viaje y su aplicación por parada es una aproximación publicada por el contrato.
- `unknown_reason_count`: circulaciones `unlocated`; cero no significa cobertura geométrica plena.
