const API_ROOT = import.meta.env.VITE_API_ROOT ?? "/api/v1";
const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface RequestOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
  headers?: Record<string, string>;
}

export interface ApiResponse<T> {
  /** `null` solo en un `304`: el recurso cacheado sigue siendo válido. */
  body: T | null;
  status: number;
  etag: string | null;
}

/**
 * Una lectura HTTP con timeout y cancelación propios.
 *
 * El timeout es independiente de la cancelación del llamante para que un
 * recurso colgado no bloquee indefinidamente a los demás: cada recurso se pide
 * por separado y falla por separado (nada de `Promise.all` como único bloque
 * indivisible de éxito).
 */
export async function requestJson<T>(
  path: string,
  { signal, timeoutMs = DEFAULT_TIMEOUT_MS, headers = {} }: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new ApiError(`Tiempo agotado en ${path}`, null)), timeoutMs);
  const onAbort = () => controller.abort(signal?.reason);
  signal?.addEventListener("abort", onAbort, { once: true });

  try {
    const response = await fetch(`${API_ROOT}${path}`, {
      signal: controller.signal,
      headers: { Accept: "application/json", ...headers },
    });
    const etag = response.headers.get("etag");
    if (response.status === 304) return { body: null, status: 304, etag };
    if (!response.ok) throw new ApiError(`La API respondió ${response.status} en ${path}`, response.status);
    return { body: (await response.json()) as T, status: response.status, etag };
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }
}

export function isAbort(reason: unknown): boolean {
  return reason instanceof DOMException && reason.name === "AbortError";
}

export function describeError(reason: unknown): string {
  if (reason instanceof ApiError) return reason.message;
  if (reason instanceof Error) return reason.message;
  return "Error desconocido al consultar la API";
}
