// @vitest-environment jsdom

import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Line } from "./types";
import { MapView } from "./MapView";

interface FakeMap {
  emit: (event: string, payload?: unknown) => void;
  fitBounds: ReturnType<typeof vi.fn>;
  handlers: Map<string, Array<(payload?: unknown) => void>>;
  sources: Map<string, { setData: ReturnType<typeof vi.fn> }>;
}

const mapState = vi.hoisted(() => ({ current: null as FakeMap | null }));

vi.mock("maplibre-gl", () => {
  class MapMock {
    handlers = new Map<string, Array<(payload?: unknown) => void>>();
    sources = new Map<string, { setData: ReturnType<typeof vi.fn> }>();
    layers = new Set<string>();
    fitBounds = vi.fn();
    addControl = vi.fn();
    remove = vi.fn();
    setLayoutProperty = vi.fn();

    constructor() {
      mapState.current = this;
    }

    on(event: string, handler: (payload?: unknown) => void) {
      this.handlers.set(event, [...(this.handlers.get(event) ?? []), handler]);
      return this;
    }

    once(event: string, handler: (payload?: unknown) => void) {
      const onceHandler = (payload?: unknown) => {
        this.handlers.set(event, (this.handlers.get(event) ?? []).filter((current) => current !== onceHandler));
        handler(payload);
      };
      return this.on(event, onceHandler);
    }

    emit(event: string, payload?: unknown) {
      for (const handler of this.handlers.get(event) ?? []) handler(payload);
    }

    addSource(id: string) {
      this.sources.set(id, { setData: vi.fn() });
    }

    addLayer(layer: { id: string }) {
      this.layers.add(layer.id);
    }

    getSource(id: string) {
      return this.sources.get(id);
    }

    getLayer(id: string) {
      return this.layers.has(id) ? { id } : undefined;
    }

    // Reproduce el estado transitorio real: `load` ya se disparó, pero
    // `loaded()` puede volver a false mientras quedan recursos pendientes.
    loaded() {
      return false;
    }
  }

  return {
    Map: MapMock,
    NavigationControl: class {},
    AttributionControl: class {},
    Marker: class {},
    LngLatBounds: class {
      extend() { return this; }
    },
    setWorkerUrl: vi.fn(),
    getVersion: () => "6.19.0",
  };
});

const line: Line = {
  network_id: "network",
  line_id: "line",
  route_ids: ["route"],
  geometry: {
    segments: [[{ lat: 40.3, lon: -3.8 }, { lat: 40.4, lon: -3.7 }]],
    stations: [{ station_id: "station", name: "Estación", lat: 40.3, lon: -3.8, distance_along_m: 0 }],
  },
};

afterEach(() => {
  mapState.current = null;
  vi.restoreAllMocks();
});

describe("MapView cold start", () => {
  it("applies a line received after the one-shot load event without waiting for polling", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    const layers = { corridor: true, stations: true, vehicles: true };

    await act(async () => root.render(
      <MapView line={null} vehicles={[]} layers={layers} recenterToken={0} />,
    ));
    expect(mapState.current).not.toBeNull();

    await act(async () => mapState.current!.emit("load"));
    await act(async () => root.render(
      <MapView line={line} vehicles={[]} layers={layers} recenterToken={0} />,
    ));

    expect(mapState.current!.handlers.get("load")).toHaveLength(1);
    expect(mapState.current!.sources.get("selected-line")!.setData).toHaveBeenLastCalledWith(
      expect.objectContaining({ features: [expect.objectContaining({ geometry: expect.objectContaining({ type: "LineString" }) })] }),
    );
    expect(mapState.current!.sources.get("stations")!.setData).toHaveBeenLastCalledWith(
      expect.objectContaining({ features: [expect.objectContaining({ geometry: expect.objectContaining({ type: "Point" }) })] }),
    );
    expect(mapState.current!.fitBounds).toHaveBeenCalledOnce();

    await act(async () => root.unmount());
  });

  it("reports MapLibre errors instead of swallowing them", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const container = document.createElement("div");
    const root = createRoot(container);

    await act(async () => root.render(
      <MapView
        line={null}
        vehicles={[]}
        layers={{ corridor: true, stations: true, vehicles: true }}
        recenterToken={0}
      />,
    ));
    const error = new Error("worker failed");
    await act(async () => mapState.current!.emit("error", { error }));

    expect(errorSpy).toHaveBeenCalledWith("MapLibre map error", error);
    await act(async () => root.unmount());
  });
});
