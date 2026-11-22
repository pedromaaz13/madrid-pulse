/**
 * Tipos del contrato publicado por MP-019 (ADR-0014).
 *
 * Reflejan `apps/api/schemas.py` campo a campo: este fichero no inventa ni
 * renombra nada del contrato, y cualquier dato ausente se declara `null`
 * igual que en el backend (dato ausente ≠ cero).
 */

export type RenderingMethod =
  | "anchor"
  | "interpolated_between_known_anchors"
  | "extrapolated_from_last_anchor"
  | "schedule_only"
  | "stale_frozen"
  | "unlocated";

export type CoordinateSpace = "map_matched" | "raw" | "schedule";

export type CirculationStatus = "active" | "expired" | "unresolved";

export type FeedStatus = "ok" | "stale" | "error" | "unknown";

export type Mode = "live" | "replay";

export interface Coordinate {
  lat: number;
  lon: number;
}

// --- Catálogo (cacheable, /api/v1/catalog) --------------------------------

export interface CatalogGeometry {
  geometry_version: string;
  relation_id: number;
  attribution: string;
  source_captured_at: string | null;
  length_m: number;
  /** Tramos continuos reales: nunca se concatenan atravesando un hueco. */
  segments: Coordinate[][];
}

export interface PatternGeometry {
  status: "validated" | "partial" | "pending";
  reason: string;
  geometry_version: string | null;
  relation_id: number | null;
  max_stop_distance_m: number | null;
  source_captured_at: string | null;
  attribution: string | null;
  can_map_match: boolean;
}

export interface PatternStation {
  station_id: string;
  name: string;
  lat: number;
  lon: number;
  stop_sequence: number;
  /** Longitud de arco física sobre el corredor; `null` sin corredor validado. */
  distance_along_m: number | null;
}

export interface Pattern {
  pattern_id: string;
  route_id: string;
  direction_key: string;
  origin_stop_id: string;
  destination_stop_id: string;
  stop_ids: string[];
  trip_count: number;
  geometry: PatternGeometry;
  stations: PatternStation[];
}

export interface CatalogLine {
  line_id: string;
  network_id: string | null;
  operator: string;
  route_ids: string[];
  patterns: Pattern[];
}

export interface Station {
  station_id: string;
  name: string;
  lat: number;
  lon: number;
}

export interface CoverageSummary {
  total_patterns: number;
  validated: number;
  partial: number;
  pending: number;
}

export interface Catalog {
  schema_version: string;
  catalog_version: string;
  gtfs_version: string;
  geometry_catalog_version: string;
  gtfs_valid_from: string;
  gtfs_valid_until: string;
  mode: Mode;
  operator: string;
  lines: CatalogLine[];
  stations: Station[];
  geometries: CatalogGeometry[];
  coverage: CoverageSummary;
}

// --- Snapshot operativo (/api/v1/snapshot) --------------------------------

export interface RawPosition {
  lat: number | null;
  lon: number | null;
  source: string;
  gps_observed_at: string;
  payload_hash: string;
}

export interface MapMatched {
  resolution: "map_matched";
  lat: number;
  lon: number;
  progress_m: number;
  distance_from_raw_m: number;
  pattern_id: string;
  geometry_version: string;
}

export interface ProgressEnvelope {
  reference_at: string;
  progress_m_at_reference: number;
  speed_mps: number;
  max_progress_m: number;
  horizon_s: number;
  dwell_until: string | null;
}

export interface Rendered {
  rendering_method: RenderingMethod;
  coordinate_space: CoordinateSpace | null;
  lat: number | null;
  lon: number | null;
  progress_m: number | null;
  pattern_id: string | null;
  geometry_version: string | null;
  geometry_candidate_version: string | null;
  /** Índice heurístico **no calibrado**: nunca se presenta como probabilidad. */
  confidence_index: number | null;
  calculated_at: string;
  display_at: string;
  valid_until: string | null;
  last_confirmed_at: string | null;
  anchor_observed_at: string | null;
  anchor_age_s: number | null;
  anchor_distance_from_raw_m: number | null;
  progress_envelope: ProgressEnvelope | null;
  reason: string | null;
}

export interface VehicleTimestamps {
  gps_observed_at: string;
  received_at: string;
  feed_published_at: string | null;
  snapshot_generated_at: string;
  display_at: string;
}

export interface SnapshotDelay {
  seconds: number | null;
  coverage: "reported" | "missing";
  observed_at: string | null;
  age_s: number | null;
  source: "operator_trip_update" | null;
  expired: boolean;
  approximation: string | null;
}

export interface Quality {
  stale: boolean;
  flags: string[];
}

export interface LegacyPosition {
  lat: number;
  lon: number;
  mode: "observed" | "estimated" | "stale" | "scheduled";
  confidence: number;
}

export interface SnapshotVehicle {
  vehicle_id: string;
  trip_id: string;
  service_date: string;
  route_id: string | null;
  line: string | null;
  pattern_id: string | null;
  circulation_status: CirculationStatus;
  schedule_relationship: string | null;
  timestamps: VehicleTimestamps;
  raw: RawPosition;
  map_matched: MapMatched | null;
  rendered: Rendered;
  position: LegacyPosition | null;
  delay: SnapshotDelay;
  quality: Quality;
}

export interface SnapshotRevision {
  scope: string;
  scope_source: "database_system_identifier" | "database_oid" | "unavailable";
  sequence: number | null;
  generated_at: string;
  tiebreak: string;
}

export interface SnapshotDegradation {
  resource: string;
  feed_name: string | null;
  status: "stale" | "error" | "unknown";
  reason: string;
  last_valid_source_timestamp: string | null;
  data_age_s: number | null;
  poll_age_s: number | null;
}

export interface FeedHealth {
  feed_name: string;
  status: FeedStatus;
  source_timestamp: string | null;
  data_age_s: number | null;
  poll_age_s: number;
  unchanged_for_s: number | null;
  entities: number | null;
  rejected: number;
}

export interface SnapshotCounts {
  vehicles_total: number;
  by_rendering_method: Partial<Record<RenderingMethod, number>>;
  by_coordinate_space: Partial<Record<CoordinateSpace | "none", number>>;
  with_operator_delay: number;
  without_operator_delay: number;
}

export interface CatalogRef {
  catalog_version: string;
  gtfs_version: string;
  geometry_catalog_version: string;
}

export interface Snapshot {
  schema_version: string;
  /** Identidad de contenido. El propio contrato declara que no es ordenable. */
  snapshot_id: string;
  snapshot_id_is_sortable: false;
  revision: SnapshotRevision;
  mode: Mode;
  catalog_ref: CatalogRef;
  generated_at: string;
  display_at: string;
  feeds: FeedHealth[];
  degraded: SnapshotDegradation[];
  vehicles: SnapshotVehicle[];
  counts: SnapshotCounts;
}

// --- Tablero de estación (/api/v1/stations/{id}/board) --------------------

export interface Eta {
  method: "schedule" | "operator_delay_on_schedule" | "unavailable";
  scheduled_at: string | null;
  eta_at: string | null;
  delay_seconds: number | null;
  delay_observed_at: string | null;
  delay_age_s: number | null;
  approximation: string | null;
  reason: string | null;
}

export interface BoardEntry {
  trip_id: string;
  service_date: string;
  route_id: string;
  line: string | null;
  network_id: string | null;
  operator: string;
  headsign: string;
  destination_stop_id: string;
  stop_sequence: number;
  scheduled_arrival_time: string | null;
  scheduled_departure_time: string | null;
  scheduled_arrival_at: string | null;
  scheduled_departure_at: string | null;
  arrival: Eta;
  departure: Eta;
  circulation_source: "scheduled_only" | "observed";
  vehicle_id: string | null;
  position_available: boolean;
  schedule_relationship: string | null;
  operator_next_stop_id: string | null;
  relative_to_operator_next: "before" | "at" | "after" | "unknown" | null;
}

export interface BoardCoverage {
  scheduled_calls: number;
  returned: number;
  observed_circulations: number;
  with_operator_delay: number;
  eta_from_operator: number;
  eta_from_schedule: number;
  eta_unavailable: number;
  /** `null` cuando el denominador es cero: un porcentaje sin muestra no es 0. */
  operator_delay_coverage_pct: number | null;
}

export interface StationBoard {
  schema_version: string;
  station_id: string;
  name: string;
  service_date: string;
  service_dates_considered: string[];
  calculated_from: string;
  mode: Mode;
  generated_at: string;
  display_at: string;
  revision: SnapshotRevision;
  catalog_ref: CatalogRef;
  entries: BoardEntry[];
  coverage: BoardCoverage;
  limitations: string[];
}

export interface Health {
  feeds: FeedHealth[];
  mode: Mode | null;
  gtfs_version: string | null;
  gtfs_valid_from: string | null;
  gtfs_valid_until: string | null;
}
