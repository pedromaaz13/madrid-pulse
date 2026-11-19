import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import "maplibre-gl/dist/maplibre-gl.css";
import type { LayerVisibility, Line, Vehicle } from "./types";

interface Props {
  line: Line | null;
  vehicles: Vehicle[];
  layers: LayerVisibility;
  recenterToken: number;
}

const SOURCE_ID = "selected-line";
const EMPTY_COLLECTION: FeatureCollection = { type: "FeatureCollection", features: [] };

function lineFeatures(line: Line | null): FeatureCollection {
  if (!line?.geometry) return EMPTY_COLLECTION;
  return {
    type: "FeatureCollection",
    features: line.geometry.segments.map((segment, index) => ({
      type: "Feature",
      properties: { segment: index },
      geometry: { type: "LineString", coordinates: segment.map(({ lon, lat }) => [lon, lat]) },
    })),
  };
}

function stationFeatures(line: Line | null): FeatureCollection {
  if (!line?.geometry) return EMPTY_COLLECTION;
  return {
    type: "FeatureCollection",
    features: line.geometry.stations.map((station) => ({
      type: "Feature",
      properties: { name: station.name },
      geometry: { type: "Point", coordinates: [station.lon, station.lat] },
    })),
  };
}

function fitLine(map: MapLibreMap, line: Line | null) {
  const coordinates = line?.geometry?.segments.flat() ?? [];
  if (!coordinates.length) return;
  const bounds = coordinates.reduce(
    (current, point) => current.extend([point.lon, point.lat]),
    new maplibregl.LngLatBounds([coordinates[0].lon, coordinates[0].lat], [coordinates[0].lon, coordinates[0].lat]),
  );
  map.fitBounds(bounds, { padding: 54, duration: 700, maxZoom: 13 });
}

export function MapView({ line, vehicles, layers, recenterToken }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const fittedLineRef = useRef<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [-3.7038, 40.4168],
      zoom: 10,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors · ODbL",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: false }), "bottom-right");
    map.on("load", () => {
      map.addSource(SOURCE_ID, { type: "geojson", data: EMPTY_COLLECTION });
      map.addSource("stations", { type: "geojson", data: EMPTY_COLLECTION });
      map.addLayer({
        id: "corridor-shadow",
        type: "line",
        source: SOURCE_ID,
        paint: { "line-color": "#06181e", "line-width": 9, "line-opacity": 0.72 },
      });
      map.addLayer({
        id: "corridor",
        type: "line",
        source: SOURCE_ID,
        paint: { "line-color": "#41e6ad", "line-width": 4.5, "line-opacity": 0.95 },
      });
      map.addLayer({
        id: "stations",
        type: "circle",
        source: "stations",
        paint: {
          "circle-radius": 4.5,
          "circle-color": "#f5fbf9",
          "circle-stroke-color": "#0b4950",
          "circle-stroke-width": 2,
        },
      });
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      (map.getSource(SOURCE_ID) as GeoJSONSource | undefined)?.setData(lineFeatures(line));
      (map.getSource("stations") as GeoJSONSource | undefined)?.setData(stationFeatures(line));
      if (line && fittedLineRef.current !== `${line.network_id}:${line.line_id}`) {
        fittedLineRef.current = `${line.network_id}:${line.line_id}`;
        fitLine(map, line);
      }
    };
    if (map.loaded()) update(); else map.once("load", update);
  }, [line]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("corridor")) return;
    map.setLayoutProperty("corridor", "visibility", layers.corridor ? "visible" : "none");
    map.setLayoutProperty("corridor-shadow", "visibility", layers.corridor ? "visible" : "none");
    map.setLayoutProperty("stations", "visibility", layers.stations ? "visible" : "none");
  }, [layers]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];
    if (!layers.vehicles) return;
    for (const vehicle of vehicles) {
      if (!vehicle.position) continue;
      const element = document.createElement("button");
      element.className = `vehicle-marker vehicle-marker--${vehicle.position.mode}`;
      element.type = "button";
      element.setAttribute("aria-label", `${vehicle.vehicle_id}: posición ${vehicle.position.mode}`);
      element.title = `${vehicle.vehicle_id} · ${vehicle.position.mode} · confianza ${Math.round(vehicle.position.confidence * 100)}%`;
      const marker = new maplibregl.Marker({ element, anchor: "center" })
        .setLngLat([vehicle.position.lon, vehicle.position.lat])
        .addTo(map);
      markersRef.current.push(marker);
    }
  }, [vehicles, layers.vehicles]);

  useEffect(() => {
    if (recenterToken > 0) fitLine(mapRef.current!, line);
  }, [recenterToken, line]);

  return (
    <div className="map-shell">
      <div ref={containerRef} className="map" role="application" aria-label="Mapa interactivo de la red ferroviaria" />
      <a className="osm-credit" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
        © OpenStreetMap contributors · ODbL
      </a>
    </div>
  );
}
