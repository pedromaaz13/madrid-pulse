import { useMemo } from "react";

/**
 * Reloj de la aplicación.
 *
 * En `live` es el reloj real. En `replay` avanza desde un instante base
 * elegido por el usuario (`?at=`) al mismo ritmo que el reloj real, de modo
 * que un corte congelado se recorre de forma **repetible**: dos ejecuciones
 * desde el mismo `?at=` ven la misma secuencia.
 *
 * Es un reloj de presentación: no reescribe ninguna edad del contrato. El
 * backend recibe el instante y calcula él las edades y la vigencia.
 */
export interface Clock {
  mode: "live" | "replay";
  /** Instante efectivo en milisegundos epoch. */
  nowMs: () => number;
  /** `null` en live: no se envía `at` y el backend usa su propio reloj. */
  queryAt: () => string | null;
  baseIso: string | null;
}

export function parseReplayBase(raw: string | null): number | null {
  if (raw === null || raw.trim() === "") return null;
  const parsed = Date.parse(raw);
  return Number.isNaN(parsed) ? null : parsed;
}

export function useClock(replayBaseMs: number | null): Clock {
  return useMemo(() => {
    if (replayBaseMs === null) {
      return {
        mode: "live" as const,
        nowMs: () => Date.now(),
        queryAt: () => null,
        baseIso: null,
      };
    }
    // El origen se captura en la primera lectura, no al construir el reloj:
    // así no se llama al reloj del sistema durante el render.
    let startedAtMs: number | null = null;
    const nowMs = () => {
      if (startedAtMs === null) startedAtMs = Date.now();
      return replayBaseMs + (Date.now() - startedAtMs);
    };
    return {
      mode: "replay" as const,
      nowMs,
      queryAt: () => new Date(nowMs()).toISOString(),
      baseIso: new Date(replayBaseMs).toISOString(),
    };
  }, [replayBaseMs]);
}
