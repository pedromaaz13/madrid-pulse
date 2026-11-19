# DATA_QUALITY.md

Estado: **cinco flags del esquema v1 implementados en MP-008** (`stale`,
`implausible_speed`, `missing_id`, `duplicate_snapshot`, `clock_anomaly`);
reglas que requieren geometría ferroviaria diferidas a MP-012. Umbrales marcados
explícitamente como calibrables — no son verdad de diseño y deben ajustarse con
datos operativos.

## Principio rector

Madrid Pulse distingue siempre tres cosas que proyectos similares tienden a mezclar:

1. **Dato ausente** ≠ **cero**. Si no hay dato de retraso, el campo es `null`/ausente con `coverage: "missing"`, nunca `0`.
2. **Posición observada** ≠ **posición interpolada** ≠ **posición estimada**. Cada una se marca explícitamente (`position.mode`), nunca se presenta una interpolación como GPS real.
3. **Cobertura** ≠ **puntualidad**. Un porcentaje de puntualidad sin su cobertura asociada es, por definición, una métrica incompleta — ver `docs/DATA_CONTRACTS.md`.

## Estados de frescura (position_mode)

```text
OBSERVED    0–60 s desde la última observación real      → confidence alta
ESTIMATED   60–180 s desde la última observación real    → confidence decreciente
STALE       >180 s desde la última observación real       → dato considerado obsoleto
SCHEDULED   sin dato de posición en absoluto              → se usa el horario GTFS como única referencia
```

Estos umbrales (`60s`, `180s`) son los propuestos en `deep-research-report.md` y deben tratarse como **punto de partida**, a calibrar en MP-012 contra la frecuencia real de actualización medida en MP-003 (el informe advierte explícitamente no asumir contractualmente ~20/30/60s de polling de Renfe sin medirlo).

## Métricas de frescura por feed

Para cada feed (`vehicle_positions`, `trip_updates`, `alerts`), se expone (inspirado conceptualmente en el modelo de observabilidad de Valfiguer, reimplementado de forma independiente):

```text
status            ok | stale | error
source_timestamp  timestamp reportado por la fuente
data_age_s        edad del dato en segundos
unchanged_for_s    segundos desde el último cambio real de contenido
entities          nº de entidades recibidas en el último poll
rejected          nº de entidades descartadas por validación
```

## Anomalías geográficas y de movimiento

| Flag | Condición (a calibrar) | Acción |
|---|---|---|
| `implausible_speed` | velocidad instantánea implica desplazamiento físicamente imposible entre dos observaciones consecutivas | marcar observación, no descartarla silenciosamente |

> **Nota (MP-005/ADR-0009):** Renfe no emite un campo `speed_kmh` en ningún payload real observado hasta ahora. `implausible_speed` debe calcularse en Madrid Pulse a partir de `distancia(posición_n, posición_n-1) / (observed_at_n - observed_at_n-1)` entre observaciones consecutivas del mismo vehículo, no leerse de un campo de origen. Si en el futuro Renfe empezara a emitir `speed_kmh`/`bearing` (campos opcionales en el esquema canónico, ver `packages/contracts/canonical.py`), podrían usarse como señal adicional, nunca como sustituto único del cálculo propio.

| `off_track` | posición se desvía más de una distancia umbral de la geometría ferroviaria esperada | marcar para revisión de map-matching |
| `backward_jump` | progreso acumulado sobre el shape retrocede de forma no explicable por parada | marcar, no corregir automáticamente sin registro |
| `station_skip_anomaly` | salto de `current_stop_sequence` que omite paradas intermedias esperadas | marcar para revisión |

`off_track`, `backward_jump` y `station_skip_anomaly` no forman parte de MP-008:
requieren map-matching/topología de MP-010–MP-012 y no están admitidos por el
`CHECK` de `data_quality_event` en el esquema v1.

## Posiciones repetidas y snapshots duplicados

- Un mismo payload (por hash canónico) recibido en polls consecutivos se deduplica — ver `docs/DATA_MODEL.md`.
- La deduplicación se aplica al **contenido**, no al hecho de recibir un poll: dos polls que devuelven el mismo contenido cuentan como una sola observación persistida, pero el `feed_run` de cada poll se registra igualmente (para medir disponibilidad del feed).
- `duplicate_snapshot` se marca cuando el feed devuelve contenido idéntico durante una ventana anómalamente larga (posible indicio de feed congelado, no de tráfico real sin cambios).
- MP-008 usa `180s` como punto de partida calibrable para esa ventana; dos polls
  consecutivos iguales a la cadencia normal de ~30s no disparan el flag.

## Anomalías de reloj y cambio de día

- `clock_anomaly`: timestamp reportado por la fuente retrocede respecto al anterior para el mismo vehículo/viaje, o se desvía de forma implausible del `received_at` propio.
- Cambio de día de servicio (medianoche local `Europe/Madrid`): un viaje que cruza la medianoche debe mantener su `service_date` de origen (ver `docs/DATA_MODEL.md`); un error aquí es la causa típica de "correcciones de reloj" documentadas empíricamente por Valfiguer. Madrid Pulse debe tener un test específico para este caso antes de MP-012.

## Cobertura de retrasos vs. puntualidad

Regla no negociable (ver también `AGENTS.md` y `docs/DATA_CONTRACTS.md`):

```text
NO publicar:  "87% de puntualidad de la C5"

SI publicar:  "87% de los viajes observados con delay disponible estuvieron
               dentro del umbral; cobertura del feed: 78%."
```

`delay_coverage_pct` se calcula como `trips_with_delay_data / trips_scheduled`. `on_time_pct_of_covered` se calcula **solo** sobre `trips_with_delay_data`, nunca sobre `trips_scheduled`.

## Continuidad temporal

- Un viaje (`trip_id`) con huecos de observación mayores a un umbral calibrable se marca como con continuidad degradada, no se interpola silenciosamente como si hubiera datos.
- El motor de movimiento (MP-012) usa esta distinción para decidir cuándo pasar de `ESTIMATED` a `STALE`.

## Diferenciación observado / interpolado / estimado — contrato con el motor de movimiento

| Modo | Origen del dato | Cuándo se usa |
|---|---|---|
| `observed` | Posición directa del feed GTFS-RT, map-matched a la vía | Hay observación reciente y plausible |
| `estimated` (interpolado) | Progreso esperado por horario + offset temporal desde la última observación | Entre observaciones, dentro de la ventana `60–180s` |
| `stale` | Última posición conocida, sin corrección adicional | Más de `180s` sin observación nueva |
| `scheduled` | Puramente horario GTFS, sin ninguna observación disponible | Sin datos de posición en absoluto para ese viaje |

Este contrato se detalla con el pipeline completo (map-match → localizar sobre shape → estimar progreso por horario → calcular offset → interpolar → limitar aceleración/velocidad/retrocesos) en `docs/ARCHITECTURE.md` y se implementa en MP-012.

## Catálogo de problemas empíricos conocidos (a cubrir con tests, MP-008)

Basado en problemas documentados públicamente por proyectos de referencia (Valfiguer, Niltra/cercanias) — **reimplementación independiente, no reutilización de su código**:

- Velocidades absurdas que requieren descarte o marcado.
- Trenes "fuera de vía" que requieren adherencia (snap) a geometría ferroviaria.
- Snapshots repetidos que no deben inflar el histórico.
- Correcciones abruptas de retraso que pueden indicar error de fuente, no cambio real.
- Cobertura parcial del dato de retraso que no debe tratarse como ausencia de retraso.
