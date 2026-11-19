# STATUS.md — Tablero vivo

> Punto de entrada del estado actual. El detalle por tarea vive en `docs/TASKS.md`; el historial de cambios, en `docs/CHANGELOG.md`.

## Hito autorizado actualmente

**Hito 1 — `MP-002` → `MP-009`: completado, aprobado por revisión cruzada el `2026-11-19`, y fusionado a `main` por el propietario (`pedromaaz13`) el `2026-11-19`.** PR #1 (`mp-009-historical-export` → `main`), commit de merge `f567d3c`. Confirmado: `git merge-base --is-ancestor 8be1272 f567d3c` → `0` (el último commit de la cadena MP-009 es ancestro de `main`; nada quedó sin integrar).

```text
Cobertura: F1 (factibilidad) + F2 (contratos) + F3 (persistencia/colector) + F4 (calidad/histórico)
Objetivo de salida: colector idempotente validado + quality engine + histórico exportado y replayable.
Cadena: MP-002 → MP-003 → MP-004 → MP-005 → MP-006 → MP-007 → MP-008 → MP-009.
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007.
```

MP-001 está `DONE`: Codex aprobó la revisión cruzada y, conforme a ADR-0007, no fue necesario que la rama estuviera fusionada en `main` para que una tarea dependiente avanzara. La rama paralela `chore/mp-001-foundation` (bitácora administrativa parcial, superada por el registro completo de la cadena `mp-00X`, ver nota de proceso más abajo) y los 9 worktrees `mp-002` a `mp-009` se conservan intactos tal como exige el propietario — ninguno se ha borrado.

**Hito 2 autorizado por el propietario el `2026-11-19`: `MP-010` → `MP-015` ("Live Railway MVP").**

```text
Cobertura: F5 (geometría y topología) + F6 (motor de movimiento) + F7 (API) + F8 (frontend) + F9 (E2E/readiness)
Objetivo de salida: primera app local funcional mostrando la C5 en vivo — topología GTFS real, geometría OSM,
  motor de movimiento con cuatro estados, API /api/v1 propia, frontend React/MapLibre, E2E + CI.
Tabla ejecutor/revisor (fijada por el propietario, coherente con docs/TASKS.md):
  MP-010 Topología GTFS      → Ejecutor Codex   · Revisor Claude
  MP-011 Geometrías OSM      → Ejecutor Claude   · Revisor Codex
  MP-012 Motor de movimiento → Ejecutor Codex   · Revisor Claude
  MP-013 FastAPI             → Ejecutor Claude   · Revisor Codex
  MP-014 React/MapLibre      → Ejecutor Codex   · Revisor Claude
  MP-015 E2E y MVP readiness → Ejecutor Claude   · Revisor Codex
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007. Además, por instrucción explícita
  del propietario para este hito: ningún push/PR/merge se ejecuta sin solicitar autorización en el momento
  (revierte, para Hito 2, la autorización puntual ya consumida en el cierre de Hito 1 — ver AGENTS.md).
No se avanza fuera de MP-010→MP-015 sin nueva autorización explícita (p. ej. no se implementa la red completa
  de Cercanías Madrid en este hito — eso es Hito 3, solo backlog de planificación, ver docs/PLAN.md F10 y la
  bitácora de este documento).
```

### Política de selección de modelo (Hito 2, fijada por el propietario)

- **Modelo principal: Claude Sonnet, esfuerzo de razonamiento alto** — por defecto para coordinación en Orca, implementación ordinaria, desarrollo de API/frontend, tests automatizados y revisiones cruzadas rutinarias.
- **Escalado: Claude Opus, esfuerzo de razonamiento alto** — solo con justificación técnica concreta (geometría/arquitectura geoespacial compleja, resolución ambigua de topología ferroviaria, algoritmos de map-matching/movimiento, errores persistentes que Sonnet no resuelve, decisiones arquitectónicas de alto impacto, revisión avanzada de UX/rendimiento/arquitectura frontend). Nunca se escala solo porque una tarea "parece importante" sin evaluar primero si Sonnet basta.
- **Verificación empírica realizada el `2026-11-19` (no se asumió ni inventó ningún identificador):** `orca orchestration worker-start --help` confirma que `--model`/`--effort` son parámetros reales y soportados para lanzar un agente Claude (`--model` acepta "opaque provider model ids"; `--effort` requiere `--model`). El identificador verificado empíricamente para "Sonnet" es `sonnet` y para "Opus" es `opus` (documentado como ejemplo real por Orca: `--model opus --effort high`); el esfuerzo de razonamiento se pasa como `--effort high`.
- **Discrepancia señalada al propietario:** el encargo nombra "Claude Sonnet 5.5" / "Claude Opus 5.5 High" como modelos. El contexto de entorno de esta sesión solo confirma la existencia de **Sonnet 5** y **Opus 5** (además de Haiku 4.5) como los modelos Claude más recientes disponibles — no se ha podido verificar ningún identificador "5.5". Siguiendo la instrucción explícita de no inventar identificadores, los workers de Hito 2 se lanzan con `--model sonnet --effort high` (por defecto) y `--model opus --effort high` (escalado), que son los identificadores reales confirmados, no una invención de "5.5".
- Codex: se usa el modelo/nivel de razonamiento disponible más adecuado, priorizando razonamiento alto para geometría, movimiento, contratos e integración, conforme a los roles ya fijados en `docs/TASKS.md`.

## Auditoría independiente de preparación para integración

**OpenAI Codex — `2026-11-19`: APROBADA, sin bloqueantes reales para integrar `mp-009-historical-export` en `main`.** El estado auditado (`c8d3bd0`, antes de registrar esta entrada) contiene de forma lineal y sin merges todo MP-001 → MP-009: `git merge-base --is-ancestor 3e7b533 c8d3bd0` devuelve `0`, y el recorrido desde `origin/main` (`5b45227`) hasta `c8d3bd0` contiene los 23 commits esperados. Los 23 tienen autor y committer `Pedro Matute <pedromaaz13@gmail.com>` y ninguno incluye un trailer literal `Co-authored-by:`.

Evidencia reproducida de forma independiente:

- La rama paralela `chore/mp-001-foundation` se separa en `3e7b533` y añade cinco commits (`fac945c` → `15820ac`) que solo modifican `docs/STATUS.md`, `docs/TASKS.md` y `docs/CHANGELOG.md`. Su contenido es seguimiento administrativo hasta MP-005 en `REVIEW`; la autorización del Hito 1, sus condiciones operativas, los hallazgos y cierres de MP-002 → MP-005 ya están reflejados —con estado final y mayor detalle— en esta rama. No se encontró contenido único material cuya ausencia causase pérdida al integrar únicamente `mp-009-historical-export`.
- Worktrees muestreados limpios antes de registrar esta auditoría: clon original, `mp-004-fixtures`, `mp-007-collector` y `chore/mp-001-foundation`; este worktree también estaba limpio.
- Diff `origin/main..HEAD`: 95 ficheros (92 añadidos, `README.md` modificado y dos renombres `R100` hacia `docs/research/`), sin cachés, entornos virtuales ni temporales versionados. `git diff --check` solo informa de una línea en blanco final en cada una de las tres fixtures JSON; son avisos cosméticos y las pruebas que las parsean pasan.
- Suites ejecutadas realmente: contratos 31/31, fixtures 6/6, collector 9/9, quality 13/13 y snapshotter 5/5 — **64/64 en verde**. PostgreSQL conservó exactamente los recuentos `668/484/3/120/0` en `vehicle_position_observation` / `trip_update_observation` / `service_alert` / `source_ingestion_run` / `data_quality_event` antes y después; no quedó residuo de pruebas.
- Escaneo de secretos: no se encontraron claves, tokens, ficheros de entorno ni llaves privadas. La única contraseña es `madrid_pulse_local`, credencial de desarrollo local usada exclusivamente contra `127.0.0.1:5433`.
- Enlaces: 48 enlaces relativos Markdown comprobados en el repositorio, 0 rotos. `docs/TASKS.md` marca MP-001 → MP-009 como `DONE`; este documento declara el Hito 1 completado y prohíbe iniciar MP-010 sin autorización nueva; `docs/CHANGELOG.md` conserva el historial de las nueve tareas.

**Veredicto de integración:** `mp-009-historical-export` está preparada para que el propietario la integre en `main`; no se identificaron omisiones, pérdida documental, problemas de autoría ni bloqueantes técnicos. Los tres avisos de whitespace en fixtures son los únicos hallazgos abiertos y no son bloqueantes.

## Resolución de DEC-015 (mecánica de convergencia de ramas, antes de MP-012)

**Resuelto el `2026-11-19`, documentado aquí y en `docs/DECISIONS.md`/`AGENTS.md`.** La pregunta abierta era qué rama usar como base y cómo integrar las demás cuando una tarea depende de varias ramas potencialmente distintas (caso previsto: MP-012 depende de MP-008, MP-010 y MP-011).

Con Hito 1 ya fusionado a `main`, el caso concreto de MP-012 **deja de requerir una fusión real de ramas divergentes**: MP-008 ya es ancestro de `main` (se fusionó como parte de la cadena MP-002→MP-009). Si MP-010 y MP-011 se ramifican a partir de `main` (o de una rama que a su vez parte de `main`, como esta misma `chore/hito-2-coordination`), entonces la cadena resultante — `main → MP-010 → MP-011` — ya contiene a MP-008 de forma transitiva. MP-012 puede ramificar simplemente desde la rama de MP-011 sin ningún `git merge` real: sus tres dependencias (MP-008, MP-010, MP-011) son todas ancestros de ese punto.

**Mecanismo general (para este y futuros casos de convergencia múltiple), registrado en `AGENTS.md`:** antes de abrir el worktree de una tarea con varias dependencias directas, comprobar con `git merge-base --is-ancestor <dependencia> <candidata-a-base>` si cada dependencia ya es ancestro de la rama candidata a base (normalmente la más "profunda" en la cadena). Si todas lo son, se ramifica directamente desde esa rama — no hace falta fusión. Solo si una dependencia **no** es ancestro de la otra (p. ej. dos ramas que de verdad divergieron sin que ninguna absorbiera a la otra vía `main`) se necesita una fusión real (`git merge` de la rama no-ancestro sobre la rama base elegida, documentando el resultado y cualquier conflicto en `docs/STATUS.md` antes de continuar). Este hito no necesita ese caso general porque la estructura tras el merge de Hito 1 ya lo evita.

## Tarea actual

**MP-014 — Frontend React/MapLibre C5**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **REVIEW**

Worktree/rama: `mp-014-frontend`, ramificada desde `mp-013-fastapi` (MP-013 `DONE`).

### Checklist de MP-014

- [x] `apps/web/`: React + TypeScript + MapLibre consumiendo `/api/v1/*` real (MP-013) — nunca Renfe/CRTM directamente, nunca mocks en la demo final.
- [x] **Gap de geometría resuelto (DEC-031):** `LineOut.geometry` nullable expone cada `Corridor.segments` por separado y las 23 estaciones proyectadas/ordenadas; no conecta paradas ni asigna el único corredor a otra línea. Test real contra GTFS/OSM y OpenAPI regenerado.
- [x] Los cuatro estados de posición (`observed`/`estimated`/`stale`/`scheduled`) tienen forma, color, opacidad y explicación textual diferentes (ADR-0004). Un ciclo real fresco los produjo simultáneamente: 24/2/4/1.
- [x] Campos `null` honestos: 114 de 145 vehículos reales quedaron sin ubicar tras el smoke; se contabilizan y listan explícitamente, sin ruta/posición inventada. `delay.coverage=missing` se explica como ausencia de dato.
- [ ] **Gate visual pendiente de revisor:** la UI incluye diseño responsive/accesible, controles de capa/centrado/zoom y estados de foco, pero esta sesión de Codex no tuvo navegador disponible (`getForUrl` → `No browser is available`; `agent.browsers.list()` → `[]`). El coordinador indicó no bloquear la entrega y asignó a Claude Code la inspección real desktop + viewport estrecho + consola + interacciones antes de aprobar `DONE`. `curl` no se presenta como sustituto.
- [x] Arquitectura preparada para más líneas (ADR-0011): selector y estado derivados de `(network_id, line_id)` de la API; ningún literal de línea en componentes, hooks ni lógica compartida (la única coincidencia textual en `package-lock.json` pertenece a hashes de integridad).
- [x] Via Península/Valfiguer no se consumen ni se copia código/diseño; implementación independiente.
- [x] Smoke real de consumo API: PostgreSQL + GTFS oficial completo + `uvicorn` + Vite; `/lines` devolvió el corredor real y `/live/vehicles` los cuatro modos simultáneos. La carga visual del mapa permanece incluida en el gate anterior.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_CONTRACTS.md`/`docs/DECISIONS.md` actualizados con evidencia y límites reales.

### Resultado y límites

Implementación completa y en revisión: frontend estático genérico multi-línea,
contrato aditivo de geometría real y pruebas reproducibles. Comandos de la demo:

```sh
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
.venv/bin/python -m apps.api.tools.fetch_gtfs_static
MADRID_PULSE_GTFS_SOURCE=data/gtfs_static/fomento_transit.zip .venv/bin/uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
cd apps/web && npm ci && npm run dev
```

Verificación ejecutada: regresión Python 102/102 (12 API + 90 previos);
frontend `npm run lint`, `npm run typecheck`, Vitest 3/3 y `npm run build`,
todo en verde. Smoke vivo tras un poll real:
145 vehículos, 31 map-matched (`observed` 24, `estimated` 2, `stale` 4,
`scheduled` 1). Esto confirma contrato/datos, no el gate visual pendiente.
Los runs `585–588` creados por el smoke y sus eventos derivados se retiraron
por ID/timestamp; PostgreSQL quedó restaurado a `668/484/3/120/0`.

Hallazgo fuera del cambio frontend: el feed fresco de `trip_updates` trajo un
`stopTimeUpdate` `SKIPPED` sin `arrival` y el contrato crudo del colector lo
rechazó. `vehicle_positions` sí se actualizó correctamente; la UI representa
salud/cobertura ausente sin inventar valores. Se deja para MP-015/colector.

### Bloqueos

Inspección visual real pendiente por indisponibilidad de navegador en la sesión
de Codex. No bloquea el estado `REVIEW`; sí bloquea `DONE` hasta que Claude Code
la ejecute y apruebe. Ningún otro bloqueo de implementación conocido.

### Siguiente paso

Al completarse y ser aprobada por Claude Code (revisor), MP-015 (E2E y readiness MVP, ejecutor Claude Code) puede ramificar su worktree desde `mp-014-frontend` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

## Tareas cerradas de la cadena

**MP-013 — FastAPI v1**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-013-fastapi`, ramificada desde `mp-012-movement-engine` (MP-012 `DONE`). MP-005/MP-007 (sus otras dependencias) ya ancestros de `main`, confirmado con `git merge-base --is-ancestor origin/main HEAD`.

### Checklist de MP-013

- [x] `apps/api/`: FastAPI real (`fastapi==0.121.2`, `uvicorn[standard]==0.38.0`, `httpx==0.28.1` para tests — DEC-030), sin reimplementar resolución GTFS/geometría/movimiento.
- [x] **Hallazgo real:** `route`/`station`/`trip`/`trip_stop` siguen vacías en PostgreSQL y `vehicle_position_observation.trip_id` sigue `NULL` en los 668 registros reales — confirmado por consulta directa. La API resuelve `trip_id`→`route_id`/`stop_id` vía `packages.gtfs.Topology` en memoria, nunca por `JOIN` SQL a esas tablas.
- [x] 7 endpoints reales: `health`, `live/vehicles`(`/{vehicle_id}`), `lines`(`/{line_id}`), `stations`(`/{station_id}`); `history`/`metrics` diferidos explícitamente (DEC-027, `docs/DATA_CONTRACTS.md`).
- [x] `/api/v1/health` calcula `data_age_s`/`unchanged_for_s`/`status` reales desde `source_ingestion_run`, nunca fabricados.
- [x] `/api/v1/live/vehicles` combina la última/penúltima observación real por vehículo con `MovementEngine.position()` (MP-012); nunca fabrica `route_id`/`line`/`position` cuando el `trip_id` no resuelve — devuelve `null` honesto.
- [x] **Hallazgo real (DEC-029):** de los 24 vehículos distintos del soak real de MP-007, solo 4 son C5 (`10T0017C5`/`10T0018C5`); 19 son otras líneas del núcleo (C1, C2, C3, C4, C4a, C4b, C8a, C8b, C10) y 1 (`SPECIAL_10_91567C2`) no resuelve, confirmado contra el GTFS estático completo — confirma empíricamente DEC-020.
- [x] **Corregido tras la revisión de Codex (hallazgo documental):** el primer recuento listaba solo 5 líneas (C1/C3/C4a/C4b/C8b) y omitía C2/C4/C8a/C10 y el trip `SPECIAL_` sin resolver — recruzados los 24 pares reales contra `trips.txt` del ZIP completo para la cifra definitiva.
- [x] **Hallazgo real (DEC-028):** un único corredor OSM (`relation_3418150`) basta para ambos sentidos reales de C5: `build_trip_schedule` detecta el sentido de cada trip comparando el orden de sus paradas contra el corredor.
- [x] OpenAPI generado y congelado en `apps/api/openapi.json`.
- [x] `apps/api/tools/fetch_gtfs_static.py`: descarga el GTFS completo real para que `/api/v1/live/vehicles` resuelva vehículos C5 en ejecución local (la fixture reducida de MP-010 solo tiene 15 trips representativos, insuficiente para el feed en vivo).
- [x] App arrancada de verdad con `uvicorn` y probada con `curl` real (`/api/v1/lines`, `/docs`), no solo `TestClient`.
- [x] 9 tests de contrato nuevos (fixture reducida + PostgreSQL real + un caso sintético de extremo a extremo con un trip real) + regresión completa: **99/99 en verde**.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_CONTRACTS.md`/ADR-0005/DECISIONES actualizados con evidencia real.

### Resultado y límites

API real conforme a `docs/DATA_CONTRACTS.md` para los endpoints `live`/`lines`/`stations`/`health`; `history`/`metrics` diferidos explícitamente (DEC-027) porque los agregados diarios siguen sin poblarse desde MP-009. Sin literales de línea en la lógica (ADR-0011): `network_id`/`short_name` son configuración.

Ejecución final real (`.venv`, Python 3.12): 101/101 tests — API 11, movement 11, GTFS 7, geo 8, contratos 31, fixtures 6, collector 9, quality 13, snapshotter 5. Suites con PostgreSQL ejecutadas con el contenedor `madrid-pulse` levantado por el ejecutor; recuentos finales `668/484/3/120/0` sin residuo.

**Revisión independiente de OpenAI Codex (`2026-11-19`): NO APROBADA en primera ronda.** Reprodujo de forma propia: PostgreSQL `route`/`station`/`trip`=0 y `trip_id` resuelto=0; volumen `668/484/3/120/0` antes/después; GTFS oficial descargado y verificado (15.717.009 bytes); DEC-028 confirmado en los 4 trips C5 reales; 9 API + 90 regresión en verde; servidor `uvicorn` real arrancado y probado con `curl` (`health`/`live/vehicles`/`docs` → `200`). Hallazgos:

- **Bloqueante 1:** `apps/api/service.py` solo calculaba `observation.age_s` cuando el motor de movimiento resolvía una posición — para los 20/24 vehículos reales que no son C5, `reported_at` era real pero `age_s` quedaba `null` aunque es calculable directamente desde el timestamp crudo.
- **Bloqueante 2:** `_movement_position` pasaba `service_date=now.astimezone(timezone.utc).date()`, pero `packages.movement.schedule.service_seconds` interpreta esa fecha como calendario Europe/Madrid (`docs/DATA_MODEL.md`). Cerca de medianoche (p. ej. `2026-11-19T23:30Z` = `2026-11-20 00:30` CET) ambas fechas difieren en un día real, desplazando el horario esperado.
- **Menor documental:** DEC-029 listaba solo 5 líneas no-C5 (C1/C3/C4a/C4b/C8b) y omitía C2/C4/C8a/C10 y un trip de refuerzo (`SPECIAL_10_91567C2`) que no resuelve contra ningún `route_id` — el cruce completo de Codex contra `trips.txt` dio la cifra real.

**Corrección de Claude Code (`2026-11-19`), lista para re-verificación:**

- **Bloqueante 1 corregido:** `age_s` ahora se calcula siempre como `(now - observation.reported_at)`, independiente de si la ruta/posición resuelve. Verificado revirtiendo el fix: el nuevo test (`test_live_vehicles_always_report_raw_observation_age`) falla con `age_s` `None` contra el código anterior y pasa con el fix restaurado.
- **Bloqueante 2 corregido:** `service_date` se calcula ahora con conversión explícita a Europe/Madrid (`now.astimezone(ZoneInfo("Europe/Madrid")).date()`), no la fecha UTC. Verificado revirtiendo el fix: el nuevo test (`test_service_date_uses_europe_madrid_calendar_not_utc`, cubre borde de invierno CET y verano CEST) falla con `AttributeError` contra el código anterior y pasa con el fix restaurado.
- **Menor corregido:** recruzados los 24 pares reales `(source_vehicle_id, source_trip_id)` contra `trips.txt` del GTFS completo. Cifra definitiva: 4 C5, 19 de otras 9 líneas (C1, C2, C3, C4, C4a, C4b, C8a, C8b, C10), 1 (`SPECIAL_10_91567C2`) sin resolver. DEC-029, `apps/api/README.md`, `docs/CHANGELOG.md` y este documento corregidos.

101/101 tests en verde (99 + 2 de regresión nuevos). La segunda verificación de Codex confirmó funcionalmente ambos bloqueantes y el cruce GTFS completo; quedó únicamente un docstring residual con la lista anterior de 5 líneas.

**Revisión final independiente de OpenAI Codex (`2026-11-19`): APROBADA, sin hallazgos abiertos.** El commit `15170c4` corrige exclusivamente ese docstring: ahora registra 19 vehículos de C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 más 1 trip de refuerzo sin resolver. `git diff --check c82e62f..15170c4` está limpio y el diff contiene solo 4 inserciones/3 borrados en `apps/api/tests/test_api_contract.py`. La suite contractual aislada se reejecutó contra PostgreSQL real: 11/11 `OK`, con recuentos finales `668/484/3/120/0`; el contenedor se bajó sin borrar el volumen. Autor y committer de `15170c4`: `Pedro Matute <pedromaaz13@gmail.com>`, sin coautor. MP-013 pasa a `DONE`.

### Bloqueos

Ninguno.

### Siguiente paso

MP-014 (Frontend React/MapLibre, ejecutor Codex) ramificó su worktree desde `mp-013-fastapi` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-012 — Motor de movimiento v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-012-movement-engine`, ramificada desde `mp-011-osm-geometry` (MP-011 `DONE`). DEC-015 resuelto: `git merge-base --is-ancestor origin/main HEAD` confirmado `true` desde `mp-011-osm-geometry` — MP-008 (ancestro de `main`), MP-010 y MP-011 quedan todos satisfechos sin fusión real (ver `AGENTS.md`).

### Checklist de MP-012

- [x] Motor de movimiento con los cuatro estados `OBSERVED` (0–60s) / `ESTIMATED` (>60–180s) / `STALE` (>180s) / `SCHEDULED` (sin observación plausible), conforme a ADR-0004; defaults parametrizados en `MovementThresholds`.
- [x] Pipeline de ADR-0004 completo: resolución GTFS → `Corridor.project_station` → progreso acumulado → perfil de `stop_times` → offset temporal → interpolación → límites de aceleración/velocidad/retroceso; una muestra imposible no borra la anterior plausible.
- [x] `MovementPosition` expone `position_mode`, `confidence` decreciente, `age_s`, `source`, timestamps, progreso y anomalías; fuentes distintas impiden confundir estimado/stale/scheduled con observado.
- [x] Calibración real: `60s/180s` mantenidos porque la cadencia ~20–22s equivale a ~3/~8 polls perdidos. Separados `max_estimated_speed_kmh=160` (trayectoria fabricada) y `unusable_jump_speed_kmh=900` (discontinuidad del feed): MP-008 midió 246–787 km/h crudos y MP-012 666,4 km/h map-matched en el volumen real.
- [x] Tests deterministas: cuatro transiciones, confianza/fuente, offset horario, velocidad/aceleración, salto de estación, retroceso, off-track, salto imposible, rango empírico 700 km/h aceptado, UTC y cambio de día/horas GTFS >24.
- [x] Validación real PostgreSQL de solo lectura: 668 observaciones antes y después, 177 a ≤200 m del corredor, máximo salto map-matched 666,4 km/h; volumen completo `668/484/3/120/0` intacto tras toda la regresión.
- [x] Ubicación decidida en ADR-0012 (`Propuesto`): `packages/movement` orquesta las capas existentes sin contaminar `geo` con horarios ni `quality` con generación de posiciones.
- [x] `off_track`/`backward_jump`/`station_skip_anomaly` calculados y expuestos. Persistencia diferida explícitamente: el `CHECK`/modelo v1 de `data_quality_event` pertenece a observaciones crudas y MP-012 no crea una tabla de derivados; cualquier persistencia futura requiere migración con dueño/clave claros.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_QUALITY.md`/ADR-0004/ADR-0012/DEC-026 actualizados con evidencia real.

### Resultado y límites

Motor genérico implementado en `packages/movement/`, sin literal de la línea piloto en la lógica. `point_at_arc_length` completa la API geométrica genérica como inversa de `arc_length_to`. El motor exige un corredor continuo por trip y rechaza explícitamente geometrías con huecos en vez de fabricar distancia. La topología huérfana sin `stop_times` sigue produciendo error explícito, no un recorrido inventado.

Ejecución final real (`.venv`, Python 3.12): 90/90 tests en verde — movement 11, GTFS 7, geo 8, contratos 31, fixtures 6, collector 9, quality 13, snapshotter 5. Las suites con PostgreSQL se ejecutaron con el contenedor `madrid-pulse` levantado por el ejecutor; recuentos finales `668/484/3/120/0`. `compileall` y `git diff --check` sin errores.

- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** `packages/movement/model.py`, `schedule.py`, `engine.py` leídos íntegros. 90/90 tests reejecutados de forma propia (10 deterministas movement + 1 integración real + 79 de regresión GTFS/geo/contratos/fixtures/collector/quality/snapshotter), subiendo y bajando el contenedor `madrid-pulse` yo mismo; integración de solo lectura reproducida con los mismos resultados exactos (668→668 posiciones, 177 a ≤200 m del corredor, máximo map-matched `666,4 km/h`). Verificado matemáticamente: `directed_progress`/`physical_arc` correctos en ambos sentidos del corredor; la estimación nunca retrocede y queda acotada por velocidad (160 km/h) y aceleración (1,2 m/s²); el fallback a la última observación plausible reaplica la clasificación de estado completa por recursión en vez de forzar `OBSERVED` de forma artificial; la separación entre límite físico (160 km/h) y filtro de discontinuidad de fuente (900 km/h) es coherente con los hallazgos reales de MP-008/MP-012. Confirmado por lectura directa que `engine.py`/`model.py`/`schedule.py` no contienen el literal `"C5"`. Identidad Git de `1edfa14` correcta (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor), `git diff --check` limpio, sin secretos. Evalué si esta revisión requería escalar a Opus (candidato explícito del propietario para revisiones algorítmicas complejas) y no fue necesario: todas las decisiones de diseño se pudieron verificar directamente con razonamiento estándar. Sin hallazgos bloqueantes ni menores.

### Bloqueos

Ninguno. ADR-0012 permanece `Propuesto` hasta revisión formal del propietario al cierre de Hito 2.

### Siguiente paso

MP-012 está `DONE`. MP-013 (FastAPI v1, ejecutor Claude Code, revisor Codex) ramificó su worktree desde `mp-012-movement-engine` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-011 — Prototipo de geometría ferroviaria sobre OSM**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-011-osm-geometry`, ramificada desde `mp-010-gtfs-topology` (MP-010 `DONE`).

### Checklist de MP-011

- [x] `packages/geo/overpass.py`: cliente Overpass API genérico (relación por id o por `ref`/`network`), sin literales de línea en la lógica; solo `urllib` de la librería estándar.
- [x] `packages/geo/corridor.py`: encadena los `ways` de vía (`role=""`) de una relación OSM en el orden declarado, uniendo por nodo extremo compartido; un hueco real se registra como `ChainGap`, nunca se fabrica una unión inexistente.
- [x] `packages/geo/geometry.py`: Haversine real + proyección punto-polilínea (plano local equirrectangular por consulta), sin `shapely`/`pyproj`.
- [x] Descarga real de las 4 relaciones direccionales OSM de C5 Madrid (`11331`/`3418148`/`3418149`/`3418150`, `ref=C-5`/`network=Cercanías Madrid`, agrupadas por el `route_master` `3418151`): las 4 encadenan sus `ways` de vía sin huecos.
- [x] Las 23 estaciones reales de la ruta larga (ambos sentidos, GTFS `10T0017C5`/`10T0018C5`) proyectan en orden monótono sobre su corredor correspondiente, distancia máxima real 63,7 m.
- [x] **Hallazgo:** la ruta corta (`10T0047C5`/`48C5`) no tiene relación OSM propia — su patrón base de 6 estaciones es una subsecuencia contigua literal de la ruta larga; la variante de 7 estaciones con Atocha solo es monótona y no contigua. No se fabrica geometría separada.
- [x] **Hallazgo:** las relaciones `3418148`/`3418149` ("Fuenlabrada→Atocha→Móstoles-El Soto") son la ruta larga truncada en Fuenlabrada, no coinciden con el patrón real de 6 estaciones de la ruta corta — documentado como variante real no usada (DEC-025).
- [x] **Hallazgo:** `usage=main` (30 `ways`)/`usage=branch` (60 `ways`) en la vía — trazado troncal potencialmente compartido vs. ramal específico de C5; no verificado qué otras líneas comparten el tramo (DEC-025).
- [x] "C5"/"C-5" colisiona también en OSM entre núcleos (Asturias, Sevilla, Cantabria, Valencia, Madrid) — mismo patrón que ADR-0008/DEC-017 ya documentó para el GTFS de Renfe.
- [x] Fixture real congelada y atribuida (`tests/fixtures/osm_c5_real/`): 4 relaciones, checksums y proceso en `MANIFEST.md`; licencia ODbL de la base de datos derivada confirmada (DEC-024).
- [x] Evidencia visual real: `packages/geo/tools/render_preview.py` genera un SVG del corredor + estaciones; renderizado y revisado en navegador (Chrome DevTools MCP, captura completa) — forma real de la C5 reconocible, estaciones sin saltos sobre la vía.
- [x] 79/79 tests en verde: 8 geo nuevos + 71 de regresión (7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DECISIONS.md`/`docs/legal/ATTRIBUTION.md`/`docs/legal/DATA_SOURCES.md` actualizados con evidencia real antes de delegar a revisión.

### Resultado y límites

Geometría real de la C5 Madrid derivada de 4 relaciones OSM reales, validada contra las 23 estaciones reales del GTFS con distancia máxima 63,7 m y orden monótono. La API (`Corridor.project_station`, `build_corridor`) queda disponible para MP-012/MP-013 sobre cualquier relación configurada, sin literales de línea en la lógica. Limitaciones documentadas, no ocultas: `10T0035C5` sigue sin validar (huérfano desde MP-010), el reparto exacto de trazado troncal compartido con otras líneas no se verificó, y la correspondencia OSM↔GTFS para la ruta corta se resuelve por subsegmento del corredor largo, no por una relación OSM dedicada (no existe una).

### Bloqueos

**Revisión independiente de OpenAI Codex (`2026-11-19`): NO APROBADA en primera ronda.** Hallazgos devueltos al ejecutor en este mismo worktree:

- **Bloqueante — `ChainGap` se registra pero la geometría aún fabrica la unión.** Con dos `ways` sintéticos desconectados, `build_corridor` produce correctamente un `ChainGap`, pero concatena ambos en una única `polyline`; `project_station` y `corridor_length_m` interpretan entonces el par de extremos alrededor del hueco como un segmento real. Reproducción independiente: una consulta situada en el centro del hueco proyectó con `distance_m=0.0`. Debe representarse/ignorarse explícitamente la discontinuidad en los cálculos y añadirse una prueba que falle con el comportamiento actual.
- **Menor — evidencia y documentación cuentan mal la suite y la ruta corta.** `python3 -m unittest packages.geo.tests.test_real_feed -v` ejecuta 6 tests, no 7; el total real es 77 (6 geo + 71 regresión), no 78. La fixture GTFS contiene 7 estaciones para `10T0047C5`, no 6. Las 7 sí proyectan monótonamente sobre el mismo corredor de `10T0017C5` (máximo independiente: 37,3 m), pero no son una subsecuencia contigua de paradas de la ruta larga: omiten cuatro paradas intermedias. Debe reservarse “subsegmento contiguo” para la geometría de vía y corregirse el recuento en `docs/TASKS.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `packages/geo/README.md`, fixture/manifiesto y comentarios/tests afectados.
- **Menor — checksums anunciados pero ausentes.** `packages/geo/README.md` afirma que el manifiesto contiene checksums, pero `tests/fixtures/osm_c5_real/MANIFEST.md` no lista ninguno. Añadir los cuatro SHA-256 o retirar la afirmación; la opción preferible es añadirlos para preservar trazabilidad.

Evidencia ya reproducida por el revisor: 6 geo + 7 GTFS + 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter, todos en verde; PostgreSQL `668/484/3/120/0` antes y después; render documentado generado como HTML/SVG real; identidad Git de `fbc3fde` correcta y `git diff --check` limpio. Pendiente corrección y re-verificación antes de aprobar.

**Corrección de Claude Code (`2026-11-19`), lista para re-verificación de Codex:**

- **Bloqueante corregido:** `Corridor` ahora tiene `segments` (tramos realmente continuos, separados en cada `ChainGap`); `project_station`/`corridor_length_m` solo operan dentro de un tramo, nunca interpolando a través de un hueco. Verificado revirtiendo el fix: el nuevo test de regresión (`test_gap_between_disconnected_ways_is_not_fabricated_as_track`, dos `ways` sintéticos desconectados) falla con `AttributeError: 'Corridor' object has no attribute 'segments'` contra el código anterior, y pasa con el fix restaurado. `render_preview.py` corregido en paralelo: dibuja un `<polyline>` por tramo, no uno solo que uniría visualmente un hueco real.
- **Menor corregido (recuento):** 8 tests geo (no 7), 79 totales (no 78) — contado de nuevo con un venv fresco (`python3 -m venv` + `pip install -r requirements.txt`), subiendo/bajando el contenedor yo mismo y confirmando `668/484/3/120/0` antes y después.
- **Menor corregido (sobre-reclamo "subsegmento contiguo"):** separado en dos tests y dos afirmaciones distintas. La variante base de 6 estaciones de `10T0047C5` (sin Atocha) SÍ es una subsecuencia contigua real (verificado por comparación literal de IDs: aparece en el índice 16 del patrón largo de 23 estaciones). La variante real de 7 estaciones (con Atocha antepuesta) proyecta en orden monótono sobre el mismo corredor pero NO es contigua — omite 4 paradas intermedias reales (Méndez Álvaro, Doce de Octubre, Orcasitas, Puente Alcocer). `packages/geo/README.md`, `docs/TASKS.md` y este documento corregidos para no confundir ambas afirmaciones.
- **Menor corregido (checksums):** 4 SHA-256 añadidos a `tests/fixtures/osm_c5_real/MANIFEST.md`, recalculados y verificados contra los ficheros reales (`hashlib.sha256` sobre cada JSON, comparación exacta con el valor documentado).

Commit de corrección `f795036`. Reenviado a Codex para segunda verificación en este mismo worktree.

**Segunda verificación independiente de OpenAI Codex (`2026-11-19`): APROBADA.** El revisor leyó íntegramente `packages/geo/corridor.py` y repitió una reproducción sintética propia: dos `ways` desconectados producen 2 `segments`; un punto en el centro del hueco proyecta a `2223,9 m` del tramo real más próximo (no ~0), y `corridor_length_m=2223,9 m` suma únicamente los dos tramos, sin el hueco. El test bloqueante dirigido pasó 1/1 y `packages.geo.tests.test_real_feed` pasó 8/8.

Regresión propia: 71/71 en verde (7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter), con las integraciones reales ejecutadas contra PostgreSQL sin `skip`; recuentos persistentes `668/484/3/120/0` idénticos antes y después. El contenedor se levantó con `--wait` y se bajó sin `-v`, conservando el volumen. La comparación literal independiente sitúa el patrón base de 6 estaciones en el índice 16 del patrón largo de 23; la variante de 7 con Atocha ocupa las posiciones `11,16,17,18,19,20,21`, por lo que no es contigua y omite cuatro estaciones. Los cuatro SHA-256 recalculados coinciden exactamente con `MANIFEST.md`; `git diff --check fbc3fde..f795036` está limpio e identidad de autor/committer de `f795036` es `Pedro Matute <pedromaaz13@gmail.com>`, sin coautor. Sin hallazgos bloqueantes ni menores abiertos; MP-011 pasa a `DONE`.

### Siguiente paso

MP-011 está `DONE`. DEC-015 resuelto y aplicado: MP-012 (ejecutor Codex, revisor Claude Code) ramificó directamente desde `mp-011-osm-geometry` sin fusión real — registrado arriba en "Tarea actual".

**MP-010 — Topología GTFS C5**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-010-gtfs-topology`, ramificada desde `chore/hito-2-coordination` (que a su vez parte de `main`, post-merge de Hito 1 — MP-004, su única dependencia directa, ya es ancestro de `main`).

### Checklist de MP-010

- [x] `packages/gtfs/`: parser en streaming de topología GTFS estático (`routes`/`trips`/`stops`/`stop_times`/`shapes`/`calendar`) desde ZIP o directorio, con comprobación de esquema y sin campos inventados.
- [x] Las 5 variantes `source_route_id` de C5 Madrid (`10T0017C5`, `10T0018C5`, `10T0035C5`, `10T0047C5`, `10T0048C5`) permanecen como rutas distintas y se agrupan por `(network_id, short_name)`.
- [x] Resolución genérica de `route_id`/`trip_id`/`stop_id`: filtros parametrizados, JOIN literal de trip estático, fallback solo para `routeId` explícito de trips `ADDED`, rechazo de contradicciones y prueba que impide literales de línea en la lógica.
- [x] Validación real de recorrido: 14 patrones ordenados, incluidos pares inversos completos y cortos. **Hallazgo:** el GTFS de Renfe no contiene `direction_id`; la dirección verificable es `stop_sequence` + `shape_id`, y no se fabrica una columna ausente.
- [x] **Hallazgo real:** `10T0035C5` tiene 8 trips y cero `stop_times` en el ZIP completo. El validador los informa como huérfanos de fuente y no inventa recorrido.
- [x] Fixture real reducida, reproducible y atribuida (`tests/fixtures/gtfs_c5_real/`): 5 rutas, 15 trips representativos, 23 estaciones, 168 stop_times, 630 puntos de shape y 4 servicios; URL/checksums/proceso en su `MANIFEST.md` (DEC-023).
- [x] 71/71 tests en verde: 7 GTFS nuevos + 64 regresiones (31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL. Ejecución adicional contra el ZIP oficial completo: 5 rutas, 8.160 trips, 23 estaciones, 165.205 stop_times, 630 puntos, 30 servicios, 14 patrones, 8 huérfanos, 0 errores de validación.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md` actualizados con evidencia real antes de delegar a revisión.

### Resultado y límites

Topología C5 parseada y validada contra la descarga oficial del `2026-11-19`. La API queda disponible para MP-012/MP-013 mediante `Topology.resolve_trip_route_id`, `resolve_trip_route` y `resolve_stop_sequences`; opera sobre cualquier línea configurada. El fichero completo no se versiona: son ~15,7 MB comprimidos/~298 MB extraídos y cambia con upstream; se conserva una fixture real mínima reproducible con checksum (DEC-023).

- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Código íntegro de `packages/gtfs/` leído (parser, topology, tests, tool de reducción). 71/71 tests reejecutados de forma propia: 7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter — subiendo y bajando el contenedor `madrid-pulse` yo mismo (no reutilizando solo el reporte de Codex) y confirmando los recuentos reales `668/484/3/120/0` idénticos antes y después, sin residuo. Confirmado con lectura directa que `parser.py`/`topology.py` no contienen el literal `"C5"` y que la resolución es genérica por `route_ids`/`network_id`/`short_name` (ADR-0011) — reforzado por un test de regresión que falla si se reintroduce el literal. `git diff --check` limpio, sin secretos en el diff, identidad Git (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor) y enlaces a ADR-0011/DEC-022/DEC-023 verificados. Fixture reducida (52 KB) con checksum, atribución `CC BY 4.0` y proceso reproducible documentado en su `MANIFEST.md`. Sin hallazgos bloqueantes ni menores.

### Bloqueos

Ninguno. Los 8 trips huérfanos y la ausencia de `direction_id` son propiedades verificadas del upstream, preservadas explícitamente y confirmadas de forma independiente, no defectos ocultos ni datos suplidos.

### Siguiente paso

MP-010 está `DONE`. MP-011 (Prototipo de geometría ferroviaria sobre OSM, ejecutor Claude Code, revisor Codex) ramificó su worktree desde `mp-010-gtfs-topology` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-009 — Exportador histórico (Parquet particionado)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-009-historical-export`, ramificada desde `mp-008-quality-engine` (MP-008 `DONE`)

### Checklist de MP-009

- [x] `services/snapshotter/export.py`: DuckDB como único motor (lee PostgreSQL vía `ATTACH ... TYPE POSTGRES`, escribe Parquet nativo); sin `pandas`/`pyarrow` adicionales (DEC-021).
- [x] Partición `date=YYYY-MM-DD/hour=HH` siempre calculada sobre Europe/Madrid, nunca UTC directo — ver hallazgo real abajo.
- [x] **Hallazgo real:** los datos del soak test de MP-007 (`23:31:42 UTC` 18-nov) pertenecen al día de servicio **19-nov** en Europe/Madrid (CET, UTC+1) — exactamente el error que `docs/DATA_MODEL.md` ya advertía. 3 tests de regresión puros (incluido CEST/verano) en `test_export.py`.
- [x] Test de replay real (`test_export_replay.py`): día de prueba conocido, COMPROMETIDO (no `rollback()`, DuckDB usa conexión `libpq` propia), exportado y verificado sin pérdida; limpieza explícita en `finally`.
- [x] Exportación real completa del día `2026-11-19` (datos reales, no fixtures): 1272 filas (668+484+120+0+0), ~76 KB ZSTD particionado; releído con consulta DuckDB independiente, recuento exacto.
- [x] `services/snapshotter/gold.py`: resumen diario por núcleo (1 fila para Madrid: 668 posiciones/24 vehículos, 484 actualizaciones/24 viajes). **Limitación deliberada documentada:** no calcula `daily_line_metrics`/`station_daily_metrics` (requieren resolución `route_id`/`station_id` diferida a MP-010, ADR-0009) — ver DEC-021.
- [x] CLI (`python -m services.snapshotter YYYY-MM-DD`) probado de punta a punta contra PostgreSQL real.
- [x] 64 tests reales en verde: 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter.
- [x] Identidad Git verificada; contenedor `madrid-pulse` detenido al finalizar la implementación (volumen real conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_d2b95955a73a`): no aprobada** — reejecutó las 64 pruebas, confirmó la conversión Europe/Madrid y el export/gold reales, y encontró un bloqueante real: las 3 `service_alert` reales (ingeridas el 19-nov vía `ingestion_run` 78) desaparecían del export de ese día porque `export.py` particionaba `service_alert` por `active_period_start` (ventana de vigencia del aviso) en vez de por cuándo se observó — esa tabla no tiene columna propia de observación.
- [x] Corregido uniendo `service_alert` a `source_ingestion_run` y usando `started_at` de esa ejecución; verificado revirtiendo el fix (el test ampliado falla `0 != 1` exactamente como reportó Codex) y restaurándolo (pasa). Reexportado el día real: `service_alert` pasa de 0 a 3 filas. Test de replay ampliado para cubrir las 5 tablas (antes solo 2).
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_095ae1499806`): APROBADA** — 2/2 tests de replay ampliados en verde contra PostgreSQL real; limpieza de las 5 tablas confirmada (`vp/tu/alert/dqe/run = 0` tras el test). Export real independiente: 668/484/**3**/120/0; los tres avisos esperados aparecen en Parquet ligados al run 78. Diff, identidad Git y aislamiento de contenedores correctos.

### Resultado y límites

El exportador mueve de verdad datos reales de PostgreSQL a Parquet particionado sin pérdida, con dos trampas reales encontradas y corregidas con evidencia, no solo teóricas: el huso horario Europe/Madrid vs. UTC, y la semántica temporal de `service_alert` (vigencia vs. observación). El agregado gold queda deliberadamente acotado a núcleo (no a línea/estación) hasta que MP-010 resuelva las FK necesarias — documentado, no improvisado.

### Bloqueos

Ninguno: el bloqueante real de la primera revisión de Codex (semántica temporal de `service_alert`) está corregido y re-verificado independientemente; la limitación de alcance del agregado gold está documentada y no bloquea el criterio de aceptación real (replay sin pérdida de la capa raw).

### Siguiente paso

MP-009 y el Hito 1 (`MP-002` → `MP-009`) están completos. El worktree queda listo para revisión del propietario; no se inicia MP-010 ni otro hito hasta que el propietario lo autorice expresamente. **Nota añadida al preparar Hito 2 (`2026-11-19`):** el propietario autorizó y fusionó Hito 1 a `main`; MP-010 arrancó en su propio worktree, registrado arriba en "Tarea actual".

**MP-008 — Quality engine**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-008-quality-engine`, ramificada desde `mp-007-collector` (MP-007 `DONE`)

### Checklist de MP-008

- [x] Cinco flags del `CHECK` de MP-006 implementados: `stale`, `implausible_speed`, `missing_id`, `duplicate_snapshot`, `clock_anomaly`.
- [x] Reglas puras en `packages/quality/engine.py`, separadas de red/BD; capa PostgreSQL en `packages/quality/db.py`.
- [x] Umbrales calibrables y nombrados: stale 180s, velocidad 200km/h, feed congelado 180s, drift de reloj 300s; documentados como puntos de partida, no contrato de Renfe.
- [x] Velocidad implícita calculada por Haversine entre posiciones consecutivas del mismo vehículo, sin usar `speed_kmh` de origen.
- [x] `duplicate_snapshot` opera sobre el hash completo del feed sostenido en el tiempo; dos polls normales iguales no disparan la regla.
- [x] Eventos y `quality_flags` persistidos dentro de la misma transacción atómica del colector; flags de feed no se atribuyen falsamente a una observación.
- [x] 13 tests de calidad: al menos disparo + falso positivo por cada regla, rollover UTC de medianoche y dos integraciones PostgreSQL reales con rollback.
- [x] Suite completa ejecutada: **59/59** (31 contratos + 6 fixtures + 9 colector + 13 calidad), todas `OK`.
- [x] Casos anómalos ausentes de las fixtures reales marcados explícitamente como sintéticos; no se presentan como observados.
- [x] Contenedor `madrid-pulse-postgres-1` dejado levantado para la revisión, volumen real conservado; contenedores `*-traza-app` verificados intactos.
- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Reproducidas
  59/59 pruebas contra el mismo PostgreSQL real (668/484/3/120 registros del
  soak test de MP-007, intactos). Revisado el diseño (reglas puras vs.
  persistencia, transacción atómica, reutilización del patrón `id DESC` de
  MP-007 en el historial de calidad).
  **Hallazgo empírico documentado, no bloqueante:** al repetir 117 pares
  reales de posiciones consecutivas del soak test contra
  `check_implausible_speed`, 12/117 (~10%) dispararon con velocidades
  implícitas de 246–787 km/h. Inspección de la secuencia del vehículo
  `21053` confirmó que son saltos reales entre filas ya almacenadas (20-40s,
  varios km), no un error de cálculo — indica que Renfe actualiza posición
  en saltos más gruesos que el cadencia de poll, no como GPS continuo.
  Registrado para considerarlo al calibrar el umbral en MP-012 (ya
  documentado como "a calibrar, no verdad de diseño").

### Resultado y límites

El motor queda integrado antes de persistir para aprovechar los objetos canónicos de MP-005 y conservar atomicidad con MP-007, sin duplicar el colector. Las reglas geométricas `off_track`, `backward_jump` y `station_skip_anomaly` siguen diferidas a MP-012: requieren map-matching y no caben en el `CHECK` actual.

### Bloqueos

Ninguno. Los umbrales requieren calibración operativa futura (ver hallazgo de `implausible_speed` arriba), tal como exige `docs/DATA_QUALITY.md`, pero no bloquean el punto de partida probado.

### Siguiente paso

MP-008 está `DONE`. MP-009 puede ramificar desde `mp-008-quality-engine` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-007 — Collector idempotente**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-007-collector`, ramificada desde `mp-006-postgis-schema` (MP-006 `DONE`)

### Checklist de MP-007

- [x] `services/collector/http_client.py`: `fetch_with_retry` con backoff exponencial y timeout, solo `urllib` (sin dependencia nueva para HTTP).
- [x] `services/collector/db.py`: capa de acceso a PostgreSQL (MP-006); corregido un bug real de transacciones (ver más abajo) para que cada ciclo se comprometa como unidad atómica.
- [x] `services/collector/collector.py`: `run_cycle` = fetch → parse → filtro de alcance (núcleo Madrid, ADR-0008) → dedupe (ADR-0010) → persist, con el ciclo entero en una sola transacción.
- [x] `services/collector/__main__.py`: bucle de polling infinito, un feed fallido no detiene el colector completo.
- [x] `docs/adr/0010-dedup-strategy.md` (nuevo, `Propuesto`): hash completo de la entidad comparado contra la última fila almacenada por clave de entidad; sin `seen_count`.
- [x] 46 tests reales en verde (31 contratos + 6 fixtures + 9 colector); 5 de los 9 del colector son integración real contra PostgreSQL (no mocks de BD).
- [x] **Soak test real de 20 minutos** contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión `psql` nueva tras el proceso.
- [x] **3 hallazgos reales corregidos** (feed en vivo, no cubiertos por fixtures de MP-003/MP-004): `trip_id` de refuerzo `SPECIAL_<núcleo>_<resto>`, `stopTimeUpdate[].arrival` sin `delay`, respuesta real sin la clave `entity`. Los tres con test de regresión. Detalle en `docs/research/MP-003-probe-findings.md` §10.
- [x] **1 bug de transacciones corregido antes de producción:** `with conn.transaction()` por `INSERT` individual, con una conexión de larga duración, dejaba `vehicle_position_observation` sin comprometer mientras `source_ingestion_run` sí persistía — detectado verificando con una conexión nueva, no confiando en la ausencia de excepción. Corregido centralizando la transacción en `run_cycle`.
- [x] **Hallazgo de alcance documentado, no bloqueante** (DEC-020): el filtro descarta por núcleo (Madrid), no todavía por línea C5 específica (ADR-0001 `Aceptado`) — acotar a C5 requiere la resolución `trip_id`→`route_id` de MP-010.
- [x] Identidad Git verificada en cada commit; contenedor `madrid-pulse` detenido al finalizar (volumen con los datos reales del soak test conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_a674a371ce8a`): no aprobada** — reejecutó las 45 pruebas, consultó el feed vivo (el snapshot puntual no contenía `SPECIAL_`/`ADDED`), confirmó esos casos en el volumen real conservado del soak test y encontró un bloqueante real: `latest_payload_hash` sin desempate (`ORDER BY observed_at DESC` solo) producía una fila duplicada real en su reproducción de 3 ciclos (`(1, 6)` en vez de `(0, 7)` en el tercer ciclo) cuando dos filas de la misma entidad comparten `observed_at`.
- [x] Corregido con `id DESC` como desempate secundario en las 3 consultas de `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix temporalmente y confirmando que el nuevo test (`test_tied_observed_at_does_not_break_dedup_on_third_cycle`) falla exactamente como reportó Codex y pasa con el fix restaurado. 46 tests en verde.
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_801574c4ef71`): aprobada** — inspeccionó el diff de `3f83699`, ejecutó el test de regresión específico contra PostgreSQL real (`OK`) y repitió las 46 pruebas completas (31 contratos + 6 fixtures + 9 colector, todas `OK`). Confirmado que `id DESC` resuelve el empate en las tres consultas de deduplicación. **APROBADO.**

### Resultado y límites

El colector ingiere y deduplica de verdad contra el feed en vivo de Renfe, con evidencia de ejecución sostenida de 20 minutos sin errores. No resuelve `trip_id` contra el GTFS estático (diferido a MP-010 por ADR-0009) ni acota a C5 específicamente (DEC-020) — ambas limitaciones ya estaban previstas y documentadas antes de empezar la tarea, no son hallazgos de última hora sin plan.

### Bloqueos

Ninguno. El bloqueante real encontrado por la primera revisión de Codex (dedup no determinista) está corregido y verificado independientemente; los dos puntos de alcance documentados no bloquean el cierre de MP-007 según los criterios de aceptación de `docs/TASKS.md`.

### Siguiente paso

MP-007 está `DONE`. MP-008 puede abrir su worktree desde `mp-007-collector` conforme al hito autorizado y al modelo de autonomía de ADR-0007, sin esperar merge a `main`.

**MP-006 — Esquema PostgreSQL/PostGIS v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-006-postgis-schema`, ramificada desde `mp-005-contrato-canonico` (MP-005 `DONE`)

### Checklist de MP-006

- [x] Compose aislado: proyecto `madrid-pulse`, imagen `postgis/postgis:17-3.5`,
  puerto `127.0.0.1:5433`, red y volumen nombrados propios; los contenedores
  `*-traza-app` no se tocaron.
- [x] `0001_init.up.sql` transaccional: PostGIS y las 14 entidades de aplicación
  (más `source_feed_version`, exigida por el versionado GTFS y su FK), constraints
  e índices B-tree/GIST.
- [x] Correspondencia canónica documentada: `entity_count`, `affected_route_ids`,
  `latitude`/`longitude`, `raw_vehicle_label`, `next_stop_id`,
  `nucleo_prefix`/`nucleo_name`/`nucleo_prefixes`; `geom` generado desde las
  coordenadas y nullable cuando la fuente no aporta posición.
- [x] Migración aplicada sobre PostgreSQL/PostGIS real con `ON_ERROR_STOP=1`:
  `CREATE TABLE` ×14, `CREATE INDEX` ×5 y `COMMIT`; PostGIS `3.5.2`.
- [x] Datos válidos insertados; `geom` generado como `POINT(-3.689 40.406)` y
  observación sin posición persistida con `latitude`, `longitude` y `geom` nulos.
- [x] Constraints probadas con fallos reales (todos exit 1): duplicado de
  `(network_id, source_route_id)`, de `(service_date, source_trip_id)` y de
  `(ingestion_run_id, payload_hash)` rechazados por sus `UNIQUE` respectivos.
- [x] Rollback real con `ON_ERROR_STOP=1`: 14 tablas eliminadas y `COMMIT`;
  consulta posterior `remaining_application_tables = 0`. PostGIS se conserva
  porque la imagen instala extensiones dependientes antes de la migración.
- [x] Ciclo final `down → up` repetido desde cero: ambos comandos exit 0.
- [x] Suites de regresión reejecutadas: contratos 23/23 `OK`; fixtures 6/6 `OK`.
- [x] `docker compose ... config --quiet` y `git diff --check`: exit 0.
- [x] Contenedor de Madrid Pulse detenido al finalizar; volumen propio conservado
  con la migración final aplicada para que el propietario pueda reanudarlo.
- [x] Revisión independiente de Claude Code (2026-11-19): **APROBADA**. Reproducido
  el ciclo completo de forma propia (no solo verificado el reporte de Codex):
  rollback necesario primero porque el volumen ya tenía el esquema cargado, luego
  `up → datos de prueba → 3 duplicados rechazados → down → up` otra vez, todo
  `exit 0`/`exit 1` según corresponde. GIST confirmados en `vehicle_position_observation.geom`
  y `station.geom`. Confirmada la ausencia real de `effect`/`cause`/`header_text`
  y `current_stop_sequence`. Suites de regresión reejecutadas de forma
  independiente (23/23 y 6/6). `check_links.py`: 46 enlaces, ninguno roto.
  Identidad Git verificada. Contenedores `*-traza-app` intactos.
  **Hallazgo (corregido en esta misma revisión):** este documento había
  reemplazado el registro completo de MP-005 en "Tarea actual" por el de MP-006
  sin archivarlo primero aquí, rompiendo el patrón de MP-002/MP-003/MP-004 —
  corregido moviendo el registro íntegro de MP-005 a esta sección.

### Resultado y límites

SQL plano permite auditar el DDL inicial sin introducir todavía un framework de
migraciones. El rollback elimina el esquema de aplicación pero no usa
`DROP EXTENSION ... CASCADE`: las extensiones PostGIS dependientes vienen
preinstaladas por la imagen y no pertenecen a esta migración.

### Bloqueos

Ninguno.

### Siguiente paso

MP-006 está `DONE`. MP-007 puede ramificar desde `mp-006-postgis-schema` sin
esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-005 — Contrato canónico interno**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-005-contrato-canonico`, ramificada desde `mp-004-fixtures` (MP-004 `DONE`)

### Checklist de MP-005

- [x] `packages/contracts/raw.py`: modelos Pydantic que reflejan exactamente el JSON bruto observado en MP-003/MP-004 (sin inventar campos); acepta campos nuevos no verificados sin fallar (`extra="ignore"`).
- [x] `packages/contracts/nucleo.py`: tabla de prefijos de núcleo verificada en MP-003, con `is_madrid`/`nucleo_name`.
- [x] `packages/contracts/canonical.py`: `VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth` — UTC siempre, dato ausente = `None` nunca `0`, `nucleo_prefix` derivado como `computed_field` (no aceptado como entrada independiente).
- [x] `packages/contracts/normalize.py`: funciones puras `raw → canonical`, sin red ni base de datos.
- [x] 23 tests reales ejecutados (`python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`) → `OK`: parseo contra fixtures reales, normalización (incluido el test de colisión núcleo/C5 a nivel de contrato canónico), sintéticos (JSON Schema, rechazo de datos inválidos, caso multi-núcleo no observado), enforcement UTC y regresión de campos `raw` no observados.
- [x] **Hallazgo:** `docs/DATA_MODEL.md` asumía `speed_kmh`/`bearing`/`current_stop_sequence` y `effect`/`cause`/`header_text` de alertas que el feed real NUNCA emite (verificado contra ~800 entidades combinadas de MP-003/MP-004). Corregido `docs/DATA_MODEL.md`, `docs/DATA_QUALITY.md` (nota sobre cómo calcular `implausible_speed` sin un campo de origen), registrado DEC-018/ADR-0009 (`Propuesto`).
- [x] Autocorregido antes de delegar: una edición introdujo una fila duplicada en `docs/DATA_QUALITY.md` (`off_track` repetida) — detectado y corregido en la misma ronda, sin necesitar que Codex lo señalara.
- [x] Primera revisión independiente de Codex (dispatch `ctx_ea1d5cf46d74`): **no aprobada** — reejecutó la suite (17/17 OK en su entorno) y auditó el diff campo a campo. 3 bloqueantes + 1 menor:
  - **Bloqueante 1:** `RawActivePeriod.end` no tenía el comentario de "campo opcional no observado" que sí llevan los demás campos documentados tras el hallazgo de MP-005 — se corrigió **añadiendo un comentario**, lo que resultó insuficiente (ver 2ª ronda).
  - **Bloqueante 2:** el esquema canónico documentaba "UTC siempre" pero no lo exigía — un `datetime` naive o con offset no UTC pasaría la validación sin error. Corregido con `field_validator` en los 4 modelos (`VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth`), con 5 tests nuevos que prueban el rechazo real.
  - **Bloqueante 3:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato original (`deep-research-report.md`) queda contradicho por esta verificación — añadida la fila correspondiente sin editar el documento de investigación congelado.
  - **Menor:** `ADR-0009` decía erróneamente que Codex podía promover el ADR a `Aceptado` (contrario a `AGENTS.md`/ADR-0007: solo el propietario puede) — corregido; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos) — corregido.
- [x] Segunda revisión independiente de Codex (dispatch `ctx_ded900b82f20`): **no aprobada** — señaló correctamente que un comentario no resuelve una contradicción: `raw.py:1-9` declara explícitamente que el módulo no debe contener campos no observados, y `RawActivePeriod.end` seguía ahí. Corregido de verdad esta vez: `end` **eliminado** de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; añadido un test de regresión (`test_raw_active_period_has_no_unobserved_end_field`) que falla si alguien lo reintroduce sin verificarlo, incluso si el JSON de origen lo trae (se ignora por `extra="ignore"`). 23 tests en total.
- [x] Tercera revisión independiente de Codex: **APROBADA**, sin hallazgos abiertos — reejecutó 23/23 tests; confirmó independientemente que `RawActivePeriod.model_fields == {"start"}`, que un `end` extra se ignora sin convertirse en atributo, que fechas naive y `+02:00` se rechazan mientras UTC se acepta, y que trazabilidad, ADR, enlaces, secretos y whitespace son coherentes.

### Resultado y límites

El contrato canónico se valida contra datos reales (MP-004) y sintéticos. La separación `raw`/`canonical` evita que un cambio futuro del feed de Renfe se propague directamente al resto del sistema sin pasar por una capa de normalización explícita. Los hallazgos de campos no observados (ADR-0009) son correcciones al modelo candidato de MP-001, no contradicciones nuevas sin resolver.

### Bloqueos

Ninguno.

### Siguiente paso

MP-005 está `DONE`. MP-006 pudo ramificar desde esta rama sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-004 — Fixtures reproducibles**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-004-fixtures`, ramificada desde `mp-003-probe-c5` (MP-003 `DONE`)

### Checklist de MP-004

- [x] Capturas frescas directas de `vehicle_positions.json`, `trip_updates.json` y `alerts.json`: `200 application/json`, sin guardar cabeceras ni cookies.
- [x] Tres fixtures JSON reducidas y versionables: 394 → 10 posiciones, 401 → 8 actualizaciones y 76 → 3 alertas.
- [x] Cada fixture conserva entidades de Madrid; posiciones conserva además C5 con prefijos `20`, `30` y `40` para probar la colisión entre núcleos.
- [x] `tests/fixtures/MANIFEST.md` registra fecha UTC, endpoint, recuentos y SHA-256.
- [x] Tests offline con Python `unittest`: envoltura GTFS-RT, esquema por feed, integridad SHA-256, cobertura Madrid y rechazo del filtro ingenuo por etiqueta C5.
- [x] Ejecución real: `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v` → 6 tests, `OK` (0.001 s).
- [x] Los tres ficheros pasan `python3 -m json.tool`; hashes re-verificados con `shasum -a 256`.
- [x] Revisión independiente de Claude Code: SHA-256 recalculados de forma propia (coinciden), suite re-ejecutada (6/6 `OK`), inspección del test de colisión C5 confirmando que es sustantivo (un filtro ingenuo por etiqueta captura 4 núcleos, el correcto aísla solo Madrid), sin cookies/secretos, enlaces y licencias revalidados. **APROBADO.**

### Resultado y límites

Las fixtures se cargan exclusivamente desde disco y no incluyen código de red ni dependencias externas. La captura de posiciones no contenía ninguna entidad sin `position`; el caso observado en MP-003 no se fabricó. `pytest` no estaba instalado, por lo que se eligió `unittest` de la biblioteca estándar para mantener la suite reproducible sin instalación adicional.

### Bloqueos

Ninguno.

### Siguiente paso

MP-004 está `DONE`. MP-005 (Contrato canónico interno, ejecutor Claude Code, revisor Codex) puede ramificar desde `mp-004-fixtures` sin esperar merge a `main`.

**MP-003 — Probe real de feeds C5 (GTFS + GTFS-RT)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-003-probe-c5`, ramificada desde `mp-002-fuentes-licencias` (MP-002 `DONE`)

### Checklist de MP-003

- [x] `vehicle_positions.json` probado en vivo: `200 OK`, JSON real (GTFS-RT 2.0), 3 polls espaciados ~20 s confirmando frecuencia de refresco real (~20–22 s).
- [x] `trip_updates.json` probado en vivo: `200 OK`, 302 entidades, esquema con `delay` en segundos por parada.
- [x] `alerts.json` probado en vivo: `200 OK`, 82 alertas activas, confirma `routeId` completo por entidad informada.
- [x] GTFS estático descargado realmente (15,7 MB, `200 OK`) desde el enlace real (`ssl.renfe.com`, distinto del enlace de portal que había fallado en MP-002) e inspeccionado (`routes/trips/stops/calendar/shapes/stop_times/transfers/agency.txt`).
- [x] **Hallazgo crítico:** "C5" no es único — existe también en Asturias (`20T0011C5`) y Andalucía (`30T0009C5`) en el mismo feed nacional. Registrado como DEC-017/ADR-0008 (`Propuesto`); `docs/DATA_MODEL.md` corregido.
- [x] Resolución de `trip_id` del feed en vivo contra GTFS estático: **igualdad literal de cadena** contra el campo `trip_id` de `trips.txt` (3er campo del CSV), confirmado 403/403 (y 404/404 en la re-verificación de Codex con datos frescos) — es un `JOIN` directo, no requiere reconstrucción por `(service_id, vehículo, línea)`.
- [x] `docs/legal/DATA_SOURCES.md` actualizado de `PENDING MP-003` a `VERIFIED` para los 4 recursos Renfe.
- [x] `docs/research/MP-003-probe-findings.md`, `docs/TASKS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` actualizados.
- [x] Primera revisión independiente de Codex (dispatch `ctx_61d7dd4fd86b`): **no aprobada** — repitió los probes en vivo él mismo (no solo leyó el reporte), incluida una comparación sistemática `comm -12`/`comm -23` de los 403 `trip_id` en vivo contra `trips.txt`. 2 bloqueantes + 2 menores:
  - **Bloqueante 1:** 403/403 `trip_id` en vivo coinciden literalmente con `trips.txt` — contradice la afirmación anterior de este documento. Causa raíz: un `grep` propio anclado al campo equivocado (`trip_id` es el 3er campo de `trips.txt`, no el 1º). Corregido en `docs/research/MP-003-probe-findings.md` §7 con la comparación de conjuntos completa.
  - **Bloqueante 2:** `docs/DATA_MODEL.md` tenía `UNIQUE(network_id, source_route_id)` junto con una nota que agrupaba 5 `source_route_id` bajo un único `route.id` — cardinalidad imposible. Corregido: 5 filas `route.id`, agrupadas por `(network_id, short_name)`.
  - **Menor:** findings afirmaba falsamente que el GTFS no incluía `shapes.txt` (sí lo incluye, está en la propia tabla del documento). Corregido.
  - **Menor:** no se había medido la frecuencia de `trip_updates`/`alerts` (solo `vehicle_positions`). Medido: `trip_updates` Δ42s, `alerts` Δ20s (2 polls cada uno).
  - Codex confirmó que el resto de pendientes (cobertura larga de `trip_updates`, CRTM, shapes/stop_times detallados, cambio de día) están razonablemente fuera de alcance de MP-003.
- [x] Revisión final independiente de Codex: **APROBADA**, sin hallazgos abiertos. Repetida la comparación con datos frescos: 404/404 `trip_id` vivos coinciden literalmente con `trips.txt`, 0 sin match. Confirmada la coherencia de cardinalidad entre `docs/DATA_MODEL.md`, DEC-017 y ADR-0008; enlaces, secretos y licencias revalidados.

### Resultado y límites

Los tres feeds GTFS-RT y el GTFS estático están disponibles, accesibles y documentados con esquema real. El hallazgo de la colisión de "C5" entre núcleos es el resultado más importante de esta tarea y obliga a una corrección de `docs/DATA_MODEL.md` (ver DEC-017/ADR-0008, `Propuesto`, pendiente de promoción por el propietario).

**Pendiente explícito, no bloqueante para MP-003, a resolver en tareas posteriores:** cobertura real de `trip_updates` para Madrid en ventana más larga (en el único poll realizado, Madrid tuvo 0/302 — no se puede concluir si es casualidad puntual o un patrón, ver findings §5); descarga del GTFS de CRTM (el NAP exigía login, no se probó); validación detallada de `shapes`/`stop_times` de las 5 variantes de C5 Madrid (corresponde a MP-010); comportamiento en cambio de día de servicio (corresponde a MP-012).

### Bloqueos

Ninguno. El hallazgo de la colisión de "C5" no bloquea MP-003 (ya está documentado y corregido en el modelo); sí debe tenerse en cuenta en MP-005 (contrato canónico) y MP-007 (colector) antes de implementarlos.

### Siguiente paso

MP-004 puede ramificar desde `mp-003-probe-c5` conforme al hito autorizado y al grafo de dependencias; no necesita esperar a que el propietario fusione esta rama a `main`.

### MP-001 y MP-002 — cerradas en ramas anteriores de esta cadena

**MP-002 — Matriz de fuentes y licencias**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado por Claude Code el 2026-11-18)

Worktree/rama: `mp-002-fuentes-licencias`

### Checklist de MP-002

- [x] Documentación y ADRs obligatorios leídos antes de modificar archivos.
- [x] Renfe GTFS estático verificado como `CC BY 4.0` en el recurso oficial.
- [x] Renfe GTFS-RT Vehicle Positions, Trip Updates y Alerts verificados como `CC BY 4.0` en sus datasets oficiales.
- [x] Condiciones adicionales de Renfe Data verificadas: atribución, actualización, conservación de metadatos y no patrocinio.
- [x] GTFS Cercanías Madrid identificado en Comunidad de Madrid/NAP y licencia propia `CRTM-LDA` verificada en CRTM.
- [x] Requisitos CRTM documentados: `Powered by CRTM`, bruto/explotado, actualización/metadatos, no falseamiento/no patrocinio.
- [x] OpenStreetMap verificado como `ODbL-1.0`; consulta/base colectiva separadas de una base derivada distribuida.
- [x] `LICENSE` de Via Península verificado como `AGPL-3.0`; política de no copiar código preservada.
- [x] `LICENSE` de Niltra/cercanias verificado como MIT.
- [x] `LICENSE` de atlas-ferroviario verificado: MIT para código más aviso Renfe `CC BY 4.0` para datos.
- [x] Valfiguer verificado: datos/API normalizados `CC BY 4.0`; no se localizó repo público de implementación ni licencia de código (DEC-016).
- [x] Dataset estadístico Comunidad de Madrid 1923861 verificado como `CC BY 4.0` y de ámbito declarado nacional.
- [x] `DATA_SOURCES.md`, `LICENSE_MATRIX.md` y `ATTRIBUTION.md` actualizados con evidencia y fecha real.
- [x] `TASKS.md`, `STATUS.md`, `CHANGELOG.md` y `DECISIONS.md` actualizados.
- [x] Revisión independiente de Claude Code: re-verificación propia (no solo lectura del reporte de Codex) vía `gh api` y fetch directo de `data.renfe.com`, `crtm.es` y los ficheros `LICENSE` reales de los tres repos de referencia. Todas las afirmaciones de Codex se confirmaron exactas, incluido el matiz MIT-pero-`NOASSERTION` de atlas-ferroviario. **APROBADO.**

### Resultado y límites

No apareció una incompatibilidad que bloquee el uso previsto de las fuentes primarias. Renfe y CRTM permiten reutilización comercial y no comercial con sus respectivas condiciones; OSM es utilizable con atribución, pero una base derivada distribuida debe cumplir ODbL. Via Península permanece estrictamente como referencia conceptual por AGPL.

La verificación de MP-002 cubre **licencia y atribución**, no disponibilidad técnica, esquema, frecuencia ni cobertura C5. Esas propiedades siguen `PENDING MP-003`. El portal Renfe mostraba un fallo histórico SSL en el comprobador del recurso GTFS estático y NAP pedía inicio de sesión para descargar el GTFS CRTM; ambos se probarán técnicamente en MP-003 y no alteran la licencia verificada.

### Bloqueos

Ninguno. La licencia desconocida de la implementación Valfiguer no bloquea porque DEC-006 prohíbe usarla como dependencia de producción; queda registrada en DEC-016 y en la matriz.

### Siguiente paso

MP-002 está `DONE`. MP-003 ramifica desde esta rama (`mp-002-fuentes-licencias`) sin esperar merge a `main`, conforme a ADR-0007.

### Nota de proceso (ramas encadenadas)

Esta rama se bifurcó de `chore/mp-001-foundation` en el commit `3e7b533`, **antes** de que esa rama recibiera un commit posterior (`fac945c`) registrando la aceptación de MP-001 por el propietario y la autorización de Hito 1. Codex infirió correctamente esa autorización por el contexto del encargo (no por leer un `STATUS.md` ya actualizado, que en esta rama no existía todavía) y la registró aquí de forma independiente. Resultado: `chore/mp-001-foundation` y esta rama tienen ahora dos redacciones distintas, pero no contradictorias, de "MP-001 está DONE / Hito 1 autorizado". Claude Code alineó el campo `Estado` de MP-001 en `docs/TASKS.md` de ambas ramas a `DONE` para que la reconciliación en el merge final sea trivial. **Lección para hitos futuros:** si se edita el `STATUS.md` de la rama base después de que una rama hija ya se bifurcó, esa edición no llega a la hija automáticamente — hay que reconciliarla explícitamente, como aquí.

## Bitácora

| Timestamp UTC | Tarea | Evento | Evidencia |
|---|---|---|---|
| `2026-11-18` | MP-001 | Revisión cruzada aprobada; tarea tratada como `DONE` para la cadena autorizada | `docs/TASKS.md`; dispatch de revisión `ctx_0ee25a6a5d2c` |
| `2026-11-18` | Hito 1 | Propietario autoriza explícitamente `MP-002` → `MP-009` | Despacho Orca de MP-002 (`task_8f7f49749f10`) |
| `2026-11-18T15:16:53Z` | MP-002 | Cierre de verificación formal de licencias y condiciones | Checklist y enlaces en `docs/legal/DATA_SOURCES.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Hallazgo Valfiguer: datos/API `CC BY 4.0`, implementación sin repo/licencia verificable | DEC-016; `docs/legal/LICENSE_MATRIX.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Entregables documentales completados; tarea pasa a `REVIEW` | `docs/TASKS.md`; commit local de MP-002 |
| `2026-11-18` | MP-002 | Revisión independiente de Claude Code (gh api + fetch directo de Renfe/CRTM/LICENSE reales): **APROBADO**, sin hallazgos bloqueantes ni menores sobre el contenido. Hallazgo de proceso (divergencia de ramas) documentado y reconciliado | — |
| `2026-11-18T15:28–15:31Z` | MP-003 | Probe real de los 3 feeds GTFS-RT (3 polls de `vehicle_positions` espaciados ~20 s, 1 poll de `trip_updates` y `alerts`) y descarga real del GTFS estático (15,7 MB) | `docs/research/MP-003-probe-findings.md` |
| `2026-11-18` | MP-003 | Hallazgo crítico: "C5" no es único en el feed nacional (también en Asturias y Andalucía); corregido `docs/DATA_MODEL.md`, registrado DEC-017/ADR-0008 (`Propuesto`) | `docs/DECISIONS.md`; `docs/adr/0008-route-identity.md` |
| `2026-11-18` | MP-003 | Entregables completados; tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | `docs/TASKS.md`; commit local de MP-003 |
| `2026-11-18` | MP-003 | Revisión de Codex (repitiendo probes en vivo él mismo): no aprobada — 2 bloqueantes (trip_id sí coincide literalmente con trips.txt; cardinalidad imposible en DATA_MODEL.md) + 2 menores (shapes.txt sí incluido; faltaba medir frecuencia de trip_updates/alerts) | dispatch `ctx_61d7dd4fd86b` |
| `2026-11-18` | MP-003 | Los 4 hallazgos corregidos tras verificación propia (comparación de conjuntos 403/403, medición real de trip_updates Δ42s y alerts Δ20s); reenviado a Codex | `bdf263e` |
| `2026-11-18` | MP-003 | Segunda revisión de Codex (con descarga fresca, 404/404 confirmado): **no aprobada** — hallazgo menor residual: `docs/STATUS.md` conservaba la afirmación bloqueante ya desmentida en un bullet que no se había actualizado; además "alerts sin cambios de contenido" se basaba solo en igual recuento, no en comparación real de contenido | dispatch `ctx_e4a31f1e7e61` |
| `2026-11-18` | MP-003 | Revisión final de Codex: **APROBADA** — 404/404 `trip_id` resueltos por igualdad literal, 0 sin match; cardinalidad, documentación, enlaces, secretos y licencias coherentes. MP-003 pasa a `DONE` | revisión posterior a `f6d8ee9` |
| `2026-11-18T16:01Z` | MP-004 | Capturas frescas de los 3 feeds; fixtures reducidas 394→10, 401→8 y 76→3 con hashes SHA-256 documentados | `tests/fixtures/MANIFEST.md` |
| `2026-11-18T16:04Z` | MP-004 | Suite offline ejecutada: 6 tests `unittest`, `OK`; JSON y hashes revalidados; tarea pasa a `REVIEW` | `tests/fixtures/test_parse_fixtures.py`; `docs/TASKS.md` |
| `2026-11-18` | MP-004 | Revisión independiente de Claude Code: hashes y suite re-ejecutados, test de colisión C5 inspeccionado y confirmado sustantivo. **APROBADO**, sin hallazgos. MP-004 pasa a `DONE` | commit pendiente |
| `2026-11-18` | MP-005 | Contrato canónico implementado (`packages/contracts/`) con 17 tests reales (reales + sintéticos) ejecutados en verde | commit pendiente |
| `2026-11-18` | MP-005 | Hallazgo: `speed_kmh`/`bearing`/`current_stop_sequence`/`effect`/`cause`/`header_text` del modelo candidato nunca aparecen en el feed real; corregidos `docs/DATA_MODEL.md`/`docs/DATA_QUALITY.md`, registrado DEC-018/ADR-0009 (`Propuesto`) | — |
| `2026-11-18` | MP-005 | Tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | — |
| `2026-11-18` | MP-005 | Primera revisión de Codex: no aprobada — 3 bloqueantes + 1 menor, todos reales (comentario inconsistente, falta de enforcement UTC, falta de trazabilidad, redacción incorrecta en ADR-0009) | dispatch `ctx_ea1d5cf46d74` |
| `2026-11-18` | MP-005 | Los 4 hallazgos corregidos: `require_utc`/`require_utc_or_none` añadidos con 5 tests nuevos (22 en total), `TRACEABILITY.md` actualizado, `ADR-0009` y `raw.py` corregidos; reenviado a Codex | commit `cf11012` |
| `2026-11-18` | MP-005 | Segunda revisión de Codex: no aprobada — el bloqueante 1 de la ronda anterior solo se había documentado con un comentario, no resuelto; `raw.py` seguía declarando `end` pese a que el propio módulo prohíbe campos no observados | dispatch `ctx_ded900b82f20` |
| `2026-11-18` | MP-005 | `end` eliminado de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; test de regresión añadido (23 tests); reenviado a Codex para tercera verificación | commit `a9b1172` |
| `2026-11-18` | MP-005 | Tercera revisión independiente de Codex: **APROBADA** — 23/23 tests, esquema `raw`, enforcement UTC, trazabilidad, ADR, enlaces, secretos y whitespace verificados; tarea pasa a `DONE` | revisión posterior a `a9b1172` |
| `2026-11-18T22:53:33Z` | MP-006 | Migración PostGIS aplicada, constraints probadas con duplicados reales, rollback verificado (`0` tablas de aplicación) y ciclo final `down → up` completado; tarea pasa a `REVIEW` | `infra/migrations/`; salida real de `psql` documentada en TASKS/checklist |
| `2026-11-19` | MP-006 | Revisión independiente de Claude Code: ciclo `up/down/up` reproducido desde cero en el worktree, 3 `UNIQUE` rechazados de verdad, 2 `GIST` confirmados, ausencia de campos no observados verificada, suites de regresión reejecutadas (23/23, 6/6), 46 enlaces sin romper. **APROBADA**. Hallazgo de proceso: `STATUS.md` había perdido el checklist completo de MP-005 al no archivarlo antes de escribir el de MP-006; corregido en la misma revisión. Tarea pasa a `DONE` | commit `30507cf`; commit de revisión pendiente |
| `2026-11-18T23:31Z–23:51Z` | MP-007 | Soak test real de 20 min contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 insertadas/304 dedup/2622 fuera de alcance; durabilidad confirmada con conexión `psql` nueva | `services/collector/`; log del soak test |
| `2026-11-18` | MP-007 | 3 hallazgos reales corregidos (trip_id `SPECIAL_`, `arrival` sin `delay`, `entity` ausente) y 1 bug de transacciones corregido antes de producción (commits parciales con conexión de larga duración); tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `packages/contracts/nucleo.py`; `packages/contracts/raw.py`; `services/collector/db.py` |
| `2026-11-19` | MP-007 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (dedup no determinista por `observed_at` empatado, fila duplicada real en reproducción de 3 ciclos) | dispatch `ctx_a674a371ce8a` |
| `2026-11-19` | MP-007 | Corregido con `id DESC` como desempate en `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix y confirmando que el test de regresión reproduce exactamente el fallo reportado y pasa con el fix restaurado; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-007 | Segunda revisión independiente de Codex: test específico y suite completa (46/46) reejecutados contra PostgreSQL real; fix de desempate confirmado. **APROBADA**. MP-007 pasa a `DONE` | dispatch `ctx_801574c4ef71`; commit de revisión pendiente |
| `2026-11-19` | MP-008 | Motor de cinco reglas implementado e integrado transaccionalmente en el colector; umbrales calibrables documentados y reglas geométricas diferidas explícitamente a MP-012 | `packages/quality/`; `services/collector/` |
| `2026-11-19` | MP-008 | Suite completa ejecutada contra PostgreSQL real: 59/59 (31 contratos + 6 fixtures + 9 colector + 13 calidad), incluidos 10 casos mínimos disparo/no-disparo, medianoche UTC y persistencia/feed congelado con rollback. Tarea pasa a `REVIEW` para Claude Code | `packages/quality/tests/`; dispatch `ctx_63638731fde4` |
| `2026-11-19` | MP-008 | Revisión independiente de Claude Code: 59/59 reproducidas contra el mismo PostgreSQL real; diseño auditado. Hallazgo empírico no bloqueante: 12/117 pares reales de posiciones consecutivas del soak test disparan `implausible_speed` (246–787 km/h) — saltos reales de posición, no bug de cálculo; registrado para calibración en MP-012. **APROBADA**. Tarea pasa a `DONE` | commit `c3db20b`; commit de revisión pendiente |
| `2026-11-19` | MP-009 | Exportador DuckDB implementado; hallazgo real de huso horario (Europe/Madrid vs. UTC) encontrado y corregido antes de delegar; export real del 19-nov (1272 filas, ~76 KB ZSTD) y test de replay verificados; tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `services/snapshotter/`; commit `0119c6a` |
| `2026-11-19` | MP-009 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (3 `service_alert` reales desaparecían del export por particionar por `active_period_start` en vez de por observación real vía `ingestion_run_id`) | dispatch `ctx_d2b95955a73a` |
| `2026-11-19` | MP-009 | Corregido uniendo `service_alert` a `source_ingestion_run`; replay ampliado a las 5 tablas; verificado revirtiendo el fix (falla `0≠1` como reportó Codex) y restaurándolo; reexportado el día real: `service_alert` pasa de 0 a 3; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-009 / Hito 1 | Segunda revisión independiente de Codex aprobada: replay ampliado 2/2, limpieza completa, export real 668/484/3/120/0 y tres alertas confirmadas en Parquet. MP-009 pasa a `DONE`; Hito 1 (`MP-002` → `MP-009`) completo, pendiente de decisión del propietario sobre el siguiente hito | dispatch `ctx_095ae1499806` |
| `2026-11-19` | Hito 1 | Auditoría independiente de Codex (dispatch no registrado como `ctx_` en esta rama, ver worktree `mp-009-historical-export`): **APROBADA**, sin bloqueantes. Propietario crea PR #1 (`mp-009-historical-export` → `main`) y lo fusiona él mismo | PR #1; commit de merge `f567d3c` |
| `2026-11-19` | Hito 2 | Propietario autoriza explícitamente `MP-010` → `MP-015` ("Live Railway MVP"), fija la tabla ejecutor/revisor, la política de selección de modelo y los límites de autonomía (sin push/PR/merge sin autorización puntual; identidad Git exclusiva del propietario; sin coautores de agente) | mensaje de autorización del propietario, `2026-11-19` |
| `2026-11-19` | Hito 2 | Sincronización inicial: `git fetch`/`git pull --ff-only` confirma `main` local al día con `origin/main`; verificado que `8be1272` (tope de `mp-009-historical-export`) es ancestro de `f567d3c`, sin commits perdidos. Verificación empírica (no asumida) de que `orca orchestration worker-start --model/--effort` son parámetros reales para Claude; identificadores confirmados `sonnet`/`opus` (no existe un "5.5" verificable en este entorno) | `agent-context.json`; `worker-start --help` |
| `2026-11-19` | Hito 2 | DEC-015 resuelto: con Hito 1 ya en `main`, la convergencia de MP-012 (MP-008+MP-010+MP-011) no requiere `git merge` real — basta ramificar la cadena MP-010→MP-011 desde una rama que ya contenga a `main` (y por tanto a MP-008) como ancestro; mecanismo general documentado en `AGENTS.md` para casos futuros con divergencia real | este documento; `AGENTS.md` |
| `2026-11-19` | Hito 2 | ADR-0011 (`Propuesto`) redactado: distingue el piloto técnico de Hito 2 (C5) del objetivo de primera versión pública (toda la red de Cercanías Madrid), sin reescribir ADR-0001 (`Aceptado`) — amplía su alcance de implementación sin contradecir su decisión ya aceptada | `docs/adr/0011-public-scope-vs-technical-pilot.md` |
| `2026-11-19` | Hito 2 | Worktrees de MP-010 (ejecutor Codex) y, tras su cierre, MP-011 (ejecutor Claude Code) preparados ramificando desde esta rama de coordinación (`chore/hito-2-coordination`, a su vez ramificada desde `main`) | `docs/TASKS.md` |
| `2026-11-19` | MP-010 | Parser/validador GTFS implementado; 71/71 tests (7 nuevos + 64 regresiones, 9 integraciones PostgreSQL reales) y ejecución adicional contra ZIP oficial completo (5 rutas, 8.160 trips, 165.205 stop_times, 14 patrones, 8 huérfanos, 0 errores). Hallazgos: upstream sin `direction_id` y variante `10T0035C5` sin stop_times. Compose Madrid Pulse detenido sin borrar volumen; `*-traza-app` intactos. Tarea pasa a `REVIEW` para Claude Code | `packages/gtfs/`; `tests/fixtures/gtfs_c5_real/MANIFEST.md`; DEC-023 |
| `2026-11-19` | MP-010 | Revisión independiente de Claude Code: código íntegro leído, 71/71 tests reejecutados subiendo/bajando el contenedor propio, recuentos reales `668/484/3/120/0` confirmados idénticos antes/después, ausencia del literal `"C5"` en la lógica verificada, identidad Git y enlaces a ADR-0011/DEC-022/DEC-023 correctos. **APROBADA, sin hallazgos.** MP-010 pasa a `DONE` | commit `add8aa6`; este documento |
| `2026-11-19` | MP-011 | Geometría OSM real implementada (`packages/geo/`): 4 relaciones direccionales de C5 Madrid descargadas y encadenadas sin huecos; 23 estaciones reales proyectadas en orden monótono (máx. 63,7 m); ruta corta confirmada como subsegmento del corredor largo. Evidencia visual real en navegador (Chrome DevTools MCP). 78/78 tests en verde. Hallazgos documentados como ambigüedades (DEC-025), no forzados: relaciones Fuenlabrada-truncadas sin coincidir con la ruta corta real, `usage=main`/`branch` sin verificar reparto exacto, huérfano `10T0035C5` aún sin validar. Overpass API devolvió `502` por capacidad varias veces; reintentos con pocos segundos de espera tuvieron éxito. Fixture ODbL congelada y atribuida (DEC-024). Tarea pasa a `REVIEW` para OpenAI Codex | `packages/geo/`; `tests/fixtures/osm_c5_real/MANIFEST.md`; DEC-024; DEC-025 |
| `2026-11-19` | MP-011 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (`ChainGap` registrado pero la geometría seguía fabricando una unión a través del hueco; repro sintética con `distance_m=0.0`) + 2 menores (recuento de tests incorrecto; una variante real de 7 estaciones de `10T0047C5` se documentó como "subsegmento contiguo" sin serlo) + checksums anunciados pero ausentes | dispatch `ctx_6b6ad999cdfe` |
| `2026-11-19` | MP-011 | Corregido: `Corridor.segments` separa tramos reales (verificado revirtiendo el fix — el test de regresión falla exactamente como describió Codex y pasa con el fix restaurado); `render_preview.py` dibuja un `<polyline>` por tramo; ruta corta dividida en variante base contigua (6 estaciones, verificado por comparación literal de IDs) y variante con Atocha monótona-pero-no-contigua (7 estaciones); 4 SHA-256 añadidos y verificados en `MANIFEST.md`. 79/79 tests en verde (8 geo + 71 regresión). Reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-011 | Segunda verificación independiente de Codex aprobada sobre `f795036`: repro sintética propia a `2223,9 m` del tramo más cercano (sin geometría fabricada), 8 geo + 71 regresión en verde, PostgreSQL `668/484/3/120/0` antes/después, patrones corto base/variante comprobados literalmente, 4 SHA-256 coincidentes, diff limpio e identidad Git correcta. MP-011 pasa a `DONE` | dispatch `ctx_24d7ea61fba0` |
| `2026-11-19` | MP-012 | DEC-015 resuelto y aplicado: `git merge-base --is-ancestor origin/main HEAD` confirmado desde `mp-011-osm-geometry`; worktree `mp-012-movement-engine` abierto sin fusión real. Dispatchado a Codex (ejecutor) con contexto de ADR-0004 (pipeline, cuatro estados), frecuencias reales medidas en MP-003 y el hallazgo de `implausible_speed` de MP-008 para calibración | `docs/TASKS.md`; `docs/STATUS.md` |
| `2026-11-19` | MP-012 | Implementación de Codex lista para revisión: `packages/movement` + ADR-0012; pipeline completo, cuatro estados/fuentes explícitos, flags topológicos y calibración. 90/90 tests en verde. Integración real read-only: 668→668 posiciones, 177 cerca del corredor, máximo salto map-matched 666,4 km/h; volumen final `668/484/3/120/0`. Tarea pasa a `REVIEW` para Claude Code | `packages/movement/`; `docs/adr/0012-movement-package-boundary.md` |
| `2026-11-19` | MP-012 | Revisión independiente de Claude Code: código íntegro leído, 90/90 tests reejecutados subiendo/bajando el contenedor propio, integración real reproducida con resultados idénticos (668→668, 177 cerca del corredor, 666,4 km/h), pipeline verificado matemáticamente (offset bidireccional, límites velocidad/aceleración, fallback recursivo correcto), ausencia del literal `"C5"` confirmada, identidad Git y enlaces ADR-0012/DEC-026 correctos. Evaluada y descartada la escalada a Opus por no ser necesaria. **APROBADA, sin hallazgos.** MP-012 pasa a `DONE` | commit `1edfa14`; este documento |
| `2026-11-19` | MP-013 | API FastAPI real implementada (`apps/api/`): 7 endpoints (`health`/`live/vehicles`(`/{id}`)/`lines`(`/{id}`)/`stations`(`/{id}`)), `history`/`metrics` diferidos explícitamente (DEC-027). Hallazgo real: `route`/`station`/`trip` siguen vacías y `trip_id` sigue `NULL` en PostgreSQL — resolución vía `Topology` en memoria, no `JOIN` SQL. Hallazgos DEC-028 (un corredor basta para ambos sentidos) y DEC-029 (solo 4/24 vehículos del soak son C5, confirma DEC-020 con datos reales). App arrancada con `uvicorn` y probada con `curl` real. 99/99 tests en verde. Tarea pasa a `REVIEW` para OpenAI Codex | `apps/api/`; `apps/api/openapi.json`; DEC-027–030 |
| `2026-11-19` | MP-013 | Primera revisión de Codex: no aprobada — 2 bloqueantes reales reproducidos (`age_s` `null` para vehículos sin ruta resuelta aunque calculable; `service_date` usaba fecha UTC en vez de Europe/Madrid, desplazando el horario cerca de medianoche) + 1 menor (recuento de líneas no-C5 incompleto en DEC-029) | dispatch `ctx_792a5fe349ba` |
| `2026-11-19` | MP-013 | Corregido: `age_s` se calcula siempre desde `observation.reported_at`; `service_date` usa conversión explícita a Europe/Madrid (verificado revirtiendo ambos fixes — los tests nuevos fallan exactamente como describió Codex y pasan con el fix restaurado); DEC-029 corregido con el cruce completo (4 C5, 19 de 9 líneas distintas, 1 sin resolver). 101/101 tests en verde. Reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-013 | Revisión final independiente de Codex aprobada sobre `15170c4`: el único residuo documental ya enumera C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 y el trip de refuerzo sin resolver; diff mínimo y limpio, 11/11 tests API en verde, PostgreSQL `668/484/3/120/0`, identidad Git correcta y sin coautor. **APROBADA, sin hallazgos abiertos.** MP-013 pasa a `DONE` | dispatch `ctx_1235555422b3`; commit `15170c4` |
| `2026-11-19` | MP-014 | Worktree `mp-014-frontend` abierto, ramificado desde `mp-013-fastapi` (MP-013 `DONE`). Dispatchado a Codex (ejecutor) con énfasis explícito en calidad visual real (inspección en navegador, no solo tests), diferenciación clara de los cuatro estados de posición y arquitectura genérica multi-línea (ADR-0011) | `docs/TASKS.md`; `docs/STATUS.md` |
| `2026-11-19` | MP-014 | Implementación de Codex lista para revisión: `LineOut.geometry` aditivo/nullable (DEC-031), `apps/web` React/TypeScript/MapLibre genérico multi-línea, nulls y cobertura ausente explícitos, atribución OSM visible. Regresión Python 102/102; frontend lint/typecheck/3 tests/build en verde. Smoke real con GTFS oficial y poll fresco: 145 vehículos, 31 map-matched y cuatro estados simultáneos (24/2/4/1); runs del smoke retirados y PostgreSQL restaurado a `668/484/3/120/0`. Browser indisponible en la sesión Codex; por instrucción del coordinador, Claude ejecutará el gate visual desktop/estrecho/consola/interacciones antes de aprobar. Tarea pasa a `REVIEW`, no `DONE` | `apps/api/`; `apps/web/`; DEC-031/032; dispatch `ctx_878dc753a9a8` |

## Cómo usar este documento

Al empezar una tarea, comprobar aquí el hito autorizado y en `docs/TASKS.md` que sus dependencias directas están `DONE`. Ningún estado `DONE` se declara sin aprobación del revisor, y ningún test/verificación se reporta sin evidencia ejecutada.
