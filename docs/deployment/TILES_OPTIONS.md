# TILES_OPTIONS.md — Fuente de teselas para MapLibre

Fecha: 2026-11-24. Requisito del propietario: no depender de `tile.openstreetmap.org` como solución escalable y mantener la fuente **configurable**. Datos leídos en las páginas oficiales de cada proveedor; las condiciones cambian y están marcadas **(verificar antes de publicar)** cuando la fuente era antigua o ambigua.

## Estado actual del código
`apps/web/src/map/MapView.tsx:195` define una fuente **ráster** con `tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"]`, atribución ODbL ya visible. No es configurable.

## Política vigente de OSMF (https://operations.osmfoundation.org/policies/tiles/)
Servicio sin SLA y financiado con donaciones; uso intensivo o inapropiado puede bloquearse sin aviso; prohibido el *scraping*, la precarga masiva y los archivos de teselas sin conexión; se exige caché, User-Agent/Referer válidos y atribución; para uso exigente indica usar un servicio alternativo o uno propio. Conclusión: aceptable en desarrollo y, como mucho, en un demo de tráfico bajo; **no** como base de un servicio público.

## Alternativas

| Opción | Tipo | Coste | Límites / licencia | Atribución | Esfuerzo en nuestro código |
|---|---|---|---|---|---|
| **OpenFreeMap** (instancia pública) | vector (OpenMapTiles), URL de *style* | 0 €, sin clave ni registro | sin límites publicados de vistas/peticiones; sin SLA; se financia con donaciones; código MIT, datos OSM; uso comercial: no confirmado en la página oficial **(verificar)** | OpenFreeMap + OpenMapTiles + OSM (MapLibre la añade sola) | pasar de fuente ráster a `style` URL y volver a añadir nuestras capas tras `style.load` (M) |
| **PMTiles propio** (Protomaps) | vector en un solo fichero, servido con peticiones *range* | tu almacenamiento/ancho de banda (R2 recomendado por no cobrar salida; precio de R2 **por verificar**; GitHub Pages ≤1 GB también valdría para un extracto pequeño) | código BSD/CC0; datos ODbL como *produced work*; sin dependencia de terceros ni claves; sin límites externos | © OpenStreetMap (+ Protomaps según su guía) | plugin `pmtiles` + estilo propio (M); hay que generar el extracto de Madrid |
| **MapTiler Cloud** | ráster/vector con clave | Free 0 € (100 k peticiones/mes, 5 k sesiones, se pausa al agotarse; orientada a no comercial/pruebas); Flex 30 USD/mes (500 k peticiones, 0,15 USD/1 000 extra) | uso comercial en Free ambiguo (**verificar**); clave pública restringida por dominio | MapTiler + OSM | cambio de URL/estilo (S–M) |
| **Stadia Maps** | ráster/vector con clave | Free 0 € solo **no comercial** (200 000 créditos/mes, 1 crédito por tesela, 429 al agotarse); Starter 20 USD/mes (1 M créditos, +0,03 USD/1 000) | comercial exige plan de pago | Stadia + OSM | cambio de URL/estilo (S–M) |
| OSMF `tile.openstreetmap.org` | ráster | 0 € | ver política | © OSM | ninguno |

Aritmética de demanda (supuesto, no medido): una sesión de mapa carga ≈ 30–60 teselas; 1 000 sesiones/mes ≈ 30–60 k teselas, dentro de cualquier plan gratuito; 20 000 sesiones/mes ya superaría el gratuito de MapTiler (100 k) y de Stadia (200 k créditos) según el tamaño de pantalla y los *pans*.

## Recomendación
1. **Hacer la fuente configurable ya (tarea D-04):** variables `VITE_MAP_STYLE_URL` (vector) y `VITE_TILE_URL` (ráster de respaldo); atribución derivada de la configuración, nunca fija.
2. **Demo (MVP 0):** OpenFreeMap con un estilo claro (tipo *positron*/*liberty*) — 0 €, sin clave ni registro, se parece más al look actual que un ráster OSM estándar. Comprobar sus condiciones el día de publicar.
3. **Servicio Live (MVP 1) y plan B inmediato:** PMTiles propio de la región de Madrid sobre el mismo VPS (Caddy sirve el fichero con *range*) o en R2: sin terceros, sin límites, coste ≈ 0 € adicional; si se prefiere externalizar, MapTiler Flex (30 USD/mes) o Stadia Starter (20 USD/mes) con clave restringida por dominio.
4. `tile.openstreetmap.org` queda solo para desarrollo local.

Decisión que necesito: confirmar OpenFreeMap para el demo y PMTiles propio como camino de Live.
