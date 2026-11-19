import { describe, expect, it } from "vitest";
import { formatAge, formatDelay, MODE_LABELS } from "./format";
import type { Vehicle } from "./types";

const vehicle = {
  delay: { seconds: null, coverage: "missing" },
} as Vehicle;

describe("transparencia de calidad", () => {
  it("mantiene cuatro etiquetas de posición distintas", () => {
    expect(Object.keys(MODE_LABELS)).toEqual(["observed", "estimated", "stale", "scheduled"]);
    expect(new Set(Object.values(MODE_LABELS).map((item) => item.label)).size).toBe(4);
  });

  it("no convierte la ausencia de retraso en cero", () => {
    expect(formatDelay(vehicle)).toBe("Sin dato de retraso");
  });

  it("formatea edad sin inventarla cuando falta", () => {
    expect(formatAge(null)).toBe("edad desconocida");
    expect(formatAge(42)).toBe("hace 42 s");
  });
});
