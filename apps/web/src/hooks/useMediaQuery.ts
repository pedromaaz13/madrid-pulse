import { useCallback, useMemo, useSyncExternalStore } from "react";

/**
 * Media query como fuente externa (`useSyncExternalStore`): sin estado
 * duplicado en React ni `setState` dentro de un efecto.
 */
export function useMediaQuery(query: string): boolean {
  const media = useMemo(
    () =>
      typeof window === "undefined" || typeof window.matchMedia !== "function"
        ? null
        : window.matchMedia(query),
    [query],
  );

  const subscribe = useCallback(
    (onChange: () => void) => {
      if (media === null) return () => {};
      media.addEventListener("change", onChange);
      return () => media.removeEventListener("change", onChange);
    },
    [media],
  );

  return useSyncExternalStore(
    subscribe,
    () => media?.matches ?? false,
    () => false,
  );
}
