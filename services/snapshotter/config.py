"""Configuración del exportador histórico."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from packages.database import database_settings_from_env

MADRID_TZ = ZoneInfo("Europe/Madrid")
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SnapshotterConfig:
    database_url: str
    environment: str
    output_dir: str = "data/parquet"
    # Mismas variables de entorno que `apps/api/config.py` (MP-013) -- misma
    # topología GTFS, sin literales de línea embebidos (ADR-0011).
    network_id: str = "10"
    short_name: str = "C5"
    """Filtro de línea comercial. **Vacío = núcleo completo**, igual que en
    `apps/api/gtfs_source.py` (MP-019): el mart de MP-021 tiene que cubrir las
    12 líneas / 42 rutas del catálogo real de Madrid (MP-017/018), no solo el
    piloto C5. El valor por defecto sigue siendo `C5` para no cambiar el
    comportamiento de los tests y del piloto que ya existían; producción pasa
    `MADRID_PULSE_SHORT_NAME=` (vacío). Se resuelve con `line_filter`, nunca
    comparando contra un literal en el código."""

    gtfs_source: Path = REPO_ROOT / "tests" / "fixtures" / "gtfs_c5_real"

    @property
    def line_filter(self) -> str | None:
        """`short_name` normalizado para `packages.gtfs.load_feed`.

        `None` (núcleo completo) cuando la configuración viene vacía o solo
        con espacios -- un `short_name` en blanco no es el nombre de ninguna
        línea real, así que interpretarlo literalmente daría una topología
        vacía en silencio.
        """
        return self.short_name.strip() or None

    @classmethod
    def from_env(cls) -> "SnapshotterConfig":
        database_url, environment = database_settings_from_env()
        defaults = cls(database_url, environment)
        return cls(
            database_url=database_url,
            environment=environment,
            output_dir=os.environ.get("SNAPSHOTTER_OUTPUT_DIR", defaults.output_dir),
            network_id=os.environ.get("MADRID_PULSE_NETWORK_ID", defaults.network_id),
            short_name=os.environ.get("MADRID_PULSE_SHORT_NAME", defaults.short_name),
            gtfs_source=Path(os.environ.get("MADRID_PULSE_GTFS_SOURCE", str(defaults.gtfs_source))),
        )
