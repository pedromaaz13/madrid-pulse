import type { Catalog, Health, Snapshot, StationBoard } from "../domain/contract";
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
