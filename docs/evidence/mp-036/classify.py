"""Clasifica el A→B→A exacto de MP-025b en ambos fotogramas de producción."""

from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import groupby
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from apps.api.snapshot import build_snapshot
from infra.operate.validation.segments import check_segment, isolate, windows
from packages.movement import MovementEngine
from tests.postgres import connect_disposable_or_skip

CONFIG = ApiConfig.from_env()


def frame(conn, network, row):
    vehicle, _, gps, visible, _, digest = row
    conn.execute("SELECT set_config('mp036.vehicle', %s, false)", (vehicle,))
    calls = []
    position = MovementEngine.position

    def observed_call(engine, **kwargs):
        latest = kwargs.get("latest")
        calls.append(latest.payload_hash if latest is not None else None)
        return position(engine, **kwargs)

    with patch.object(MovementEngine, "position", observed_call):
        (result,) = build_snapshot(conn, network, CONFIG, visible, display_lag_s=0).vehicles
    if result.raw.gps_observed_at != gps or result.raw.payload_hash != digest:
        return "superseded", None, calls
    if result.rendered.coordinate_space not in ("map_matched", "schedule"):
        return "no_engine", None, calls
    return "engine", result.rendered.last_confirmed_at, calls


def classify(conn, network, start, end, after_gap):
    conn.execute("SET default_transaction_read_only = off")
    isolate(conn, start, end, after_gap)
    check_segment(conn, start, end, after_gap)
    records = conn.execute(
        """
        SELECT v.source_vehicle_id, v.source_trip_id, v.observed_at,
               greatest(v.observed_at, r.started_at), ARRAY[v.latitude,v.longitude], v.payload_hash
        FROM vehicle_position_observation v JOIN source_ingestion_run r ON r.id=v.ingestion_run_id
        ORDER BY v.source_vehicle_id,v.observed_at,v.id
        """
    ).fetchall()
    # La misma serie y los mismos runs. Se reduce un vehículo por respuesta
    # para evitar reconstruir los demás cientos en cada reloj de la prueba.
    conn.execute("ALTER VIEW vehicle_position_observation RENAME TO segment_positions")
    conn.execute(
        """
        CREATE TEMP VIEW vehicle_position_observation AS
        SELECT * FROM segment_positions WHERE source_vehicle_id = current_setting('mp036.vehicle')
        """
    )
    conn.execute("SET default_transaction_read_only = on")
    counts = Counter()
    for _, positions in groupby(records, key=lambda row: row[0]):
        rows = list(positions)
        stamp_counts = Counter(row[2] for row in rows)
        for a, b, c in zip(rows, rows[1:], rows[2:]):
            if not a[1] == b[1] == c[1] or None in a[4] or None in b[4]:
                continue
            if not a[4] == c[4] != b[4]:
                continue
            # El JSON publica el reloj del ancla. Exigir su unicidad en este
            # corte permite usarlo como identidad de B sin ambigüedad.
            if stamp_counts[b[2]] != 1 or stamp_counts[c[2]] != 1:
                raise ValueError("Timestamp de ancla ambiguo")
            counts["total"] += 1
            b_status, b_anchor, _ = frame(conn, network, b)
            c_status, c_anchor, c_calls = frame(conn, network, c)
            # MP-012 reentraba en position con B como observación única.
            if c_calls == [c[-1], b[-1]]:
                counts["fallback_called_with_b"] += 1
            if "superseded" in (b_status, c_status):
                category = "superseded"
            elif "no_engine" in (b_status, c_status):
                category = "no_engine"
            elif c_anchor == b[2] and b_anchor != b[2]:
                category = "resurrected"
                print("resurrected", a[0], b[2].isoformat(), c[3].isoformat())
            elif c_anchor == b[2]:
                category = "accepted_kept"
            elif c_anchor == c[2]:
                category = "return_accepted"
            elif c_anchor is None:
                category = "no_confirmed_anchor"
            else:
                category = "earlier_anchor"
            counts[category] += 1

    conn.execute("SET default_transaction_read_only = off")
    conn.execute("DROP VIEW vehicle_position_observation")
    conn.execute("DROP VIEW segment_positions")
    return counts


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text())
    url = urlsplit(CONFIG.database_dsn)
    if (url.hostname, url.port, url.path, url.query, CONFIG.mode, CONFIG.short_name) != (
        "127.0.0.1", 5459, "/mp036_capture", "", "replay", "",
    ):
        raise ValueError("Se requiere la copia local MP-036 y replay del núcleo completo")
    network = load_network(CONFIG)
    if (
        network.catalog_version != manifest["catalog_version"]
        or network.anchor_profile(CONFIG.thresholds) != manifest["profile"]["anchor_profile"]
    ):
        raise ValueError("Catálogo o perfil distinto al manifiesto")
    total = Counter()
    spans = windows(manifest)
    with connect_disposable_or_skip() as conn:
        conn.autocommit = True
        for i, (start, end) in enumerate(spans):
            result = classify(conn, network, start, end, i > 0)
            print(f"segmento {i + 1}", json.dumps(result, sort_keys=True))
            total.update(result)
    if total["total"] != 416:
        raise ValueError("Población distinta de la jornada 1 de MP-025b")
    print("total", json.dumps(total, sort_keys=True))


if __name__ == "__main__":
    main()
