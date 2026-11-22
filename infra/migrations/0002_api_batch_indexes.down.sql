BEGIN;

DROP INDEX IF EXISTS vehicle_position_observation_source_trip_observed_at_idx;
DROP INDEX IF EXISTS source_ingestion_run_feed_started_at_idx;
DROP INDEX IF EXISTS trip_update_observation_trip_observed_at_idx;

COMMIT;
