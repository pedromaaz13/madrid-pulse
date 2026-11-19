# Motor de movimiento (`packages/movement`)

Implementación de MP-012 y consumidor directo de `packages/gtfs` y
`packages/geo`. El paquete no conoce identificadores de una línea concreta:
recibe una topología y un corredor ya seleccionados por configuración.

## Contrato de salida

`MovementEngine.position()` devuelve `MovementPosition`, estructura lista para
MP-013 con:

- `position_mode`: `observed`, `estimated`, `stale` o `scheduled`;
- `confidence`, `age_s` y `source` explícitos;
- coordenada siempre map-matched, `progress_m` en sentido de marcha y timestamps;
- anomalías estructuradas (`off_track`, `backward_jump`,
  `station_skip_anomaly`, `implausible_speed`).

`age_s=None` significa que no existe observación; nunca se convierte ausencia
en cero. Una muestra presente pero inutilizable conserva su edad y timestamp,
usa `scheduled` solo si tampoco existe una observación plausible anterior y
expone el motivo en `anomalies`. Una coordenada `estimated`, `stale` o
`scheduled` nunca usa la fuente ni el modo de una coordenada `observed`.

## Pipeline

1. `Topology.resolve_trip_route_id` y `stop_times_for_trip` resuelven viaje y
   horario; no se reimplementa la topología.
2. `Corridor.project_station` proyecta paradas y observaciones sobre vía real;
   no se reimplementa la geometría. Un corredor con huecos se rechaza para un
   viaje individual en vez de atravesarlo artificialmente.
3. El perfil horario interpola progreso entre `stop_times`, admite horas GTFS
   mayores de 24 y calcula el día de servicio en `Europe/Madrid` desde un
   `service_date` explícito.
4. La última observación plausible fija un offset temporal: hora observada
   menos hora programada en ese mismo progreso. La estimación consulta el
   horario con ese offset.
5. La estimación nunca retrocede y queda limitada por velocidad y aceleración.
   Una observación imposible se marca y no borra la anterior plausible.

## Calibración 2026-11-19

Se mantienen como defaults configurables `60 s` para `observed → estimated` y
`180 s` para `estimated → stale`. MP-003 midió `vehicle_positions` cada
~20–22 s: los cortes representan aproximadamente 3 y 8 actualizaciones
perdidas, un margen razonable frente a jitter sin llamar “en vivo” a un punto
con varios minutos de edad.

Hay dos umbrales deliberadamente distintos:

- `max_estimated_speed_kmh=160`: límite físico conservador de la trayectoria
  fabricada por el motor, junto con `1.2 m/s²` de aceleración;
- `unusable_jump_speed_kmh=900`: filtro de discontinuidad del feed, no velocidad
  atribuida al tren. MP-008 ya encontró 12/117 pares crudos a 246–787 km/h. La
  integración de MP-012 sobre las 668 observaciones reales obtuvo 177 puntos a
  ≤200 m del corredor y un máximo map-matched de 666,4 km/h. Un corte ferroviario
  convencional (p. ej. 200 km/h) descartaría evidencia real; 900 conserva esos
  saltos y todavía rechaza casos sintéticos físicamente extremos.

`off_track_distance_m=200` se apoya en la validación independiente de MP-011:
las 23 estaciones reales quedaron a ≤63,7 m del eje OSM. Es un margen operativo,
no una afirmación sobre precisión del feed.

## Flags y persistencia

Los tres flags diferidos por MP-008 ya se calculan:

- `off_track`: distancia al corredor superior al umbral;
- `backward_jump`: retroceso map-matched superior a 250 m (y la muestra deja de
  ser utilizable a partir de 1.000 m);
- `station_skip_anomaly`: salto hacia delante de más de una `stop_sequence`
  resuelta literalmente para el trip.

Se exponen en `MovementPosition.anomalies` para MP-013. No se persisten todavía
en `data_quality_event`: MP-012 no crea una tabla de posiciones derivadas y el
`CHECK` v1 solo admite flags asociados a observaciones crudas de MP-008. Añadir
persistencia sin un dueño/clave de resultado derivado mezclaría ambos niveles;
si MP-013 decide persistir snapshots derivados, deberá hacerlo mediante una
migración explícita, sin perder estos flags del contrato en memoria.

## Pruebas

```sh
.venv/bin/python -m unittest discover -s packages/movement/tests -p 'test_*.py' -v
```

La integración PostgreSQL es de solo lectura, exige el volumen local de
`madrid-pulse` y confirma `668 → 668` filas antes/después.
