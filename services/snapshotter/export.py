"""Exportación de las tablas "hot" de PostgreSQL a Parquet particionado ("frío").

Usa DuckDB como único motor: su extensión `postgres` lee directamente de
PostgreSQL (sin duplicar lógica de acceso a datos del colector) y su soporte
nativo de Parquet escribe los ficheros particionados con compresión ZSTD. No
se introduce `pandas`/`pyarrow` como dependencias separadas -- DuckDB ya
cubre ambas necesidades (ver ADR-0003: "consumido vía DuckDB/dbt").

Partición temporal: `docs/DATA_MODEL.md` fija `service_date` en
**Europe/Madrid, no UTC** -- un timestamp UTC de madrugada puede pertenecer
al día de servicio SIGUIENTE en hora local (España está en CET/UTC+1 en
noviembre). Por eso la partición `date=`/`hour=` se calcula siempre
convirtiendo el timestamp a `Europe/Madrid` antes de particionar, nunca
sobre el valor UTC crudo.

Columna de observación por tabla: `vehicle_position_observation` y
`trip_update_observation` tienen su propio `observed_at`; `source_ingestion_run`
tiene `started_at`; `data_quality_event` tiene `occurred_at`. **`service_alert`
NO tiene ningún `observed_at`/`received_at` propio** -- su `active_period_start`
es la ventana de VIGENCIA del aviso (puede ser semanas antes o después del
día en que Madrid Pulse lo observó), no el momento en que se ingirió.
Hallazgo real de la revisión de Codex en MP-009: particionar `service_alert`
por `active_period_start` hacía que alertas realmente observadas el día X
desaparecieran del Parquet de ese día si su vigencia caía en otra fecha --
3 alertas reales quedaron fuera del export del 19-nov pese a haberse
ingerido ese mismo día. Corregido uniendo a `source_ingestion_run` (vía
`ingestion_run_id`) y usando `started_at` de esa ejecución como el momento
de observación real, igual que para el resto de tablas.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import duckdb

MADRID_TZ = ZoneInfo("Europe/Madrid")

logger = logging.getLogger(__name__)

STAGING_DIR_NAME = ".staging"
"""Directorio de preparación, **fuera** de `raw/`.

Está deliberadamente fuera del árbol que lee la capa gold
(`services/snapshotter/gold.py` glosa `raw/<tabla>/date=<fecha>/**/*.parquet`):
un Parquet a medio escribir nunca debe poder entrar en un agregado. Empieza
por punto para que, además, ningún `glob` convencional lo recoja.
"""


@dataclass(frozen=True)
class TableSource:
    table: str
    from_clause: str  # FROM de la consulta; alias siempre "t" para la tabla principal
    time_expr: str  # expresión SQL del momento de observación real


# Las cinco tablas "hot", con la expresión que representa de verdad cuándo se
# observó cada fila (no necesariamente una columna propia -- ver docstring).
RAW_TABLE_SOURCES: dict[str, TableSource] = {
    "vehicle_position_observation": TableSource(
        table="vehicle_position_observation",
        from_clause="pg.public.vehicle_position_observation AS t",
        time_expr="t.observed_at",
    ),
    "trip_update_observation": TableSource(
        table="trip_update_observation",
        from_clause="pg.public.trip_update_observation AS t",
        time_expr="t.observed_at",
    ),
    "service_alert": TableSource(
        table="service_alert",
        from_clause=(
            "pg.public.service_alert AS t "
            "JOIN pg.public.source_ingestion_run AS r ON r.id = t.ingestion_run_id"
        ),
        time_expr="r.started_at",
    ),
    "source_ingestion_run": TableSource(
        table="source_ingestion_run",
        from_clause="pg.public.source_ingestion_run AS t",
        time_expr="t.started_at",
    ),
    "data_quality_event": TableSource(
        table="data_quality_event",
        from_clause="pg.public.data_quality_event AS t",
        time_expr="t.occurred_at",
    ),
}


def service_date_utc_bounds(service_date: date) -> tuple[datetime, datetime]:
    """Límites `[inicio, fin)` en UTC del día de servicio `service_date` (Europe/Madrid)."""
    start_local = datetime.combine(service_date, time.min, tzinfo=MADRID_TZ)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(ZoneInfo("UTC")), end_local.astimezone(ZoneInfo("UTC"))


ArchiveAction = Literal["written", "absent", "preserved_existing"]
"""Qué le ocurrió al archivo frío del día en esta ejecución.

- `written`: el día tenía filas en la tabla hot y su subárbol
  `date=<fecha>` se ha reemplazado por completo (idempotente).
- `absent`: el día no tenía filas y tampoco había archivo previo -- nada
  que escribir y nada que conservar.
- `preserved_existing`: el día no tenía filas en la tabla hot pero SÍ existe
  archivo previo. Ver `export_raw_table` -- no se borra.
"""


@dataclass(frozen=True)
class ExportResult:
    table: str
    row_count: int
    output_path: Path
    action: ArchiveAction = "written"
    """Qué se hizo con el archivo del día. `row_count` es siempre el recuento
    leído de la tabla hot, no el del archivo: con `preserved_existing` vale
    `0` y el archivo conserva las filas de la exportación anterior."""


def _connect_with_postgres(database_url: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{database_url}' AS pg (TYPE POSTGRES, READ_ONLY)")
    return con


def _service_date_partition(table_output_dir: Path, service_date: date) -> Path:
    return table_output_dir / f"date={service_date.isoformat()}"


def _has_parquet(directory: Path) -> bool:
    return directory.is_dir() and any(directory.glob("**/*.parquet"))


def export_raw_table(
    con: duckdb.DuckDBPyConnection,
    source: TableSource,
    service_date: date,
    output_dir: Path,
) -> ExportResult:
    """Exporta las filas de `source.table` del día de servicio dado a Parquet particionado.

    El filtro de rango usa los límites UTC reales del día Europe/Madrid sobre
    `source.time_expr` (el momento de observación REAL de la fila, no
    necesariamente una columna propia de esa tabla -- ver docstring del
    módulo); la columna de partición `date`/`hour` se deriva de la misma
    expresión, convertida a hora local.

    **Idempotencia por día de servicio (MP-021).** Escribir directamente sobre
    `raw/<tabla>/` con `OVERWRITE_OR_IGNORE` NO es idempotente: ese modo deja
    intactas las particiones que la nueva ejecución ya no produce. Medido en
    MP-021 con DuckDB 2.0: tras escribir `hour=10` (3 filas) + `hour=11`
    (2 filas) y reprocesar con una única fila en `hour=10`, el glob del archivo
    seguía devolviendo **3 filas** -- las 2 de `hour=11` sobrevivían como
    fantasmas. Con la tabla hot purgada (DEC-011) o corregida, el agregado gold
    heredaba filas que ya no existen en el origen.

    `OVERWRITE` tampoco sirve: es **destructivo a nivel de raíz**. Verificado
    en el mismo banco: exportar `2026-11-20` con `OVERWRITE` sobre
    `raw/<tabla>/` borró el `date=2026-11-19` ya archivado. Un reproceso de un
    día no puede llevarse por delante el resto del histórico.

    La estrategia es por tanto **preparar y sustituir**: se escribe el día en
    `.staging/` (fuera del árbol que lee la capa gold) y, solo cuando la
    escritura ha terminado, se reemplaza el subárbol `date=<fecha>` con un
    `rename` del sistema de ficheros. El resultado no puede contener restos de
    una ejecución anterior y ningún otro día se toca.

    **Un origen vacío no borra el archivo.** Si el día no tiene filas en la
    tabla hot pero sí existe archivo previo, se conserva y se devuelve
    `action="preserved_existing"`. El Parquet es el almacén permanente y la
    tabla hot se purga por diseño (DEC-011/NOGO-003): la ausencia de filas
    calientes no es prueba de que el día no tuviera observaciones -- dato
    ausente no es cero (docs/DATA_QUALITY.md). Vaciar el archivo del día
    exigiría una orden explícita, no un reproceso rutinario.
    """
    utc_start, utc_end = service_date_utc_bounds(service_date)
    table_output_dir = output_dir / "raw" / source.table
    final_partition = _service_date_partition(table_output_dir, service_date)

    (count,) = con.execute(
        f"""
        SELECT count(*) FROM {source.from_clause}
        WHERE {source.time_expr} >= ? AND {source.time_expr} < ?
        """,
        (utc_start, utc_end),
    ).fetchone()

    if count == 0:
        if _has_parquet(final_partition):
            logger.warning(
                "%s: 0 filas calientes para %s pero el archivo frío ya tiene datos de ese día; "
                "se conserva (dato ausente no es cero -- DEC-011)",
                source.table,
                service_date.isoformat(),
            )
            return ExportResult(
                table=source.table,
                row_count=0,
                output_path=table_output_dir,
                action="preserved_existing",
            )
        return ExportResult(
            table=source.table, row_count=0, output_path=table_output_dir, action="absent"
        )

    staging_root = (
        output_dir / STAGING_DIR_NAME / f"{source.table}-{service_date.isoformat()}"
    )
    shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True, exist_ok=True)
    try:
        con.execute(
            f"""
            COPY (
                SELECT t.*,
                    strftime({source.time_expr} AT TIME ZONE 'Europe/Madrid', '%Y-%m-%d') AS date,
                    strftime({source.time_expr} AT TIME ZONE 'Europe/Madrid', '%H') AS hour
                FROM {source.from_clause}
                WHERE {source.time_expr} >= ? AND {source.time_expr} < ?
            ) TO '{staging_root}'
            (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (date, hour), OVERWRITE_OR_IGNORE)
            """,
            (utc_start, utc_end),
        )
        staged_partition = _service_date_partition(staging_root, service_date)
        if not _has_parquet(staged_partition):
            # No puede ocurrir con el filtro de arriba (los límites UTC son los
            # del propio día local, así que toda fila seleccionada particiona en
            # `date=<fecha>`); si ocurriese, fallar es la única opción honesta --
            # dejar el archivo del día a medias sería peor.
            raise RuntimeError(
                f"{source.table}: la preparación de {service_date.isoformat()} no produjo "
                f"ninguna partición en {staged_partition} pese a contar {count} filas"
            )
        table_output_dir.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(final_partition, ignore_errors=True)
        staged_partition.replace(final_partition)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return ExportResult(
        table=source.table, row_count=count, output_path=table_output_dir, action="written"
    )


def export_service_date(
    database_url: str, service_date: date, output_dir: Path
) -> list[ExportResult]:
    """Exporta las cinco tablas "hot" para un día de servicio completo.

    Cada tabla reemplaza su propio subárbol `date=<fecha>` de forma atómica
    (ver `export_raw_table`): reprocesar el mismo día no acumula filas ni deja
    particiones huérfanas, y no toca ningún otro día ya archivado.
    """
    con = _connect_with_postgres(database_url)
    try:
        return [
            export_raw_table(con, source, service_date, output_dir)
            for source in RAW_TABLE_SOURCES.values()
        ]
    finally:
        con.close()
