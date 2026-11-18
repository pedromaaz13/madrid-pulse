# Madrid Pulse — Brief inicial de transferencia a Orca

**Fecha:** 2026-11-18  
**Destino:** repositorio `pedromaaz13/madrid-pulse`, tarea `MP-001`  
**Estado:** contexto de arranque derivado de decisiones de planificación; **NO sustituye el informe íntegro de Investigación avanzada ni es una auditoría de código verificada**.

## 1. Misión y producto

Construir **Madrid Pulse**, plataforma independiente de visualización en tiempo real y analítica histórica del ferrocarril de Cercanías Madrid, ampliable posteriormente. Un mapa fluido y visualmente excelente con modos futuros **Live, History y Explore**, respaldado por ingesta propia y persistencia histórica, es el producto objetivo. En el primer MVP, limitar la prueba a una línea (preferencia **C5**) hasta demostrar identificación correcta de trenes, geometrías y calidad de datos.

**Diferenciación:** no ser únicamente otro mapa de trenes. Priorizar trazabilidad de fuentes, historial consultable, reproducibilidad, datos de puntualidad acompañados de indicadores de cobertura/confianza, visualización temporal, documentación técnica y una API propia. No afirmar ocupación de cada tren en directo si los operadores no proporcionan sensores confiables: los datos anuales de viajeros por estación son otra clase de datos; los reportes colaborativos serían una fase posterior y requieren política de privacidad.

## 2. Referencias y usos permitidos

- Via Península: https://viapeninsula.gariasf.com/ y repositorio https://github.com/gariasf/viapeninsula . Estudiar **fuentes, arquitectura, ADRs, contratos publicados, procesamiento GTFS/GTFS-RT, geometría y motor de movimiento**. La licencia del repositorio se ha identificado preliminarmente como **AGPL-3.0**: inspeccionar el LICENSE real y solicitar revisión legal si se plantea reutilizar código; por defecto **NO COPIAR NI IMPORTAR código fuente**. Rediseñar/implementar de forma independiente. Como patrón de diseño, la aproximación conocida es «horarios impulsan movimiento continuo, GPS corrige tiempos» y publicación de snapshots compactos en CDN; comprobar alcance y matices contra fuentes.
- Valfiguer: https://trenes.valfiguer.com/ y artículo de autor https://valfiguer.com/es/blog/despues-de-urda-un-mapa-abierto-de-los-trenes . Usar de benchmark de funcionalidades, no de API upstream de producción; no afirmar disponibilidad de repositorio público de la aplicación sin verificarlo.
- Renfe oficial: https://tiempo-real.renfe.com/ ; fuentes candidatas a **validar mediante solicitudes reales, estatus HTTP, respuesta y permisos**: `https://gtfsrt.renfe.com/vehicle_positions.json`, `https://gtfsrt.renfe.com/trip_updates.json`, `https://gtfsrt.renfe.com/alerts.json`; GTFS estático: https://data.renfe.com/dataset/horarios-cercanias . Estos enlaces son *hipótesis de trabajo que requieren pruebas*, no contratos garantizados.
- Estadísticas agregadas Madrid: https://datos.comunidad.madrid/dataset/1923861 . Verificar período, definición, licencia y granularidad.
- Alternativas código MIT para estudiar: https://github.com/xaviour-ai-2026/atlas-ferroviario , https://github.com/Niltra/cercanias ; confirmar cada licencia y procedencia.

## 3. Arquitectura candidata, sujeta a ADR y POC

```text
Renfe static GTFS ---------> ingestión versionada / catálogos de servicio
Renfe GTFS-Realtime -------> collector Python (~20 s nominal, sujeto a prueba)
                                 |----> Postgres/PostGIS (estado actual + detalle reciente)
                                 |----> Parquet diario comprimido (histórico particionado)
                                 |----> snapshot JSON normalizado y versionado
                                                              |
                              CDN/R2 cuando corresponda <----+
                                                              |
React + TypeScript + Vite + MapLibre  <------ snapshot + API FastAPI
     |                          ^                       |
     +--> motor de movimiento   |                   Postgres + DuckDB/dbt
          (observado / interpolado / estimado / obsoleto)
```

**Principios:** monorepo; desarrollo local antes de contratar infraestructura; Python/FastAPI/Pydantic para ingesta/API; PostgreSQL/PostGIS para geografía y consulta operacional; Parquet con particiones diarias y compresión para detalle histórico; DuckDB + dbt para calidad y agregados; MapLibre y geometrías de ferrocarril derivadas de fuentes con licencia respetada; publicación de snapshot en CDN sólo después de POC. No Kafka, Spark ni Kubernetes inicialmente.

**Movimiento:** distinguir posiciones (a) observadas por fuente, (b) interpoladas con retraso entre puntos conocidos y (c) estimadas a partir de horarios/correcciones. Nunca etiquetar (c) como GPS observado. Incluir timestamp, latencia, estado de frescura, confianza y trazas de corrección; testear saltos de estación y velocidades físicamente inverosímiles.

## 4. Datos y contratos a diseñar, NO copiados de terceros

Entidades candidatas: `source_ingestion_run`, `source_feed_version`, `dim_station`, `dim_route`, `dim_service_trip`, `vehicle_position_observation`, `vehicle_position_clean`, `trip_update_observation`, `service_alert`, `daily_trip_quality`, `daily_station_metrics`, `snapshot_publication`. IDs de viaje deben contemplar la **fecha de servicio local Europe/Madrid** y diferencias entre `trip_id`, `vehicle_id`, `train_id`; almacenar instantes como UTC. Claves idempotentes y trazabilidad de procedencia. PostGIS para geometrías e índices; particiones de detalle y agregados calculados reproduciblemente. Empezar contratos con ejemplos **sintéticos** antes de confundirlos con JSON oficiales; generar fixtures reales sólo tras validación.

API propia propuesta (pendiente de contrato/ADR): `/api/v1/health`, `/api/v1/live/trains`, `/api/v1/trains/{train_id}`, `/api/v1/stations`, `/api/v1/history/trains`; esquema de snapshot JSON versionado, `observed_at`, `ingested_at`, `published_at`, `position_kind`, `freshness`, `source`. El cliente no debe consumir APIs de proyectos independientes como dependencia del producto.

**Retención inicial propuesta, revisable tras dimensionamiento:** posiciones detalladas 14 días en Postgres; exportación Parquet por día de servicio con compresión ZSTD para 12 meses; métricas diarias agregadas por tiempo indefinido mientras sean útiles; eliminar duplicados técnicos sin perder la distinción entre observaciones repetidas y eventos reales. Probar volumen y costes con 24–72 h de ingesta antes de confirmar estos valores. Backups/restore separados del archivado analítico.

## 5. Fases y puertas de calidad (borrador)

- **F0. Gobierno:** MP-001 repo / documentación / decisiones / protocolo agentes / no código de producto.
- **F1. Factibilidad de datos:** verificar feeds, licencias, frecuencia, cobertura Madrid/C5 y mapeo real de trip IDs.
- **F2. Contratos y calidad:** JSON/proto/fixtures, claves, timestamps, test de parsing y validaciones.
- **F3. Ingesta mínima:** collector, reintentos, observabilidad, idempotencia; 24 h sin errores críticos.
- **F4. Persistencia:** PostGIS/Parquet particionado, estrategia de retención, backup y lectura.
- **F5. API y snapshot:** FastAPI + snapshot normalizado; indicadores de frescura y errores.
- **F6. Mapa C5:** React/TypeScript/MapLibre; estaciones, trenes observados, controles de fuente.
- **F7. Motor de movimiento:** geometrías, pruebas deterministas de interpolación/estimación, transparencia de posición.
- **F8. Histórico y analítica:** DuckDB/dbt, cobertura, puntualidad con restricciones, playback.
- **F9. Despliegue/seguridad:** CI/CD, CDN/R2/VPS según coste, alertas de ingestión y backups.
- **F10. Expansión:** resto Madrid, Explore, ocupación colaborativa sólo si se diseña privacidad.

Las fases son **propuesta inicial**: convertirlas en tareas MP-001 a MP-015 (o más, justificando numeración), con dependencias, dueño, revisor, tests y criterio de aceptación; no implementar todo en un solo prompt.

## 6. Gobernanza de agentes y repositorio

**IDE:** Orca. **Agentes:** Claude Code (primera implementación) y Codex (primera revisión), alternando responsabilidades en tareas futuras. Prohibido usar «Orca» como nombre de un tercer agente. Una rama/worktree por tarea; commits atómicos; revisión independiente de diffs; no merge sin evidencia de tests y conformidad. Orca ejecuta agentes con permisos potencialmente amplios por defecto: verificar ajustes de autonomía antes de ejecutar comandos. No compartir credenciales ni datos privados; las pruebas de feeds deben respetar límites y condiciones de servicio.

Primer conjunto de documentación a crear en rama `chore/mp-001-foundation`:

```text
README.md
AGENTS.md
CLAUDE.md
.gitignore
docs/PLAN.md
docs/TASKS.md
docs/STATUS.md
docs/CHANGELOG.md
docs/DECISIONS.md
docs/ARCHITECTURE.md
docs/DATA_CONTRACTS.md
docs/research/README.md
docs/legal/DATA_SOURCES.md
docs/legal/LICENSE_MATRIX.md
docs/adr/README.md
.github/pull_request_template.md
```

Añadir el **informe completo original de Investigación avanzada** a `docs/research/` cuando el usuario lo exporte, conservando citas y enlaces. **Este brief no equivale a ese informe**. Si algo no pudo verificarse, registrar `UNVERIFIED`/`PENDING` en lugar de presentarlo como hecho.

## 7. MP-001 — Definición de hecho

1. Existen archivos mínimos y enlaces navegables entre README, PLAN, TASKS, STATUS, DECISIONS y ADRs.
2. La arquitectura separa claramente confirmado/propuesto/pendiente.
3. Cada tarea muestra ID, dependencia, ejecutor (Claude Code o Codex), revisor contrario, inputs/outputs, comandos de prueba cuando existan y aceptación.
4. `STATUS.md` contiene checklist de tareas y una bitácora que remite a commits/PRs.
5. `AGENTS.md` y `CLAUDE.md` no se contradicen, imponen un ámbito acotado y verificación real.
6. PR de documentación abierto, revisado por Codex con hallazgos documentados; sin fusionar hasta aprobación del usuario.
7. No se han configurado servicios cloud, desplegado servicios ni implementado el producto durante MP-001.

**Dudas no bloqueantes:** licencia definitiva propia (MIT/Apache 2.0/AGPL y requisitos), dominio, identidad gráfica, prioridad de expansión a Metro/EMT, retención exacta según volumen, proveedor cloud, políticas de colaboración de usuarios. Resolver después de medir y contrastar.
