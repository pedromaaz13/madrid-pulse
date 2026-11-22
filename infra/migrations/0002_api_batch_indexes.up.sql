-- MP-019: índices que faltaban para las lecturas por lote de la API.
--
-- Hallazgo real medido con EXPLAIN (ANALYZE, BUFFERS) sobre la base de
-- desarrollo (ver docs/evidence/mp-019-explain-y-bench.md):
--
--   * `trip_update_observation` solo tenía su PK y el UNIQUE
--     (ingestion_run_id, payload_hash). Toda consulta por `source_trip_id`
--     -- la que hace `apps/api/db.py::latest_trip_updates` y hacía
--     `latest_trip_update` una vez por vehículo -- resolvía con `Seq Scan`.
--   * `source_ingestion_run` solo tenía su PK, así que la ventana por feed de
--     `recent_ingestion_runs` también barría la tabla completa.
--   * `vehicle_position_observation` sí tenía un índice por viaje, pero sobre
--     la clave ajena `trip_id` (bigint), no sobre `source_trip_id` (el id de
--     Renfe), que es por el que consulta la API -- `trip_id` sigue sin
--     poblarse desde el colector. `db.py::vehicles_for_trips` resolvía con
--     `Seq Scan` pese a existir un índice de nombre parecido.
--
-- Ninguno de los dos índices cambia datos ni semántica: son estructuras de
-- acceso. El orden DESC acompaña al `ORDER BY ... DESC` real de cada consulta.
BEGIN;

CREATE INDEX IF NOT EXISTS trip_update_observation_trip_observed_at_idx
    ON trip_update_observation (source_trip_id, observed_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS source_ingestion_run_feed_started_at_idx
    ON source_ingestion_run (feed_name, started_at DESC);

CREATE INDEX IF NOT EXISTS vehicle_position_observation_source_trip_observed_at_idx
    ON vehicle_position_observation (source_trip_id, observed_at DESC, id DESC);

COMMIT;
