"""Punto de entrada: `python -m services.snapshotter <YYYY-MM-DD>`.

Exporta un día de servicio (Europe/Madrid) de PostgreSQL a Parquet
particionado y calcula el resumen gold: por núcleo (MP-009),
y por línea/estación (MP-015, requiere la topología GTFS estática).
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

from packages.gtfs import load_feed
from services.snapshotter.config import SnapshotterConfig
from services.snapshotter.export import export_service_date
from services.snapshotter.gold import (
    build_line_daily_metrics,
    build_nucleo_daily_summary,
    build_station_daily_metrics,
)

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) != 2:
        print("uso: python -m services.snapshotter <YYYY-MM-DD>", file=sys.stderr)
        raise SystemExit(2)
    service_date = date.fromisoformat(sys.argv[1])

    config = SnapshotterConfig.from_env()
    output_dir = Path(config.output_dir)
    results = export_service_date(config.database_url, service_date, output_dir)
    for result in results:
        logger.info("exportado %s: %d filas -> %s", result.table, result.row_count, result.output_path)

    gold = build_nucleo_daily_summary(output_dir, service_date, output_dir)
    logger.info("resumen gold por núcleo: %d filas -> %s", gold.row_count, gold.output_path)

    topology = load_feed(config.gtfs_source, network_id=config.network_id, short_name=config.short_name)
    line_gold = build_line_daily_metrics(output_dir, service_date, output_dir, topology)
    logger.info("daily_line_metrics: %d filas -> %s", line_gold.row_count, line_gold.output_path)
    station_gold = build_station_daily_metrics(output_dir, service_date, output_dir, topology)
    logger.info("station_daily_metrics: %d filas -> %s", station_gold.row_count, station_gold.output_path)


if __name__ == "__main__":
    main()
