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

/**
 * Causas por las que el backend declara una ETA no disponible. Son códigos
 * estables del contrato (`apps/api/snapshot.py`): se traducen para el lector
 * y se conserva el código en el detalle técnico, en vez de volcar el
 * identificador crudo en la interfaz.
 */
export const ETA_REASON_LABELS: Record<string, string> = {
  trip_canceled: "Circulación cancelada",
  schedule_time_missing: "El horario no publica hora para esta parada",
  passed_or_skipped_per_operator_next_stop:
    "El operador ya declara una parada posterior: esta llamada quedó atrás u omitida",
  operator_delay_expired: "El retraso del operador es demasiado antiguo para aplicarlo",
};

export function formatEtaReason(reason: string | null): string | null {
  if (reason === null) return null;
  return ETA_REASON_LABELS[reason] ?? reason;
}

export const ETA_METHOD_LABELS: Record<Eta["method"], string> = {
  schedule: "Horario",
  operator_delay_on_schedule: "Horario + retraso del operador",
  unavailable: "No disponible",
};

export function boardEntryNote(entry: BoardEntry): string {
  if (entry.circulation_source === "scheduled_only") return "Solo horario";
  const eta = entry.departure.method === "unavailable" ? entry.arrival : entry.departure;
  if (eta.method === "unavailable") return formatEtaReason(eta.reason) ?? "ETA no disponible";
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

// --- Histórico (MP-021) ---------------------------------------------------

/**
 * Porcentaje **siempre** con su fracción real al lado. Nunca convierte un
 * `null` en `0 %`: sin muestra se dice "sin muestra", porque un 0 % sugiere
 * que se midió y salió cero (docs/DATA_QUALITY.md, DEC-009).
 */
export function formatPctWithDenominator(
  pct: number | null,
  numerator: number | null,
  denominator: number | null,
): string {
  if (denominator === null || denominator === 0) return "sin muestra";
  if (pct === null) return `sin muestra (0/${denominator})`;
  return `${pct.toFixed(1)} % (${numerator ?? 0}/${denominator})`;
}

/** Recuento que puede ser dato ausente. `null` no se muestra como 0. */
export function formatCount(value: number | null): string {
  return value === null ? "sin dato" : String(value);
}

/** Hora GTFS tal cual la publica el feed, incluidas las horas `24:xx`. */
export function formatGtfsTime(value: string | null): string {
  if (value === null || value.trim() === "") return "—";
  const parts = value.split(":");
  return parts.length >= 2 ? `${parts[0]}:${parts[1]}` : value;
}

/** Veredicto de puntualidad de una circulación archivada, con su procedencia. */
export function formatHistoryOnTime(
  onTime: boolean | null,
  delaySeconds: number | null,
  reportedCount: number | null,
): string {
  if (onTime === null || reportedCount === null || reportedCount === 0) {
    return "Sin dato de retraso";
  }
  const minutes = Math.round(Math.abs(delaySeconds ?? 0) / 60);
  const magnitude =
    delaySeconds === null
      ? ""
      : delaySeconds === 0
        ? " (0 min)"
        : delaySeconds > 0
          ? ` (+${minutes} min)`
          : ` (−${minutes} min)`;
  return `${onTime ? "En hora" : "Fuera de umbral"}${magnitude} · ${reportedCount} reporte(s)`;
}

/**
 * Qué es una fila del histórico. El cruce de `scheduled`/`observed` es la
 * información de cobertura del mart: las cuatro combinaciones tienen nombre
 * propio y ninguna se presenta como "sin datos".
 */
export function circulationCoverageLabel(scheduled: boolean, observed: boolean): string {
  if (scheduled && observed) return "Programada y observada";
  if (scheduled && !observed) return "Programada sin observar";
  if (!scheduled && observed) return "Observada fuera de programación";
  return "Sin clasificar";
}

export const HISTORY_FILTER_LABELS: Record<string, string> = {
  all: "Todas",
  observed: "Observadas",
  unobserved: "Huecos de cobertura",
  unscheduled: "Fuera de programación",
};
