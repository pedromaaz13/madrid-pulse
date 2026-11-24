"""AUD-04: alcance real de `_is_unusable` y coherencia del bloque `map_matched`
cuando el motor rechaza la ultima observacion."""
from __future__ import annotations
import sys
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import timedelta
sys.path.insert(0, ".")
from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds
from packages.movement.schedule import build_trip_schedule

MADRID = ZoneInfo("Europe/Madrid"); TH = MovementThresholds()
R = Path("data/hito-03/replay")
topo = load_feed(R / "fomento_transit.zip", network_id="10")
cat = build_catalog(topo, gtfs_version="aud04")
corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
tr = {t.trip_id: t.route_id for t in topo.trips}

def cut(name):
    raw = RawVehiclePositionsFeed.model_validate_json((R / name / "vehicle_positions.json").read_bytes())
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}

prev, last = cut("1532"), cut("1533")
rows = []
for vid, lat_obs in sorted(last.items()):
    trip = lat_obs.source_trip_id
    times = topo.stop_times_for_trip(trip)
    if not times or trip not in tr:
        continue
    cov = corridors.coverage_for_stops(tr[trip], tuple(i.stop_id for i in times))
    if not cov.can_map_match or cov.corridor is None:
        continue
    eng = MovementEngine(topo, cov.corridor, thresholds=TH)
    sch = build_trip_schedule(topo, cov.corridor, trip)
    p = prev.get(vid)
    if p is not None and p.source_trip_id != trip:
        p = None
    m1, m0 = eng.map_match(lat_obs), (eng.map_match(p) if p else None)
    if m0 is None:
        continue
    el = (lat_obs.observed_at - p.observed_at).total_seconds()
    d = sch.directed_progress(m1.physical_arc_m) - sch.directed_progress(m0.physical_arc_m)
    rows.append((vid, trip, el, d, abs(d)/el*3.6 if el > 0 else None,
                 m1.distance_from_track_m, eng._is_unusable(sch, lat_obs, m1, p, m0)))

print(f"pares (1532,1533) con corredor validado: {len(rows)}")
print(f"umbrales: off_track={TH.off_track_distance_m} m  backward_jump={TH.backward_jump_m} m  "
      f"unusable_backward={TH.unusable_backward_jump_m} m  unusable_speed={TH.unusable_jump_speed_kmh} km/h")
sp = [r[4] for r in rows if r[4] is not None]
print(f"velocidad implicita entre las dos observaciones (cuerda->arco dirigido): "
      f"max={max(sp):.1f} km/h  p50={sorted(sp)[len(sp)//2]:.1f} km/h")
print(f"delta de progreso: min={min(r[3] for r in rows):+.1f} m  max={max(r[3] for r in rows):+.1f} m")
print(f"observaciones declaradas inutilizables por el motor: {sum(1 for r in rows if r[6])}")
for r in sorted(rows, key=lambda x: x[3])[:4]:
    print(f"  retroceso mayor: {r[0]} {r[1]} elapsed={r[2]:.0f}s delta={r[3]:+.1f} m "
          f"v={r[4]:.1f} km/h dist_track={r[5]:.1f} m unusable={r[6]}")
for r in sorted(rows, key=lambda x: -(x[4] or 0))[:3]:
    print(f"  mas rapida:      {r[0]} {r[1]} elapsed={r[2]:.0f}s delta={r[3]:+.1f} m "
          f"v={r[4]:.1f} km/h unusable={r[6]}")
