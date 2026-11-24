import { describe, expect, it } from "vitest";
import type { SnapshotDelay } from "./contract";
import { ageSecondsAt, formatAge, formatDelay, formatEtaReason, METHOD_STYLES } from "./format";

function delay(partial: Partial<SnapshotDelay> = {}): SnapshotDelay {
  return {
    seconds: 120,
    coverage: "reported",
    observed_at: "2026-11-20T14:33:00Z",
    age_s: 20,
    source: "operator_trip_update",
    expired: false,
    approximation: null,
    ...partial,
  };
}

describe("formatAge", () => {
  it("dice que la edad es desconocida en vez de mostrar cero", () => {
    expect(formatAge(null)).toBe("edad desconocida");
  });

  it("no presenta edades negativas", () => {
    expect(formatAge(-5)).toBe("hace 0 s");
  });

  it("escala a minutos y horas", () => {
    expect(formatAge(45)).toBe("hace 45 s");
    expect(formatAge(180)).toBe("hace 3 min");
    expect(formatAge(7200)).toBe("hace 2 h");
  });
});

describe("ageSecondsAt", () => {
  it("avanza con el reloj de presentación, no con el sondeo", () => {
    const observed = "2026-11-20T14:33:00Z";
    const a = ageSecondsAt(observed, Date.parse("2026-11-20T14:33:30Z"));
    const b = ageSecondsAt(observed, Date.parse("2026-11-20T14:35:00Z"));
    expect(a).toBe(30);
    expect(b).toBe(120);
  });

  it("devuelve null cuando no hay instante", () => {
    expect(ageSecondsAt(null, Date.now())).toBeNull();
  });
});

describe("formatDelay", () => {
  it("distingue dato ausente de en hora", () => {
    expect(formatDelay(delay({ coverage: "missing", seconds: null }))).toBe("Sin dato de retraso");
    expect(formatDelay(delay({ seconds: 0 }))).toBe("En hora");
  });

  it("declara un retraso caducado en vez de aplicarlo", () => {
    expect(formatDelay(delay({ expired: true, age_s: 900 }))).toContain("caducado");
  });

  it("distingue retraso de adelanto", () => {
    expect(formatDelay(delay({ seconds: 300 }))).toBe("Retraso +5 min");
    expect(formatDelay(delay({ seconds: -120 }))).toBe("Adelanto 2 min");
  });
});

describe("formatEtaReason", () => {
  it("traduce los códigos del contrato", () => {
    expect(formatEtaReason("trip_canceled")).toBe("Circulación cancelada");
    expect(formatEtaReason("operator_delay_expired")).toContain("demasiado antiguo");
  });

  it("deja pasar un código desconocido sin romperse", () => {
    expect(formatEtaReason("codigo_nuevo_del_backend")).toBe("codigo_nuevo_del_backend");
    expect(formatEtaReason(null)).toBeNull();
  });
});

describe("METHOD_STYLES", () => {
  it("cubre los seis métodos del anexo con forma propia", () => {
    const methods = Object.keys(METHOD_STYLES);
    expect(methods).toHaveLength(6);
    // La procedencia se distingue sin depender del color.
    expect(new Set(methods.map((m) => METHOD_STYLES[m as keyof typeof METHOD_STYLES].label)).size).toBe(6);
  });
});
