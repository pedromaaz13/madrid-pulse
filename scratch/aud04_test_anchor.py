"""AUD-04 (corrección post-revisión 3): ¿dónde cae, dentro de la ventana estrecha,
el ancla que construye `test_scheduled_dwell_holds_the_train_at_the_anchor`?

Reproduce literalmente la construcción del test (misma fixture, mismo trip, misma
generación de lat/lon con `point_at_arc_length`) y mide el offset del progreso
map-matcheado resultante respecto al tramo plano, para situarlo en la ventana
[-0,999, 0,000] m medida en `scratch/aud04_dwell_window.py`.
"""
from __future__ import annotations
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.canonical import VehiclePositionObservation
from packages.geo import build_corridor, load_relation_geometry_json, point_at_arc_length
from packages.gtfs import load_feed
from packages.movement import MovementEngine
from packages.movement.schedule import build_trip_schedule

ROOT = Path(".")
GTFS_FIXTURE = ROOT / "tests" / "fixtures" / "gtfs_c5_real"
OSM_FIXTURE = ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"
SERVICE_DATE = __import__("datetime").date(2026, 11, 19)
MADRID = ZoneInfo("Europe/Madrid")
TRIP = "1022J19502C5"

topology = load_feed(GTFS_FIXTURE, network_id="10", short_name="C5")
corridor = build_corridor(load_relation_geometry_json(OSM_FIXTURE))
engine = MovementEngine(topology, corridor)
schedule = build_trip_schedule(topology, corridor, TRIP)
polyline = list(corridor.segments[0])

dwell_index = next(
    i for i, (l, r) in enumerate(zip(schedule.points, schedule.points[1:]))
    if abs(r.progress_m - l.progress_m) < 1.0 and r.seconds > l.seconds
)
point = schedule.points[dwell_index]
flat = point.progress_m
print(f"fixture del test: {GTFS_FIXTURE}  trip={TRIP}")
print(f"dwell_index={dwell_index}  tramo plano en progreso {flat:.6f} m "
      f"(espera {schedule.points[dwell_index+1].seconds - point.seconds:.0f} s)")

# construcción EXACTA del test: lat/lon generados sobre la propia geometría
lat, lon = point_at_arc_length(polyline, schedule.physical_arc(flat))
midnight = datetime.combine(SERVICE_DATE, time.min, tzinfo=MADRID).astimezone(timezone.utc)
anchor_at = midnight + timedelta(seconds=point.seconds)
obs = VehiclePositionObservation(
    source_vehicle_id="rendering-test", source_trip_id=TRIP, observed_at=anchor_at,
    latitude=lat, longitude=lon,
    raw_vehicle_label="synthetic deterministic rendering test", payload_hash="a" * 64,
)
m = engine.map_match(obs)
got = schedule.directed_progress(m.physical_arc_m)
print(f"\nlat/lon generados sobre la geometria: ({lat!r}, {lon!r})")
print(f"progreso tras el map-match de ida y vuelta: {got:.6f} m")
print(f"offset respecto al tramo plano: {got - flat:+.6f} m")
print(f"distancia GPS->via del ancla del test: {m.distance_from_track_m:.6f} m")
print(f"\ndwell_end_seconds(progreso del test) -> {schedule.dwell_end_seconds(got)}")
print("ventana efectiva medida (aud04_dwell_window.py): [-0,999, 0,000] m")
inside = -0.999 <= (got - flat) <= 0.0
print(f"=> el ancla del test cae {'DENTRO' if inside else 'FUERA'} de la ventana, "
      f"en su borde superior inclusivo (offset {got - flat:+.6f} m)")
print(f"   el ancla real del corte 1533 cayo a +5,38 m: {5.38:.2f} m fuera")
