import { useCallback, useEffect, useState } from "react";
import type { HistoryFilter } from "../domain/contract";
import type { Selection } from "../domain/identity";

export type View = "live" | "history" | "explore";

const VIEWS: readonly View[] = ["live", "history", "explore"];
const FILTERS: readonly HistoryFilter[] = ["all", "observed", "unobserved", "unscheduled"];
const SERVICE_DATE = /^\d{4}-\d{2}-\d{2}$/;

export interface UrlState {
  view: View;
  selection: Selection;
  activeLines: string[];
  replayAt: string | null;
  /** Día de servicio del histórico (`hd`). `null` = el más reciente archivado. */
  historyDate: string | null;
  /** Línea comercial filtrada en el histórico (`hl`). */
  historyLine: string | null;
  /** Filtro de cobertura del histórico (`hf`). */
  historyFilter: HistoryFilter;
}

export const INITIAL_URL_STATE: UrlState = {
  view: "live",
  selection: { kind: "none" },
  activeLines: [],
  replayAt: null,
  historyDate: null,
  historyLine: null,
  historyFilter: "all",
};

function parse(search: string): UrlState {
  const params = new URLSearchParams(search);
  const station = params.get("station");
  const vehicle = params.get("train");
  const trip = params.get("trip");
  const serviceDate = params.get("sd");
  const lines = (params.get("lines") ?? "")
    .split(",")
    .map((value) => value.trim())
    .filter((value) => value !== "");

  let selection: Selection = { kind: "none" };
  // Un enlace restaura el objeto **y** su fecha de circulación: sin los tres
  // campos no se reconstruye una identidad a medias. Los mismos tres
  // parámetros valen en Live y en History: así cambiar de vista conserva la
  // circulación sin traducir ninguna clave (MP-021).
  if (vehicle !== null && trip !== null && serviceDate !== null) {
    selection = { kind: "train", circulation: { vehicleId: vehicle, tripId: trip, serviceDate } };
  } else if (trip !== null && serviceDate !== null) {
    // Circulación programada que nunca se observó: no tiene vehículo, y
    // fabricarle uno sería inventar un dato. Se representa con vehículo vacío.
    selection = { kind: "train", circulation: { vehicleId: "", tripId: trip, serviceDate } };
  } else if (station !== null && station !== "") {
    selection = { kind: "station", stationId: station };
  }

  const view = params.get("view");
  const historyDate = params.get("hd");
  const historyFilter = params.get("hf");

  return {
    // Un `view` desconocido no rompe la aplicación ni muestra una pantalla en
    // blanco: se cae a Live, que es la vista por omisión del producto.
    view: VIEWS.includes(view as View) ? (view as View) : "live",
    selection,
    activeLines: lines,
    replayAt: params.get("at"),
    historyDate: historyDate !== null && SERVICE_DATE.test(historyDate) ? historyDate : null,
    historyLine: params.get("hl"),
    historyFilter: FILTERS.includes(historyFilter as HistoryFilter)
      ? (historyFilter as HistoryFilter)
      : "all",
  };
}

function serialize(state: UrlState): string {
  const params = new URLSearchParams();
  if (state.view !== "live") params.set("view", state.view);
  if (state.replayAt !== null) params.set("at", state.replayAt);
  if (state.activeLines.length > 0) params.set("lines", [...state.activeLines].sort().join(","));
  if (state.selection.kind === "station") params.set("station", state.selection.stationId);
  if (state.selection.kind === "train") {
    if (state.selection.circulation.vehicleId !== "") {
      params.set("train", state.selection.circulation.vehicleId);
    }
    params.set("trip", state.selection.circulation.tripId);
    params.set("sd", state.selection.circulation.serviceDate);
  }
  if (state.historyDate !== null) params.set("hd", state.historyDate);
  if (state.historyLine !== null) params.set("hl", state.historyLine);
  if (state.historyFilter !== "all") params.set("hf", state.historyFilter);
  const query = params.toString();
  return query === "" ? window.location.pathname : `${window.location.pathname}?${query}`;
}

/**
 * Estado navegable en la URL. La navegación entre objetos y vistas usa
 * `pushState` (el botón Atrás del navegador vuelve al contexto anterior); la
 * cámara no entra aquí, para no llenar el historial con movimientos de mapa.
 */
export function useUrlState(): [UrlState, (next: UrlState, push: boolean) => void] {
  const [state, setState] = useState<UrlState>(() =>
    typeof window === "undefined" ? INITIAL_URL_STATE : parse(window.location.search),
  );

  useEffect(() => {
    const onPop = () => setState(parse(window.location.search));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const update = useCallback((next: UrlState, push: boolean) => {
    const url = serialize(next);
    if (url !== `${window.location.pathname}${window.location.search}`) {
      if (push) window.history.pushState(null, "", url);
      else window.history.replaceState(null, "", url);
    }
    setState(next);
  }, []);

  return [state, update];
}

export const __testing = { parse, serialize };
