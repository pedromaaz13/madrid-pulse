import type { Snapshot, SnapshotVehicle } from "./contract";
import { degradationText, formatAge, formatDelay } from "./format";
import { circulationOf, vehicleKey, type CirculationId } from "./identity";

export interface NewsEvent {
  id: string;
  text: string;
  circulation: CirculationId | null;
}

/**
 * Novedades derivadas de datos reales: degradación por recurso y cambios
 * acreditados entre dos snapshots. No se inventa ningún aviso y los avisos
 * repetidos no se vuelven a publicar — el `id` es su identidad, de modo que
 * un aviso idéntico al anterior no cuenta como novedad.
 */
export function deriveNews(current: Snapshot, previous: Snapshot | null): NewsEvent[] {
  const events: NewsEvent[] = [];

  for (const degradation of current.degraded) {
    events.push({
      id: `degraded:${degradation.resource}:${degradation.status}:${degradation.last_valid_source_timestamp ?? "none"}`,
      text:
        degradationText(degradation) +
        (degradation.data_age_s !== null ? ` (${formatAge(degradation.data_age_s)})` : ""),
      circulation: null,
    });
  }

  if (previous !== null) {
    const before = new Map<string, SnapshotVehicle>(
      previous.vehicles.map((vehicle) => [vehicleKey(vehicle), vehicle]),
    );
    for (const vehicle of current.vehicles) {
      const key = vehicleKey(vehicle);
      const old = before.get(key);
      if (old === undefined) {
        events.push({
          id: `new:${key}:${vehicle.timestamps.gps_observed_at}`,
          text: `${vehicle.line ?? "Sin línea"} · nueva circulación ${vehicle.vehicle_id} en el snapshot.`,
          circulation: circulationOf(vehicle),
        });
        continue;
      }
      if (
        old.delay.seconds !== vehicle.delay.seconds ||
        old.delay.coverage !== vehicle.delay.coverage
      ) {
        events.push({
          id: `delay:${key}:${vehicle.delay.seconds ?? "null"}:${vehicle.delay.observed_at ?? "none"}`,
          text: `${vehicle.line ?? "Sin línea"} · ${vehicle.vehicle_id}: ${formatDelay(vehicle.delay).toLowerCase()}.`,
          circulation: circulationOf(vehicle),
        });
      }
      if (
        old.rendered.rendering_method !== vehicle.rendered.rendering_method &&
        (vehicle.rendered.rendering_method === "stale_frozen" ||
          vehicle.rendered.rendering_method === "unlocated")
      ) {
        events.push({
          id: `frozen:${key}:${vehicle.rendered.rendering_method}:${vehicle.rendered.last_confirmed_at ?? "none"}`,
          text: `${vehicle.line ?? "Sin línea"} · ${vehicle.vehicle_id} dejó de actualizar: última posición ${formatAge(vehicle.rendered.anchor_age_s)}.`,
          circulation: circulationOf(vehicle),
        });
      }
    }
  }

  return events;
}

/** Fusiona novedades nuevas conservando las vigentes, sin duplicar por `id`. */
export function mergeNews(previous: NewsEvent[], incoming: NewsEvent[], limit = 12): NewsEvent[] {
  const seen = new Set(incoming.map((event) => event.id));
  // Las degradaciones reflejan el snapshot actual; no perpetuar avisos
  // caducados cuando un recurso se recupera o cambia de estado.
  const kept = previous.filter((event) => !event.id.startsWith("degraded:") && !seen.has(event.id));
  return [...incoming, ...kept].slice(0, limit);
}
