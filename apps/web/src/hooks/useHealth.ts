import { useCallback } from "react";
import { fetchHealth } from "../api/resources";
import type { Health } from "../domain/contract";
import { useResource, type ResourceState } from "./useResource";

const HEALTH_POLL_MS = 30_000;

/** Salud del backend, independiente del snapshot: uno puede fallar sin el otro. */
export function useHealth(enabled: boolean): ResourceState<Health> {
  const fetcher = useCallback(async (signal: AbortSignal) => {
    const response = await fetchHealth({ signal });
    return response.body;
  }, []);

  return useResource<Health>(fetcher, { intervalMs: HEALTH_POLL_MS, enabled });
}
