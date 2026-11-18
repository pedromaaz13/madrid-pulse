# TASKS.md — Backlog Madrid Pulse (MP-001 a MP-015)

Numeración y dependencias conservadas de `docs/research/deep-research-report.md`. Cualquier desviación de la numeración original debe justificarse aquí y registrarse en `docs/DECISIONS.md`.

Leyenda de estado: `TODO` · `IN_PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`.

Cada tarea se trabaja en **un único worktree/rama** (`mp-00X-nombre-corto`), compartido secuencialmente por el ejecutor y el revisor hasta su aprobación — ver el protocolo completo en `AGENTS.md` ("Protocolo de coordinación en Orca" y "Modelo de autonomía por hito") y `CLAUDE.md`. El worktree de una tarea se abre, ramificado desde la rama de su dependencia directa, en cuanto esa dependencia (ver "Grafo de dependencias" más abajo) está `DONE` — **no** es necesario que ya esté fusionada en `main` — y la tarea está dentro del hito autorizado vigente (`docs/STATUS.md`); no se requiere autorización nueva por cada tarea. El propietario decide cuándo fusionar esas ramas a `main` (en lote al cierre del hito u otro momento), sin que eso bloquee el avance. Tareas que no dependen entre sí dentro del mismo hito pueden tener sus worktrees abiertos en paralelo.

---

## MP-001 — Bootstrap documental del repositorio

- **Fase:** F0 — Gobierno y documentación
- **Objetivo:** convertir la investigación en un repositorio profesional: estructura, documentación de arquitectura, backlog y protocolo de agentes, sin código de producto.
- **Prioridad:** P0
- **Depende de:** —
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** raíz del repo, `docs/*`, `AGENTS.md`, `CLAUDE.md`, `.github/*`, estructura de `apps/`, `services/`, `packages/`, `analytics/`, `infra/`, `tests/`.
- **Entradas:** `deep-research-report.md`, `MADRID_PULSE_BRIEF_INICIAL.md`, `README.md` originales.
- **Entregables:** estructura de monorepo; `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`; `docs/PLAN.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/DATA_QUALITY.md`, `docs/DEVELOPMENT.md`; `docs/adr/0001`–`0006`; `docs/legal/DATA_SOURCES.md`, `LICENSE_MATRIX.md`, `ATTRIBUTION.md`; `docs/research/` con los dos documentos originales íntegros + `TRACEABILITY.md`; plantillas `.github/`.
- **Criterios de aceptación:** ver `MADRID_PULSE_BRIEF_INICIAL.md` §7 (enlaces navegables, separación confirmado/propuesto/pendiente, cada tarea con responsable y revisor, `STATUS.md` con checklist y bitácora, `AGENTS.md`/`CLAUDE.md` coherentes, sin servicios cloud configurados, sin producto implementado).
- **Pruebas necesarias:** validación documental (enlaces internos resuelven, tabla de tareas sin huecos de responsable/revisor, ausencia de secretos).
- **Evidencia de verificación:** 4 rondas de revisión cruzada con Codex en este mismo worktree (dispatches `ctx_64731a94e6bc` → `ctx_e72e7a44721a` → `ctx_762cad1ca40c` → `ctx_0ee25a6a5d2c`): 1 bloqueante + 3 menores (ronda 1), 2 bloqueantes + 2 menores (ronda 2), 1 bloqueante + 1 menor (ronda 3), **APROBADO sin hallazgos** (ronda 4). Detalle completo en `docs/STATUS.md` → bitácora.
- **Estado:** `DONE` — **Codex: APROBADO** en revisión cruzada; el propietario autorizó Hito 1 (`MP-002` → `MP-009`) el 2026-11-18. El merge a `main` no es requisito para `DONE` según ADR-0007.

---

## MP-002 — Matriz de fuentes y licencias

- **Fase:** F1 — Factibilidad real de datos
- **Objetivo:** documentar y verificar formalmente las licencias y condiciones de uso de Renfe Data, CRTM, OpenStreetMap y los proyectos de referencia (Via Península, Valfiguer, Niltra/cercanias, xaviour-ai-2026/atlas-ferroviario).
- **Prioridad:** P0
- **Depende de:** MP-001
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `docs/legal/DATA_SOURCES.md`, `docs/legal/LICENSE_MATRIX.md`, `docs/legal/ATTRIBUTION.md`.
- **Entradas:** URLs y licencias preliminares listadas en `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` §2 y en el informe completo.
- **Entregables:** matriz de licencias confirmada (no asumida) con `source_id`, publisher, licencia exacta, texto de atribución y restricciones por fuente.
- **Criterios de aceptación:** cada fuente usada tiene licencia verificada contra su página oficial (no solo citada por la investigación previa); AGPL de Via Península y ODbL de OSM explícitamente resueltos con sus implicaciones documentadas.
- **Pruebas necesarias:** checklist de verificación por fuente (URL accedida, fecha de verificación, captura/registro de la licencia vigente).
- **Evidencia de verificación:** checklist por fuente, URLs oficiales accedidas, fecha/hora UTC, hallazgo y hashes de los ficheros `LICENSE` registrados en `docs/legal/DATA_SOURCES.md`; implicaciones ODbL/AGPL resueltas en `docs/legal/LICENSE_MATRIX.md`; textos de atribución en `docs/legal/ATTRIBUTION.md`. Valfiguer queda documentado con datos/API `CC BY 4.0` y licencia de implementación desconocida (DEC-016). **Auditoría independiente de Claude Code (revisor):** re-verificadas de forma autónoma (no solo leyendo el reporte de Codex) las licencias de Via Península, Niltra/cercanias y atlas-ferroviario vía `gh api` y lectura directa de los ficheros `LICENSE`, y las de Renfe/CRTM vía fetch directo de `data.renfe.com/legal`, la ficha del dataset `ubicacion-vehiculos` y `crtm.es/licencia-de-uso` — todas coinciden con lo documentado. Enlaces y secretos re-validados sin hallazgos. **APROBADO.**
- **Estado:** `DONE` — Codex ejecutó, Claude Code revisó y aprobó el 2026-11-18 sin hallazgos bloqueantes ni menores.

---

## MP-003 — Probe real de feeds C5 (GTFS + GTFS-RT)

- **Fase:** F1 — Factibilidad real de datos
- **Objetivo:** validar empíricamente, mediante peticiones reales, los endpoints `gtfsrt.renfe.com/vehicle_positions.json`, `trip_updates.json`, `alerts.json` y el GTFS estático de Cercanías para la línea C5.
- **Prioridad:** P0
- **Depende de:** MP-002
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `docs/research/MP-003-probe-findings.md` (nuevo), `docs/legal/DATA_SOURCES.md`, `docs/DATA_MODEL.md`, `docs/DECISIONS.md` (DEC-017), `docs/adr/0008-route-identity.md` (nuevo, `Propuesto`); fixtures crudas temporales (no versionadas todavía — ver MP-004).
- **Entradas:** endpoints hipotéticos de `MADRID_PULSE_BRIEF_INICIAL.md` §2.
- **Entregables:** captura controlada de los tres feeds GTFS-RT y del GTFS estático; esquema real de payload documentado (campos observados, no asumidos); frecuencia de actualización medida (no asumida en ~20/30/60 s).
- **Criterios de aceptación:** evidencia reproducible (comandos, timestamps, status HTTP) de que los endpoints responden y cubren trenes de la C5; cualquier discrepancia con lo documentado en la investigación queda registrada en `docs/DECISIONS.md`.
- **Pruebas necesarias:** capturas repetidas en ventanas de tiempo distintas para medir frecuencia real; validación de que `trip_id` del feed en vivo es resoluble contra el GTFS estático.
- **Evidencia de verificación:** `docs/research/MP-003-probe-findings.md` — 3 polls reales de `vehicle_positions.json` espaciados ~20 s (headers/timestamps), 1 poll de `trip_updates.json` (302 entidades) y de `alerts.json` (82 entidades), descarga real del GTFS estático (15,7 MB, `200 OK`) e inspección de `routes.txt`/`trips.txt`/`stops.txt`/`calendar.txt`. `docs/legal/DATA_SOURCES.md` actualizado de `PENDING MP-003` a `VERIFIED` para disponibilidad/esquema. Hallazgo crítico registrado como DEC-017/ADR-0008 (`Propuesto`): "C5" no es único en el feed nacional (existe también en Asturias y Andalucía); `docs/DATA_MODEL.md` corregido en consecuencia.
- **Estado:** `REVIEW` — implementación completada por Claude Code el 2026-11-18; pendiente de auditoría y aprobación de Codex. Pendientes explícitos y no bloqueantes para tareas posteriores: cobertura de `trip_updates` para Madrid en ventana más larga (MP-007/MP-008), descarga real del GTFS CRTM (requería login en el NAP, no probado), validación detallada de `shapes`/`stop_times` de C5 (MP-010), comportamiento en cambio de día de servicio (MP-012).

---

## MP-004 — Fixtures reproducibles

- **Fase:** F2 — Contratos y calidad de datos
- **Objetivo:** congelar fixtures anonimizadas de los payloads reales capturados en MP-003, con hashes y tests de parseo.
- **Prioridad:** P0
- **Depende de:** MP-003
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `tests/fixtures/`.
- **Entradas:** capturas de MP-003.
- **Entregables:** fixtures congeladas (JSON/protobuf decodificado) con hash de verificación; tests de parseo contra esas fixtures.
- **Criterios de aceptación:** fixtures no contienen datos sensibles ni dependen de endpoints en vivo; tests de parseo reproducibles sin red.
- **Pruebas necesarias:** suite de parseo ejecutada en CI local.
- **Evidencia de verificación:** salida de tests y hashes documentados.
- **Estado:** `TODO`

---

## MP-005 — Contrato canónico interno

- **Fase:** F2 — Contratos y calidad de datos
- **Objetivo:** definir el esquema canónico interno (Pydantic/JSON Schema) para vehículo, viaje y salud de feed, desacoplado del formato bruto de Renfe.
- **Prioridad:** P0
- **Depende de:** MP-004
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `packages/contracts/`.
- **Entradas:** fixtures de MP-004, modelo propuesto en `docs/DATA_MODEL.md` y `docs/DATA_CONTRACTS.md`.
- **Entregables:** esquema canónico versionado, con separación explícita `raw` vs `normalized`.
- **Criterios de aceptación:** el esquema resuelve el modelo candidato de `docs/DATA_MODEL.md` sin contradicciones no documentadas; cambios respecto al modelo candidato se registran como ADR.
- **Pruebas necesarias:** tests de validación de esquema contra fixtures reales y sintéticas.
- **Evidencia de verificación:** suite de tests de esquema.
- **Estado:** `TODO`

---

## MP-006 — Esquema PostgreSQL/PostGIS v1

- **Fase:** F3 — Persistencia e ingesta mínima
- **Objetivo:** migraciones iniciales del esquema relacional (entidades, constraints, índices) con rollback probado.
- **Prioridad:** P0
- **Depende de:** MP-005
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `infra/migrations/`.
- **Entradas:** modelo relacional de `docs/DATA_MODEL.md`.
- **Entregables:** migraciones versionadas (up/down), constraints de unicidad e índices (incluyendo `GIST` sobre geometría).
- **Criterios de aceptación:** migraciones aplican y revierten limpiamente sobre PostgreSQL/PostGIS local; constraints reflejan las claves de deduplicación documentadas.
- **Pruebas necesarias:** aplicación y rollback de migraciones en base local, verificación de constraints con datos de prueba.
- **Evidencia de verificación:** log de ejecución de migraciones.
- **Estado:** `TODO`

---

## MP-007 — Collector idempotente

- **Fase:** F3 — Persistencia e ingesta mínima
- **Objetivo:** servicio de polling contra los feeds de Renfe con reintentos, timeout, hashing de payload y deduplicación.
- **Prioridad:** P0
- **Depende de:** MP-005, MP-006
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `services/collector/`.
- **Entradas:** contrato canónico (MP-005), esquema de persistencia (MP-006).
- **Entregables:** colector con polling parametrizable, reintentos con backoff, timeout, hash canónico de payload, deduplicación, métricas de ejecución (`feed_run`).
- **Criterios de aceptación:** ejecución sostenida sin errores críticos durante la ventana de prueba definida en `docs/PLAN.md` (F3); deduplicación verificada con payloads idénticos repetidos.
- **Pruebas necesarias:** test de idempotencia (mismo payload → una sola observación almacenada), test de manejo de fallos de red.
- **Evidencia de verificación:** logs de ejecución y métricas de `feed_run`.
- **Estado:** `TODO`

---

## MP-008 — Quality engine

- **Fase:** F4 — Motor de calidad e histórico
- **Objetivo:** motor de detección de anomalías: datos obsoletos (stale), velocidades implausibles, IDs ausentes, snapshots duplicados, anomalías de reloj (incluido cambio de día).
- **Prioridad:** P0
- **Depende de:** MP-007
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `packages/quality/`.
- **Entradas:** observaciones persistidas por el colector (MP-007); catálogo de problemas empíricos documentado en `docs/DATA_QUALITY.md` (inspirado en los hallazgos públicos de Valfiguer y Niltra/cercanias, reimplementado de forma independiente).
- **Entregables:** reglas de calidad con flags documentados (`quality_flags`), eventos de calidad persistidos (`data_quality_event`).
- **Criterios de aceptación:** cada regla tiene al menos un test con caso real o fixture que la dispara y uno que no la dispara (falso positivo controlado).
- **Pruebas necesarias:** suite de tests de reglas de calidad.
- **Evidencia de verificación:** suite de tests y ejemplos de flags generados.
- **Estado:** `TODO`

---

## MP-009 — Exportador histórico (Parquet particionado)

- **Fase:** F4 — Motor de calidad e histórico
- **Objetivo:** exportación diaria particionada a Parquet con compresión, y test de replay.
- **Prioridad:** P1
- **Depende de:** MP-007, MP-008
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `services/snapshotter/`, `analytics/duckdb/`, `analytics/dbt/` (transformación silver → gold inicial).
- **Entradas:** datos hot de PostgreSQL (MP-006/007) y flags de calidad (MP-008).
- **Entregables:** exportador con particionado `date=YYYY-MM-DD/hour=HH` (raw) y `date=YYYY-MM-DD` (silver/gold), compresión ZSTD.
- **Criterios de aceptación:** un día exportado puede reconstruirse (*replay*) reproduciendo el estado observado sin pérdida de eventos relevantes.
- **Pruebas necesarias:** test de replay de un día completo de fixtures.
- **Evidencia de verificación:** resultado del test de replay.
- **Estado:** `TODO`

---

## MP-010 — Topología GTFS C5

- **Fase:** F5 — Geometría y topología
- **Objetivo:** modelar estaciones, trips y shapes de la C5 a partir del GTFS estático, con validación de recorrido.
- **Prioridad:** P0
- **Depende de:** MP-004
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `packages/gtfs/`.
- **Entradas:** GTFS estático capturado en MP-003/MP-004.
- **Entregables:** parser de topología GTFS para C5, validación de que el recorrido de estaciones coincide con lo esperado (orden, direcciones).
- **Criterios de aceptación:** topología validada contra el GTFS estático real, sin datos inventados.
- **Pruebas necesarias:** tests de parseo de `routes`, `trips`, `stops`, `stop_times`, `shapes` para C5.
- **Evidencia de verificación:** suite de tests de topología.
- **Estado:** `TODO`

---

## MP-011 — Prototipo de geometría ferroviaria sobre OSM

- **Fase:** F5 — Geometría y topología
- **Objetivo:** derivar geometría ferroviaria de la C5 desde OpenStreetMap, con atribución y registro de casos ambiguos.
- **Prioridad:** P1
- **Depende de:** MP-010
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `packages/geo/`.
- **Entradas:** topología GTFS (MP-010), datos OSM.
- **Entregables:** geometría de la C5 entre estaciones consecutivas, atribución ODbL incluida, documentación de ambigüedades (vía doble, cambios de ancho, etc.) sin copiar la implementación de Via Península.
- **Criterios de aceptación:** geometría renderizable y revisable visualmente contra el trazado real; atribución OSM presente.
- **Pruebas necesarias:** test de continuidad geométrica (sin saltos) entre estaciones consecutivas de la C5.
- **Evidencia de verificación:** salida de test de continuidad + capturas de geometría.
- **Estado:** `TODO`

---

## MP-012 — Motor de movimiento v1

- **Fase:** F6 — Motor de movimiento
- **Objetivo:** implementar los estados `OBSERVED / ESTIMATED / STALE / SCHEDULED` con tests deterministas.
- **Prioridad:** P1
- **Depende de:** MP-008, MP-010, MP-011
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Nota de worktree (pendiente de resolver antes de empezar, sugerencia no bloqueante de Codex en la revisión de MP-001):** MP-012 es el primer punto de convergencia de ramas encadenadas — depende de tres tareas que pueden terminar en ramas distintas (MP-008 en la cadena MP-005→009, MP-010 y MP-011 en su propia rama paralela). `AGENTS.md` ("Modelo de autonomía por hito") describe cadenas y bifurcaciones, pero no especifica aún cómo una tarea con varias dependencias elige su rama base e integra las demás (p. ej. ramificar desde MP-011 y hacer `git merge`/rebase de MP-008 sobre ella, o viceversa). Debe decidirse y documentarse en `AGENTS.md` antes de abrir el worktree de MP-012.
- **Archivos/componentes afectados:** `packages/geo/`, `packages/quality/`, lógica de movimiento (ubicación exacta a definir en ADR si no cabe en paquetes existentes).
- **Entradas:** flags de calidad (MP-008), topología (MP-010), geometría (MP-011).
- **Entregables:** motor de movimiento con los cuatro estados, `confidence`, `age_s`, umbrales parametrizados (no fijos) siguiendo `docs/DATA_QUALITY.md`.
- **Criterios de aceptación:** tests deterministas cubren transición entre estados, saltos de estación y velocidades físicamente inverosímiles.
- **Pruebas necesarias:** suite de tests deterministas del motor de movimiento.
- **Evidencia de verificación:** suite de tests.
- **Estado:** `TODO`

---

## MP-013 — FastAPI v1

- **Fase:** F7 — API propia
- **Objetivo:** API propia versionada con OpenAPI, endpoints de vehículos en vivo, salud de feed, líneas y estaciones.
- **Prioridad:** P1
- **Depende de:** MP-005, MP-007, MP-012
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `apps/api/`.
- **Entradas:** contrato canónico (MP-005), datos del colector (MP-007), motor de movimiento (MP-012).
- **Entregables:** API FastAPI conforme a `docs/DATA_CONTRACTS.md`, OpenAPI publicado.
- **Criterios de aceptación:** endpoints responden con los campos de frescura/calidad exigidos; sin inventar datos ausentes como ceros.
- **Pruebas necesarias:** tests de contrato de API (schema de respuesta, casos de borde de frescura).
- **Evidencia de verificación:** suite de tests de contrato + OpenAPI generado.
- **Estado:** `TODO`

---

## MP-014 — Frontend React/MapLibre C5

- **Fase:** F8 — Frontend Live
- **Objetivo:** mapa funcional de la C5 con movimiento y visualización explícita de incertidumbre de posición.
- **Prioridad:** P1
- **Depende de:** MP-013
- **Ejecutor:** OpenAI Codex
- **Revisor:** Claude Code
- **Archivos/componentes afectados:** `apps/web/`.
- **Entradas:** API v1 (MP-013).
- **Entregables:** mapa React/TypeScript/MapLibre consumiendo la API real, con diferenciación visual de los cuatro estados de posición y atribución OSM visible en UI.
- **Criterios de aceptación:** demo funcional contra API real (no mocks), estados de posición distinguibles por el usuario.
- **Pruebas necesarias:** smoke test de carga de mapa y de consumo de API; verificación manual en navegador (no solo tests automatizados).
- **Evidencia de verificación:** capturas/registro de la demo funcional + resultado de smoke tests.
- **Estado:** `TODO`

---

## MP-015 — E2E y readiness MVP

- **Fase:** F9 — Histórico/Explore y endurecimiento
- **Objetivo:** validación end-to-end completa, CI verde, checklist de preparación de MVP y ADRs actualizados a la implementación real.
- **Prioridad:** P1
- **Depende de:** MP-009, MP-012, MP-013, MP-014
- **Ejecutor:** Claude Code
- **Revisor:** OpenAI Codex
- **Archivos/componentes afectados:** `tests/e2e/`, `.github/workflows/` (si se crea en esta tarea), `docs/adr/`, `analytics/dbt/`, `analytics/duckdb/` (ampliación de métricas con cobertura, ver `docs/PLAN.md` F9).
- **Entradas:** todos los componentes de F1 a F8.
- **Entregables:** replay E2E completo, pipeline CI configurado y verde, checklist de MVP documentado, ADRs reconciliados con la implementación final.
- **Criterios de aceptación:** checklist de MVP superado y aceptado por el propietario; ningún ADR describe algo distinto de lo implementado.
- **Pruebas necesarias:** suite E2E completa + CI.
- **Evidencia de verificación:** resultado de CI + checklist firmado.
- **Estado:** `TODO`

---

## Grafo de dependencias

Esta tabla refleja **exactamente** el campo "Depende de" de cada ficha anterior — sin añadir dependencias transitivas redundantes. Para dependencias transitivas (p. ej. qué depende indirectamente de MP-004), recórrase la tabla hacia arriba.

| Tarea | Depende directamente de |
|---|---|
| MP-001 | — |
| MP-002 | MP-001 |
| MP-003 | MP-002 |
| MP-004 | MP-003 |
| MP-005 | MP-004 |
| MP-006 | MP-005 |
| MP-007 | MP-005, MP-006 |
| MP-008 | MP-007 |
| MP-009 | MP-007, MP-008 |
| MP-010 | MP-004 |
| MP-011 | MP-010 |
| MP-012 | MP-008, MP-010, MP-011 |
| MP-013 | MP-005, MP-007, MP-012 |
| MP-014 | MP-013 |
| MP-015 | MP-009, MP-012, MP-013, MP-014 |

Dos ramas pueden avanzar en paralelo en worktrees independientes una vez resuelto su ancestro común: `MP-005` y `MP-010` corren en paralelo tras `MP-004` (no dependen entre sí); `MP-006`/`MP-007` corren en la rama de `MP-005`, mientras `MP-011` corre en la rama de `MP-010`, hasta que ambas convergen en `MP-012`.
