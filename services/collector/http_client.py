"""Cliente HTTP con timeout y reintentos con backoff exponencial.

Usa únicamente `urllib` de la librería estándar -- no se introduce una
dependencia nueva solo para hacer GET a tres endpoints JSON.
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

Fetcher = Callable[[str, float], bytes]


def default_fetcher(url: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "madrid-pulse-collector/1"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        return response.read()


class FetchError(Exception):
    """Todos los reintentos de una petición se agotaron sin éxito."""


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int
    backoff_base_seconds: float
    timeout_seconds: float


def fetch_with_retry(
    url: str,
    policy: RetryPolicy,
    fetcher: Fetcher = default_fetcher,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    """Intenta `fetcher(url, timeout)` hasta `policy.max_retries + 1` veces.

    Backoff exponencial: `backoff_base_seconds * 2**intento` entre reintentos
    (no tras el último intento fallido). Cualquier error de red o timeout se
    trata igual -- el feed de Renfe no distingue entre ambos de forma útil
    para el colector.
    """
    last_error: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return fetcher(url, policy.timeout_seconds)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            last_error = exc
            logger.warning(
                "fetch_with_retry: intento %d/%d falló para %s: %s",
                attempt + 1,
                policy.max_retries + 1,
                url,
                exc,
            )
            if attempt < policy.max_retries:
                sleep(policy.backoff_base_seconds * (2**attempt))
    raise FetchError(f"agotados {policy.max_retries + 1} intentos contra {url}") from last_error
