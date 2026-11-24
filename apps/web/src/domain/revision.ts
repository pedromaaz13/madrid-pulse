import type { SnapshotRevision } from "./contract";

/**
 * Regla de orden del contrato de MP-019 para descartar respuestas antiguas.
 *
 * `snapshot_id` es identidad de contenido y **nunca** se ordena. Solo se
 * comparan revisiones dentro del mismo `scope`: si el ámbito cambia (otra
 * base, reinicio con identificador distinto) no hay orden posible y se trata
 * como discontinuidad, aceptando la respuesta nueva.
 *
 * Dentro del ámbito: `sequence`, y con `sequence` igual, `generated_at`; con
 * ambos iguales, `tiebreak` solo decide que son distintas, no cuál es mejor,
 * así que una respuesta con el mismo contenido no sustituye a la anterior.
 */
export function isNewerRevision(
  candidate: SnapshotRevision,
  current: SnapshotRevision | null,
): boolean {
  if (current === null) return true;
  if (candidate.scope !== current.scope) return true;

  if (candidate.sequence !== null && current.sequence !== null) {
    if (candidate.sequence !== current.sequence) return candidate.sequence > current.sequence;
  } else if (candidate.sequence !== current.sequence) {
    // Un ámbito que deja de publicar secuencia (o empieza a hacerlo) es un
    // cambio de régimen: se decide por tiempo, no se inventa una comparación.
    return Date.parse(candidate.generated_at) >= Date.parse(current.generated_at);
  }

  const candidateAt = Date.parse(candidate.generated_at);
  const currentAt = Date.parse(current.generated_at);
  if (candidateAt !== currentAt) return candidateAt > currentAt;
  return false;
}
