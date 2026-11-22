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

from packages.contracts.nucleo import MADRID_PREFIX
from packages.gtfs import load_feed
from services.collector.collector import run_cycle
from services.collector.config import CollectorConfig
from services.collector.http_client import RetryPolicy

logger = logging.getLogger(__name__)


def _load_madrid_stop_ids(gtfs_source: str | None) -> frozenset[str] | None:
    """Carga el conjunto de `stop_id` del núcleo Madrid, si hay fuente GTFS.

    Usado solo para resolver avisos por estación en `_persist_alerts`
    (hallazgo MP-017) -- nunca para filtrar posiciones/viajes, que ya tienen
    su propio filtro por núcleo de `route_id`/`trip_id` (ADR-0008).
    """
    if not gtfs_source:
        logger.warning(
            "MADRID_PULSE_GTFS_SOURCE no definido: avisos por estación (sin routeId) "
            "se descartarán como fuera de alcance en vez de resolverse por stop_id "
            "(limitación documentada, no un fallo)."
        )
        return None
    topology = load_feed(gtfs_source, network_id=MADRID_PREFIX)
    return frozenset(stop.stop_id for stop in topology.stops)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = CollectorConfig.from_env()
    retry_policy = RetryPolicy(
        max_retries=config.max_retries,
        backoff_base_seconds=config.backoff_base_seconds,
        timeout_seconds=config.request_timeout_seconds,
    )
    madrid_stop_ids = _load_madrid_stop_ids(config.gtfs_source)
    logger.info(
        "Colector iniciado: %d feeds, poll=%.0fs, timeout=%.0fs, max_retries=%d, "
        "estaciones Madrid=%s",
        len(config.feeds),
        config.poll_interval_seconds,
        config.request_timeout_seconds,
        config.max_retries,
        len(madrid_stop_ids) if madrid_stop_ids is not None else "sin catálogo",
    )
    with psycopg.connect(config.database_url, autocommit=False) as conn:
        while True:
            for feed in config.feeds:
                try:
                    run_cycle(feed, conn, retry_policy, madrid_stop_ids=madrid_stop_ids)
                except Exception:  # noqa: BLE001 - un feed no debe tumbar el colector entero
                    logger.exception("Ciclo inesperadamente fallido para %s", feed.name)
            time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    main()
