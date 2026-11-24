import { describe, expect, it } from "vitest";
import type { Snapshot, SnapshotVehicle } from "./contract";
import { deriveNews, mergeNews } from "./news";
import fixture from "../__fixtures__/snapshot-map-matched.json";

const sample = fixture.vehicles as unknown as SnapshotVehicle[];

function snapshot(vehicles: SnapshotVehicle[], degraded: Snapshot["degraded"] = []): Snapshot {
  return {
    schema_version: "1.0",
    snapshot_id: "sha256:test",
    snapshot_id_is_sortable: false,
    revision: {
      scope: "pg:1",
      scope_source: "database_system_identifier",
      sequence: 1,
      generated_at: "2026-11-20T14:33:40Z",
      tiebreak: "sha256:aaa",
    },
    mode: "replay",
    catalog_ref: { catalog_version: "c", gtfs_version: "g", geometry_catalog_version: "y" },
    generated_at: "2026-11-20T14:33:40Z",
    display_at: "2026-11-20T14:33:40Z",
    feeds: [],
    degraded,
    vehicles,
    counts: {
      vehicles_total: vehicles.length,
      by_rendering_method: {},
      by_coordinate_space: {},
      with_operator_delay: 0,
      without_operator_delay: 0,
    },
  };
}

describe("deriveNews", () => {
  it("publica la degradación de un recurso con su causa", () => {
    const news = deriveNews(
      snapshot(sample.slice(0, 1), [
        {
          resource: "delays_and_eta",
          feed_name: "trip_updates",
          status: "error",
          reason: "feed detenido",
          last_valid_source_timestamp: null,
          data_age_s: 120,
          poll_age_s: 30,
        },
      ]),
      null,
    );
    expect(news).toHaveLength(1);
    expect(news[0].text).toContain("feed detenido");
  });

  it("no inventa novedades cuando no hay snapshot anterior", () => {
    expect(deriveNews(snapshot(sample.slice(0, 2)), null)).toEqual([]);
  });

  it("anuncia un cambio real de retraso, no el valor repetido", () => {
    const before = sample.slice(0, 1);
    const changed: SnapshotVehicle[] = [
      { ...before[0], delay: { ...before[0].delay, seconds: (before[0].delay.seconds ?? 0) + 60 } },
    ];
    expect(deriveNews(snapshot(before), snapshot(before))).toEqual([]);
    expect(deriveNews(snapshot(changed), snapshot(before))).toHaveLength(1);
  });

  it("anuncia una circulación nueva", () => {
    const news = deriveNews(snapshot(sample.slice(0, 2)), snapshot(sample.slice(0, 1)));
    expect(news.some((event) => event.text.includes("nueva circulación"))).toBe(true);
  });
});

describe("mergeNews", () => {
  it("no duplica un aviso ya presente", () => {
    const first = [{ id: "a", text: "A", circulation: null }];
    expect(mergeNews(first, first)).toHaveLength(1);
  });

  it("conserva los vigentes y pone los nuevos delante", () => {
    const merged = mergeNews(
      [{ id: "a", text: "A", circulation: null }],
      [{ id: "b", text: "B", circulation: null }],
    );
    expect(merged.map((event) => event.id)).toEqual(["b", "a"]);
  });

  it("acota la lista", () => {
    const many = Array.from({ length: 30 }, (_, i) => ({ id: `n${i}`, text: `${i}`, circulation: null }));
    expect(mergeNews([], many).length).toBeLessThanOrEqual(12);
  });
});
