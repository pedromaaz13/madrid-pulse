# ADR-0002: Fuentes de datos primarias

- **Estado:** Aceptado (fuentes), con verificación formal **pendiente** en MP-002/MP-003
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md` y `docs/research/MADRID_PULSE_BRIEF_INICIAL.md`

## Contexto

Existen al menos tres formas de obtener datos de Cercanías Madrid: (1) directamente de Renfe (GTFS estático + GTFS-RT), (2) vía CRTM (GTFS estático de Comunidad de Madrid), (3) vía la API pública de Valfiguer, que ya normaliza y expone estos mismos datos con metadatos de calidad.

## Decisión

Las fuentes primarias de Madrid Pulse son **Renfe** (GTFS estático + GTFS-RT: `vehicle_positions.json`, `trip_updates.json`, `alerts.json`) y **CRTM** (GTFS estático), consultadas directamente. **No se usa la API de Valfiguer como dependencia de producción** — se usa únicamente como benchmark de producto/funcionalidad.

La geometría ferroviaria usa **OpenStreetMap**.

## Alternativas consideradas

- **Consumir la API de Valfiguer directamente:** descartada como dependencia de producción porque (a) introduce una dependencia no garantizada de un tercero sin SLA, (b) no está claro si su implementación es pública/licenciada para ese uso, (c) reduce el control sobre el contrato de datos propio. Se mantiene como fuente de benchmark/validación de hipótesis, no como fuente de datos.
- **Scraping de `tiempo-real.renfe.com`:** no evaluado como fuente primaria; los endpoints GTFS-RT son la vía oficial soportada.

## Consecuencias

- MP-002 debe verificar formalmente licencia y accesibilidad real de Renfe/CRTM antes de que MP-003 dependa de ellos como hecho confirmado.
- Cualquier cambio de contrato en los endpoints de Renfe (estructura, autenticación, disponibilidad) requiere actualizar este ADR y `docs/legal/DATA_SOURCES.md`, no solo el código del colector.
- Los endpoints y frecuencias documentados en la investigación (`~20s` posiciones, `~30s` trip updates, `~60s` alerts) son **hipótesis de Valfiguer sobre el comportamiento observado**, no un contrato garantizado por Renfe — deben medirse directamente en MP-003.
