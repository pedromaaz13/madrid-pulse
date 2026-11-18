# ADR-0008: `route_id` completo, no el código de línea, como identificador de ruta

- **Estado:** `Propuesto` — aplicado provisionalmente en MP-003 bajo el régimen de autonomía de ADR-0007; pendiente de revisión y promoción a `Aceptado` por el propietario en el cierre de Hito 1.
- **Fecha:** 2026-11-18
- **Decisores (propuesta):** Claude Code (ejecutor de MP-003); pendiente de aprobación del propietario.

## Contexto

El probe real de MP-003 (`docs/research/MP-003-probe-findings.md`) descubrió, mediante captura directa de `vehicle_positions.json`, `alerts.json` y el GTFS estático descargado, que **el código de línea "C5" no es único en el feed nacional de Renfe**: Madrid, Asturias (Gijón) y Andalucía (Sevilla) tienen cada una una línea llamada literalmente "C5" (`route_short_name = "C5"` en los tres casos), con `route_id` completos distintos (`10T0047C5`, `20T0011C5`, `30T0009C5`).

`docs/DATA_MODEL.md` (escrito en MP-001, antes de esta verificación) modela `route.source_route_id` sin especificar si debe ser el código de línea o el `route_id` completo del proveedor. Dado el hallazgo, dejarlo ambiguo produciría un bug real: cualquier filtro o `JOIN` por `"C5"` mezclaría trenes de tres núcleos distintos.

## Decisión

`route.source_route_id` (y cualquier filtro de ingesta/colector por línea) debe usar el **`route_id` completo** devuelto por Renfe (p. ej. `10T0047C5`), nunca el `route_short_name` (`"C5"`) en solitario. Para la C5 de Madrid existen **cinco** `route_id` distintos que deben tratarse como la misma línea comercial a efectos de producto (`10T0017C5`, `10T0018C5`, `10T0035C5`, `10T0047C5`, `10T0048C5` — variantes de sentido y de tramo corto/largo), agrupados bajo un único `route.id` interno con `short_name = "C5"` y una lista de `source_route_id` asociados, o bien un campo adicional `route_variant`.

El prefijo de dos cifras del `route_id`/`service_id`/`trip_id` (`10` = Madrid, `20` = Asturias, `30`/`31`/`32` = Andalucía, etc. — tabla completa en los findings de MP-003) identifica el núcleo de Cercanías y debe usarse como filtro de ingesta para limitar el colector (MP-007) a Madrid, en vez de filtrar por texto de línea.

## Alternativas consideradas

- **Filtrar por `route_short_name = "C5"` directamente:** descartada — produce falsos positivos de otros núcleos, confirmado empíricamente.
- **Filtrar solo por `network_id`/`agency_id` del GTFS, ignorando el prefijo numérico:** `agency.txt` tiene una sola fila (Renfe), no distingue núcleos — no es una opción. El prefijo numérico de `route_id`/`trip_id`/`service_id` es, por ahora, el único disambiguador verificado disponible en los datos reales.

## Consecuencias

- `docs/DATA_MODEL.md` debe actualizarse (hecho en esta misma tarea) para explicitar que `route.source_route_id` es el `route_id` completo del proveedor, con una nota sobre las 5 variantes de C5 Madrid.
- `services/collector` (MP-007) debe filtrar por prefijo de núcleo `10`, no por subcadena `"C5"`.
- `packages/contracts` (MP-005) debe resolver `trip_id` del feed en vivo contra `trips.txt` por `(service_id activo, número de vehículo, línea)`, no por igualdad literal de `trip_id` — ver findings §7.
- Pendiente: el propietario revisa y promueve este ADR a `Aceptado` (o lo corrige) en el cierre de Hito 1, conforme a ADR-0007.
