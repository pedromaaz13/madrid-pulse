"""AUD-09 (v2, 2026-11-24): estado de parada frente a la envolvente PUBLICADA por producción.

Corrección respecto a la v1 (commit 3014347), pedida por la revisión de Codex
`gpt-5.6-sol` · high: la v1 evaluaba las travesías hasta `ancla + 190 s`
(`calculated_at + stale_after_s`), pero `render_from_movement` limita la envolvente
de un ancla observada a `valid_until = ancla + stale_after_s` (180 s;
`packages/movement/rendering.py:279,341-346`). El horizonte de la travesía es ahora
exactamente `rendered.valid_until`, y una parada solo cuenta como atravesada si el
progreso publicado la supera ESTRICTAMENTE antes de ese límite (`p0 + 1 < prog < p1`).
Para transparencia se imprime también el recuento con la desigualdad no estricta
(`prog <= p1`), que reproduce el sesgo de la v1.

Mide sobre las 44 circulaciones del corte 1533 con cadena raw -> matched -> rendered
(reloj de la evidencia MP-019: `calculated_at = ancla + 10 s`):

1. estado declarado por el operador (`current_status`) frente a `speed_mps` publicado;
2. cuántas envolventes atraviesan al menos una parada antes de `valid_until`;
3. cuántas atraviesan una parada con espera DECLARADA en el horario;
4. cuántas publican `dwell_until`.

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
    horizons = set()
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
        status = str(getattr(latest.current_status, "value", latest.current_status))
        same_gps = (previous is not None and previous.latitude == latest.latitude
                    and previous.longitude == latest.longitude)
        base = dict(vid=vid, trip=trip_id, cohort=cohort, status=status, same_gps=same_gps,
                    first_stop=stop_ids[0], stop_id=latest.current_stop_id)
        if env is None or rd.valid_until is None:
            rows.append(dict(base, env=False))
            continue
        # Horizonte REAL de producción: el que publica el propio snapshot.
        horizon_end = rd.valid_until
        horizons.add((horizon_end - anchor_at).total_seconds())
        p0 = env.progress_m_at_reference
        p1 = env.progress_at(horizon_end)
        strict_any, strict_dwell, loose_any, loose_dwell = [], [], [], []
        for prog, dwell in stops_from_schedule(schedule):
            if p0 + 1.0 < prog <= p1:
                loose_any.append(prog)
                if dwell > 0:
                    loose_dwell.append((prog, dwell))
            if p0 + 1.0 < prog < p1:
                strict_any.append(prog)
                if dwell > 0:
                    strict_dwell.append((prog, dwell))
        rows.append(dict(base, env=True, speed=env.speed_mps, advance=p1 - p0,
                         n_any=len(strict_any), n_dwell=len(strict_dwell),
                         n_any_loose=len(loose_any), n_dwell_loose=len(loose_dwell),
                         dwell_until=env.dwell_until is not None,
                         dwells=[d for _, d in strict_dwell],
                         edge=[(round(p, 1), round(p1, 1)) for p, _ in loose_dwell
                               if (p, _) not in strict_dwell]))

    print(f"horizontes de producción observados desde el ancla (s): {sorted(horizons)}")
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
    sp = [r["speed"] for r in stopped_moving]
    adv = [r["advance"] for r in stopped_moving]
    print(f"   speed_mps publicado: {min(sp):.2f}-{max(sp):.2f} m/s "
          f"({min(sp)*3.6:.1f}-{max(sp)*3.6:.1f} km/h); avance publicado en el horizonte: "
          f"{min(adv):.0f}-{max(adv):.0f} m")

    print(f"\ncirculaciones con cadena completa: {len(rows)}  (horizonte = rendered.valid_until; "
          f"calculated_at = ancla + {CALC_DELAY_S:.0f} s)")
    for cohort in ("en_ventana", "pre_salida", "post_llegada", None):
        sub = [r for r in rows if r["env"] and (cohort is None or r["cohort"] == cohort)]
        label = cohort or "TOTAL"
        if not sub:
            print(f"== {label}: 0")
            continue
        adv = [r["advance"] for r in sub]
        print(f"== {label}: n={len(sub)}")
        print(f"   avance publicado en el horizonte: p50={statistics.median(adv):.0f} m "
              f"max={max(adv):.0f} m")
        print(f"   atraviesan >=1 parada (estricto, antes de valid_until): "
              f"{sum(1 for r in sub if r['n_any'] > 0)}/{len(sub)}  "
              f"(paradas: {sum(r['n_any'] for r in sub)})")
        print(f"   atraviesan >=1 parada con espera DECLARADA (estricto): "
              f"{sum(1 for r in sub if r['n_dwell'] > 0)}/{len(sub)}")
        print(f"   [no estricto, sesgo de la v1] >=1 parada: "
              f"{sum(1 for r in sub if r['n_any_loose'] > 0)}/{len(sub)}; "
              f"con espera declarada: {sum(1 for r in sub if r['n_dwell_loose'] > 0)}/{len(sub)}")
        print(f"   dwell_until publicado: {sum(1 for r in sub if r['dwell_until'])}/{len(sub)}")
    edge = [(r["trip"], r["edge"]) for r in rows if r["env"] and r["edge"]]
    print(f"\nparadas con espera declarada alcanzadas EXACTAMENTE en el límite del horizonte "
          f"(prog == p1): {edge}")


if __name__ == "__main__":
    main()
