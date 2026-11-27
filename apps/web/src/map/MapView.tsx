import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, Map as MapLibreMap, MapMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { CatalogIndex } from "../domain/catalogIndex";
import { methodStyle } from "../domain/format";
import type { SnapshotVehicle } from "../domain/contract";
import { vehicleKey } from "../domain/identity";
import type { Clock } from "../hooks/useClock";
import { addRailLayers, EMPTY_COLLECTION, LAYERS, SOURCES } from "./layers";
import {
  corridorFeatures,
  lastKnownFeatures,
  stationFeatures,
  vehicleFrames,
  type MapStyleContext,
  type VehicleFrame,
} from "./features";

// MapLibre deriva la URL de su worker en runtime, así que Rolldown no puede
// descubrirla: producción la fija explícitamente contra el asset emitido y
// verificado byte a byte por `scripts/verify-build.mjs` (hallazgo de MP-014).
if (import.meta.env.PROD) {
  maplibregl.setWorkerUrl(
    `${import.meta.env.BASE_URL}assets/maplibre-gl-worker.mjs?v=${maplibregl.getVersion()}`,
  );
}

const MADRID_CENTER: [number, number] = [-3.7038, 40.4168];
const MADRID_ZOOM = 9.6;
/** Cadencia del rótulo del tren seguido; el símbolo va a cada fotograma. */
const LABEL_THROTTLE_MS = 250;
/** Por debajo de este zoom los nombres de estación se solapan: no se rotulan. */
const LABEL_MIN_ZOOM = 11;

export interface MapViewProps {
  index: CatalogIndex;
  colors: Map<string, string>;
  vehicles: SnapshotVehicle[];
  activeLines: Set<string>;
  selectedVehicleKey: string | null;
  selectedStationId: string | null;
  /** Estaciones cuyo nombre se rotula (contexto seleccionado, no toda la red). */
  labelledStationIds: string[];
  followKey: string | null;
  reducedMotion: boolean;
  clock: Clock;
  /**
   * Sello de **revisión** del snapshot vigente. Con movimiento reducido marca
   * cuándo puede repintarse, en vez de hacerlo en cada fotograma.
   *
   * Deliberadamente **no** es `snapshot_id`: ese campo es identidad de
   * contenido y se repite entre sondeos cuando los vehículos no han cambiado,
   * aunque `display_at` sí avance. Usarlo aquí congelaba el mapa (defecto real
   * observado en navegador). La revisión avanza con cada respuesta aceptada,
   * que es justo la señal de "ha llegado dato nuevo".
   */
  snapshotStamp: string | null;
  /** Instante de presentación que publica el propio snapshot. */
  displayAtMs: number | null;
  onSelectVehicle: (vehicle: SnapshotVehicle) => void;
  onSelectStation: (stationId: string) => void;
  /** El usuario tomó la cámara con un gesto: se suelta el seguimiento. */
  onCameraGesture: () => void;
  onRecenterDone?: () => void;
  recenterToken: number;
}

function styleContext(state: FrameState): MapStyleContext {
  return {
    index: state.index,
    colors: state.colors,
    activeLines: state.activeLines,
    selectedVehicleKey: state.selectedVehicleKey,
    selectedStationId: state.selectedStationId,
  };
}

interface FrameState {
  index: CatalogIndex;
  colors: Map<string, string>;
  vehicles: SnapshotVehicle[];
  activeLines: Set<string>;
  selectedVehicleKey: string | null;
  selectedStationId: string | null;
  followKey: string | null;
  reducedMotion: boolean;
  clock: Clock;
  snapshotStamp: string | null;
  displayAtMs: number | null;
}

export function MapView(props: MapViewProps) {
  const {
    index,
    colors,
    vehicles,
    activeLines,
    selectedVehicleKey,
    selectedStationId,
    labelledStationIds,
    followKey,
    reducedMotion,
    clock,
    snapshotStamp,
    displayAtMs,
    onSelectVehicle,
    onSelectStation,
    onCameraGesture,
    recenterToken,
  } = props;

  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const readyRef = useRef(false);
  const labelsRef = useRef(new Map<string, maplibregl.Marker>());
  const rafRef = useRef<number | null>(null);
  const lastLabelAtRef = useRef(0);
  const staticKeyRef = useRef<string | null>(null);
  const lastPaintRef = useRef<{ atMs: number; frames: VehicleFrame[]; count: number }>({
    atMs: 0,
    frames: [],
    count: 0,
  });
  const vehicleIndexRef = useRef(new Map<string, SnapshotVehicle>());
  const [zoom, setZoom] = useState(MADRID_ZOOM);

  // Todo lo que el bucle de fotogramas necesita vive en una ref: el reloj de
  // presentación nunca pasa por `setState`, así que React no renderiza por
  // fotograma (ni una sola vez por segundo).
  const stateRef = useRef<FrameState>({
    index,
    colors,
    vehicles,
    activeLines,
    selectedVehicleKey,
    selectedStationId,
    followKey,
    reducedMotion,
    clock,
    snapshotStamp,
    displayAtMs,
  });
  useEffect(() => {
    stateRef.current = {
      index,
      colors,
      vehicles,
      activeLines,
      selectedVehicleKey,
      selectedStationId,
      followKey,
      reducedMotion,
      clock,
      snapshotStamp,
      displayAtMs,
    };
  }, [
    index,
    colors,
    vehicles,
    activeLines,
    selectedVehicleKey,
    selectedStationId,
    followKey,
    reducedMotion,
    clock,
    snapshotStamp,
    displayAtMs,
  ]);

  const paintStatic = useCallback(() => {
    const map = mapRef.current;
    if (map === null || !readyRef.current) return;
    const context = styleContext(stateRef.current);
    (map.getSource(SOURCES.corridors) as GeoJSONSource | undefined)?.setData(
      corridorFeatures(context),
    );
    (map.getSource(SOURCES.stations) as GeoJSONSource | undefined)?.setData(
      stationFeatures(context),
    );
  }, []);

  useEffect(() => {
    if (containerRef.current === null || mapRef.current !== null) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      center: MADRID_CENTER,
      zoom: MADRID_ZOOM,
      attributionControl: false,
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
        layers: [
          { id: "osm", type: "raster", source: "osm", paint: { "raster-saturation": -0.55, "raster-brightness-max": 0.82 } },
        ],
      },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.on("error", (event) => console.error("MapLibre", event.error));
    map.on("zoomend", () => setZoom(map.getZoom()));
    map.on("load", () => {
      addRailLayers(map);
      readyRef.current = true;
      paintStatic();
    });
    mapRef.current = map;
    const labels = labelsRef.current;
    return () => {
      readyRef.current = false;
      for (const marker of labels.values()) marker.remove();
      labels.clear();
      map.remove();
      mapRef.current = null;
    };
    // El mapa se crea una sola vez: su contenido se actualiza por fuente, no
    // recreando la instancia ni los objetos en cada poll.
  }, [paintStatic]);

  // Capas estáticas: dependen del catálogo y de la selección, no del reloj.
  useEffect(() => {
    paintStatic();
  }, [paintStatic, index, colors, activeLines, selectedStationId]);

  // Bucle de presentación: un `requestAnimationFrame` que escribe directamente
  // en las fuentes de MapLibre. Independiente del sondeo y de React.
  useEffect(() => {
    const render = () => {
      rafRef.current = requestAnimationFrame(render);
      const map = mapRef.current;
      const state = stateRef.current;
      if (map === null || !readyRef.current) return;

      const context = styleContext(state);

      // Sonda de desarrollo: se publica en **cada** fotograma, aunque no haya
      // repintado, para poder auditar también el caso de movimiento reducido
      // (donde no repintar es justamente lo correcto). Desaparece de la build:
      // `import.meta.env.DEV` es constante en release.
      if (import.meta.env.DEV) {
        (window as unknown as Record<string, unknown>).__mpMap = map;
        (window as unknown as Record<string, unknown>).__mpFrame = () => ({
          atMs: lastPaintRef.current.atMs,
          paintCount: lastPaintRef.current.count,
          center: map.getCenter(),
          zoom: map.getZoom(),
          followKey: stateRef.current.followKey,
          reducedMotion: stateRef.current.reducedMotion,
          snapshotStamp: stateRef.current.snapshotStamp,
          displayAtMs: stateRef.current.displayAtMs,
          vehicles: lastPaintRef.current.frames.map((frame) => ({
            key: frame.key,
            lon: frame.lon,
            lat: frame.lat,
            method: frame.vehicle.rendered.rendering_method,
            line: frame.vehicle.line,
          })),
        });
      }

      // `prefers-reduced-motion`: ninguna animación espacial automática. Las
      // posiciones se evalúan en el instante de presentación que publica el
      // propio snapshot y solo se repintan cuando llega uno nuevo o cambia
      // la selección, de modo que nada se mueve por sí solo. El dato sigue
      // siendo el mismo; lo que desaparece es la interpolación continua.
      const staticKey =
        `${state.snapshotStamp ?? "none"}|${state.selectedVehicleKey ?? "none"}` +
        `|${[...state.activeLines].sort().join(",")}`;
      if (state.reducedMotion) {
        if (staticKey === staticKeyRef.current) return;
        staticKeyRef.current = staticKey;
      } else {
        staticKeyRef.current = null;
      }

      const atMs =
        state.reducedMotion && state.displayAtMs !== null
          ? state.displayAtMs
          : state.clock.nowMs();
      const { collection, frames } = vehicleFrames(state.vehicles, context, atMs);
      (map.getSource(SOURCES.vehicles) as GeoJSONSource | undefined)?.setData(collection);
      if (import.meta.env.DEV) {
        lastPaintRef.current = { atMs, frames, count: lastPaintRef.current.count + 1 };
      }

      const followKeyNow = state.followKey;
      if (followKeyNow !== null) {
        const target = frames.find((frame) => frame.key === followKeyNow);
        if (target !== undefined) {
          // Movimiento programático explícito, no un `easeTo` por fotograma:
          // `jumpTo` sobre una posición que ya es continua evita encadenar
          // animaciones que se pisan entre sí. Con movimiento reducido esto
          // ocurre una vez por snapshot, no de forma continua.
          map.jumpTo({ center: [target.lon, target.lat] });
        }
      }

      const now = performance.now();
      if (now - lastLabelAtRef.current >= LABEL_THROTTLE_MS) {
        lastLabelAtRef.current = now;
        const selected = frames.find((frame) => frame.key === state.selectedVehicleKey);
        const marker = labelsRef.current.get("selected-vehicle");
        if (selected !== undefined && marker !== undefined) {
          marker.setLngLat([selected.lon, selected.lat]);
        }
      }
    };
    rafRef.current = requestAnimationFrame(render);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    };
  }, []);

  // Última lectura conocida: cambia con cada snapshot, no con cada fotograma.
  useEffect(() => {
    const map = mapRef.current;
    if (map === null || !readyRef.current) return;
    (map.getSource(SOURCES.lastKnown) as GeoJSONSource | undefined)?.setData(
      lastKnownFeatures(vehicles, styleContext(stateRef.current)),
    );
    vehicleIndexRef.current = new Map(vehicles.map((vehicle) => [vehicleKey(vehicle), vehicle]));
  }, [vehicles, activeLines]);

  // Interacción: clic y teclado resuelven lo esencial; el hover es opcional.
  useEffect(() => {
    const map = mapRef.current;
    if (map === null) return;

    const onVehicleClick = (event: MapMouseEvent) => {
      const feature = map
        .queryRenderedFeatures(event.point, { layers: [LAYERS.vehicle] })
        .at(0);
      if (feature === undefined) return;
      const key = feature.properties?.key as string | undefined;
      if (key === undefined) return;
      const vehicle = vehicleIndexRef.current.get(key);
      if (vehicle !== undefined) onSelectVehicle(vehicle);
    };
    const onStationClick = (event: MapMouseEvent) => {
      // Desambiguación de solapamientos: si hay un tren bajo el puntero, gana
      // el tren, que es el objeto más pequeño y más difícil de acertar.
      if (map.queryRenderedFeatures(event.point, { layers: [LAYERS.vehicle] }).length > 0) return;
      const feature = map
        .queryRenderedFeatures(event.point, { layers: [LAYERS.stations] })
        .at(0);
      const stationId = feature?.properties?.stationId as string | undefined;
      if (stationId !== undefined) onSelectStation(stationId);
    };
    const onEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("click", LAYERS.vehicle, onVehicleClick);
    map.on("click", LAYERS.stations, onStationClick);
    map.on("mouseenter", LAYERS.vehicle, onEnter);
    map.on("mouseleave", LAYERS.vehicle, onLeave);
    map.on("mouseenter", LAYERS.stations, onEnter);
    map.on("mouseleave", LAYERS.stations, onLeave);
    return () => {
      map.off("click", LAYERS.vehicle, onVehicleClick);
      map.off("click", LAYERS.stations, onStationClick);
      map.off("mouseenter", LAYERS.vehicle, onEnter);
      map.off("mouseleave", LAYERS.vehicle, onLeave);
      map.off("mouseenter", LAYERS.stations, onEnter);
      map.off("mouseleave", LAYERS.stations, onLeave);
    };
  }, [onSelectVehicle, onSelectStation]);

  // Un gesto del usuario libera la cámara; los movimientos programáticos del
  // seguimiento no se confunden con un gesto.
  useEffect(() => {
    const map = mapRef.current;
    if (map === null) return;
    const release = () => onCameraGesture();
    map.on("dragstart", release);
    map.on("wheel", release);
    map.on("touchmove", release);
    return () => {
      map.off("dragstart", release);
      map.off("wheel", release);
      map.off("touchmove", release);
    };
  }, [onCameraGesture]);

  // Rótulos de estación acotados al contexto seleccionado: ni toda la red
  // rotulada ni un `symbol` con glifos remotos.
  useEffect(() => {
    const map = mapRef.current;
    if (map === null) return;
    // Desambiguación de solapamientos: por debajo de este zoom los nombres de
    // un patrón completo se pisan entre sí, así que no se rotulan. El objeto
    // seleccionado conserva siempre su rótulo.
    const readable = zoom >= LABEL_MIN_ZOOM;
    const wanted = new Set(
      readable ? labelledStationIds : labelledStationIds.slice(0, 1),
    );
    for (const [id, marker] of labelsRef.current) {
      if (id === "selected-vehicle") continue;
      if (!wanted.has(id)) {
        marker.remove();
        labelsRef.current.delete(id);
      }
    }
    for (const stationId of wanted) {
      if (labelsRef.current.has(stationId)) continue;
      const station = index.stationsById.get(stationId);
      if (station === undefined) continue;
      const element = document.createElement("span");
      element.className = "map-label";
      element.textContent = station.name;
      const marker = new maplibregl.Marker({ element, anchor: "left", offset: [10, 0] })
        .setLngLat([station.lon, station.lat])
        .addTo(map);
      labelsRef.current.set(stationId, marker);
    }
  }, [labelledStationIds, index, zoom]);

  // Rótulo del tren seleccionado: un único marcador DOM reutilizado.
  useEffect(() => {
    const map = mapRef.current;
    if (map === null) return;
    const existing = labelsRef.current.get("selected-vehicle");
    if (selectedVehicleKey === null) {
      existing?.remove();
      labelsRef.current.delete("selected-vehicle");
      return;
    }
    // Se busca en el array de vehículos, no en `vehicleIndexRef`: ese índice
    // lo puebla el efecto de la fuente «última lectura», que **retorna antes
    // de poblarlo** mientras el estilo del mapa no está listo. Al abrir un
    // enlace con circulación ya seleccionada (lo normal al volver desde el
    // histórico), el primer snapshot llegaba antes que el mapa y el rótulo se
    // quedaba fijo en «Sin línea» para siempre: `vehicles` no vuelve a cambiar
    // de identidad si el siguiente sondeo trae la misma revisión, así que el
    // efecto no se repetía nunca. Defecto real encontrado mirando el
    // navegador en MP-021, no detectado por ningún test.
    const vehicle = vehicles.find((item) => vehicleKey(item) === selectedVehicleKey);
    const label = `${vehicle?.line ?? "Sin línea"} · ${selectedVehicleKey.split("|")[0]}${vehicle ? ` · ${methodStyle(vehicle.rendered.rendering_method, vehicle.rendered.coordinate_space).label}` : ""}`;
    if (existing !== undefined) {
      existing.getElement().textContent = label;
      return;
    }
    const element = document.createElement("span");
    element.className = "map-label map-label--vehicle";
    element.textContent = label;
    const marker = new maplibregl.Marker({ element, anchor: "bottom", offset: [0, -14] })
      .setLngLat(MADRID_CENTER)
      .addTo(map);
    labelsRef.current.set("selected-vehicle", marker);
  }, [selectedVehicleKey, vehicles]);

  // Reencuadre explícito: una sola respuesta por pulsación, nunca un
  // `fitBounds` automático en cada sondeo.
  useEffect(() => {
    if (recenterToken === 0) return;
    const map = mapRef.current;
    if (map === null) return;
    map.easeTo({
      center: MADRID_CENTER,
      zoom: MADRID_ZOOM,
      duration: reducedMotion ? 0 : 600,
    });
  }, [recenterToken, reducedMotion]);

  const ariaLabel = useMemo(
    () =>
      `Mapa de Cercanías Madrid. ${vehicles.length} circulaciones en el snapshot. ` +
      "Usa la lista lateral o la búsqueda para seleccionar con teclado.",
    [vehicles.length],
  );

  return (
    <div className="map-shell">
      <div
        ref={containerRef}
        className="map-canvas"
        role="application"
        aria-label={ariaLabel}
      />
    </div>
  );
}

export { EMPTY_COLLECTION };
