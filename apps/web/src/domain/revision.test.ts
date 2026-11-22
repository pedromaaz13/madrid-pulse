import { describe, expect, it } from "vitest";
import { isNewerRevision } from "./revision";
import type { SnapshotRevision } from "./contract";

function revision(partial: Partial<SnapshotRevision>): SnapshotRevision {
  return {
    scope: "pg:1",
    scope_source: "database_system_identifier",
    sequence: 1,
    generated_at: "2026-11-20T14:33:00Z",
    tiebreak: "sha256:aaa",
    ...partial,
  };
}

describe("isNewerRevision", () => {
  it("acepta la primera respuesta", () => {
    expect(isNewerRevision(revision({}), null)).toBe(true);
  });

  it("ordena por sequence dentro del mismo ámbito", () => {
    const current = revision({ sequence: 5 });
    expect(isNewerRevision(revision({ sequence: 6 }), current)).toBe(true);
    expect(isNewerRevision(revision({ sequence: 4 }), current)).toBe(false);
  });

  it("descarta una respuesta antigua aunque llegue después", () => {
    const current = revision({ sequence: 9, generated_at: "2026-11-20T14:40:00Z" });
    const late = revision({ sequence: 3, generated_at: "2026-11-20T14:30:00Z" });
    expect(isNewerRevision(late, current)).toBe(false);
  });

  it("con la misma sequence desempata por generated_at", () => {
    const current = revision({ sequence: 7, generated_at: "2026-11-20T14:33:00Z" });
    expect(
      isNewerRevision(revision({ sequence: 7, generated_at: "2026-11-20T14:33:10Z" }), current),
    ).toBe(true);
    expect(
      isNewerRevision(revision({ sequence: 7, generated_at: "2026-11-20T14:32:50Z" }), current),
    ).toBe(false);
  });

  it("no sustituye una revisión por otra idéntica", () => {
    const current = revision({});
    expect(isNewerRevision(revision({}), current)).toBe(false);
  });

  it("trata un cambio de ámbito como discontinuidad, no como orden", () => {
    // Otro ámbito (otra base, o un reinicio con identificador nuevo) no es
    // comparable: se acepta aunque su `sequence` sea menor.
    const current = revision({ scope: "pg:1", sequence: 900 });
    expect(isNewerRevision(revision({ scope: "pg:2", sequence: 1 }), current)).toBe(true);
  });

  it("nunca usa snapshot_id: dos revisiones iguales con distinto tiebreak no avanzan", () => {
    const current = revision({ tiebreak: "sha256:aaa" });
    expect(isNewerRevision(revision({ tiebreak: "sha256:zzz" }), current)).toBe(false);
  });
});
