# ADR-0013: No se introduce dbt-core/dbt-duckdb como motor literal para la capa gold

- **Estado:** `Aceptado` — promovido por el propietario en el cierre de Hito 2 (`2026-11-20`), tras la auditoría de integración de Hito 2 (`docs/STATUS.md`), que confirmó contra `requirements.txt`/`gold.py`/`analytics/dbt/README.md` que no se introdujo `dbt-core`/`dbt-duckdb` y que ADR-0003 permanece intacto.
- **Fecha:** 2026-11-20 (promovido el mismo día)
- **Decisores:** Claude Code (ejecutor de MP-015); auditado por OpenAI Codex como revisor de MP-015 y de la auditoría de integración de Hito 2; promovido por el propietario (Pedro Matute).

## Contexto

[ADR-0003](0003-storage-strategy.md) (`Aceptado`) establece que el histórico frío en Parquet se "consume vía DuckDB/dbt para agregados", siguiendo la disciplina dbt (staging/intermediate/marts, tests, documentación, lineage) descrita también en `docs/ARCHITECTURE.md` desde MP-001 — sin comprometerse en ese momento a si dbt-core se introduciría literalmente como motor ("a decidir en MP-009").

MP-009 (DEC-021) implementó la primera capa gold (`services/snapshotter/gold.py`, resumen por núcleo) usando únicamente DuckDB, sin `dbt-core`, por ser la única tarea posible en ese momento (la resolución `route_id`/`station_id` necesaria para el agregado objetivo de `docs/DATA_MODEL.md` no existía todavía). MP-015 extiende esa misma capa (`build_line_daily_metrics`/`build_station_daily_metrics`, DEC-033) ahora que esa resolución sí existe (`packages.gtfs.Topology`, MP-010→MP-014) — y es la primera tarea donde introducir dbt-core literalmente era técnicamente viable, por lo que exige decidirlo explícitamente en vez de aplazarlo de nuevo.

La resolución `trip_id`→`route_id`/`stop_id`→`station_id` (calendario GTFS, proyección sobre topología) es lógica Python con ramificación condicional (p. ej. `_scheduled_trip_ids_by_route`, que cruza `calendar.txt` con el día de la semana y rangos de fecha), no una transformación tabular que encaje de forma natural en un modelo SQL de dbt sin reimplementarla en SQL y duplicar esa lógica en dos lenguajes.

**Hallazgo de proceso de la revisión de Codex en MP-015:** una primera versión de esta tarea documentó esta misma decisión solo como DEC-034 (`docs/DECISIONS.md`) y, al hacerlo, reescribió directamente la "Decisión" de ADR-0003 (`Aceptado`) sin pasar por el proceso de ADR (regla 8, `AGENTS.md`) — corregido revirtiendo ADR-0003 a su texto original y escribiendo este ADR específico en su lugar, como exige el régimen de autonomía (ADR-0007: un cambio de arquitectura se propone como ADR nuevo en estado `Propuesto`, no se edita en caliente un ADR ya `Aceptado`).

## Decisión

1. **ADR-0003 permanece `Aceptado` sin modificación de su texto.** Su mención de "DuckDB/dbt" describe el ecosistema de consumo de la capa fría a nivel de principio arquitectónico, no un compromiso con el binario `dbt-core` concreto.
2. **MP-015 no introduce `dbt-core`/`dbt-duckdb` como motor literal.** La disciplina dbt (capas raw→gold, grano explícito, tests, documentación, lineage) se aplica directamente en `services/snapshotter/gold.py`: cada función (`build_nucleo_daily_summary`, `build_line_daily_metrics`, `build_station_daily_metrics`) es una capa documentada, testeada y versionada, sin el motor dbt.
3. **`analytics/dbt/` permanece como documentado, no implementado literalmente** — ver `analytics/dbt/README.md`. No se borra ni se le quita su lugar en la estructura del monorepo.
4. Esta decisión es revisable: si un futuro hito (más líneas, más volumen, más colaboradores tocando transformaciones SQL) hace que la resolución Python dificulte mantener la disciplina dbt sin el motor real, introducir `dbt-core` sobre la capa ya construida es viable sin reescribir `services/snapshotter/gold.py` desde cero.

## Alternativas consideradas

- **Introducir `dbt-core`/`dbt-duckdb` ahora, con la resolución `route_id`/`station_id` hecha en un modelo SQL/Python híbrido (Python para resolver, dbt para las capas tabulares finales):** evaluada — añade un segundo lenguaje de transformación (Jinja/SQL de dbt) y un segundo runtime a mantener para una capa que, con DuckDB puro, ya es real, testeada y documentada; no se adoptó por falta de valor proporcional a su coste en este hito, no por imposibilidad técnica.
- **No decidir nada y dejar la ambigüedad de ADR-0003 sin resolver:** descartada — es exactamente el estado que llevó a reescribir sin querer un ADR aceptado; una decisión explícita, aunque sea "no todavía", evita que un futuro ejecutor interprete la ambigüedad de forma distinta.
- **Reescribir ADR-0003 directamente para eliminar la mención a dbt:** descartada por el mismo motivo documentado en el "Contexto" — violaría el proceso de ADR (regla 8) sobre un ADR ya `Aceptado`.

## Consecuencias

- `docs/ARCHITECTURE.md` y `docs/PLAN.md` (F9) referencian este ADR al describir la capa DuckDB/`analytics/`, en vez de implicar directamente que "dbt no se usa" sin fundamento documentado.
- `docs/DECISIONS.md` (DEC-034) pasa a referenciar este ADR como su respaldo formal, en vez de presentarse como la única justificación de un cambio de arquitectura.
- Cualquier tarea futura que SÍ introduzca `dbt-core` debe revisar este ADR y proponer su revisión o sustitución, no ignorarlo en silencio.
- Pendiente: el propietario revisa y promueve este ADR a `Aceptado` (o lo corrige) en el cierre de Hito 2, conforme a ADR-0007.
