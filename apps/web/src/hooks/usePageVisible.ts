import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void): () => void {
  document.addEventListener("visibilitychange", onChange);
  return () => document.removeEventListener("visibilitychange", onChange);
}

/**
 * Visibilidad de la pestaña. La adquisición se pausa al ocultarse y revalida
 * al volver, en vez de seguir sondeando contra una pestaña que nadie mira.
 */
export function usePageVisible(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => !document.hidden,
    () => true,
  );
}
