"""AUD-01: magnitud real del salto cuando llega el ancla siguiente (1532 -> 1533).

Para cada circulación map-matcheable presente en los dos cortes congelados:
 - envolvente publicada a partir del ancla de 1532 (mismo código de producción);
 - progreso real del ancla de 1533, 77 s después;
 - diferencia = corrección que el cliente aplica de golpe al refrescar.
Sin PostgreSQL ni red: solo las fixtures del kit y el código del repositorio.
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.geo import PositionResolution, build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope
from packages.movement.schedule import build_trip_schedule

MADRID = ZoneInfo("Europe/Madrid")
CUTS = {
    "1532": datetime(2026, 11, 20, 14, 32, 4, tzinfo=timezone.utc),
    "1533": datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc),
}


def load_positions(cut: str) -> dict[str, tuple[str, float, float]]:
    data = json.loads(Path(f"data/hito-03/replay/{cut}/vehicle_positions.json").read_text())
    out = {}
    for entity in data["entity"]:
        v = entity["vehicle"]
        trip_id = v.get("trip", {}).get("tripId")
        pos = v.get("position") or {}
        if trip_id and pos.get("latitude") is not None:
            out[v["vehicle"]["id"]] = (trip_id, pos["latitude"], pos["longitude"])
    return out


def main() -> None:
    topo = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
    cat = build_catalog(topo, gtfs_version="aud01")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    stops_by_trip = {}
    for trip in topo.trips:
        times = topo.stop_times_for_trip(trip.trip_id)
        if times:
            stops_by_trip[trip.trip_id] = tuple(t.stop_id for t in times)

    a, b = load_positions("1532"), load_positions("1533")
    service_date = CUTS["1532"].astimezone(MADRID).date()
    thresholds = MovementThresholds()
    gap_s = (CUTS["1533"] - CUTS["1532"]).total_seconds()

    rows = []
    for vehicle_id, (trip_id, lat_a, lon_a) in a.items():
        if vehicle_id not in b:
            continue
        trip_b, lat_b, lon_b = b[vehicle_id]
        if trip_b != trip_id:
            continue
        route_id = trip_route.get(trip_id)
        stop_ids = stops_by_trip.get(trip_id)
        if route_id is None or stop_ids is None:
            continue
        coverage = corridors.coverage_for_stops(route_id, stop_ids)
        if not coverage.can_map_match or coverage.corridor is None:
            continue
        ma = corridors.match_position(coverage.identity.pattern_id, raw_lat=lat_a, raw_lon=lon_a)
        mb = corridors.match_position(coverage.identity.pattern_id, raw_lat=lat_b, raw_lon=lon_b)
        if (ma.resolution is not PositionResolution.MAP_MATCHED
                or mb.resolution is not PositionResolution.MAP_MATCHED):
            continue
        schedule = build_trip_schedule(topo, coverage.corridor, trip_id)
        anchor_at = CUTS["1532"]
        # Horizonte EFECTIVO desde el ancla: 10 s de desfase del snapshot (reloj de la
        # evidencia MP-019) + los 180 s configurados en `stale_after_s` = 190 s.
        horizon_end = anchor_at + timedelta(seconds=10 + thresholds.stale_after_s)
        env = _envelope(
            schedule=schedule,
            service_date=service_date,
            anchor_at=anchor_at,
            anchor_progress_m=ma.progress_m,
            horizon_end=horizon_end,
            max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
        )
        predicted = min(
            env.progress_m_at_reference + env.speed_mps * gap_s, env.max_progress_m
        )
        snap = mb.progress_m - predicted
        real_speed = (mb.progress_m - ma.progress_m) / gap_s
        rows.append((vehicle_id, coverage.identity.route_id, env.speed_mps, real_speed,
                     predicted, mb.progress_m, snap))

    rows.sort(key=lambda r: -abs(r[6]))
    horizon_effective_s = 10 + thresholds.stale_after_s
    print(f"circulaciones map-matcheables presentes en ambos cortes: {len(rows)}  "
          f"(separación real {gap_s:.0f} s)")
    print(f"horizonte efectivo de la envolvente desde el ancla: {horizon_effective_s:.0f} s "
          f"(stale_after_s={thresholds.stale_after_s:.0f} configurados + 10 s de desfase)\n")
    print("vehículo  ruta         v_envolvente  v_real    progreso previsto   progreso real     SALTO")
    for vid, rid, vs, vr, pred, real, snap in rows:
        print(f"{vid:<9} {rid:<12} {vs:>8.2f} m/s {vr:>8.2f} {pred:>16.1f} m {real:>14.1f} m "
              f"{snap:>+9.1f} m")
    # "No se movió" = el progreso map-matcheado es idéntico en los dos cortes, es decir
    # v_real == 0 exactamente: ni la coordenada bruta ni su proyección cambian.
    still = [r for r in rows if r[3] == 0.0]
    moving = [r for r in rows if r[3] != 0.0]
    print(f"\nsin cambio de coordenada ni de progreso entre los dos cortes: "
          f"{len(still)} de {len(rows)}")
    print(f"con movimiento real: {len(moving)} de {len(rows)} "
          f"(uno de ellos, {[r[0] for r in moving if r[3] < 0]}, hacia atrás)")
    snaps = [abs(r[6]) for r in rows]
    print(f"\n|salto| p50 = {statistics.median(snaps):.0f} m · "
          f"media = {statistics.mean(snaps):.0f} m · máx = {max(snaps):.0f} m")
    print(f"a la cadencia real del feed (~30 s, MP-003/DEC-041) el salto esperado escala a "
          f"~{statistics.median(snaps)*30/gap_s:.0f} m (p50) y ~{max(snaps)*30/gap_s:.0f} m (máx)")


if __name__ == "__main__":
    main()
