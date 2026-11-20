# PLAN.md — Roadmap de Madrid Pulse

Fuente: `docs/research/deep-research-report.md` (§ "Repositorio, fases y tareas") y `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` (§5). Este documento traduce esas fases en un roadmap operable. El backlog detallado tarea por tarea vive en `docs/TASKS.md`; el estado vivo en `docs/STATUS.md`.

## Principio rector

El MVP **no empieza por el frontend**. La capa visual solo se construye cuando el colector, los contratos y el replay histórico funcionan de forma demostrable sobre datos reales de la C5. Cada fase tiene una puerta de salida (*exit gate*) verificable; una tarea no empieza sin que sus dependencias directas (`docs/TASKS.md`) estén `DONE`. Esto **no** equivale a esperar siempre a que toda la fase anterior esté completa: el grafo real tiene excepciones (p. ej. F5 depende solo de F2, no de F3/F4 — ver "Dependencias entre fases" más abajo), y son esas excepciones, no una cadena F0→F10 estrictamente lineal, las que determinan cuándo puede empezar cada tarea.

## Fases

### F0 — Gobierno y documentación (MP-001)
**Objetivo:** repositorio estructurado, protocolo de agentes, backlog y decisiones registradas.
**Entregables:** estructura de carpetas, `docs/*`, `AGENTS.md`, `CLAUDE.md`, ADRs iniciales.
**Exit gate:** MP-001 en `REVIEW`, aceptado por Codex y por el propietario. Ningún código de producto.

### F1 — Factibilidad real de datos (MP-002, MP-003)
**Objetivo:** confirmar empíricamente que los feeds de Renfe/CRTM existen, responden, y cubren la C5 con la granularidad asumida.
**Entregables:** matriz de fuentes y licencias; captura controlada de GTFS estático + GTFS-RT (vehicle positions, trip updates, alerts) para C5; esquema real documentado (no asumido).
**Exit gate:** evidencia reproducible de que los endpoints responden, con esquema de payload documentado y licencias confirmadas. Si algún endpoint no es accesible o cambia de contrato, se actualiza `docs/DECISIONS.md` antes de continuar.

### F2 — Contratos y calidad de datos (MP-004, MP-005)
**Objetivo:** fixtures reproducibles congeladas y contrato canónico interno (Pydantic/JSON Schema) para vehículo, viaje y salud de feed.
**Entregables:** fixtures anonimizadas con hashes, tests de parseo, esquema canónico versionado.
**Exit gate:** tests de parseo verdes contra fixtures reales y sintéticas; contrato canónico revisado por el agente contrario.

### F3 — Persistencia e ingesta mínima (MP-006, MP-007)
**Objetivo:** esquema Postgres/PostGIS v1 y colector idempotente.
**Entregables:** migraciones con constraints e índices y rollback probado; colector con polling, reintentos, timeout, hashing y deduplicación.
**Exit gate:** 24 h de ingesta sin errores críticos (ver F3 en el brief); dedupe verificado contra payloads idénticos.

### F4 — Motor de calidad e histórico (MP-008, MP-009)
**Objetivo:** detección de anomalías (velocidad implausible, IDs ausentes, snapshots duplicados, saltos de reloj) y exportación histórica particionada.
**Entregables:** quality engine con flags documentados; exportador Parquet diario particionado con compresión y test de replay.
**Exit gate:** replay de un día completo reconstruye el estado observado sin pérdida de eventos relevantes; anomalías conocidas (del artículo de Valfiguer) cubiertas por test.

### F5 — Geometría y topología (MP-010, MP-011)
**Objetivo:** topología GTFS de la C5 (estaciones, trips, shapes) y prototipo de geometría ferroviaria sobre OSM.
**Entregables:** validación de recorrido C5; geometría con atribución OSM y registro de casos ambiguos.
**Exit gate:** geometría de la C5 renderizable y validada contra el recorrido real documentado en GTFS estático.

### F6 — Motor de movimiento (MP-012)
**Objetivo:** estados `observed / estimated / stale / scheduled` con tests deterministas.
**Entregables:** motor de movimiento parametrizado (umbrales calibrables, no fijos), tests de interpolación y casos límite (saltos de estación, velocidades imposibles).
**Exit gate:** tests deterministas verdes; umbrales documentados como calibrables y pendientes de ajuste con datos reales (no verdad de diseño).

### F7 — API propia (MP-013)
**Objetivo:** FastAPI v1 con OpenAPI, vehículos en vivo, salud de feed, endpoints de línea/estación.
**Entregables:** API versionada (`/api/v1`), contratos conformes a `docs/DATA_CONTRACTS.md`.
**Exit gate:** OpenAPI publicado, tests de contrato verdes, indicadores de frescura/calidad presentes en cada respuesta relevante.

### F8 — Frontend Live (MP-014)
**Objetivo:** mapa React/MapLibre funcional sobre la C5, con visualización explícita de incertidumbre de posición.
**Entregables:** mapa con estaciones, trenes observados/estimados diferenciados visualmente, controles de fuente.
**Exit gate:** demo funcional contra la API real (no mocks), con los cuatro estados de posición visibles.

### F9 — Histórico / Explore y endurecimiento (MP-015)
**Objetivo:** E2E completo, CI verde, checklist de preparación de MVP.
**Entregables:** replay end-to-end, pipeline DuckDB para métricas con cobertura (disciplina dbt sin el motor literal — ver [ADR-0013](adr/0013-no-literal-dbt-engine.md) y DEC-034), CI configurado, ADRs actualizados a la realidad implementada.
**Exit gate:** checklist de MVP superado y aceptado por el propietario; sin deuda de documentación pendiente.

### F10 — Expansión (fuera de alcance de MP-001 a MP-015)
**Objetivo:** extender de C5 a toda Cercanías Madrid, y después al resto de España; explorar colaborativo/ocupación solo con diseño de privacidad explícito (actualmente **NO-GO**, ver `docs/DECISIONS.md`).

## Dependencias entre fases

```text
F0 → F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F10
                 (F5 depende de F2, no de F3/F4 directamente — ver TASKS.md)
```

El grafo de dependencia real, tarea por tarea, es el de `docs/TASKS.md` (no todas las fases son estrictamente secuenciales: MP-010 depende de MP-004, no de MP-006/007/008).

## Prioridades

- **P0** — bloqueante para cualquier avance posterior: MP-001 a MP-008, MP-010.
- **P1** — necesario para MVP demostrable pero no bloqueante entre sí: MP-009, MP-011 a MP-015.

## Mecánica de ejecución por tarea

Cada tarea del backlog se ejecuta en **un único worktree/rama propio**, compartido secuencialmente por el agente ejecutor y el agente revisor (implementar → revisar → corregir → re-verificar, en el mismo worktree). Una tarea queda `DONE` cuando el revisor aprueba — eso ya es suficiente para que cualquier tarea dependiente ramifique su propio worktree desde ahí; **no** hace falta esperar a que el propietario fusione esa rama a `main` (si lo exigiera, el propietario tendría que fusionar en tiempo real tras cada tarea, y el modelo de autonomía por hito no eliminaría la supervisión constante que busca evitar). El propietario decide cuándo fusionar a `main` — en lote al cierre del hito, o antes. El protocolo completo está en `AGENTS.md` ("Protocolo de coordinación en Orca" y "Modelo de autonomía por hito") y `CLAUDE.md`. Dos o más tareas del mismo hito que no dependan entre sí (`docs/TASKS.md` → "Grafo de dependencias") pueden tener su worktree abierto simultáneamente — eso es el comportamiento normal, no una excepción; lo que no varía es que cada tarea individual vive en un único worktree propio.

## Gates de calidad transversales (todas las fases)

- Ningún test se declara superado sin ejecución real.
- Ninguna tarea se marca `DONE` sin revisión cruzada completada (`AGENTS.md`).
- Ninguna decisión arquitectónica cambia sin ADR.
- Ninguna métrica de puntualidad se publica sin su cobertura asociada.
- Ninguna posición estimada se presenta como observada.
- Ninguna tarea se trabaja en más de un worktree a la vez; los agentes pueden commitear de forma iterativa dentro de ese worktree, pero ningún agente hace `push`, abre/fusiona PR o fusiona a `main` por su cuenta (`AGENTS.md`).

## Servicios a activar por fase

Ver `docs/DEVELOPMENT.md` para el detalle de qué se ejecuta en local y qué requiere una cuenta/servicio cloud, y en qué fase se activa cada uno.
