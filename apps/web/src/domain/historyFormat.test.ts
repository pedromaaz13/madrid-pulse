import { describe, expect, it } from "vitest";
import {
  circulationCoverageLabel,
  formatCount,
  formatGtfsTime,
  formatHistoryOnTime,
  formatPctWithDenominator,
  COVERAGE_DETAILS,
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
  it("nombra las cinco categorías sin llamar «sin datos» a ninguna", () => {
    expect(circulationCoverageLabel("observed")).toBe("Programada y observada");
    expect(circulationCoverageLabel("unobserved")).toBe("Programada sin ninguna señal");
    expect(circulationCoverageLabel("unscheduled")).toBe("Observada fuera de programación");
    expect(circulationCoverageLabel("operator_only")).toBe("Sin posición, con parte del operador");
  });

  it("una circulación anulada no se presenta como hueco de cobertura", () => {
    // El tren no circuló y el operador lo dijo: llamarlo hueco culparía al
    // colector de un fallo de captura que no existió.
    expect(circulationCoverageLabel("canceled")).toBe("Anulada por el operador");
    expect(circulationCoverageLabel("canceled")).not.toContain("hueco");
    expect(COVERAGE_DETAILS.canceled).toContain("no circuló");
  });
});
