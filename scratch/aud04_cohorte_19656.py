"""AUD-04 (corrección post-revisión): cohorte real y estado observado de 1023V19656C5.

Comprueba las dos cifras que el revisor corrige:
 1) ¿en qué cohorte cae el ancla respecto de la ventana programada del viaje?
 2) ¿qué dice el dato observado sobre si el tren estaba parado?
"""
from __future__ import annotations
import sys
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import build_madrid_corridor_catalog, haversine_m
from packages.gtfs import build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds
from packages.movement.schedule import build_trip_schedule, service_seconds

MADRID = ZoneInfo("Europe/Madrid"); TH = MovementThresholds()
R = Path("data/hito-03/replay"); TARGET = "1023V19656C5"

topo = load_feed(R / "fomento_transit.zip", network_id="10")
cat = build_catalog(topo, gtfs_version="aud04")
corr = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
tr = {t.trip_id: t.route_id for t in topo.trips}

def cut(n):
    raw = RawVehiclePositionsFeed.model_validate_json((R/n/"vehicle_positions.json").read_bytes())
    return {o.source_trip_id: o for o in vehicle_positions_to_canonical(raw)}

prev, last = cut("1532"), cut("1533")
a, b = prev[TARGET], last[TARGET]
times = topo.stop_times_for_trip(TARGET)
cov = corr.coverage_for_stops(tr[TARGET], tuple(i.stop_id for i in times))
eng = MovementEngine(topo, cov.corridor, thresholds=TH)
sch = build_trip_schedule(topo, cov.corridor, TARGET)

sd = b.observed_at.astimezone(MADRID).date()
anchor_s = service_seconds(b.observed_at, sd)
first_s, last_s = sch.points[0].seconds, sch.points[-1].seconds

print("== 1) cohorte real del ancla ==")
print(f"  primera salida programada : {first_s:8.0f} s ({first_s/3600:05.2f} h)")
print(f"  ultima llegada programada : {last_s:8.0f} s ({last_s/3600:05.2f} h)")
print(f"  ancla (observed_at 1533)  : {anchor_s:8.0f} s ({anchor_s/3600:05.2f} h)")
cohorte = ("pre_salida" if anchor_s < first_s
           else "post_llegada" if anchor_s > last_s else "en_ventana")
print(f"  -> cohorte = {cohorte};  ancla - ultima_llegada = {anchor_s - last_s:+.0f} s")
print(f"  progreso del ancla {sch.directed_progress(eng.map_match(b).physical_arc_m):.2f} m "
      f"de {sch.points[-1].progress_m:.2f} m -> faltan "
      f"{sch.points[-1].progress_m - sch.directed_progress(eng.map_match(b).physical_arc_m):.1f} m")

print("\n== 2) que dice el dato observado sobre la parada ==")
for name, o in (("1532", a), ("1533", b)):
    m = eng.map_match(o)
    print(f"  corte {name}: observed_at={o.observed_at.isoformat()} "
          f"current_status={o.current_status!r} current_stop_id={o.current_stop_id!r}")
    print(f"           GPS=({o.latitude},{o.longitude}) "
          f"progreso dirigido={sch.directed_progress(m.physical_arc_m):.2f} m "
          f"dist_via={m.distance_from_track_m:.2f} m")
d_arc = (sch.directed_progress(eng.map_match(b).physical_arc_m)
         - sch.directed_progress(eng.map_match(a).physical_arc_m))
chord = haversine_m(a.latitude, a.longitude, b.latitude, b.longitude)
el = (b.observed_at - a.observed_at).total_seconds()
print(f"  entre los dos cortes: {el:.0f} s, arco dirigido {d_arc:+.2f} m, "
      f"cuerda {chord:.2f} m  -> {abs(d_arc)/el*3.6:.1f} km/h")
print("  => ninguna de las dos observaciones tiene current_status='STOPPED_AT':")
print(f"     1532={a.current_status!r}  1533={b.current_status!r}")
