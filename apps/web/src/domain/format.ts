import type {
  BoardEntry,
  Eta,
  RenderingMethod,
  SnapshotDelay,
  SnapshotVehicle,
} from "./contract";

/**
 * Vocabulario de procedencia. El color identifica la línea; la **forma, el
 * contorno y el texto** identifican cómo se obtuvo la posición, para que el
 * símbolo siga siendo legible en escala de grises y con lector de pantalla.
 */
export interface MethodStyle {
  label: string;
  detail: string;
  /** Glifo que acompaña al código de línea sobre el mapa. */
  glyph: string;
  /** Clave de forma/contorno usada por las capas del mapa y la leyenda. */
  shape: "solid" | "ring" | "dashed" | "hollow" | "absent";
}

export const METHOD_STYLES: Record<RenderingMethod, MethodStyle> = {
  anchor: {
    label: "Observada",
    detail: "Coordenada de la última observación publicada por la fuente",
    glyph: "●",
    shape: "solid",
  },
  interpolated_between_known_anchors: {
    label: "Interpolada",
    detail: "Entre dos observaciones reales, con retraso de presentación declarado",
    glyph: "◆",
    shape: "ring",
  },
  extrapolated_from_last_anchor: {
    label: "Proyectada",
    detail: "Avance estimado desde la última observación; no es una lectura GPS",
    glyph: "▸",
    shape: "dashed",
  },
  schedule_only: {
    label: "Solo horario",
    detail: "Derivada del horario, sin observación utilizable",
    glyph: "○",
    shape: "hollow",
  },
  stale_frozen: {
    label: "Congelada",
    detail: "Última posición confirmada; la fuente dejó de actualizar",
    glyph: "◼",
    shape: "ring",
  },
  unlocated: {
    label: "Sin ubicar",
    detail: "La circulación existe pero no hay posición defendible",
    glyph: "—",
    shape: "absent",
  },
};

export const CIRCULATION_LABELS: Record<SnapshotVehicle["circulation_status"], string> = {
  active: "En servicio hoy",
  expired: "Día de servicio anterior",
  unresolved: "No resuelve contra el GTFS cargado",
};

export function formatClock(ms: number): string {
  return new Date(ms).toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Madrid",
  });
}

export function formatClockSeconds(ms: number): string {
  return new Date(ms).toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Europe/Madrid",
  });
}

export function formatIsoClock(iso: string | null): string {
  if (iso === null) return "—";
  const parsed = Date.parse(iso);
  return Number.isNaN(parsed) ? "—" : formatClock(parsed);
}

/** Edad legible. `null` es dato ausente y se dice, nunca se muestra como 0. */
export function formatAge(seconds: number | null): string {
  if (seconds === null) return "edad desconocida";
  const value = Math.max(0, Math.round(seconds));
  if (value < 60) return `hace ${value} s`;
  if (value < 3600) return `hace ${Math.round(value / 60)} min`;
  return `hace ${Math.round(value / 360) / 10} h`;
}

/**
 * Edad recalculada contra el reloj de presentación: la edad avanza aunque el
 * siguiente sondeo falle o no llegue nunca.
 */
export function ageSecondsAt(iso: string | null, nowMs: number): number | null {
  if (iso === null) return null;
  const parsed = Date.parse(iso);
  if (Number.isNaN(parsed)) return null;
  return Math.max(0, (nowMs - parsed) / 1000);
}

export function formatDelay(delay: SnapshotDelay): string {
  if (delay.coverage === "missing" || delay.seconds === null) return "Sin dato de retraso";
  if (delay.expired) {
    return `Retraso caducado (${formatAge(delay.age_s)})`;
  }
  if (delay.seconds === 0) return "En hora";
  const minutes = Math.round(Math.abs(delay.seconds) / 60);
  return delay.seconds > 0 ? `Retraso +${minutes} min` : `Adelanto ${minutes} min`;
}

export function formatEta(eta: Eta): string {
  if (eta.method === "unavailable" || eta.eta_at === null) {
    return eta.scheduled_at === null ? "Sin hora" : formatIsoClock(eta.scheduled_at);
  }
  return formatIsoClock(eta.eta_at);
}

export const ETA_METHOD_LABELS: Record<Eta["method"], string> = {
  schedule: "Horario",
  operator_delay_on_schedule: "Horario + retraso del operador",
  unavailable: "No disponible",
};

export function boardEntryNote(entry: BoardEntry): string {
  if (entry.circulation_source === "scheduled_only") return "Solo horario";
  const eta = entry.departure.method === "unavailable" ? entry.arrival : entry.departure;
  if (eta.method === "unavailable") return eta.reason ?? "ETA no disponible";
  if (eta.delay_seconds === null) return "Sin dato de retraso";
  if (eta.delay_seconds === 0) return "En hora";
  const minutes = Math.round(Math.abs(eta.delay_seconds) / 60);
  return eta.delay_seconds > 0 ? `Retraso +${minutes} min` : `Adelanto ${minutes} min`;
}

/** El destino real del viaje; el GTFS de Renfe deja `headsign` vacío a menudo. */
export function destinationLabel(
  entry: BoardEntry,
  stationName: (stationId: string) => string | null,
): string {
  if (entry.headsign.trim() !== "") return entry.headsign.trim();
  return stationName(entry.destination_stop_id) ?? entry.destination_stop_id;
}
