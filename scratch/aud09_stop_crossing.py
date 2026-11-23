"""AUD-09: cuántas circulaciones atraviesan una parada dentro del horizonte sin retenerse.

Pregunta de severidad (AUD04-P0-001 vs P1): no basta con el único caso de
Fuenlabrada. Sobre las 44 circulaciones con cadena raw -> matched -> rendered del
corte 1533, mide, con el código de producción y el mismo reloj que la evidencia
MP-019 (ancla + 10 s, horizonte stale_after_s = 180 s):

- cuántas envolventes cruzan el progreso de al menos una parada (cualquier
  parada del horario) entre el ancla y el final del horizonte;
- cuántas cruzan una parada con espera DECLARADA en el horario (tramo plano);
- cuántas publican dwell_until;
- cota superior del error de posición si el tren honra la espera declarada:
  speed_mps * min(espera, tiempo restante del horizonte al llegar a la parada).

Separado por cohortes (en_ventana / pre_salida / post_llegada) como AUD-04.
No escribe en ninguna base de datos ni usa red.
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
CALC_DELAY_S = 10.0


def load_cut(name: str) -> dict:
    raw = RawVehiclePositionsFeed.model_validate_json(
        (REPLAY / name / "vehicle_positions.json").read_bytes()
    )
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}


def stops_from_schedule(schedule) -> list[tuple[float, float]]:
    """(progreso de la parada, espera declarada en s) agrupando puntos a <= 1 m."""
    stops: list[tuple[float, float]] = []
    pts = schedule.points
    i = 0
    while i < len(pts):
        j = i
        while j + 1 < len(pts) and abs(pts[j + 1].progress_m - pts[i].progress_m) <= 1.0:
            j += 1
        stops.append((pts[i].progress_m, pts[j].seconds - pts[i].seconds))
        i = j + 1
    return stops


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="aud09")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)

    prev_by_vehicle = load_cut("1532")
    latest_by_vehicle = load_cut("1533")
    rows = []
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
        now = anchor_at + timedelta(seconds=CALC_DELAY_S)
        mv = engine.position(trip_id=trip_id, service_date=service_date,
                             calculated_at=now, latest=latest, previous=previous)
        rd = render_from_movement(
            mv, schedule=schedule, corridor=coverage.corridor, service_date=service_date,
            display_at=now, pattern_id=coverage.identity.pattern_id,
            geometry_version=coverage.geometry_version, thresholds=TH)
        env = rd.progress_envelope
        cohort = ("pre_salida" if anchor_s < first_s
                  else "post_llegada" if anchor_s > last_s else "en_ventana")
        if env is None:
            rows.append(dict(vid=vid, cohort=cohort, env=False))
            continue
        horizon_end = now + timedelta(seconds=TH.stale_after_s)
        p0 = env.progress_m_at_reference
        p1 = env.progress_at(horizon_end)
        crossed_any = []
        crossed_dwell = []
        err_bound = 0.0
        for prog, dwell in stops_from_schedule(schedule):
            if p0 + 1.0 < prog <= p1:
                crossed_any.append(prog)
                if dwell > 0:
                    crossed_dwell.append((prog, dwell))
                    if env.speed_mps > 0:
                        t_reach = (prog - p0) / env.speed_mps
                        remaining = (horizon_end - anchor_at).total_seconds() - t_reach
                        err_bound = max(err_bound, env.speed_mps * max(0.0, min(dwell, remaining)))
        if crossed_dwell:
            print(f"   [detalle] {trip_id} {cohort} speed={env.speed_mps:.2f} p0={p0:.0f} paradas_espera={[(round(p), d) for p, d in crossed_dwell]} cota={err_bound:.0f} m")
        status = getattr(latest.current_status, "value", latest.current_status)
        same_gps = (previous is not None and previous.latitude == latest.latitude
                    and previous.longitude == latest.longitude)
        rows.append(dict(vid=vid, trip=trip_id, cohort=cohort, env=True, speed=env.speed_mps,
                         advance=p1 - p0, n_any=len(crossed_any), n_dwell=len(crossed_dwell),
                         dwell_until=env.dwell_until is not None, err_bound=err_bound,
                         dwells=[d for _, d in crossed_dwell], status=str(status),
                         same_gps=same_gps, first_stop=stop_ids[0],
                         stop_id=latest.current_stop_id))

    # Clase que el operador declara detenida y la envolvente pone en marcha.
    stopped = [r for r in rows if r["env"] and "STOPPED_AT" in r["status"]]
    stopped_moving = [r for r in stopped if r["speed"] > 0]
    at_origin = [r for r in stopped_moving if r["stop_id"] == r["first_stop"]]
    frozen = [r for r in stopped_moving if r["same_gps"]]
    print("== operador STOPPED_AT en el corte 1533 ==")
    print(f"   con envolvente: {len(stopped)}; con speed_mps > 0: {len(stopped_moving)}; "
          f"de ellas en la parada de ORIGEN: {len(at_origin)}; con GPS identico en 1532 y 1533: "
          f"{len(frozen)}")
    for r in stopped_moving:
        print(f"   [stopped] {r['trip']} cohorte={r['cohort']} stop={r['stop_id']} "
              f"origen={r['stop_id'] == r['first_stop']} gps_identico={r['same_gps']} "
              f"speed={r['speed']:.2f} m/s avance_publicado={r['advance']:.0f} m")
    by_cohort: dict[str, int] = {}
    for r in at_origin:
        by_cohort[r["cohort"]] = by_cohort.get(r["cohort"], 0) + 1
    print(f"   en origen con avance, por cohorte AUD-04: {by_cohort}")
    print(f"circulaciones con cadena completa: {len(rows)}  (horizonte {TH.stale_after_s:.0f} s "
          f"configurados desde calculated_at = ancla + {CALC_DELAY_S:.0f} s)")
    for cohort in ("en_ventana", "pre_salida", "post_llegada", None):
        sub = [r for r in rows if r["env"] and (cohort is None or r["cohort"] == cohort)]
        label = cohort or "TOTAL"
        if not sub:
            print(f"== {label}: 0")
            continue
        any_ = [r for r in sub if r["n_any"] > 0]
        dw = [r for r in sub if r["n_dwell"] > 0]
        held = [r for r in sub if r["dwell_until"]]
        adv = [r["advance"] for r in sub]
        print(f"== {label}: n={len(sub)}")
        print(f"   avance publicado en el horizonte: p50={statistics.median(adv):.0f} m "
              f"max={max(adv):.0f} m")
        print(f"   cruzan >=1 parada sin retenerse: {len(any_)}/{len(sub)}  "
              f"(paradas cruzadas: total={sum(r['n_any'] for r in sub)})")
        print(f"   cruzan >=1 parada con espera DECLARADA: {len(dw)}/{len(sub)}  "
              f"esperas cruzadas (s): {sorted(d for r in dw for d in r['dwells'])}")
        print(f"   dwell_until publicado: {len(held)}/{len(sub)}")
        if dw:
            eb = [r["err_bound"] for r in dw]
            print(f"   cota de error si el tren honra la espera declarada: "
                  f"p50={statistics.median(eb):.0f} m max={max(eb):.0f} m  "
                  f"(trips: {', '.join(r['trip'] for r in dw)})")


if __name__ == "__main__":
    main()
