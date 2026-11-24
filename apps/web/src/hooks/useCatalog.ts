import { useCallback, useMemo, useRef } from "react";
import { fetchCatalog } from "../api/resources";
import type { Catalog } from "../domain/contract";
import { buildCatalogIndex, type CatalogIndex } from "../domain/catalogIndex";
import { useResource, type ResourceState } from "./useResource";

/** Revalidación del catálogo: suficiente para detectar un GTFS nuevo. */
const CATALOG_REVALIDATE_MS = 10 * 60_000;

/**
 * El catálogo se descarga una vez y se revalida con `ETag`; un `304` conserva
 * el índice ya construido (longitudes de arco incluidas) sin recalcular nada.
 */
export function useCatalog(enabled: boolean): ResourceState<Catalog> & { index: CatalogIndex | null } {
  const etagRef = useRef<string | null>(null);

  const fetcher = useCallback(async (signal: AbortSignal) => {
    const response = await fetchCatalog(etagRef.current, { signal });
    if (response.status === 304) return null;
    if (response.etag !== null) etagRef.current = response.etag;
    return response.body;
  }, []);

  const state = useResource<Catalog>(fetcher, {
    intervalMs: CATALOG_REVALIDATE_MS,
    enabled,
    accept: (incoming, current) => current === null || incoming.catalog_version !== current.catalog_version,
  });

  const index = useMemo(
    () => (state.data === null ? null : buildCatalogIndex(state.data)),
    [state.data],
  );

  return { ...state, index };
}
