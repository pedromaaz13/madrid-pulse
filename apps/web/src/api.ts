import type { Health, Line, Vehicle } from "./types";

const API_ROOT = import.meta.env.VITE_API_ROOT ?? "/api/v1";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`La API respondió ${response.status} en ${path}`);
  }
  return response.json() as Promise<T>;
}

export function fetchLines(signal?: AbortSignal): Promise<Line[]> {
  return getJson<Line[]>("/lines", signal);
}

export function fetchVehicles(signal?: AbortSignal): Promise<Vehicle[]> {
  return getJson<Vehicle[]>("/live/vehicles", signal);
}

export function fetchHealth(signal?: AbortSignal): Promise<Health> {
  return getJson<Health>("/health", signal);
}

export async function fetchDashboard(signal?: AbortSignal) {
  const [lines, vehicles, health] = await Promise.all([
    fetchLines(signal),
    fetchVehicles(signal),
    fetchHealth(signal),
  ]);
  return { lines, vehicles, health };
}
