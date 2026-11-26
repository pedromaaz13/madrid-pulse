// @vitest-environment jsdom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import fixture from "./__fixtures__/snapshot-map-matched.json";
import type { SnapshotDegradation } from "./domain/contract";

vi.mock("./map/webgl", () => ({ hasWebGL: () => false }));
vi.mock("./hooks/usePageVisible", () => ({ usePageVisible: () => true }));

afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); document.body.innerHTML = ""; });

it("App sigue la vigencia del snapshot al conservar el catálogo cacheado", async () => {
  vi.useFakeTimers();
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  HTMLElement.prototype.scrollTo = vi.fn();
  let seq = 1;
  let item: SnapshotDegradation | null = {resource: "gtfs", feed_name: null, status: "stale", reason: "El catálogo GTFS vence el 18 de diciembre.", last_valid_source_timestamp: null, data_age_s: null, poll_age_s: null};
  let catalogRequests = 0;
  let conditionalHeader: string | undefined;
  const catalog = {...fixture.catalog, gtfs_status: "valid"};
  const fetchMock = vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const path = String(input);
    if (path.includes("/catalog")) {
      catalogRequests++;
      if (catalogRequests > 1) conditionalHeader = (options?.headers as Record<string, string>)["If-None-Match"];
      return new Response(JSON.stringify(catalogRequests === 1 ? catalog : {...catalog, gtfs_status: "expired", operator: "OPERADOR NUEVO"}), {status: 200, headers: {"Content-Type": "application/json", ETag: '"catalogo"'}});
    }
    if (path.includes("/snapshot")) return new Response(JSON.stringify({
      schema_version: "1.0", snapshot_id: `snapshot-${seq}`, snapshot_id_is_sortable: false,
      revision: {scope: "test", scope_source: "database_system_identifier", sequence: seq, generated_at: `2026-12-${String(17 + seq).padStart(2, "0")}T12:00:00Z`, tiebreak: `t${seq}`},
      mode: "replay", catalog_ref: {catalog_version: catalog.catalog_version, gtfs_version: catalog.gtfs_version, geometry_catalog_version: catalog.geometry_catalog_version},
      generated_at: "2026-12-18T12:00:00Z", display_at: "2026-12-18T12:00:00Z", feeds: [], degraded: item ? [item] : [], vehicles: [],
      counts: {vehicles_total: 0, by_rendering_method: {}, by_coordinate_space: {}, with_operator_delay: 0, without_operator_delay: 0},
    }), {status: 200, headers: {"Content-Type": "application/json"}});
    return new Response(JSON.stringify({mode: "replay", feeds: []}), {status: 200, headers: {"Content-Type": "application/json"}});
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div"); document.body.append(container);
  const root = createRoot(container);
  await act(async () => { root.render(<App />); });
  expect(container.textContent).toContain("GTFS · aviso: El catálogo GTFS vence el 18 de diciembre.");
  expect(catalogRequests).toBe(1);
  seq = 2; item = {...item!, status: "error", reason: "El catálogo GTFS venció el 18 de diciembre."};
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(container.querySelector('[role="alert"]')?.textContent).toContain("GTFS · error: El catálogo GTFS venció el 18 de diciembre.");
  expect(catalogRequests).toBe(1);
  seq = 3; item = {...item!, status: "unknown", reason: "El catálogo GTFS aún no ha entrado en vigencia."};
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(container.textContent).toContain("GTFS · vigencia desconocida: El catálogo GTFS aún no ha entrado en vigencia.");
  seq = 4; item = null;
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(container.textContent).not.toContain("GTFS ·");
  await act(async () => { await vi.advanceTimersByTimeAsync(570_000); });
  expect(catalogRequests).toBeGreaterThan(1);
  expect(conditionalHeader).toBe('"catalogo"');
  expect(container.textContent).toContain("Red · Renfe");
  expect(container.textContent).not.toContain("OPERADOR NUEVO");
  expect(container.textContent).not.toContain("GTFS ·");
  expect(container.textContent).not.toContain("último dato válido");
  await act(async () => { root.unmount(); });
});
