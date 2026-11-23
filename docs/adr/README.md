# Architecture Decision Records

| ADR | Título | Estado |
|---|---|---|
| [0001](0001-project-scope-c5.md) | Alcance del MVP limitado a la línea C5 | Aceptado |
| [0002](0002-data-sources.md) | Fuentes de datos primarias | Aceptado (fuentes): Renfe verificada e integrada; CRTM con licencia verificada, disponibilidad técnica e integración pendientes — resuelto en cierre de Hito 2 |
| [0003](0003-storage-strategy.md) | Estrategia de almacenamiento híbrido | Aceptado (principio); parámetros pendientes |
| [0004](0004-position-model.md) | Modelo de posición en cuatro estados | Aceptado (principio); umbrales pendientes de calibración |
| [0005](0005-api-contract.md) | Contrato de API propio versionado | Aceptado — confirmado en MP-013, promovido en cierre de Hito 2 |
| [0006](0006-licensing-policy.md) | Política de licenciamiento frente a proyectos de referencia | Aceptado |
| [0007](0007-autonomy-model.md) | Modelo de autonomía acotada para la ejecución del backlog (autorización por hito, commits en worktree, gates limitados a licencia/coste) | Aceptado |
| [0008](0008-route-identity.md) | `route_id` completo (no el código de línea) como identificador de ruta, tras descubrir en MP-003 que "C5" existe también en Asturias y Andalucía | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`) |
| [0009](0009-unobserved-raw-fields.md) | Campos del modelo candidato no observados en el feed real (`speed_kmh`/`bearing` nullable, `current_stop_id` en vez de `current_stop_sequence`, se elimina `effect`/`cause`/`header_text` de alertas) | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`) |
| [0010](0010-dedup-strategy.md) | Deduplicación por hash canónico de payload completo comparado contra la última fila almacenada por clave de entidad de origen, con desempate `id DESC`; sin `seen_count` | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`), tras corregir la omisión del desempate `id DESC` encontrada en la auditoría de integración |
| [0011](0011-public-scope-vs-technical-pilot.md) | C5 es el piloto técnico de Hito 2; el objetivo de primera versión pública es toda la red de Cercanías Madrid — complementa ADR-0001 sin reescribirlo | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`) |
| [0012](0012-movement-package-boundary.md) | Motor de movimiento como capa independiente entre geometría, topología, calidad y API | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`) |
| [0013](0013-no-literal-dbt-engine.md) | No se introduce dbt-core/dbt-duckdb como motor literal para la capa gold; la disciplina dbt se aplica directamente en `services/snapshotter/gold.py` — ADR-0003 permanece intacto, esta decisión no lo reescribe | `Aceptado` — promovido en el cierre de Hito 2 (`2026-11-20`) |
| [0014](0014-snapshot-and-temporal-contract.md) | Contrato temporal de presentación (`rendered` con envolvente de progreso compacta calculada por el backend, extendiendo `packages/movement` sin duplicarlo) y snapshot coherente: identidad `snapshot_id` separada de una revisión monotónica con ámbito explícito, catálogo cacheable separado del feed operativo, ETA con procedencia | `Propuesto` — aplicado provisionalmente bajo ADR-0007 en MP-019; pendiente de revisión de Codex y promoción del propietario |
| [0015](0015-cold-archive-and-history-contract.md) | Archivo frío idempotente por preparación y sustitución (un origen vacío nunca borra el archivo), agregados byte-estables con orden explícito, una sola implementación del calendario GTFS, mart nuevo por circulación con los huecos como filas, e histórico servido como recursos **nuevos** sobre Parquet sin tocar el contrato de MP-019 | `Propuesto` — aplicado provisionalmente bajo ADR-0007 en MP-021; pendiente de revisión de Codex y promoción del propietario |

Ver `docs/DECISIONS.md` para el resumen ejecutivo de estado de todas las decisiones (aceptadas, propuestas, pendientes y no-go), con enlaces de vuelta a estos ADRs.

## Cómo añadir un ADR nuevo

1. Numerar secuencialmente (`000N-titulo-corto.md`).
2. Usar la misma estructura: Estado, Fecha, Decisores, Contexto, Decisión, Alternativas consideradas, Consecuencias.
3. Registrar el ADR en esta tabla y en `docs/DECISIONS.md`.
4. Ningún ADR se marca `Aceptado` sin autorización del propietario del repositorio (ver `AGENTS.md`, regla 8). Durante un hito autónomo (ver [ADR-0007](0007-autonomy-model.md)), un ADR de arquitectura puede crearse y aplicarse de forma provisional en estado `Propuesto`; se promueve a `Aceptado` solo cuando el propietario lo revisa, normalmente en el cierre del hito — nunca antes.
