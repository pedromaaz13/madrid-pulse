/**
 * Paleta de líneas.
 *
 * El color identifica **la línea** y nada más: la procedencia de la posición
 * se expresa con forma, contorno y texto, para que el símbolo siga siendo
 * legible en escala de grises.
 *
 * Asignación determinista por `line_id` sobre una paleta fija, sin
 * identificadores de línea incrustados en la lógica (ADR-0011): la misma
 * línea recibe siempre el mismo color y una línea nueva del catálogo recibe
 * uno sin tocar código.
 *
 * Limitación declarada: el GTFS oficial publica `route_color` real de Renfe
 * (p. ej. `75B6E0` para C1), pero el contrato `/api/v1/catalog` de MP-019 no
 * expone ese campo y MP-020 no reescribe el contrato. Esta paleta es por
 * tanto una elección de presentación del cliente, **no** el color corporativo
 * del operador, y así se documenta en `apps/web/README.md`.
 */
const PALETTE = [
  "#ffc95b",
  "#6de3d0",
  "#8fb8ff",
  "#f2886f",
  "#b7e06a",
  "#d9a3f0",
  "#5fd0f5",
  "#f6d56a",
  "#9ad4a8",
  "#ff9fc0",
  "#c8b6ff",
  "#78d6b0",
];

const FALLBACK = "#c3d0cd";

function hash(value: string): number {
  let result = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    result ^= value.charCodeAt(index);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
}

/**
 * Colores estables por línea. Se resuelven colisiones recorriendo la paleta,
 * de modo que dos líneas del mismo catálogo nunca comparten color mientras
 * haya entradas libres.
 */
export function buildLineColors(lineIds: string[]): Map<string, string> {
  const colors = new Map<string, string>();
  const used = new Set<string>();
  for (const lineId of [...lineIds].sort()) {
    const start = hash(lineId) % PALETTE.length;
    let chosen: string | null = null;
    for (let offset = 0; offset < PALETTE.length; offset += 1) {
      const candidate = PALETTE[(start + offset) % PALETTE.length];
      if (!used.has(candidate)) {
        chosen = candidate;
        break;
      }
    }
    const color = chosen ?? FALLBACK;
    used.add(color);
    colors.set(lineId, color);
  }
  return colors;
}

export function lineColor(colors: Map<string, string>, lineId: string | null): string {
  if (lineId === null) return FALLBACK;
  return colors.get(lineId) ?? FALLBACK;
}

export const UNRESOLVED_COLOR = FALLBACK;
