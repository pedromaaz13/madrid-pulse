import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import fixture from "../__fixtures__/snapshot-map-matched.json";
import type { CatalogIndex } from "../domain/catalogIndex";
import type { HoldReason, RenderingMethod, SnapshotDegradation, SnapshotVehicle } from "../domain/contract";
import { methodStyle } from "../domain/format";
import { DegradationNotice } from "./DegradationNotice";
import { TrainPanel } from "./TrainPanel";

const sample = fixture.vehicles[0] as unknown as SnapshotVehicle;
const index = { patternsById: new Map(), stationsById: new Map() } as unknown as CatalogIndex;
function panel(vehicle: SnapshotVehicle) {
  return renderToStaticMarkup(<TrainPanel index={index} colors={new Map()} circulation={{vehicleId: vehicle.vehicle_id, tripId: vehicle.trip_id, serviceDate: vehicle.service_date}} vehicle={vehicle} nowMs={Date.parse("2026-11-20T14:33:40Z")} following={false} cameraReleased={false} onToggleFollow={vi.fn()} onBackToCamera={vi.fn()} onOpenStation={vi.fn()} onOpenLine={vi.fn()} onBack={null} backLabel={null} />);
}

describe("procedencia y parada", () => {
  it.each([
    ["anchor", "Observada en bruto"], ["extrapolated_from_last_anchor", "Extrapolada"],
    ["interpolated_between_known_anchors", "Interpolada"], ["schedule_only", "Solo horario"],
    ["stale_frozen", "Congelada"], ["unlocated", "Sin ubicar"],
  ])("rotula %s", (method, label) => {
    expect(methodStyle(method as RenderingMethod, "raw").label).toBe(label);
  });
  it("distingue ancla bruta y proyectada", () => {
    expect(methodStyle("anchor", "map_matched").label).toBe("Observada sobre corredor");
  });
  it.each([["operator_stopped_at", "Detenido según el operador"], ["before_first_departure", "Antes de la primera salida"], ["terminal", "En la estación terminal"], ["trip_canceled", "Viaje cancelado"], ["anchor_version_changed", "Cambió la versión del ancla"], ["operator_incoming_at", "Llegando a la parada según el operador"], ["schedule_incoherent", "Horario incoherente"], ["outside_schedule_extent", "Fuera del tramo"], ["schedule_stop_zone", "En zona de parada"], ["horizon_exhausted", "Horizonte de estimación agotado"]])("muestra retención %s", (reason, label) => {
    const envelope = {...sample.rendered.progress_envelope!, speed_mps: 0, hold_reason: reason as HoldReason};
    const markup = panel({...sample, rendered: {...sample.rendered, progress_envelope: envelope}});
    expect(markup).toContain(label);
    expect(markup).toContain("La coordenada no avanza durante la retención");
  });
  it.each(["authorized_envelope_end", "anchor_version_changed", null] as const)("explica congelación %s sin valid_until", basis => {
    const markup = panel({...sample, rendered: {...sample.rendered, rendering_method: "stale_frozen", frozen_basis: basis, valid_until: null, last_confirmed_progress_m: 123}});
    expect(markup).toContain("Posición congelada");
    expect(markup).toContain("123 m sobre el patrón");
    expect(markup).toContain(basis === "authorized_envelope_end" ? "final estimado autorizado" : basis === "anchor_version_changed" ? "ancla disponible" : "Base de congelación desconocida");
  });
  it("rotula cancelación independiente de envolvente", () => {
    expect(panel({...sample, schedule_relationship: "CANCELED"})).toContain("Viaje cancelado según el operador");
  });
  it("muestra estado de parada", () => {
    expect(panel({...sample, rendered: {...sample.rendered, stop_state: {source: "operator", operator_status: "STOPPED_AT", operator_stop_id: "X", observation_observed_at: null, coherent: true}}})).toContain("detenido en la parada");
  });
});

it.each([["stale", "aviso"], ["error", "error"], ["unknown", "vigencia desconocida"]] as const)("GTFS %s procede del snapshot", (status, label) => {
  const item: SnapshotDegradation = {resource: "gtfs", feed_name: null, status, reason: "vigencia del snapshot", last_valid_source_timestamp: null, data_age_s: null, poll_age_s: null};
  const markup = renderToStaticMarkup(<DegradationNotice item={item} />);
  expect(markup).toContain(label);
  expect(markup).not.toContain("último dato válido");
});
