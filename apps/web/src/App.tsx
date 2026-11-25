import { DegradationNotice } from "./ui/DegradationNotice";
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  BoardEntry,
  HistoryCirculation,
  HistoryFilter,
  RenderingMethod,
  Snapshot,
  SnapshotVehicle,
} from "./domain/contract";
import { circulationKey, circulationOf, selectionKey, vehicleKey, type CirculationId, type Selection } from "./domain/identity";
import { buildLineColors } from "./domain/palette";
import { deriveNews, mergeNews, type NewsEvent } from "./domain/news";
import { useCatalog } from "./hooks/useCatalog";
import { useClock, parseReplayBase } from "./hooks/useClock";
import { useHealth } from "./hooks/useHealth";
import {
  useHistoryCirculation,
  useHistoryCirculations,
  useHistoryDays,
  useHistoryLines,
  useHistoryStations,
} from "./hooks/useHistory";
import { useMediaQuery } from "./hooks/useMediaQuery";
import { usePageVisible } from "./hooks/usePageVisible";
import { useReducedMotion } from "./hooks/useReducedMotion";
import { useSnapshot } from "./hooks/useSnapshot";
import { useStationBoard } from "./hooks/useStationBoard";
import { useUrlState, type UrlState, type View } from "./hooks/useUrlState";
import { hasWebGL } from "./map/webgl";
import { ExploreView } from "./ui/ExploreView";
import { HistoryView } from "./ui/HistoryView";
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

  // --- Histórico ---------------------------------------------------------
  // Los recursos del archivo solo se piden cuando su vista está activa: en
  // Live no se gasta ni una petición en el histórico, y el snapshot sigue
  // sondeándose en History porque es lo que permite decir si una circulación
  // archivada está además en circulación ahora mismo («Ver en Live»).
  const isHistory = url.view === "history";
  const isExplore = url.view === "explore";
  const isArchiveView = isHistory || isExplore;

  const historyDays = useHistoryDays(isArchiveView && visible);
  // Sin fecha en la URL se usa el día más reciente archivado, no "hoy": un
  // calendario libre ofrecería días sin archivo que solo pueden dar 404.
  const historyDate = url.historyDate ?? historyDays.data?.days[0]?.service_date ?? null;
  const historyCirculations = useHistoryCirculations(
    historyDate,
    url.historyLine,
    url.historyFilter,
    isHistory && visible,
  );
  const historyLines = useHistoryLines(historyDate, isExplore && visible);
  const historyStations = useHistoryStations(historyDate, isExplore && visible);

  // La circulación seleccionada en History es la misma identidad que en Live:
  // vehículo + viaje + día de servicio, leída de los mismos parámetros de URL.
  const historySelection = isHistory && selection.kind === "train" ? selection.circulation : null;
  const historyDetail = useHistoryCirculation(
    historySelection?.serviceDate ?? null,
    historySelection === null || historySelection.vehicleId === ""
      ? null
      : historySelection.vehicleId,
    historySelection?.tripId ?? null,
    isHistory && visible,
  );

  // Intención explícita de seguir una circulación, separada de si la cámara
  // está ahora mismo enganchada: un gesto del usuario la desengancha sin
  // borrar la intención, que es lo que permite ofrecer «Volver al tren».
  const [followIntent, setFollowIntent] = useState<string | null>(null);
  const [cameraDetached, setCameraDetached] = useState(false);
  const [recenterToken, setRecenterToken] = useState(0);
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [newsPaused, setNewsPaused] = useState(reducedMotion);
  const [panelExpanded, setPanelExpanded] = useState(false);
  const [panelNowMs, setPanelNowMs] = useState(() => clock.nowMs());
  const [returnTo, setReturnTo] = useState<Selection | null>(null);

  const previousSnapshotRef = useRef<Snapshot | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  const selectionId = selectionKey(selection);

  // Al cambiar de objeto, la ficha empieza por su encabezado: sin esto el
  // panel conserva el desplazamiento del tablero anterior y la cabecera (con
  // el destino y el botón de seguir) queda fuera de la vista.
  useEffect(() => {
    panelRef.current?.scrollTo({ top: 0 });
  }, [selectionId]);

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
      setUrl({ ...url, selection: next }, push);
    },
    [setUrl, url],
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
      setUrl({ ...url, selection, activeLines: [...next] }, false);
    },
    [setUrl, selection, url],
  );

  const clearLines = useCallback(() => {
    setUrl({ ...url, selection, activeLines: [] }, false);
  }, [setUrl, selection, url]);

  const openLine = useCallback(
    (lineId: string) => {
      setUrl({ ...url, selection, activeLines: [lineId] }, false);
    },
    [setUrl, selection, url],
  );

  // --- Navegación entre vistas ------------------------------------------

  const changeView = useCallback(
    (view: View) => {
      // Cambiar de vista **conserva** la circulación seleccionada: es la misma
      // identidad en ambas, así que Live → History → Live devuelve al mismo
      // objeto sin traducir ninguna clave. Al entrar en History con una
      // circulación seleccionada, su día de servicio fija la fecha consultada.
      const next: UrlState = { ...url, view };
      if (view === "history" && selection.kind === "train") {
        next.historyDate = selection.circulation.serviceDate;
      }
      setUrl(next, true);
    },
    [setUrl, url, selection],
  );

  const pickHistoryDate = useCallback(
    (serviceDate: string) => {
      // Al cambiar de día se suelta la circulación seleccionada: la misma
      // identidad no existe en otro día de servicio, y arrastrarla daría un
      // 404 o, peor, parecería la misma circulación en una fecha ajena.
      setUrl({ ...url, historyDate: serviceDate, selection: { kind: "none" } }, true);
    },
    [setUrl, url],
  );

  const pickHistoryLine = useCallback(
    (line: string | null) => {
      setUrl({ ...url, historyLine: line, selection: { kind: "none" } }, false);
    },
    [setUrl, url],
  );

  const pickHistoryFilter = useCallback(
    (filter: HistoryFilter) => {
      setUrl({ ...url, historyFilter: filter, selection: { kind: "none" } }, false);
    },
    [setUrl, url],
  );

  const openHistoryCirculation = useCallback(
    (circulation: HistoryCirculation) => {
      setUrl(
        {
          ...url,
          historyDate: circulation.service_date,
          selection: {
            kind: "train",
            circulation: {
              // Una circulación programada sin observar no tiene vehículo: se
              // representa con cadena vacía y la URL omite `train`, en vez de
              // fabricar un identificador.
              vehicleId: circulation.vehicle_id ?? "",
              tripId: circulation.trip_id,
              serviceDate: circulation.service_date,
            },
          },
        },
        true,
      );
    },
    [setUrl, url],
  );

  const backToHistoryList = useCallback(() => {
    setUrl({ ...url, selection: { kind: "none" } }, true);
  }, [setUrl, url]);

  const openHistoryLineInList = useCallback(
    (line: string) => {
      setUrl(
        { ...url, view: "history", historyLine: line, selection: { kind: "none" } },
        true,
      );
    },
    [setUrl, url],
  );

  // --- Seguimiento y cámara ---------------------------------------------

  // Seguir es explícito y nunca una consecuencia de seleccionar. Todo se
  // **deriva** de la intención y de la selección vigente: al cambiar de
  // circulación el seguimiento no se arrastra a otra, y no hace falta un
  // efecto que corrija el estado después de pintar.
  const followsSelection = followIntent !== null && followIntent === selectedVehicleKey;
  const activeFollowKey = followsSelection && !cameraDetached ? followIntent : null;
  const canReturnToTrain = followsSelection && cameraDetached;

  // El gesto solo tiene efecto si había seguimiento activo; se lee de una ref
  // para que el manejador registrado en el mapa nunca use un valor obsoleto.
  const followingRef = useRef(false);
  useEffect(() => {
    followingRef.current = activeFollowKey !== null;
  }, [activeFollowKey]);

  const toggleFollow = useCallback(() => {
    if (selectedVehicleKey === null) return;
    setCameraDetached(false);
    setFollowIntent((current) => (current === selectedVehicleKey ? null : selectedVehicleKey));
  }, [selectedVehicleKey]);

  // Un gesto suelta la cámara pero **conserva la ficha** y la intención de
  // seguimiento: solo deja de arrastrar la cámara y ofrece volver.
  const onCameraGesture = useCallback(() => {
    if (!followingRef.current) return;
    followingRef.current = false;
    setCameraDetached(true);
  }, []);

  const backToTrain = useCallback(() => {
    if (selectedVehicleKey === null) return;
    setCameraDetached(false);
    setFollowIntent(selectedVehicleKey);
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

  // Señal de "ha llegado una respuesta nueva": la revisión del contrato, no
  // `snapshot_id`, que es identidad de contenido y se repite si los vehículos
  // no cambiaron aunque el instante de presentación sí avance.
  const snapshotStamp = useMemo(() => {
    const revision = snapshot.data?.revision;
    if (revision === undefined) return null;
    return `${revision.scope}|${revision.sequence ?? "none"}|${revision.generated_at}`;
  }, [snapshot.data]);

  const mapIndex = catalog.index;
  const mapAvailable = webgl && mapIndex !== null;
  const degradedCount = snapshot.data?.degraded.length ?? 0;
  const mode = snapshot.data?.mode ?? catalog.data?.mode ?? health.data?.mode ?? null;

  // Una circulación archivada solo se puede «ver en Live» si está de verdad en
  // el snapshot vigente: ofrecer el salto sin comprobarlo llevaría a una ficha
  // vacía. La comprobación es por identidad completa, no por `vehicle_id`.
  const selectedIsLiveNow =
    historySelection !== null &&
    historySelection.vehicleId !== "" &&
    vehiclesByKey.has(circulationKey(historySelection));

  const openSelectedInLive = useCallback(() => {
    setUrl({ ...url, view: "live" }, true);
  }, [setUrl, url]);

  const panel = (() => {
    if (isHistory) {
      return (
        <HistoryView
          index={catalog.index}
          colors={colors}
          days={historyDays.data}
          daysError={historyDays.error}
          daysLoading={historyDays.loading}
          serviceDate={historyDate}
          line={url.historyLine}
          filter={url.historyFilter}
          circulations={historyCirculations.data}
          circulationsError={historyCirculations.error}
          circulationsLoading={historyCirculations.loading}
          selected={historySelection}
          detail={historyDetail.data}
          detailError={historyDetail.error}
          detailLoading={historyDetail.loading}
          selectedIsLiveNow={selectedIsLiveNow}
          onPickDate={pickHistoryDate}
          onPickLine={pickHistoryLine}
          onPickFilter={pickHistoryFilter}
          onOpenCirculation={openHistoryCirculation}
          onBackToList={backToHistoryList}
          onOpenInLive={openSelectedInLive}
        />
      );
    }
    if (isExplore) {
      return (
        <ExploreView
          index={catalog.index}
          colors={colors}
          days={historyDays.data}
          daysError={historyDays.error}
          serviceDate={historyDate}
          lines={historyLines.data}
          linesError={historyLines.error}
          linesLoading={historyLines.loading}
          stations={historyStations.data}
          stationsError={historyStations.error}
          onPickDate={pickHistoryDate}
          onOpenLineInHistory={openHistoryLineInList}
        />
      );
    }
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
          cameraReleased={canReturnToTrain}
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
    <div
      className={[
        "app",
        panelExpanded ? "app--expanded" : "",
        isArchiveView ? "app--archive" : "",
      ]
        .filter((token) => token !== "")
        .join(" ")}
    >
      <TopBar
        mode={mode}
        nowMs={panelNowMs}
        snapshot={snapshot.data}
        degradedCount={degradedCount}
        snapshotError={snapshot.error}
        view={url.view}
        onChangeView={changeView}
      />

      <main className="workspace">
        <aside ref={panelRef} className="side-panel" aria-label="Panel de navegación y detalle">
          {isMobile && !isArchiveView && (
            <button
              type="button"
              className="sheet-toggle"
              onClick={() => setPanelExpanded((value) => !value)}
              aria-expanded={panelExpanded}
            >
              {panelExpanded ? "Recoger panel" : "Ampliar panel"}
            </button>
          )}
          {/* Búsqueda, filtro de líneas y avisos del snapshot son de Live: en
              el archivo filtrarían un dato que no se está sondeando. */}
          {!isArchiveView && (
            <>
              <SearchBox
                index={catalog.index}
                onPickStation={selectStation}
                onPickLine={openLine}
              />
              <LineFilter
                index={catalog.index}
                colors={colors}
                activeLines={activeLines}
                counts={lineCounts}
                onToggle={toggleLine}
                onClear={clearLines}
              />
              {snapshot.error !== null && (
                <p className="notice notice--warn" role="status">El snapshot no se pudo actualizar ({snapshot.error}). Se conserva el último válido y su edad sigue avanzando.</p>
              )}
              {snapshot.data?.degraded.map((item, i) => (
                <DegradationNotice item={item} key={`${item.resource}-${item.feed_name ?? i}`} />
              ))}
            </>
          )}
          {panel}
        </aside>

        {!isArchiveView && (
        <section className="map-column" aria-label="Mapa de la red">
          {mapAvailable ? (
            <Suspense fallback={<div className="map-message">Preparando el mapa…</div>}>
              <MapView
                index={mapIndex}
                colors={colors}
                vehicles={visibleVehicles}
                activeLines={activeLines}
                selectedVehicleKey={selectedVehicleKey}
                selectedStationId={selectedStationId}
                labelledStationIds={labelledStationIds}
                followKey={activeFollowKey}
                reducedMotion={reducedMotion}
                clock={clock}
                snapshotStamp={snapshotStamp}
                displayAtMs={
                  snapshot.data === null ? null : Date.parse(snapshot.data.display_at)
                }
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
                  : "La navegación sigue siendo completa: busca una estación, abre su tablero y selecciona una circulación desde el panel."}
              </p>
            </div>
          )}
          <div className="map-overlay">
            {mapAvailable && (
              <button
                type="button"
                className="map-button"
                onClick={() => setRecenterToken((value) => value + 1)}
              >
                Centrar Madrid
              </button>
            )}
            {activeFollowKey !== null && (
              <span className="map-badge">Siguiendo · arrastra para soltar la cámara</span>
            )}
            {canReturnToTrain && (
              <button type="button" className="map-button" onClick={backToTrain}>
                Volver al tren
              </button>
            )}
          </div>
          {mapAvailable && <Legend present={presentMethods} />}
        </section>
        )}
      </main>

      {!isArchiveView && (
        <NewsTicker
          items={newsItems}
          paused={newsPaused}
          onTogglePause={() => setNewsPaused((value) => !value)}
          reducedMotion={reducedMotion}
        />
      )}
      <p className="visually-hidden" aria-live="polite">
        {isArchiveView
          ? `Vista de archivo: ${url.view === "history" ? "histórico" : "Explore"}${historyDate === null ? "" : `, día ${historyDate}`}`
          : selection.kind === "none"
            ? "Vista de red"
            : selection.kind === "station"
              ? `Estación seleccionada: ${catalog.index?.stationsById.get(selection.stationId)?.name ?? selection.stationId}`
              : `Circulación seleccionada: ${selection.circulation.vehicleId}`}
      </p>
      <span className="visually-hidden">{selectionId}</span>
    </div>
  );
}
