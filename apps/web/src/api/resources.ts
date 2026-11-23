import type {
  Catalog,
  Health,
  HistoryCirculationDetail,
  HistoryCirculations,
  HistoryDays,
  HistoryFilter,
  HistoryLines,
  HistoryStations,
  Snapshot,
  StationBoard,
} from "../domain/contract";
import { requestJson, type ApiResponse, type RequestOptions } from "./client";

/**
 * Catálogo cacheable: se revalida con `ETag` y un `304` conserva el que ya
 * está en memoria. Nunca se repite su descarga en cada sondeo.
 */
export function fetchCatalog(
  etag: string | null,
  options: RequestOptions = {},
): Promise<ApiResponse<Catalog>> {
  return requestJson<Catalog>("/catalog", {
    ...options,
    headers: etag === null ? options.headers : { ...options.headers, "If-None-Match": etag },
  });
}

/** Reloj explícito: solo lo admite el backend en modo replay. */
export function fetchSnapshot(at: string | null, options: RequestOptions = {}) {
  const query = at === null ? "" : `?at=${encodeURIComponent(at)}`;
  return requestJson<Snapshot>(`/snapshot${query}`, options);
}

export function fetchHealth(options: RequestOptions = {}) {
  return requestJson<Health>("/health", options);
}

export function fetchStationBoard(
  stationId: string,
  at: string | null,
  limit: number,
  options: RequestOptions = {},
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (at !== null) params.set("at", at);
  return requestJson<StationBoard>(
    `/stations/${encodeURIComponent(stationId)}/board?${params.toString()}`,
    options,
  );
}

// --- Histórico frío (MP-021) ---------------------------------------------
// Recursos nuevos. Un día archivado es inmutable salvo reproceso explícito,
// así que no hay sondeo periódico: se piden al cambiar la fecha/el filtro.

export function fetchHistoryDays(options: RequestOptions = {}) {
  return requestJson<HistoryDays>("/history/days", options);
}

export function fetchHistoryLines(serviceDate: string, options: RequestOptions = {}) {
  const params = new URLSearchParams({ service_date: serviceDate });
  return requestJson<HistoryLines>(`/history/lines?${params.toString()}`, options);
}

export function fetchHistoryStations(
  serviceDate: string,
  limit: number,
  options: RequestOptions = {},
) {
  const params = new URLSearchParams({ service_date: serviceDate, limit: String(limit) });
  return requestJson<HistoryStations>(`/history/stations?${params.toString()}`, options);
}

export function fetchHistoryCirculations(
  serviceDate: string,
  line: string | null,
  only: HistoryFilter,
  limit: number,
  options: RequestOptions = {},
) {
  const params = new URLSearchParams({
    service_date: serviceDate,
    only,
    limit: String(limit),
  });
  if (line !== null) params.set("line", line);
  return requestJson<HistoryCirculations>(`/history/circulations?${params.toString()}`, options);
}

/**
 * Detalle de una circulación histórica por su identidad de Live (vehículo +
 * viaje + día de servicio). `vehicleId` `null` consulta un viaje programado
 * que nunca se observó: la API lo direcciona con `-`.
 */
export function fetchHistoryCirculation(
  serviceDate: string,
  vehicleId: string | null,
  tripId: string,
  options: RequestOptions = {},
) {
  const params = new URLSearchParams({ service_date: serviceDate });
  const vehicle = encodeURIComponent(vehicleId ?? "-");
  return requestJson<HistoryCirculationDetail>(
    `/history/circulations/${vehicle}/${encodeURIComponent(tripId)}?${params.toString()}`,
    options,
  );
}
