# DECISIONS.md — Registro de decisiones

Las decisiones arquitectónicas con detalle completo de alternativas viven como ADR en `docs/adr/`. Este documento es el índice y resumen ejecutivo de estado: qué está **aceptado**, qué está **propuesto** (viable pero sujeto a validación posterior) y qué está **pendiente** (requiere decisión del propietario o datos que todavía no existen).

## Aceptadas

| ID | Decisión | ADR | Justificación resumida |
|---|---|---|---|
| DEC-001 | MVP limitado a la línea C5 de Cercanías Madrid, antes de expandir a toda la red | [ADR-0001](adr/0001-project-scope-c5.md) | Validar identificación de trenes, geometría y calidad de datos a escala manejable antes de escalar. |
| DEC-005 | Arquitectura monorepo + modular monolith para el MVP; evitar microservicios prematuros | [ADR-0003](adr/0003-storage-strategy.md) | Simplicidad operativa; los procesos se separan físicamente solo donde aportan aislamiento real (collector, API, frontend). |
| DEC-006 | Las fuentes primarias de datos son Renfe (GTFS/GTFS-RT) y CRTM directamente, no APIs de terceros como Valfiguer | [ADR-0002](adr/0002-data-sources.md) | Reproducibilidad, control de licencia y evitar dependencia de una capa intermedia no garantizada. |
| DEC-007 | Timestamps internos siempre en UTC (`timestamptz`); `Europe/Madrid` solo en presentación y calendario de servicio GTFS | [ADR-0004](adr/0004-position-model.md) | Evita errores de DST en históricos, especialmente en cambios de hora y de día de servicio. |
| DEC-008 | No copiar código AGPL-3.0 de Via Península; solo estudio conceptual y reimplementación independiente | [ADR-0006](adr/0006-licensing-policy.md) | Evitar obligaciones AGPL no deseadas sobre el código propio sin que exista ADR explícito que las acepte. |
| DEC-009 | No se publican métricas de puntualidad sin exponer su cobertura (qué fracción de los viajes tenía dato disponible) | — (principio transversal, ver `AGENTS.md`) | Evitar presentar una muestra parcial como si representara todo el servicio. |
| DEC-014 | Modelo de autonomía acotada: autorización por hito (no por tarea individual), commits de iteración permitidos dentro del worktree de la tarea (nunca push/PR/merge), gates de pausa en tiempo real limitados a decisiones de licencia/coste | [ADR-0007](adr/0007-autonomy-model.md) | Decisión explícita del propietario (2026-11-18) para permitir avanzar el backlog MP-002 en adelante sin supervisión constante, preservando el control sobre lo irreversible (historial de Git compartido, licencia, coste). |

## Propuestas (viables, pendientes de validación empírica)

| ID | Decisión | ADR | Qué falta para aceptarla |
|---|---|---|---|
| DEC-010 | Modelo de posición en cuatro estados: `OBSERVED / ESTIMATED / STALE / SCHEDULED` | [ADR-0004](adr/0004-position-model.md) | Calibrar umbrales de transición (`0–60s`, `60–180s`, `>180s`) con datos reales de MP-003/MP-012. |
| DEC-011 | Modelo de almacenamiento híbrido: PostgreSQL/PostGIS (hot, retención corta) + Parquet particionado diario en object storage (histórico frío) + agregados permanentes | [ADR-0003](adr/0003-storage-strategy.md) | Medir volumen real de ingesta de la C5 (MP-007) para confirmar los supuestos de tamaño extrapolados de Valfiguer. |
| DEC-012 | Contratos de API propios versionados bajo `/api/v1/*`, con campos de frescura/calidad en cada respuesta relevante | [ADR-0005](adr/0005-api-contract.md) | Reconciliar la propuesta de endpoints del informe completo con la del brief inicial (ver `docs/DATA_CONTRACTS.md` — discrepancia documentada) antes de MP-013. |
| DEC-013 | Deduplicación de observaciones por hash canónico de payload, con `seen_count` opcional en lugar de almacenar cada poll idéntico | [ADR-0003](adr/0003-storage-strategy.md) | Validar en MP-007 que el hash canónico no descarta cambios relevantes de campos no incluidos en el hash. |
| DEC-015 | Mecánica de convergencia de ramas encadenadas para una tarea con varias dependencias (p. ej. MP-012 = MP-008 + MP-010 + MP-011): qué rama se usa como base y cómo se integran las demás | [ADR-0007](adr/0007-autonomy-model.md) | Sugerencia no bloqueante de Codex en la 4ª revisión de MP-001: decidir y documentar el mecanismo exacto en `AGENTS.md` antes de abrir el worktree de MP-012. No bloquea Hito 1 (MP-002→MP-009), que es una cadena sin convergencias. |

## Pendientes (requieren decisión del propietario, no bloquean MP-001)

| ID | Pregunta | Opciones | Cuándo decidir |
|---|---|---|---|
| DEC-002 | Licencia del código propio de Madrid Pulse | MIT · Apache-2.0 · otra | Antes de hacer público el repositorio o de aceptar contribuciones externas. No bloquea MP-001 a MP-006 (desarrollo local). |
| DEC-003 | Visibilidad del repositorio en GitHub | Público · Privado inicialmente | Puede decidirse en cualquier momento antes de invitar colaboradores externos. |
| DEC-004 | Retención definitiva del histórico detallado en almacenamiento frío | Permanente · 12 meses · 24 meses | Debe fijarse después de medir volumen/coste real con 24–72 h de ingesta (MP-007/MP-009), no antes. El brief inicial propone 12 meses con compresión ZSTD como punto de partida revisable. |

## No-Go explícitos (del informe de investigación)

| ID | Decisión | Razón |
|---|---|---|
| NOGO-001 | No implementar ocupación en tiempo real inferida | Sin fuente legítima de sensores; solo viable con fuente real o capa colaborativa futura con política de privacidad explícita. |
| NOGO-002 | No copiar código AGPL-3.0 de Via Península en un producto con licencia potencialmente incompatible | Ver DEC-008 / ADR-0006. |
| NOGO-003 | No almacenar indefinidamente cada poll de posición en PostgreSQL | Insostenible en coste y rendimiento; modelo hot + Parquet diario + agregados permanentes es la alternativa aceptada (DEC-011). |

## Relación con ADRs

Cada decisión con alternativas y trade-offs documentados tiene su propio ADR en `docs/adr/`. Este índice no sustituye la lectura del ADR correspondiente antes de proponer un cambio.
