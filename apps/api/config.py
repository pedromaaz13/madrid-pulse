"""Configuración de la API — sin identificadores de línea embebidos (ADR-0011)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from packages.movement.model import MovementThresholds
from packages.movement.profile import thresholds_from_env
from packages.database import database_settings_from_env

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ApiConfig:
    database_dsn: str
    network_id: str
    short_name: str
    gtfs_fixture_dir: Path
    osm_relation_path: Path
    geometry_fixtures_root: Path
    feed_stale_after_s: float
    mode: str
    operator_delay_max_age_s: float
    display_lag_s: float
    archive_dir: Path
    """Raíz del histórico frío en Parquet (MP-021), la misma que escribe
    `services/snapshotter` con `SNAPSHOTTER_OUTPUT_DIR`. Se lee en solo
    lectura y solo desde `apps/api/history.py`; nada del estado operativo
    pasa por aquí."""

    gtfs_expiring_days: int = 7
    thresholds: MovementThresholds = MovementThresholds()

    @classmethod
    def from_env(cls) -> "ApiConfig":
        database_url, _ = database_settings_from_env()
        gtfs_expiring_days = int(os.environ.get("MADRID_PULSE_GTFS_EXPIRING_DAYS", "7"))
        if gtfs_expiring_days < 0:
            raise ValueError("MADRID_PULSE_GTFS_EXPIRING_DAYS debe ser un entero no negativo")
        return cls(
            database_dsn=database_url,
            network_id=os.environ.get("MADRID_PULSE_NETWORK_ID", "10"),
            short_name=os.environ.get("MADRID_PULSE_SHORT_NAME", "C5"),
            gtfs_fixture_dir=Path(
                os.environ.get(
                    "MADRID_PULSE_GTFS_SOURCE",
                    str(REPO_ROOT / "tests" / "fixtures" / "gtfs_c5_real"),
                )
            ),
            osm_relation_path=Path(
                os.environ.get(
                    "MADRID_PULSE_OSM_RELATION",
                    str(REPO_ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"),
                )
            ),
            geometry_fixtures_root=Path(
                os.environ.get(
                    "MADRID_PULSE_GEOMETRY_FIXTURES_ROOT", str(REPO_ROOT / "tests" / "fixtures")
                )
            ),
            feed_stale_after_s=float(os.environ.get("MADRID_PULSE_FEED_STALE_AFTER_S", "180")),
            mode=os.environ.get("MADRID_PULSE_MODE", "replay").strip().lower(),
            operator_delay_max_age_s=float(
                os.environ.get("MADRID_PULSE_OPERATOR_DELAY_MAX_AGE_S", "600")
            ),
            display_lag_s=float(os.environ.get("MADRID_PULSE_DISPLAY_LAG_S", "0")),
            archive_dir=Path(
                os.environ.get("SNAPSHOTTER_OUTPUT_DIR", str(REPO_ROOT / "data" / "parquet"))
            ),
            gtfs_expiring_days=gtfs_expiring_days,
            thresholds=thresholds_from_env(),
        )
