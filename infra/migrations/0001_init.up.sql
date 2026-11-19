BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE network (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL
);

-- DATA_MODEL.md requires service_date.gtfs_version_id to reference an immutable
-- GTFS version. The entity is described in its "Versionado GTFS" section even
-- though it is not present in the compact entity listing.
CREATE TABLE source_feed_version (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    feed_name text NOT NULL CHECK (feed_name = 'gtfs_static'),
    published_on date,
    source_checksum text NOT NULL CHECK (source_checksum ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (feed_name, source_checksum)
);

CREATE TABLE route (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    network_id bigint NOT NULL REFERENCES network(id),
    source_route_id text NOT NULL,
    short_name text NOT NULL,
    color text,
    nucleo_prefix text NOT NULL CHECK (nucleo_prefix ~ '^[0-9]{2}$'),
    UNIQUE (network_id, source_route_id)
);

CREATE TABLE station (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_stop_id text NOT NULL UNIQUE,
    name text NOT NULL,
    geom geography(Point, 4326) NOT NULL
);

CREATE TABLE service_date (
    date date PRIMARY KEY,
    gtfs_version_id bigint NOT NULL REFERENCES source_feed_version(id)
);

CREATE TABLE trip (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_date date NOT NULL REFERENCES service_date(date),
    source_trip_id text NOT NULL,
    route_id bigint NOT NULL REFERENCES route(id),
    direction_id smallint CHECK (direction_id IN (0, 1)),
    start_time interval CHECK (start_time >= interval '0 seconds'),
    UNIQUE (service_date, source_trip_id)
);

CREATE TABLE trip_stop (
    trip_id bigint NOT NULL REFERENCES trip(id) ON DELETE CASCADE,
    stop_sequence integer NOT NULL CHECK (stop_sequence >= 0),
    station_id bigint NOT NULL REFERENCES station(id),
    scheduled_arrival interval CHECK (scheduled_arrival >= interval '0 seconds'),
    scheduled_departure interval CHECK (scheduled_departure >= interval '0 seconds'),
    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE TABLE source_ingestion_run (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    feed_name text NOT NULL CHECK (
        feed_name IN ('vehicle_positions', 'trip_updates', 'alerts', 'gtfs_static')
    ),
    source_timestamp timestamptz,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    status text NOT NULL CHECK (status IN ('ok', 'error', 'partial')),
    entity_count integer CHECK (entity_count >= 0),
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE vehicle_position_observation (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    observed_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    source_vehicle_id text NOT NULL,
    source_trip_id text NOT NULL,
    trip_id bigint REFERENCES trip(id),
    latitude double precision CHECK (latitude BETWEEN -90 AND 90),
    longitude double precision CHECK (longitude BETWEEN -180 AND 180),
    geom geography(Point, 4326) GENERATED ALWAYS AS (
        CASE
            WHEN latitude IS NULL THEN NULL
            ELSE ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
        END
    ) STORED,
    current_status text,
    current_stop_id text,
    speed_kmh double precision CHECK (speed_kmh >= 0),
    bearing double precision CHECK (bearing >= 0 AND bearing < 360),
    raw_vehicle_label text NOT NULL,
    nucleo_prefix text NOT NULL CHECK (nucleo_prefix ~ '^[0-9]{2}$'),
    nucleo_name text NOT NULL,
    quality_flags jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(quality_flags) = 'array'),
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    ingestion_run_id bigint NOT NULL REFERENCES source_ingestion_run(id),
    CHECK ((latitude IS NULL) = (longitude IS NULL)),
    UNIQUE (ingestion_run_id, payload_hash)
);

CREATE TABLE trip_update_observation (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    observed_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    source_trip_id text NOT NULL,
    trip_id bigint REFERENCES trip(id),
    schedule_relationship text,
    delay_seconds integer,
    delay_coverage text NOT NULL CHECK (delay_coverage IN ('reported', 'missing')),
    next_stop_id text,
    nucleo_prefix text NOT NULL CHECK (nucleo_prefix ~ '^[0-9]{2}$'),
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    ingestion_run_id bigint NOT NULL REFERENCES source_ingestion_run(id),
    CHECK (
        (delay_coverage = 'reported' AND delay_seconds IS NOT NULL)
        OR (delay_coverage = 'missing' AND delay_seconds IS NULL)
    ),
    UNIQUE (ingestion_run_id, payload_hash)
);

CREATE TABLE service_alert (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_alert_id text NOT NULL,
    description_text text NOT NULL,
    description_language text NOT NULL,
    active_period_start timestamptz NOT NULL,
    active_period_end timestamptz,
    affected_route_ids jsonb NOT NULL CHECK (jsonb_typeof(affected_route_ids) = 'array'),
    nucleo_prefixes jsonb NOT NULL CHECK (jsonb_typeof(nucleo_prefixes) = 'array'),
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    ingestion_run_id bigint NOT NULL REFERENCES source_ingestion_run(id),
    CHECK (active_period_end IS NULL OR active_period_end >= active_period_start),
    UNIQUE (ingestion_run_id, payload_hash)
);

CREATE TABLE daily_line_metrics (
    service_date date NOT NULL REFERENCES service_date(date),
    route_id bigint NOT NULL REFERENCES route(id),
    trips_scheduled integer NOT NULL CHECK (trips_scheduled >= 0),
    trips_with_delay_data integer NOT NULL CHECK (
        trips_with_delay_data >= 0 AND trips_with_delay_data <= trips_scheduled
    ),
    delay_coverage_pct numeric(5, 2) NOT NULL CHECK (delay_coverage_pct BETWEEN 0 AND 100),
    on_time_pct_of_covered numeric(5, 2) CHECK (on_time_pct_of_covered BETWEEN 0 AND 100),
    PRIMARY KEY (service_date, route_id)
);

CREATE TABLE station_daily_metrics (
    service_date date NOT NULL REFERENCES service_date(date),
    station_id bigint NOT NULL REFERENCES station(id),
    observations_count integer NOT NULL CHECK (observations_count >= 0),
    data_quality_events_count integer NOT NULL CHECK (data_quality_events_count >= 0),
    PRIMARY KEY (service_date, station_id)
);

CREATE TABLE data_quality_event (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at timestamptz NOT NULL,
    entity_type text NOT NULL CHECK (entity_type IN ('vehicle_position', 'trip_update', 'alert')),
    entity_ref text NOT NULL,
    flag text NOT NULL CHECK (
        flag IN ('stale', 'implausible_speed', 'missing_id', 'duplicate_snapshot', 'clock_anomaly')
    ),
    details jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object')
);

CREATE INDEX vehicle_position_observation_observed_at_idx
    ON vehicle_position_observation (observed_at DESC);
CREATE INDEX vehicle_position_observation_trip_observed_at_idx
    ON vehicle_position_observation (trip_id, observed_at DESC);
CREATE INDEX vehicle_position_observation_vehicle_observed_at_idx
    ON vehicle_position_observation (source_vehicle_id, observed_at DESC);
CREATE INDEX vehicle_position_observation_geom_idx
    ON vehicle_position_observation USING GIST (geom);
CREATE INDEX station_geom_idx ON station USING GIST (geom);

COMMIT;
