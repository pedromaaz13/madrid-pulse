"""AUD-04: barrido con cohortes separadas para no confundirse con AUD01-P0-001.

Cohorte EN VENTANA: el instante del ancla cae entre la primera salida y la
ultima llegada programadas del viaje (el tren esta de verdad en ruta).
Cohorte PRE-SALIDA: el ancla es anterior a la primera salida programada
(el caso ya documentado por AUD01-P0-001; se reporta aparte).
"""
from __future__ import annotations

import statistics
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
from packages.movement.rendering import render_from_movement
from packages.movement.schedule import build_trip_schedule, service_seconds

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
FIXTURES = Path("tests/fixtures")
TH = MovementThresholds()


def load_cut(name: str):
    raw = RawVehiclePositionsFeed.model_validate_json(
        (REPLAY / name / "vehicle_positions.json").read_bytes()
    )
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud04")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)

    prev_by_vehicle = load_cut("1532")
    latest_by_vehicle = load_cut("1533")

    cohorts = {"en_ventana": [], "pre_salida": [], "post_llegada": []}

    for vid, latest in sorted(latest_by_vehicle.items()):
        trip_id = latest.source_trip_id
        route_id = trip_route.get(trip_id)
        stop_ids = stops_by_trip.get(trip_id)
        if route_id is None or stop_ids is None:
            continue
        coverage = corridors.coverage_for_stops(route_id, stop_ids)
        if not coverage.can_map_match or coverage.corridor is None:
            continue
        engine = MovementEngine(topo, coverage.corridor, thresholds=TH)
        schedule = build_trip_schedule(topo, coverage.corridor, trip_id)
        previous = prev_by_vehicle.get(vid)
        if previous is not None and previous.source_trip_id != trip_id:
            previous = None

        anchor_at = latest.observed_at
        service_date = anchor_at.astimezone(MADRID).date()
        anchor_s = service_seconds(anchor_at, service_date)
        first_s, last_s = schedule.points[0].seconds, schedule.points[-1].seconds

        def render_at(age_s: float):
            now = anchor_at + timedelta(seconds=age_s)
            mv = engine.position(trip_id=trip_id, service_date=service_date,
                                 calculated_at=now, latest=latest, previous=previous)
            rd = render_from_movement(
                mv, schedule=schedule, corridor=coverage.corridor,
                service_date=service_date, display_at=now,
                pattern_id=coverage.identity.pattern_id,
                geometry_version=coverage.geometry_version, thresholds=TH)
            return mv, rd

        mv0, rd0 = render_at(10.0)
        env = rd0.progress_envelope
        mv_a, rd_a = render_at(TH.stale_after_s - 1.0)
        mv_b, rd_b = render_at(TH.stale_after_s + 1.0)
        rewind = (rd_a.progress_m or 0.0) - (rd_b.progress_m or 0.0)

        # divergencia motor/envolvente SOLO donde el motor ya estima (edad > 60 s)
        worst = (0, 0.0, 0.0, 0.0)
        if env is not None:
            for age in (61, 80, 100, 120, 150, 179):
                mv_t, _ = render_at(float(age))
                client = env.progress_at(anchor_at + timedelta(seconds=age))
                d = client - mv_t.progress_m
                if abs(d) > abs(worst[1]):
                    worst = (age, d, client, mv_t.progress_m)

        # esperas programadas dentro del horizonte
        flats_in = []
        nearest_flat = None
        if env is not None:
            offset = anchor_s - schedule.seconds_at_progress(env.progress_m_at_reference)
            end_s = service_seconds(anchor_at + timedelta(seconds=TH.stale_after_s),
                                    service_date) - offset
            start_s = anchor_s - offset
            for left, right in zip(schedule.points, schedule.points[1:]):
                if abs(right.progress_m - left.progress_m) <= 1.0 and right.seconds > left.seconds:
                    gap = abs(left.progress_m - env.progress_m_at_reference)
                    if nearest_flat is None or gap < nearest_flat:
                        nearest_flat = gap
                    if start_s < left.seconds < end_s:
                        flats_in.append(right.seconds - left.seconds)

        row = dict(vid=vid, trip=trip_id, anchor_s=anchor_s, first_s=first_s, last_s=last_s,
                   anchor_progress=env.progress_m_at_reference if env else None,
                   speed=env.speed_mps if env else None,
                   dwell=env.dwell_until if env else None,
                   method0=rd0.rendering_method.value, mode0=mv0.position_mode.value,
                   rewind=rewind, p179=rd_a.progress_m, p181=rd_b.progress_m,
                   worst=worst, flats_in=flats_in, nearest_flat=nearest_flat,
                   total_m=schedule.points[-1].progress_m)
        key = ("pre_salida" if anchor_s < first_s
               else "post_llegada" if anchor_s > last_s else "en_ventana")
        cohorts[key].append(row)

    for name, rows in cohorts.items():
        print(f"=== cohorte {name}: {len(rows)} circulaciones ===")
        if not rows:
            print()
            continue
        rw = [r["rewind"] for r in rows]
        print(f"  A) retroceso al cruzar stale_after_s: n>1m={sum(1 for v in rw if v>1)}  "
              f"min={min(rw):.1f} p50={statistics.median(rw):.1f} max={max(rw):.1f} m")
        dv = [abs(r["worst"][1]) for r in rows]
        print(f"  B) |envolvente - motor| con edad 61-179 s: max={max(dv):.1f} "
              f"p50={statistics.median(dv):.1f} m")
        print(f"  C) dwell_until poblado: {sum(1 for r in rows if r['dwell'] is not None)}; "
              f"con espera programada dentro del horizonte: "
              f"{sum(1 for r in rows if r['flats_in'])}")
        nf = [r["nearest_flat"] for r in rows if r["nearest_flat"] is not None]
        if nf:
            print(f"     distancia del ancla al tramo plano mas cercano: "
                  f"min={min(nf):.1f} p50={statistics.median(nf):.1f} m "
                  f"(tolerancia de dwell_end_seconds = 1,0 m)")
        sp = [r["speed"] for r in rows if r["speed"] is not None]
        if sp:
            print(f"     speed_mps: min={min(sp):.2f} p50={statistics.median(sp):.2f} "
                  f"max={max(sp):.2f}")
        print("  detalle (peores por retroceso):")
        for r in sorted(rows, key=lambda x: -x["rewind"])[:6]:
            w = r["worst"]
            print(f"    {r['vid']} {r['trip']} ancla={r['anchor_progress']:.0f} m de "
                  f"{r['total_m']:.0f} m  v={r['speed']:.2f} m/s  "
                  f"179s={r['p179']:.0f} m -> 181s={r['p181']:.0f} m ({r['rewind']:+.0f} m)  "
                  f"| B a {w[0]} s: cliente {w[2]:.0f} m vs motor {w[3]:.0f} m ({w[1]:+.0f} m)")
        print()


if __name__ == "__main__":
    main()
