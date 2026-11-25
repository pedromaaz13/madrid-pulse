"""Punto de entrada: `python -m services.snapshotter <YYYY-MM-DD>`.

Exporta un día de servicio (Europe/Madrid) de PostgreSQL a Parquet
particionado y calcula los agregados: por núcleo (MP-009), por línea/estación
(MP-015) y por circulación (MP-021, `history.py`).

Reprocesar el mismo día es seguro y determinista: el export reemplaza de
forma atómica el subárbol `date=<fecha>` de cada tabla y los cuatro agregados
se reescriben con orden explícito, así que el resultado no depende de cuántas
veces se haya corrido (ver `export.py` y `gold.py`).

El alcance de líneas lo fija la configuración, no el código:
`MADRID_PULSE_SHORT_NAME=` (vacío) calcula el mart para el núcleo Madrid
completo -- las 12 líneas / 42 rutas de MP-017/018 -- y un valor concreto lo
restringe a esa línea (ver `SnapshotterConfig.line_filter`).
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

import psycopg

from packages.database import (
    DISPOSABLE_ENVIRONMENTS,
    DatabaseConfigurationError,
    require_disposable_database,
)
from packages.gtfs import load_feed
from services.snapshotter.config import SnapshotterConfig
from services.snapshotter.export import export_service_date
from services.snapshotter.gold import (
    build_line_daily_metrics,
    build_nucleo_daily_summary,
    build_station_daily_metrics,
)
from services.snapshotter.history import build_circulation_daily_history

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) != 2:
        print("uso: python -m services.snapshotter <YYYY-MM-DD>", file=sys.stderr)
        raise SystemExit(2)
    service_date = date.fromisoformat(sys.argv[1])

    try:
        config = SnapshotterConfig.from_env()
        if config.environment in DISPOSABLE_ENVIRONMENTS:
            with psycopg.connect(config.database_url, autocommit=True) as conn:
                require_disposable_database(conn)
    except DatabaseConfigurationError as exc:
        raise SystemExit(str(exc)) from None

    output_dir = Path(config.output_dir)
    results = export_service_date(config.database_url, service_date, output_dir)
    for result in results:
        logger.info(
            "exportado %s: %d filas (%s) -> %s",
            result.table, result.row_count, result.action, result.output_path,
        )

    gold = build_nucleo_daily_summary(output_dir, service_date, output_dir)
    logger.info("resumen gold por núcleo: %d filas -> %s", gold.row_count, gold.output_path)

    topology = load_feed(
        config.gtfs_source, network_id=config.network_id, short_name=config.line_filter
    )
    logger.info(
        "topología GTFS: %d rutas, %d viajes (filtro de línea=%s)",
        len(topology.routes), len(topology.trips), config.line_filter or "núcleo completo",
    )
    line_gold = build_line_daily_metrics(output_dir, service_date, output_dir, topology)
    logger.info("daily_line_metrics: %d filas -> %s", line_gold.row_count, line_gold.output_path)
    station_gold = build_station_daily_metrics(output_dir, service_date, output_dir, topology)
    logger.info("station_daily_metrics: %d filas -> %s", station_gold.row_count, station_gold.output_path)
    circulation_gold = build_circulation_daily_history(
        output_dir, service_date, output_dir, topology
    )
    logger.info(
        "circulation_daily_history: %d filas -> %s",
        circulation_gold.row_count, circulation_gold.output_path,
    )


if __name__ == "__main__":
    main()
