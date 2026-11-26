import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import type { Map as MapLibreMap } from "maplibre-gl";
import { methodStyle } from "../domain/format";
import { Legend } from "../ui/Legend";
import { addRailLayers, LAYERS } from "./layers";

// Evalúa los extremos de zoom de las expresiones reales usadas por MapLibre.
function evaluate(value: unknown, shape: string, zoom: 8 | 13): unknown {
  if (!Array.isArray(value)) return value;
  if (value[0] === "get") return value[1] === "shape" ? shape : value[1] === "color" ? "line-color" : false;
  if (value[0] === "match") {
    const selected = evaluate(value[1], shape, zoom);
    for (let i = 2; i < value.length - 1; i += 2) if (value[i] === selected) return evaluate(value[i + 1], shape, zoom);
    return evaluate(value[value.length - 1], shape, zoom);
  }
  if (value[0] === "interpolate") return evaluate(value[zoom === 8 ? 4 : 6], shape, zoom);
  if (value[0] === "case") return evaluate(value[3], shape, zoom);
  throw new Error(`Expresión no cubierta: ${value[0]}`);
}

it("ningún método localizado comparte el mismo relleno, contorno y marca interior", () => {
  const layers = new Map<string, { paint?: Record<string, unknown> }>();
  const map = { addSource: () => {}, addLayer: (layer: { id: string; paint?: Record<string, unknown> }) => layers.set(layer.id, layer) } as unknown as MapLibreMap;
  addRailLayers(map);
  const body = layers.get(LAYERS.vehicle)!.paint!;
  const core = layers.get(LAYERS.vehicleCore)!.paint!;
  const pairs = [
    ["anchor", "raw"], ["anchor", "map_matched"],
    ["interpolated_between_known_anchors", "map_matched"],
    ["extrapolated_from_last_anchor", "map_matched"],
    ["schedule_only", "schedule"], ["stale_frozen", "map_matched"],
  ] as const;
  for (const zoom of [8, 13] as const) {
    const signatures = pairs.map(([method, space]) => {
      const shape = methodStyle(method, space).shape;
      return JSON.stringify([evaluate(body["circle-color"], shape, zoom), evaluate(body["circle-stroke-width"], shape, zoom), evaluate(core["circle-radius"], shape, zoom)]);
    });
    expect(new Set(signatures).size).toBe(signatures.length);
  }
});

it("fusiona congeladas de distintos espacios en una sola entrada", () => {
  const html = renderToStaticMarkup(<Legend present={[{method: "stale_frozen", space: "raw"}, {method: "stale_frozen", space: "map_matched"}]} />);
  expect(html.match(/Congelada/g)).toHaveLength(1);
});
