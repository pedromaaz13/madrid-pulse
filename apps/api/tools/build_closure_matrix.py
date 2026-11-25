"""Genera la matriz de cobertura reproducible de cierre de MP-022.

La matriz cruza cuatro universos que no deben confundirse:

* catálogo y servicios programados del GTFS para un día de servicio;
* entidades de vehículo de **un corte congelado exacto**;
* resolución y presentación del snapshot construido por la API;
* cobertura ETA derivada de la última actualización de operador disponible.

No consulta producción ni descarga datos. Requiere que el corte elegido ya se
haya ingerido en un PostgreSQL desechable (por ejemplo con
``apps.api.tools.replay_three_snapshots``). ``captured_at_utc`` identifica el
timestamp de las observaciones que forman el denominador; una observación
anterior conservada por el snapshot no se cuenta como si perteneciera al corte.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import psycopg

from apps.api import snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from packages.database import DatabaseConfigurationError, require_disposable_database
from packages.gtfs import scheduled_trip_instances_for_date


COLUMNS = (
    "gtfs_version",
    "captured_at_utc",
    "line_id",
    "route_ids",
    "pattern_count",
    "scheduled_trip_instances",
    "feed_vehicle_observations",
    "resolved_trip_instances",
    "matched_positions",
    "drawable_positions",
    "position_age_p50_s",
    "position_age_p95_s",
    "route_coverage_numerator",
    "route_coverage_denominator",
    "route_coverage_pct",
    "geometry_validated_patterns",
    "geometry_total_patterns",
    "eta_covered_stops",
    "eta_eligible_stops",
    "unknown_reason_count",
    "caveats",
)


def percentile(values: Iterable[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return round(ordered[index], 2)


def pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(100.0 * numerator / denominator, 2)


def iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("captured_at debe incluir zona horaria")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _stop_ids_by_trip(network) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for item in network.topology.stop_times:
        result[item.trip_id].add(item.stop_id)
    return result


def build_rows(
    conn: psycopg.Connection,
    *,
    config: ApiConfig,
    captured_at: datetime,
    service_date: date,
) -> list[dict[str, object]]:
    network = load_network(config)
    validity = network.gtfs_validity(captured_at, expiring_days=config.gtfs_expiring_days)
    catalog = snapshot.build_catalog_payload(network, validity)
    route_to_line = {
        route_id: line.line_id for line in catalog.lines for route_id in line.route_ids
    }
    scheduled = scheduled_trip_instances_for_date(network.topology, service_date)
    scheduled_by_line: dict[str, list] = defaultdict(list)
    scheduled_trip_ids: set[str] = set()
    for instance in scheduled:
        line_id = route_to_line.get(instance.route_id)
        if line_id is None:
            continue
        scheduled_by_line[line_id].append(instance)
        scheduled_trip_ids.add(instance.trip_id)

    # Denominador exacto del corte, no "último conocido": así una fila que
    # solo sobrevivió desde 1532 no se atribuye falsamente al corte 1533.
    observed_rows = conn.execute(
        """
        SELECT source_vehicle_id, source_trip_id, observed_at
        FROM vehicle_position_observation
        WHERE observed_at = %s
        ORDER BY source_vehicle_id
        """,
        (captured_at,),
    ).fetchall()
    observed_ids = {row[0] for row in observed_rows}

    observed_by_line: dict[str, list[tuple[str, str, datetime]]] = defaultdict(list)
    resolved_by_line: dict[str, set[str]] = defaultdict(set)
    for vehicle_id, trip_id, observed_at in observed_rows:
        route_id = network.topology.resolve_trip_route_id(trip_id)
        line_id = route_to_line.get(route_id) if route_id is not None else None
        if line_id is None:
            continue
        observed_by_line[line_id].append((vehicle_id, trip_id, observed_at))
        if trip_id in scheduled_trip_ids:
            resolved_by_line[line_id].add(trip_id)

    # Diez segundos después del corte, igual que la evidencia MP-019. Solo se
    # conservan para esta matriz los vehículos presentes en el corte exacto.
    operational = snapshot.build_snapshot(
        conn, network, config, captured_at + timedelta(seconds=10)
    )
    vehicles_by_line: dict[str, list] = defaultdict(list)
    for vehicle in operational.vehicles:
        if vehicle.vehicle_id in observed_ids and vehicle.line is not None:
            vehicles_by_line[vehicle.line].append(vehicle)

    latest_updates = conn.execute(
        """
        SELECT DISTINCT ON (source_trip_id)
               source_trip_id, delay_coverage
        FROM trip_update_observation
        WHERE observed_at <= %s
        ORDER BY source_trip_id, observed_at DESC, id DESC
        """,
        (captured_at,),
    ).fetchall()
    updated_trip_ids = {
        trip_id for trip_id, coverage in latest_updates if coverage == "reported"
    }
    stops_by_trip = _stop_ids_by_trip(network)

    rows: list[dict[str, object]] = []
    for line in catalog.lines:
        line_id = line.line_id
        feed_rows = observed_by_line[line_id]
        vehicles = vehicles_by_line[line_id]
        ages = [
            max(0.0, (captured_at + timedelta(seconds=10) - item.timestamps.gps_observed_at).total_seconds())
            for item in vehicles
        ]
        eligible_stops = {
            stop_id
            for instance in scheduled_by_line[line_id]
            for stop_id in stops_by_trip.get(instance.trip_id, ())
        }
        covered_stops = {
            stop_id
            for instance in scheduled_by_line[line_id]
            if instance.trip_id in updated_trip_ids
            for stop_id in stops_by_trip.get(instance.trip_id, ())
        }
        validated_patterns = sum(item.geometry.can_map_match for item in line.patterns)
        denominator = len(feed_rows)
        numerator = len(resolved_by_line[line_id])

        caveats = [
            "corte congelado 1533; no es producción en vivo",
            "ETA por actualización de viaje aplicada a paradas como aproximación declarada",
        ]
        if denominator == 0:
            caveats.append("sin observaciones GPS en el corte; cobertura de ruta null")
        if validated_patterns < len(line.patterns):
            caveats.append(
                f"geometría incompleta: {validated_patterns}/{len(line.patterns)} patrones map-matcheables; fallback raw/tablero"
            )
        if len(covered_stops) < len(eligible_stops):
            caveats.append(
                f"ETA parcial: {len(covered_stops)}/{len(eligible_stops)} estaciones elegibles"
            )

        rows.append(
            {
                "gtfs_version": catalog.gtfs_version,
                "captured_at_utc": iso_utc(captured_at),
                "line_id": line_id,
                "route_ids": "|".join(line.route_ids),
                "pattern_count": len(line.patterns),
                "scheduled_trip_instances": len(scheduled_by_line[line_id]),
                "feed_vehicle_observations": denominator,
                "resolved_trip_instances": numerator,
                "matched_positions": sum(item.map_matched is not None for item in vehicles),
                "drawable_positions": sum(
                    item.rendered.lat is not None and item.rendered.lon is not None
                    for item in vehicles
                ),
                "position_age_p50_s": percentile(ages, 0.50),
                "position_age_p95_s": percentile(ages, 0.95),
                "route_coverage_numerator": numerator,
                "route_coverage_denominator": denominator,
                "route_coverage_pct": pct(numerator, denominator),
                "geometry_validated_patterns": validated_patterns,
                "geometry_total_patterns": len(line.patterns),
                "eta_covered_stops": len(covered_stops),
                "eta_eligible_stops": len(eligible_stops),
                "unknown_reason_count": sum(
                    item.rendered.rendering_method == "unlocated" for item in vehicles
                ),
                "caveats": "; ".join(caveats),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "null" if row[key] is None else row[key] for key in COLUMNS})


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total_num = sum(int(row["route_coverage_numerator"]) for row in rows)
    total_den = sum(int(row["route_coverage_denominator"]) for row in rows)
    lines = [
        "# MP-022 — Matriz de cobertura del corte congelado 1533",
        "",
        "Esta tabla es una vista legible del CSV canónico. El corte es una fixture congelada, **no producción en vivo**. La cobertura agregada se calcula como suma de numeradores / suma de denominadores; nunca como media de porcentajes por línea.",
        "",
        f"Cobertura de resolución ponderada: **{total_num}/{total_den} ({pct(total_num, total_den)}%)**. Catálogo: **{sum(len(str(row['route_ids']).split('|')) for row in rows)} rutas / {sum(int(row['pattern_count']) for row in rows)} patrones / {len(rows)} líneas**.",
        "",
        "| Línea | Rutas | Patrones | Programados | GPS corte | Resueltos | Matched | Dibujables | Edad p50/p95 (s) | Cobertura ruta | Geometría | ETA estaciones | Motivos desconocidos |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        age = (
            "null (sin GPS)"
            if row["position_age_p50_s"] is None
            else f"{row['position_age_p50_s']}/{row['position_age_p95_s']}"
        )
        coverage = (
            "null (denominador 0)"
            if row["route_coverage_pct"] is None
            else f"{row['route_coverage_numerator']}/{row['route_coverage_denominator']} ({row['route_coverage_pct']}%)"
        )
        lines.append(
            f"| {row['line_id']} | {len(str(row['route_ids']).split('|'))} | {row['pattern_count']} | "
            f"{row['scheduled_trip_instances']} | {row['feed_vehicle_observations']} | "
            f"{row['resolved_trip_instances']} | {row['matched_positions']} | {row['drawable_positions']} | "
            f"{age} | {coverage} | {row['geometry_validated_patterns']}/{row['geometry_total_patterns']} | "
            f"{row['eta_covered_stops']}/{row['eta_eligible_stops']} | {row['unknown_reason_count']} |"
        )
    lines.extend(["", "## Limitaciones por línea", ""])
    lines.extend(f"- **{row['line_id']}:** {row['caveats']}" for row in rows)
    lines.extend(
        [
            "",
            "## Definiciones",
            "",
            "- `scheduled_trip_instances`: instancias del día de servicio enumeradas con `calendar.txt` + `calendar_dates.txt` y `stop_times.txt`.",
            "- `feed_vehicle_observations`: vehículos cuyo `observed_at` coincide exactamente con el corte 1533. Una observación anterior conservada no entra en este denominador.",
            "- `resolved_trip_instances`: viajes observados del corte que resuelven contra el GTFS y están programados ese día.",
            "- `drawable_positions`: coordenada defendible para mostrar; puede ser GPS `raw` cuando no existe geometría validada. No equivale a map matching.",
            "- `eta_covered_stops`: estaciones distintas alcanzadas por viajes con actualización de retraso disponible. El retraso es de nivel viaje y su aplicación por parada es una aproximación publicada por el contrato.",
            "- `unknown_reason_count`: circulaciones `unlocated`; cero no significa cobertura geométrica plena.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    captured_at = datetime.fromisoformat(args.captured_at.replace("Z", "+00:00"))
    service_date = date.fromisoformat(args.service_date)
    try:
        config = ApiConfig.from_env()
        with psycopg.connect(config.database_dsn) as conn:
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            conn.read_only = True
            require_disposable_database(conn)
            rows = build_rows(
                conn, config=config, captured_at=captured_at, service_date=service_date
            )
    except DatabaseConfigurationError as exc:
        raise SystemExit(str(exc)) from None
    except psycopg.OperationalError:
        raise SystemExit("PostgreSQL no disponible para calcular la matriz de cobertura.") from None
    write_csv(args.csv, rows)
    write_markdown(args.markdown, rows)
    print(f"{len(rows)} líneas escritas en {args.csv} y {args.markdown}")


if __name__ == "__main__":
    main()
