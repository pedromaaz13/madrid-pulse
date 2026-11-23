"""Punto de entrada: `python -m services.collector`.

Bucle infinito de polling sobre los tres feeds, con backoff entre reintentos
de red (ver `http_client.py`) y pausa fija `poll_interval_seconds` entre
ciclos completos. Un fallo de red en un feed no detiene el colector: se
registra como `source_ingestion_run.status = 'error'` y el bucle continúa
con el siguiente feed/ciclo.

**Un fallo de red no es lo mismo que perder la base (MP-021).** La conexión a
PostgreSQL es larga y vive fuera del bucle: si la base se reinicia, esa
conexión queda inservible para siempre y **ningún** ciclo posterior puede
escribir. Hasta MP-021 el `except Exception` de abajo también tragaba ese caso,
así que el proceso seguía vivo, consumiendo los tres feeds cada 30 s y
descartándolos en silencio: reproducido de verdad reiniciando el contenedor de
PostgreSQL con el colector en marcha -- 90 s después el proceso seguía en pie
y el recuento de `source_ingestion_run` llevaba congelado desde el reinicio,
con `psycopg.OperationalError: the connection is lost` en cada ciclo.

Un proceso vivo que no ingiere es peor que un proceso muerto: nadie lo
reinicia porque nadie lo ve caer. Por eso una conexión perdida termina el
proceso con `EXIT_DATABASE_LOST`, y es el supervisor
(`infra/operate/supervise-collector.sh`, `KeepAlive` de launchd o
`Restart=always` de systemd) quien lo levanta con una conexión nueva. El hueco
de captura queda además registrado como tal en el histórico, que es lo
correcto: no se observó, y eso se ve.
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

EXIT_DATABASE_LOST = 75
"""Código de salida cuando se pierde la conexión con PostgreSQL.

`75` es `EX_TEMPFAIL` de `sysexits.h`: fallo temporal, reintentar tiene
sentido. Lo distingue de `0` (parada limpia) y de `1` (error de programa), de
modo que el supervisor y las bitácoras puedan diferenciar "la base se fue" de
"el colector está roto".
"""


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
                except psycopg.OperationalError:
                    # La conexión se ha perdido (base reiniciada, red caída,
                    # servidor cerrado). No es recuperable dentro de este
                    # proceso: se sale para que el supervisor arranque uno
                    # nuevo con una conexión limpia -- ver docstring.
                    logger.exception(
                        "Conexión con PostgreSQL perdida durante %s; terminando para que el "
                        "supervisor reinicie el colector con una conexión nueva",
                        feed.name,
                    )
                    raise SystemExit(EXIT_DATABASE_LOST) from None
                except Exception:  # noqa: BLE001 - un feed no debe tumbar el colector entero
                    logger.exception("Ciclo inesperadamente fallido para %s", feed.name)
            time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    main()
