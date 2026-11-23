"""AUD-01: ¿qué envolvente publica el contrato para un tren observado ANTES de su salida?

Reproduce, sin PostgreSQL, exactamente la cadena que usa apps/api/snapshot.py:
coverage_for_trip -> match_position (GPS real del corte 1533) -> build_trip_schedule
-> packages.movement.rendering._envelope.

Ojo con el rótulo del horizonte: `stale_after_s` vale 180 s (valor CONFIGURADO), pero
`horizon_end = calculated_at + stale_after_s` y `calculated_at = ancla + 10 s` (el mismo
reloj de la evidencia MP-019), así que la ventana EFECTIVA desde el ancla es de 190 s.
Las columnas de avance van rotuladas con los 190 s reales, no con los 180 s configurados.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.geo import PositionResolution, build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed, scheduled_trip_instances_for_date
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope
from packages.movement.schedule import build_trip_schedule

MADRID = ZoneInfo("Europe/Madrid")
ZIP = Path("data/hito-03/replay/fomento_transit.zip")
FIXTURES = Path("tests/fixtures")


def ss(t: str) -> int:
    h, m, s = (int(p) for p in t.split(":"))
    return h * 3600 + m * 60 + s


def main() -> None:
    topo = load_feed(ZIP, network_id="10")
    cat = build_catalog(topo, gtfs_version="aud01")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=FIXTURES)
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)
    trip_route = {t.trip_id: t.route_id for t in topo.trips}

    cut = datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc)
    anchor_at = cut                      # el ancla es la observación del corte
    calculated_at = cut + timedelta(seconds=10)   # mismo reloj que la evidencia MP-019
    local = cut.astimezone(MADRID)
    service_date = local.date()
    now_s = local.hour * 3600 + local.minute * 60 + local.second
    thresholds = MovementThresholds()
    horizon_end = calculated_at + timedelta(seconds=thresholds.stale_after_s)

    instances = {i.trip_id: i for i in scheduled_trip_instances_for_date(topo, service_date)}
    vp = json.loads((Path("data/hito-03/replay/1533/vehicle_positions.json")).read_text())

    horizon_effective_s = (horizon_end - anchor_at).total_seconds()
    print(f"umbral configurado: stale_after_s={thresholds.stale_after_s} s  "
          f"max_estimated_speed_kmh={thresholds.max_estimated_speed_kmh}")
    print(f"horizonte EFECTIVO desde el ancla: {horizon_effective_s:.0f} s "
          f"(= 10 s de desfase del snapshot + {thresholds.stale_after_s:.0f} s configurados)")
    print(f"ancla={anchor_at.isoformat()}  calculated_at={calculated_at.isoformat()}  "
          f"horizonte hasta {horizon_end.isoformat()}\n")

    rows = []
    for entity in vp["entity"]:
        v = entity["vehicle"]
        trip_id = v.get("trip", {}).get("tripId")
        route_id = trip_route.get(trip_id)
        inst = instances.get(trip_id)
        if route_id is None or inst is None:
            continue
        lead_s = ss(inst.first_departure_time) - now_s
        if lead_s <= 0:
            continue
        stop_ids = stops_by_trip.get(trip_id)
        coverage = corridors.coverage_for_stops(route_id, stop_ids)
        if not coverage.can_map_match or coverage.corridor is None:
            continue
        pos = v.get("position") or {}
        match = corridors.match_position(
            coverage.identity.pattern_id,
            raw_lat=pos.get("latitude"),
            raw_lon=pos.get("longitude"),
        )
        if match.resolution is not PositionResolution.MAP_MATCHED or match.progress_m is None:
            continue
        schedule = build_trip_schedule(topo, coverage.corridor, trip_id)
        env = _envelope(
            schedule=schedule,
            service_date=service_date,
            anchor_at=anchor_at,
            anchor_progress_m=match.progress_m,
            horizon_end=horizon_end,
            max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
        )
        # Avance total autorizado dentro del horizonte efectivo (ancla -> horizon_end).
        advance_horizon = env.max_progress_m - env.progress_m_at_reference
        rows.append((trip_id, lead_s, match.progress_m, env.speed_mps, advance_horizon,
                     env.dwell_until))

    rows.sort(key=lambda r: -r[1])
    print(f"trip_id           antelación a la salida  progreso ancla  speed_mps  "
          f"avance en {horizon_effective_s:.0f} s  dwell_until")
    for trip_id, lead, prog, speed, adv, dwell in rows:
        print(f"{trip_id:<16} {lead:>5.0f} s ({lead/60:>5.2f} min) {prog:>12.1f} m "
              f"{speed:>9.2f} {adv:>14.1f} m  "
              f"{'None' if dwell is None else dwell.isoformat()}")
    if rows:
        moving = [r for r in rows if r[3] > 0.5]
        print(f"\ncirculaciones pre-salida con corredor validado: {len(rows)}")
        print(f"  de ellas con avance publicado > 0,5 m/s: {len(moving)}")
        speeds = [r[3] for r in rows]
        print(f"  speed_mps publicado: min {min(speeds):.2f} max {max(speeds):.2f} "
              f"({min(speeds)*3.6:.1f}-{max(speeds)*3.6:.1f} km/h)")
        if moving:
            worst = max(moving, key=lambda r: r[4])
            print(f"  peor caso: {worst[0]} — {worst[1]:.0f} s ({worst[1]/60:.2f} min) antes de salir, "
                  f"{worst[3]:.2f} m/s ({worst[3]*3.6:.0f} km/h), "
                  f"{worst[4]:.0f} m de avance dibujado en {horizon_effective_s:.0f} s")


if __name__ == "__main__":
    main()
