import { describe, expect, it } from "vitest";
import fixture from "../__fixtures__/snapshot-map-matched.json";
import type { Catalog, ProgressEnvelope, Rendered, SnapshotVehicle } from "./contract";
import { buildCatalogIndex } from "./catalogIndex";
import { haversineM } from "./geometry";
import { coordinateAtProgress, frameFor, progressAt } from "./movement";

const index = buildCatalogIndex(fixture.catalog as unknown as Catalog);
const vehicles = fixture.vehicles as unknown as SnapshotVehicle[];

function envelope(partial: Partial<ProgressEnvelope> = {}): ProgressEnvelope {
  return {
    reference_at: "2026-11-20T14:33:00Z",
    progress_m_at_reference: 1000,
    speed_mps: 10,
    max_progress_m: 5000,
    horizon_s: 180,
    dwell_until: null,
    ...partial,
  };
}

describe("progressAt — fórmula publicada por el contrato", () => {
  it("avanza linealmente desde el ancla", () => {
    const e = envelope();
    expect(progressAt(e, Date.parse("2026-11-20T14:33:00Z"))).toBe(1000);
    expect(progressAt(e, Date.parse("2026-11-20T14:33:30Z"))).toBe(1300);
  });

  it("nunca retrocede antes del ancla", () => {
    const e = envelope();
    expect(progressAt(e, Date.parse("2026-11-20T14:32:00Z"))).toBe(1000);
  });

  it("se detiene en max_progress_m", () => {
    const e = envelope({ max_progress_m: 1200 });
    expect(progressAt(e, Date.parse("2026-11-20T14:40:00Z"))).toBe(1200);
  });

  it("respeta la espera en estación: no avanza hasta dwell_until", () => {
    const e = envelope({ dwell_until: "2026-11-20T14:34:00Z" });
    const dwellEnd = Date.parse("2026-11-20T14:34:00Z");
    expect(progressAt(e, Date.parse("2026-11-20T14:33:30Z"))).toBe(1000);
    expect(progressAt(e, dwellEnd)).toBe(1000);
    expect(progressAt(e, dwellEnd + 10_000)).toBe(1100);
  });

  it("speed_mps cero es avance nulo declarado, no dato ausente", () => {
    const e = envelope({ speed_mps: 0, max_progress_m: 1000 });
    expect(progressAt(e, Date.parse("2026-11-20T14:36:00Z"))).toBe(1000);
  });
});

describe("frameFor", () => {
  const rendered = (partial: Partial<Rendered>): Rendered => ({
    rendering_method: "extrapolated_from_last_anchor",
    coordinate_space: "map_matched",
    lat: 40,
    lon: -3.7,
    progress_m: 1000,
    pattern_id: null,
    geometry_version: null,
    geometry_candidate_version: null,
    confidence_index: 0.9,
    calculated_at: "2026-11-20T14:33:00Z",
    display_at: "2026-11-20T14:33:00Z",
    valid_until: "2026-11-20T14:36:00Z",
    last_confirmed_at: "2026-11-20T14:33:00Z",
    anchor_observed_at: "2026-11-20T14:33:00Z",
    anchor_age_s: 0,
    anchor_distance_from_raw_m: 3,
    progress_envelope: null,
    reason: null,
    ...partial,
  });

  it("sin envolvente dibuja exactamente la coordenada publicada", () => {
    const frame = frameFor(rendered({}), null, Date.parse("2026-11-20T14:35:00Z"));
    expect(frame).toEqual({
      coordinate: { lat: 40, lon: -3.7 },
      progressM: 1000,
      source: "published",
    });
  });

  it("sin coordenada publicada no dibuja nada (unlocated)", () => {
    const frame = frameFor(
      rendered({ rendering_method: "unlocated", lat: null, lon: null }),
      null,
      Date.now(),
    );
    expect(frame).toBeNull();
  });

  it("congela al agotarse la vigencia en vez de extrapolar sin límite", () => {
    const axis = [...index.axisByPatternId.values()][0];
    const base = rendered({ progress_envelope: envelope({ max_progress_m: 1e9 }) });
    const atHorizon = frameFor(base, axis, Date.parse("2026-11-20T14:36:00Z"));
    const wayPast = frameFor(base, axis, Date.parse("2026-11-20T15:30:00Z"));
    expect(atHorizon?.progressM).toBe(wayPast?.progressM);
    expect(wayPast?.source).toBe("frozen_horizon");
  });

  it("respeta stale_frozen incluso sin valid_until y con envolvente móvil", () => {
    const axis = [...index.axisByPatternId.values()][0];
    const base = rendered({rendering_method: "stale_frozen", valid_until: null, progress_envelope: envelope()});
    expect(frameFor(base, axis, Date.parse("2026-11-20T15:30:00Z"))).toEqual({
      coordinate: {lat: 40, lon: -3.7}, progressM: 1000, source: "published",
    });
  });
});

describe("coordenada del cliente frente a la que publicó el backend", () => {
  // La prueba que importa: el cliente convierte `progress_m` en coordenada
  // sobre la polilínea real del corredor, y debe caer donde el backend dijo.
  // La fixture es una grabación de la API real de este repositorio.
  it("reproduce rendered.lat/lon de todas las circulaciones map-matcheadas", () => {
    expect(vehicles.length).toBeGreaterThan(0);
    let worstM = 0;
    for (const vehicle of vehicles) {
      const { rendered: r } = vehicle;
      const axis = index.axisByPatternId.get(r.pattern_id as string);
      expect(axis, `sin eje para ${r.pattern_id}`).toBeDefined();
      const client = coordinateAtProgress(axis!, r.progress_m as number);
      const error = haversineM(client, { lat: r.lat as number, lon: r.lon as number });
      worstM = Math.max(worstM, error);
    }
    // Margen por aritmética en coma flotante, no por una aproximación de modelo.
    expect(worstM).toBeLessThan(1);
  });

  it("avanzar sobre la envolvente sigue el corredor, sin saltos entre fotogramas", () => {
    const vehicle = vehicles.find((v) => v.rendered.progress_envelope !== null);
    expect(vehicle).toBeDefined();
    const r = vehicle!.rendered;
    const axis = index.axisByPatternId.get(r.pattern_id as string)!;
    const start = Date.parse(r.progress_envelope!.reference_at);

    const steps: number[] = [];
    let previous = frameFor(r, axis, start)!.coordinate;
    for (let second = 1; second <= 60; second += 1) {
      const next = frameFor(r, axis, start + second * 1000)!.coordinate;
      steps.push(haversineM(previous, next));
      previous = next;
    }
    const max = Math.max(...steps);
    const min = Math.min(...steps);
    // Paso por segundo coherente con la velocidad declarada y sin teletransporte:
    // ningún fotograma salta respecto al resto.
    expect(max).toBeLessThan(r.progress_envelope!.speed_mps * 1.5 + 1);
    expect(max - min).toBeLessThan(2);
  });
});
