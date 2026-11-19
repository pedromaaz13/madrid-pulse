# Quality engine (MP-008)

El motor separa reglas puras (`engine.py`) de acceso a PostgreSQL (`db.py`). El
colector evalúa cada entidad normalizada en memoria antes de insertarla y guarda
observación, `quality_flags` y `data_quality_event` en la misma transacción. Esta
ubicación evita un segundo proceso y conserva atomicidad sin acoplar las reglas a
la red o la base de datos.

Los cinco flags admitidos por `0001_init.up.sql` son `stale`,
`implausible_speed`, `missing_id`, `duplicate_snapshot` y `clock_anomaly`.
`implausible_speed` se calcula con Haversine entre posiciones consecutivas del
mismo `source_vehicle_id`; nunca usa el `speed_kmh` de origen, ausente en los
feeds reales observados. PostGIS sigue almacenando la geometría, pero Python
permite probar la regla sin BD y es suficientemente preciso para el umbral de
plausibilidad, no para map-matching.

`duplicate_snapshot` compara el hash del payload **completo del feed** entre
polls y solo dispara cuando permanece idéntico más de la ventana configurada.
No marca la deduplicación normal de entidades de MP-007.

Los valores de `QualityThresholds` (`180 s` stale, `200 km/h`, `180 s` feed
congelado, `300 s` drift de reloj) son puntos de partida explícitamente
calibrables con el histórico real; no describen un contrato garantizado por
Renfe.
