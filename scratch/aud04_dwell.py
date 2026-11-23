"""AUD-04: el caso real 1023V19656C5 — tren sobre una parada con espera declarada.

Mide el hueco real entre el progreso del ancla map-matcheada y el progreso del
tramo plano del horario, y que devuelve `dwell_end_seconds` con la tolerancia
fijada (1,0 m) frente a tolerancias del orden del error de map-matching medido.
"""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope, render_from_movement
from packages.movement.schedule import build_trip_schedule, service_seconds

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
FIXTURES = Path("tests/fixtures")
TH = MovementThresholds()
TARGET = "1023V19656C5"


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud04")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}

    raw = RawVehiclePositionsFeed.model_validate_json(
        (REPLAY / "1533" / "vehicle_positions.json").read_bytes())
    obs = [o for o in vehicle_positions_to_canonical(raw) if o.source_trip_id == TARGET]
    latest = obs[0]
    print(f"observacion real: vehicle_id={latest.source_vehicle_id} trip={latest.source_trip_id}")
    print(f"  GPS bruto publicado por Renfe: lat={latest.latitude!r} lon={latest.longitude!r}")
    print(f"  observed_at={latest.observed_at.isoformat()}  current_stop_id={latest.current_stop_id!r}"
          f"  current_status={latest.current_status!r}")

    times = topo.stop_times_for_trip(TARGET)
    stop_ids = tuple(t.stop_id for t in times)
    coverage = corridors.coverage_for_stops(trip_route[TARGET], stop_ids)
    corridor = coverage.corridor
    engine = MovementEngine(topo, corridor, thresholds=TH)
    schedule = build_trip_schedule(topo, corridor, TARGET)
    em = engine.map_match(latest)
    anchor_progress = schedule.directed_progress(em.physical_arc_m)
    print(f"  map-match: distancia GPS->geometria = {em.distance_from_track_m:.2f} m; "
          f"progreso dirigido del ancla = {anchor_progress:.2f} m")

    stops = {s.stop_id: s for s in topo.stops}
    print("\nparadas con espera declarada (arrival != departure) y su progreso proyectado:")
    flats = []
    for left, right in zip(schedule.points, schedule.points[1:]):
        if abs(right.progress_m - left.progress_m) <= 1.0 and right.seconds > left.seconds:
            flats.append((left, right))
    for left, right in flats:
        gap = left.progress_m - anchor_progress
        mark = "  <== la mas cercana al ancla" if abs(gap) < 50 else ""
        print(f"  progreso {left.progress_m:9.2f} m  espera {right.seconds-left.seconds:4.0f} s "
              f"({left.seconds/3600:05.2f}h)  hueco al ancla {gap:+10.2f} m{mark}")

    nearest = min(flats, key=lambda p: abs(p[0].progress_m - anchor_progress))
    gap = abs(nearest[0].progress_m - anchor_progress)
    # que estacion es
    best = None
    for item in times:
        stop = stops[item.stop_id]
        _, arc = corridor.project_station(stop.latitude, stop.longitude)
        d = abs(schedule.directed_progress(arc) - nearest[0].progress_m)
        if best is None or d < best[1]:
            best = (stop, d)
    print(f"\nparada mas cercana al ancla: {best[0].name} ({best[0].stop_id}); "
          f"hueco ancla->tramo plano = {gap:.2f} m")
    print(f"tolerancia fijada en dwell_end_seconds: 1,0 m")
    for tol in (1.0, 2.0, 5.0, 6.0, 10.0, 25.0):
        end = schedule.dwell_end_seconds(anchor_progress, tolerance_m=tol)
        print(f"  dwell_end_seconds(tolerance_m={tol:5.1f}) -> {end}")

    print("\nenvolvente publicada con la tolerancia real (1,0 m):")
    anchor_at = latest.observed_at
    service_date = anchor_at.astimezone(MADRID).date()
    now = anchor_at + timedelta(seconds=10)
    env = _envelope(schedule=schedule, service_date=service_date, anchor_at=anchor_at,
                    anchor_progress_m=anchor_progress,
                    horizon_end=now + timedelta(seconds=TH.stale_after_s),
                    max_speed_mps=TH.max_estimated_speed_kmh / 3.6)
    print(f"  speed_mps={env.speed_mps:.2f} ({env.speed_mps*3.6:.1f} km/h)  "
          f"dwell_until={env.dwell_until}  max_progress_m={env.max_progress_m:.1f}")
    print(f"  avance dibujado en 60 s: "
          f"{env.progress_at(anchor_at+timedelta(seconds=60))-anchor_progress:.1f} m")
    print(f"  avance dibujado en 190 s: "
          f"{env.progress_at(anchor_at+timedelta(seconds=190))-anchor_progress:.1f} m")

    mv = engine.position(trip_id=TARGET, service_date=service_date, calculated_at=now,
                         latest=latest)
    rd = render_from_movement(mv, schedule=schedule, corridor=corridor,
                              service_date=service_date, display_at=now,
                              pattern_id=coverage.identity.pattern_id,
                              geometry_version=coverage.geometry_version, thresholds=TH)
    print(f"\n  rendering_method={rd.rendering_method.value}  reason={rd.reason!r}")

    anchor_s = service_seconds(anchor_at, service_date)
    sched_s = schedule.seconds_at_progress(anchor_progress)
    print(f"\n  anchor_s={anchor_s:.0f} s de dia de servicio; horario en ese progreso="
          f"{sched_s:.0f} s; temporal_offset_s={anchor_s-sched_s:+.0f} s")




def counterfactual() -> None:
    """Contrafactual: la misma envolvente con el ancla exactamente en el tramo plano,
    y con la tolerancia que el error de map-matching medido exigiria."""
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud04")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    times = topo.stop_times_for_trip(TARGET)
    coverage = corridors.coverage_for_stops(trip_route[TARGET], tuple(t.stop_id for t in times))
    schedule = build_trip_schedule(topo, coverage.corridor, TARGET)
    raw = RawVehiclePositionsFeed.model_validate_json(
        (REPLAY / "1533" / "vehicle_positions.json").read_bytes())
    latest = [o for o in vehicle_positions_to_canonical(raw) if o.source_trip_id == TARGET][0]
    anchor_at = latest.observed_at
    service_date = anchor_at.astimezone(MADRID).date()
    flat_progress = 41193.35
    print("\n--- contrafactual A: ancla exactamente en el tramo plano (41193.35 m) ---")
    print(f"  dwell_end_seconds(41193.35, tol=1.0) -> {schedule.dwell_end_seconds(flat_progress)}")
    print(f"  seconds_at_progress(41193.35) -> {schedule.seconds_at_progress(flat_progress):.0f}")
    env = _envelope(schedule=schedule, service_date=service_date, anchor_at=anchor_at,
                    anchor_progress_m=flat_progress,
                    horizon_end=anchor_at + timedelta(seconds=190),
                    max_speed_mps=TH.max_estimated_speed_kmh / 3.6)
    print(f"  envolvente: speed={env.speed_mps:.2f} m/s dwell_until={env.dwell_until}")
    print(f"  avance a 30 s: {env.progress_at(anchor_at+timedelta(seconds=30))-flat_progress:.1f} m")
    print(f"  avance a 90 s: {env.progress_at(anchor_at+timedelta(seconds=90))-flat_progress:.1f} m")

    print("\n--- contrafactual B: el ancla real (41198.73 m) con la espera SI detectada ---")
    anchor_progress = 41198.73
    anchor_s = service_seconds(anchor_at, service_date)
    offset = anchor_s - schedule.seconds_at_progress(anchor_progress)
    dwell_end_s = schedule.dwell_end_seconds(anchor_progress, tolerance_m=6.0)
    candidate = anchor_at + timedelta(seconds=dwell_end_s + offset - anchor_s)
    print(f"  dwell_end_seconds(tol=6.0) = {dwell_end_s:.0f}; temporal_offset_s = {offset:+.0f}")
    print(f"  candidate = {candidate.isoformat()} ; anchor_at = {anchor_at.isoformat()}")
    print(f"  anchor_at < candidate ? {anchor_at < candidate}  -> dwell_until "
          f"{'poblado' if anchor_at < candidate else 'DESCARTADO igualmente'}")


if __name__ == "__main__":
    main()
    counterfactual()
