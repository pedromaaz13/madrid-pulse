"""Mismo benchmark HTTP, con tiempos separados de historial y metadatos."""
import sys
from contextlib import ExitStack
from runpy import run_path
from time import perf_counter
from unittest.mock import patch

from apps.api import db, snapshot
from apps.api.tools.bench_snapshot import percentile

complete = sys.argv[1] == "complete"
measurements = {}
build_snapshot = snapshot.build_snapshot


def snapshot_with_check(*args, **kwargs):
    result = build_snapshot(*args, **kwargs)
    vehicle = next(v for v in result.vehicles if v.vehicle_id == "V1")
    if complete:
        assert vehicle.rendered.last_confirmed_at is not None
        assert "anchor_history_truncated" not in vehicle.quality.flags
    return result


def time_query(name, original):
    samples = measurements[name] = []

    def measure(*args, **kwargs):
        started = perf_counter()
        result = original(*args, **kwargs)
        samples.append(((perf_counter() - started) * 1000, len(args[-1])))
        return result

    return measure


with ExitStack() as stack:
    for name in ("expand_vehicle_histories", "anchor_metadata"):
        original = getattr(db, name, None)
        if original is not None:
            stack.enter_context(patch.object(db, name, time_query(name, original)))
    stack.enter_context(patch.object(snapshot, "build_snapshot", snapshot_with_check))
    run_path("docs/evidence/mp-026b/bench.py", run_name="__main__")

for name, samples in measurements.items():
    assert len(samples) == 71
    times, counts = zip(*samples[-60:])
    print(name, f"p50={percentile(times, .5):.2f} ms p95={percentile(times, .95):.2f} ms",
          f"filas o vehículos solicitados: {sorted(set(counts))}")
