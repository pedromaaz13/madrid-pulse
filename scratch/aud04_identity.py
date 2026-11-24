"""AUD-04: identidad (vehiculo/viaje/recorrido), conservacion del GPS bruto y
sentido de los corredores validados."""
from __future__ import annotations
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import CoverageStatus, build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement.schedule import build_trip_schedule

REPLAY = Path("data/hito-03/replay")
topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
cat = build_catalog(topo, gtfs_version="aud04")
corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
trip_route = {t.trip_id: t.route_id for t in topo.trips}

print("== 1) conservacion EXACTA del GPS bruto (feed JSON -> canonico) ==")
for cut in ("1532", "1533"):
    blob = json.loads((REPLAY / cut / "vehicle_positions.json").read_text())
    raw = RawVehiclePositionsFeed.model_validate_json((REPLAY / cut / "vehicle_positions.json").read_bytes())
    canon = {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}
    diffs = 0
    checked = 0
    for entity in blob["entity"]:
        v = entity["vehicle"]
        vid = v["vehicle"]["id"]
        pos = v.get("position") or {}
        o = canon.get(vid)
        if o is None:
            continue
        checked += 1
        if pos.get("latitude") != o.latitude or pos.get("longitude") != o.longitude:
            diffs += 1
            if diffs <= 3:
                print(f"    DIFERENCIA {vid}: feed=({pos.get('latitude')!r},{pos.get('longitude')!r}) "
                      f"canonico=({o.latitude!r},{o.longitude!r})")
    print(f"  corte {cut}: {checked} entidades comparadas, {diffs} con lat/lon alterada")
print()

print("== 2) identidad vehiculo <-> viaje entre los dos cortes ==")
cuts = {}
for cut in ("1532", "1533"):
    raw = RawVehiclePositionsFeed.model_validate_json((REPLAY / cut / "vehicle_positions.json").read_bytes())
    cuts[cut] = {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}
by_trip = defaultdict(set)
for cut, obs in cuts.items():
    for vid, o in obs.items():
        by_trip[o.source_trip_id].add(vid)
shared = {t: v for t, v in by_trip.items() if len(v) > 1}
print(f"  trip_id servido por >1 vehicle_id (union de los dos cortes): {len(shared)}")
for t, v in list(shared.items())[:5]:
    print(f"    {t} -> {sorted(v)}")
changed = [vid for vid in cuts['1532'] if vid in cuts['1533']
           and cuts['1532'][vid].source_trip_id != cuts['1533'][vid].source_trip_id]
print(f"  vehicle_id que cambia de trip_id entre 1532 y 1533: {len(changed)}")
for vid in changed[:5]:
    print(f"    {vid}: {cuts['1532'][vid].source_trip_id} -> {cuts['1533'][vid].source_trip_id}")
labels = Counter()
for o in cuts['1533'].values():
    labels[o.raw_vehicle_label == o.source_vehicle_id] += 1
print(f"  raw_vehicle_label == source_vehicle_id: {dict(labels)}")
print()

print("== 3) sentido (forward) de los corredores VALIDADOS ==")
validated = [e for e in corridors.entries if e.can_map_match]
print(f"  patrones validados: {len(validated)} de {len(corridors.entries)}")
fw = Counter()
for entry in validated:
    # un viaje representativo del patron
    trip_id = None
    for trip in topo.trips:
        if trip.route_id != entry.identity.route_id:
            continue
        times = topo.stop_times_for_trip(trip.trip_id)
        if not times:
            continue
        if tuple(i.stop_id for i in times) != entry.identity.stop_ids:
            continue
        trip_id = trip.trip_id
        break
    if trip_id is None:
        fw["sin viaje resoluble"] += 1
        continue
    sched = build_trip_schedule(topo, entry.corridor, trip_id)
    fw[sched.forward] += 1
print(f"  forward: {dict(fw)}")
