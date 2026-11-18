"""Configuración del colector, siempre desde variables de entorno (sin hardcodear secretos).

URLs reales verificadas en MP-003 (`docs/research/MP-003-probe-findings.md`):
`Cache-Control: max-age=30` en los tres feeds -- 30s es el intervalo de polling
por defecto, ligeramente por encima del refresco real observado (~20-22s) para
no sondear más rápido de lo que el propio feed se actualiza.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeedConfig:
    name: str
    url: str


@dataclass(frozen=True)
class CollectorConfig:
    feeds: tuple[FeedConfig, ...] = field(
        default_factory=lambda: (
            FeedConfig("vehicle_positions", "https://gtfsrt.renfe.com/vehicle_positions.json"),
            FeedConfig("trip_updates", "https://gtfsrt.renfe.com/trip_updates.json"),
            FeedConfig("alerts", "https://gtfsrt.renfe.com/alerts.json"),
        )
    )
    poll_interval_seconds: float = 30.0
    request_timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_base_seconds: float = 1.0
    database_url: str = "postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5433/madrid_pulse"

    @classmethod
    def from_env(cls) -> "CollectorConfig":
        defaults = cls()
        return cls(
            poll_interval_seconds=float(
                os.environ.get("COLLECTOR_POLL_INTERVAL_SECONDS", defaults.poll_interval_seconds)
            ),
            request_timeout_seconds=float(
                os.environ.get(
                    "COLLECTOR_REQUEST_TIMEOUT_SECONDS", defaults.request_timeout_seconds
                )
            ),
            max_retries=int(os.environ.get("COLLECTOR_MAX_RETRIES", defaults.max_retries)),
            backoff_base_seconds=float(
                os.environ.get("COLLECTOR_BACKOFF_BASE_SECONDS", defaults.backoff_base_seconds)
            ),
            database_url=os.environ.get("MADRID_PULSE_DATABASE_URL", defaults.database_url),
        )
