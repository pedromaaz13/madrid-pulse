# ARCHITECTURE.md

> **Actualización de estado (2026-11-25).** El texto original de este documento fue una propuesta previa al código. Hoy, **implementado y en `main` (solo local, sin despliegue)**: collector idempotente, normalización y quality layer, PostgreSQL/PostGIS (migraciones 0001–0002), exportación Parquet diaria con DuckDB, API FastAPI `/api/v1`, motor de movimiento y frontend React/MapLibre (Live/History/Explore). **Sigue siendo propuesta o no implementado:** snapshot en CDN, Cloudflare R2, hosting gestionado, VPS, MVP 0 y Live público (ver [`roadmap/RELEASE_ROADMAP.md`](roadmap/RELEASE_ROADMAP.md) y [`plans/MVP_LIVE_END_TO_END.md`](plans/MVP_LIVE_END_TO_END.md), que es PROPUESTA). ADR-0014 y ADR-0015 siguen `Propuesto`. La auditoría H3 halló defectos P0 en movimiento (FR-01) y API de replay (FR-02): la arquitectura descrita no garantiza por sí sola la veracidad ferroviaria. Estado de cada pieza: [`governance/PROJECT_STATE.json`](governance/PROJECT_STATE.json).

Estado de este documento: **propuesta validada por investigación, pendiente de validación empírica en MP-002 a MP-007**. Ningún componente aquí descrito está implementado todavía (ver `docs/STATUS.md`).

## Visión general

Madrid Pulse se construye como **monorepo + modular monolith** para el MVP: procesos separados solo donde aportan aislamiento real (colector, API, frontend), evitando proliferación prematura de microservicios, Kafka, Spark o Kubernetes. Esta decisión está aceptada en [ADR-0003](adr/0003-storage-strategy.md).

```text
Renfe GTFS (estático) ──────────────────────────────┐
Renfe GTFS-Realtime (vehicle_positions,              │
  trip_updates, alerts) ~20-60s (a validar, MP-003)  │
        │                                            │
        ▼                                            │
  Python Collector (services/collector)              │
        │  raw payload + metadata inmutable          │
        ▼                                            │
  Normalizer + Quality Layer                          │
  (packages/contracts, packages/quality)              │
        │                                            │
        ├──► PostgreSQL/PostGIS ◄─────────────────────┘
        │    (estado operativo + hot history, retención corta)
        │
        └──► Parquet diario particionado (histórico frío)
                     │
                     ▼
              DuckDB (analytics/, disciplina dbt sin el motor literal — ADR-0013)
                     │
              métricas/agregados permanentes
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   FastAPI propia          snapshot JSON
   (apps/api)              publicado en CDN (futuro)
         │
         ▼
   React + TypeScript + MapLibre (apps/web)
         │
         └── motor de movimiento (observed/estimated/stale/scheduled)
```

## Componentes y responsabilidades

### `services/collector`
Hace polling de los feeds GTFS-RT de Renfe. Responsabilidades: idempotencia (hash canónico de payload), reintentos con backoff, timeout, registro de `feed_run` (metadatos de cada ejecución: éxito, latencia, nº de entidades). No normaliza ni interpreta — solo captura y persiste el crudo con su metadata.

### Normalizer + Quality Layer (`packages/contracts`, `packages/quality`)
Transforma el payload crudo al contrato canónico interno (ver `docs/DATA_CONTRACTS.md`) y aplica las reglas de `docs/DATA_QUALITY.md`: detección de staleness, anomalías geográficas, duplicados, continuidad temporal. Produce los `quality_flags` que acompañan cada observación.

### `services/snapshotter`
Exporta periódicamente el histórico desde PostgreSQL a Parquet particionado por fecha (y hora para `raw/`), con compresión ZSTD, siguiendo la política de retención de `docs/DATA_MODEL.md`.

### PostgreSQL / PostGIS
Almacena el estado operativo actual y el histórico "caliente" de corto plazo. Se justifica frente a una alternativa solo-columnar porque Madrid Pulse necesita: entidades relacionales (rutas, estaciones, viajes), consultas temporales frecuentes sobre ventanas cortas, e índices espaciales (`GIST`) para geometría de vías y estaciones. Supabase (gestionado) es la opción de producción candidata, no decidida — ver `docs/DEVELOPMENT.md`.

### Parquet + R2/object storage
Histórico frío, particionado diariamente (`date=YYYY-MM-DD/hour=HH` para `raw`, `date=YYYY-MM-DD` para `silver`/`gold`). Se eligió Parquet columnar porque el análisis histórico (Explore) es predominantemente agregado y por línea/estación/fecha, no por fila individual — el formato columnar y la partición diaria permiten escanear solo lo necesario. Cloudflare R2 se señala como candidato por no cobrar egress y por el tamaño estimado del histórico (ver `docs/DECISIONS.md`, DEC-011), pero no se contrata durante MP-001 a MP-006.

### DuckDB (`analytics/` + `services/snapshotter/gold.py`)
Motor analítico local sobre los Parquet para transformar silver → gold (métricas diarias por núcleo/línea/estación) con disciplina dbt (staging/intermediate/marts, tests, documentación, lineage), implementada directamente en `services/snapshotter/gold.py` sin el motor `dbt-core`/`dbt-duckdb` literal — decisión de MP-015 documentada en [ADR-0013](adr/0013-no-literal-dbt-engine.md) (`Propuesto`; no modifica el texto de [ADR-0003](adr/0003-storage-strategy.md), que sigue `Aceptado` sin cambios) y resumida en DEC-034 (ver `analytics/dbt/README.md` para el detalle de implementación).

### FastAPI (`apps/api`)
API propia versionada (`/api/v1/*`), nunca un passthrough de la API de Renfe ni de proyectos de terceros. Expone vehículos en vivo, salud de feed, líneas, estaciones e histórico, siempre con metadatos de frescura/calidad (ver `docs/DATA_CONTRACTS.md`). FastAPI se eligió por tipado con Pydantic (coherente con el contrato canónico interno), generación automática de OpenAPI y ecosistema async maduro para I/O concurrente (polling + servir peticiones).

### React + TypeScript + MapLibre (`apps/web`)
Frontend de los tres módulos de producto (Live/History/Explore). MapLibre se eligió por ser open source (a diferencia de Mapbox GL JS post-v2) y compatible con la necesidad de mostrar geometría ferroviaria propia derivada de OSM con atribución correcta.

### Snapshot CDN (futuro)
Publicación de snapshots JSON estáticos para desacoplar el coste de servir el mapa en vivo del número de espectadores, inspirado en el patrón "fetch periódico → publicar en CDN" documentado en Via Península — adoptado como **principio arquitectónico**, no como código. Se evalúa después de validar el colector (MP-007), no antes.

## Límites de servicio

- El **collector** nunca sirve peticiones HTTP de usuarios; solo escribe a la capa de persistencia.
- La **API** nunca hace polling directo a Renfe; siempre lee de PostgreSQL/Parquet.
- El **frontend** nunca consume APIs de Renfe, CRTM o proyectos de terceros directamente; solo consume la API propia.
- La capa de **calidad** es transversal: tanto el collector como el snapshotter escriben a través de ella antes de persistir como "normalizado".

## Arquitectura local vs. producción futura

**Local (MP-001 a MP-008, ver `docs/DEVELOPMENT.md`):** Docker Compose con PostgreSQL/PostGIS, sin dependencias cloud. DuckDB embebido, sin R2.

**Producción futura (no antes de validar MP-001–MP-009):** PostgreSQL gestionado (Supabase u equivalente), Cloudflare R2 para histórico frío, hosting ligero para FastAPI/collector (Render u equivalente), CDN para snapshots. Ningún proveedor está contratado; ver `docs/DEVELOPMENT.md` para el detalle de qué se activa en qué fase.

## Qué NO se construye en el MVP

- Microservicios desacoplados por dominio (se usan procesos separados solo para collector/API/frontend/snapshotter).
- Kafka, Spark, Kubernetes.
- Ocupación en tiempo real inferida (NOGO-001 en `docs/DECISIONS.md`).
- Reutilización de la API de Valfiguer como dependencia de producción.
