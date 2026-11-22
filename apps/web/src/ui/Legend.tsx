import { METHOD_STYLES } from "../domain/format";
import type { RenderingMethod } from "../domain/contract";

const ORDER: RenderingMethod[] = [
  "anchor",
  "extrapolated_from_last_anchor",
  "interpolated_between_known_anchors",
  "stale_frozen",
  "schedule_only",
  "unlocated",
];

interface Props {
  present: Set<RenderingMethod>;
}

/**
 * Leyenda de procedencia. Solo lista los métodos realmente presentes en el
 * snapshot vigente: no anuncia categorías que no existen en estos datos.
 */
export function Legend({ present }: Props) {
  const shown = ORDER.filter((method) => present.has(method));
  if (shown.length === 0) return null;
  return (
    <div className="legend" aria-label="Leyenda de procedencia de la posición">
      {shown.map((method) => {
        const style = METHOD_STYLES[method];
        return (
          <span className="legend__item" key={method} title={style.detail}>
            <i className={`legend__mark legend__mark--${style.shape}`} aria-hidden="true" />
            {style.label}
          </span>
        );
      })}
    </div>
  );
}
