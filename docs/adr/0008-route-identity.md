# ADR-0008: `route_id` completo, no el código de línea, como identificador de ruta

- **Estado:** `Aceptado` — promovido por el propietario en el cierre de Hito 2 (`2026-11-20`), tras la auditoría de integración de Hito 2 (`docs/STATUS.md`), que confirmó contra el código real (`Topology`, `route_groups()`, filtro de núcleo `10`, `UNIQUE(network_id, source_route_id)`) que la identidad adoptada se aplica sin colapsar en ninguna capa implementada.
- **Fecha:** 2026-11-18 (promovido 2026-11-20)
- **Decisores:** Claude Code (ejecutor de MP-003); auditado por Codex en la revisión de MP-003 y en la auditoría de integración de Hito 2; promovido por el propietario (Pedro Matute).

## Contexto

El probe real de MP-003 (`docs/research/MP-003-probe-findings.md`) descubrió, mediante captura directa de `vehicle_positions.json`, `alerts.json` y el GTFS estático descargado, que **el código de línea "C5" no es único en el feed nacional de Renfe**: Madrid, Asturias (Gijón) y Andalucía (Sevilla) tienen cada una una línea llamada literalmente "C5" (`route_short_name = "C5"` en los tres casos), con `route_id` completos distintos (`10T0047C5`, `20T0011C5`, `30T0009C5`).

`docs/DATA_MODEL.md` (escrito en MP-001, antes de esta verificación) modela `route.source_route_id` sin especificar si debe ser el código de línea o el `route_id` completo del proveedor. Dado el hallazgo, dejarlo ambiguo produciría un bug real: cualquier filtro o `JOIN` por `"C5"` mezclaría trenes de tres núcleos distintos.

## Decisión

`route.source_route_id` (y cualquier filtro de ingesta/colector por línea) debe usar el **`route_id` completo** devuelto por Renfe (p. ej. `10T0047C5`), nunca el `route_short_name` (`"C5"`) en solitario. Para la C5 de Madrid existen **cinco** `route_id` distintos (`10T0017C5`, `10T0018C5`, `10T0035C5`, `10T0047C5`, `10T0048C5` — variantes de sentido y de tramo corto/largo). Dado que `UNIQUE(network_id, source_route_id)` exige una fila de `route` por cada `source_route_id`, **cada variante recibe su propia fila `route.id`**; la agrupación como "la misma línea comercial C5" se expresa mediante `short_name = "C5"` compartido entre esas cinco filas (todas con el mismo `network_id` = Madrid) — no mediante una lista de `source_route_id` dentro de una sola fila, que sería incompatible con la restricción `UNIQUE` existente. Cualquier consulta de producto que quiera "todos los trenes de la C5 de Madrid" debe agrupar por `(network_id, short_name)`, no asumir un único `route.id`.

El prefijo de dos cifras del `route_id`/`service_id`/`trip_id` (`10` = Madrid, `20` = Asturias, `30`/`31`/`32` = Andalucía, etc. — tabla completa en los findings de MP-003) identifica el núcleo de Cercanías y debe usarse como filtro de ingesta para limitar el colector (MP-007) a Madrid, en vez de filtrar por texto de línea.

## Alternativas consideradas

- **Filtrar por `route_short_name = "C5"` directamente:** descartada — produce falsos positivos de otros núcleos, confirmado empíricamente.
- **Filtrar solo por `network_id`/`agency_id` del GTFS, ignorando el prefijo numérico:** `agency.txt` tiene una sola fila (Renfe), no distingue núcleos — no es una opción. El prefijo numérico de `route_id`/`trip_id`/`service_id` es, por ahora, el único disambiguador verificado disponible en los datos reales.

## Consecuencias

- `docs/DATA_MODEL.md` debe actualizarse (hecho en esta misma tarea) para explicitar que `route.source_route_id` es el `route_id` completo del proveedor, con una fila por variante y agrupación por `(network_id, short_name)` — no una lista de `source_route_id` en una sola fila.
- `services/collector` (MP-007) debe filtrar por prefijo de núcleo `10`, no por subcadena `"C5"`.
- `packages/contracts` (MP-005) resuelve `trip_id` del feed en vivo contra `trips.txt` por **igualdad literal de cadena** (confirmado 403/403 en MP-003, ver findings §7) — es un `JOIN` directo, no requiere reconstrucción por `(service_id, vehículo, línea)`.
- Pendiente: el propietario revisa y promueve este ADR a `Aceptado` (o lo corrige), conforme a ADR-0007 — en el cierre de Hito 2 (ver corrección en el campo `Estado`).

## Adenda (MP-007, 2026-11-18): formato `SPECIAL_<núcleo>_<resto>` y alcance real implementado

El colector de MP-007 encontró en vivo un `trip_id` de tren de refuerzo (`SPECIAL_10_91567C2`) que no empieza por 2 cifras numéricas — rompe el supuesto de extracción `trip_or_route_id[:2]` de `packages/contracts/nucleo.py`. Corregido con una regex específica para el prefijo `SPECIAL_`; no contradice el disambiguador de 2 cifras para el formato estándar, lo complementa. Detalle completo en `docs/research/MP-003-probe-findings.md` §10.

MP-007 implementa el filtro de ingesta por núcleo que este ADR pide ("Consecuencias" arriba): descarta entidades cuyo `nucleo_prefix` no sea `10` (Madrid) antes de persistir. **Limitación conocida** (ver DEC-020 en `docs/DECISIONS.md`): esto filtra por núcleo (todo Madrid), no todavía por línea C5 específicamente, que es el alcance real exigido por ADR-0001 (`Aceptado`). Acotar a C5 exige resolver `trip_id` → `route_id` contra el GTFS estático, trabajo que ADR-0009 asigna explícitamente a MP-010. El filtro por núcleo es una reducción de alcance real y verificada hacia ese objetivo, no el objetivo completo.
