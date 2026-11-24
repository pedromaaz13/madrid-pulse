"""AUD-01: cobertura honesta — programados en curso vs observados en el corte 1533/1532.

Usa el GTFS oficial congelado del kit (data/hito-03/replay/fomento_transit.zip)
y los dos cortes congelados. No toca PostgreSQL ni la red.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.gtfs import build_catalog, load_feed, scheduled_trip_instances_for_date

ZIP = Path("data/hito-03/replay/fomento_transit.zip")
MADRID = ZoneInfo("Europe/Madrid")


def service_seconds(gtfs_time: str) -> int:
    h, m, s = (int(part) for part in gtfs_time.split(":"))
    return h * 3600 + m * 60 + s


def main() -> None:
    topology = load_feed(ZIP, network_id="10")
    catalog = build_catalog(topology, gtfs_version="aud01")
    route_to_line = {
        route_id: line.short_name for line in catalog.lines for route_id in line.route_ids
    }
    print(f"catálogo: {len(catalog.lines)} líneas, "
          f"{sum(len(l.route_ids) for l in catalog.lines)} rutas, "
          f"{sum(len(l.patterns) for l in catalog.lines)} patrones")

    for cut, captured in (("1532", "2026-11-20T14:32:21Z"), ("1533", "2026-11-20T14:33:21Z")):
        instant = datetime.fromisoformat(captured.replace("Z", "+00:00"))
        local = instant.astimezone(MADRID)
        service_date = local.date()
        now_s = local.hour * 3600 + local.minute * 60 + local.second

        instances = scheduled_trip_instances_for_date(topology, service_date)
        in_progress = [
            i for i in instances
            if service_seconds(i.first_departure_time) <= now_s <= service_seconds(i.last_arrival_time)
        ]

        vp = json.loads((Path("data/hito-03/replay") / cut / "vehicle_positions.json").read_text())
        madrid_vehicles, resolved_trips = [], set()
        trip_route = {t.trip_id: t.route_id for t in topology.trips}
        for entity in vp["entity"]:
            v = entity["vehicle"]
            trip_id = v.get("trip", {}).get("tripId")
            route_id = trip_route.get(trip_id)
            if route_id is None or route_to_line.get(route_id) is None:
                continue
            madrid_vehicles.append((v["vehicle"]["id"], trip_id))
            resolved_trips.add(trip_id)

        inprog_ids = {i.trip_id for i in in_progress}
        observed_inprog = resolved_trips & inprog_ids

        print(f"\n--- corte {cut} ({local.isoformat()}) ---")
        print(f"  instancias programadas del día de servicio : {len(instances)}")
        print(f"  instancias programadas EN CURSO al instante: {len(in_progress)}")
        print(f"  vehículos Madrid observados (resolubles)   : {len(madrid_vehicles)}")
        print(f"  viajes observados distintos                : {len(resolved_trips)}")
        print(f"  observados que están EN CURSO por horario  : {len(observed_inprog)}")
        den = len(in_progress)
        print(f"  COBERTURA REAL DE POSICIONAMIENTO          : "
              f"{len(observed_inprog)}/{den} = {100*len(observed_inprog)/den:.1f}%" if den else "n/a")

        by_line_sched: dict[str, int] = {}
        by_line_obs: dict[str, int] = {}
        for i in in_progress:
            line = route_to_line.get(i.route_id)
            if line:
                by_line_sched[line] = by_line_sched.get(line, 0) + 1
        for trip_id in observed_inprog:
            line = route_to_line.get(trip_route[trip_id])
            if line:
                by_line_obs[line] = by_line_obs.get(line, 0) + 1
        print("  por línea (observados en curso / programados en curso):")
        for line in sorted(set(by_line_sched) | set(by_line_obs)):
            s = by_line_sched.get(line, 0)
            o = by_line_obs.get(line, 0)
            pct = f"{100*o/s:.0f}%" if s else "n/a"
            print(f"    {line:<4} {o:>3} / {s:>3}  = {pct}")


if __name__ == "__main__":
    main()
