"""Bench reproducible de los endpoints de MP-019 (ADR-0014).

Mide p50/p95 reales en proceso (`TestClient`), es decir el coste del código de
la API + PostgreSQL, **sin** red ni servidor ASGI. Esa separación es
deliberada: una cifra que incluya la red depende del host y no sirve para
detectar una regresión del backend. Para medir el camino completo, arrancar
`uvicorn` y usar un cliente HTTP externo.

Las cifras obtenidas son *medidas*, no presupuestos: ver
`docs/evidence/mp-019-explain-y-bench.md` para el equipo y el dataset exactos
con los que se registraron. No se declara ningún umbral universal.

Uso:

    MADRID_PULSE_GTFS_SOURCE=... MADRID_PULSE_SHORT_NAME= \\
      .venv/bin/python -m apps.api.tools.bench_snapshot --iterations 60
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time

import psycopg
from fastapi.testclient import TestClient

from apps.api.config import ApiConfig
from apps.api.main import app, get_connection


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("sin muestras")
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def measure(client: TestClient, path: str, iterations: int) -> dict[str, object]:
    samples: list[float] = []
    sizes: list[int] = []
    status_codes: set[int] = set()
    for _ in range(iterations):
        started = time.perf_counter()
        response = client.get(path)
        samples.append((time.perf_counter() - started) * 1000.0)
        status_codes.add(response.status_code)
        sizes.append(len(response.content))
    return {
        "path": path,
        "iterations": iterations,
        "status_codes": sorted(status_codes),
        "p50_ms": round(percentile(samples, 0.50), 2),
        "p95_ms": round(percentile(samples, 0.95), 2),
        "min_ms": round(min(samples), 2),
        "max_ms": round(max(samples), 2),
        "mean_ms": round(statistics.fmean(samples), 2),
        "response_bytes": max(sizes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=60)
    parser.add_argument("--station-id", default="18000", help="stop_id para el tablero")
    parser.add_argument(
        "--at",
        default=None,
        help="reloj explícito ISO-8601 para el tablero/snapshot (solo modo replay)",
    )
    parser.add_argument(
        "--reuse-connection",
        action="store_true",
        help=(
            "mide con una conexión PostgreSQL reutilizada en vez de una por "
            "petición (lo que hace la API hoy). Aísla el coste del código de la "
            "API del coste de establecer la conexión; ver la nota de la evidencia."
        ),
    )
    args = parser.parse_args()

    shared: psycopg.Connection | None = None
    if args.reuse_connection:
        shared = psycopg.connect(ApiConfig.from_env().database_dsn)
        app.dependency_overrides[get_connection] = lambda: shared

    clock = f"?at={args.at}" if args.at else ""
    with TestClient(app) as client:
        catalog = client.get("/api/v1/catalog")
        catalog.raise_for_status()
        etag = catalog.headers["etag"]
        paths = [
            "/api/v1/catalog",
            f"/api/v1/snapshot{clock}",
            f"/api/v1/stations/{args.station_id}/board{clock}",
            "/api/v1/live/vehicles",
            "/api/v1/health",
        ]
        results = [measure(client, path, args.iterations) for path in paths]

        # `304` se mide aparte: es el camino que un cliente real usa a partir
        # de la segunda carga del catálogo.
        samples: list[float] = []
        for _ in range(args.iterations):
            started = time.perf_counter()
            response = client.get("/api/v1/catalog", headers={"If-None-Match": etag})
            samples.append((time.perf_counter() - started) * 1000.0)
            assert response.status_code == 304, response.status_code
        results.append(
            {
                "path": "/api/v1/catalog (If-None-Match -> 304)",
                "iterations": args.iterations,
                "status_codes": [304],
                "p50_ms": round(percentile(samples, 0.50), 2),
                "p95_ms": round(percentile(samples, 0.95), 2),
                "min_ms": round(min(samples), 2),
                "max_ms": round(max(samples), 2),
                "mean_ms": round(statistics.fmean(samples), 2),
                "response_bytes": 0,
            }
        )

    if shared is not None:
        app.dependency_overrides.clear()
        shared.close()

    print(
        json.dumps(
            {
                "machine": {
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "python": platform.python_version(),
                },
                "connection_mode": (
                    "reused" if args.reuse_connection else "one_per_request"
                ),
                "note": (
                    "medición en proceso (TestClient): excluye red y servidor ASGI; "
                    "cifras medidas, no presupuestos"
                ),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
