"""Descarga el GTFS estático completo de Renfe para operar la API en vivo.

La fixture reducida de MP-010 (`tests/fixtures/gtfs_c5_real/`) solo contiene
15 trips representativos -- suficiente para tests deterministas, insuficiente
para resolver los `trip_id` reales que llegan por el feed en vivo (DEC-023:
el ZIP completo no se versiona por tamaño/volatilidad). Este script lo
descarga a una ruta local para que `MADRID_PULSE_GTFS_SOURCE` apunte a él.

Uso:
  python -m apps.api.tools.fetch_gtfs_static [DEST]
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
DEFAULT_DEST = Path(__file__).resolve().parents[3] / "data" / "gtfs_static" / "fomento_transit.zip"


def main() -> None:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "madrid-pulse-api/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        dest.write_bytes(response.read())
    print(f"escrito {dest} ({dest.stat().st_size} bytes)")
    print(f"export MADRID_PULSE_GTFS_SOURCE={dest}")


if __name__ == "__main__":
    main()
