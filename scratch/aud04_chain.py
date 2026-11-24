"""AUD-04: cadena real Renfe -> raw -> matched -> rendered sobre los cortes 1532/1533.

Reproduce exactamente la secuencia de apps/api/snapshot.py:
  normalize (packages.contracts.normalize) -> coverage_for_stops
  -> MovementEngine.position(latest, previous) -> render_from_movement
y, en paralelo, el bloque `map_matched` que snapshot.py publica con
CorridorCatalog.match_position, para contrastar los dos caminos.

Sin PostgreSQL: las dos observaciones reales de cada vehiculo (1532 = previous,
1533 = latest) son el `VehicleHistory` del snapshot.
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import PositionResolution, build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds, PositionMode
from packages.movement.rendering import render_from_movement
from packages.movement.schedule import build_trip_schedule

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
FIXTURES = Path("tests/fixtures")


def load_cut(name: str):
    raw = RawVehiclePositionsFeed.model_validate_json((REPLAY / name / "vehicle_positions.json").read_bytes())
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}, raw.header.timestamp


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud04")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)

    prev_by_vehicle, h1532 = load_cut("1532")
    latest_by_vehicle, h1533 = load_cut("1533")
    print(f"cabecera 1532: {datetime.fromtimestamp(int(h1532), timezone.utc).isoformat()}")
    print(f"cabecera 1533: {datetime.fromtimestamp(int(h1533), timezone.utc).isoformat()}")
    print(f"vehiculos 1532={len(prev_by_vehicle)} 1533={len(latest_by_vehicle)}\n")

    thresholds = MovementThresholds()
    rows = []
    identity_collisions = {}
    for vid, latest in sorted(latest_by_vehicle.items()):
        trip_id = latest.source_trip_id
        identity_collisions.setdefault(trip_id, []).append(vid)

    multi = {t: v for t, v in identity_collisions.items() if len(v) > 1}
    print(f"trip_id compartidos por >1 vehicle_id en el corte 1533: {len(multi)}")
    for t, v in list(multi.items())[:10]:
        print(f"  {t} -> {v}")
    print()

    for vid, latest in sorted(latest_by_vehicle.items()):
        trip_id = latest.source_trip_id
        route_id = trip_route.get(trip_id)
        stop_ids = stops_by_trip.get(trip_id)
        if route_id is None or stop_ids is None:
            continue
        coverage = corridors.coverage_for_stops(route_id, stop_ids)
        if not coverage.can_map_match or coverage.corridor is None:
            continue
        engine = MovementEngine(topo, coverage.corridor, thresholds=thresholds)
        schedule = build_trip_schedule(topo, coverage.corridor, trip_id)
        previous = prev_by_vehicle.get(vid)
        if previous is not None and previous.source_trip_id != trip_id:
            previous = None

        # observed_at real de la observacion 1533
        now = latest.observed_at + timedelta(seconds=10)
        service_date = now.astimezone(MADRID).date()
        try:
            mv = engine.position(
                trip_id=trip_id, service_date=service_date, calculated_at=now,
                latest=latest, previous=previous,
            )
        except ValueError as exc:
            rows.append((vid, trip_id, None, None, None, f"ValueError: {exc}"))
            continue

        em = engine.map_match(latest)
        pm = corridors.match_position(
            coverage.identity.pattern_id, raw_lat=latest.latitude, raw_lon=latest.longitude
        )
        directed = schedule.directed_progress(em.physical_arc_m) if em else None
        rendered = render_from_movement(
            mv, schedule=schedule, corridor=coverage.corridor, service_date=service_date,
            display_at=now, pattern_id=coverage.identity.pattern_id,
            geometry_version=coverage.geometry_version, thresholds=thresholds,
            anchor_distance_from_raw_m=pm.distance_from_raw_m,
        )
        rows.append((
            vid, trip_id, coverage.identity.pattern_id, schedule.forward,
            em.distance_from_track_m if em else None,
            em.physical_arc_m if em else None,
            directed,
            pm.resolution.value, pm.progress_m, pm.distance_from_raw_m,
            mv.position_mode.value, mv.progress_m, mv.anchor_progress_m,
            rendered.rendering_method.value, rendered.progress_m,
            rendered.progress_envelope.speed_mps if rendered.progress_envelope else None,
            rendered.progress_envelope.dwell_until if rendered.progress_envelope else None,
            [a.flag for a in mv.anomalies],
        ))

    good = [r for r in rows if len(r) > 6]
    print(f"circulaciones con corredor validado y cadena completa: {len(good)}\n")

    # 1) distancia GPS <-> geometria
    dists = [r[4] for r in good if r[4] is not None]
    print("== distancia GPS bruto -> geometria (engine.map_match.distance_from_track_m) ==")
    print(f"  n={len(dists)}  min={min(dists):.1f}  p50={statistics.median(dists):.1f}  "
          f"p95={sorted(dists)[int(0.95*(len(dists)-1))]:.1f}  max={max(dists):.1f} m")
    off = [r for r in good if r[4] is not None and r[4] > thresholds.off_track_distance_m]
    print(f"  por encima de off_track_distance_m={thresholds.off_track_distance_m:.0f} m: {len(off)}")
    for r in off:
        print(f"    {r[0]} {r[1]} dist={r[4]:.1f} m  motor={r[10]}  rendered={r[13]}  "
              f"map_matched publicado={r[7]} dist_from_raw={r[9]:.1f}")
    print()

    # 2) dos marcos de progress_m en el mismo payload
    print("== progress_m: marco fisico (map_matched) vs dirigido (rendered) ==")
    backward = [r for r in good if r[3] is False]
    print(f"  patrones forward=False (dirigido = L - fisico): {len(backward)} de {len(good)}")
    mismatch = [r for r in good if r[8] is not None and r[6] is not None and abs(r[8]-r[6]) > 1.0]
    print(f"  circulaciones donde map_matched.progress_m != rendered anchor dirigido (>1 m): {len(mismatch)}")
    for r in mismatch[:6]:
        print(f"    {r[0]} {r[1]} forward={r[3]} fisico={r[8]:.1f} dirigido={r[6]:.1f} "
              f"delta={r[8]-r[6]:+.1f} m")
    print()

    # 3) metodos y modos
    from collections import Counter
    print("== reparto de modos del motor y metodos de presentacion ==")
    print(f"  position_mode:   {dict(Counter(r[10] for r in good))}")
    print(f"  rendering_method: {dict(Counter(r[13] for r in good))}")
    print(f"  dwell_until poblado: {sum(1 for r in good if r[16] is not None)} de {len(good)}")
    speeds = [r[15] for r in good if r[15] is not None]
    if speeds:
        print(f"  speed_mps envolvente: min={min(speeds):.2f} p50={statistics.median(speeds):.2f} "
              f"max={max(speeds):.2f} ({max(speeds)*3.6:.1f} km/h)")
    print(f"  anomalias: {dict(Counter(f for r in good for f in r[17]))}")


if __name__ == "__main__":
    main()
