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
from packages.database import (
    DISPOSABLE_ENVIRONMENTS,
    DatabaseConfigurationError,
    require_disposable_database,
)
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
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


def _load_madrid_stop_ids(gtfs_source: str, conn: psycopg.Connection) -> frozenset[str] | None:
    config = ApiConfig.from_env()
    network = load_network(config)
    with conn.transaction():
        conn.execute("SELECT set_config('madrid_pulse.anchor_profile', %s, false)",
                     (network.anchor_profile(network.engine.thresholds),))
    topology = (load_feed(gtfs_source, network_id=MADRID_PREFIX)
                if config.short_name or config.network_id != MADRID_PREFIX else network.topology)
    return frozenset(stop.stop_id for stop in topology.stops)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        _run()
    except DatabaseConfigurationError as exc:
        raise SystemExit(str(exc)) from None


def _run() -> None:
    config = CollectorConfig.from_env()
    retry_policy = RetryPolicy(
        max_retries=config.max_retries,
        backoff_base_seconds=config.backoff_base_seconds,
        timeout_seconds=config.request_timeout_seconds,
    )
    with psycopg.connect(config.database_url, autocommit=False) as conn:
        if config.environment in DISPOSABLE_ENVIRONMENTS:
            require_disposable_database(conn)
            conn.rollback()  # Finaliza la transacción de comprobación antes del polling.
        # Bloqueo de sesión. Sigue vigente entre commits y se libera al desconectar.
        with conn.transaction():
            acquired = conn.execute("SELECT pg_try_advisory_lock(1297101395)").fetchone()[0]
            if not acquired:
                raise SystemExit("Ya hay otro colector activo en esta base de datos.")
        madrid_stop_ids = _load_madrid_stop_ids(config.gtfs_source, conn) if config.gtfs_source else None
        logger.info(
            "Colector iniciado: %d feeds, poll=%.0fs, timeout=%.0fs, max_retries=%d, "
            "estaciones Madrid=%s",
            len(config.feeds),
            config.poll_interval_seconds,
            config.request_timeout_seconds,
            config.max_retries,
            len(madrid_stop_ids) if madrid_stop_ids is not None else "sin catálogo",
        )
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
