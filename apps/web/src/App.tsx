import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { BoardEntry, RenderingMethod, Snapshot, SnapshotVehicle } from "./domain/contract";
import { circulationKey, circulationOf, selectionKey, vehicleKey, type CirculationId, type Selection } from "./domain/identity";
import { buildLineColors } from "./domain/palette";
import { deriveNews, mergeNews, type NewsEvent } from "./domain/news";
import { useCatalog } from "./hooks/useCatalog";
import { useClock, parseReplayBase } from "./hooks/useClock";
import { useHealth } from "./hooks/useHealth";
import { useMediaQuery } from "./hooks/useMediaQuery";
import { usePageVisible } from "./hooks/usePageVisible";
import { useReducedMotion } from "./hooks/useReducedMotion";
import { useSnapshot } from "./hooks/useSnapshot";
import { useStationBoard } from "./hooks/useStationBoard";
import { useUrlState } from "./hooks/useUrlState";
import { hasWebGL } from "./map/webgl";
import { Legend } from "./ui/Legend";
import { LineFilter } from "./ui/LineFilter";
import { NetworkPanel } from "./ui/NetworkPanel";
import { NewsTicker, type NewsItem } from "./ui/NewsTicker";
import { SearchBox } from "./ui/SearchBox";
import { StationPanel } from "./ui/StationPanel";
import { TopBar } from "./ui/TopBar";
import { TrainPanel } from "./ui/TrainPanel";

const MapView = lazy(() => import("./map/MapView").then((module) => ({ default: module.MapView })));

/** Cadencia del reloj visible de la ficha: legible, y no un render por frame. */
const PANEL_CLOCK_MS = 1_000;
const MOBILE_QUERY = "(max-width: 740px)";

export default function App() {
  const [url, setUrl] = useUrlState();
  const replayBaseMs = useMemo(() => parseReplayBase(url.replayAt), [url.replayAt]);
  const clock = useClock(replayBaseMs);
  const visible = usePageVisible();
  const reducedMotion = useReducedMotion();
  const isMobile = useMediaQuery(MOBILE_QUERY);
  const webgl = useMemo(() => hasWebGL(), []);

  const catalog = useCatalog(true);
  const snapshot = useSnapshot(clock, visible);
  const health = useHealth(visible);

  const selection = url.selection;
  const activeLines = useMemo(() => new Set(url.activeLines), [url.activeLines]);
  const selectedStationId = selection.kind === "station" ? selection.stationId : null;
  const board = useStationBoard(selectedStationId, clock, visible);

  const [followKey, setFollowKey] = useState<string | null>(null);
  const [cameraReleased, setCameraReleased] = useState(false);
  const [recenterToken, setRecenterToken] = useState(0);
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [newsPaused, setNewsPaused] = useState(reducedMotion);
  const [panelExpanded, setPanelExpanded] = useState(false);
  const [panelNowMs, setPanelNowMs] = useState(() => clock.nowMs());
  const [returnTo, setReturnTo] = useState<Selection | null>(null);

  const previousSnapshotRef = useRef<Snapshot | null>(null);

  // Reloj visible de la ficha: un render por segundo, nunca por fotograma.
  // El valor inicial ya lo fija el estado al montar; el intervalo solo lo
  // hace avanzar, sin un `setState` sincrónico dentro del efecto.
  useEffect(() => {
    const timer = window.setInterval(() => setPanelNowMs(clock.nowMs()), PANEL_CLOCK_MS);
    return () => window.clearInterval(timer);
  }, [clock]);

  // Novedades derivadas de dos snapshots reales, sin duplicar avisos.
  useEffect(() => {
    const current = snapshot.data;
    if (current === null) return;
    const previous = previousSnapshotRef.current;
    if (previous !== null && previous.snapshot_id === current.snapshot_id) return;
    const derived = deriveNews(current, previous);
    previousSnapshotRef.current = current;
    if (derived.length === 0) return;
    setNews((existing) => mergeNews(existing, derived));
  }, [snapshot.data]);

  const colors = useMemo(
    () => buildLineColors((catalog.index?.catalog.lines ?? []).map((line) => line.line_id)),
    [catalog.index],
  );

  const vehicles = useMemo(() => snapshot.data?.vehicles ?? [], [snapshot.data]);
  const visibleVehicles = useMemo(
    () =>
      activeLines.size === 0
        ? vehicles
        : vehicles.filter((vehicle) => vehicle.line !== null && activeLines.has(vehicle.line)),
    [vehicles, activeLines],
  );

  const vehiclesByKey = useMemo(() => {
    const map = new Map<string, SnapshotVehicle>();
    for (const vehicle of vehicles) map.set(vehicleKey(vehicle), vehicle);
    return map;
  }, [vehicles]);

  const selectedVehicleKey =
    selection.kind === "train" ? circulationKey(selection.circulation) : null;
  const selectedVehicle =
    selectedVehicleKey === null ? null : (vehiclesByKey.get(selectedVehicleKey) ?? null);

  const lineCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const vehicle of vehicles) {
      if (vehicle.line === null) continue;
      counts.set(vehicle.line, (counts.get(vehicle.line) ?? 0) + 1);
    }
    return counts;
  }, [vehicles]);

  const presentMethods = useMemo(() => {
    const present = new Set<RenderingMethod>();
    for (const vehicle of visibleVehicles) present.add(vehicle.rendered.rendering_method);
    return present;
  }, [visibleVehicles]);

  // --- Navegación -------------------------------------------------------

  const navigate = useCallback(
    (next: Selection, push = true) => {
      setUrl({ selection: next, activeLines: url.activeLines, replayAt: url.replayAt }, push);
    },
    [setUrl, url.activeLines, url.replayAt],
  );

  const selectStation = useCallback(
    (stationId: string) => {
      setReturnTo(null);
      navigate({ kind: "station", stationId });
    },
    [navigate],
  );

  const selectCirculation = useCallback(
    (circulation: CirculationId, from: Selection | null = null) => {
      setReturnTo(from);
      navigate({ kind: "train", circulation });
    },
    [navigate],
  );

  const selectVehicle = useCallback(
    (vehicle: SnapshotVehicle) => {
      selectCirculation(circulationOf(vehicle), selection.kind === "station" ? selection : null);
    },
    [selectCirculation, selection],
  );

  const toggleLine = useCallback(
    (lineId: string) => {
      const next = new Set(url.activeLines);
      if (next.has(lineId)) next.delete(lineId);
      else next.add(lineId);
      setUrl({ selection, activeLines: [...next], replayAt: url.replayAt }, false);
    },
    [setUrl, selection, url.activeLines, url.replayAt],
  );

  const clearLines = useCallback(() => {
    setUrl({ selection, activeLines: [], replayAt: url.replayAt }, false);
  }, [setUrl, selection, url.replayAt]);

  const openLine = useCallback(
    (lineId: string) => {
      setUrl({ selection, activeLines: [lineId], replayAt: url.replayAt }, false);
    },
    [setUrl, selection, url.replayAt],
  );

  // --- Seguimiento y cámara ---------------------------------------------

  // Seguir es explícito y nunca una consecuencia de seleccionar. El
  // seguimiento efectivo se **deriva** de la selección vigente, así que al
  // cambiar de circulación deja de aplicarse sin arrastrarse a otra y sin
  // un efecto que corrija el estado después de pintar.
  const activeFollowKey = followKey === selectedVehicleKey ? followKey : null;

  const toggleFollow = useCallback(() => {
    if (selectedVehicleKey === null) return;
    setCameraReleased(false);
    setFollowKey((current) => (current === selectedVehicleKey ? null : selectedVehicleKey));
  }, [selectedVehicleKey]);

  // Un gesto libera la cámara pero **conserva la ficha**: solo deja de
  // arrastrarla y ofrece volver.
  const onCameraGesture = useCallback(() => {
    setFollowKey((current) => {
      if (current === null) return null;
      setCameraReleased(true);
      return null;
    });
  }, []);

  const backToTrain = useCallback(() => {
    if (selectedVehicleKey === null) return;
    setCameraReleased(false);
    setFollowKey(selectedVehicleKey);
  }, [selectedVehicleKey]);

  const openBoardEntry = useCallback(
    (entry: BoardEntry) => {
      if (entry.vehicle_id === null) return;
      selectCirculation(
        { vehicleId: entry.vehicle_id, tripId: entry.trip_id, serviceDate: entry.service_date },
        selection,
      );
    },
    [selectCirculation, selection],
  );

  // Rótulos: solo el contexto seleccionado, no los 95 nombres a la vez.
  const labelledStationIds = useMemo(() => {
    if (catalog.index === null) return [];
    if (selection.kind === "station") return [selection.stationId];
    if (selection.kind === "train" && selectedVehicle?.pattern_id != null) {
      const pattern = catalog.index.patternsById.get(selectedVehicle.pattern_id);
      return pattern?.stations.map((station) => station.station_id) ?? [];
    }
    return [];
  }, [catalog.index, selection, selectedVehicle]);

  const newsItems: NewsItem[] = useMemo(
    () =>
      news.map((event) => ({
        id: event.id,
        text: event.text,
        onOpen:
          event.circulation === null
            ? undefined
            : () => selectCirculation(event.circulation as CirculationId),
      })),
    [news, selectCirculation],
  );

  const degradedCount = snapshot.data?.degraded.length ?? 0;
  const mode = snapshot.data?.mode ?? catalog.data?.mode ?? health.data?.mode ?? null;

  const panel = (() => {
    if (catalog.index === null) {
      return (
        <div className="panel-body">
          <p className="label">Catálogo</p>
          <h1>Cargando la red</h1>
          <p className="meta">
            {catalog.error ?? "Descargando el catálogo cacheable de Cercanías Madrid…"}
          </p>
        </div>
      );
    }
    if (selection.kind === "train") {
      return (
        <TrainPanel
          index={catalog.index}
          colors={colors}
          circulation={selection.circulation}
          vehicle={selectedVehicle}
          nowMs={panelNowMs}
          following={activeFollowKey !== null}
          cameraReleased={cameraReleased}
          onToggleFollow={toggleFollow}
          onBackToCamera={backToTrain}
          onOpenStation={selectStation}
          onOpenLine={openLine}
          onBack={
            returnTo !== null && returnTo.kind === "station"
              ? () => navigate(returnTo)
              : () => navigate({ kind: "none" })
          }
          backLabel={
            returnTo !== null && returnTo.kind === "station"
              ? `Tablero de ${catalog.index.stationsById.get(returnTo.stationId)?.name ?? returnTo.stationId}`
              : "Volver a la red"
          }
        />
      );
    }
    if (selection.kind === "station") {
      return (
        <StationPanel
          index={catalog.index}
          colors={colors}
          stationId={selection.stationId}
          board={board.data}
          error={board.error}
          loading={board.loading}
          onOpenEntry={openBoardEntry}
          onOpenLine={openLine}
        />
      );
    }
    return (
      <NetworkPanel
        index={catalog.index}
        colors={colors}
        snapshot={snapshot.data}
        vehicles={visibleVehicles}
        activeLines={activeLines}
        onOpenVehicle={selectVehicle}
        onOpenStation={selectStation}
      />
    );
  })();

  return (
    <div className={panelExpanded ? "app app--expanded" : "app"}>
      <TopBar
        mode={mode}
        nowMs={panelNowMs}
        snapshot={snapshot.data}
        degradedCount={degradedCount}
        snapshotError={snapshot.error}
      />

      <main className="workspace">
        <aside className="side-panel" aria-label="Panel de navegación y detalle">
          {isMobile && (
            <button
              type="button"
              className="sheet-toggle"
              onClick={() => setPanelExpanded((value) => !value)}
              aria-expanded={panelExpanded}
            >
              {panelExpanded ? "Recoger panel" : "Ampliar panel"}
            </button>
          )}
          <SearchBox index={catalog.index} onPickStation={selectStation} onPickLine={openLine} />
          <LineFilter
            index={catalog.index}
            colors={colors}
            activeLines={activeLines}
            counts={lineCounts}
            onToggle={toggleLine}
            onClear={clearLines}
          />
          {(snapshot.error !== null || degradedCount > 0) && (
            <p className="notice notice--warn" role="status">
              {snapshot.error !== null
                ? `El snapshot no se pudo actualizar (${snapshot.error}). Se conserva el último válido y su edad sigue avanzando.`
                : `${degradedCount} recurso(s) degradado(s): se conserva el último dato válido con su hora.`}
            </p>
          )}
          {panel}
        </aside>

        <section className="map-column" aria-label="Mapa de la red">
          {webgl && catalog.index !== null ? (
            <Suspense fallback={<div className="map-message">Preparando el mapa…</div>}>
              <MapView
                index={catalog.index}
                colors={colors}
                vehicles={visibleVehicles}
                activeLines={activeLines}
                selectedVehicleKey={selectedVehicleKey}
                selectedStationId={selectedStationId}
                labelledStationIds={labelledStationIds}
                followKey={activeFollowKey}
                reducedMotion={reducedMotion}
                clock={clock}
                onSelectVehicle={selectVehicle}
                onSelectStation={selectStation}
                onCameraGesture={onCameraGesture}
                recenterToken={recenterToken}
              />
            </Suspense>
          ) : (
            <div className="map-fallback">
              <p className="label">Mapa no disponible</p>
              <h2>
                {webgl
                  ? "Esperando el catálogo"
                  : "Este navegador no ofrece WebGL"}
              </h2>
              <p className="meta">
                {webgl
                  ? "El mapa aparecerá en cuanto el catálogo esté cargado."
                  : "La navegación sigue siendo completa: busca una estación, abre su tablero y seleccióna una circulación desde el panel."}
              </p>
            </div>
          )}
          <div className="map-overlay">
            <button
              type="button"
              className="map-button"
              onClick={() => setRecenterToken((value) => value + 1)}
            >
              Centrar Madrid
            </button>
            {activeFollowKey !== null && (
              <span className="map-badge">Siguiendo · arrastra para soltar la cámara</span>
            )}
            {cameraReleased && activeFollowKey === null && selectedVehicleKey !== null && (
              <button type="button" className="map-button" onClick={backToTrain}>
                Volver al tren
              </button>
            )}
          </div>
          <Legend present={presentMethods} />
        </section>
      </main>

      <NewsTicker
        items={newsItems}
        paused={newsPaused}
        onTogglePause={() => setNewsPaused((value) => !value)}
        reducedMotion={reducedMotion}
      />
      <p className="visually-hidden" aria-live="polite">
        {selection.kind === "none"
          ? "Vista de red"
          : selection.kind === "station"
            ? `Estación seleccionada: ${catalog.index?.stationsById.get(selection.stationId)?.name ?? selection.stationId}`
            : `Circulación seleccionada: ${selection.circulation.vehicleId}`}
      </p>
      <span className="visually-hidden">{selectionKey(selection)}</span>
    </div>
  );
}
