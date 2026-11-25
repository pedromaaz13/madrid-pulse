# Madrid Pulse

> **Estado (2026-11-24): versión local auditada — NO-GO para despliegue público.**
> El Hito 3 (`MP-016`→`MP-022`) está cerrado **solo en local** y la auditoría adversarial AUD-00…AUD-09 sigue demostrando **2 defectos P0 abiertos** (FR-01: el mapa pone en marcha trenes que el operador declara detenidos; FR-02: el replay `?at=` oculta datos reales) y 16 P1. Decisión y evidencia: [`docs/audits/hito-03/AUDIT_EXECUTIVE_DECISION.md`](docs/audits/hito-03/AUDIT_EXECUTIVE_DECISION.md). Uso previsto: local/demo supervisada. Las secciones «Estado actual» y «Estructura» de más abajo describen la fase inicial del proyecto y están **desactualizadas** (hallazgo FR-11 de la auditoría, pendiente en `MP-027`).

Plataforma open source de visualización en tiempo real y analítica histórica de Cercanías Madrid.

## Visión

Madrid Pulse no es "otro mapa de trenes". Es un producto de datos propio con tres módulos:

- **Live** — mapa en tiempo real con motor de movimiento transparente (observado / interpolado / estimado / obsoleto), nunca presentando una estimación como posición GPS real.
- **History** — histórico propio consultable de posiciones, retrasos y calidad de servicio, con particiones diarias y métricas agregadas permanentes.
- **Explore** — análisis temporal y exploratorio sobre el histórico (puntualidad con cobertura explícita, patrones por estación/línea/franja horaria).

El MVP arranca con una sola línea, **C5 Cercanías Madrid**, y solo se ampliará a toda la red de Cercanías Madrid —y después al resto de España— una vez validada la calidad de datos, los contratos y el motor de movimiento sobre datos reales.

## Por qué existe este proyecto

Via Península ha resuelto brillantemente el problema de movimiento visual sobre geometría ferroviaria real (AGPL-3.0, **solo estudio conceptual, no copia de código**). Valfiguer ha resuelto bien la normalización, transparencia de fuente y explotación de históricos. Madrid Pulse toma esas lecciones de arquitectura sin copiar implementación, y construye su propia base de datos, contratos de API y pipeline analítico desde el primer día, pensados para crecer.

Ver `docs/research/deep-research-report.md` y `docs/research/MADRID_PULSE_BRIEF_INICIAL.md` para el análisis completo que fundamenta estas decisiones.

## Estado actual (2026-11-25)

**Hay código de producto implementado, solo en local.** Los Hitos 1–3 (`MP-001`→`MP-022`) y la auditoría adversarial (`AUD-00`→`AUD-09`) están integrados en `main` (merge `7583ca5`, etiqueta `h3-local-audited`): colector GTFS-RT idempotente, esquema PostgreSQL/PostGIS, motor de calidad, histórico Parquet, API FastAPI `/api/v1`, frontend React/MapLibre (Live/History/Explore) sobre toda Cercanías Madrid. **No hay servicio desplegado ni URL pública.** Veredicto de la auditoría: **NO-GO para despliegue público; CONDITIONAL GO para el código local**, con dos defectos P0 abiertos (FR-01, FR-02). El Hito 4, la demo estática (MVP 0) y el Design Discovery están **planificados, no iniciados**. Índice completo: [`docs/README.md`](docs/README.md); estado vivo: [`docs/STATUS.md`](docs/STATUS.md).

## Estructura del repositorio

```text
madrid-pulse/
├── docs/            Gobernanza, arquitectura, contratos, calidad, legal, ADRs, investigación
├── apps/            web (React/TS/MapLibre), api (FastAPI)
├── services/        collector, normalizer, snapshotter
├── packages/        contracts, gtfs, geo, quality, movement — paquetes compartidos
├── analytics/       capa analítica (DuckDB, ADR-0013)
├── infra/           docker, migrations, operate (cloudflare: vacío por decisión)
└── tests/           fixtures, integration, e2e (+ tests/governance)
```

## Documentación clave

| Documento | Contenido |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | Roadmap por fases, dependencias, entregables, gates de calidad |
| [`docs/README.md`](docs/README.md) | Índice canónico: qué leer primero, qué es vigente, propuesta o histórico |
| [`docs/TASKS.md`](docs/TASKS.md) | Fichas MP-001 a MP-022 e índice generado del backlog planificado |
| [`docs/roadmap/`](docs/roadmap/) | Hitos, hoja de ruta de releases y equivalencias de IDs |
| [`docs/governance/`](docs/governance/) | Estado estructurado canónico y protocolo de actualización |
| [`docs/STATUS.md`](docs/STATUS.md) | Tablero vivo: tarea actual, bloqueos, siguiente tarea autorizable |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decisiones aceptadas, propuestas y pendientes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Componentes, flujo de datos, justificación tecnológica |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Entidades, claves, versionado GTFS, retención |
| [`docs/DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md) | Contratos de API propuestos, ejemplos sintéticos |
| [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md) | Métricas de frescura, anomalías, cobertura |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Entorno local y servicios por fase |
| [`docs/legal/`](docs/legal/) | Fuentes de datos, licencias, atribución |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`docs/research/`](docs/research/) | Investigación original íntegra |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Protocolo de colaboración entre agentes |

## Agentes de desarrollo

Este repositorio se desarrolla con asistencia de dos agentes de IA como **herramientas de desarrollo**, no como autores: **Claude Code** (Anthropic) y **OpenAI Codex**, operando dentro de **Orca IDE** (el IDE, no un tercer agente). El protocolo completo de ejecución y revisión cruzada está en [`AGENTS.md`](AGENTS.md). El único contribuidor que figura en el historial de Git es el propietario humano del repositorio.

## Licencia

Código propio y documentación original: [MIT](LICENSE) (DEC-002, DEC-045). Los datos y materiales de terceros (Renfe, CRTM, OpenStreetMap, fixtures derivadas de OSM bajo ODbL, dependencias) **no** quedan cubiertos por esa licencia y mantienen la suya: ver [`NOTICE.md`](NOTICE.md) y [`docs/legal/LICENSE_MATRIX.md`](docs/legal/LICENSE_MATRIX.md).
