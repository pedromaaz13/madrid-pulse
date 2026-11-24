import { describe, expect, it } from "vitest";
import { METHOD_STYLES } from "../../apps/web/src/domain/format";
import type { RenderingMethod } from "../../apps/web/src/domain/contract";

/**
 * AUD-04: ¿distingue el mapa las cinco categorias de posicion?
 * El unico canal que las capas de MapLibre usan es `shape`
 * (apps/web/src/map/layers.ts:29-80: STROKE_COLOR, STROKE_WIDTH, CORE_RADIUS
 * son todas `["match", ["get", "shape"], ...]`), y la leyenda usa
 * `legend__mark--${shape}` (apps/web/src/ui/Legend.tsx:30).
 */
describe("canales visuales por metodo de presentacion", () => {
  it("imprime el mapeo metodo -> forma/glifo/etiqueta", () => {
    const rows = (Object.keys(METHOD_STYLES) as RenderingMethod[]).map((m) => ({
      method: m,
      shape: METHOD_STYLES[m].shape,
      glyph: METHOD_STYLES[m].glyph,
      label: METHOD_STYLES[m].label,
    }));
    // eslint-disable-next-line no-console
    console.table(rows);
    const byShape = new Map<string, RenderingMethod[]>();
    for (const r of rows) {
      byShape.set(r.shape, [...(byShape.get(r.shape) ?? []), r.method]);
    }
    const collisions = [...byShape.entries()].filter(([, v]) => v.length > 1);
    // eslint-disable-next-line no-console
    console.log("formas compartidas por >1 metodo:", JSON.stringify(collisions));
    expect(rows).toHaveLength(6);
  });

  it("interpolated y stale_frozen comparten la MISMA forma", () => {
    expect(METHOD_STYLES.interpolated_between_known_anchors.shape).toBe(
      METHOD_STYLES.stale_frozen.shape,
    );
  });

  it("`anchor` no distingue coordenada bruta de proyeccion sobre via", () => {
    // `anchor` lo emiten tanto render_from_movement (coordinate_space=map_matched)
    // como render_raw_anchor (coordinate_space=raw): una sola entrada de estilo.
    expect(METHOD_STYLES.anchor.detail).toBe(
      "Coordenada de la última observación publicada por la fuente",
    );
  });
});
