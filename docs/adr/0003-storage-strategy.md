# ADR-0003: Estrategia de almacenamiento híbrido

- **Estado:** Aceptado (principio), parámetros de retención **propuestos, pendientes de medición real**
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md`

## Contexto

Guardar cada lectura de posición indefinidamente en una base relacional es insostenible en coste y rendimiento a medida que crece el histórico. Valfiguer demuestra, como referencia, que deduplicar y archivar solo cambios significativos reduce drásticamente el volumen (≈11–21 MB/día comprimidos para un conjunto de fuentes mayor que solo la C5).

## Decisión

Arquitectura de almacenamiento en dos capas:

1. **PostgreSQL/PostGIS ("hot")**: estado operativo actual + histórico de corto plazo (días), con índices espaciales y temporales para servir la API en vivo.
2. **Parquet particionado diario ("frío")**, con compresión ZSTD, para histórico de medio/largo plazo, consumido vía DuckDB para agregados (ver DEC-034: MP-015 aplica la disciplina dbt sobre esta capa sin introducir el motor dbt literal).

Deduplicación por hash canónico de payload: observaciones idénticas consecutivas no se almacenan repetidamente.

Se evita explícitamente la opción de almacenar cada poll crudo indefinidamente en Postgres (NOGO-003 en `docs/DECISIONS.md`).

## Alternativas consideradas

- **Solo PostgreSQL con retención indefinida:** descartada — coste y degradación de rendimiento a largo plazo.
- **Solo almacenamiento columnar (sin capa hot relacional):** descartada para el MVP — se necesitan consultas relacionales/espaciales de baja latencia para servir el estado en vivo, que un almacén columnar frío no sirve bien.
- **Kafka/stream processing para el pipeline:** descartada para el MVP — complejidad operativa no justificada al tamaño actual (una línea, C5).

## Consecuencias

- Los números de retención en `docs/DATA_MODEL.md` (7–14 días hot, 90 días `feed_run`, 12 meses frío, etc.) son una propuesta inicial de la investigación, no confirmada — deben validarse con volumen real medido en MP-007/MP-009 antes de fijarse como definitivos (ver DEC-004 en `docs/DECISIONS.md`).
- El snapshotter (MP-009) es responsable de mover datos de "hot" a "frío" de forma reproducible (test de replay).
