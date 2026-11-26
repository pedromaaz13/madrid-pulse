"""Medición local de dos fotogramas y del listado legado de jornada 1."""
from contextlib import ExitStack
from datetime import datetime
from statistics import median
from time import perf_counter
from unittest.mock import patch
from urllib.parse import urlsplit

from apps.api import db, service, snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from tests.postgres import connect_disposable_or_skip

config = ApiConfig.from_env()
url = urlsplit(config.database_dsn)
assert (url.hostname, url.port, url.path, config.mode, config.short_name) == (
    "127.0.0.1", 5459, "/mp036_capture", "replay", "",
)
network = load_network(config)
queries = {}


def measure(name, original):
    def timed(*args, **kwargs):
        start = perf_counter()
        result = original(*args, **kwargs)
        queries[name] = round((perf_counter() - start) * 1000, 2), len(args[-1])
        return result

    return timed


with connect_disposable_or_skip() as conn, ExitStack() as stack:
    for name in ("expand_vehicle_histories", "anchor_metadata"):
        original = getattr(db, name, None)
        if original is not None:
            stack.enter_context(patch.object(db, name, measure(name, original)))

    def snap(at):
        return snapshot.build_snapshot(conn, network, config, at, display_lag_s=0).vehicles

    def vehicles(at):
        return service.list_vehicles(conn, network, at)

    for fn, clock in (
        (snap, "06:22:35.444589"),
        (snap, "08:47:40.042598"),
        (vehicles, "08:47:40.042598"),
    ):
        at = datetime.fromisoformat("2026-11-26T" + clock + "+00:00")
        times = []
        query_times = {}
        for _ in range(6):
            queries.clear()
            start = perf_counter()
            rows = fn(at)
            times.append((perf_counter() - start) * 1000)
            conn.rollback()
            for name, (ms, count) in queries.items():
                query_times.setdefault(name, []).append((ms, count))
        print(fn.__name__, clock, f"{len(rows)} vehículos", f"frío {times[0]:.2f} ms",
              f"mediana caliente {median(times[1:]):.2f} ms")
        for name, values in query_times.items():
            print(name, f"{median([v[0] for v in values[1:]]):.2f} ms",
                  f"filas o vehículos solicitados: {sorted({v[1] for v in values})}")
