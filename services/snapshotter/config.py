"""Configuración del exportador histórico."""

from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass(frozen=True)
class SnapshotterConfig:
    database_url: str = "postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5433/madrid_pulse"
    output_dir: str = "data/parquet"

    @classmethod
    def from_env(cls) -> "SnapshotterConfig":
        defaults = cls()
        return cls(
            database_url=os.environ.get("MADRID_PULSE_DATABASE_URL", defaults.database_url),
            output_dir=os.environ.get("SNAPSHOTTER_OUTPUT_DIR", defaults.output_dir),
        )
