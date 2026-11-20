# ADR-0010: Estrategia de deduplicación del colector

- **Estado:** `Aceptado` — promovido por el propietario en el cierre de Hito 2 (`2026-11-20`), tras la auditoría de integración de Hito 2 (ver `docs/STATUS.md`) que encontró y corrigió una omisión real en la "Decisión": faltaba el desempate `id DESC` que el código real sí implementa desde MP-007.
- **Fecha:** 2026-11-19 (promovido 2026-11-20)
- **Decisores:** Claude Code (ejecutor de MP-007); auditado por Codex como revisor de MP-007 y de la auditoría de integración de Hito 2; promovido por el propietario (Pedro Matute).

## Contexto

`docs/DATA_MODEL.md` (sección "Deduplicación") deja explícitamente abierta esta decisión: "Si Renfe repite exactamente el mismo payload en polls consecutivos, se almacena una sola fila (o se incrementa un contador `seen_count` si se decide conservarlo — pendiente de ADR en MP-007)." DEC-013 (`docs/DECISIONS.md`) exige además validar que el hash canónico no descarte cambios relevantes de campos no incluidos en el hash.

`packages/contracts/normalize.py` calcula `payload_hash` sobre el **volcado completo de la entidad bruta** (`entity.model_dump(mode="json", by_alias=True)`), no sobre un subconjunto de campos elegido a mano. Esto incluye el `timestamp` propio de cada entidad (el reportado por el tren/el feed, no el instante de nuestro poll): si el vehículo no ha enviado una actualización nueva, Renfe repite el mismo `timestamp` además de la misma posición, por lo que el hash es idéntico; si cualquier campo observado cambia (incluido el propio `timestamp`), el hash cambia. Esto resuelve la validación pedida por DEC-013 sin trabajo adicional: el hash no puede "esconder" un cambio relevante porque no excluye ningún campo observado.

## Decisión

1. La clave de deduplicación es `(clave_de_entidad_de_origen, payload_hash)`, donde la clave de entidad es `source_vehicle_id` (posiciones), `source_trip_id` (actualizaciones de viaje) o `source_alert_id` (alertas) — no `ingestion_run_id`. El colector compara el `payload_hash` de la entidad recién parseada contra el de la **última fila almacenada** para esa misma clave (`ORDER BY observed_at DESC, id DESC LIMIT 1` para posiciones/viajes; `ORDER BY active_period_start DESC, id DESC LIMIT 1` para alertas); si coincide, no inserta una fila nueva. **El desempate `id DESC` es necesario, no cosmético:** si dos filas comparten exactamente el mismo `observed_at`/`active_period_start` (Renfe puede repetir el timestamp reportado en polls consecutivos sin que cambie), `ORDER BY observed_at DESC` por sí solo no garantiza determinismo sobre cuál es "la última" — el motor puede devolver cualquiera de las filas empatadas, arriesgando comparar contra la fila equivocada e insertar un duplicado en vez de deduplicar. `id DESC` como desempate secundario corrige esto de forma determinista (bloqueante real encontrado y corregido en MP-007; ver `services/collector/db.py` y `packages/quality/db.py`).
2. **No se implementa `seen_count`.** Cuando una entidad se deduplica, no se incrementa ningún contador ni se actualiza la fila existente. Se puede derivar una cadencia de observación equivalente más adelante a partir de `source_ingestion_run` (que registra todos los ciclos, con o sin inserciones) sin necesitar un contador por fila.
3. El `UNIQUE(ingestion_run_id, payload_hash)` de MP-006 queda como salvaguarda defensiva contra un bug que insertara la misma entidad dos veces dentro del mismo ciclo de ingesta — no es el mecanismo de deduplicación entre ciclos, que ocurre en la capa de aplicación (este colector) antes del `INSERT`.

## Alternativas consideradas

- **`seen_count` incremental en la fila existente:** descartada por ahora — añade una operación de `UPDATE` extra por cada poll sin cambios (que, en régimen estacionario, es la mayoría de los polls) y no hay un consumidor definido de esa métrica todavía (MP-008/MP-009 pueden derivarla de `source_ingestion_run` si resulta necesaria). Revisar si una fase posterior la requiere explícitamente.
- **Deduplicar a nivel de feed completo** (comparar el hash de toda la respuesta HTTP y descartar el ciclo entero si no cambió): descartada — un solo vehículo puede actualizarse mientras el resto del feed permanece igual; deduplicar por feed completo perdería esa actualización parcial.
- **Excluir el `timestamp` del hash para detectar solo cambios "sustantivos" (posición/estado):** descartada — el `timestamp` es en sí mismo una señal real (confirma que el tren sigue reportando), y excluirlo sin una razón empírica habría sido una decisión de diseño no validada contra DEC-013.

## Consecuencias

- `services/collector/db.py` expone `latest_payload_hash(conn, tabla, clave)` como única consulta de lectura antes de cada posible inserción.
- El test de idempotencia de MP-007 (`services/collector/tests/`) verifica contra la base real que un mismo payload repetido produce una sola fila almacenada, no dos.
- Si una fase posterior necesita `seen_count` o una métrica de "última vez vista sin cambios", requerirá una migración adicional y una revisión de este ADR — no se improvisa sin verificar antes.
- Codex (revisor de MP-007) auditó el contenido técnico de este ADR; el propietario lo promovió a `Aceptado` en el cierre de Hito 2, tras corregir la omisión de `id DESC` en la "Decisión" (hallazgo real de la auditoría de integración de Hito 2, no cosmético: ver Parte 2 de la auditoría en `docs/STATUS.md`).
