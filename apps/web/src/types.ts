export type PositionMode = "observed" | "estimated" | "stale" | "scheduled";

export interface Coordinate {
  lat: number;
  lon: number;
}

export interface LineStation extends Coordinate {
  station_id: string;
  name: string;
  distance_along_m: number;
}

export interface LineGeometry {
  segments: Coordinate[][];
  stations: LineStation[];
}

export interface Line {
  line_id: string;
  network_id: string;
  route_ids: string[];
  geometry: LineGeometry | null;
}

export interface Vehicle {
  vehicle_id: string;
  trip_id: string;
  route_id: string | null;
  line: string | null;
  position: (Coordinate & { mode: PositionMode; confidence: number }) | null;
  delay: { seconds: number | null; coverage: "reported" | "missing" };
  observation: {
    reported_at: string | null;
    received_at: string | null;
    age_s: number | null;
  };
  quality: { stale: boolean; flags: string[] };
  circulation_status: "active" | "expired" | "unresolved";
}

export interface FeedHealth {
  feed_name: string;
  status: "ok" | "stale" | "error" | "unknown";
  data_age_s: number | null;
}

export interface Health {
  feeds: FeedHealth[];
}

export interface LayerVisibility {
  corridor: boolean;
  stations: boolean;
  vehicles: boolean;
}
