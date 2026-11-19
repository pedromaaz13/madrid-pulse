# Architecture Decision Records

| ADR | Título | Estado |
|---|---|---|
| [0001](0001-project-scope-c5.md) | Alcance del MVP limitado a la línea C5 | Aceptado |
| [0002](0002-data-sources.md) | Fuentes de datos primarias | Aceptado (fuentes); verificación pendiente MP-002/MP-003 |
| [0003](0003-storage-strategy.md) | Estrategia de almacenamiento híbrido | Aceptado (principio); parámetros pendientes |
| [0004](0004-position-model.md) | Modelo de posición en cuatro estados | Aceptado (principio); umbrales pendientes de calibración |
| [0005](0005-api-contract.md) | Contrato de API propio versionado | Propuesto; confirmación en MP-013 |
| [0006](0006-licensing-policy.md) | Política de licenciamiento frente a proyectos de referencia | Aceptado |
| [0007](0007-autonomy-model.md) | Modelo de autonomía acotada para la ejecución del backlog (autorización por hito, commits en worktree, gates limitados a licencia/coste) | Aceptado |
| [0008](0008-route-identity.md) | `route_id` completo (no el código de línea) como identificador de ruta, tras descubrir en MP-003 que "C5" existe también en Asturias y Andalucía | `Propuesto` — pendiente de revisión del propietario en cierre de Hito 2 (corregido en MP-015: el cierre real de Hito 1 pasó sin promoción) |
| [0009](0009-unobserved-raw-fields.md) | Campos del modelo candidato no observados en el feed real (`speed_kmh`/`bearing` nullable, `current_stop_id` en vez de `current_stop_sequence`, se elimina `effect`/`cause`/`header_text` de alertas) | `Propuesto` — pendiente de revisión de Codex (MP-005, ya auditado) y del propietario en cierre de Hito 2 (corregido en MP-015: el cierre real de Hito 1 pasó sin promoción) |
| [0010](0010-dedup-strategy.md) | Deduplicación por hash canónico de payload completo comparado contra la última fila almacenada por clave de entidad de origen; sin `seen_count` | `Propuesto` — pendiente de revisión del propietario en cierre de Hito 2 (corregido en MP-015: el cierre real de Hito 1 pasó sin promoción) |
| [0011](0011-public-scope-vs-technical-pilot.md) | C5 es el piloto técnico de Hito 2; el objetivo de primera versión pública es toda la red de Cercanías Madrid — complementa ADR-0001 sin reescribirlo | `Propuesto` — pendiente de revisión del propietario en cierre de Hito 2 |
| [0012](0012-movement-package-boundary.md) | Motor de movimiento como capa independiente entre geometría, topología, calidad y API | `Propuesto` — pendiente de revisión del propietario en cierre de Hito 2 |

Ver `docs/DECISIONS.md` para el resumen ejecutivo de estado de todas las decisiones (aceptadas, propuestas, pendientes y no-go), con enlaces de vuelta a estos ADRs.

## Cómo añadir un ADR nuevo

1. Numerar secuencialmente (`000N-titulo-corto.md`).
2. Usar la misma estructura: Estado, Fecha, Decisores, Contexto, Decisión, Alternativas consideradas, Consecuencias.
3. Registrar el ADR en esta tabla y en `docs/DECISIONS.md`.
4. Ningún ADR se marca `Aceptado` sin autorización del propietario del repositorio (ver `AGENTS.md`, regla 8). Durante un hito autónomo (ver [ADR-0007](0007-autonomy-model.md)), un ADR de arquitectura puede crearse y aplicarse de forma provisional en estado `Propuesto`; se promueve a `Aceptado` solo cuando el propietario lo revisa, normalmente en el cierre del hito — nunca antes.
