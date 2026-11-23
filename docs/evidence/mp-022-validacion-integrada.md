# MP-022 — Validación integral de cierre

Resultado del ejecutor: **PARTIAL, entregado a revisión**. Las puertas 1–6
quedan reproducidas; la 7 conserva evidencia real de MP-020 y añade una
secuencia sintética controlada, pero no pudo revalidarse visualmente en esta
sesión; las puertas 8 y 9 no se cierran porque Orca no expuso navegador. No se
marca el hito ni la tarea `DONE`.

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

Los 88 tests frontend incluyen `revision.test.ts`: una respuesta de secuencia
3 se descarta cuando la vigente es 9; un `snapshot_id`/hash distinto con la
misma revisión tampoco reemplaza el estado. El backend verificó en el replay
revisión `3 → 6 → 7` dentro del mismo scope y declaró
`snapshot_id_is_sortable=false`. La selección y la cámara dependen de
identidad/estado React, no del hash.

### 7. Tres capturas con reloj controlado y movimiento reducido — PARTIAL

La nueva prueba
`test_three_controlled_clocks_advance_then_freeze_at_the_horizon` usa tres
instantes controlados: avanza dentro de la envolvente, respeta el máximo
físico de velocidad y se congela en `max_progress_m` al agotar horizonte.
Los tests del motor cubren espera de estación y sentido; los del cliente
congelan `frameFor` tras `valid_until`.

La inspección real de MP-020 ya observó en Chrome deriva 0 durante 4 s con
`prefers-reduced-motion`, un único repintado por snapshot y contenido
accesible. Se auditó esa evidencia y sigue respaldada por el código, pero no
se reejecutó en navegador durante MP-022 porque no había navegador disponible.
Por eso esta puerta no se eleva a cierre final nuevo.

### 8. UX completa desktop/móvil/teclado/sin WebGL — PARTIAL

Las capturas reales heredadas de MP-020 demuestran mapa integrado (no el
prototipo), C4/C5, Atocha/Alcorcón, tren, Seguir → arrastrar → Volver al tren,
390 px, teclado, Atrás y fallback sin WebGL. MP-021 demuestra History,
identidad Live↔History y 390 px con el frontend integrado.

Para MP-022 se levantó el entorno propio y se verificaron API/tablero/archivo,
pero `agent.browsers.list()` devolvió `[]` después del diagnóstico obligatorio
de la skill. No existen capturas o vídeo nuevos de esta sesión y no se usó
`diseno/live.html`. La navegación completa combinada queda pendiente de
repetición por el revisor o en una sesión con navegador disponible.

### 9. Benchmark reproducible — PARTIAL

[`mp-022-benchmark.md`](mp-022-benchmark.md) publica equipo, dataset, reloj,
p50/p95 de API, edad y cobertura. Snapshot: 254,73/418,23 ms; tablero Atocha:
103,14/179,75 ms; salud: 75,23/83,14 ms. Se registró el coste del endpoint
legado (1 621,14/2 110,15 ms) en vez de ocultarlo. API/Vite ya calentados:
13,1/3,6 MiB RSS.

No se pudo medir duración de frames, heap ni memoria del navegador en el
recorrido MP-022. Las medidas de 60 s de MP-020 se conservan como evidencia
heredada, no se renombran como una corrida nueva. Puerta `PARTIAL`.

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
  vitest: 9 ficheros, 88/88
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

No apareció un bloqueante de producto en catálogo/datos: las 12 líneas están,
C4 permanece seleccionable con 0 GPS, 121/121 observaciones del corte resuelven
sin atribución falsa y los 75 patrones sin map matching usan fallback honesto.
Sin embargo, las puertas 7–9 exigen evidencia de navegador nueva que esta
sesión no pudo producir. MP-022 queda `REVIEW (PARTIAL)`, no `DONE`; el revisor
debe repetir la inspección integrada y completar frames/memoria antes de poder
aprobar el cierre del Hito 3.
