import type { CatalogIndex } from "../domain/catalogIndex";
import { lineColor } from "../domain/palette";

interface Props {
  index: CatalogIndex | null;
  colors: Map<string, string>;
  activeLines: Set<string>;
  counts: Map<string, number>;
  onToggle: (lineId: string) => void;
  onClear: () => void;
}

/**
 * Multiselección de líneas. Los contadores tienen el **mismo ámbito** que el
 * mapa: cuentan las circulaciones del snapshot vigente, no un total genérico,
 * y una línea sin circulaciones sigue presente y seleccionable.
 */
export function LineFilter({ index, colors, activeLines, counts, onToggle, onClear }: Props) {
  if (index === null) return null;
  const lines = [...index.catalog.lines].sort((a, b) => a.line_id.localeCompare(b.line_id, "es"));

  return (
    <fieldset className="line-filter">
      <legend className="label">Líneas · {index.catalog.operator}</legend>
      <div className="line-filter__chips">
        <button
          type="button"
          className={activeLines.size === 0 ? "line-chip is-active" : "line-chip"}
          aria-pressed={activeLines.size === 0}
          onClick={onClear}
        >
          Todas
        </button>
        {lines.map((line) => {
          const active = activeLines.has(line.line_id);
          const count = counts.get(line.line_id) ?? 0;
          return (
            <button
              key={line.line_id}
              type="button"
              className={active ? "line-chip is-active" : "line-chip"}
              aria-pressed={active}
              onClick={() => onToggle(line.line_id)}
              title={`${line.line_id}: ${count} circulaciones en este snapshot`}
            >
              <span
                className="line-chip__swatch"
                style={{ background: lineColor(colors, line.line_id) }}
                aria-hidden="true"
              />
              {line.line_id}
              <small>{count}</small>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
