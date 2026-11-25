"""Procedencia de la envolvente, compartida por ingesta y presentación."""

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from .model import MovementThresholds


def thresholds_from_env():
    defaults = MovementThresholds()
    return MovementThresholds(
        **{
            name: float(os.environ.get("MADRID_PULSE_" + name.upper(), getattr(defaults, name)))
            for name in ("stop_zone_radius_m", "min_dwell_s", "cancel_max_age_s")
        }
    )


def source_version(source: Path) -> str:
    digest = hashlib.sha256()
    if source.is_file():
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        for path in sorted(item for item in source.iterdir() if item.is_file()):
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _envelope_thresholds(thresholds):
    return {
        name: getattr(thresholds, name)
        for name in (
            "stop_zone_radius_m",
            "min_dwell_s",
            "cancel_max_age_s",
            "stale_after_s",
            "max_estimated_speed_kmh",
            "off_track_distance_m",
        )
    }


def anchor_profile(gtfs_version, catalog, thresholds):
    geometries = {
        entry.identity.pattern_id: entry.geometry_version
        for entry in catalog.entries
        if entry.can_map_match
    }
    return json.dumps(
        [gtfs_version, _envelope_thresholds(thresholds), geometries],
        sort_keys=True,
        separators=(",", ":"),
    )


@lru_cache(maxsize=16)
def _decode(stored):
    try:
        fields = json.loads(stored)
    except (ValueError, TypeError):
        return None
    if isinstance(fields, list) and len(fields) == 3 and isinstance(fields[2], dict):
        return fields
    return None


def profile_matches(stored, gtfs_version, pattern, geometry_version, thresholds):
    fields = _decode(stored)
    return bool(
        fields
        and fields[0] == gtfs_version
        and fields[1] == _envelope_thresholds(thresholds)
        and geometry_version
        and fields[2].get(pattern) == geometry_version
    )
