"""AUD-04: el cambio de hora dentro de `_envelope`.

`_envelope` mezcla dos relojes: `service_seconds` (reloj de PARED del dia de
servicio) y `timedelta` (segundos REALES). En los dos dias de cambio de hora de
Europe/Madrid las dos escalas dejan de coincidir, asi que se mide:

 1) el histograma real de horas de `stop_times` del ZIP oficial, para saber si
    la franja afectada tiene trenes de verdad (reachability);
 2) que publica la envolvente con un ancla a caballo del salto, usando el
    horario real de un viaje real.
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.geo import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope
from packages.movement.schedule import build_trip_schedule, service_day_instant, service_seconds

MADRID = ZoneInfo("Europe/Madrid")
REPLAY = Path("data/hito-03/replay")
FIXTURES = Path("tests/fixtures")
TH = MovementThresholds()


def main() -> None:
    topo = load_feed(REPLAY / "fomento_transit.zip", network_id="10")
    hours = Counter()
    total = 0
    for trip in topo.trips:
        for item in topo.stop_times_for_trip(trip.trip_id):
            for value in (item.arrival_time, item.departure_time):
                if not value:
                    continue
                hours[int(value.split(":")[0])] += 1
                total += 1
    print(f"== histograma de horas de stop_times (Madrid, nucleo 10) — {total} valores ==")
    for h in sorted(hours):
        print(f"  {h:02d}:xx  {hours[h]:7d}")
    print()

    print("== 1) ida y vuelta service_seconds / service_day_instant (DEC-039) ==")
    for d in (date(2026, 3, 29), date(2026, 10, 25), date(2026, 11, 20)):
        bad = 0
        for s in range(0, 108000, 60):
            inst = service_day_instant(d, s)
            back = service_seconds(inst, d)
            if abs(back - s) > 0.5:
                bad += 1
        print(f"  {d}: segundos que no cierran la ida y vuelta: {bad} de 1800")
    print()

    print("== 2) escala de pared vs escala real dentro de _envelope ==")
    # Viaje real cualquiera con corredor validado, para tener un horario real.
    cat = build_catalog(topo, gtfs_version="aud04")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    chosen = None
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if not times:
            continue
        cov = corridors.coverage_for_stops(trip_route[trip.trip_id],
                                           tuple(t.stop_id for t in times))
        if cov.can_map_match and cov.corridor is not None:
            chosen = (trip.trip_id, cov)
            break
    trip_id, cov = chosen
    schedule = build_trip_schedule(topo, cov.corridor, trip_id)
    print(f"  viaje usado: {trip_id}; horario real de "
          f"{schedule.points[0].seconds/3600:.2f}h a {schedule.points[-1].seconds/3600:.2f}h; "
          f"{schedule.points[-1].progress_m:.0f} m de recorrido")

    for label, service_date, utc_anchor in (
        ("dia normal        ", date(2026, 11, 20), datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc)),
        ("atraso 2026-10-25 ", date(2026, 10, 25), datetime(2026, 10, 25, 0, 59, 0, tzinfo=timezone.utc)),
        ("adelanto 2026-03-29", date(2026, 3, 29), datetime(2026, 3, 29, 0, 59, 0, tzinfo=timezone.utc)),
    ):
        horizon_end = utc_anchor + timedelta(seconds=190)
        a_s = service_seconds(utc_anchor, service_date)
        h_s = service_seconds(horizon_end, service_date)
        print(f"\n  {label}  ancla UTC {utc_anchor.isoformat()} "
              f"(local {utc_anchor.astimezone(MADRID).strftime('%H:%M:%S %Z')})")
        print(f"    segundos reales entre ancla y fin de horizonte: 190")
        print(f"    segundos de PARED que mide service_seconds:     {h_s - a_s:.0f}")
        print(f"    (service_seconds ancla={a_s:.0f}  horizonte={h_s:.0f})")
        # progreso que el horario autoriza en esa ventana, con el ancla en el inicio
        anchor_progress = schedule.points[0].progress_m
        env = _envelope(schedule=schedule, service_date=service_date, anchor_at=utc_anchor,
                        anchor_progress_m=anchor_progress, horizon_end=horizon_end,
                        max_speed_mps=TH.max_estimated_speed_kmh / 3.6)
        print(f"    envolvente: speed={env.speed_mps:.2f} m/s ({env.speed_mps*3.6:.1f} km/h)  "
              f"max_progress={env.max_progress_m - anchor_progress:+.1f} m sobre el ancla")


if __name__ == "__main__":
    main()
