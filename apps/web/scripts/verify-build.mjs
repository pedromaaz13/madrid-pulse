import { readFile } from "node:fs/promises";

const sourceUrl = new URL("../node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs", import.meta.url);
const builtUrl = new URL("../dist/assets/maplibre-gl-worker.mjs", import.meta.url);

const [source, built] = await Promise.all([readFile(sourceUrl), readFile(builtUrl)]);

if (!source.equals(built)) {
  throw new Error("The production MapLibre worker is missing or differs from the installed package");
}

console.log(`Verified production MapLibre worker (${built.byteLength} bytes)`);
