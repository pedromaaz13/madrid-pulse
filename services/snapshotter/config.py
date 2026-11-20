"""Configuración del exportador histórico."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID_TZ = ZoneInfo("Europe/Madrid")
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SnapshotterConfig:
    database_url: str = "postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5433/madrid_pulse"
    output_dir: str = "data/parquet"
    # Mismas variables de entorno que `apps/api/config.py` (MP-013) -- misma
    # topología GTFS, sin literales de línea embebidos (ADR-0011).
    network_id: str = "10"
    short_name: str = "C5"
    gtfs_source: Path = REPO_ROOT / "tests" / "fixtures" / "gtfs_c5_real"

    @classmethod
    def from_env(cls) -> "SnapshotterConfig":
        defaults = cls()
        return cls(
            database_url=os.environ.get("MADRID_PULSE_DATABASE_URL", defaults.database_url),
            output_dir=os.environ.get("SNAPSHOTTER_OUTPUT_DIR", defaults.output_dir),
            network_id=os.environ.get("MADRID_PULSE_NETWORK_ID", defaults.network_id),
            short_name=os.environ.get("MADRID_PULSE_SHORT_NAME", defaults.short_name),
            gtfs_source=Path(os.environ.get("MADRID_PULSE_GTFS_SOURCE", str(defaults.gtfs_source))),
        )
