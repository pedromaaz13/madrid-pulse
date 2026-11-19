# analytics/dbt

**Decisión de alcance (DEC-034):** este directorio no contiene un proyecto
`dbt-core`/`dbt-duckdb` literal. La transformación silver → gold con
disciplina dbt (staging/intermediate/marts, grain explícito, tests,
documentación, lineage — ver `CLAUDE.md`: "Apply dbt principles even if dbt
is not the exact stack") se implementa en `services/snapshotter/gold.py`:

- **Raw** (silver): `services/snapshotter/export.py` exporta las cinco
  tablas "hot" de PostgreSQL a Parquet particionado por día de servicio.
- **Gold — por núcleo** (`build_nucleo_daily_summary`, MP-009): primer
  agregado real, sin dependencias no resueltas en su momento.
- **Gold — por línea/estación** (`build_line_daily_metrics`,
  `build_station_daily_metrics`, MP-015): `daily_line_metrics` y
  `station_daily_metrics` reales (docs/DATA_MODEL.md), resolviendo
  `trip_id`→`route_id`/`stop_id`→`station_id` contra
  `packages.gtfs.Topology` — la resolución que bloqueaba esto desde MP-009
  (DEC-021/DEC-027) ya existe de verdad desde MP-010→MP-014.

Cada función tiene su propio docstring con el límite conocido de ese nivel
(ver DEC-033), tests reales (`services/snapshotter/tests/test_gold.py` y
`test_export_replay.py`) y se invoca desde `python -m services.snapshotter
<YYYY-MM-DD>`.

No se introduce dbt-core como envoltorio porque la resolución `route_id`/
`station_id` es lógica Python (calendario GTFS, `Topology`) que no encaja de
forma natural en modelos SQL puros sin duplicar esa lógica, y DEC-021 ya fijó
un único motor (DuckDB) sin dependencias añadidas salvo que aporten algo que
DuckDB no cubra. Queda como mejora viable de Hito 3 si el volumen o la
estructura de equipo lo justifican.
