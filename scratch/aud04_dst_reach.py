"""AUD-04: alcance real de la ventana afectada por el cambio de hora."""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.gtfs import load_feed, scheduled_trip_instances_for_date
from datetime import date

topo = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
vals = Counter()
late_trips = {}
for trip in topo.trips:
    times = topo.stop_times_for_trip(trip.trip_id)
    for item in times:
        for value in (item.arrival_time, item.departure_time):
            if not value:
                continue
            h, m, s = (int(p) for p in value.split(":"))
            if h in (0, 1, 24, 25, 26):
                vals[f"{h:02d}:{m:02d}"] += 1
                late_trips.setdefault(trip.trip_id, []).append(value)
print("horas de stop_times en las franjas que rodean el salto de 02:00 local:")
for key in sorted(vals):
    print(f"  {key}  x{vals[key]}")
print(f"\nviajes con alguna hora en esas franjas: {len(late_trips)}")
ext = sorted(late_trips.items(), key=lambda kv: max(kv[1]))[-6:]
for trip_id, v in ext:
    print(f"  {trip_id}: {min(v)} -> {max(v)}")

# calendario: opera el servicio de esos viajes en los dos domingos de cambio?
for d in (date(2026, 3, 28), date(2026, 3, 29), date(2026, 10, 24), date(2026, 10, 25)):
    inst = {i.trip_id: i for i in scheduled_trip_instances_for_date(topo, d)}
    hit = [t for t in late_trips if t in inst]
    print(f"\n{d} ({d.strftime('%A')}): viajes programados con horas 00/01/24:xx = {len(hit)}")
    for t in hit[:5]:
        print(f"   {t}: {inst[t].first_departure_time} -> {inst[t].last_arrival_time}")
