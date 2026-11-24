"""AUD-04: anulaciones (DEC-042) frente a la capa de posicion/movimiento.

Pregunta: una circulacion que Renfe declara CANCELED en `trip_updates` y que
sigue publicando `vehicle_position`, ¿recibe envolvente y se dibuja en marcha?
"""
from __future__ import annotations
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.normalize import trip_updates_to_canonical, vehicle_positions_to_canonical
from packages.contracts.raw import RawTripUpdatesFeed, RawVehiclePositionsFeed
from packages.geo import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds
from packages.movement.rendering import render_from_movement
from packages.movement.schedule import build_trip_schedule

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
TH = MovementThresholds()

topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
cat = build_catalog(topo, gtfs_version="aud04")
corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
trip_route = {t.trip_id: t.route_id for t in topo.trips}

for cut in ("1532", "1533"):
    tu_raw = RawTripUpdatesFeed.model_validate_json((REPLAY / cut / "trip_updates.json").read_bytes())
    vp_raw = RawVehiclePositionsFeed.model_validate_json((REPLAY / cut / "vehicle_positions.json").read_bytes())
    tus = {t.source_trip_id: t for t in trip_updates_to_canonical(tu_raw)}
    vps = {v.source_trip_id: v for v in vehicle_positions_to_canonical(vp_raw)}
    rels = Counter(t.schedule_relationship for t in tus.values())
    print(f"=== corte {cut}: {len(tus)} trip_updates, {len(vps)} vehicle_positions ===")
    print(f"  schedule_relationship: {dict(rels)}")
    canceled = [t for t in tus.values() if t.schedule_relationship == "CANCELED"]
    print(f"  CANCELED: {len(canceled)}")
    both = [t for t in canceled if t.source_trip_id in vps]
    print(f"  CANCELED **con** vehicle_position en el mismo corte: {len(both)}")
    for t in both:
        v = vps[t.source_trip_id]
        print(f"    {t.source_trip_id} vehicle={v.source_vehicle_id} "
              f"lat={v.latitude} lon={v.longitude} observed_at={v.observed_at.isoformat()}")
        times = topo.stop_times_for_trip(t.source_trip_id)
        if not times:
            print("      (sin stop_times en el GTFS cargado)")
            continue
        cov = corridors.coverage_for_stops(trip_route.get(t.source_trip_id),
                                           tuple(i.stop_id for i in times))
        if not cov.can_map_match or cov.corridor is None:
            print(f"      corredor no validado ({cov.geometry_status if hasattr(cov,'geometry_status') else 'pending'}): "
                  f"se publicaria raw etiquetado")
            continue
        engine = MovementEngine(topo, cov.corridor, thresholds=TH)
        schedule = build_trip_schedule(topo, cov.corridor, t.source_trip_id)
        now = v.observed_at + timedelta(seconds=10)
        sd = now.astimezone(MADRID).date()
        mv = engine.position(trip_id=t.source_trip_id, service_date=sd, calculated_at=now, latest=v)
        rd = render_from_movement(mv, schedule=schedule, corridor=cov.corridor, service_date=sd,
                                  display_at=now, pattern_id=cov.identity.pattern_id,
                                  geometry_version=cov.geometry_version, thresholds=TH)
        env = rd.progress_envelope
        print(f"      CORREDOR VALIDADO -> rendering_method={rd.rendering_method.value} "
              f"speed_mps={env.speed_mps if env else None}")
    print()
