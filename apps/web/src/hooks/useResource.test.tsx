// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useResource, type ResourceState } from "./useResource";

interface Probe<T> {
  state: ResourceState<T> & { refresh: () => void };
}

function mount<T>(
  fetcher: (signal: AbortSignal) => Promise<T | null>,
  options: Parameters<typeof useResource<T>>[1],
): { probe: Probe<T>; root: Root; container: HTMLDivElement } {
  const probe = { state: null as unknown as Probe<T>["state"] };
  function Harness() {
    probe.state = useResource<T>(fetcher, options);
    return null;
  }
  const container = document.createElement("div");
  document.body.append(container);
  const root = createRoot(container);
  act(() => root.render(<Harness />));
  return { probe, root, container };
}

const roots: Root[] = [];
afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
});

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("useResource", () => {
  it("publica el primer valor bueno", async () => {
    const { probe, root } = mount(async () => ({ v: 1 }), { intervalMs: null, enabled: true });
    roots.push(root);
    await flush();
    expect(probe.state.data).toEqual({ v: 1 });
    expect(probe.state.error).toBeNull();
  });

  it("mantiene una sola lectura en vuelo por recurso", async () => {
    let resolve!: (value: { v: number }) => void;
    const pending = new Promise<{ v: number }>((r) => { resolve = r; });
    const fetcher = vi.fn(() => pending);
    const { probe, root } = mount(fetcher, { intervalMs: null, enabled: true });
    roots.push(root);
    await flush();
    // Varias peticiones mientras la primera sigue viva no lanzan más fetches.
    act(() => { probe.state.refresh(); probe.state.refresh(); });
    expect(fetcher).toHaveBeenCalledTimes(1);
    await act(async () => { resolve({ v: 7 }); await pending; });
    expect(probe.state.data).toEqual({ v: 7 });
  });

  it("conserva el último valor bueno cuando un sondeo falla", async () => {
    let attempt = 0;
    const fetcher = async () => {
      attempt += 1;
      if (attempt === 1) return { v: "bueno" };
      throw new Error("la fuente no responde");
    };
    const { probe, root } = mount(fetcher, { intervalMs: null, enabled: true });
    roots.push(root);
    await flush();
    expect(probe.state.data).toEqual({ v: "bueno" });
    await act(async () => { probe.state.refresh(); });
    await flush();
    expect(probe.state.data).toEqual({ v: "bueno" });
    expect(probe.state.error).toBe("la fuente no responde");
    expect(probe.state.failures).toBe(1);
  });

  it("descarta una respuesta que `accept` rechaza por antigua", async () => {
    const values = [{ seq: 5 }, { seq: 2 }];
    let index = 0;
    const fetcher = async () => values[Math.min(index++, values.length - 1)];
    const { probe, root } = mount(fetcher, {
      intervalMs: null,
      enabled: true,
      accept: (incoming, current) => current === null || incoming.seq > current.seq,
    });
    roots.push(root);
    await flush();
    expect(probe.state.data).toEqual({ seq: 5 });
    await act(async () => { probe.state.refresh(); });
    await flush();
    // La respuesta más antigua no sustituye a la vigente, y no es un error.
    expect(probe.state.data).toEqual({ seq: 5 });
    expect(probe.state.error).toBeNull();
  });

  it("un 304 (null) es éxito sin sustituir ni rejuvenecer el valor", async () => {
    let first = true;
    const fetcher = async () => {
      if (first) { first = false; return { v: "catálogo" }; }
      return null;
    };
    const { probe, root } = mount(fetcher, { intervalMs: null, enabled: true });
    roots.push(root);
    await flush();
    const acceptedAt = probe.state.acceptedAtMs;
    await act(async () => { probe.state.refresh(); });
    await flush();
    expect(probe.state.data).toEqual({ v: "catálogo" });
    expect(probe.state.acceptedAtMs).toBe(acceptedAt);
    expect(probe.state.error).toBeNull();
  });

  it("no sondea mientras está deshabilitado", async () => {
    const fetcher = vi.fn(async () => ({ v: 1 }));
    const { root } = mount(fetcher, { intervalMs: null, enabled: false });
    roots.push(root);
    await flush();
    expect(fetcher).not.toHaveBeenCalled();
  });
});
