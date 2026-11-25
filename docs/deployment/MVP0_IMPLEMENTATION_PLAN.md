# MVP0_IMPLEMENTATION_PLAN.md — Demo estática en GitHub Pages (para aprobación)

Fecha: 2026-11-24. **Propuesta. No se ha modificado código funcional ni publicado ninguna URL.** Sustituye las tareas D-01…D-07 de `MVP_RELEASE_CHECKLIST.md`.

## 1. Principio: contrato propio de demo estática
FR-01 (movimiento ficticio antes de salida/tras llegada) y FR-02 (replay/snapshot inconsistente) viven en `build_snapshot`, el motor de movimiento y la ruta `?at=`. **La demo no pasa por ellos.** Un exportador offline genera ficheros con un contrato mínimo y verificable, derivado de datos observados:

| Fichero | Contenido | Qué se excluye a propósito |
|---|---|---|
| `demo/manifest.json` | versión del contrato, fecha de captura, rango, ciclos, SHA-256 de feeds y GTFS, licencias/atribuciones, versión del catálogo | — |
| `demo/catalog.json` | líneas, estaciones, geometría de corredor y cobertura ("28 patrones verificados"), tal cual el catálogo existente (`/api/v1/catalog`, `packages.geo`/`gtfs`, no afectado por FR-01/02) | geometría inventada: líneas sin corredor verificado se dibujan sin trazado |
| `demo/frames/NNNN.json` | **una trama por actualización real del feed** (≈20–30 s): por vehículo `id`, `trip_id`, línea, coordenada **observada**, `observed_at`, edad respecto a la trama, estado GPS tal como lo informó la fuente, retraso informado por el operador si existe | `progress_envelope`, `speed_mps`, ETA, `rendered` proyectado/interpolado, cualquier posición no observada |
| `demo/stations.json` | ficha de estación: nombre, líneas que la sirven, horario programado de la parada si procede (GTFS estático) | tablero "próximos trenes" calculado con RT |

Forma: subconjunto estricto del esquema `SnapshotOut` con `progress_envelope: null` y `rendering_method` observado. Así la interfaz (`frameFor` devuelve `published` cuando no hay envolvente: `domain/movement.ts`) **no mueve nada entre tramas**: los trenes saltan de una observación a la siguiente. Se acabó FR-01 por construcción.

## 2. Datos: qué captura usar
- Disponible hoy: `data/hito-03/replay`, **dos muestras** (15:32 y 15:33 del 2026-11-20) + GTFS (SHA `c5b40823…`). Insuficiente para "navegar" (sin recorrido).
- Procedimiento propuesto (D-01), dentro de la autorización existente de acceso a los feeds públicos de Renfe (colector a 30 s, `max-age=30`, MP-003): ejecutar el colector del repositorio contra una **base desechable propia** (puerto propio, nunca 5433) durante **90 min en hora punta de un día laborable** (≈180 ciclos, ≈55 MB de descarga). Resultado: `manifest` con SHA-256 de cada trama bruta; las muestras se guardan como evidencia reproducible.
- Mientras llega la captura, la cadena se construye y prueba con las dos muestras.

## 3. Cambios por archivo

| Archivo | Cambio | Tipo |
|---|---|---|
| `scripts/export_static_demo.py` (nuevo) | lee observaciones de la base desechable + GTFS; escribe `demo/*`; determinista (mismo SHA en dos ejecuciones) | nuevo |
| `scripts/demo_contract.py` (nuevo) o `packages/contracts/demo_schema.json` | esquema del contrato de demo y validador | nuevo |
| `apps/web/src/api/client.ts` | si `VITE_DATA_MODE=static`, `requestJson` resuelve `/catalog`, `/snapshot`, `/health` contra `${BASE_URL}demo/…` | modificar (~30 líneas) |
| `apps/web/src/api/resources.ts` | `fetchSnapshot(at)` → trama más cercana ≤ `at`; `fetchHealth` → estado `archive` con fecha de captura; `board`/`history` desactivados con mensaje honesto | modificar |
| `apps/web/src/hooks/useClock.ts`, `useSnapshot.ts` | reloj de demo en bucle sobre `[inicio, fin]` de la captura; el bucle se **declara** ("reinicio de la reproducción") | modificar |
| `apps/web/src/ui/TopBar.tsx` | etiqueta de modo: `DEMO · CAPTURA 2026-11-20 HH:MM–HH:MM`, nunca `LIVE`; ocultar pestaña History/Explore si no hay datos de demo | modificar |
| `apps/web/src/App.tsx` | banner persistente (captura congelada, sin movimiento entre observaciones, cobertura parcial); sin "Ver en Live" | modificar |
| `apps/web/src/map/MapView.tsx` (líneas ~195) | fuente configurable `VITE_MAP_STYLE_URL` / `VITE_TILE_URL`; atribución derivada de la configuración | modificar |
| `apps/web/src/ui/Legend.tsx` / pie | pie con atribución Renfe (CC BY 4.0, "datos modificados, sin respaldo de Renfe") y OSM/ODbL | modificar |
| `apps/web/vite.config.ts` | `base` desde `VITE_BASE_PATH` (por defecto `/`) | modificar (3 líneas) |
| `apps/web/scripts/verify-build.mjs` | modo demo: falla si `dist/` contiene `/api/`, `localhost`, la cadena `LIVE` como estado o ficheros `rendered.progress_envelope` ≠ null | modificar |
| `.github/workflows/pages.yml` (nuevo) | build con `VITE_DATA_MODE=static`; despliegue **solo en `workflow_dispatch` desde `main`**, permisos mínimos; sin secretos | nuevo |
| `docs/legal/ATTRIBUTION.md`, `README.md` | enlace a la demo y atribuciones | docs |

No se toca: `apps/api/*`, `packages/movement/*`, `packages/geo/*` (cero cambios en código del motor).

## 4. Dependencias reales
Sin dependencias npm nuevas para MapLibre ráster/estilo vectorial. PMTiles (plan B) añadiría `pmtiles` (BSD). Python: las ya instaladas (`requirements.txt`). Docker: solo para la base desechable de la captura. Datos: GTFS Renfe (CC BY 4.0), feeds RT (CC BY 4.0); la redistribución de tramas observadas exige la atribución anterior.

## 5. Pruebas (todas deben fallar sin el cambio)
1. **Contrato** (pytest/unittest sobre `demo/*`): sin `progress_envelope` ≠ null, sin campos de velocidad/ETA; toda coordenada es una observación del feed (`observed_at` ≤ trama, edad ≥ 0); ids resuelven al catálogo; coordenadas dentro del bbox de Madrid.
2. **Determinismo:** dos exportaciones → mismo hash de `manifest` y tramas.
3. **Adaptador** (vitest): `at` → trama; límites de ventana; bucle; no hay llamadas `fetch` a `/api` en modo estático.
4. **Anti-FR-01:** un tren sin observación nueva entre dos tramas mantiene exactamente la misma coordenada (test de `frameFor` con tramas de demo).
5. **Build:** `verify-build` en modo demo; `dist/` sin secretos ni `localhost`.
6. **Visual (revisor Claude con DevTools, preflight de la herramienta):** capturas 1440 y 390 px con banner, atribuciones y fecha visibles; sin `LIVE`.
7. **Atribución/licencia:** test que exige las cadenas de Renfe y OSM en el pie.

## 6. Tareas, modelos y revisores (política vigente; ningún Opus necesario)

| ID | Tarea | Ejecutor · esfuerzo | Revisor contrario · esfuerzo | Puerta humana |
|---|---|---|---|---|
| D-01 | Captura 90 min con BD desechable + `manifest` | `claude-sonnet-5-5` · medium (coordinador; solo ejecuta el colector existente) | `gpt-6.2-sol` · medium | autorizar la captura continua local |
| D-02 | Contrato de demo + exportador determinista + tests 1–2 | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | — |
| D-03 | Adaptador estático, reloj en bucle, TopBar/banner/pie, tests 3–4, 7 | `claude-sonnet-5-5` · high (frontend; Terra sin navegador no valida visual) | `gpt-6.2-sol` · high (código); validación visual la hace el coordinador con DevTools | — |
| D-04 | Teselas configurables (`MapView.tsx`) + estilo OpenFreeMap | `claude-sonnet-5-5` · medium | `gpt-6.2-sol` · medium | confirmar proveedor |
| D-05 | `vite base`, `verify-build` demo, `pages.yml` | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | activar Pages y ejecutar el despliegue |
| D-06 | Validación integrada previa a publicar (capturas, build, contrato, atribuciones) | `claude-sonnet-5-5` · medium | `gpt-6.2-sol` · high | **aprobación de la demo antes de la URL** |

Dependencias: D-01 ∥ D-02 → D-03 (necesita el contrato) ∥ D-04 → D-05 → D-06. Estimación: 1,5–2 jornadas de agentes más 90 min de captura.

## 7. Orden de trabajo con el Hito 4 (conflictos de archivos)
**La demo no condiciona ni retrasa los P0 de Live, y los P0 no esperan a la demo.** Ambos avanzan en paralelo cuando no comparten archivos (`docs/roadmap/RELEASE_ROADMAP.md`).
- **Aislamiento previo de la captura:** D-01 depende de MP-023 (la captura en vivo usa BD desechable y la auditoría exige no usar defaults hacia 5433) y de la autorización humana `HG-CAPTURE`. D-02 y D-04 pueden empezar sin captura (con las dos muestras).
- **Paralelizable sin solaparse:** MP-023 (`apps/api/config.py`, `services/collector/config.py`, tests), MP-024 (ADR) y MP-026a (`apps/api`, `packages`) no tocan `apps/web`.
- **Secuenciar solo si hay solape efectivo:** si D-03/D-04 y MP-030 (`apps/web/src/ui/*`, `App.tsx`, `MapView.tsx`) están activas a la vez, MP-030 espera a D-06; si la demo no se ejecuta, MP-030 no se retrasa.
- **MP-025a/b y MP-026b siguen su ruta propia** (tras la aprobación del ADR de MP-024); no se posponen por la demo.
- Límite de concurrencia: ≤2 workers pesados por proveedor.

## 8. Riesgos y límites
- Una demo de tramas observadas es **menos fluida** que Live (saltos cada 20–30 s): honesta, no espectacular. Si el propietario quiere suavidad, necesita H4-04 (movimiento correcto) — no se finge.
- Las líneas con trazado no verificado (hoy 72 de 103 patrones sin corredor) se muestran sin línea; el banner lo dice.
- Condiciones de OpenFreeMap a verificar el día de publicar; plan B PMTiles.
- Publicar no ocurre sin tu aprobación tras D-06.
