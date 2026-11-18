# ADR-0009: Campos del modelo candidato no observados en el feed real de Renfe

- **Estado:** `Propuesto` — aplicado provisionalmente en MP-005 bajo el régimen de autonomía de ADR-0007; pendiente de revisión y promoción a `Aceptado` por el propietario (o por Codex como revisor de MP-005) en el cierre de Hito 1.
- **Fecha:** 2026-11-18
- **Decisores (propuesta):** Claude Code (ejecutor de MP-005); pendiente de revisión de Codex en esta misma tarea.

## Contexto

Al construir el contrato canónico interno (`packages/contracts/`) contra las fixtures reales congeladas en MP-004 (a su vez capturadas en vivo en MP-003), se encontraron tres campos que `docs/DATA_MODEL.md` (escrito en MP-001, antes de cualquier verificación empírica) asumía disponibles y que **no aparecen en ningún payload real observado**:

1. `vehicle_position_observation.speed_kmh` y `.bearing` — GTFS-RT estándar los define como opcionales en `VehiclePosition`, pero Renfe no los emite en ninguna de las capturas de MP-003/MP-004 (3 polls de `vehicle_positions.json` en MP-003, más la fixture fresca de MP-004 — ~800 entidades combinadas, cero con estos campos).
2. `vehicle_position_observation.current_stop_sequence` — el feed real da `stopId` (identificador de parada), no una posición de secuencia dentro del viaje. Resolver a `stop_sequence` exige un `JOIN` contra `stop_times.txt` del GTFS estático, que no es responsabilidad de la ingesta (MP-007) sino de una capa posterior (MP-010/MP-012).
3. `service_alert.effect`, `.cause`, `.header_text` — GTFS-RT estándar los define para `Alert`, pero ninguna de las 82+76+3 alertas observadas en MP-003/MP-004 los incluye; solo aparecen `activePeriod`, `informedEntity` (con `routeId`) y `descriptionText`.

Mantener estos campos en el modelo candidato como si estuvieran garantizados habría violado el principio de `AGENTS.md`: "No se inventan campos ni comportamientos de la API de Renfe: todo contrato con fuentes externas se valida empíricamente... antes de documentarse como hecho."

## Decisión

1. `speed_kmh` y `bearing` se mantienen en el esquema (porque el estándar GTFS-RT los contempla y Renfe podría empezar a emitirlos), pero explícitamente `nullable`/`Optional`, documentados como "no observados hasta ahora" tanto en `docs/DATA_MODEL.md` como en `packages/contracts/canonical.py`. Ningún código debe asumir que están poblados.
2. `current_stop_sequence` se renombra a `current_stop_id` en el modelo de ingesta (lo que realmente llega del feed). La resolución a `stop_sequence` mediante el GTFS estático queda explícitamente diferida a MP-010/MP-012, no a MP-005/MP-007.
3. `effect`, `cause` y `header_text` se **eliminan** de `service_alert` en el modelo candidato. Se añade `description_language` (sí observado: cada traducción trae su código de idioma).

## Alternativas consideradas

- **Mantener los campos como estaban, asumiendo que aparecerán más adelante:** descartada — contradice el principio de no inventar comportamiento de fuentes externas; además, un esquema que declara campos obligatorios inexistentes en la realidad rompería la ingesta real en MP-007 o forzaría a rellenarlos con valores inventados (violando también "un dato ausente nunca se representa como cero").
- **Eliminar `speed_kmh`/`bearing` por completo en vez de dejarlos `nullable`:** no se adoptó — son parte del estándar GTFS-RT y Renfe podría empezar a emitirlos sin aviso; es más seguro declararlos opcionales desde ahora que tener que añadir una migración reactiva.

## Consecuencias

- `docs/DATA_MODEL.md` actualizado (hecho en esta misma tarea) en las entidades `vehicle_position_observation`, `trip_update_observation` y `service_alert`.
- `packages/contracts/raw.py` y `canonical.py` reflejan exactamente estos hallazgos, con comentarios explicando por qué cada campo ausente no se modela o se modela como opcional.
- MP-006 (esquema PostgreSQL) debe definir `speed_kmh`/`bearing`/`geom` como columnas `NULL`-ables, y `current_stop_id` (no `current_stop_sequence`) como la columna de ingesta cruda.
- MP-010 es responsable de la resolución `stop_id` → `stop_sequence` vía el GTFS estático, no MP-007.
- Pendiente: Codex (revisor de MP-005) y, en el cierre del hito, el propietario, revisan y promueven este ADR a `Aceptado`.
