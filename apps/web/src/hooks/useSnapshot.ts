import { useCallback } from "react";
import { fetchSnapshot } from "../api/resources";
import type { Snapshot } from "../domain/contract";
import { isNewerRevision } from "../domain/revision";
import { useResource, type ResourceState } from "./useResource";
import type { Clock } from "./useClock";

export const SNAPSHOT_POLL_MS = 10_000;

/**
 * Snapshot operativo: ligero, `no-store` y descartando respuestas antiguas
 * por `revision` (nunca ordenando `snapshot_id`, que es identidad de
 * contenido y el propio payload declara no ordenable).
 */
export function useSnapshot(clock: Clock, enabled: boolean): ResourceState<Snapshot> & { refresh: () => void } {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      const response = await fetchSnapshot(clock.queryAt(), { signal });
      return response.body;
    },
    [clock],
  );

  return useResource<Snapshot>(fetcher, {
    intervalMs: SNAPSHOT_POLL_MS,
    enabled,
    accept: (incoming, current) => isNewerRevision(incoming.revision, current?.revision ?? null),
  });
}
