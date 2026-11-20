# ADR-0011: Piloto técnico C5 (Hito 2) frente a objetivo de primera versión pública (toda Cercanías Madrid)

- **Estado:** `Aceptado` — promovido por el propietario en el cierre de Hito 2 (`2026-11-20`), tras la auditoría de integración de Hito 2 (`docs/STATUS.md`), que confirmó que la lógica de GTFS/geo/movimiento no fija la línea piloto como literal y que los defaults `C5` de `ApiConfig`/`SnapshotterConfig` son configuración sustituible, no un filtro codificado.
- **Fecha:** 2026-11-19 (promovido 2026-11-20)
- **Decisores:** Claude Code, por instrucción explícita del propietario al autorizar Hito 2; promovido por el propietario (Pedro Matute) en el cierre de Hito 2.

## Contexto

[ADR-0001](0001-project-scope-c5.md) (`Aceptado`, 2026-11-18) limita el backlog `MP-001` a `MP-015` a la línea C5 de Cercanías Madrid, como superficie manejable para validar identificación de trenes, geometría y calidad de datos antes de escalar. Esa decisión sigue vigente y este ADR no la reescribe ni la contradice: ADR-0001 acota un **backlog de implementación** (MP-001→MP-015), no el **objetivo de producto** a largo plazo de Madrid Pulse.

Al autorizar Hito 2 (`MP-010`→`MP-015`), el propietario señaló un riesgo concreto: que las decisiones de arquitectura tomadas durante el piloto C5 (topología GTFS, geometría OSM, motor de movimiento, API, frontend) queden implícitamente diseñadas como si C5 fuera el alcance final del producto, obligando a un rediseño cuando se añadan más líneas. El propietario fue explícito: **la primera versión pública de Madrid Pulse debe cubrir toda la red de Cercanías Madrid, no solo C5** — C5 es únicamente el piloto técnico de Hito 2, elegido por las mismas razones que ya documentaba ADR-0001 (superficie manejable para validar lo fundamental).

Esta distinción ya estaba parcialmente anticipada en las consecuencias de ADR-0001 ("los contratos de datos y el modelo deben ser extensibles a más líneas sin rediseño... aunque solo se pueble con C5") y en `docs/PLAN.md` (Fase F10, "extender de C5 a toda Cercanías Madrid"). Lo que faltaba era hacer la distinción pilot-vs-producto explícita como regla de diseño vinculante para MP-010 a MP-015, no solo como nota de alcance futuro.

## Decisión

1. **ADR-0001 permanece `Aceptado` sin modificación de su texto.** El backlog `MP-001`→`MP-015` sigue implementando y validando únicamente C5; ninguna tarea de Hito 2 implementa otra línea de Cercanías.
2. **C5 es el piloto técnico de Hito 2, no el alcance final del producto.** El objetivo de la primera versión pública de Madrid Pulse (fuera del rango MP-001→MP-015, planificado como Hito 3 — ver `docs/PLAN.md` F10) es cubrir **toda la red de Cercanías Madrid** (los distintos núcleos/líneas que comparten el núcleo "10" de Madrid: C1, C2, C3, C4, C5, C7, C8, C9, C10, según confirme el GTFS estático), no permanecer limitada a C5 de forma indefinida.
3. **Regla de diseño vinculante para MP-010 a MP-015:** ningún motor, API o componente de frontend compartido hardcodea un identificador de línea (p. ej. `"C5"` literal en lógica de negocio, filtros de consulta o nombres de función/endpoint). En su lugar:
   - `network_id`, `route_id` (completo, nunca el código corto — ver ADR-0008/DEC-017), `trip_id`, `stop_id` y el prefijo de núcleo se resuelven siempre de forma genérica, igual que si el sistema sirviera varias líneas.
   - La configuración/geometría específica de C5 (qué estaciones, qué `route_id`, qué shapes) vive en datos o configuración cargable, no en lógica de código condicionada por el literal `"C5"`.
   - Estaciones, variantes de sentido/tramo y direcciones se modelan de forma que una estación compartida entre dos líneas (p. ej. un intercambiador) no exige una estructura distinta cuando se añada una segunda línea.
   - La API (MP-013) y el frontend (MP-014) se preparan para aceptar un filtro por línea/`route_id` aunque en Hito 2 solo exista una línea con datos poblados — el contrato no asume "una sola línea para siempre".
4. **No se implementa la red completa en Hito 2.** Esto es deliberadamente Hito 3 (ver Sección 7 del encargo de autorización del propietario, `2026-11-19`): Hito 2 entrega la arquitectura extensible y el piloto C5 poblado; Hito 3 planifica (no implementa) la cobertura de toda la red, estaciones de intercambio, filtros por línea en UI, escalabilidad con muchos trenes simultáneos y métricas de puntualidad fiables por línea.

## Alternativas consideradas

- **Dejar ADR-0001 como única fuente de verdad de alcance, sin aclaración adicional:** descartada — ADR-0001 solo habla del backlog de implementación; sin esta aclaración explícita, un ejecutor de MP-010/MP-013/MP-014 podría razonablemente diseñar asumiendo C5 como alcance final (p. ej. hardcodeando `"C5"` en un endpoint), que es exactamente el riesgo que el propietario señaló.
- **Reescribir ADR-0001 directamente para mencionar "toda la red" como alcance del MVP:** descartada — ADR-0001 ya está `Aceptado` y su decisión (backlog MP-001→MP-015 limitado a C5) sigue siendo correcta y vigente; reescribirlo en caliente violaría el procedimiento de ADRs (`docs/adr/README.md`: ningún ADR se modifica sin pasar por el proceso de revisión) y confundiría "qué implementa el backlog actual" con "cuál es el objetivo de producto a largo plazo", que son preguntas distintas.
- **Implementar toda la red Cercanías Madrid ya en Hito 2:** descartada explícitamente por el propietario — mayor superficie de validación sin beneficio adicional para probar la arquitectura en este hito; queda como Hito 3.

## Consecuencias

- MP-010 (topología GTFS) y MP-011 (geometría OSM) deben resolver `route_id`/`trip_id`/`stop_id` de forma genérica aunque solo carguen datos de C5 — no pueden asumir "una línea" como invariante de diseño.
- MP-012 (motor de movimiento) debe operar sobre la topología/geometría resuelta de forma genérica, no sobre una estructura especializada para C5.
- MP-013 (API) debe dejar espacio en el contrato (`docs/DATA_CONTRACTS.md`) para filtros por línea/`route_id`, aunque Hito 2 solo los ejercite contra C5.
- MP-014 (frontend) debe estructurar sus componentes de mapa/lista de forma que añadir una segunda línea no requiera reescribir la capa de presentación, aunque la UI de Hito 2 solo muestre C5.
- El backlog de Hito 3 (planificación, no implementación) debe referenciar este ADR al describir la expansión a toda la red.
- Este ADR puede revisarse si la experiencia de Hito 2 revela que alguna de estas reglas de diseño es inviable o insuficiente; cualquier cambio sigue requiriendo el procedimiento de ADR y, para marcarse `Aceptado`, autorización del propietario.
