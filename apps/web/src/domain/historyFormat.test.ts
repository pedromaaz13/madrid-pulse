import { describe, expect, it } from "vitest";
import {
  circulationCoverageLabel,
  formatCount,
  formatGtfsTime,
  formatHistoryOnTime,
  formatPctWithDenominator,
} from "./format";

describe("formatPctWithDenominator", () => {
  it("nunca presenta una ausencia de muestra como 0 %", () => {
    expect(formatPctWithDenominator(null, 0, 0)).toBe("sin muestra");
    expect(formatPctWithDenominator(null, null, null)).toBe("sin muestra");
  });

  it("dice sin muestra y conserva el denominador cuando el numerador es cero", () => {
    expect(formatPctWithDenominator(null, 0, 72)).toBe("sin muestra (0/72)");
  });

  it("publica el porcentaje siempre junto a su fracción real", () => {
    expect(formatPctWithDenominator(5.56, 4, 72)).toBe("5.6 % (4/72)");
    expect(formatPctWithDenominator(100, 2, 2)).toBe("100.0 % (2/2)");
  });

  it("distingue un 0 % medido de una ausencia de muestra", () => {
    expect(formatPctWithDenominator(0, 0, 35)).toBe("0.0 % (0/35)");
  });
});

describe("formatCount", () => {
  it("un recuento ausente no se muestra como cero", () => {
    expect(formatCount(null)).toBe("sin dato");
    expect(formatCount(0)).toBe("0");
  });
});

describe("formatGtfsTime", () => {
  it("conserva las horas extendidas del feed tal cual", () => {
    expect(formatGtfsTime("24:15:00")).toBe("24:15");
    expect(formatGtfsTime("04:59:00")).toBe("04:59");
  });

  it("declara la ausencia en vez de inventar una hora", () => {
    expect(formatGtfsTime(null)).toBe("—");
    expect(formatGtfsTime("  ")).toBe("—");
  });
});

describe("formatHistoryOnTime", () => {
  it("sin retrasos reportados no emite veredicto", () => {
    expect(formatHistoryOnTime(null, null, 0)).toBe("Sin dato de retraso");
    expect(formatHistoryOnTime(null, null, null)).toBe("Sin dato de retraso");
  });

  it("el veredicto viaja con su magnitud y su número de reportes", () => {
    expect(formatHistoryOnTime(true, 60, 2)).toBe("En hora (+1 min) · 2 reporte(s)");
    expect(formatHistoryOnTime(false, 900, 1)).toBe("Fuera de umbral (+15 min) · 1 reporte(s)");
    expect(formatHistoryOnTime(true, -120, 3)).toBe("En hora (−2 min) · 3 reporte(s)");
  });

  it("un retraso reportado de 0 s es un dato, no una ausencia", () => {
    expect(formatHistoryOnTime(true, 0, 1)).toBe("En hora (0 min) · 1 reporte(s)");
  });
});

describe("circulationCoverageLabel", () => {
  it("nombra las cuatro combinaciones de cobertura sin llamarlas «sin datos»", () => {
    expect(circulationCoverageLabel(true, true)).toBe("Programada y observada");
    expect(circulationCoverageLabel(true, false)).toBe("Programada sin observar");
    expect(circulationCoverageLabel(false, true)).toBe("Observada fuera de programación");
  });
});
