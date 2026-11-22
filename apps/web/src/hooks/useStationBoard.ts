import { useCallback } from "react";
import { fetchStationBoard } from "../api/resources";
import type { StationBoard } from "../domain/contract";
import { isNewerRevision } from "../domain/revision";
import { useResource, type ResourceState } from "./useResource";
import type { Clock } from "./useClock";

const BOARD_POLL_MS = 20_000;
const BOARD_LIMIT = 12;

/**
 * Tablero de estación: se calcula con calendario + horario + RT en el
 * backend, nunca por proximidad geográfica en el cliente. Falla de forma
 * independiente del snapshot y conserva su último resultado bueno.
 */
export function useStationBoard(
  stationId: string | null,
  clock: Clock,
  enabled: boolean,
): ResourceState<StationBoard> {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (stationId === null) return null;
      const response = await fetchStationBoard(stationId, clock.queryAt(), BOARD_LIMIT, { signal });
      return response.body;
    },
    [stationId, clock],
  );

  return useResource<StationBoard>(fetcher, {
    intervalMs: BOARD_POLL_MS,
    enabled: enabled && stationId !== null,
    accept: (incoming, current) =>
      current === null ||
      incoming.station_id !== current.station_id ||
      isNewerRevision(incoming.revision, current.revision),
    resetKey: stationId ?? "none",
  });
}
