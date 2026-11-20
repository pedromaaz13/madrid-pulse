# ADR-0012: Paquete independiente para el motor de movimiento

- **Estado:** `Aceptado` — promovido por el propietario en el cierre de Hito 2 (`2026-11-20`), tras la auditoría de integración de Hito 2 (`docs/STATUS.md`), que confirmó que `packages/movement` sigue siendo puro y sin persistencia en producción, consumido por FastAPI sin incorporar el algoritmo a la capa HTTP.
- **Fecha:** 2026-11-19 (promovido 2026-11-20)
- **Decisores:** OpenAI Codex como ejecutor de MP-012; revisado por Claude Code en MP-012 y en la auditoría de integración de Hito 2; promovido por el propietario (Pedro Matute).

## Contexto

MP-012 combina tres responsabilidades existentes sin pertenecer por completo a
ninguna: geometría/map-matching (`packages/geo`), topología y horario
(`packages/gtfs`) y señales de calidad (`packages/quality`). Además produce un
estado derivado orientado a consumo por la API (`observed / estimated / stale /
scheduled`), no una observación cruda ni una regla aislada de calidad.

Colocarlo en `geo` obligaría a esa capa matemática a depender de GTFS y de los
contratos canónicos. Colocarlo en `quality` mezclaría detección de anomalías
sobre datos de fuente con generación explícita de coordenadas estimadas.

## Decisión

Crear `packages/movement` como capa de orquestación pura y sin persistencia:

- depende de las APIs públicas de `packages/geo`, `packages/gtfs` y
  `packages/contracts`;
- no reimplementa proyección geométrica ni resolución de IDs/stop sequences;
- expone un contrato tipado (`MovementPosition`) consumible directamente por
  MP-013, con modo, confianza, edad, fuente y anomalías;
- recibe `Topology`, `Corridor`, `trip_id`, `service_date` y umbrales como datos
  o configuración; no contiene literales de la línea piloto;
- mantiene `packages/geo` como capa inferior añadiendo solo la primitiva
  geométrica genérica inversa `point_at_arc_length`.

## Alternativas consideradas

- **Integrarlo en `packages/geo`:** descartado porque horario, estados de
  frescura, confianza y semántica de fuente no son responsabilidades
  geométricas.
- **Integrarlo en `packages/quality`:** descartado porque ese paquete evalúa y
  persiste flags de observaciones crudas; el motor genera posiciones derivadas
  y debe conservar una frontera explícita entre observado y estimado.
- **Implementarlo directamente en MP-013:** descartado porque acoplaría el
  algoritmo a HTTP/FastAPI y dificultaría las pruebas deterministas y el replay
  sin servidor.

## Consecuencias

- MP-013 puede serializar `MovementPosition` sin reconstruir semántica de
  calidad o inferir fuentes.
- La selección de topología/corredor queda fuera del motor y sigue siendo
  genérica para futuras líneas, conforme a ADR-0011.
- Los flags topológicos se calculan y exponen, pero su persistencia se difiere
  hasta que exista un modelo persistente para posiciones derivadas; no se
  amplía silenciosamente el significado de `data_quality_event` v1.
- Este ADR se aplica provisionalmente bajo ADR-0007 y permanece `Propuesto`
  hasta revisión del propietario.
