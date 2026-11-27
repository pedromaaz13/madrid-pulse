import type { Coordinate, ProgressEnvelope, Rendered, SnapshotVehicle } from "./contract";
import { pointAtArcLength, type PolylineIndex } from "./geometry";

/**
 * Evaluación de la `ProgressEnvelope` publicada por MP-019. La fórmula está
 * fijada por el contrato y **no se reinventa aquí**:
 *
 * ```text
 * t0 = dwell_until or reference_at
 * progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0),
 *                   max_progress_m)
 * ```
 *
 * `speed_mps === 0` es avance nulo declarado por el horario, no dato ausente.
 */
export function progressAt(envelope: ProgressEnvelope, atMs: number): number {
  const movingFromMs = Date.parse(envelope.dwell_until ?? envelope.reference_at);
  const elapsedS = Math.max(0, (atMs - movingFromMs) / 1000);
  return Math.min(
    envelope.progress_m_at_reference + envelope.speed_mps * elapsedS,
    envelope.max_progress_m,
  );
}

export function phase(envelope: ProgressEnvelope, atMs: number): string {
  const start = Date.parse(envelope.dwell_until ?? envelope.reference_at);
  if (envelope.speed_mps === 0 || atMs < start) return `hold:${envelope.hold_reason ?? "null"}`;
  if (envelope.cap_reached_at && atMs >= Date.parse(envelope.cap_reached_at)) {
    return `cap:${envelope.cap_kind}`;
  }
  return "moving";
}

/**
 * Eje de progreso de un patrón: convierte el progreso **dirigido** del
 * contrato en longitud de arco **física** sobre el corredor.
 *
 * Es la misma conversión que `packages.movement.schedule.TripSchedule`:
 * `physical_arc = forward ? progress_m : corridor_length_m - progress_m`,
 * con `forward` derivado del orden real de las paradas del patrón sobre el
 * corredor (`distance_along_m` crece o decrece con `stop_sequence`) y
 * `corridor_length_m` igual a la longitud publicada de la geometría.
 */
export interface PatternAxis {
  patternId: string;
  geometryVersion: string;
  forward: boolean;
  corridorLengthM: number;
  polyline: PolylineIndex;
}

export function physicalArcM(axis: PatternAxis, progressM: number): number {
  return axis.forward ? progressM : axis.corridorLengthM - progressM;
}

export function coordinateAtProgress(axis: PatternAxis, progressM: number): Coordinate {
  return pointAtArcLength(axis.polyline, physicalArcM(axis, progressM));
}

/** Cómo se obtuvo la coordenada que se está dibujando en este fotograma. */
export type FrameSource =
  /** Avance del cliente sobre la envolvente, dentro de su horizonte. */
  | "envelope"
  /** Coordenada publicada por el backend, sin avance del cliente. */
  | "published"
  /** Horizonte agotado: congelado en la última coordenada autorizada. */
  | "frozen_horizon";

export interface Frame {
  coordinate: Coordinate;
  progressM: number | null;
  source: FrameSource;
}

/**
 * Coordenada a dibujar en el instante `atMs`.
 *
 * Una posición `stale_frozen` se conserva tal como la publicó el backend.
 * En los demás casos el cliente solo avanza cuando publicó una envolvente y un
 * patrón con corredor, y únicamente hasta `rendered.valid_until`. Agotado el
 * horizonte se congela: nunca se extrapola más allá de lo que el contrato
 * autoriza, y jamás se interpola lat/lon en recta entre dos puntos.
 */
export function frameFor(
  rendered: Rendered,
  axis: PatternAxis | null,
  atMs: number,
): Frame | null {
  const envelope = rendered.progress_envelope;
  if (rendered.rendering_method !== "stale_frozen" && envelope !== null && axis !== null) {
    const validUntilMs =
      rendered.valid_until === null ? Number.POSITIVE_INFINITY : Date.parse(rendered.valid_until);
    const clampedMs = Math.min(atMs, validUntilMs);
    const progressM = progressAt(envelope, clampedMs);
    return {
      coordinate: coordinateAtProgress(axis, progressM),
      progressM,
      source: atMs > validUntilMs ? "frozen_horizon" : "envelope",
    };
  }
  if (rendered.lat === null || rendered.lon === null) return null;
  return {
    coordinate: { lat: rendered.lat, lon: rendered.lon },
    progressM: rendered.progress_m,
    source: "published",
  };
}

/**
 * Última lectura realmente confirmada, para dibujarla junto al símbolo cuando
 * la posición mostrada ya no es una observación (`extrapolated_from_last_anchor`
 * o `stale_frozen`). Es la proyección del ancla cuando existe; si no hubo
 * proyección, el punto bruto tal cual lo publicó la fuente.
 */
export function lastConfirmedCoordinate(vehicle: SnapshotVehicle): Coordinate | null {
  if (vehicle.map_matched !== null) {
    return { lat: vehicle.map_matched.lat, lon: vehicle.map_matched.lon };
  }
  if (vehicle.raw.lat !== null && vehicle.raw.lon !== null) {
    return { lat: vehicle.raw.lat, lon: vehicle.raw.lon };
  }
  return null;
}
