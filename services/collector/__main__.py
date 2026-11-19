"""Punto de entrada: `python -m services.collector`.

Bucle infinito de polling sobre los tres feeds, con backoff entre reintentos
de red (ver `http_client.py`) y pausa fija `poll_interval_seconds` entre
ciclos completos. Un fallo de red en un feed no detiene el colector: se
registra como `source_ingestion_run.status = 'error'` y el bucle continúa
con el siguiente feed/ciclo.
"""

from __future__ import annotations

import logging
import time

import psycopg

from services.collector.collector import run_cycle
from services.collector.config import CollectorConfig
from services.collector.http_client import RetryPolicy

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = CollectorConfig.from_env()
    retry_policy = RetryPolicy(
        max_retries=config.max_retries,
        backoff_base_seconds=config.backoff_base_seconds,
        timeout_seconds=config.request_timeout_seconds,
    )
    logger.info(
        "Colector iniciado: %d feeds, poll=%.0fs, timeout=%.0fs, max_retries=%d",
        len(config.feeds),
        config.poll_interval_seconds,
        config.request_timeout_seconds,
        config.max_retries,
    )
    with psycopg.connect(config.database_url, autocommit=False) as conn:
        while True:
            for feed in config.feeds:
                try:
                    run_cycle(feed, conn, retry_policy)
                except Exception:  # noqa: BLE001 - un feed no debe tumbar el colector entero
                    logger.exception("Ciclo inesperadamente fallido para %s", feed.name)
            time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    main()
