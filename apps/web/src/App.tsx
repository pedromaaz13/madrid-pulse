import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { fetchDashboard } from "./api";
import { formatAge, formatDelay, MODE_LABELS } from "./format";
import type { Health, LayerVisibility, Line, PositionMode, Vehicle } from "./types";

const POLL_INTERVAL_MS = 20_000;
const MODES = Object.keys(MODE_LABELS) as PositionMode[];
const MapView = lazy(() => import("./MapView").then((module) => ({ default: module.MapView })));

export default function App() {
  const [lines, setLines] = useState<Line[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [health, setHealth] = useState<Health>({ feeds: [] });
  const [lineKey, setLineKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [recenterToken, setRecenterToken] = useState(0);
  const [layers, setLayers] = useState<LayerVisibility>({ corridor: true, stations: true, vehicles: true });

  const load = useCallback(async (signal?: AbortSignal) => {
    setRefreshing(true);
    try {
      const dashboard = await fetchDashboard(signal);
      setLines(dashboard.lines);
      setVehicles(dashboard.vehicles);
      setHealth(dashboard.health);
      setLineKey((current) => current || (dashboard.lines[0] ? `${dashboard.lines[0].network_id}:${dashboard.lines[0].line_id}` : ""));
      setUpdatedAt(new Date());
      setError(null);
    } catch (reason) {
      if (!(reason instanceof DOMException && reason.name === "AbortError")) {
        setError(reason instanceof Error ? reason.message : "No se pudo actualizar la red");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const initial = window.setTimeout(() => void load(controller.signal), 0);
    const timer = window.setInterval(() => void load(controller.signal), POLL_INTERVAL_MS);
    return () => {
      controller.abort();
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [load]);

  const selectedLine = useMemo(
    () => lines.find((line) => `${line.network_id}:${line.line_id}` === lineKey) ?? null,
    [lineKey, lines],
  );
  const located = vehicles.filter((vehicle) => vehicle.position !== null);
  const unresolved = vehicles.filter((vehicle) => vehicle.position === null || vehicle.route_id === null);
  const selectedVehicles = selectedLine ? located.filter((vehicle) => vehicle.line === selectedLine.line_id) : located;
  const unhealthy = health.feeds.some((feed) => feed.status !== "ok");

  function toggleLayer(layer: keyof LayerVisibility) {
    setLayers((current) => ({ ...current, [layer]: !current[layer] }));
  }

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <div><p>Madrid Pulse</p><span>Red ferroviaria en vivo</span></div>
        </div>
        <div className={`feed-state ${unhealthy ? "feed-state--warn" : ""}`}>
          <span aria-hidden="true" />
          {health.feeds.length ? (unhealthy ? "Fuente con incidencias" : "Fuentes conectadas") : "Conectando fuentes"}
        </div>
      </header>

      <section className="hero-panel">
        <div>
          <p className="eyebrow">Movilidad metropolitana · datos reales</p>
          <h1>La red, sin ocultar la incertidumbre.</h1>
          <p className="hero-copy">Cada tren indica si su posición fue observada, estimada, quedó obsoleta o procede solo del horario.</p>
        </div>
        <div className="hero-stats" aria-label="Resumen de datos">
          <div><strong>{vehicles.length}</strong><span>vehículos detectados</span></div>
          <div><strong>{selectedVehicles.length}</strong><span>ubicables en la línea</span></div>
          <div><strong>{selectedLine?.geometry?.stations.length ?? "—"}</strong><span>estaciones en corredor</span></div>
        </div>
      </section>

      <section className="workspace">
        <div className="map-column">
          <div className="toolbar" aria-label="Controles del mapa">
            <label htmlFor="line-selector">
              <span>Línea</span>
              <select id="line-selector" name="line" value={lineKey} onChange={(event) => setLineKey(event.target.value)} disabled={!lines.length}>
                {lines.map((line) => <option key={`${line.network_id}:${line.line_id}`} value={`${line.network_id}:${line.line_id}`}>{line.line_id}</option>)}
              </select>
            </label>
            <div className="layer-toggles">
              {(Object.keys(layers) as (keyof LayerVisibility)[]).map((layer) => (
                <button key={layer} className={layers[layer] ? "active" : ""} onClick={() => toggleLayer(layer)} aria-pressed={layers[layer]}>
                  {layer === "corridor" ? "Trazado" : layer === "stations" ? "Estaciones" : "Trenes"}
                </button>
              ))}
            </div>
            <button className="icon-button" onClick={() => setRecenterToken((value) => value + 1)} aria-label="Centrar el mapa en la línea">⌖</button>
            <button className="refresh-button" onClick={() => void load()} disabled={refreshing}>{refreshing ? "Actualizando…" : "Actualizar"}</button>
          </div>

          <div className="map-frame">
            <Suspense fallback={<div className="map-message">Preparando el mapa…</div>}>
              <MapView line={selectedLine} vehicles={selectedVehicles} layers={layers} recenterToken={recenterToken} />
            </Suspense>
            {loading && <div className="map-message">Cargando la red real…</div>}
            {!loading && selectedLine && !selectedLine.geometry && <div className="map-message">Esta línea no tiene un corredor cargado. No se dibuja geometría inventada.</div>}
            {error && <div className="error-banner" role="alert"><strong>No se pudo actualizar</strong><span>{error}</span></div>}
          </div>

          <div className="legend" aria-label="Leyenda de calidad de posición">
            {MODES.map((mode) => (
              <div key={mode} className="legend-item">
                <span className={`legend-symbol legend-symbol--${mode}`} aria-hidden="true" />
                <div><strong>{MODE_LABELS[mode].label}</strong><span>{MODE_LABELS[mode].detail}</span></div>
              </div>
            ))}
          </div>
        </div>

        <aside className="side-panel" aria-label="Estado de vehículos">
          <div className="side-heading">
            <div><p className="eyebrow">Estado actual</p><h2>Trenes de {selectedLine?.line_id ?? "la red"}</h2></div>
            <span>{updatedAt ? `Consulta ${updatedAt.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}` : "Sin actualizar"}</span>
          </div>
          <div className="vehicle-list">
            {selectedVehicles.length ? selectedVehicles.map((vehicle) => (
              <article className="vehicle-card" key={vehicle.vehicle_id}>
                <div className="vehicle-card__top">
                  <span className={`mode-dot mode-dot--${vehicle.position!.mode}`} aria-hidden="true" />
                  <div><h3>{vehicle.vehicle_id}</h3><p>{vehicle.trip_id}</p></div>
                  <span className={`mode-pill mode-pill--${vehicle.position!.mode}`}>{MODE_LABELS[vehicle.position!.mode].label}</span>
                </div>
                <div className="vehicle-card__meta"><span>{formatAge(vehicle.observation.age_s)}</span><span>{formatDelay(vehicle)}</span><span>{Math.round(vehicle.position!.confidence * 100)}% confianza</span></div>
                {vehicle.delay.coverage === "missing" && <p className="coverage-note">La fuente no aporta retraso para este viaje; no se interpreta como cero.</p>}
              </article>
            )) : <p className="empty-state">No hay vehículos ubicables para la línea seleccionada.</p>}
          </div>
          <div className="unresolved-panel">
            <div><strong>{unresolved.length} vehículos sin ubicar</strong><span>Existen en el feed, pero su línea o posición no resuelve contra la topología cargada.</span></div>
            <details><summary>Ver identificadores</summary><ul>{unresolved.map((vehicle) => <li key={vehicle.vehicle_id}>{vehicle.vehicle_id} · {formatAge(vehicle.observation.age_s)}</li>)}</ul></details>
          </div>
        </aside>
      </section>
    </main>
  );
}
