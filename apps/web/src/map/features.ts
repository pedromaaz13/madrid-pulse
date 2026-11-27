import type { Feature, FeatureCollection, Point } from "geojson";
import type { CatalogIndex } from "../domain/catalogIndex";
import type { SnapshotVehicle } from "../domain/contract";
import { methodStyle } from "../domain/format";
import { vehicleKey } from "../domain/identity";
import { frameFor, lastConfirmedCoordinate } from "../domain/movement";
import { lineColor } from "../domain/palette";

export interface MapStyleContext {
  index: CatalogIndex;
  colors: Map<string, string>;
  /** Vacío = ninguna línea filtrada, se muestran todas. */
  activeLines: Set<string>;
  selectedVehicleKey: string | null;
  selectedStationId: string | null;
}

function isActive(context: MapStyleContext, lineId: string | null): boolean {
  if (context.activeLines.size === 0) return true;
  return lineId !== null && context.activeLines.has(lineId);
}

export function corridorFeatures(context: MapStyleContext): FeatureCollection {
  const features: Feature[] = [];
  for (const corridor of context.index.drawableCorridors) {
    const dimmed = !isActive(context, corridor.lineId);
    for (const [segmentIndex, segment] of corridor.segments.entries()) {
      features.push({
        type: "Feature",
        id: undefined,
        properties: {
          lineId: corridor.lineId,
          patternId: corridor.patternId,
          color: lineColor(context.colors, corridor.lineId),
          dimmed,
        },
        geometry: {
          type: "LineString",
          coordinates: segment.map((point) => [point.lon, point.lat]),
        },
      });
      void segmentIndex;
    }
  }
  return { type: "FeatureCollection", features };
}

export function stationFeatures(context: MapStyleContext): FeatureCollection {
  const features: Feature<Point>[] = [];
  for (const station of context.index.catalog.stations) {
    const lines = context.index.linesByStation.get(station.station_id) ?? new Set<string>();
    const dimmed =
      context.activeLines.size > 0 && ![...lines].some((line) => context.activeLines.has(line));
    features.push({
      type: "Feature",
      properties: {
        stationId: station.station_id,
        name: station.name,
        selected: station.station_id === context.selectedStationId,
        dimmed,
      },
      geometry: { type: "Point", coordinates: [station.lon, station.lat] },
    });
  }
  return { type: "FeatureCollection", features };
}

export interface VehicleFrame {
  key: string;
  vehicle: SnapshotVehicle;
  lon: number;
  lat: number;
}

/**
 * Posiciones de un fotograma. Se recalculan desde la envolvente publicada y
 * la geometría ya indexada del catálogo: ningún fotograma vuelve al backend
 * ni se archiva como observación.
 */
export function vehicleFrames(
  vehicles: SnapshotVehicle[],
  context: MapStyleContext,
  atMs: number,
): { collection: FeatureCollection; frames: VehicleFrame[] } {
  const features: Feature<Point>[] = [];
  const frames: VehicleFrame[] = [];
  for (const vehicle of vehicles) {
    if (!isActive(context, vehicle.line)) continue;
    const axis =
      vehicle.rendered.pattern_id === null
        ? null
        : (context.index.axisByPatternId.get(vehicle.rendered.pattern_id) ?? null);
    const frame = frameFor(vehicle.rendered, axis, atMs);
    if (frame === null) continue;
    const style = methodStyle(vehicle.rendered.rendering_method, vehicle.rendered.coordinate_space);
    const key = vehicleKey(vehicle);
    features.push({
      type: "Feature",
      // `id` estable por circulación: el marcador se reconcilia por identidad,
      // no por índice ni por el objeto de la respuesta.
      id: key,
      properties: {
        key,
        color: lineColor(context.colors, vehicle.line),
        shape: style.shape,
        provenance: style.label,
        selected: key === context.selectedVehicleKey,
        faded: vehicle.quality.stale,
        line: vehicle.line ?? "—",
        label: `${vehicle.line ?? "sin línea"} ${style.glyph}`,
      },
      geometry: { type: "Point", coordinates: [frame.coordinate.lon, frame.coordinate.lat] },
    });
    frames.push({ key, vehicle, lon: frame.coordinate.lon, lat: frame.coordinate.lat });
  }
  return { collection: { type: "FeatureCollection", features }, frames };
}

/**
 * Marcador de la última lectura conocida, solo para símbolos que ya no son
 * una observación (`extrapolated_from_last_anchor` / `stale_frozen`).
 */
export function lastKnownFeatures(
  vehicles: SnapshotVehicle[],
  context: MapStyleContext,
): FeatureCollection {
  const features: Feature<Point>[] = [];
  for (const vehicle of vehicles) {
    if (!isActive(context, vehicle.line)) continue;
    const method = vehicle.rendered.rendering_method;
    if (method !== "extrapolated_from_last_anchor" && method !== "stale_frozen") continue;
    const coordinate = lastConfirmedCoordinate(vehicle);
    if (coordinate === null) continue;
    features.push({
      type: "Feature",
      properties: { color: lineColor(context.colors, vehicle.line) },
      geometry: { type: "Point", coordinates: [coordinate.lon, coordinate.lat] },
    });
  }
  return { type: "FeatureCollection", features };
}
