import { useCallback } from "react";
import {
  fetchHistoryCirculation,
  fetchHistoryCirculations,
  fetchHistoryDays,
  fetchHistoryLines,
  fetchHistoryStations,
} from "../api/resources";
import type {
  HistoryCirculationDetail,
  HistoryCirculations,
  HistoryDays,
  HistoryFilter,
  HistoryLines,
  HistoryStations,
} from "../domain/contract";
import { useResource, type ResourceState } from "./useResource";

const CIRCULATION_LIMIT = 120;
const STATION_LIMIT = 40;

/**
 * Recursos del histórico frío.
 *
 * A diferencia del snapshot, **no se sondean**: un día ya archivado es
 * inmutable salvo reproceso explícito, así que sondearlo cada 20 s solo
 * gastaría peticiones y podría hacer parecer "vivo" un dato cerrado. Cada hook
 * reutiliza `useResource` para heredar lo que sí aplica: una lectura en vuelo,
 * timeout y cancelación propios, y conservación del último valor bueno cuando
 * una lectura falla.
 */
export function useHistoryDays(enabled: boolean): ResourceState<HistoryDays> {
  const fetcher = useCallback(async (signal: AbortSignal) => {
    const response = await fetchHistoryDays({ signal });
    return response.body;
  }, []);
  return useResource<HistoryDays>(fetcher, { intervalMs: null, enabled });
}

export function useHistoryLines(
  serviceDate: string | null,
  enabled: boolean,
): ResourceState<HistoryLines> {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (serviceDate === null) return null;
      const response = await fetchHistoryLines(serviceDate, { signal });
      return response.body;
    },
    [serviceDate],
  );
  return useResource<HistoryLines>(fetcher, {
    intervalMs: null,
    enabled: enabled && serviceDate !== null,
    resetKey: serviceDate ?? "none",
  });
}

export function useHistoryStations(
  serviceDate: string | null,
  enabled: boolean,
): ResourceState<HistoryStations> {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (serviceDate === null) return null;
      const response = await fetchHistoryStations(serviceDate, STATION_LIMIT, { signal });
      return response.body;
    },
    [serviceDate],
  );
  return useResource<HistoryStations>(fetcher, {
    intervalMs: null,
    enabled: enabled && serviceDate !== null,
    resetKey: serviceDate ?? "none",
  });
}

export function useHistoryCirculations(
  serviceDate: string | null,
  line: string | null,
  only: HistoryFilter,
  enabled: boolean,
): ResourceState<HistoryCirculations> {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (serviceDate === null) return null;
      const response = await fetchHistoryCirculations(
        serviceDate,
        line,
        only,
        CIRCULATION_LIMIT,
        { signal },
      );
      return response.body;
    },
    [serviceDate, line, only],
  );
  return useResource<HistoryCirculations>(fetcher, {
    intervalMs: null,
    enabled: enabled && serviceDate !== null,
    resetKey: `${serviceDate ?? "none"}|${line ?? "all"}|${only}`,
  });
}

/** Detalle por identidad de Live: vehículo + viaje + día de servicio. */
export function useHistoryCirculation(
  serviceDate: string | null,
  vehicleId: string | null,
  tripId: string | null,
  enabled: boolean,
): ResourceState<HistoryCirculationDetail> {
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (serviceDate === null || tripId === null) return null;
      const response = await fetchHistoryCirculation(serviceDate, vehicleId, tripId, { signal });
      return response.body;
    },
    [serviceDate, vehicleId, tripId],
  );
  return useResource<HistoryCirculationDetail>(fetcher, {
    intervalMs: null,
    enabled: enabled && serviceDate !== null && tripId !== null,
    resetKey: `${serviceDate ?? "none"}|${vehicleId ?? "-"}|${tripId ?? "none"}`,
  });
}
