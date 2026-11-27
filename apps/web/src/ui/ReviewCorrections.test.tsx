import schema from "../../../api/openapi.json";
import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import fixture from "../__fixtures__/snapshot-map-matched.json";
import { buildCatalogIndex } from "../domain/catalogIndex";
import type { Catalog, SnapshotVehicle } from "../domain/contract";
import { degradationText, HOLD_LABELS, methodStyle } from "../domain/format";
import { mergeNews } from "../domain/news";
import { vehicleFrames } from "../map/features";
import { Legend } from "./Legend";

it("traduce exhaustivamente el enum del contrato OpenAPI", () => {
  const reasons = schema.components.schemas.ProgressEnvelopeOut.properties.hold_reason.anyOf[0].enum!;
  expect(Object.keys(HOLD_LABELS).sort()).toEqual([...reasons].sort());
  for (const reason of reasons) expect(HOLD_LABELS[reason as keyof typeof HOLD_LABELS]).not.toMatch(/^[a-z]+(?:_[a-z]+)+$/);
});

it("traduce identificadores de fuentes y retira avisos de degradación recuperados", () => {
  const text = degradationText({resource: "delays_and_eta", feed_name: "trip_updates", status: "stale", reason: "feed trip_updates en estado stale", last_valid_source_timestamp: null, data_age_s: null, poll_age_s: null});
  expect(text).toContain("Retrasos y próximas llegadas");
  expect(text).toContain("fuente de actualizaciones de viajes en estado desactualizado");
  expect(text).not.toContain("trip_updates");
  expect(mergeNews([{id: "degraded:gtfs:error:none", text: "GTFS vencido", circulation: null}], [])).toEqual([]);
});

it("distingue GPS bruto, corredor y extrapolación en leyenda y mapa", () => {
  const raw = methodStyle("anchor", "raw");
  const matched = methodStyle("anchor", "map_matched");
  expect(raw.detail).toContain("sin proyectar");
  expect(matched.detail).toContain("sobre el corredor");
  expect(raw.shape).not.toBe(matched.shape);
  expect(methodStyle("extrapolated_from_last_anchor", "map_matched").label).toBe("Extrapolada");
  const legend = renderToStaticMarkup(<Legend present={[{method: "anchor", space: "raw"}, {method: "anchor", space: "map_matched"}]} />);
  expect(legend).toContain("Observada en bruto");
  expect(legend).toContain("Observada sobre corredor");
  const index = buildCatalogIndex(fixture.catalog as unknown as Catalog);
  const original = fixture.vehicles[0] as unknown as SnapshotVehicle;
  const vehicle = {...original, rendered: {...original.rendered, rendering_method: "anchor" as const, coordinate_space: "raw" as const}};
  const frame = vehicleFrames([vehicle], {index, colors: new Map(), activeLines: new Set(), selectedVehicleKey: null, selectedStationId: null}, Date.parse(fixture.at));
  expect(frame.collection.features[0].properties?.provenance).toBe("Observada en bruto");
  expect(frame.collection.features[0].properties?.shape).toBe(raw.shape);
});
