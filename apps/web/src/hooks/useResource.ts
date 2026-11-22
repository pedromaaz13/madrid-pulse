import { useCallback, useEffect, useRef, useState } from "react";
import { describeError, isAbort } from "../api/client";

export interface ResourceState<T> {
  /** Último valor bueno. Un fallo posterior **no** lo borra. */
  data: T | null;
  /** Instante (epoch ms) en que se aceptó `data`, solo para diagnóstico. */
  acceptedAtMs: number | null;
  error: string | null;
  loading: boolean;
  /** Fallos consecutivos desde el último éxito. */
  failures: number;
}

export interface ResourceOptions<T> {
  /** Milisegundos entre sondeos; `null` desactiva el sondeo periódico. */
  intervalMs: number | null;
  /** Si `false`, no se sondea (pestaña oculta, recurso no necesario…). */
  enabled: boolean;
  /**
   * Decide si una respuesta debe sustituir a la vigente. Devolver `false`
   * descarta una respuesta que llegó tarde y es más antigua que la actual.
   */
  accept?: (incoming: T, current: T | null) => boolean;
  /** Reinicia el estado cuando cambia (p. ej. otra estación seleccionada). */
  resetKey?: string;
}

const EMPTY: ResourceState<never> = {
  data: null,
  acceptedAtMs: null,
  error: null,
  loading: false,
  failures: 0,
};

/**
 * Un recurso de la API, adquirido de forma independiente de los demás.
 *
 * Reglas que implementa (MP-019/MP-020):
 *
 * - **Una lectura en vuelo por recurso**: si ya hay una petición viva, el
 *   siguiente tick no lanza otra ni la encola.
 * - **Timeout y cancelación** por petición, heredados de `requestJson`.
 * - **Descarte de respuestas antiguas** mediante `accept`.
 * - **Fallo parcial aislado**: el último valor bueno se conserva y se publica
 *   el error junto a él; el recurso que falla no vacía a los demás.
 * - **Una respuesta exitosa no rejuvenece el dato**: `acceptedAtMs` es el
 *   instante de aceptación y nunca se usa como edad del dato de origen, que
 *   siempre procede de los timestamps del propio contrato.
 */
export function useResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T | null>,
  { intervalMs, enabled, accept, resetKey }: ResourceOptions<T>,
): ResourceState<T> & { refresh: () => void } {
  const [state, setState] = useState<ResourceState<T>>(EMPTY);
  const inFlightRef = useRef<AbortController | null>(null);
  const dataRef = useRef<T | null>(null);
  const fetcherRef = useRef(fetcher);
  const acceptRef = useRef(accept);
  fetcherRef.current = fetcher;
  acceptRef.current = accept;

  useEffect(() => {
    dataRef.current = null;
    setState(EMPTY);
  }, [resetKey]);

  const run = useCallback(async () => {
    if (inFlightRef.current !== null) return;
    const controller = new AbortController();
    inFlightRef.current = controller;
    setState((current) => ({ ...current, loading: true }));
    try {
      const value = await fetcherRef.current(controller.signal);
      if (controller.signal.aborted) return;
      // `null` = el recurso sigue siendo el que ya teníamos (304): éxito, sin
      // sustitución, y sin rejuvenecer nada.
      if (value === null) {
        setState((current) => ({ ...current, error: null, failures: 0, loading: false }));
        return;
      }
      const shouldAccept = acceptRef.current?.(value, dataRef.current) ?? true;
      if (!shouldAccept) {
        setState((current) => ({ ...current, error: null, failures: 0, loading: false }));
        return;
      }
      dataRef.current = value;
      setState({
        data: value,
        acceptedAtMs: Date.now(),
        error: null,
        loading: false,
        failures: 0,
      });
    } catch (reason) {
      if (controller.signal.aborted || isAbort(reason)) return;
      setState((current) => ({
        ...current,
        error: describeError(reason),
        failures: current.failures + 1,
        loading: false,
      }));
    } finally {
      if (inFlightRef.current === controller) inFlightRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      inFlightRef.current?.abort();
      inFlightRef.current = null;
      return;
    }
    void run();
    if (intervalMs === null) return;
    const timer = window.setInterval(() => void run(), intervalMs);
    return () => window.clearInterval(timer);
  }, [enabled, intervalMs, run, resetKey]);

  useEffect(
    () => () => {
      inFlightRef.current?.abort();
      inFlightRef.current = null;
    },
    [],
  );

  return { ...state, refresh: run };
}
