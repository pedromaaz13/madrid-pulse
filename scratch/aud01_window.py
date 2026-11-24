"""AUD-01: cuánto se desvían del horario los vehículos observados fuera de su ventana."""
from __future__ import annotations
import json, sys, statistics
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.gtfs import build_catalog, load_feed, scheduled_trip_instances_for_date

MADRID = ZoneInfo("Europe/Madrid")
def ss(t: str) -> int:
    h, m, s = (int(p) for p in t.split(":")); return h*3600+m*60+s

topology = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
catalog = build_catalog(topology, gtfs_version="aud01")
route_to_line = {r: l.short_name for l in catalog.lines for r in l.route_ids}
trip_route = {t.trip_id: t.route_id for t in topology.trips}

instant = datetime.fromisoformat("2026-11-20T14:33:21+00:00").astimezone(MADRID)
now_s = instant.hour*3600 + instant.minute*60 + instant.second
instances = {i.trip_id: i for i in scheduled_trip_instances_for_date(topology, instant.date())}

vp = json.loads(Path("data/hito-03/replay/1533/vehicle_positions.json").read_text())
tu = json.loads(Path("data/hito-03/replay/1533/trip_updates.json").read_text())
delays = {e["tripUpdate"]["trip"]["tripId"]: e["tripUpdate"].get("delay")
          for e in tu["entity"]}

inside = after = before = orphan = 0
after_offsets, after_covered_by_delay = [], 0
for entity in vp["entity"]:
    v = entity["vehicle"]
    trip_id = v.get("trip", {}).get("tripId")
    route_id = trip_route.get(trip_id)
    if route_id is None or route_to_line.get(route_id) is None:
        continue
    inst = instances.get(trip_id)
    if inst is None:
        orphan += 1
        continue
    start, end = ss(inst.first_departure_time), ss(inst.last_arrival_time)
    if start <= now_s <= end:
        inside += 1
    elif now_s > end:
        after += 1
        off = now_s - end
        after_offsets.append(off)
        d = delays.get(trip_id)
        if d is not None and off <= d:
            after_covered_by_delay += 1
    else:
        before += 1

print(f"observados resolubles        : {inside+after+before+orphan}")
print(f"  dentro de su ventana       : {inside}")
print(f"  ya terminados por horario  : {after}")
print(f"  aún no salidos por horario : {before}")
print(f"  programados no enumerados  : {orphan}")
if after_offsets:
    print(f"  retardo tras fin de horario: p50 {statistics.median(after_offsets):.0f}s "
          f"max {max(after_offsets)}s")
    print(f"  de esos, explicados por el delay publicado: {after_covered_by_delay}/{after}")
