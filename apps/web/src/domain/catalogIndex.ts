import type { Catalog, CatalogGeometry, CatalogLine, Pattern, Station } from "./contract";
import { indexPolyline } from "./geometry";
import type { PatternAxis } from "./movement";

/**
 * Los índices dependen del GTFS y de la geometría. Se reutilizan mientras
 * coincida `catalog_version`, incluso cuando cambia la vigencia GTFS.
 */
export interface CatalogIndex {
  catalog: Catalog;
  stationsById: Map<string, Station>;
  stationsByLine: Map<string, Set<string>>;
  linesByStation: Map<string, Set<string>>;
  patternsById: Map<string, Pattern>;
  lineByPatternId: Map<string, string>;
  geometriesByVersion: Map<string, CatalogGeometry>;
  /** Solo para patrones con corredor validado: el resto no tiene eje real. */
  axisByPatternId: Map<string, PatternAxis>;
  linesById: Map<string, CatalogLine>;
  /** Trazados dibujables, agrupados por línea para colorearlos. */
  drawableCorridors: { lineId: string; patternId: string; segments: CatalogGeometry["segments"] }[];
}

function foldAccents(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

/** Búsqueda con y sin tilde, como exige `INTERACCIONES.md`. */
export function normalizeForSearch(value: string): string {
  return foldAccents(value).trim();
}

export function buildCatalogIndex(catalog: Catalog): CatalogIndex {
  const stationsById = new Map<string, Station>();
  for (const station of catalog.stations) stationsById.set(station.station_id, station);

  const geometriesByVersion = new Map<string, CatalogGeometry>();
  for (const geometry of catalog.geometries) {
    geometriesByVersion.set(geometry.geometry_version, geometry);
  }

  const patternsById = new Map<string, Pattern>();
  const lineByPatternId = new Map<string, string>();
  const axisByPatternId = new Map<string, PatternAxis>();
  const stationsByLine = new Map<string, Set<string>>();
  const linesByStation = new Map<string, Set<string>>();
  const linesById = new Map<string, CatalogLine>();
  const drawableCorridors: CatalogIndex["drawableCorridors"] = [];
  // Un mismo corredor sirve a varios patrones (ida/vuelta, tramo compartido):
  // se dibuja una sola vez por línea para no apilar trazados idénticos.
  const drawnByLine = new Map<string, Set<string>>();

  for (const line of catalog.lines) {
    linesById.set(line.line_id, line);
    const lineStations = new Set<string>();
    stationsByLine.set(line.line_id, lineStations);

    for (const pattern of line.patterns) {
      patternsById.set(pattern.pattern_id, pattern);
      lineByPatternId.set(pattern.pattern_id, line.line_id);

      for (const stopId of pattern.stop_ids) {
        lineStations.add(stopId);
        let lines = linesByStation.get(stopId);
        if (lines === undefined) {
          lines = new Set<string>();
          linesByStation.set(stopId, lines);
        }
        lines.add(line.line_id);
      }

      const version = pattern.geometry.geometry_version;
      const geometry = version === null ? undefined : geometriesByVersion.get(version);
      if (!pattern.geometry.can_map_match || geometry === undefined || version === null) continue;

      const drawn = drawnByLine.get(line.line_id) ?? new Set<string>();
      if (!drawn.has(version)) {
        drawn.add(version);
        drawnByLine.set(line.line_id, drawn);
        drawableCorridors.push({
          lineId: line.line_id,
          patternId: pattern.pattern_id,
          segments: geometry.segments,
        });
      }

      const projected = pattern.stations.filter((station) => station.distance_along_m !== null);
      if (projected.length < 2 || geometry.segments.length === 0) continue;
      const first = projected[0].distance_along_m as number;
      const last = projected[projected.length - 1].distance_along_m as number;
      axisByPatternId.set(pattern.pattern_id, {
        patternId: pattern.pattern_id,
        geometryVersion: version,
        // Mismo criterio que `build_trip_schedule`: el sentido lo fija el orden
        // real de las paradas sobre el corredor, no una convención de nombre.
        forward: last >= first,
        corridorLengthM: geometry.length_m,
        // El backend convierte progreso a coordenada sobre `segments[0]`
        // (`packages.movement.rendering._coordinate`): se replica literalmente
        // para no dibujar en un punto distinto del que publica el contrato.
        polyline: indexPolyline(geometry.segments[0]),
      });
    }
  }

  return {
    catalog,
    stationsById,
    stationsByLine,
    linesByStation,
    patternsById,
    lineByPatternId,
    geometriesByVersion,
    axisByPatternId,
    linesById,
    drawableCorridors,
  };
}

export interface SearchHit {
  kind: "station" | "line";
  id: string;
  label: string;
  detail: string;
}

export function searchCatalog(index: CatalogIndex, query: string, limit = 8): SearchHit[] {
  const needle = normalizeForSearch(query);
  if (needle.length === 0) return [];
  const hits: SearchHit[] = [];

  for (const line of index.catalog.lines) {
    if (normalizeForSearch(line.line_id).includes(needle)) {
      hits.push({
        kind: "line",
        id: line.line_id,
        label: line.line_id,
        detail: `Línea · ${line.patterns.length} patrones`,
      });
    }
  }
  for (const station of index.catalog.stations) {
    if (!normalizeForSearch(station.name).includes(needle)) continue;
    const lines = [...(index.linesByStation.get(station.station_id) ?? [])].sort();
    hits.push({
      kind: "station",
      id: station.station_id,
      label: station.name,
      detail: lines.length > 0 ? lines.join(" · ") : "Sin línea catalogada",
    });
  }
  return hits.slice(0, limit);
}
