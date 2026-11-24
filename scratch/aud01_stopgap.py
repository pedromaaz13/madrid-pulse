"""AUD-01: intervalo real entre paradas del núcleo Madrid vs horizonte de 180 s."""
from __future__ import annotations
import statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.gtfs import load_feed

def ss(t: str) -> int:
    h, m, s = (int(p) for p in t.split(":")); return h*3600+m*60+s

topology = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
gaps = []
dwells = []
per_trip_stops = []
for trip in topology.trips:
    times = topology.stop_times_for_trip(trip.trip_id)
    if len(times) < 2:
        continue
    per_trip_stops.append(len(times))
    for a, b in zip(times, times[1:]):
        gaps.append(ss(b.arrival_time) - ss(a.departure_time))
    for st in times:
        dwells.append(ss(st.departure_time) - ss(st.arrival_time))

gaps = [g for g in gaps if 0 <= g <= 3600]
print(f"trips con >=2 paradas: {len(per_trip_stops)}")
print(f"paradas por trip: p50 {statistics.median(per_trip_stops):.0f} max {max(per_trip_stops)}")
print(f"intervalo salida->llegada siguiente: n={len(gaps)} p50 {statistics.median(gaps):.0f}s "
      f"media {statistics.mean(gaps):.0f}s p10 {statistics.quantiles(gaps, n=10)[0]:.0f}s "
      f"p90 {statistics.quantiles(gaps, n=10)[8]:.0f}s")
print(f"parada (dwell) declarada: p50 {statistics.median(dwells):.0f}s "
      f"fracción de dwell>0: {sum(1 for d in dwells if d>0)/len(dwells):.1%}")
under = sum(1 for g in gaps if g <= 180)
print(f"intervalos <= 180 s (horizonte por defecto): {under}/{len(gaps)} = {100*under/len(gaps):.1f}%")
