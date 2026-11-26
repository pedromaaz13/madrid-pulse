"""Capture production decisions at the unmodified MP-025b replay instants."""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

import psycopg

from apps.api import snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from packages.database import require_disposable_database
from packages.geo.corridor import Corridor
from packages.movement import engine
from packages.movement.profile import anchor_profile

from . import metrics, replay, segments


class Trace:
    def __init__(self):
        self.segments = []
        self.identify_original = replay.identify

    def analyze(self, *args):
        self.segments.append({"ticks": [], "rows": defaultdict(list)})
        return self.analyze_original(*args)

    def snapshot(self, conn, network, config, at, **kwargs):
        result = snapshot.build_snapshot(conn, network, config, at, **kwargs)
        vehicles = {}
        for v in result.vehicles:
            r = v.rendered
            vehicles[v.vehicle_id] = {
                "trip": v.trip_id,
                "day": v.service_date,
                "raw_at": v.raw.gps_observed_at,
                "raw_hash": v.raw.payload_hash,
                "confirmed_at": r.last_confirmed_at,
                "confirmed_m": r.last_confirmed_progress_m,
                "anchor_at": r.anchor_observed_at,
                "geometry": r.geometry_version,
                "shown_m": r.progress_m
                if r.coordinate_space == "map_matched"
                else None,
                "method": r.rendering_method,
                "coordinate_space": r.coordinate_space,
                "reason": r.reason,
                "flags": v.quality.flags,
            }
        self.segments[-1]["ticks"].append([at, vehicles])
        return result

    def identify(self, a, v, network, limits):
        self.identify_original(a, v, network, limits)
        row = asdict(a)
        if a.previous_anchor_used:
            rendered = v.rendered
            row["effective_anchor_at"] = rendered.anchor_observed_at
            if rendered.progress_envelope is not None:
                row["effective_plan"] = rendered.progress_envelope.model_dump()
            elif (
                rendered.coordinate_space == "map_matched"
                and rendered.rendering_method == "stale_frozen"
            ):
                row["effective_frozen_m"] = rendered.progress_m
        self.segments[-1]["rows"][a.vehicle].append(row)


def check_target(config):
    port = os.environ.get("MP038_PORT", "5470")
    if port not in ("5470", "5471"):
        raise ValueError("MP038_PORT debe ser 5470 o 5471")
    url = urlsplit(config.database_dsn)
    if (
        (url.scheme, url.hostname, url.port, url.path)
        != ("postgresql", "127.0.0.1", int(port), "/mp038")
        or url.query
        or url.fragment
        or (os.environ.get("MADRID_PULSE_ENV"), config.mode, config.short_name)
        != ("replay", "replay", "")
    ):
        raise ValueError(
            "Se requiere la copia local marcada de MP-038 y el núcleo completo"
        )


@contextmanager
def memoized_projections():
    project = Corridor.project_station
    projections = {}

    def cached_project(corridor, lat, lon):
        # The network retains its corridors. This caches only the pure geometric projection.
        key = (id(corridor), lat, lon)
        if key not in projections:
            projections[key] = project(corridor, lat, lon)
        return projections[key]

    with patch.object(Corridor, "project_station", cached_project):
        yield


def module_origins():
    roots = {
        "harness": Path(__file__).resolve().parents[3],
        "checkout": Path.cwd().resolve(),
    }
    origins = {}
    for origin, modules in (
        ("harness", (__file__, replay.__file__, metrics.__file__, segments.__file__)),
        ("checkout", (snapshot.__file__, engine.__file__)),
    ):
        for filename in modules:
            location = Path(filename).resolve()
            relative = location.relative_to(roots[origin]).as_posix()
            origins[relative] = origin
            print(f"{origin} {location}", file=sys.stderr)
    return origins


def run(manifest_path, dump):
    config = ApiConfig.from_env()
    check_target(config)
    origins = module_origins()
    manifest = json.loads(manifest_path.read_text())
    trace = Trace()
    trace.analyze_original = replay.analyze
    with ExitStack() as stack:
        stack.enter_context(memoized_projections())
        stack.enter_context(patch.object(replay, "analyze", trace.analyze))
        stack.enter_context(patch.object(replay, "build_snapshot", trace.snapshot))
        stack.enter_context(patch.object(replay, "identify", trace.identify))
        network = load_network(config)
        profile = anchor_profile(
            network.gtfs_version, network.corridor_catalog, config.thresholds
        )
        if (network.catalog_version, profile) != (
            manifest["catalog_version"],
            manifest["profile"]["anchor_profile"],
        ):
            raise ValueError("Catálogo o perfil distinto al de captura")
        conn = stack.enter_context(
            psycopg.connect(
                config.database_dsn,
                autocommit=True,
                options="-c default_transaction_read_only=on",
            )
        )
        require_disposable_database(conn)
        result = replay.analyze_segments(
            conn, network, config, manifest, replay.windows(manifest)
        )
        if (
            sum(len(rows) for s in trace.segments for rows in s["rows"].values())
            != result["rows"]
        ):
            raise ValueError("Hay filas fuera de los fotogramas instrumentados")
        if sum(len(s["ticks"]) for s in trace.segments) != result["frames"]:
            raise ValueError("La traza no contiene el mismo reloj que MP-025b")
        return {
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "module_origins": origins,
            "manifest_sha256": replay.sha(manifest_path),
            "dump_sha256": replay.sha(dump),
            "gtfs_version": network.gtfs_version,
            "catalog_version": network.catalog_version,
            "thresholds": asdict(config.thresholds),
            "replay": result,
            "segments": trace.segments,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("dump", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.manifest, args.dump),
            sort_keys=True,
            default=lambda d: d.isoformat(),
            allow_nan=False,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
