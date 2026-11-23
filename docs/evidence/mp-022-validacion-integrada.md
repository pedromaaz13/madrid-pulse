# MP-022 — Validación integral de cierre

Resultado del ejecutor tras la inspección independiente: **las nueve puertas
quedan cerradas y la tarea se entrega a `REVIEW`**. Las puertas 1–6 se
reprodujeron en el entorno propio del ejecutor; el revisor ejecutó las puertas
7–9 en una sesión nueva con navegador real sobre el frontend integrado. No se
marca el hito ni la tarea `DONE`: esa promoción corresponde al revisor tras
auditar la corrección del hallazgo descrito al final.

## Entorno exclusivo de la auditoría

- PostgreSQL desechable `mp022-validation-db`, PostGIS 17-3.5, puerto 5437.
- API real en `127.0.0.1:8012`, Vite real en `127.0.0.1:5183`, Node 22.13.1.
- GTFS congelado `sha256:c5b40823…`; replay `1532/1533` ingerido con el
  colector real. Recuentos finales `240/199/4/7/2`.
- Segundo PostgreSQL limpio `mp022-ci-db`, puerto 5438, exclusivo para suite:
  termina en `0/0/0/0/0`; ninguna escritura tocó la base de desarrollo 5433.
- Archivo frío propio en `data/parquet/` (ignorado por Git), día 2026-11-20.
  Dos reprocesados consecutivos produjeron el mismo inventario de 9 ficheros
  y los mismos SHA-256 (`byte_identical: true`).

## Las nueve pruebas vinculantes

### 1. Viaje programado válido sin GPS — PASS

`StationBoardPostgresTests.test_board_entries_appear_even_without_any_gps`
construye el tablero desde calendario/servicios sobre una base sin posiciones:
cada entrada tiene hora, operador Renfe, `circulation_source=scheduled_only`,
`position_available=false`, método ETA `schedule` y ningún retraso fabricado.

Además, contra el replay integrado, Atocha (`18000`) devolvió 118 llamadas
programadas, 20 visibles; una C10 (`1023V21339C10`) apareció como
`scheduled_only`, sin posición y con salida `schedule`. No se rotuló como GPS.

### 2. Excepción de calendario + 24:xx — PASS

Nueva prueba sintética explícita
`SyntheticCalendarBoundaryAcceptanceTests.test_removed_service_with_24xx_trip_never_leaks_into_the_wrong_day`:
un viaje 23:55→24:05 con excepción tipo 2 queda fuera del 2026-11-20 y no
reaparece por el cambio de día; el 2026-11-21 conserva únicamente su propia
instancia. La fixture está marcada como no oficial.

### 3. Recuperación de GPS tras estimación — PASS sintético derivado

`SyntheticDerivedRecoveryAcceptanceTests.test_gps_recovery_after_estimation_keeps_raw_matched_and_rendered_distinct`
parte de un ancla sintética sobre GTFS/OSM versionados, entra en `estimated`,
recibe una nueva observación y vuelve a `observed`. La observación raw, la
proyección y la coordenada rendered conservan su procedencia; la corrección
avanza por el mismo corredor y queda acotada a 70 m, sin salto de ramal.
`tests/fixtures/mp022_synthetic/README.md` dice expresamente que no es Renfe.

### 4. Feed detenido / vacío / parcial — PASS

`apps.api.tools.replay_three_snapshots` produjo cuatro estados reales sobre
la base desechable:

- normal 1532: 119 vehículos;
- normal 1533: 122 últimos conocidos (121 observados exactamente en el corte);
- parcial: `trip_updates=error`, 122 vehículos conservados y solo
  `delays_and_eta` degradado;
- detenido +1 h: 122 `stale_frozen`, feeds `stale/error`, mismo
  `gps_observed_at`; ninguna observación rejuvenecida.

`VehiclePositionIngestionTests.test_valid_empty_feed_is_success_not_network_failure`
cubre además feed válido con cero entidades. Las alertas caídas degradan su
recurso de forma independiente en la prueba de snapshots parcial/congelado.

### 5. Cambio de identidad vehículo→trip/día — PASS

`VehicleTripChangeTests.test_previous_observation_from_another_trip_is_not_passed_to_engine`
demuestra que una observación previa de otro `trip_id` no se entrega al motor.
La identidad Live/History incluye vehículo + viaje + día de servicio; los
tests de History confirman que un día distinto no reutiliza la circulación ni
un retraso de otro servicio.

### 6. Respuestas fuera de orden — PASS

Los 89 tests frontend incluyen `revision.test.ts`: una respuesta de secuencia
3 se descarta cuando la vigente es 9; un `snapshot_id`/hash distinto con la
misma revisión tampoco reemplaza el estado. El backend verificó en el replay
revisión `3 → 6 → 7` dentro del mismo scope y declaró
`snapshot_id_is_sortable=false`. La selección y la cámara dependen de
identidad/estado React, no del hash.

### 7. Tres capturas con reloj controlado y movimiento reducido — PASS

La nueva prueba
`test_three_controlled_clocks_advance_then_freeze_at_the_horizon` usa tres
instantes controlados: avanza dentro de la envolvente, respeta el máximo
físico de velocidad y se congela en `max_progress_m` al agotar horizonte.
Los tests del motor cubren espera de estación y sentido; los del cliente
congelan `frameFor` tras `valid_until`.

En la inspección MP-022 del revisor, `window.matchMedia` se forzó a
`prefers-reduced-motion: reduce` **antes de montar React**. Se muestrearon
centro y zoom de `window.__mpMap` cada 700 ms durante 3,5 s: las seis muestras
fueron idénticas (deriva 0), mientras el reloj REPLAY y el snapshot seguían
actualizándose hasta 12:11:59. Se conserva así la información accesible sin
animación espacial automática.

### 8. UX completa desktop/móvil/teclado/sin WebGL — PASS

La sesión nueva del revisor recorrió el frontend integrado —nunca
`diseno/live.html`— así: Live → filtros C4a+C4b (`?lines=C4a,C4b`) → tren C4a
20277 (Alcobendas-San Sebastián de los Reyes) → Seguir tren → arrastre real
del lienzo MapLibre (`pointerdown`, 15 `mousemove`, `pointerup`) → aparición de
«Volver al tren» → clic y recentrado confirmado visualmente → History del
2026-11-20 → detalle real de 19656 con «no se puede abrir en Live» → Atrás.
El navegador restauró exactamente la URL con C5, tren 19656, `trip` y
`sd=2026-11-20`.

La emulación móvil fue real (`390x844x2,mobile,touch`), no un resize:
`scrollWidth == clientWidth == 390`, sin recorte. Con teclado, Tab alcanzó
buscador y filtros, el foco mostró outline de 3 px y Enter activó un filtro y
cambió la URL. Con `HTMLCanvasElement.prototype.getContext` anulado mediante
un script previo al montaje, apareció «Mapa no disponible · Este navegador no
ofrece WebGL» y lista/tablero siguieron navegables.

### 9. Benchmark reproducible — PASS con límite declarado

[`mp-022-benchmark.md`](mp-022-benchmark.md) publica equipo, dataset, reloj,
p50/p95 de API, edad y cobertura. Snapshot: 254,73/418,23 ms; tablero Atocha:
103,14/179,75 ms; salud: 75,23/83,14 ms. Se registró el coste del endpoint
legado (1 621,14/2 110,15 ms) en vez de ocultarlo. API/Vite ya calentados:
13,1/3,6 MiB RSS.

La sesión MP-022 midió `requestAnimationFrame` durante 3 s de zoom+pan+zoom:
182 frames, 60,3 fps, p50 16,70 ms, p95 18,30 ms y máximo 18,50 ms. El heap
real de `performance.memory` fue 96,2 MiB usados / 154,2 MiB totales / límite
4 192 MiB.

Límite honesto: el único corte disponible estaba ya congelado y tenía 68,7 h
de edad. Esta corrida mide fluidez de **interacción de mapa**, no animación de
posiciones ni 60 s de circulaciones avanzando. La medición continua de MP-020
se mantiene separada y no se atribuye a esta corrida.

## Replay congelado frente a producción

- `data/hito-03/replay/1532` y `1533`: capturas oficiales **congeladas** del
  2026-11-20, verificadas por SHA-256. La sonda reprodujo 119/119/49 y
  121/121/49.
- `tests/fixtures/mp022_synthetic/`: **sintética derivada**, `is_official_capture=false`,
  `is_live_production=false`; cubre escenarios temporales, no exactitud física.
- Producción en vivo: **no consultada ni afirmada** por MP-022. Ningún test se
  llama ni documenta como producción cuando usa replay o datos fabricados.

## Suites ejecutadas

```text
Python 3.12.3 + PostgreSQL limpio 5438
  Ran 283 tests in 41.429s — OK (skipped=5)
  focal MP-022: 7/7 — OK

Frontend, Node 22.13.1
  vitest: 10 ficheros, 89/89 (incluye regresión HistoryView 1/1)
  eslint --max-warnings 0: limpio
  tsc -b: limpio
  vite build: OK; worker MapLibre 550754 bytes verificado

Replay del kit
  1532: 119 Madrid / 119 matches / 49 SKIPPED sin arrival
  1533: 121 Madrid / 121 matches / 49 SKIPPED sin arrival
```

La primera corrida Python se lanzó erróneamente contra el GTFS completo y una
base ya ingerida; falló como era esperable porque parte de la suite contractual
usa la fixture C5 y exige base vacía. No se ocultó ni se contó como resultado.
Se corrigió el entorno con `mp022-ci-db` limpio y configuración por defecto;
esa segunda corrida es la válida y quedó en verde.

## Veredicto del ejecutor

No apareció un bloqueante de catálogo/datos: las 12 líneas están, C4 permanece
seleccionable con 0 GPS, 121/121 observaciones del corte resuelven sin
atribución falsa y los 75 patrones sin map matching usan fallback honesto. La
inspección sí encontró un defecto real: History sustituía silenciosamente un
día URL no archivado por el primero disponible en encabezado y breadcrumb. Se
corrigió para mostrar «Día no archivado», conservar la fecha solicitada y
ofrecer los días reales solo como opciones; la regresión renderizada impide
volver a presentar 2026-11-20 como si fuera el 2026-11-23 solicitado. MP-022
queda `REVIEW`, nunca `DONE` por el ejecutor, pendiente de la auditoría final
de Claude.
