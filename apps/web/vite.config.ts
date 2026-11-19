import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // MapLibre crea su worker mediante una URL ESM propia. Prebundlearlo con
  // esbuild hace que Vite dev responda 504 para maplibre-gl-worker.mjs y deja
  // sin procesar las fuentes GeoJSON (corredor/estaciones), aunque los tiles y
  // marcadores DOM sigan visibles. Servir el paquete directamente conserva el
  // worker; la build de producción usa el pipeline normal de Rolldown.
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
