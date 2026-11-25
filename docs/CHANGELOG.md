# CHANGELOG.md

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Solo se registran cambios realmente realizados y verificables — nunca funcionalidad planeada o supuesta.

## [Unreleased]

### MP-026a — Replay temporal `?at=` y vigencia del GTFS (rama `pedromaaz13/mp-026a-replay-gtfs`, sin fusionar; apilada sobre MP-023)

Ejecutor Codex `gpt-6.2-sol` · high (recibo de Orca); revisor Claude Opus 5.5 · high (argv verificado): 2 rondas, APPROVED. **No integrada en `main`.**

#### Fixed
- FR-02: las lecturas de ingestas y observaciones se acotan al instante pedido; antes del primer dato el estado es «sin dato» con edades `null`, nunca negativas; `?at=` fuera de rango → 400 (antes 500).
- FR-19: la vigencia del GTFS se evalúa en ejecución con el reloj de la petición (`valid`/`expiring`/`expired`/`not_yet_valid`) en health, catálogo y snapshot, y degrada el snapshot con causa visible.

#### Changed
- Contrato con tres excepciones declaradas a «aditivo» (`poll_age_s` nullable, `feeds` siempre con tres, formato del ETag) y esquema `1.1`.

#### Verified
- RED contra `beb9434`/`fe0ea85` y GREEN; 296 tests con 18 skipped sobre PostgreSQL desechable; web 89 tests. Pendiente: Actions remoto y rotulado en la UI (MP-030).

### MP-023 — Configuración segura de PostgreSQL (rama `pedromaaz13/mp-023-db-segura`, sin fusionar)

Implementada por Codex `gpt-6.2-sol` · medium (recibo de Orca); revisada por Claude Sonnet 5.5 · high (argv verificado), 2 rondas, 0 bloqueantes. **No integrada en `main`.**

#### Changed
- API, colector y snapshotter sin valor por defecto de conexión: una sola variable `MADRID_PULSE_DATABASE_URL` y `MADRID_PULSE_ENV` obligatorios; fallo seguro antes de abrir conexiones; el puerto compartido de desarrollo se rechaza en cualquier host; marca de base desechable para escribir/probar; CI con base desechable, `MADRID_PULSE_REQUIRE_DB=1` y la marca tras las migraciones.

#### Verified
- RED contra `beb9434` y GREEN; 283 tests con 18 skipped en 28 módulos contra PostgreSQL desechable propio; arranques sin variables con 0 filas y 0 conexiones; el contenedor compartido de desarrollo no se tocó. Evidencia: `docs/evidence/mp-023/`. Pendiente: ejecución real en GitHub Actions.

### MP-024 — Propuesta de enmienda de ADR-0014 (rama `pedromaaz13/mp-024-adr-estado-parada`, sin fusionar)

Solo documentación y evidencia offline; **ningún cambio de código de producto**. ADR en estado `Propuesto`: no está aprobado ni implementado. Ejecutor Claude Opus 5.5 · high; revisor Codex `gpt-6.2-astra` · high: **sin dictamen APPROVED** (2 rondas con CHANGES_REQUESTED parcial; las correcciones finales no se re-verificaron).

#### Added
- `docs/adr/0014-amendment-stop-state.md` (alternativas A/B/C/D comparadas por pruebas, reglas, criterios de aceptación, decisión del propietario) y `docs/evidence/mp-024/` (arnés offline determinista, equivalencia Python↔TypeScript y resultados).

### Gobernanza documental y roadmap maestro (2026-11-25, rama `docs/governance-roadmap`, sin fusionar)

Solo documentación y mecanismo de seguimiento; **ningún cambio funcional**. La rama incorpora además dos commits de documentos de despliegue (`docs/deployment/*`, propuestas, procedentes de `docs/mvp-web-deployment`).

#### Added
- Fuentes recibidas incorporadas íntegras (cabecera de procedencia, cuerpo intacto verificado con `cmp`): `docs/plans/MVP_LIVE_END_TO_END.md` (propuesta), `docs/research/COMPARATIVE_ARCHITECTURE_2026-11-24.md`, `docs/design/DESIGN_DISCOVERY_A_B_C.md`, más `docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md`.
- `docs/README.md`, `docs/roadmap/{MILESTONES,RELEASE_ROADMAP,CROSSWALK}.md`, `docs/governance/{PROJECT_STATE.json,UPDATE_PROTOCOL.md}`.
- `scripts/governance/sync_docs.py` y `check_docs.py` con tests en `tests/governance/` y job `governance` en `.github/workflows/ci.yml` (resultado de CI: se registrará tras la ejecución real en GitHub Actions; hasta entonces solo ejecución local).

#### Changed
- `README.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/DEVELOPMENT.md` y `docs/deployment/MVP_RELEASE_CHECKLIST.md`: afirmaciones obsoletas corregidas o marcadas como históricas con notas de vigencia fechadas; el texto histórico se conserva. Otros documentos con texto previo al merge llevan su propia nota (`MVP_READINESS`, `HITO_3_BACKLOG`, `INTEGRATION_H3_VERIFIED`, `PREPUBLICATION_H3`, `DATA_MODEL`, `DATA_CONTRACTS`, `ORCHESTRATION_*`).

### MP-022 — Validación integral de cierre (`DONE`)

> *Histórico: entrada redactada antes del merge; MP-022 está integrada en `main` desde `7583ca5` (2026-11-24).*

Worktree `mp-022-validacion-integrada`, ramificado desde `mp-021-historico` (`1ecbc8f`). `DONE`: aprobada por Claude el `2026-11-23` tras dos rondas de revisión independiente. **Cierra la cadena completa `MP-016`→`MP-022` del Hito 3** — pendiente únicamente de la decisión del propietario sobre integración a `main` y promoción de ADR-0014/ADR-0015. Auditoría final sobre un entorno desechable propio. No añade features ni cambia arquitectura.

#### Added
- Generador reproducible `apps/api/tools/build_closure_matrix.py` y matriz CSV/Markdown con el esquema vinculante exacto: 12 líneas, 42 rutas, 103 patrones, 1 299 instancias con horario y denominadores explícitos. C4 conserva horario/catálogo con GPS 0 y cobertura `null`; 28/103 patrones map-matcheables, fallback raw/tablero declarado.
- Fixture `tests/fixtures/mp022_synthetic/`, marcada inequívocamente como sintética derivada, no oficial y no producción, más E2E de recuperación tras estimación, tres relojes/horizonte y excepción de calendario junto a 24:xx.
- Evidencia integral, benchmark y dossier de integración en `docs/evidence/mp-022-{validacion-integrada,benchmark,dossier-integracion}.md`.

#### Verified
- Replay congelado intacto: 1532 = 119/119/49; 1533 = 121/121/49. Cuatro snapshots normal/normal/parcial/congelado con revisión 3→6→7, conservación de 122 últimos conocidos y timestamps sin rejuvenecer.
- Archivo del 2026-11-20 reprocesado dos veces con los mismos 9 ficheros y SHA-256; base replay propia `240/199/4/7/2` y base de suite limpia al terminar.
- Workflow Python actualizado: 283/283 con 5 `skip` en `mp022-ci-db:5438`; la corrida independiente anterior del revisor sobre los 276 tests base dio 1 `skip` en su PostgreSQL fresco, diferencia de entorno/alcance conservada explícitamente. Frontend Node 22.13.1: 89/89, lint, typecheck y build; worker MapLibre 550754 bytes.
- Benchmark reproducible de 30 iteraciones: snapshot 254,73/418,23 ms p50/p95; tablero Atocha 103,14/179,75 ms; salud 75,23/83,14 ms. Se registra el endpoint legado lento y DEC-038 permanece abierta.
- Inspección nueva del frontend integrado: reduced-motion con deriva 0 en seis muestras; recorrido Live→History en desktop, móvil 390×844, teclado y fallback sin WebGL; interacción MapLibre con 182 frames/60,3 fps, p50/p95 16,70/18,30 ms y heap 96,2 MiB usado. El replay tenía 68,7 h y estaba congelado: la cifra mide zoom/pan, no animación continua de trenes.

#### Fixed
- `HistoryView` ya no sustituye silenciosamente un día URL no archivado por el primero disponible en encabezado y breadcrumb: muestra un estado explícito, conserva la fecha solicitada y ofrece los días reales como opciones. Frontend 89/89, typecheck y lint limpios.
- `.github/workflows/ci.yml` ejecuta ahora `apps.api.tests.test_closure_matrix` y `tests.e2e.test_mp022_synthetic_derived`; los siete tests de aceptación MP-022 dejan de quedar fuera del pipeline.

#### Verified (auditoría final de Claude, 2026-11-23)
- Inspección real en navegador que la sesión del ejecutor no pudo hacer (sin superficie de navegador, mismo límite de MP-020): gate 7 con `matchMedia` forzado a `reduce` antes de montar React (deriva 0 en seis muestras de centro/zoom mientras el reloj seguía avanzando); gate 8 con un recorrido real nuevo (Live → filtro C4a+C4b → tren 20277 → Seguir → arrastre sintético real del lienzo MapLibre → Volver al tren → History → Atrás, restaurando la URL exacta), móvil 390×844 real vía `emulate` (no resize), teclado (Tab+Enter) y sin WebGL vía `initScript`; gate 9 con `requestAnimationFrame` real (182 frames, 60,3 fps, p50 16,70 ms, p95 18,30 ms) y `performance.memory` (96,2 MiB).
- Dos hallazgos reales encontrados y devueltos al ejecutor, ambos corregidos y reverificados de forma independiente: la sustitución silenciosa de día en `HistoryView.tsx` (ver `Fixed`) y dos módulos de test nuevos (`apps.api.tests.test_closure_matrix`, `tests.e2e.test_mp022_synthetic_derived`) ausentes de `.github/workflows/ci.yml` pese a blindar las puertas 2/3/7 y el contrato de matriz de esta misma tarea.
- Reejecución propia, dos veces, contra contenedores PostgreSQL 17-3.5 desechables (puertos `5439`/`5440`, migraciones desde cero, destruidos al terminar): **283/283** tests Python con la lista de CI ya corregida, 1 `skip` real (`test_real_soak_postgres`). Frontend **89/89** con Node 22.13.1 real, lint/typecheck limpios, build con worker MapLibre de **550754 bytes** verificado. `git diff --check` limpio; autoría exclusiva de Pedro Matute sin `Co-authored-by` en los tres commits (`c745374`, `4d25658`, `23ec6c0`).

#### Not done (declarado explícitamente, decisión exclusiva del propietario)
- ADR-0014/0015 siguen `Propuesto`; DECs 033(b)/(c), 038 y 004 abiertas; no se afirma 24/7 ni trabajo de AV/LD/MD; ningún agente ha hecho `push`/PR/merge.

### MP-021 — Histórico y continuidad analítica

Worktree `mp-021-historico`, ramificado desde `mp-020-mapa-y-tablero` (`b616ae6`). `DONE`: aprobado por OpenAI Codex el `2026-11-23` tras dos rondas de revisión independiente; pendiente únicamente de la decisión del propietario sobre integración y promoción de ADR-0015.

#### Added
- **`circulation_daily_history`** (`services/snapshotter/history.py`): cuarto agregado gold, con grano **vehículo + viaje + día de servicio** — la misma identidad que publica `/api/v1/snapshot` y que lleva la URL del frontend. Los huecos de cobertura son **filas**, no ausencias, y la columna `coverage` los clasifica en una sola categoría (`observed` · `canceled` · `operator_only` · `unobserved` · `unscheduled`): una anulación del operador no es un hueco de captura, y una circulación observada fuera del calendario aparece con `scheduled = false` en vez de descartarse. Cada métrica va con el denominador que la sostiene.
- **`/api/v1/history/*`** (`apps/api/history.py`, 5 rutas nuevas): días archivados con sus denominadores, métricas por línea y por estación, circulaciones filtrables por línea y por cobertura (`only=unobserved` devuelve exactamente el hueco), y detalle de una circulación con sus observaciones crudas. Se sirven desde el Parquet con DuckDB en solo lectura; **el contrato de MP-019 no se toca**, y un test lo fija como regresión. Un día no archivado responde `404` con el comando que lo archivaría, nunca un día vacío con métricas a cero.
- **History y Explore navegables** (`apps/web/src/ui/HistoryView.tsx`, `ExploreView.tsx`, `hooks/useHistory.ts`, `domain/format.ts`): los botones de `TopBar.tsx` dejan de estar `disabled`. Ida y vuelta Live ↔ History conservando la identidad (`?train=&trip=&sd=` valen en ambas vistas), «Ver en Live» solo si esa circulación está de verdad en el snapshot vigente, y todo porcentaje con su fracción real (`5.6 % (4/72)`); sin muestra se escribe «sin muestra», nunca `0 %`. Sin SQL Lab, sin cuentas, sin dbt, sin infraestructura distribuida.
- **`infra/operate/`**: supervisor portable del colector con retroceso acotado, plantillas `launchd` (macOS) y `systemd` (Linux) para colector y archivo diario, script de archivo diario idempotente, y `measure-cost.py`, que **mide** una ventana real y extrapola marcando la extrapolación como tal.
- **`docs/evidence/mp-021-coste-colector-continuo.md`** y **`mp-021-medicion-coste.json`**: coste real medido sobre operación continua contra los feeds en vivo — 21 ciclos en 823 s sin errores de ingesta, RSS máximo 18,6 MB, 434 KB de bajada por ciclo, ≈631 B/fila en PostgreSQL y **≈48,9 B/fila en Parquet ZSTD** (≈19 MB/día proyectados, ≈7 GB/año). Es la medición que DEC-004 esperaba.
- **`docs/evidence/mp-021-inspeccion-navegador.md`** y `docs/evidence/mp-021-capturas/` (10 capturas): inspección real en navegador de History y Explore, escritorio y móvil 390 px, incluida la segunda ronda sobre anulaciones.
- 43 pruebas nuevas en la suite Python (`test_idempotency.py`, `test_history.py`, `test_history_contract.py`, `test_supervised_loop.py` y ampliaciones de `test_gold.py`) y 39 en la del cliente, estas últimas sobre una **grabación real** de la nueva API (`src/__fixtures__/history-archive.json`).

#### Fixed
- **El archivo frío no era idempotente, pese a lo que decía su docstring.** `OVERWRITE_OR_IGNORE` deja intactas las particiones que una nueva ejecución ya no produce: medido con DuckDB 2.0, tras escribir `hour=10` (3 filas) + `hour=11` (2 filas) y reprocesar con una sola fila, el archivo seguía devolviendo **3 filas**. `OVERWRITE` tampoco servía: borra la raíz entera — reexportar `2026-11-20` se llevó por delante el `date=2026-11-19` ya archivado. Ahora cada tabla se escribe en `.staging/` y su subárbol `date=<fecha>` se reemplaza apartando antes la versión anterior, y **un origen vacío nunca borra un día ya archivado** (la tabla caliente se purga por diseño, DEC-011: 0 filas calientes no prueba que el día no tuviera observaciones).
- **La sustitución del día no era atómica** (hallazgo bloqueante de la revisión de Codex). La primera versión hacía `rmtree(final)` y después `replace(staged, final)`: dos pasos con un agujero real en medio, porque una caída entre ambos dejaba el día **borrado sin reemplazo** — justo lo que ADR-0015/DEC-040 existen para impedir. Ahora la versión anterior se **aparta** a `.quarantine/` con un `rename` atómico, la preparada ocupa el nombre definitivo con otro, y solo entonces se borra la cuarentena; toda exportación empieza por `recover_interrupted_swaps`, que resuelve una interrupción anterior sin intervención. Se deja de afirmar atomicidad de un solo paso: `rename(2)` no la ofrece para directorios no vacíos y las alternativas que sí (enlace simbólico, `renameat2`/`renamex_np`) rompen el contrato de lectura de la capa gold o no son portables — ambas descartadas con su razón en el ADR. Lo que se garantiza es **a prueba de caídas con recuperación automática**, fijado con inyección de fallo en la costura exacta.
- **Tres «huecos de cobertura» del `2026-11-20` no lo eran** (segundo hallazgo bloqueante de Codex). `1023V20865C5`, `1023V21340C10` y `1023V21748C2` salían como `scheduled=true/observed=false` con `trip_updates_count=1` y `delay_reported_count=0`, contradiciendo el criterio «huecos con métricas NULL, nunca 0» que esta misma entrega daba por cumplido. Rastreado al dato crudo: los tres tienen una `trip_update_observation` real con `schedule_relationship='CANCELED'` y cero posiciones — **Renfe había anulado esos servicios**. El tren no circuló y el operador lo dijo, así que contarlos como hueco culpaba al colector de algo que no hizo; además `apps/api/snapshot.py` ya trataba la cancelación como ciudadana de primera desde MP-019 (ETA `trip_canceled`) mientras este mart la ignoraba. Corregido con `coverage`/`canceled`, Parquet regenerado y documentación alineada con el comportamiento real: el día cierra como `1304 = 122 observadas + 1179 huecos reales + 3 anuladas` y de los 1 179 huecos ninguno tiene métricas no nulas.
- **El filtro de cobertura de la URL caía en silencio a «Todas»** al pedir las categorías nuevas: la lista blanca en tiempo de ejecución de `hooks/useUrlState.ts` se quedó con las cuatro antiguas. Encontrado al re-verificar en navegador; `?hf=canceled` mostraba 120 filas en vez de 3.
- **Los agregados no eran byte-estables.** Mismo conjunto de filas al recalcularlos, distinto **orden**: sobre el catálogo Madrid completo del `2026-11-20` (35 filas de línea, 69 de estación) dos corridas con la misma entrada daban SHA-256 distintos, porque el `GROUP BY` paralelo de DuckDB no garantiza orden. Los cuatro marts llevan ahora `ORDER BY` explícito.
- **Límite (a) de DEC-033 cerrado:** `gold.py` reimplementaba el calendario GTFS a mano y solo leía `calendar.txt`, así que una excepción de `calendar_dates.txt` no cambiaba `trips_scheduled` — el **denominador** de toda métrica de puntualidad. Ahora lo resuelve `packages.gtfs.scheduled_service_ids_for_date` (MP-017), la misma función que usa el tablero de estación.
- **El mart no podía cubrir Madrid entero:** `SnapshotterConfig` fijaba `short_name="C5"`. `line_filter` interpreta el valor vacío como núcleo completo, igual que ya hacía `apps/api/gtfs_source.py`: 42 rutas y 12 líneas reales en vez de una.
- **El mismo día tenía dos denominadores distintos** (1304 en una tabla, 1299 en otra). Causa: 5 viajes huérfanos reales del ZIP oficial del `2026-11-20` (`1023V17120C8b`, `1023V17128C8b`, `1023V17130C8b`, `1023V17134C8b`, `1023V17707C5`) que `daily_line_metrics` contaba y el mart por circulación descartaba. Ahora se conservan como filas con el horario explícitamente ausente.
- **El colector sobrevivía a perder la base sin volver a ingerir nunca** (DEC-041). Reproducido reiniciando PostgreSQL con el colector en marcha: 90 s después el proceso seguía vivo consumiendo los tres feeds cada 30 s y descartándolos, con `source_ingestion_run` congelado y `psycopg.OperationalError: the connection is lost` en cada ciclo; ningún supervisor puede rescatar un proceso que no cae. Ahora termina con `EX_TEMPFAIL` (75) y el supervisor lo levanta con una conexión nueva: verificado, la ingesta se reanuda (48 → 51 ejecuciones).
- **Rótulo del tren seleccionado fijado en «Sin línea»** al abrir un enlace con circulación ya seleccionada (el caso normal al volver desde el histórico): `MapView` leía un índice que su efecto poblador deja vacío mientras el mapa no está listo, y sus dependencias no volvían a cambiar. Defecto encontrado mirando el navegador, no por un test.
- **Media pantalla en blanco en móvil** en las vistas de archivo: la rejilla móvil reservaba el 54 % para un mapa que esas vistas no dibujan.

#### Verified
- Idempotencia probada **contra PostgreSQL real**, no por lectura de código: exportar + agregar dos veces produce un archivo byte-idéntico; una fila borrada del origen no sobrevive; reprocesar un día no toca otro ya archivado; un origen vacío conserva el archivo. Las mismas pruebas contra el `export.py` anterior fallan con el síntoma exacto.
- **Inyección de fallo en la costura exacta de la sustitución**: con `Path.replace` instrumentado para caer justo antes del segundo renombrado, el día ya archivado sobrevive **byte a byte** (se compara ruta + SHA-256 de cada Parquet antes de la caída y tras la recuperación), un reintento posterior deja el día completo, y una caída después del segundo renombrado conserva el contenido nuevo en vez de retroceder. Verificado contra el mecanismo anterior: falla con `la versión anterior no está en cuarentena: se ha perdido`.
- **Semántica de cobertura comprobada sobre los 1 179 huecos completos** del `2026-11-20`, no sobre una muestra: ninguno es una anulación y ninguno tiene métricas no nulas. El caso `operator_only` (parte del operador sin cancelar y sin posición) no existe en el archivo actual, así que se cubre con un test sintético explícito en vez de declararlo verificado sobre datos que no hay.
- Recuperación del colector verificada **provocando los fallos**: `kill -9` (reinicio en 5 s) y reinicio de PostgreSQL (salida 75 y reanudación).
- Suite Python exacta de CI: **276/276 OK** contra PostgreSQL real (233 → 276), con los recuentos de la base de desarrollo intactos en `668/484/3/120/0`. Frontend con Node **22.13.1**: lint, typecheck, **88/88** pruebas (49 → 88) y build en verde con el worker de MapLibre verificado (550754 bytes).
- Revisión final independiente de OpenAI Codex sobre `d68b351`, sin hallazgos abiertos: 36 pruebas focales de idempotencia/caídas/cobertura/API; suite completa **276/276** contra desarrollo y 276 con 5 `skip` esperados sobre PostGIS fresco; Parquet real `1304 = 122 observadas + 1179 huecos + 3 anuladas`; navegación real de History/Explore y emulación exacta `390x844` sin desbordamiento de página (`scrollWidth == clientWidth == 390`). `git diff --check`, autoría exclusiva de Pedro Matute y ausencia de coautores verificados. Estado final: `DONE`, aprobado el 2026-11-23; ADR-0015 permanece `Propuesto`.

#### Not done (declarado explícitamente)
- **No hay operación «24/7 verificada»**, y no se afirma: la ventana medida son 13 min 43 s y todas las cifras de 24/72 h están marcadas como proyección.
- **No se ha contratado ningún servicio de pago ni desplegado ningún host persistente** (ADR-0007 reserva esa decisión al propietario), ni se ha instalado el agente `launchd` en el equipo del propietario.
- **Límites (b) y (c) de DEC-033 siguen abiertos:** el umbral de puntualidad de 300 s no tiene todavía histórico con el que calibrarse —dos días archivados y minutos de cobertura no son base, y fijarlo con esa muestra sería fabricar una calibración— y `data_quality_event.entity_ref` sigue sin referenciar nunca una parada.

### MP-020 — Mapa y tablero (React/MapLibre)

#### Added
- `apps/web/` reconstruido como experiencia map-first de **toda Cercanías Madrid** sobre el contrato de MP-019 (`/api/v1/catalog` + `/api/v1/snapshot` + `/api/v1/stations/{id}/board`), sustituyendo en la UI los endpoints antiguos `/lines` + `/live/vehicles` de MP-014, que siguen existiendo por compatibilidad. `App.tsx` queda como composición; la lógica vive en `src/api/`, `src/domain/`, `src/hooks/`, `src/map/` y `src/ui/`.
- Adquisición por recurso (`useCatalog`, `useSnapshot`, `useHealth`, `useStationBoard` sobre `useResource`): una lectura en vuelo por recurso, timeout y cancelación propios, descarte de respuestas antiguas por `revision`, catálogo revalidado con `ETag`/`304`, y pausa/revalidación según la visibilidad de la pestaña. Sin `Promise.all` como bloque indivisible de éxito; un fallo parcial conserva el último valor bueno y una respuesta con éxito no rejuvenece el dato.
- Evaluación en el cliente de la `ProgressEnvelope` publicada por el backend, con conversión de progreso dirigido a longitud de arco física y proyección sobre la polilínea del patrón; nunca interpolación lat/lon en recta entre estaciones, y congelación al agotarse `rendered.valid_until`. El sentido se deriva del orden real de las paradas sobre el corredor, no de una convención de nombre.
- Reloj de presentación en `requestAnimationFrame` que escribe directamente en las fuentes de MapLibre: ningún `setState` global por fotograma. Una sola instancia de mapa, con marcadores reconciliados por identidad de circulación (vehículo + viaje + día de servicio, nunca `vehicle_id` solo).
- Anillo de la **última lectura confirmada** junto al símbolo cuando la posición mostrada es `extrapolated_from_last_anchor` o `stale_frozen`.
- Seguimiento explícito separado de la selección: arrastrar suelta la cámara conservando la ficha y ofrece «Volver al tren». La cámara no hace `fitBounds` por sondeo y «Centrar Madrid» responde una sola vez por pulsación.
- Búsqueda de estación y línea con y sin tilde y teclado completo (flechas, Intro, Escape), multiselección de líneas con contadores del mismo ámbito que el mapa, tablero de estación con cobertura y limitaciones declaradas, y cinta de novedades progresiva, pausable y con lista estática alternativa.
- Estado restaurable en la URL (`?station=`, `?train=&trip=&sd=`, `?lines=`) con `pushState`, de modo que Atrás vuelve al contexto anterior; y modo replay `?at=<ISO>` que recorre un corte congelado de forma repetible con la etiqueta `REPLAY` y el instante siempre visibles.
- Alternativa navegable de lista y tablero cuando el navegador no ofrece WebGL, y comportamiento sin animación espacial automática con `prefers-reduced-motion`.
- 49 pruebas nuevas en `apps/web` apoyadas en una grabación real de esta API (`src/__fixtures__/snapshot-map-matched.json`, con su procedencia declarada dentro del fichero), incluida la que comprueba que la coordenada calculada por el cliente cae sobre `rendered.lat/lon` del backend con error inferior a 1 m.
- `docs/evidence/mp-020-inspeccion-navegador.md` y `docs/evidence/mp-020-capturas/`: evidencia ejecutada de la inspección real en navegador, con la secuencia continua de 60 s de la app real.
- `vite.config.ts` acepta `MADRID_PULSE_API_TARGET` para apuntar el proxy `/api` a otro puerto cuando el 8000 ya está ocupado por otra instancia local; el valor por defecto no cambia.

#### Fixed
- **Mapa invisible en el navegador, invisible también para los tests:** el chunk diferido de `maplibre-gl.css` carga después de la hoja propia y su `.maplibregl-map { position: relative }` ganaba por igual especificidad y orden al `position: absolute` del contenedor, que quedaba con altura 0. Se dimensiona ahora con `width`/`height`, correcto sea cual sea el `position` aplicado.
- **`snapshot_id` no puede usarse como señal de «ha llegado dato nuevo»:** es identidad de contenido y se repite entre sondeos cuando los vehículos no han cambiado, aunque `display_at` avance; usarlo como disparador de repintado dejaba el mapa congelado con movimiento reducido. La señal es la `revision` del contrato.
- «Volver al tren» no aparecía nunca tras soltar la cámara: el estado se escribía dentro del actualizador de `setFollowKey`, que debe ser puro.
- Scroll horizontal en móvil de 390 px (449 px de ancho real) por la barra superior; cinta de novedades de 120 px de alto; leyenda pegada a la barra de atribución; y controles pequeños por debajo del tamaño táctil cómodo.
- El tablero volcaba códigos crudos del contrato (`passed_or_skipped_per_operator_next_stop`) en la interfaz; los cuatro códigos de causa se traducen y se conserva el horario planificado cuando la ETA no está disponible.
- Los nombres de las estaciones de un patrón se solapaban al estar alejado el zoom, y la ficha heredaba el desplazamiento del tablero anterior abriendo con su cabecera fuera de la vista.

#### Notes
- El GTFS oficial publica `route_color` real de Renfe, pero `/api/v1/catalog` no expone ese campo y MP-020 no reescribe el contrato de MP-019: la paleta de líneas del cliente es una elección de presentación propia, determinista por `line_id` y sin identificadores de línea incrustados en la lógica (ADR-0011), **no** el color corporativo del operador. Anotado para MP-021/MP-022.
- Histórico y Explore no se implementan aquí (son MP-021): sus pestañas aparecen deshabilitadas y lo declaran, en vez de simular una función inexistente.

#### Verified
- Revisión final de OpenAI Codex sobre `74667c0..5f8b739`, sin hallazgos abiertos. Inspección visual real reproducida en Chrome DevTools desde la sesión coordinadora de Orca contra API `8010` + Vite `5181`: red completa, varias líneas, circulación C5 `19656`, URL restaurable, seguimiento, degradación honesta y móvil `390x844`; sin errores de aplicación en consola. El arrastre y `prefers-reduced-motion`, no disponibles en esa herramienta concreta, quedaron cubiertos por la evidencia ejecutada del implementador, tests de regresión y auditoría directa del código.
- Frontend con Node **22.13.1**: `npm ci` sin vulnerabilidades, lint, typecheck, **49/49 tests** y build en verde con worker MapLibre verificado (550754 bytes). Backend exacto de CI: **233/233** sin `skip` contra desarrollo con `668/484/3/120/0` intactos; 233 ejecutados con 5 `skip` esperados sobre PostGIS fresco tras aplicar `0001`+`0002`.
- `git diff --check` limpio; los cinco commits de MP-020 tienen autor y committer exclusivos de Pedro Matute, sin `Co-authored-by`. Estado final: `DONE`, aprobado por OpenAI Codex el 2026-11-22.

### MP-019 — Contrato de snapshot/API coherente

#### Added
- [ADR-0014](adr/0014-snapshot-and-temporal-contract.md) (`Propuesto`): contrato temporal de presentación y snapshot coherente, con las tres alternativas del encargo comparadas y dos más evaluadas y descartadas. Escrito **antes** de implementar, como exige `docs/hitos/hito-03/MEJORAS-PRODUCTO-VALIDADAS.md`.
- `packages/movement/rendering.py`: capa `rendered` con los seis `rendering_method` del anexo (`anchor`, `interpolated_between_known_anchors`, `extrapolated_from_last_anchor`, `schedule_only`, `stale_frozen`, `unlocated`), `ProgressEnvelope` compacta (una sola expresión monótona y acotada, sin array de puntos futuros) y los instantes separados `calculated_at`/`display_at`/`valid_until`/`last_confirmed_at`. Extiende `packages/movement` (MP-012); no lo duplica.
- `MovementPosition.anchor_progress_m` (aditivo, por defecto `None`): progreso del ancla realmente usada, para construir la envolvente sin recalcular el map-matching.
- `MovementEngine(schedule_cache=...)` opcional e inyectable, y `TripSchedule.dwell_end_seconds`. `build_trip_schedule` emite llegada **y** salida cuando difieren, de modo que las esperas reales del horario (11 paradas en la fixture C5, p. ej. 60 s en Madrid-Atocha) dejan de absorberse y el contrato puede declarar `dwell_until`.
- `GET /api/v1/catalog`: catálogo cacheable versionado por `gtfs_version` + `geometry_catalog_version`, con `ETag`/`304`, geometría física publicada una sola vez y referenciada por patrón, y cobertura `validated`/`partial`/`pending` explícita.
- `GET /api/v1/snapshot`: snapshot operativo ligero con `raw`/`map_matched`/`rendered` separados, `snapshot_id` de identidad de contenido declarado **no ordenable** y bloque `revision` (`scope`/`scope_source`/`sequence`/`generated_at`/`tiebreak`) monotónico solo dentro de su ámbito, degradación por recurso y `Cache-Control: no-store`.
- `GET /api/v1/stations/{station_id}/board`: tablero calculado con `scheduled_trip_instances_for_date` (calendario + excepciones + `stop_times`, `24:xx` incluidas) cruzado con `trip_update` y observaciones; nunca por proximidad geográfica. ETA con procedencia (`schedule` / `operator_delay_on_schedule` / `unavailable` con causa) y aproximación declarada al propagar un retraso de nivel viaje.
- `apps/api/db.py`: `latest_trip_updates` y `vehicles_for_trips` por lote, `revision_marker` con ámbito del clúster, y `feed_published_at` por observación (quinto timestamp del anexo).
- `CorridorCatalog.coverage_for_stops` en `packages/geo`: resuelve el patrón de una circulación viva sin lanzar cuando el GTFS cargado no lo contiene.
- Migración `0002_api_batch_indexes`: tres índices medidos con `EXPLAIN (ANALYZE, BUFFERS)`; solo estructuras de acceso, sin cambios de datos ni de semántica.
- Herramientas reproducibles `apps.api.tools.bench_snapshot` y `apps.api.tools.replay_three_snapshots`; evidencia en `docs/evidence/mp-019-explain-y-bench.md` y `docs/evidence/mp-019-tres-snapshots-replay.md`.
- `apps.api.tests.test_snapshot_contract` (36 tests) y `packages.movement.tests.test_rendering` (17 tests), ambos añadidos a `.github/workflows/ci.yml`.
- `counts` del snapshot publica dos particiones independientes y exactas de `vehicles_total` (`by_rendering_method` y `by_coordinate_space`) en vez de contadores que mezclaban método y espacio de coordenada; cada diccionario suma el total y hay test de esa invariante.

#### Fixed
- **N+1 real eliminado:** `service.list_vehicles` hacía una consulta `latest_trip_update` por vehículo (24 con el soak de MP-007, una por circulación en operación). Ahora son dos consultas fijas, y un test cuenta los `execute` reales para impedir la regresión.
- `latest_vehicle_histories` aplica el filtro `rank <= 2` en SQL en vez de traer toda la tabla a Python, y publica `feed_published_at` con un `JOIN` a `source_ingestion_run`.
- `recent_ingestion_runs` usa `LATERAL ... LIMIT` por feed en vez de rankear el histórico completo.
- `/api/v1/catalog` memoiza su payload serializado por `catalog_version`: medido **122,67 ms → 0,40 ms** de p50 (no consultaba PostgreSQL; el coste era reserializar el mismo payload inmutable en cada petición).
- `MADRID_PULSE_SHORT_NAME` vacío carga el núcleo completo (42 `route_id` / 12 líneas / 103 patrones) en vez de una sola línea; el filtro por línea sigue siendo configuración, nunca un literal (ADR-0011).

#### Findings
- Existía un índice `vehicle_position_observation_trip_observed_at_idx` sobre la clave ajena `trip_id` (bigint) que **el colector no puebla**: no servía para consultar por `source_trip_id`, y la consulta del tablero resolvía con `Seq Scan` pese al nombre parecido.
- El coste dominante de cada petición no era la consulta sino **abrir la conexión**: `~66 ms` de los `68,91 ms` de p50 de `/api/v1/health`. Queda abierto y documentado (un pool es dependencia nueva y decisión del propietario), con ambas columnas medidas en la evidencia.
- Ninguno de los 24 `source_trip_id` del soak de MP-007 (`2026-11-19`) resuelve contra el ZIP GTFS del kit (`2026-11-20`): Renfe regenera los `trip_id` entre publicaciones. Por eso la evidencia de `map_matched`/`rendered` con datos reales se produjo con las capturas `1532`/`1533`, de la misma fecha que ese ZIP.
- Con las capturas reales, **44 de 119** circulaciones de Madrid obtienen coordenada `map_matched`; las otras 75 publican GPS bruto etiquetado porque solo 28 de los 103 patrones tienen corredor validado tras MP-018. Ninguna se oculta ni se proyecta sobre un corredor ajeno.
- El `stop_time_update` por parada no está persistido en el modelo canónico (solo `next_stop_id`), así que no existe evidencia directa de `SKIPPED` por parada. El tablero lo declara en `limitations` y expone `operator_next_stop_id` con la posición relativa, sin afirmar que una parada fue omitida.

#### Fixed after independent review (first round)
- **Hallazgo 1 de Codex — aritmética DST:** `service_instant` sumaba los segundos del día de servicio **después** de convertir la medianoche a UTC, es decir sobre un desplazamiento fijo, así que desplazaba una hora los horarios de los dos días de cambio de hora (`2026-03-29`: `03:30+02` se reconstruía como `04:30+02`; `2026-10-25`: como `02:30+01`). Causa raíz: `service_seconds` restaba dos `datetime` *aware* con el mismo `tzinfo`, caso que Python resuelve de forma naive, de modo que era aritmética de reloj de pared y acertaba *por accidente*; la inversa eligió sin saberlo otro modelo temporal. Corregido con una sola implementación explícita en ambas direcciones (`service_seconds` / `service_day_instant` en `packages/movement/schedule.py`), a la que `apps/api/snapshot.py` delega. Casos límite declarados, no omitidos: hora inexistente del adelanto resuelta con el desplazamiento previo (el feed real no publica ninguna hora en esa franja: 0 valores en `02:xx`/`26:xx` sobre 3,5 M de `stop_times`) y hora ambigua del atraso resuelta en su primera ocurrencia.
- **Hallazgo 2 de Codex — viajes `24:xx` tras medianoche:** la fecha de servicio se elegía por reloj civil, así que a las `00:02` un viaje real del día anterior con paradas a las `24:00`/`24:05` se resolvía contra el día siguiente: `service_seconds` pasaba de 86 520 a 120 y el motor situaba el tren a **10,4 km** de su posición real, además de marcarlo `expired`. No es marginal: 742 circulaciones del núcleo Madrid tienen horas `24:xx` en el ZIP oficial. Corregido con `ServiceDateResolver`, que resuelve la fecha **por circulación** dentro de una ventana derivada del horizonte de horas extendidas del propio feed (3 180 s con el ZIP real, `0.0` sin horas extendidas), admitiendo un día candidato solo si el `service_id` está programado en él y el instante cae dentro del horario publicado del viaje. La fecha resuelta gobierna posición y `circulation_status`; el snapshot publica `service_date` por circulación y el tablero cruza los dos días candidatos con `service_date` por entrada y `service_dates_considered`.
- Fixture real nueva `tests/fixtures/gtfs_24h_real/` (dos circulaciones del ZIP oficial con horas `24:xx`: una con corredor OSM `validated` y otra sin geometría) más la herramienta genérica `packages.gtfs.tools.extract_trips_fixture`. Se añade **aparte** en vez de ampliar `gtfs_c5_real`, cuyo SHA-256 sostiene la matriz de cobertura ya aprobada de MP-018 y varias aserciones de MP-010/MP-017. Registrada en `docs/legal/ATTRIBUTION.md` y `docs/legal/DATA_SOURCES.md`, con manifiesto propio.
- Regresiones añadidas (16): barrido de ida y vuelta minuto a minuto de 00:00 a 28:00 en las dos fechas DST de 2026, sus vísperas y un día normal; y el escenario post-medianoche con los dos viajes `24:xx` reales (progreso correcto > 12 km frente a < 100 m con la fecha civil, > 10 km de separación; tablero con las llamadas `24:00`/`24:05` y su instante absoluto; cierre de la ventana a las 02:00; sin duplicación entre días candidatos; sin fabricar pertenencia cuando el servicio no está programado).

#### Fixed after independent review (second round)
- **Hallazgo 3 de Codex — la ventana del tablero no determinaba sus días de servicio:** `build_station_board` derivaba sus días candidatos de `resolver.candidates`, calculado con `now`, así que al rebasar el horizonte de horas extendidas dejaba de consultar el día anterior aunque `lookback_s` todavía lo cubriera. Con `tests/fixtures/gtfs_24h_real/`, estación `17000` y `lookback_s=600`, la llamada real de las `24:32` (las `00:32` en reloj de pared) aparecía a las `00:32` y **desaparecía a las `00:33`**, un minuto después de ocurrir; reproducido también contra el ZIP completo con `1023V21644C2` (llamada `24:53`, estación `70200`), presente a las `00:53` y ausente a las `00:54`. **El mismo error existía en el sentido contrario y no estaba en el informe:** a las `23:55` el tablero no consideraba el día de servicio siguiente, de modo que perdía `1024S27997C5` (salida `00:01` del día 21) aunque estuviera a seis minutos dentro de `lookahead_s`. Corregido con `service_dates_covering(start, end, extended_horizon_s)`, que devuelve los días cuyo tramo `[medianoche local, +24 h + horizonte]` intersecta la ventana; el tablero la llama con `window_start`/`window_end` y `ServiceDateResolver` con la ventana degenerada `[now, now]`, conservando exactamente su comportamiento para resolver la fecha de una circulación. Los límites se calculan con `service_day_instant`, así que la cobertura también es correcta en los días de cambio de hora. Ahora el límite es la **ventana pedida**: la llamada se ve de `00:31` a `00:42` y desaparece en `00:43`.
- Regresiones añadidas (11): `BoardWindowCoversItsCandidateServiceDaysTests` (el minuto exacto del hallazgo, la supervivencia minuto a minuto hasta el borde real de la ventana, una ventana más corta que la descarta antes, el lado simétrico hacia delante con entradas reales y el orden por instante absoluto al mezclar días) y `ServiceDatesCoveringTests` sobre la función pura (equivalencia con el resolver en ventana degenerada, bordes de `lookback`/`lookahead`, feed sin horas extendidas, ventanas invertidas y las dos fechas DST). Comprobado que fallan con el cálculo anterior (13 fallos) y pasan con la corrección.

#### Verified
- Suite Python exacta de CI (con los dos módulos nuevos y las 27 regresiones de las dos rondas de corrección): **233/233 OK sin ningún `skip`** contra la base de desarrollo real; recuentos `668/484/3/120/0` idénticos antes y después, soak intacto (`rows=668`, `near_corridor=177`, `after=668`). Evolución: 206 en la primera entrega → 222 tras la primera ronda → 233 tras la segunda.
- Misma suite contra un contenedor PostgreSQL **fresco y desechable** con `0001` + `0002` aplicadas desde cero: **233 ejecutados, OK con 5 `skip` explícitos** (los del soak irrepetible de MP-007, DEC-035).
- Frontend con **Node `22.13.1`**, la versión que fija CI (la primera entrega se verificó con `20.20.0`; hallazgo de proceso de la auditoría): `npm ci` sin vulnerabilidades, lint, typecheck, **5/5 tests** y build en verde (worker MapLibre `550754` bytes, idéntico a MP-018).
- Tres snapshots reales (normal/parcial/congelado) sobre las capturas `1532`/`1533` con reloj controlado: 119 y 121 vehículos de Madrid ingeridos, 13 circulaciones map-matcheadas con avance real entre capturas, revisión monotónica `3 → 6 → 7` dentro del mismo ámbito, fallo parcial que degrada solo `delays_and_eta` sin vaciar vehículos ni rejuvenecer el GPS, y congelado que conserva el último dato válido con `revision.sequence` detenida.
- `EXPLAIN (ANALYZE, BUFFERS)` de las cuatro consultas de lectura y p50/p95 con equipo y dataset documentados, en dos datasets (fixture C5 y núcleo Madrid completo).
- Revisión final independiente de OpenAI Codex sobre `60a6eb3`: reproducción propia con el ZIP completo de los bordes hacia atrás (`1023V21644C2`, visible hasta `01:03` y fuera a `01:04`) y hacia delante (`1024S27997C5`, incluido a las `23:55` con salida `00:01`), orden absoluto entre días, 11 tests focales, 233/233 sin `skip` en desarrollo, 233 con 5 `skip` en PostGIS fresco, frontend Node `22.13.1` y replay con siete invariantes. Diff y autoría limpios; sin hallazgos abiertos.
- Estado final: `DONE`, aprobado por OpenAI Codex el 2026-11-22. ADR-0014 permanece `Propuesto` para decisión del propietario.

### MP-018 — Corredores ferroviarios por patrón y sentido

#### Added
- `packages/geo/catalog.py` y `madrid.py`: catálogo de `Corridor` por patrón GTFS ordenado/sentido, con identidad estable, versión OSM por SHA-256 y matriz `validated`/`partial`/`pending`. La secuencia de paradas representa el sentido porque el GTFS real no publica `direction_id`; no se fabrica ese dato.
- Contrato geométrico mínimo `PositionMatch`: raw conservado, `Projection`, `progress_m`, `geometry_version` y `distance_from_raw_m` para corredores validados; fallback explícito `raw` o `unlocated` sin unir huecos ni proyectar sobre geometría no fiable.
- Fixture real C4 (`11332`, `9174510`, `9174511`) con manifiesto ODbL, atribución, checksums y comandos reproducibles. C4a queda verificada en ambos sentidos; C4b Colmenar→Parla, en el sentido descargado.
- Matriz versionada `docs/evidence/mp-018-corridor-coverage.csv` (103 patrones/12 líneas): 28 `validated`, 3 `partial`, 72 `pending`; exportador reproducible `packages.geo.tools.export_madrid_catalog`.
- `packages.geo.tests.test_catalog` añadido a CI: verifica checksums/continuidad incluso sin el ZIP GTFS no versionado y, cuando está presente, cobertura total, dirección, C4, vía compartida, casos problemáticos, CSV y raw→matched.

#### Findings
- C4a Alcobendas→Parla (`9174510`) y C4b Colmenar→Parla (`9174511`) comparten 77 IDs literales de `way` ferroviario OSM: tramo físico compartido confirmado, no inferido solo por estaciones.
- Dos variantes C5 de 7 paradas permanecen `partial` por la ambigüedad DEC-025; una variante C4b de 14 paradas omite Nuevos Ministerios entre Chamartín y Sol y también queda `partial`.
- Overpass respondió `502 Bad Gateway` dos veces al pedir C4b Parla→Colmenar (`9174512`); ese sentido queda `pending`, sin convertir indisponibilidad del endpoint en ausencia de dato.

#### Verified
- Suite Python exacta de CI: **153/153 OK** contra PostgreSQL real; recuentos antes/después `668/484/3/120/0`. Frontend con Node `22.13.1`: lint, typecheck, **5/5 tests** y build en verde. `compileall` y `git diff --check` limpios.
- Estado entregado: `REVIEW`; pendiente aprobación independiente de Claude Code antes de `DONE`.

#### Fixed after independent review (first round)
- La fixture derivada ODbL `tests/fixtures/osm_c4_real/` ya estaba licenciada,
  atribuida y reproducible en su propio manifiesto, pero los registros legales
  centrales aún nombraban solo C5. `docs/legal/ATTRIBUTION.md`, la fila
  `osm.rail_geometry` de `docs/legal/DATA_SOURCES.md` y DEC-024 ahora cubren
  explícitamente las relaciones C4a/C4b `11332`/`9174510`/`9174511` bajo la
  misma decisión ODbL; MP-018 permanece en `REVIEW` hasta re-verificación.

#### Approved
- Claude Code aprobó MP-018 como `DONE` el `2026-11-22` tras dos rondas de
  revisión en el mismo worktree. Único hallazgo (registro legal de la base
  derivada ODbL C4 ausente de `ATTRIBUTION.md`/`DATA_SOURCES.md`/DEC-024)
  corregido en `1b19df8` sin cambio de código y re-verificado: delta
  exclusivamente documental, los tres registros coherentes con la vara de la
  entrada C5 original, `ref`/`network`/`official_ref` de las tres relaciones
  comprobados contra las propias fixtures, suite **153/153 OK sin `skip`**
  contra desarrollo con recuentos `668/484/3/120/0` intactos y
  `git diff --check` limpio en todo `47f2732..1b19df8`. Sin hallazgos abiertos;
  las dos notas no bloqueantes quedan como pendientes explícitas de MP-019.

### MP-017 — Catálogo completo de Madrid

#### Added
- `packages/gtfs/catalog.py` (nuevo): `build_catalog` agrupa el GTFS completo del núcleo Madrid por línea/variante/patrón (verificado: 42 `route_id` → 12 líneas reales, conservando líneas sin patrones válidos u observaciones). `scheduled_service_ids_for_date`/`scheduled_trip_instances_for_date` enumeran explícitamente los servicios programados aplicando `calendar.txt` + `calendar_dates.txt` (soporte nuevo y opcional en `packages/gtfs/parser.py` — el ZIP oficial real no incluye este fichero hoy, verificado empíricamente, no asumido).
- Avisos por estación (`stopId` sin `routeId`) resueltos contra el catálogo real de paradas de Madrid: `RawInformedEntity.stop_id`, `ServiceAlert.affected_stop_ids`, `services/collector/collector.py::_persist_alerts(madrid_stop_ids=...)`, cargado una vez al arrancar el colector desde `MADRID_PULSE_GTFS_SOURCE`.
- `packages/gtfs/tests/test_catalog.py` (10 tests): 6 síncronos (topología sintética) + 4 gateados por la presencia del ZIP oficial completo (`skip` explícito si no está).

#### Fixed
- **Hallazgo real:** `apps/api/db.latest_trip_update` no acotaba por tiempo — un `trip_id` GTFS recurrente podía devolver el retraso de un día de servicio anterior como "el más reciente" hasta que llegara una observación de hoy. Añadida ventana de recencia (`observed_after`, 20h desde `apps/api/service.py`).
- Avisos por estación (ej. `AVISO_527127`, `stopId=60104`, Valdemoro — hallazgo P1 de `docs/hitos/hito-03/referencia/01-auditoria-live.md`) se descartaban silenciosamente como "fuera de alcance" por no tener `routeId`.

#### Verified
- Suite completa (+`packages.gtfs.tests.test_catalog`) contra la base de desarrollo real: 138/138 OK, `668/484/3/120/0` intacto. Contra un segundo PostgreSQL fresco desechable con `data/` ausente (simulando CI real, sin el ZIP oficial): 138 tests, 9 `skip` (5 del soak de MP-007 + 4 de `test_catalog` gateados), ninguno inesperado.

#### Fixed after Codex review (first round)
- **Versión/procedencia e identidad red/operador ausentes** (hallazgo real contra `PLAN-Y-ACEPTACION.md`/`MATRIZ-CIERRE-MADRID.md`): `Catalog`/`LineVariant`/`ScheduledTripInstance` no llevaban esos campos. `Catalog.gtfs_version: str` ahora obligatorio (mismo identificador que `/api/v1/health`); `ScheduledTripInstance.network_id`/`operator` añadidos.
- **Sin "estado activo separado de último histórico"**: `latest_vehicle_histories`/`list_vehicles` seguían devolviendo todo vehículo histórico sin cota; la ventana de 20h solo afectaba a `trip_update_observation`. Nuevo `VehicleOut.circulation_status` (`active`/`expired`/`unresolved`), comparando el `service_id` real del vehículo contra `scheduled_service_ids_for_date`.

#### Verified (second round)
- 3 tests nuevos (provenance/identidad real del catálogo; `circulation_status` activo/caducado/sin resolver). Suite completa: 141/141 contra desarrollo (`668/484/3/120/0` intacto), 141 tests/10 `skip` contra un segundo contenedor fresco con `data/` ausente. `git diff --check` limpio.

#### Fixed after Codex review (second round)
- **Contrato OpenAPI desincronizado:** añadir `VehicleOut.circulation_status` cambió la forma real de `app.openapi()` sin regenerar `apps/api/openapi.json`, dejando también `apps/web/src/types.ts` y el ejemplo de `docs/DATA_CONTRACTS.md` con el contrato anterior. Regenerado el JSON congelado (comando documentado en `apps/api/README.md`); sincronizados `types.ts` y `DATA_CONTRACTS.md`. Añadido `test_committed_openapi_json_matches_the_live_schema` (regresión permanente contra este tipo de drift).

#### Verified (third round)
- 142/142 contra desarrollo (`668/484/3/120/0` intacto); frontend lint/typecheck/5 tests/build en verde. `git diff --check` limpio.

#### Approved
- Codex aprobó MP-017 como `DONE` tras tres rondas (versión/procedencia e identidad red/operador; estado activo/caducado de circulación; sincronización OpenAPI/frontend), todas corregidas y re-verificadas. Sin hallazgos abiertos.

### MP-016 — Fiabilidad realtime

#### Added
- Modos locales explícitos `MADRID_PULSE_MODE=live|replay`; Live rechaza fixtures y GTFS fuera de vigencia. `/api/v1/health` publica modo, SHA-256 y vigencia del catálogo.
- `poll_age_s` separa edad del sondeo/colector de `data_age_s` (edad de la cabecera fuente), manteniendo salud independiente para posiciones, actualizaciones y avisos.
- Regresiones para `SKIPPED` sin `arrival`, JSON roto, feed válido vacío, colector detenido, reloj PostgreSQL Europe/Madrid y cambio de viaje del mismo vehículo.

#### Fixed
- Trip updates reales con paradas `SKIPPED` sin `arrival` ya no invalidan el documento completo ni se usan como próxima parada comercial; errores de transporte/validación se registran con el hash recibido sin borrar el último éxito.
- Lecturas `timestamptz` de API/calidad se normalizan a UTC antes de crear contratos canónicos.
- La salud usa `source_timestamp` real y comprueba también la edad del sondeo; el frontend rotula la hora local como `Consulta`.
- Una posición anterior del mismo vehículo pero de otro viaje ya no provoca que el motor descarte la primera posición válida del viaje nuevo.

#### Verified
- Replay congelado: `1532` = 119/119/49 y `1533` = 121/121/49 (vehículos Madrid/matches/SKIPPED sin arrival). Python: 123/123 contra desarrollo; 118 verdes + 5 skips de soak contra PostGIS fresco. Frontend: lint, typecheck, 5 tests y build verdes. Base de desarrollo intacta en `668/484/3/120/0`.

### MP-015 — E2E y readiness MVP

#### Added
- `services/snapshotter/gold.py`: `build_line_daily_metrics`/`build_station_daily_metrics` calculan de verdad `daily_line_metrics`/`station_daily_metrics` (diferidas desde MP-009/DEC-021), resolviendo `trip_id`→`route_id`/`stop_id`→`station_id` contra `packages.gtfs.Topology`. `_scheduled_trip_ids_by_route` resuelve trips programados por `service_date` vía `calendar.txt` (día de la semana + rango de fechas). `GoldThresholds.on_time_threshold_seconds` (300s, calibrable). `SnapshotterConfig` ampliado con `network_id`/`short_name`/`gtfs_source` (mismas variables que `apps/api`). Ver DEC-033 para los tres límites documentados.
- `services/snapshotter/tests/test_gold.py` (9 tests, sin PostgreSQL, fixture GTFS real con calendario de un solo día) y una extensión real de `test_export_replay.py` (PostgreSQL real). 112/112 tests Python en verde.
- DEC-034: decisión documentada de no introducir dbt-core/dbt-duckdb como herramienta literal — `gold.py` ya aplica la disciplina dbt (capas, tests, documentación) sin el motor dbt, consistente con DEC-021. `analytics/dbt/README.md`/`analytics/duckdb/README.md` actualizados para reflejar esto.

- `.github/workflows/ci.yml`: job Python (PostgreSQL de servicio, migraciones aplicadas desde cero, suite real) y job frontend (lint/typecheck/test/build); nunca toca Renfe/CRTM/OSM en vivo. Verificado de verdad contra un contenedor PostgreSQL recién creado, no solo contra la base de desarrollo (DEC-035).
- `tests/e2e/test_replay.py`: replay E2E determinista — inyecta bytes de fixtures reales como respuesta del `fetcher` real del colector, recorriendo la cadena completa sin red en vivo (JSON crudo con forma de Renfe → colector → PostgreSQL real → resolución GTFS → API real). Dos escenarios: la fixture de MP-004 (nunca fabrica una resolución) y un payload sintético con forma real para un trip de la GTFS reducida (resuelve `route_id`/posición de extremo a extremo).

#### Fixed
- DEC-035: 5 tests (`test_export_replay.py`, `test_collector_cycle.py`, `test_persistence.py`, `test_real_soak_postgres.py`) usaban `CollectorConfig()` en vez de `CollectorConfig.from_env()`, ignorando silenciosamente `MADRID_PULSE_DATABASE_URL` — nunca se notaba porque el valor por defecto coincidía con el de desarrollo local. Encontrado al verificar la suite contra un PostgreSQL recién creado (no la base de desarrollo). Los tests atados al soak real irrepetible de MP-007 (668 filas/24 vehículos) ahora hacen `skip` explícito y documentado, no `fail`, cuando ese histórico puntual no está presente.
- Auditoría de contenido de los 12 ADRs contra la implementación real (ningún `Estado` cambiado — esa promoción sigue siendo decisión exclusiva del propietario). 5 corregidos en esta primera pasada: ADR-0002 (CRTM verificado por licencia pero nunca integrado — solo Renfe se implementó), ADR-0004 (corrige la nomenclatura real de campos de posición: `position.mode`, no `position_mode`; sin `source` público), ADR-0008/0009/0010 (la referencia "pendiente... en el cierre de Hito 1" ya pasó sin promoción el 2026-11-19 — corregida a "cierre de Hito 2", igual que `docs/adr/README.md` y `docs/DECISIONS.md`). Esta misma pasada editó también la "Decisión" de ADR-0003 (`Aceptado`) para eliminar la implicación de dbt-core literal — **esto violaba el proceso de ADR (regla 8, `AGENTS.md`) y se revirtió en la revisión de Codex**: ver sección "Fixed after Codex review" más abajo, donde ADR-0003 vuelve a su texto original y la decisión se formaliza como [ADR-0013](adr/0013-no-literal-dbt-engine.md) (`Propuesto`). `docs/ARCHITECTURE.md`/`docs/PLAN.md` corregidos para no implicar dbt-core literal (DEC-034).

#### Verified
- 114/114 tests Python en verde contra la base de desarrollo real (sin ningún `skip`); 109 en verde + 5 `skip` explícitos contra un PostgreSQL recién creado con las migraciones aplicadas desde cero, simulando exactamente lo que hace CI. Frontend: lint/typecheck/5 tests/build en verde. Corrida real end-to-end del exportador (`python -m services.snapshotter 2026-11-19`) contra el soak completo: 3 filas en `daily_line_metrics`, 18 en `station_daily_metrics`, sin datos fabricados. PostgreSQL restaurado exactamente a `668/484/3/120/0` en todos los casos.

#### Added
- `docs/MVP_READINESS.md`: checklist de cierre de Hito 2 para la aceptación del propietario — cumplimiento del objetivo declarado, demo local reproducible, estado real de tests (ambos escenarios), principios de datos verificados con evidencia, hallazgos clave, límites conocidos documentados y pendientes exclusivos de gobernanza.
- `docs/HITO_3_BACKLOG.md` recuperado desde `chore/hito-2-coordination` (redactado en una sesión anterior por instrucción explícita del propietario, Sección 7 de la autorización de Hito 2) — había divergido de la cadena `mp-010`→`mp-015` y se habría perdido al fusionar a `main` sin traerlo explícitamente a este worktree. Actualizado con un pointer a DEC-033 (las métricas por línea que planificaba como pendientes ya están resueltas para C5).

#### Fixed after Codex review (first round)
- Escala de porcentaje real: `build_line_daily_metrics` calculaba `delay_coverage_pct`/`on_time_pct_of_covered` como fracción `0..1`; el esquema real (`numeric(5,2) CHECK BETWEEN 0 AND 100`, `docs/DATA_CONTRACTS.md`) exige `0..100`. Corregido (`* 100`, redondeado a 2 decimales); test de regresión añadido.
- `docs/DATA_CONTRACTS.md`/`apps/api/README.md`/ADR-0005 corregidos: ya no dicen que las tablas gold "siguen vacías" (lo que falta es solo exponerlas vía endpoint).
- `docs/MVP_READINESS.md`: semántica `NULL` real precisada (`delay_coverage_pct` nunca `NULL` para una fila emitida; `on_time_pct_of_covered` sí, cuando `trips_with_delay_data = 0`); CI trigger descrito con precisión (`push` a `main` + `pull_request`, no "cada push").
- **Hallazgo de proceso real:** DEC-034 había reescrito la "Decisión" de ADR-0003 (`Aceptado`) sin pasar por el proceso de ADR. Revertido el texto de ADR-0003 a su redacción original; DEC-034 queda como nota de implementación, sin tocar la Decisión aceptada.
- `docs/HITO_3_BACKLOG.md` (área 5): corregido el dato obsoleto "~24 vehículos C5" con el desglose real de DEC-029.

#### Verified
- 115/115 tests Python (114 + 1 de regresión nuevo) contra la base de desarrollo; 110 en verde + 5 `skip` (de 115) contra un segundo contenedor PostgreSQL fresco desechable. PostgreSQL restaurado exactamente a `668/484/3/120/0`.

#### Fixed after Codex review (second round)
- El revertido de ADR-0003 (ronda anterior) dejó una incoherencia nueva: ADR-0003 (`Aceptado`) volvía a decir "consumido vía DuckDB/dbt", pero `docs/ARCHITECTURE.md`, `docs/PLAN.md` (F9), `analytics/dbt/README.md` y DEC-034 seguían afirmando que dbt-core/dbt-duckdb literal no forma parte del stack, y `docs/ARCHITECTURE.md` incluso decía "decidido en MP-015" — una decisión de arquitectura asentada sin ADR. Corregido creando [ADR-0013](adr/0013-no-literal-dbt-engine.md) (`Propuesto`, conforme a ADR-0007): ADR-0003 permanece intacto y sin reinterpretación; ADR-0013 documenta formalmente que MP-015 no introduce el motor dbt-core. `docs/ARCHITECTURE.md`/`docs/PLAN.md`/`analytics/dbt/README.md`/DEC-034 ahora referencian ADR-0013 en vez de asentar la decisión sin respaldo de ADR.
- `docs/STATUS.md:166` decía "109/115 + 5 skip" — corregido a "110 en verde + 5 `skip` (de 115)", el resultado real ya reflejado correctamente en este CHANGELOG.
- Las descripciones de "6 ADRs corregidos" en `docs/STATUS.md` (checklist) y en este CHANGELOG (ver arriba) no reflejaban el balance final tras el revertido de ADR-0003: quedó intacto (no fue uno de los corregidos) y ADR-0005 sí recibió una nota de drift real (tablas gold ya no vacías) que no estaba contemplada en el recuento original. Ambas descripciones actualizadas.

#### Verified
- Sin re-ejecución completa de la suite (cambio puramente documental de esta ronda); `git diff --check` sin problemas de espacio en blanco; coherencia re-verificada con `rg` sobre todas las referencias cruzadas a DEC-034/ADR-0003/ADR-0013.

#### Approved after cross-review
- OpenAI Codex aprobó MP-015 como `DONE` tras auditar el diff completo y re-verificar las dos rondas de correcciones. Evidencia independiente: 114/114 tests Python contra la base de desarrollo, 110 en verde + 5 `skip` (de 115) contra PostgreSQL fresco, frontend lint/typecheck/5 tests/build, y 13/13 tests gold+replay tras corregir la escala de porcentajes. ADR-0013 permanece `Propuesto` para decisión del propietario; no quedan bloqueantes técnicos o documentales para el cierre funcional de Hito 2.

### MP-014 — Frontend React/MapLibre C5

#### Added
- `apps/web/`: cliente estático React/TypeScript/MapLibre, responsive y accesible, con selector derivado de `/api/v1/lines`, polling HTTP cada 20 s, controles de capas/centrado/zoom, trazado OSM real, estaciones y vehículos.
- Diferenciación visual de `observed`/`estimated`/`stale`/`scheduled` por forma, color y opacidad, más leyenda textual que explica su semántica. Vehículos sin línea/posición resoluble permanecen contabilizados y consultables, sin coordenadas fabricadas; `delay.coverage=missing` se rotula como ausencia de dato, nunca como cero.
- Atribución visible `© OpenStreetMap contributors · ODbL` sobre el mapa.
- Extensión aditiva `LineOut.geometry` (DEC-031): `Corridor.segments` reales separados y estaciones GTFS proyectadas/ordenadas; `null` cuando no existe corredor asociado. OpenAPI regenerado y test de contrato contra fixtures GTFS/OSM reales.
- Dependencias frontend verificadas y lockfile npm reproducible (DEC-032).

#### Verified
- PostgreSQL/PostGIS, API (`uvicorn`) y Vite levantados de verdad con el GTFS oficial completo descargado (15.717.009 bytes). Smoke HTTP: 145 vehículos reales tras refrescar `vehicle_positions`; 31 resolvieron posición y exhibieron simultáneamente los cuatro estados (`observed` 24, `estimated` 2, `stale` 4, `scheduled` 1); 114 quedaron explícitamente no ubicables.
- Regresión Python completa 102/102 en verde (12 API + 90 previos), incluido el corredor real (636 puntos en 1 segmento continuo), 23 estaciones ordenadas de Móstoles-El Soto a Humanes e integraciones PostgreSQL. Los cuatro runs del smoke vivo y sus tres eventos de calidad se limpiaron por ID/timestamp; volumen final restaurado a `668/484/3/120/0`.
- Frontend con Node 22.13.1: ESLint sin avisos, TypeScript en verde, Vitest 5/5 y build Vite de producción completada.
- La inspección visual real no pudo ejecutarse en la sesión de Codex: Browser devolvió `No browser is available` y lista vacía. Por instrucción del coordinador, queda pendiente como gate explícito de la revisión de Claude Code (desktop + viewport estrecho + consola + interacciones); la evidencia HTTP confirma datos, no sustituye esa inspección.

#### Found
- El feed vivo de `trip_updates` incorporó un caso nuevo `stopTimeUpdate.arrival` ausente con `scheduleRelationship=SKIPPED`; el colector actual lo rechazó por validación. Queda registrado para MP-015/una tarea de colector; no impidió refrescar `vehicle_positions`, y la UI comunica estados de fuente y cobertura ausente sin inventar retrasos.

#### Fixed after Claude review
- Inspección real en navegador: Vite 8 prebundled devolvía `504` para `maplibre-gl-worker.mjs`; tiles raster y marcadores DOM aparecían, pero el worker no procesaba las fuentes GeoJSON y el corredor/las 23 estaciones quedaban invisibles. `optimizeDeps.exclude = ["maplibre-gl"]` sirve el ESM directo (`200`) y la revisión de Claude confirmó visualmente que ambas capas vuelven a aparecer con el cambio diagnóstico; Codex aplicó el fix definitivo y lo dejó para re-verificación visual.
- Accesibilidad: el selector de línea ahora tiene `id="line-selector"`, `name="line"` y asociación explícita `label[for]`, eliminando el aviso de Chrome sobre campos sin identificador.
- La segunda revisión confirmó dev correcto, pero detectó que producción pedía un worker no emitido y recibía `index.html` como fallback SPA. Vite ahora emite explícitamente `assets/maplibre-gl-worker.mjs`, `MapView` configura esa URL solo en producción y el build falla si el asset no coincide byte a byte con la dependencia instalada. Smoke de preview: `200`, `Content-Type: text/javascript`, 550.754 bytes y SHA-256 `c8564c4a4147326a587c9cc4c2a871c4b02a6c37c3f1ea51da55be3220d4b112`; queda pendiente la tercera pasada visual de Claude, no sustituida por esta evidencia HTTP.
- La tercera revisión confirmó el worker de producción y encontró una carrera menor en carga en frío: registrar `once("load")` desde cada cambio de línea podía perder el único evento y retrasar corredor/estaciones hasta el poll de 20 s. `MapView` mantiene ahora readiness y los últimos datos/capas en refs; el handler inicial de `load` crea fuentes/capas y aplica inmediatamente ese estado, mientras actualizaciones posteriores no vuelven a esperar el evento. Se registran errores internos de MapLibre y se añaden dos tests jsdom (carrera y visibilidad de errores); suite frontend 5/5 y build en verde.
- Cuarta revisión visual de Claude (final): build de producción reconstruida y verificada en navegador real con tres cargas en frío independientes (pestañas aisladas nuevas) — 3/3 mostraron el corredor real y las 23 estaciones de inmediato, sin errores de consola. Dev revalidado sin regresión; interacción del toggle de capas ("Trazado") comprobada. MP-014 aprobada `DONE`.

### MP-013 — FastAPI v1

#### Added
- `apps/api/`: FastAPI real bajo `/api/v1/*` — `health`, `live/vehicles`(`/{vehicle_id}`), `lines`(`/{line_id}`), `stations`(`/{station_id}`). Nunca pasa a través de Renfe/CRTM; siempre lee PostgreSQL + topología/geometría/movimiento ya resueltos en memoria.
- `apps/api/tools/fetch_gtfs_static.py`: descarga el GTFS completo real (reutilizando el endpoint verificado en MP-003) para que el feed en vivo resuelva contra la topología completa, no solo la fixture reducida de 15 trips de MP-010.
- OpenAPI generado y congelado en `apps/api/openapi.json`.
- Dependencias nuevas `fastapi==0.121.2`, `uvicorn[standard]==0.38.0`, `httpx==0.28.1` (DEC-030), versiones reales verificadas por instalación, no inventadas.

#### Found
- `route`/`station`/`trip`/`trip_stop` siguen vacías en PostgreSQL y `vehicle_position_observation.trip_id` sigue `NULL` en los 668 registros reales (confirmado por consulta directa) — la API resuelve vía `packages.gtfs.Topology` en memoria, nunca por `JOIN` SQL a esas tablas.
- De los 24 vehículos distintos del soak real de MP-007, solo 4 pertenecen a C5 (`10T0017C5`/`10T0018C5`); 19 son otras líneas del núcleo Madrid (C1, C2, C3, C4, C4a, C4b, C8a, C8b, C10) y 1 (`SPECIAL_10_91567C2`) no resuelve, confirmado contra el GTFS estático completo — confirma empíricamente DEC-020 con datos reales (DEC-029).
- Un único corredor OSM (`relation_3418150`) basta para ambos sentidos reales de C5: `build_trip_schedule` detecta el sentido de cada trip comparando el orden de sus paradas contra el corredor, no hace falta un corredor por sentido (DEC-028).

#### Deferred (documented, not silent)
- `history/lines/{line_id}`, `history/trips/{trip_id}`, `metrics/lines/{line_id}`, `metrics/stations/{station_id}`: `daily_line_metrics`/`station_daily_metrics` siguen vacías desde que MP-009 las difirió (DEC-021); calcularlas de verdad es alcance propio, no una extensión trivial de esta tarea (DEC-027).

#### Verified
- 101/101 tests en verde: 11 API nuevos (fixture reducida sin red + PostgreSQL real + un caso sintético de extremo a extremo + 2 de regresión de la revisión de Codex) + 90 de regresión (11 movement, 7 GTFS, 8 geo, 31 contratos, 6 fixtures, 9 collector, 13 quality, 5 snapshotter), incluidas las integraciones reales contra PostgreSQL.
- `/api/v1/live/vehicles` nunca fabrica `route_id`/`line`/`position` para un vehículo no resoluble (devuelve `null`), probado explícitamente. `/api/v1/health` calcula `data_age_s`/`unchanged_for_s` reales desde `source_ingestion_run`, nunca fabricados.
- App arrancada de verdad con `uvicorn --reload` y probada con `curl` real (`/api/v1/lines` → `200`, `/docs` → `200`), no solo `TestClient`.
- Revisión final independiente de Codex aprobada sobre `15170c4`: el único cambio desde `c82e62f` es la corrección del docstring residual con las 9 líneas no-C5 y el trip sin resolver; diff limpio, 11/11 tests API en verde, PostgreSQL `668/484/3/120/0` intacto e identidad Git correcta sin coautor. MP-013 pasa a `DONE`.

#### Fixed after Codex review (first round, blocking)
- `observation.age_s` solo se calculaba cuando el motor de movimiento resolvía una posición, dejando `null` para los 20/24 vehículos reales que no son C5 aunque su timestamp crudo sí era conocido. Corregido calculándola siempre desde `observation.reported_at`, independiente de si la ruta resuelve.
- `service_date` se pasaba como la fecha UTC (`now.astimezone(timezone.utc).date()`) al motor de movimiento, que la interpreta como fecha de calendario Europe/Madrid (`docs/DATA_MODEL.md`). Cerca de medianoche ambas difieren un día real, desplazando el horario esperado — mismo tipo de hallazgo que MP-009 ya documentó (DEC-021). Corregido con conversión explícita a Europe/Madrid; test de regresión cubre el borde de invierno (CET) y verano (CEST).
- Recuento de líneas no-C5 del soak corregido: el primero (DEC-029 inicial) listaba solo 5 líneas y omitía C2/C4/C8a/C10 y un trip de refuerzo (`SPECIAL_10_91567C2`) que no resuelve contra ningún `route_id` — recruzados los 24 pares reales contra el GTFS completo para la cifra definitiva (19 no-C5 + 1 sin resolver).
- Ambos bugs verificados revirtiendo el fix: los nuevos tests fallan exactamente como describió Codex (`age_s` `None`/`AttributeError`) y pasan con el fix restaurado.

### MP-012 — Motor de movimiento v1

#### Added
- `packages/movement/`: motor genérico con estados `observed`/`estimated`/`stale`/`scheduled`, contrato tipado directo para MP-013 (`confidence`, `age_s`, `source`, progreso, timestamps y anomalías) y umbrales configurables.
- Pipeline completo de ADR-0004 sobre APIs existentes: resolución literal GTFS, map-matching OSM, perfil de horario con horas >24/día de servicio, offset temporal, interpolación limitada y fallback a la última muestra plausible.
- `off_track`, `backward_jump` y `station_skip_anomaly` calculados y expuestos en cada resultado; `implausible_speed` refinado con distancia map-matched.
- ADR-0012 (`Propuesto`)/DEC-026: el motor vive en `packages/movement`, separado de geometría y reglas sobre observaciones crudas. `packages/geo.point_at_arc_length` añadido como primitiva geométrica genérica.

#### Calibrated
- Defaults `60s/180s` mantenidos: con `vehicle_positions` cada ~20–22 s equivalen a ~3/~8 polls perdidos.
- Límite físico de estimación 160 km/h y aceleración 1,2 m/s² separados del filtro de discontinuidad de fuente 900 km/h. El soak real midió un máximo map-matched de 666,4 km/h, coherente con los saltos crudos 246–787 km/h ya encontrados por MP-008.

#### Verified
- 90/90 tests en verde: 11 movement (10 deterministas + integración real), 7 GTFS, 8 geo, 31 contratos, 6 fixtures, 9 collector, 13 quality y 5 snapshotter.
- Volumen PostgreSQL real consultado en solo lectura: 668 posiciones antes/después, 177 a ≤200 m del corredor; recuentos finales `668/484/3/120/0` sin residuo.
- Cambio de día de servicio/horas GTFS >24, UTC estricto, transición de estados, fuentes distintas, saltos de estación, retrocesos, off-track y velocidades imposibles cubiertos por test.

#### Independent review (approved)
- Claude Code auditó `1edfa14`: código íntegro de `packages/movement/` leído, 90/90 tests reejecutados de forma propia (subiendo/bajando el contenedor `madrid-pulse` él mismo), integración real reproducida con resultados idénticos (668→668, 177 cerca del corredor, 666,4 km/h), pipeline verificado matemáticamente (offset temporal bidireccional, límites de velocidad/aceleración, fallback recursivo a la última observación plausible sin forzar `OBSERVED` artificialmente), ausencia del literal `"C5"` confirmada por lectura directa, identidad Git y enlaces ADR-0012/DEC-026 correctos. Evaluada la escalada a Opus (candidato explícito para revisiones algorítmicas complejas) y descartada por no ser necesaria. MP-012 queda `DONE`.

### MP-011 — Prototipo de geometría ferroviaria sobre OSM

#### Added
- `packages/geo/overpass.py`: cliente Overpass API genérico (por id de relación o `ref`/`network`), solo `urllib`.
- `packages/geo/corridor.py`: encadena los `ways` de vía de una relación OSM en el orden declarado, uniendo por nodo extremo compartido; registra huecos reales como `ChainGap` y mantiene cada tramo continuo (`Corridor.segments`) separado para que ningún cálculo geométrico fabrique una unión a través de un hueco.
- `packages/geo/geometry.py`: Haversine real + proyección punto-polilínea sin `shapely`/`pyproj`.
- `packages/geo/tools/fetch_fixture.py` y `tools/render_preview.py`: descarga/congela geometría real y genera un SVG de depuración reproducible (un `<polyline>` por tramo continuo).
- Fixture real de 4 relaciones OSM de C5 Madrid con checksum (4 SHA-256) y atribución ODbL; 8 tests contra ella.

#### Found
- La variante base de 6 estaciones de la ruta corta del GTFS (`10T0047C5`, sin Atocha) no tiene relación OSM propia: es una subsecuencia **contigua** real de paradas de la ruta larga, confirmado por comparación literal de IDs. Una variante real distinta del mismo `route_id` (7 estaciones, con Atocha antepuesta) proyecta en orden monótono sobre el mismo corredor pero **no** es contigua — omite 4 paradas intermedias reales.
- Las relaciones OSM `3418148`/`3418149` ("Fuenlabrada → Atocha → Móstoles-El Soto") son la ruta larga truncada en Fuenlabrada y no coinciden con el patrón real de 6 estaciones de la ruta corta — variante real documentada, no usada.
- `usage=main` (30 `ways`) / `usage=branch` (60 `ways`) en la vía: trazado troncal potencialmente compartido con otras líneas de Cercanías vs. ramal específico de C5 — no verificado qué otras líneas comparten el tramo.
- "C5"/"C-5" colisiona también en OSM entre núcleos (Asturias, Sevilla, Cantabria, Valencia, Madrid), igual que ya documentó ADR-0008/DEC-017 para el GTFS de Renfe.
- El endpoint público de Overpass devolvió `502 Gateway Timeout` por capacidad varias veces durante la descarga real; reintentos con pocos segundos de espera tuvieron éxito.

#### Verified
- 79/79 tests en verde: 8 geo nuevos + 71 de regresión (7 GTFS, 31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL.
- Las 4 relaciones direccionales encadenan sus `ways` de vía sin huecos; las 23 estaciones reales de la ruta larga (ambos sentidos) proyectan en orden monótono con distancia máxima real de 63,7 m.
- Evidencia visual real: SVG renderizado y revisado en navegador (Chrome DevTools MCP, captura completa) — forma real de la C5 reconocible, estaciones sin saltos sobre la vía.
- La lógica de `corridor.py`/`geometry.py`/`overpass.py` no contiene el literal de la línea piloto (test de regresión).

#### Fixed after Codex review (first round, blocking)
- `build_corridor` registraba `ChainGap` pero seguía concatenando ambos `ways` en una única `polyline`, así que `project_station`/`corridor_length_m` fabricaban un segmento recto sobre un hueco real (repro de Codex: `distance_m=0.0` en el centro de un hueco sintético). Corregido con `Corridor.segments` (tramos realmente continuos, separados en cada hueco); verificado revirtiendo el fix y confirmando que el nuevo test de regresión falla exactamente como describió Codex y pasa con el fix restaurado. `render_preview.py` corregido en paralelo para dibujar un `<polyline>` por tramo.
- Documentación corregida: recuento de tests (8/79, no 7/78); la variante de 7 estaciones de `10T0047C5` deja de describirse como "subsegmento contiguo" (solo es monótona); 4 SHA-256 añadidos a `tests/fixtures/osm_c5_real/MANIFEST.md` y verificados contra los ficheros reales.

### MP-010 — Topología GTFS C5

#### Added
- `packages/gtfs/`: parser en streaming de las seis tablas reales del GTFS estático, selección genérica por IDs/red/nombre corto, agrupación de variantes por `(network_id, short_name)` y API de resolución literal `trip_id` → `route_id` y `stop_id` → `stop_sequence`.
- Validador de referencias, secuencias, shapes y patrones de recorrido; fixture real reducida y reproducible con checksum/licencia; 7 tests contra esa fixture.

#### Found
- La descarga oficial del `2026-11-19` contiene para C5 Madrid 5 rutas, 8.160 trips, 23 estaciones, 165.205 stop_times, 630 puntos de shape, 30 servicios y 14 patrones de recorrido. `10T0035C5` aporta 8 trips pero ningún stop_time.
- `trips.txt` no contiene `direction_id`; la dirección real disponible se valida por el orden de `stop_sequence` y `shape_id`. No se inventó la columna ni recorrido para los huérfanos.

#### Verified
- 71/71 tests en verde: 7 GTFS nuevos + 64 regresiones (31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL. Parser ejecutado además contra el ZIP oficial completo: validación válida, 0 errores, 14 patrones y 8 huérfanos informados.
- Las cinco variantes permanecen separadas y agrupables; los recorridos completos y cortos incluyen sus pares inversos reales. La lógica de parser/resolución no contiene el literal de la línea piloto.

#### Independent review (approved)
- Claude Code auditó `add8aa6`: código íntegro de `packages/gtfs/` leído, 71/71 tests reejecutados de forma propia (subiendo/bajando el contenedor `madrid-pulse` él mismo), recuentos reales `668/484/3/120/0` confirmados idénticos antes y después de los tests, ausencia del literal `"C5"` en `parser.py`/`topology.py` verificada por lectura directa (reforzada por el test de regresión que lo impone), identidad Git y enlaces a ADR-0011/DEC-022/DEC-023 correctos. MP-010 queda `DONE`.

### MP-009 — Exportador histórico (Parquet particionado)

#### Added
- `services/snapshotter/export.py`: DuckDB como único motor para exportar las cinco tablas "hot" de PostgreSQL a Parquet particionado `date=YYYY-MM-DD/hour=HH`, comprimido ZSTD. Sin `pandas`/`pyarrow` adicionales (DEC-021).
- `services/snapshotter/gold.py`: resumen diario inicial por núcleo (`nucleo_prefix`), partición `date=YYYY-MM-DD`.
- `services/snapshotter/__main__.py`: CLI `python -m services.snapshotter YYYY-MM-DD`.
- 5 tests nuevos: 3 puros de límites de día de servicio (incluido CEST/verano) y 2 de replay real contra PostgreSQL.

#### Found
- Los datos reales del soak test de MP-007 (`23:31:42 UTC` del 18-nov-2026) pertenecen al día de servicio **19-nov** en Europe/Madrid (CET, UTC+1 en noviembre) — leer la fecha UTC directamente habría exportado esas filas al día equivocado, exactamente el error que `docs/DATA_MODEL.md` ya advertía. Corregido convirtiendo siempre a `Europe/Madrid` antes de calcular los límites del día de servicio y la partición.

#### Verified
- Exportación real completa del día `2026-11-19` (datos reales del soak test, no fixtures): 1272 filas (668 posiciones + 484 actualizaciones + 120 ejecuciones de ingesta), ~76 KB comprimidos; releído con una consulta DuckDB independiente, recuento exacto sin pérdida.
- Test de replay real: día de prueba conocido insertado y COMPROMETIDO (no `rollback()` — DuckDB usa su propia conexión `libpq`), exportado, verificado fila a fila, y limpiado explícitamente (`finally`).
- Suite completa: 64/64 pruebas en verde (31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter).

#### Fixed after Codex review (first round, blocking)
- `services/snapshotter/export.py`: `service_alert` no tiene columna propia de observación/recepción; se particionaba por `active_period_start` (la ventana de VIGENCIA del aviso), por lo que 3 alertas reales ingeridas el 19-nov desaparecían de ese día si su vigencia caía en otra fecha. Corregido uniendo `service_alert` a `source_ingestion_run` (vía `ingestion_run_id`) y usando `started_at` de esa ejecución como el momento de observación real. `test_export_replay.py` ampliado para cubrir las 5 tablas (antes solo `vehicle_position_observation`/`trip_update_observation`); verificado revirtiendo el fix (falla `0 ≠ 1` exactamente como reportó Codex) y restaurándolo. Reexportado el día real: `service_alert` pasa de 0 a 3 filas.

#### Independent review (second round, approved)
- Codex auditó `a7b36b0`, ejecutó los 2 tests de replay ampliados contra PostgreSQL real y confirmó limpieza completa de las filas temporales en las 5 tablas. Reexportó independientemente `2026-11-19` (668 posiciones, 484 actualizaciones, 3 alertas, 120 ejecuciones, 0 eventos de calidad) y leyó las tres alertas esperadas desde Parquet. MP-009 queda `DONE` y completa el Hito 1 (`MP-002` → `MP-009`), pendiente de que el propietario autorice los siguientes pasos.

#### Known limitation (documented, not blocking)
- El resumen gold calcula por núcleo, no por `route_id`/`station_id` (`daily_line_metrics`/`station_daily_metrics`): esa resolución depende de MP-010 (GTFS estático), que no es dependencia de MP-009. Ver DEC-021.

### MP-008 — Quality engine

#### Added
- `packages/quality/engine.py`: reglas puras para los cinco flags admitidos por el esquema v1, con umbrales calibrables nombrados y eventos estructurados.
- `packages/quality/db.py`: lectura de historial reciente y persistencia transaccional de `data_quality_event`; derivación estable de `vehicle_position_observation.quality_flags`.
- Integración en el colector: calidad evaluada sobre observaciones normalizadas antes de persistirlas, dentro de la misma transacción del poll.
- 13 tests de calidad: disparo y control de falso positivo para cada regla, cambio de día UTC y dos pruebas contra PostgreSQL real con rollback.

#### Changed
- `duplicate_snapshot` se calcula sobre el hash del payload completo sostenido más de 180s; la deduplicación normal entre polls consecutivos de MP-007 no se marca.
- `implausible_speed` se calcula en Python con Haversine entre posiciones consecutivas del mismo `source_vehicle_id`; no espera el campo `speed_kmh`, ausente en Renfe.
- `docs/DATA_QUALITY.md` distingue los cinco flags implementados de las tres reglas geométricas diferidas a MP-012.

#### Verified
- Suite completa: 59/59 pruebas en verde (31 contratos + 6 fixtures + 9 colector + 13 calidad), incluidas integraciones reales con PostgreSQL/PostGIS.
- Las inserciones de prueba se ejecutaron dentro de una transacción ambiente y terminaron en rollback; el volumen del soak test no se borró ni truncó.

#### Revisión independiente (Claude Code, 2026-11-19)
- Reproducidas las 59 pruebas contra el mismo PostgreSQL real; revisado el diseño de `engine.py`/`db.py`/`collector.py`. **APROBADA.**
- **Hallazgo empírico documentado, no bloqueante:** se repitieron 117 pares reales de posiciones consecutivas del soak test de MP-007 contra `check_implausible_speed`; 12/117 (~10%) dispararon con velocidades implícitas de 246–787 km/h. La inspección de la secuencia completa del vehículo `21053` confirmó que son saltos reales entre filas ya almacenadas (20-40s de separación, varios km), no un error del cálculo de Haversine — indica que el feed en vivo de Renfe actualiza posición en saltos más gruesos de lo que sugiere la cadencia de poll. Registrado para calibrar el umbral `implausible_speed_kmh` en MP-012.

### MP-007 — Collector idempotente

#### Added
- `services/collector/`: colector de polling contra los tres feeds GTFS-RT de Renfe, con reintentos/backoff/timeout (`http_client.py`, solo `urllib`), filtro de alcance por núcleo (ADR-0008), deduplicación por hash canónico contra la última fila almacenada (ADR-0010, nuevo) y persistencia en PostgreSQL (MP-006).
- `requirements.txt` + `.venv`: primera dependencia de terceros del proyecto (`psycopg[binary]`) para escribir en PostgreSQL desde Python; Python 3.12 fijado como versión de desarrollo (DEC-019).

#### Verified
- 46 tests reales en verde (31 contratos, 6 fixtures, 9 colector — 5 de ellos integración real contra PostgreSQL, no mocks).
- Soak test real de 20 minutos contra los tres feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión nueva tras el proceso.
- Rechazo de duplicados y detección de cambios reales verificados contra PostgreSQL real (no simulado).
- Segunda revisión independiente de Codex aprobada: test de regresión del empate y suite completa reejecutados contra PostgreSQL real; `id DESC` confirmado como desempate determinista en las tres consultas de deduplicación. MP-007 pasa a `DONE`.

#### Fixed during verification
- `packages/contracts/nucleo.py`: `nucleo_prefix()` no reconocía trip_id de refuerzo con formato `SPECIAL_<núcleo>_<resto>` (sin prefijo numérico directo) — hallazgo real del feed en vivo, corregido con una regex específica.
- `packages/contracts/raw.py`: `RawStopTimeArrival.delay` y los tres `entity` de `Raw*Feed` eran obligatorios basándose en las fixtures de MP-004; el feed en vivo trajo un `arrival` sin `delay` (tren `ADDED`) y una respuesta sin la clave `entity` (0 vehículos activos) — ambos corregidos a opcionales/con default, con test de regresión.
- `services/collector/db.py`: una versión anterior envolvía cada `INSERT` en su propio `with conn.transaction()`; con una conexión de larga duración, esto dejaba filas de observación sin comprometer indefinidamente mientras `source_ingestion_run` sí persistía (detectado verificando con una conexión nueva, no confiando en la ausencia de excepción). Corregido centralizando el límite de transacción en `run_cycle` (todo el ciclo se compromete como una unidad).
- Tests de integración: `addCleanup` en orden LIFO cerraba la conexión antes de poder hacer `rollback()`; corregido el orden de registro.

#### Fixed after Codex review (first round, blocking)
- `services/collector/db.py`: `latest_payload_hash` ordenaba solo por `observed_at DESC` sin desempate; dos filas de la misma entidad con `observed_at` empatado (ese timestamp lo reporta la fuente, no nuestro poll) hacían que Postgres devolviera una fila arbitraria, insertando una fila duplicada real en vez de deduplicar (reproducido por Codex: `(1, 6)` en vez de `(0, 7)` en el tercer ciclo de una secuencia inicial→cambio→repetición). Corregido con `id DESC` como desempate secundario en las 3 consultas de `_LATEST_HASH_QUERIES`; test de regresión `test_tied_observed_at_does_not_break_dedup_on_third_cycle` verificado contra el fix revertido (falla igual que reportó Codex) y restaurado (pasa).

#### Known limitation (documented, not blocking)
- El filtro de ingesta descarta por núcleo (Madrid), no todavía por línea C5 específicamente (ADR-0001, `Aceptado`) — ver DEC-020. Acotar a C5 exige la resolución `trip_id` → `route_id` vía el GTFS estático, asignada explícitamente a MP-010 por ADR-0009.

### MP-006 — Esquema PostgreSQL/PostGIS v1

#### Added
- Compose local aislado con `postgis/postgis:17-3.5`, puerto `127.0.0.1:5433`,
  volumen/red propios y montaje de migraciones en solo lectura.
- Migración SQL plana `0001_init` up/down con 14 tablas de aplicación,
  `source_feed_version`, PostGIS, constraints de dominio/deduplicación y los cinco
  índices propuestos (incluidos dos GIST).
- Documentación de arranque/parada, aplicación ordenada, rollback y diferencias
  de nombres resueltas a favor de `packages/contracts/canonical.py`.

#### Verified
- Aplicación real en PostgreSQL 17/PostGIS 3.5.2: 14 `CREATE TABLE`, 5
  `CREATE INDEX`, `COMMIT`; geometría generada y caso de posición ausente nulo.
- Duplicados de route, trip y observación rechazados realmente por PostgreSQL
  (exit 1 y nombre de constraint en cada caso).
- Rollback real: 14 `DROP TABLE`, `COMMIT` y 0 tablas de aplicación restantes;
  ciclo posterior `down → up` completado con exit 0.
- Regresión: 23 tests de contratos y 6 tests de fixtures, todos `OK`.

#### Fixed during verification
- La etiqueta oficial no ofrece manifiesto ARM64: Compose fija `linux/amd64` para
  Docker Desktop en Apple Silicon.
- El primer `down` intentaba retirar `postgis`, pero la imagen ya había creado
  extensiones dependientes y PostgreSQL revirtió la transacción. El rollback final
  conserva correctamente esa infraestructura preexistente y elimina solo el
  esquema de aplicación, sin `CASCADE` destructivo.

#### Revisión independiente (Claude Code, 2026-11-19)
- Reproducido el ciclo completo `down → up → datos → 3 rechazos UNIQUE → down → up`
  de forma propia en el mismo worktree, sin depender solo del reporte de Codex;
  confirmados los 2 índices `GIST`, la ausencia real de `effect`/`cause`/
  `header_text`/`current_stop_sequence`, y las suites de regresión (23/23, 6/6).
  `*-traza-app` verificado intacto antes y después. **APROBADA.**
- **Hallazgo corregido:** `docs/STATUS.md` había sustituido el checklist completo
  de MP-005 en "Tarea actual" por el de MP-006 sin archivarlo primero en "Tareas
  cerradas de la cadena", rompiendo el patrón seguido por MP-002/MP-003/MP-004.
  Corregido moviendo el registro íntegro de MP-005 a esa sección.

### MP-005 — Contrato canónico interno

#### Added
- `packages/contracts/raw.py`: modelos Pydantic fieles al JSON bruto observado de Renfe (vehicle_positions, trip_updates, alerts), sin campos inventados.
- `packages/contracts/nucleo.py`: tabla de prefijos de núcleo verificada en MP-003 y helpers de disambiguación.
- `packages/contracts/canonical.py`: esquema normalizado (`VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth`) con UTC, dato ausente = `None`, y `nucleo_prefix` como campo derivado.
- `packages/contracts/normalize.py`: funciones puras `raw → canonical`.
- `packages/contracts/tests/`: 17 tests (`test_raw_parsing.py`, `test_canonical_normalization.py`, `test_synthetic_schema.py`).
- `docs/adr/0009-unobserved-raw-fields.md` (`Propuesto`) y DEC-018.

#### Changed
- `docs/DATA_MODEL.md`: `speed_kmh`/`bearing` marcados `nullable` (no observados nunca), `current_stop_sequence` renombrado a `current_stop_id` (el feed da stopId, no posición de secuencia), eliminados `effect`/`cause`/`header_text` de `service_alert` (no observados), añadido `schedule_relationship` y `description_language` (sí observados).
- `docs/DATA_QUALITY.md`: nota aclarando que `implausible_speed` debe calcularse a partir de posiciones consecutivas, no leerse de un campo `speed_kmh` de origen.

#### Verified
- `python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`: 23 tests, `OK`.
- JSON Schema exportable (`model_json_schema`) incluyendo campos derivados en modo serialización.
- Rechazo activo de datos inválidos (`ValidationError` en tipos incorrectos y campos obligatorios ausentes).

#### Found
- `docs/DATA_MODEL.md` (escrito en MP-001, antes de verificación empírica) asumía tres grupos de campos que el feed real de Renfe nunca emite — ver DEC-018/ADR-0009.

#### Fixed (tras 1ª revisión de Codex, dispatch `ctx_ea1d5cf46d74`)
- **Bloqueante:** `RawActivePeriod.end` carecía del comentario de "no observado" que sí tienen los demás campos corregidos tras el hallazgo de MP-005 — se corrigió añadiendo un comentario. Insuficiente: ver 2ª ronda.
- **Bloqueante:** el esquema canónico documentaba "UTC siempre" sin exigirlo — añadidos `require_utc`/`require_utc_or_none` como `field_validator` en los 4 modelos; 5 tests nuevos prueban el rechazo real de `datetime` naive u offset no UTC (22 tests en total).
- **Bloqueante:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato de `deep-research-report.md` queda contradicho por esta verificación — añadida la fila, sin editar el documento congelado.
- **Menor:** `ADR-0009` decía erróneamente que Codex (revisor) podía promover el ADR a `Aceptado` — corregido, solo el propietario puede; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos).

#### Fixed (tras 2ª revisión de Codex, dispatch `ctx_ded900b82f20`)
- **Bloqueante:** Codex señaló que un comentario no resuelve una contradicción -- `packages/contracts/raw.py` declara explícitamente que no debe contener campos no observados, y `RawActivePeriod.end` seguía declarado. Corregido eliminando `end` del modelo `raw` (no comentándolo); `normalize.py` ya no lo lee (`active_period_end` siempre `None` hoy); `canonical.py` conserva `ServiceAlert.active_period_end` como campo opcional de cara al futuro, con un comentario que aclara por qué siempre es `None` actualmente. Añadido test de regresión que falla si se reintroduce sin verificar, incluso si el JSON de origen lo trae (se ignora por `extra="ignore"`). 23 tests en total.

#### Reviewed
- Tercera revisión independiente de Codex: **APROBADA**, sin hallazgos abiertos. Reejecutados 23/23 tests; verificados directamente el esquema `raw`, el descarte de campos extra no observados, el enforcement UTC, la trazabilidad del modelo candidato, ADR-0009, enlaces, ausencia de secretos y whitespace.

### MP-004 — Fixtures reproducibles

#### Added
- Fixtures JSON reducidas de capturas reales frescas de `vehicle_positions`, `trip_updates` y `alerts`, sin cabeceras ni cookies, con casos Madrid y colisión C5 entre núcleos.
- `tests/fixtures/MANIFEST.md`: fecha UTC, endpoints, recuentos original/conservado y SHA-256 de cada fixture.
- `tests/fixtures/test_parse_fixtures.py`: 6 pruebas offline con `unittest` para integridad, envoltura GTFS-RT, esquemas observados y disambiguación por prefijo de núcleo.

#### Verified
- Capturas directas: `200 application/json`; 394 posiciones, 401 actualizaciones y 76 alertas antes del recorte.
- `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v`: 6 tests ejecutados, `OK`.
- Los 3 JSON pasan `python3 -m json.tool`; SHA-256 recalculados coinciden con el manifiesto.

#### Reviewed
- Claude Code aprobó MP-004 el 2026-11-18 tras re-verificación independiente: hashes SHA-256 recalculados de forma propia (coinciden), suite de 6 tests re-ejecutada (`OK`), e inspección manual confirmando que el test de colisión C5 es sustantivo, no tautológico. MP-004 pasa a `DONE`.

### MP-003 — Probe real de feeds C5

#### Added
- `docs/research/MP-003-probe-findings.md`: evidencia real (status HTTP, timestamps, esquema JSON observado) de los 3 feeds GTFS-RT y descarga/inspección real del GTFS estático de Cercanías.
- `docs/adr/0008-route-identity.md` (`Propuesto`): `route.source_route_id` debe ser el `route_id` completo, no el código de línea.

#### Changed
- `docs/legal/DATA_SOURCES.md`: disponibilidad y esquema de los 3 feeds GTFS-RT y del GTFS estático pasan de `PENDING MP-003` a `VERIFIED`.
- `docs/DATA_MODEL.md`: entidad `route` corregida para explicitar `source_route_id` como `route_id` completo y añadir `nucleo_prefix`.
- `docs/DECISIONS.md`: DEC-017 (route_id completo, no código de línea).

#### Verified
- `vehicle_positions.json`, `trip_updates.json`, `alerts.json`: `200 OK`, JSON real GTFS-RT 2.0, no protobuf.
- Frecuencia de refresco de `vehicle_positions`: ~20–22 s medidos con 3 polls reales (coincide con `Cache-Control: max-age=30`).
- GTFS estático: descarga real exitosa (15,7 MB) vía `ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip`; el fallo SSL mencionado en MP-002 correspondía al enlace de portal (CKAN), no al enlace de descarga real.
- `stop_id` del feed en vivo coincide con `stops.txt` del GTFS estático (coordenadas verificadas).

#### Found
- **"C5" no es un identificador único**: existe también en Asturias (`20T0011C5`, Gijón–Pola de Laviana) y Andalucía (`30T0009C5`, Jardines de Hércules–Benacazón) en el mismo feed nacional. Ver DEC-017.
- Cobertura de `trip_updates` para Madrid fue 0/302 en el único poll realizado — pendiente de más muestreo antes de concluir nada (no se afirma que sea un problema sistemático).

#### Fixed (tras 1ª revisión de Codex, dispatch `ctx_61d7dd4fd86b`)
- **Bloqueante:** corregida la afirmación de que el `trip_id` en vivo no coincidía literalmente con `trips.txt`. Era falsa — causada por un `grep` propio anclado al campo equivocado (`trip_id` es el 3er campo del CSV, no el 1º). Verificado con comparación de conjuntos completa: 403/403 coinciden.
- **Bloqueante:** corregida la cardinalidad imposible en `docs/DATA_MODEL.md` — `UNIQUE(network_id, source_route_id)` exige una fila `route.id` por cada una de las 5 variantes de C5 Madrid, no una fila con una lista de `source_route_id`. `docs/adr/0008-route-identity.md` actualizado igual.
- **Menor:** corregida la afirmación falsa de que el GTFS estático no incluía `shapes.txt` (sí lo incluye).
- **Menor:** medida la frecuencia real de `trip_updates` (Δ42s) y `alerts` (Δ20s) con 2 polls cada uno — antes solo se había medido `vehicle_positions`.

#### Reviewed
- OpenAI Codex aprobó MP-003 el 2026-11-18 tras re-verificación independiente final: 404/404 `trip_id` de un snapshot fresco coincidieron literalmente con `trips.txt`, sin elementos no resueltos; DEC-017/ADR-0008 y `docs/DATA_MODEL.md` quedaron coherentes. MP-003 pasa a `DONE`.

### MP-002 — Matriz de fuentes y licencias

#### Changed
- `docs/legal/DATA_SOURCES.md`: licencias de Renfe GTFS/GTFS-RT, CRTM GTFS, estadística 1923861, OpenStreetMap y proyectos de referencia verificadas contra páginas oficiales y ficheros `LICENSE`, con `source_id`, publisher, dataset, URL, fecha UTC, restricciones y checklist reproducible.
- `docs/legal/LICENSE_MATRIX.md`: sustituidas las hipótesis `PENDING` por resultados verificables; documentadas la reciprocidad ODbL para bases derivadas, la separación consulta/software, y las obligaciones AGPL de Via Península sin reutilizar código.
- `docs/legal/ATTRIBUTION.md`: textos operativos de atribución para Renfe, CRTM, OSM, Comunidad de Madrid y el uso eventual de datos normalizados de Valfiguer.
- `docs/DECISIONS.md`: DEC-016 registra que los datos/API de Valfiguer son `CC BY 4.0`, pero no existe un repositorio público de implementación verificable ni puede inferirse su licencia de código.
- `docs/TASKS.md` y `docs/STATUS.md`: MP-001 reflejada como `DONE`, Hito 1 autorizado y MP-002 entregada en `REVIEW` para auditoría de Claude Code.

#### Verified
- Via Península: `AGPL-3.0`; Niltra/cercanias: `MIT`; atlas-ferroviario: texto MIT para código más aviso Renfe `CC BY 4.0`; Valfiguer: datos/API `CC BY 4.0`, código desconocido.
- Renfe Data: `CC BY 4.0` en GTFS estático y los tres datasets GTFS-RT, con condiciones adicionales del portal; CRTM: licencia propia `CRTM-LDA`; OpenStreetMap: `ODbL-1.0`.

### MP-001 — Bootstrap documental del repositorio

#### Added
- Estructura de monorepo: `apps/{web,api}`, `services/{collector,normalizer,snapshotter}`, `packages/{contracts,gtfs,geo,quality}`, `analytics/{dbt,duckdb}`, `infra/{docker,cloudflare,migrations}`, `tests/{fixtures,integration,e2e}`, `.github/{ISSUE_TEMPLATE,pull_request_template.md}` — todos los directorios de servicios futuros contienen únicamente `README.md` explicativo, sin código funcional.
- `AGENTS.md` y `CLAUDE.md`: protocolo de colaboración Claude Code ↔ Codex, regla de autoría exclusiva del propietario humano, principios de datos transversales.
- `docs/PLAN.md`: roadmap por fases F0–F10 con dependencias, entregables y gates de calidad.
- `docs/TASKS.md`: backlog completo MP-001 a MP-015 con ejecutor, revisor, dependencias, entradas/entregables, criterios de aceptación y estado.
- `docs/STATUS.md`: tablero vivo con checklist, bloqueos y bitácora.
- `docs/DECISIONS.md`: decisiones aceptadas, propuestas y pendientes.
- `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/DATA_QUALITY.md`, `docs/DEVELOPMENT.md`.
- `docs/adr/0001` a `0006`: decisiones de alcance C5, fuentes de datos, estrategia de almacenamiento, modelo de posición, contrato de API y política de licenciamiento.
- `docs/legal/DATA_SOURCES.md`, `LICENSE_MATRIX.md`, `ATTRIBUTION.md`.
- `docs/research/TRACEABILITY.md`: trazabilidad entre decisiones/tareas y evidencia consultada.
- `README.md` reescrito con visión del producto, estructura del repo y enlaces a la documentación.
- `.gitignore` para Python/Node/datos/env.

- `docs/adr/0007-autonomy-model.md` y DEC-014 en `docs/DECISIONS.md`: modelo de autonomía acotada (autorización por hito, commits de iteración en worktree, gates limitados a licencia/coste), a petición explícita del propietario.

#### Changed
- `deep-research-report.md` y `MADRID_PULSE_BRIEF_INICIAL.md` movidos a `docs/research/`, contenido preservado íntegro.
- `AGENTS.md`/`CLAUDE.md`: protocolo de coordinación en Orca (un worktree por tarea, delegación directa agente-a-agente) añadido a petición del propietario.
- `AGENTS.md`/`CLAUDE.md`: regla de autoría reescrita tras la revisión de Codex (hallazgo bloqueante — contradicción entre la excepción de "commit si el propietario lo pide" y la prohibición absoluta) y para incorporar la nueva política de commits de iteración en worktree.
- `docs/TASKS.md`: añadido `analytics/dbt/` a los componentes afectados de MP-009 y MP-015 (hallazgo menor de Codex); grafo de dependencias en ASCII sustituido por tabla exacta de dependencias directas (hallazgo menor de Codex).
- `AGENTS.md`: añadida nota de excepción de naming de rama para `chore/mp-001-foundation` (hallazgo menor de Codex).
- Segunda ronda de correcciones tras la primera re-verificación de Codex (2 bloqueantes + 2 menores, dispatch `ctx_e72e7a44721a`): añadida la sección "Modelo de autonomía por hito" a `AGENTS.md` (antes referenciada pero inexistente); reescritos el protocolo de worktree, el diagrama de flujo y la regla 10 en `AGENTS.md`/`CLAUDE.md`/`docs/TASKS.md`/`docs/PLAN.md` para reflejar autorización por hito y worktrees paralelos entre tareas independientes, en vez del texto anterior que seguía exigiendo autorización y merge por tarea individual; `docs/adr/0007-autonomy-model.md` corregido para que los ADR de arquitectura propuestos durante la autonomía se registren como `Propuesto` (nunca `Aceptado`) hasta la revisión del propietario, coherente con `docs/adr/README.md`; `docs/STATUS.md` corregido para quitar MP-010 del paralelismo de Hito 1 (está fuera de su rango MP-002→MP-009) y quitar DEC-003 de los gates de licencia/coste (es una decisión de visibilidad, no de licencia/coste).
- Tercera ronda de correcciones tras la segunda re-verificación de Codex (1 bloqueante + 1 menor, dispatch `ctx_762cad1ca40c`): el protocolo exigía que la dependencia directa de una tarea estuviera fusionada en `main` antes de abrir el siguiente worktree, lo que obligaba al propietario a fusionar en tiempo real tras cada tarea y anulaba el propósito del modelo de autonomía (ADR-0007 solo exigía `DONE`, no fusionada). Corregido introduciendo un mecanismo de ramas encadenadas: el worktree de una tarea dependiente se crea a partir de la rama de su dependencia directa en cuanto está `DONE`, sin esperar merge a `main`; el propietario decide cuándo fusionar (en lote al cierre del hito u otro momento) sin bloquear el avance. Reescrito en `AGENTS.md` (regla 10, sección de autonomía por hito, pasos 1/6/7 del protocolo, diagrama de flujo), `CLAUDE.md`, `docs/TASKS.md` y `docs/PLAN.md`. También corregido el "Principio rector" de `docs/PLAN.md`, que afirmaba una cadena de fases estrictamente lineal contradiciendo la excepción de dependencias (F5↔F2) ya documentada en la misma página.
- Cuarta revisión de Codex (dispatch `ctx_0ee25a6a5d2c`): **APROBADA**, sin hallazgos bloqueantes ni menores. Registrada la sugerencia no bloqueante de Codex (cómo converge una tarea con varias dependencias de ramas paralelas, relevante para MP-012) como DEC-015 en `docs/DECISIONS.md` y como nota en la ficha de MP-012 en `docs/TASKS.md`, a resolver antes de abrir esa tarea, no antes de cerrar MP-001.

#### Not done in this task
- Sin código de producto, sin dependencias instaladas, sin servicios cloud configurados, sin bases de datos ni contenedores — fuera de alcance de MP-001 según `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` §7.
