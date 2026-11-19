# Madrid Pulse

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

## Estado actual

El proyecto está en **MP-001 — Fundación del repositorio**: estructura, gobernanza, documentación y backlog. Todavía **no hay código de producto**. Ver `docs/STATUS.md` para el tablero vivo y `docs/TASKS.md` para el backlog completo MP-001 a MP-015.

## Estructura del repositorio

```text
madrid-pulse/
├── docs/            Gobernanza, arquitectura, contratos, calidad, legal, ADRs, investigación
├── apps/            web (React/TS/MapLibre), api (FastAPI) — vacíos hasta sus tareas
├── services/        collector, normalizer, snapshotter — vacíos hasta sus tareas
├── packages/        contracts, gtfs, geo, quality — paquetes compartidos, vacíos hasta sus tareas
├── analytics/       dbt, duckdb — capa analítica, vacía hasta sus tareas
├── infra/           docker, cloudflare, migrations — infraestructura, vacía hasta sus tareas
└── tests/           fixtures, integration, e2e — vacíos hasta sus tareas
```

## Documentación clave

| Documento | Contenido |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | Roadmap por fases, dependencias, entregables, gates de calidad |
| [`docs/TASKS.md`](docs/TASKS.md) | Backlog MP-001 a MP-015 con dependencias y criterios de aceptación |
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

Pendiente de decisión — ver `docs/DECISIONS.md` (DEC-002). Los datos de terceros utilizados (Renfe, CRTM, OpenStreetMap) mantienen sus propias licencias; ver `docs/legal/LICENSE_MATRIX.md`.
