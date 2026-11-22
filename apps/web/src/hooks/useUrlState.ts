import { useCallback, useEffect, useState } from "react";
import type { Selection } from "../domain/identity";

export interface UrlState {
  selection: Selection;
  activeLines: string[];
  replayAt: string | null;
}

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
  // campos no se reconstruye una identidad a medias.
  if (vehicle !== null && trip !== null && serviceDate !== null) {
    selection = { kind: "train", circulation: { vehicleId: vehicle, tripId: trip, serviceDate } };
  } else if (station !== null && station !== "") {
    selection = { kind: "station", stationId: station };
  }

  return { selection, activeLines: lines, replayAt: params.get("at") };
}

function serialize(state: UrlState): string {
  const params = new URLSearchParams();
  if (state.replayAt !== null) params.set("at", state.replayAt);
  if (state.activeLines.length > 0) params.set("lines", [...state.activeLines].sort().join(","));
  if (state.selection.kind === "station") params.set("station", state.selection.stationId);
  if (state.selection.kind === "train") {
    params.set("train", state.selection.circulation.vehicleId);
    params.set("trip", state.selection.circulation.tripId);
    params.set("sd", state.selection.circulation.serviceDate);
  }
  const query = params.toString();
  return query === "" ? window.location.pathname : `${window.location.pathname}?${query}`;
}

/**
 * Estado navegable en la URL. La navegación entre objetos usa `pushState`
 * (el botón Atrás del navegador vuelve al contexto anterior); la cámara no
 * entra aquí, para no llenar el historial con movimientos de mapa.
 */
export function useUrlState(): [UrlState, (next: UrlState, push: boolean) => void] {
  const [state, setState] = useState<UrlState>(() =>
    typeof window === "undefined" ? { selection: { kind: "none" }, activeLines: [], replayAt: null } : parse(window.location.search),
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
