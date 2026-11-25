INSERT INTO source_ingestion_run (feed_name, source_timestamp, started_at, finished_at, status, entity_count, payload_hash)
SELECT (ARRAY['vehicle_positions','trip_updates','alerts'])[1 + g % 3], ts, ts, ts, 'ok', 1, repeat('c',64)
FROM (SELECT g, timestamptz '2026-11-01 00:00Z' + g * interval '6.6667 seconds' AS ts FROM generate_series(1,300000) g) s;
INSERT INTO trip_update_observation (observed_at, received_at, source_trip_id, schedule_relationship, delay_coverage, nucleo_prefix, payload_hash, ingestion_run_id)
SELECT r.started_at, r.started_at, 'T'||t, 'SCHEDULED', 'missing', '10', md5(r.id||'-'||t)||md5(t||'x'), r.id
FROM source_ingestion_run r, generate_series(1,100) t WHERE r.feed_name='trip_updates' AND r.id > 297000;
INSERT INTO vehicle_position_observation (source_vehicle_id, source_trip_id, observed_at, received_at, latitude, longitude, current_status, current_stop_id, raw_vehicle_label, payload_hash, ingestion_run_id, nucleo_prefix, nucleo_name)
SELECT 'V'||t, 'T'||t, r.started_at, r.started_at, 40.4, -3.7, 'IN_TRANSIT_TO', '18000', 'x', md5(r.id||'-'||t)||md5(t||'y'), r.id, '10', 'Madrid'
FROM source_ingestion_run r, generate_series(1,100) t WHERE r.feed_name='vehicle_positions' AND r.id > 297000;
ANALYZE;
