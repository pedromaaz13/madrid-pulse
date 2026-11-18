BEGIN;

DROP TABLE IF EXISTS data_quality_event;
DROP TABLE IF EXISTS station_daily_metrics;
DROP TABLE IF EXISTS daily_line_metrics;
DROP TABLE IF EXISTS service_alert;
DROP TABLE IF EXISTS trip_update_observation;
DROP TABLE IF EXISTS vehicle_position_observation;
DROP TABLE IF EXISTS source_ingestion_run;
DROP TABLE IF EXISTS trip_stop;
DROP TABLE IF EXISTS trip;
DROP TABLE IF EXISTS service_date;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS route;
DROP TABLE IF EXISTS source_feed_version;
DROP TABLE IF EXISTS network;

-- The postgis/postgis image provisions postgis plus dependent extensions
-- (postgis_topology and postgis_tiger_geocoder) before this migration runs.
-- Do not DROP ... CASCADE infrastructure that this migration did not create.

COMMIT;
