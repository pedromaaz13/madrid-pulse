"""Ejecuta el benchmark MP-026b y mide por separado el lote de historial."""

from pathlib import Path
from runpy import run_path
from time import perf_counter
from unittest.mock import patch

from apps.api import db
from apps.api.tools.bench_snapshot import percentile

samples_ms = []
expand = getattr(db, "expand_vehicle_histories", None)


def measure(*args, **kwargs):
    started = perf_counter()
    result = expand(*args, **kwargs)
    samples_ms.append((perf_counter() - started) * 1000)
    return result


path = Path("docs/evidence/mp-026b/bench.py")
if expand is None:
    run_path(str(path), run_name="__main__")
else:
    with patch.object(db, "expand_vehicle_histories", measure):
        run_path(str(path), run_name="__main__")
    measured = samples_ms[-60:]
    assert len(samples_ms) == 71, len(samples_ms)
    print(f"Lectura adicional (60 muestras): p50={percentile(measured, 0.5):.2f} ms "
          f"p95={percentile(measured, 0.95):.2f} ms")
