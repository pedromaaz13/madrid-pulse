// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { __testing } from "./useUrlState";

const { parse, serialize } = __testing;

describe("estado de URL del histórico (MP-021)", () => {
  it("la vista por omisión es Live y no aparece en la URL", () => {
    expect(parse("").view).toBe("live");
    expect(serialize(parse(""))).not.toContain("view=");
  });

  it("una vista desconocida cae a Live en vez de dejar la pantalla en blanco", () => {
    expect(parse("?view=sql-lab").view).toBe("live");
  });

  it("restaura vista, día, línea y filtro del histórico", () => {
    const state = parse("?view=history&hd=2026-11-20&hl=C5&hf=unobserved");
    expect(state.view).toBe("history");
    expect(state.historyDate).toBe("2026-11-20");
    expect(state.historyLine).toBe("C5");
    expect(state.historyFilter).toBe("unobserved");
  });

  it("descarta un día de servicio que no es una fecha ISO", () => {
    expect(parse("?view=history&hd=ayer").historyDate).toBeNull();
  });

  it("descarta un filtro de cobertura desconocido", () => {
    expect(parse("?view=history&hf=inventado").historyFilter).toBe("all");
  });

  it("acepta las cinco categorías reales de cobertura del mart", () => {
    // Regresión: la lista en tiempo de ejecución se quedó corta al añadir
    // `canceled`/`operator_only` y el enlace caía silenciosamente a «Todas»,
    // mostrando 120 circulaciones donde se habían pedido 3 anuladas.
    for (const filter of ["observed", "unobserved", "canceled", "operator_only", "unscheduled"]) {
      expect(parse(`?view=history&hf=${filter}`).historyFilter).toBe(filter);
      expect(serialize(parse(`?view=history&hf=${filter}`))).toContain(`hf=${filter}`);
    }
  });

  it("la identidad de circulación es la misma en Live y en History", () => {
    const live = parse("?train=19656&trip=1023V19656C5&sd=2026-11-20");
    const history = parse("?view=history&train=19656&trip=1023V19656C5&sd=2026-11-20");
    expect(live.selection).toEqual(history.selection);
    expect(history.selection).toEqual({
      kind: "train",
      circulation: { vehicleId: "19656", tripId: "1023V19656C5", serviceDate: "2026-11-20" },
    });
  });

  it("una circulación programada sin observar se restaura sin fabricar vehículo", () => {
    const state = parse("?view=history&trip=1023V19502C5&sd=2026-11-20");
    expect(state.selection).toEqual({
      kind: "train",
      circulation: { vehicleId: "", tripId: "1023V19502C5", serviceDate: "2026-11-20" },
    });
    // Y al volver a serializar no inventa un `train=`:
    const url = serialize(state);
    expect(url).not.toContain("train=");
    expect(url).toContain("trip=1023V19502C5");
    expect(url).toContain("sd=2026-11-20");
  });

  it("serializa y vuelve a parsear sin perder nada (ida y vuelta)", () => {
    const search = "?view=explore&hd=2026-11-19&hl=C4a&hf=observed&lines=C1%2CC5&at=2026-11-20T14%3A33%3A00Z";
    const parsed = parse(search);
    const again = parse(serialize(parsed).replace(/^[^?]*/, ""));
    expect(again).toEqual(parsed);
  });
});
