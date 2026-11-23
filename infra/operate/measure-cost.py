"""Medición real del coste de operar el colector continuo (MP-021).

No estima: **mide** una ventana real de operación y, a partir de ella,
extrapola a 24 h y 72 h dejando explícito que la extrapolación es una
proyección, no una observación. `SIGUIENTES-HITOS.md` exige exactamente eso
--"medir primero recursos, almacenamiento, transferencia, coste de 24/72 h y
licencias antes de contratar servicios"-- y prohíbe declarar "24/7 verificado"
sin haberlo verificado.

Qué mide, y de dónde sale cada número:

- **Ciclos y filas**: de `source_ingestion_run` y de las tablas hot de la
  propia base usada en la ventana, no de los logs.
- **Almacenamiento caliente**: `pg_database_size` antes y después.
- **Almacenamiento frío**: bytes reales del Parquet que produce
  `services/snapshotter` para el día medido.
- **Transferencia**: tamaño real de las respuestas de los tres feeds,
  muestreado de verdad con varias descargas (comprimido y sin comprimir).
  Es el tráfico de bajada por ciclo; el de subida es despreciable (tres GET).
- **CPU y memoria**: del muestreo de `ps` sobre el proceso del colector
  durante la ventana (fichero CSV producido por el supervisor/el operador).

Uso:

    python infra/operate/measure-cost.py \
        --database-url postgresql://... \
        --window-start 2026-11-23T05:23:00Z \
        --samples-csv ruta/rss_samples.csv \
        [--parquet-dir data/parquet] [--feed-samples 5]
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg

FEEDS = (
    "https://gtfsrt.renfe.com/vehicle_positions.json",
    "https://gtfsrt.renfe.com/trip_updates.json",
    "https://gtfsrt.renfe.com/alerts.json",
)

HOT_TABLES = (
    "vehicle_position_observation",
    "trip_update_observation",
    "service_alert",
    "source_ingestion_run",
    "data_quality_event",
)


def _parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fetch_with_retry(url: str, attempts: int = 4) -> tuple[bytes, str, int]:
    """Una descarga real del feed, reintentando un corte transitorio.

    Se mide un servicio público real: una desconexión puntual es ruido de la
    medición, no un dato. Los reintentos se cuentan y se publican en el
    informe, para no ocultar que el origen falló.
    """
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), response.headers.get("Content-Encoding", ""), attempt
        except Exception as exc:  # noqa: BLE001 - cualquier corte de red cuenta igual
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"no se pudo descargar {url} tras {attempts} intentos: {last}")


def measure_feed_transfer(samples: int) -> dict[str, object]:
    """Tamaño real de bajada de un ciclo completo, muestreado varias veces.

    Se mide el cuerpo **comprimido** (lo que viaja por la red, con
    `Accept-Encoding: gzip`) y el descomprimido, porque la factura de
    transferencia de cualquier proveedor cuenta lo primero y el coste de
    parseo depende de lo segundo.
    """
    per_cycle_wire: list[int] = []
    per_feed: dict[str, dict[str, int]] = {}
    failures = 0
    for _ in range(samples):
        cycle_wire = 0
        for url in FEEDS:
            body, encoding, retries = _fetch_with_retry(url)
            failures += retries
            wire = len(body)
            plain = len(gzip.decompress(body)) if encoding == "gzip" else wire
            cycle_wire += wire
            entry = per_feed.setdefault(url, {"wire_min": wire, "wire_max": wire, "plain": plain})
            entry["wire_min"] = min(entry["wire_min"], wire)
            entry["wire_max"] = max(entry["wire_max"], wire)
            entry["plain"] = max(entry["plain"], plain)
        per_cycle_wire.append(cycle_wire)
    return {
        "samples": samples,
        "reintentos_de_red": failures,
        "per_feed": per_feed,
        "bytes_per_cycle_wire_mean": statistics.mean(per_cycle_wire),
        "bytes_per_cycle_wire_min": min(per_cycle_wire),
        "bytes_per_cycle_wire_max": max(per_cycle_wire),
    }


def measure_database(database_url: str, window_start: datetime) -> dict[str, object]:
    with psycopg.connect(database_url, connect_timeout=5) as conn:
        (size_bytes,) = conn.execute("SELECT pg_database_size(current_database())").fetchone()
        counts = {
            table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in HOT_TABLES
        }
        (cycles, first_run, last_run, errors) = conn.execute(
            """
            SELECT count(*), min(started_at), max(started_at),
                   count(*) FILTER (WHERE status <> 'ok')
            FROM source_ingestion_run
            WHERE started_at >= %s
            """,
            (window_start,),
        ).fetchone()
    return {
        "database_size_bytes": size_bytes,
        "row_counts": counts,
        "ingestion_runs": cycles,
        "ingestion_runs_failed": errors,
        "first_run_at": first_run.isoformat() if first_run else None,
        "last_run_at": last_run.isoformat() if last_run else None,
    }


def _cpu_seconds(value: str) -> float:
    """`ps -o time=` da `MM:SS.cc` o `HH:MM:SS`."""
    parts = value.strip().split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def measure_process(samples_csv: Path) -> dict[str, object] | None:
    """CPU y memoria del colector durante la ventana, **sumando por PID**.

    El contador de CPU de `ps` es **acumulado por proceso** y se reinicia en
    cada reinicio del colector. Restar el máximo global menos el mínimo global
    mezclaría procesos distintos y daría una cifra sin sentido. Se toma el
    último valor observado de cada PID (su CPU acumulada) y se suman: es el
    consumo real de la ventana supervisada, salvo el que cada proceso gastara
    después de su último muestreo -- una cota inferior ajustada, no una
    estimación optimista.
    """
    if not samples_csv.is_file():
        return None
    rows = [line.split(",") for line in samples_csv.read_text().splitlines()[1:] if line.strip()]
    if not rows:
        return None
    rss_kb = [int(row[2]) for row in rows]
    cpu_by_pid: dict[str, list[float]] = {}
    for row in rows:
        cpu_by_pid.setdefault(row[1], []).append(_cpu_seconds(row[3]))
    cpu_total = sum(max(values) for values in cpu_by_pid.values())
    return {
        "samples": len(rows),
        "process_instances": len(cpu_by_pid),
        "rss_max_mb": round(max(rss_kb) / 1024, 1),
        "rss_mean_mb": round(statistics.mean(rss_kb) / 1024, 1),
        "cpu_seconds_total": round(cpu_total, 2),
        "cpu_seconds_by_instance": {
            pid: round(max(values), 2) for pid, values in sorted(cpu_by_pid.items())
        },
        "first_sample": rows[0][0],
        "last_sample": rows[-1][0],
    }


def measure_parquet(parquet_dir: Path) -> dict[str, object]:
    files = sorted(parquet_dir.rglob("*.parquet")) if parquet_dir.is_dir() else []
    by_day: dict[str, int] = {}
    for path in files:
        day = next((part[5:] for part in path.parts if part.startswith("date=")), "sin-partición")
        by_day[day] = by_day.get(day, 0) + path.stat().st_size
    return {
        "files": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "bytes_by_service_date": by_day,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--window-start", required=True, help="Instante ISO-8601 (UTC).")
    parser.add_argument("--size-before-bytes", type=int, default=None)
    parser.add_argument("--samples-csv", type=Path, default=None)
    parser.add_argument("--parquet-dir", type=Path, default=Path("data/parquet"))
    parser.add_argument("--feed-samples", type=int, default=5)
    args = parser.parse_args()

    window_start = _parse_instant(args.window_start)
    now = datetime.now(timezone.utc)
    window_s = (now - window_start).total_seconds()

    database = measure_database(args.database_url, window_start)
    transfer = measure_feed_transfer(args.feed_samples)
    process = measure_process(args.samples_csv) if args.samples_csv else None
    parquet = measure_parquet(args.parquet_dir)

    cycles = database["ingestion_runs"] or 0
    # Un "ciclo" del colector son TRES ejecuciones de ingesta, una por feed.
    full_cycles = cycles / len(FEEDS) if cycles else 0
    cycles_per_hour = (full_cycles / window_s * 3600) if window_s > 0 else 0

    growth_bytes = (
        database["database_size_bytes"] - args.size_before_bytes
        if args.size_before_bytes is not None
        else None
    )

    report = {
        "medido": {
            "ventana_inicio_utc": window_start.isoformat(),
            "ventana_fin_utc": now.isoformat(),
            "ventana_segundos": round(window_s, 1),
            "ciclos_completos": round(full_cycles, 1),
            "ejecuciones_de_ingesta": cycles,
            "ejecuciones_con_error": database["ingestion_runs_failed"],
            "filas_por_tabla": database["row_counts"],
            "postgresql_bytes": database["database_size_bytes"],
            "postgresql_crecimiento_bytes": growth_bytes,
            "transferencia": transfer,
            "proceso": process,
            "parquet": parquet,
        },
        "extrapolado": {
            "_aviso": (
                "PROYECCIÓN a partir de la ventana medida arriba, NO una observación de "
                "24/72 h. No autoriza declarar «24/7 verificado»."
            ),
            "ciclos_por_hora": round(cycles_per_hour, 1),
            "transferencia_bajada_24h_mb": round(
                cycles_per_hour * 24 * transfer["bytes_per_cycle_wire_mean"] / 1024 / 1024, 1
            ),
            "transferencia_bajada_72h_mb": round(
                cycles_per_hour * 72 * transfer["bytes_per_cycle_wire_mean"] / 1024 / 1024, 1
            ),
        },
    }
    if growth_bytes is not None and window_s > 0:
        per_hour = growth_bytes / window_s * 3600
        report["extrapolado"]["postgresql_crecimiento_24h_mb"] = round(
            per_hour * 24 / 1024 / 1024, 1
        )
        report["extrapolado"]["postgresql_crecimiento_72h_mb"] = round(
            per_hour * 72 / 1024 / 1024, 1
        )
    if process is not None and window_s > 0:
        report["extrapolado"]["cpu_pct_de_un_nucleo"] = round(
            100 * process["cpu_seconds_total"] / window_s, 2
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
