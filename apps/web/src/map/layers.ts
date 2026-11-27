import type { ExpressionSpecification, Map as MapLibreMap } from "maplibre-gl";
import type { FeatureCollection } from "geojson";

export const SOURCES = {
  corridors: "mp-corridors",
  stations: "mp-stations",
  lastKnown: "mp-last-known",
  vehicles: "mp-vehicles",
} as const;

export const LAYERS = {
  corridorCasing: "mp-corridor-casing",
  corridor: "mp-corridor",
  stations: "mp-stations",
  lastKnown: "mp-last-known",
  vehicleHalo: "mp-vehicle-halo",
  vehicle: "mp-vehicle",
  vehicleCore: "mp-vehicle-core",
} as const;

export const EMPTY_COLLECTION: FeatureCollection = { type: "FeatureCollection", features: [] };

/**
 * Las capas del mapa no llevan texto propio: un `symbol` con `text-field`
 * exigiría un servidor de glifos externo, y la aplicación no depende de
 * ninguno fuera de las teselas de OpenStreetMap. La procedencia se distingue
 * por **contorno y forma interior** (legible en escala de grises), y el texto
 * que exige el anexo vive en los rótulos DOM, la ficha y la leyenda.
 */
const STROKE_COLOR: ExpressionSpecification = [
  "match",
  ["get", "shape"],
  "solid",
  "#f7fbf7",
  "dashed",
  "#ffd98f",
  "ring",
  "#0b1f27",
  "matched",
  "#0b1f27",
  "frozen",
  "#0b1f27",
  "hollow",
  "#9fb3ba",
  "#9fb3ba",
];

const STROKE_WIDTH: ExpressionSpecification = [
  "match",
  ["get", "shape"],
  "solid",
  2.2,
  "dashed",
  2.4,
  "ring",
  3.6,
  "matched",
  3.6,
  "frozen",
  1.6,
  "hollow",
  1.6,
  1.6,
];

const BODY_RADIUS: ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["zoom"],
  8,
  ["case", ["get", "selected"], 7.5, 5],
  13,
  ["case", ["get", "selected"], 11.5, 8],
];

/**
 * Marca interior: las observaciones no llevan punto; para las posiciones
 * estimadas o congeladas el tamaño del punto distingue la procedencia.
 */
const CORE_RADIUS: ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["zoom"],
  8,
  ["match", ["get", "shape"], "solid", 0, "matched", 0, "dashed", 1.6, "ring", 2.2, "hollow", 2.6, "frozen", 3.6, 0],
  13,
  ["match", ["get", "shape"], "solid", 0, "matched", 0, "dashed", 2.6, "ring", 3.4, "hollow", 4, "frozen", 5.2, 0],
];

export function addRailLayers(map: MapLibreMap): void {
  for (const id of Object.values(SOURCES)) {
    map.addSource(id, { type: "geojson", data: EMPTY_COLLECTION });
  }

  map.addLayer({
    id: LAYERS.corridorCasing,
    type: "line",
    source: SOURCES.corridors,
    layout: { "line-cap": "round", "line-join": "round" },
    paint: {
      "line-color": "#08171d",
      "line-width": ["interpolate", ["linear"], ["zoom"], 8, 5, 14, 12],
      "line-opacity": ["case", ["get", "dimmed"], 0.25, 0.85],
    },
  });
  map.addLayer({
    id: LAYERS.corridor,
    type: "line",
    source: SOURCES.corridors,
    layout: { "line-cap": "round", "line-join": "round" },
    paint: {
      "line-color": ["get", "color"],
      "line-width": ["interpolate", ["linear"], ["zoom"], 8, 2.4, 14, 6],
      "line-opacity": ["case", ["get", "dimmed"], 0.16, 0.95],
    },
  });

  map.addLayer({
    id: LAYERS.stations,
    type: "circle",
    source: SOURCES.stations,
    paint: {
      "circle-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        8,
        ["case", ["get", "selected"], 6, 3],
        14,
        ["case", ["get", "selected"], 10, 5.5],
      ],
      "circle-color": ["case", ["get", "selected"], "#2644b2", "#203540"],
      "circle-stroke-color": "#f0f6ed",
      "circle-stroke-width": 2,
      "circle-opacity": ["case", ["get", "dimmed"], 0.22, 1],
      "circle-stroke-opacity": ["case", ["get", "dimmed"], 0.22, 1],
    },
  });

  // Última lectura realmente confirmada: se dibuja aparte cuando el símbolo
  // ya no representa una observación (proyectada o congelada).
  map.addLayer({
    id: LAYERS.lastKnown,
    type: "circle",
    source: SOURCES.lastKnown,
    paint: {
      "circle-radius": 5,
      "circle-color": "rgba(0,0,0,0)",
      "circle-stroke-color": ["get", "color"],
      "circle-stroke-width": 1.8,
      "circle-stroke-opacity": 0.75,
    },
  });

  map.addLayer({
    id: LAYERS.vehicleHalo,
    type: "circle",
    source: SOURCES.vehicles,
    filter: ["==", ["get", "selected"], true],
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 13, 13, 19],
      "circle-color": "#2644b2",
      "circle-opacity": 0.32,
    },
  });
  map.addLayer({
    id: LAYERS.vehicle,
    type: "circle",
    source: SOURCES.vehicles,
    paint: {
      "circle-radius": BODY_RADIUS,
      "circle-color": ["get", "color"],
      "circle-stroke-color": STROKE_COLOR,
      "circle-stroke-width": STROKE_WIDTH,
      "circle-opacity": ["case", ["get", "faded"], 0.55, 1],
      "circle-stroke-opacity": ["case", ["get", "faded"], 0.65, 1],
    },
  });
  map.addLayer({
    id: LAYERS.vehicleCore,
    type: "circle",
    source: SOURCES.vehicles,
    paint: {
      "circle-radius": CORE_RADIUS,
      "circle-color": "#0b1f27",
      "circle-opacity": ["case", ["get", "faded"], 0.6, 0.9],
    },
  });
}
