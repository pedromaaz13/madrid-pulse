BEGIN;
DROP TRIGGER IF EXISTS classify_ingestion ON source_ingestion_run;
DROP FUNCTION IF EXISTS classify_ingestion_run();
DROP INDEX IF EXISTS vehicle_position_vehicle_time_idx;
DROP INDEX IF EXISTS trip_update_trip_run_idx;
DROP INDEX IF EXISTS ingestion_run_started_id_idx;
ALTER TABLE source_ingestion_run DROP COLUMN IF EXISTS is_retroactive;
COMMIT;
