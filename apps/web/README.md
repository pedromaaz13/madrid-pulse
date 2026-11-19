# apps/web — Madrid Pulse live map (MP-014)

Cliente estático React + TypeScript + MapLibre GL JS. Consume exclusivamente la
API propia `/api/v1/*`; Vite proxificala a `http://127.0.0.1:8000` en desarrollo.
No contiene fixtures ni respuestas simuladas en la build.

```sh
npm ci
npm run dev
```

La UI deriva las líneas de `/api/v1/lines` y no fija identificadores en su
lógica. Dibuja cada tramo de `line.geometry.segments` por separado, muestra las
estaciones en el orden proyectado por el backend, conserva visibles los
vehículos sin línea/posición resoluble y distingue los cuatro modos de ADR-0004
por forma, color y opacidad. La cartografía raster y la geometría ferroviaria
derivan de OpenStreetMap; la atribución ODbL permanece visible sobre el mapa.

Verificación local:

```sh
npm run lint
npm run typecheck
npm test
npm run build
npm run preview
```

`vite.config.ts` excluye `maplibre-gl` del prebundle de dependencias en
desarrollo. Vite 8 respondía `504` para su worker ESM prebundled y dejaba sin
procesar el corredor/las estaciones GeoJSON aunque tiles y marcadores DOM sí
aparecieran; servido directamente desde `node_modules`, el worker responde y
ambas capas se dibujan. La build de producción no usa `.vite/deps`: incorpora
el worker al chunk de MapLibre. `npm run preview` añade solo para el smoke local
el mismo proxy `/api` que desarrollo; el artefacto sigue siendo estático y en
despliegue espera `/api` bajo el mismo origen.
