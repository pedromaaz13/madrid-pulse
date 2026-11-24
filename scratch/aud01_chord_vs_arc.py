"""AUD-01: velocidad de cuerda (quality) vs velocidad de arco (movimiento) en los dos cortes."""
from __future__ import annotations
import json, math, statistics, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.geo import PositionResolution, build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.quality.engine import QualityThresholds

GAP = 77.0

def hav(la1, lo1, la2, lo2, r=6371008.8):
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def load(cut):
    d = json.loads(Path(f"data/hito-03/replay/{cut}/vehicle_positions.json").read_text())
    out = {}
    for e in d["entity"]:
        v = e["vehicle"]; p = v.get("position") or {}
        t = v.get("trip", {}).get("tripId")
        if t and p.get("latitude") is not None:
            out[v["vehicle"]["id"]] = (t, p["latitude"], p["longitude"])
    return out

topo = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
cat = build_catalog(topo, gtfs_version="aud01")
cor = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
trip_route = {t.trip_id: t.route_id for t in topo.trips}
stops = {}
for t in topo.trips:
    ts = topo.stop_times_for_trip(t.trip_id)
    if ts: stops[t.trip_id] = tuple(x.stop_id for x in ts)

a, b = load("1532"), load("1533")
th = QualityThresholds()
rows = []
for vid, (tid, la, lo) in a.items():
    if vid not in b: continue
    tb, lb, ob = b[vid]
    if tb != tid: continue
    chord = hav(la, lo, lb, ob)
    chord_kmh = chord / GAP * 3.6
    rid, sid = trip_route.get(tid), stops.get(tid)
    arc_kmh = None
    if rid and sid:
        cv = cor.coverage_for_stops(rid, sid)
        if cv.can_map_match and cv.corridor is not None:
            ma = cor.match_position(cv.identity.pattern_id, raw_lat=la, raw_lon=lo)
            mb = cor.match_position(cv.identity.pattern_id, raw_lat=lb, raw_lon=ob)
            if (ma.resolution is PositionResolution.MAP_MATCHED
                    and mb.resolution is PositionResolution.MAP_MATCHED):
                arc_kmh = abs(mb.progress_m - ma.progress_m) / GAP * 3.6
    rows.append((vid, rid, chord_kmh, arc_kmh))

flagged = [r for r in rows if r[2] > th.implausible_speed_kmh]
print(f"pares (vehículo presente en ambos cortes, mismo viaje): {len(rows)}")
print(f"umbral implausible_speed_kmh = {th.implausible_speed_kmh} (sobre distancia de CUERDA)")
print(f"marcarían implausible_speed con la regla real: {len(flagged)}")
arc_rows = [r for r in rows if r[3] is not None]
over_arc = [r for r in arc_rows if r[3] > th.implausible_speed_kmh]
print(f"con velocidad de ARCO > {th.implausible_speed_kmh} km/h: {len(over_arc)}")
for vid, rid, c, arc in sorted(arc_rows, key=lambda r: -(r[3] or 0))[:6]:
    print(f"  {vid:<7} {rid:<12} cuerda {c:>7.1f} km/h   arco {arc:>7.1f} km/h   "
          f"arco/cuerda {arc/c if c>0 else float('inf'):>5.2f}")
ratios = [r[3]/r[2] for r in arc_rows if r[2] > 1]
if ratios:
    print(f"\nrazón arco/cuerda para pares con movimiento real: p50 {statistics.median(ratios):.2f} "
          f"máx {max(ratios):.2f}")

madrid = [r for r in rows if r[1] is not None]
mflag = [r for r in madrid if r[2] > th.implausible_speed_kmh]
print(f"\npares de Madrid (route_id resuelto): {len(madrid)}; "
      f"de ellos sobre el umbral de cuerda: {len(mflag)}")
for vid, rid, c, arc in mflag:
    print(f"  {vid:<7} {rid:<12} cuerda {c:>7.1f} km/h  arco "
          f"{'n/d' if arc is None else f'{arc:7.1f} km/h'}")
blind = [r for r in madrid if r[3] is not None and r[2] <= th.implausible_speed_kmh
         and r[3] > th.implausible_speed_kmh]
print(f"ciegos (cuerda bajo umbral, arco por encima): {len(blind)}")
for vid, rid, c, arc in blind:
    print(f"  {vid:<7} {rid:<12} cuerda {c:>7.1f}  arco {arc:>7.1f}")
