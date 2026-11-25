BEGIN;
ALTER TABLE source_ingestion_run ADD COLUMN IF NOT EXISTS is_retroactive boolean;
-- Runs existentes: clasificar una sola vez en orden de reserva de id.
WITH ordered AS (
    SELECT id, started_at, max(started_at) OVER (
        ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS prior_max FROM source_ingestion_run
)
UPDATE source_ingestion_run r
SET is_retroactive = COALESCE(o.started_at < o.prior_max - interval '2 seconds', false)
FROM ordered o WHERE r.id = o.id AND r.is_retroactive IS NULL;
CREATE INDEX IF NOT EXISTS ingestion_run_started_id_idx ON source_ingestion_run (started_at, id);
CREATE INDEX IF NOT EXISTS trip_update_trip_run_idx ON trip_update_observation
    (source_trip_id, ingestion_run_id DESC, observed_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS vehicle_position_vehicle_time_idx ON vehicle_position_observation
    (source_vehicle_id, observed_at DESC, id DESC);
CREATE OR REPLACE FUNCTION classify_ingestion_run() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    tolerance_s double precision := COALESCE(NULLIF(current_setting('madrid_pulse.retro_tolerance_s', true), '')::double precision, 2);
BEGIN
    IF NOT (tolerance_s >= 0 AND tolerance_s < 'Infinity'::double precision) THEN
        RAISE EXCEPTION 'retro_tolerance_s debe ser un número finito no negativo';
    END IF;
    NEW.is_retroactive := EXISTS (
        SELECT FROM source_ingestion_run
        WHERE started_at > NEW.started_at + make_interval(secs => tolerance_s)
          AND id < NEW.id
    );
    RETURN NEW;
END;
$$;
CREATE OR REPLACE TRIGGER classify_ingestion BEFORE INSERT ON source_ingestion_run
FOR EACH ROW EXECUTE FUNCTION classify_ingestion_run();
ALTER TABLE source_ingestion_run ALTER COLUMN is_retroactive SET NOT NULL;
COMMIT;
