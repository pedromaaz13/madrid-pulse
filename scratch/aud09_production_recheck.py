"""AUD-09 (2026-11-24): recálculo con el horizonte REAL de producción de las cifras
que AUD-01 y AUD-04 midieron con un horizonte de 190 s.

Hallazgo de la revisión de Codex `gpt-5.6-sol` · high sobre AUD-09, verificado en
código: para un ancla observada, `render_from_movement` llama a `_envelope` con
`horizon_end = valid_until = ancla + stale_after_s` (180 s;
`packages/movement/rendering.py:279,341-346`). Solo la rama `schedule_only` usa
`calculated_at + stale_after_s` (`:241-246`). Los arneses aprobados
`scratch/aud01_envelope_predeparture.py`, `aud01_snap.py`, `aud04_dwell.py` y
`aud04_dwell_window.py` llaman a `_envelope` directamente con 190 s. No se modifican
(son evidencia aprobada de otras tareas); este guion repite sus medidas con 180 s y
comprueba que esa envolvente coincide exactamente con la que publica
`render_from_movement`.

No escribe en ninguna base de datos ni usa red.
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
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope, render_from_movement
from packages.movement.schedule import build_trip_schedule, service_seconds

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
FIXTURES = Path("tests/fixtures")
TH = MovementThresholds()
CUT_1532 = datetime(2026, 11, 20, 14, 32, 4, tzinfo=timezone.utc)
CUT_1533 = datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc)
MAX_SPEED = TH.max_estimated_speed_kmh / 3.6


def env_at(schedule, service_date, anchor_at, progress_m, horizon_s):
    return _envelope(schedule=schedule, service_date=service_date, anchor_at=anchor_at,
                     anchor_progress_m=progress_m,
                     horizon_end=anchor_at + timedelta(seconds=horizon_s),
                     max_speed_mps=MAX_SPEED)


def load_cut(name: str) -> dict:
    raw = RawVehiclePositionsFeed.model_validate_json(
        (REPLAY / name / "vehicle_positions.json").read_bytes()
    )
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud09")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)
    prev, latest_by_vehicle = load_cut("1532"), load_cut("1533")

    # 0) Equivalencia: _envelope(ancla + 180 s) == envolvente publicada por producción.
    mismatches, n, pre = 0, 0, []
    case_19656 = None
    for vid, latest in sorted(latest_by_vehicle.items()):
        trip_id = latest.source_trip_id
        route_id, stop_ids = trip_route.get(trip_id), stops_by_trip.get(trip_id)
        if route_id is None or stop_ids is None:
            continue
        cov = corridors.coverage_for_stops(route_id, stop_ids)
        if not cov.can_map_match or cov.corridor is None:
            continue
        engine = MovementEngine(topo, cov.corridor, thresholds=TH)
        schedule = build_trip_schedule(topo, cov.corridor, trip_id)
        previous = prev.get(vid)
        if previous is not None and previous.source_trip_id != trip_id:
            previous = None
        anchor_at = latest.observed_at
        sd = anchor_at.astimezone(MADRID).date()
        now = anchor_at + timedelta(seconds=10)
        mv = engine.position(trip_id=trip_id, service_date=sd, calculated_at=now,
                             latest=latest, previous=previous)
        rd = render_from_movement(mv, schedule=schedule, corridor=cov.corridor,
                                  service_date=sd, display_at=now,
                                  pattern_id=cov.identity.pattern_id,
                                  geometry_version=cov.geometry_version, thresholds=TH)
        env = rd.progress_envelope
        if env is None:
            continue
        n += 1
        mine = env_at(schedule, sd, anchor_at, env.progress_m_at_reference, TH.stale_after_s)
        if abs(mine.speed_mps - env.speed_mps) > 1e-9 or mine.dwell_until != env.dwell_until:
            mismatches += 1
        old = env_at(schedule, sd, anchor_at, env.progress_m_at_reference, 10 + TH.stale_after_s)
        anchor_s = service_seconds(anchor_at, sd)
        if anchor_s < schedule.points[0].seconds:
            pre.append((trip_id, schedule.points[0].seconds - anchor_s, env, old))
        if trip_id == "1023V19656C5":
            case_19656 = (env, old)
    print(f"== 0) equivalencia: _envelope(ancla + {TH.stale_after_s:.0f} s) frente a la "
          f"envolvente publicada por render_from_movement: {n - mismatches}/{n} idénticas")

    # 1) Caso 19656 (AUD04-P0-001).
    env, old = case_19656
    print("\n== 1) 1023V19656C5 (AUD04-P0-001) ==")
    for label, e, h in (("producción 180 s", env, TH.stale_after_s),
                        ("arnés AUD-04 190 s", old, 10 + TH.stale_after_s)):
        print(f"   {label}: speed={e.speed_mps:.2f} m/s ({e.speed_mps*3.6:.1f} km/h)  "
              f"avance 30 s={e.speed_mps*30:.1f} m  60 s={e.speed_mps*60:.1f} m  "
              f"horizonte={e.max_progress_m - e.progress_m_at_reference:.1f} m  "
              f"dwell_until={e.dwell_until}")

    # 2) Pre-salida (AUD01-P0-001).
    print(f"\n== 2) pre-salida (AUD01-P0-001): {len(pre)} circulaciones ==")
    for label, k in (("producción 180 s", 2), ("arnés AUD-01 190 s", 3)):
        sp = [r[k].speed_mps for r in pre]
        worst = max(pre, key=lambda r: r[k].max_progress_m - r[k].progress_m_at_reference)
        w = worst[k]
        print(f"   {label}: speed {min(sp):.2f}-{max(sp):.2f} m/s "
              f"({min(sp)*3.6:.1f}-{max(sp)*3.6:.1f} km/h); con avance: "
              f"{sum(1 for s in sp if s > 0.5)}/{len(pre)}; peor caso {worst[0]} a "
              f"{worst[1]:.0f} s ({worst[1]/60:.2f} min) de salir con "
              f"{w.max_progress_m - w.progress_m_at_reference:.1f} m de avance")

    # 3) Salto al llegar el ancla siguiente (AUD01-P0-001, aud01_snap.py).
    data_a = json.loads((REPLAY / "1532" / "vehicle_positions.json").read_text())
    data_b = json.loads((REPLAY / "1533" / "vehicle_positions.json").read_text())

    def raw_positions(data):
        out = {}
        for entity in data["entity"]:
            v = entity["vehicle"]
            trip_id = v.get("trip", {}).get("tripId")
            pos = v.get("position") or {}
            if trip_id and pos.get("latitude") is not None:
                out[v["vehicle"]["id"]] = (trip_id, pos["latitude"], pos["longitude"])
        return out

    a, b = raw_positions(data_a), raw_positions(data_b)
    gap_s = (CUT_1533 - CUT_1532).total_seconds()
    sd = CUT_1532.astimezone(MADRID).date()
    snaps = {TH.stale_after_s: [], 10 + TH.stale_after_s: []}
    for vehicle_id, (trip_id, lat_a, lon_a) in a.items():
        if vehicle_id not in b or b[vehicle_id][0] != trip_id:
            continue
        _, lat_b, lon_b = b[vehicle_id]
        route_id, stop_ids = trip_route.get(trip_id), stops_by_trip.get(trip_id)
        if route_id is None or stop_ids is None:
            continue
        cov = corridors.coverage_for_stops(route_id, stop_ids)
        if not cov.can_map_match or cov.corridor is None:
            continue
        ma = corridors.match_position(cov.identity.pattern_id, raw_lat=lat_a, raw_lon=lon_a)
        mb = corridors.match_position(cov.identity.pattern_id, raw_lat=lat_b, raw_lon=lon_b)
        if (ma.resolution is not PositionResolution.MAP_MATCHED
                or mb.resolution is not PositionResolution.MAP_MATCHED):
            continue
        schedule = build_trip_schedule(topo, cov.corridor, trip_id)
        for h in snaps:
            e = env_at(schedule, sd, CUT_1532, ma.progress_m, h)
            predicted = min(e.progress_m_at_reference + e.speed_mps * gap_s, e.max_progress_m)
            snaps[h].append(abs(mb.progress_m - predicted))
    print(f"\n== 3) salto al llegar el ancla siguiente (77 s), n={len(snaps[TH.stale_after_s])} ==")
    for h, label in ((TH.stale_after_s, "producción 180 s"),
                     (10 + TH.stale_after_s, "arnés AUD-01 190 s")):
        s = snaps[h]
        print(f"   {label}: p50={statistics.median(s):.2f} m  máx={max(s):.2f} m")


if __name__ == "__main__":
    main()
