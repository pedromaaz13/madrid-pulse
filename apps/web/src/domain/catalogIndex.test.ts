import { describe, expect, it } from "vitest";
import fixture from "../__fixtures__/snapshot-map-matched.json";
import type { Catalog } from "./contract";
import { buildCatalogIndex, normalizeForSearch, searchCatalog } from "./catalogIndex";

const catalog = fixture.catalog as unknown as Catalog;
const index = buildCatalogIndex(catalog);

describe("normalizeForSearch", () => {
  it("iguala con y sin tilde", () => {
    expect(normalizeForSearch("Alcorcón")).toBe(normalizeForSearch("alcorcon"));
    expect(normalizeForSearch("  Móstoles ")).toBe("mostoles");
  });
});

describe("searchCatalog", () => {
  it("encuentra una estación escrita sin tilde", () => {
    const hits = searchCatalog(index, "alcorcon");
    expect(hits.some((hit) => hit.kind === "station" && hit.label.includes("Alcorcón"))).toBe(true);
  });

  it("encuentra una línea por su identificador", () => {
    const lineId = catalog.lines[0].line_id;
    const hits = searchCatalog(index, lineId);
    expect(hits.some((hit) => hit.kind === "line" && hit.id === lineId)).toBe(true);
  });

  it("no devuelve nada con la consulta vacía", () => {
    expect(searchCatalog(index, "   ")).toEqual([]);
  });
});

describe("buildCatalogIndex", () => {
  it("solo construye eje de progreso para patrones con corredor validado", () => {
    for (const [patternId, axis] of index.axisByPatternId) {
      const pattern = index.patternsById.get(patternId);
      expect(pattern?.geometry.can_map_match).toBe(true);
      expect(axis.corridorLengthM).toBeGreaterThan(0);
      expect(axis.polyline.points.length).toBeGreaterThan(1);
    }
  });

  it("deriva el sentido del orden real de las paradas sobre el corredor", () => {
    for (const [patternId, axis] of index.axisByPatternId) {
      const stations = index
        .patternsById.get(patternId)!
        .stations.filter((station) => station.distance_along_m !== null);
      const first = stations[0].distance_along_m as number;
      const last = stations[stations.length - 1].distance_along_m as number;
      expect(axis.forward).toBe(last >= first);
    }
  });

  it("no dibuja dos veces el mismo corredor dentro de una línea", () => {
    const seen = new Set<string>();
    for (const corridor of index.drawableCorridors) {
      const key = `${corridor.lineId}|${JSON.stringify(corridor.segments[0][0])}`;
      expect(seen.has(key)).toBe(false);
      seen.add(key);
    }
  });

  it("conserva toda estación del catálogo aunque no tenga circulaciones", () => {
    expect(index.stationsById.size).toBe(catalog.stations.length);
  });
});
