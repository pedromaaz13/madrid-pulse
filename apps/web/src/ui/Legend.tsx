import type { CoordinateSpace, RenderingMethod } from "../domain/contract";
import { methodStyle } from "../domain/format";

export interface ProvenancePair { method: RenderingMethod; space: CoordinateSpace | null }

/** Cada entrada describe un par realmente presente en el snapshot. */
export function Legend({ present }: { present: ProvenancePair[] }) {
  if (present.length === 0) return null;
  const unique = new Map<string, ProvenancePair>();
  for (const pair of present) {
    const style = methodStyle(pair.method, pair.space);
    unique.set(`${pair.method}:${style.label}:${style.shape}`, pair);
  }
  return <div className="legend" aria-label="Leyenda de procedencia de la posición">
    {[...unique.values()].map(({ method, space }) => {
      const style = methodStyle(method, space);
      return <span className="legend__item" key={`${method}:${space ?? "none"}`} title={style.detail}>
        <i className={`legend__mark legend__mark--${style.shape}`} aria-hidden="true" /><span aria-hidden="true">{style.glyph}</span> {style.label}
      </span>;
    })}
  </div>;
}
