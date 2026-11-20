import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";

const MAPLIBRE_WORKER_FILE = "assets/maplibre-gl-worker.mjs";
const MAPLIBRE_WORKER_SOURCE = new URL(
  "./node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs",
  import.meta.url,
);

function emitMapLibreWorker(): Plugin {
  return {
    name: "emit-maplibre-worker",
    apply: "build",
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: MAPLIBRE_WORKER_FILE,
        source: readFileSync(MAPLIBRE_WORKER_SOURCE),
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), emitMapLibreWorker()],
  // MapLibre crea su worker mediante una URL ESM propia. Prebundlearlo con
  // esbuild hace que Vite dev responda 504 para maplibre-gl-worker.mjs y deja
  // sin procesar las fuentes GeoJSON (corredor/estaciones), aunque los tiles y
  // marcadores DOM sigan visibles. Servir el paquete directamente conserva el
  // worker. Producción lo emite como asset explícito porque MapLibre deriva
  // su URL en runtime y Rolldown no puede descubrir esa dependencia dinámica.
  optimizeDeps: {
    exclude: ["maplibre-gl"],
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  preview: {
    // Solo para el smoke local de la build estática. En despliegue, el
    // frontend y /api se sirven bajo el mismo origen mediante reverse proxy.
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
