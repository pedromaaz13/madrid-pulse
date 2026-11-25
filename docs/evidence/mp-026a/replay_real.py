"""Prueba local de FR-02 y FR-19 contra los datos externos del kit de Hito 3."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api import gtfs_source, main, snapshot
from apps.api.config import ApiConfig
from services.collector.collector import run_cycle
from services.collector.config import FeedConfig
from services.collector.http_client import RetryPolicy
from tests.postgres import connect_disposable_or_skip

# CAP_1532 y CAP_1533 de apps/api/tools/replay_three_snapshots.py.
CUTS = (
    ("1532", datetime.fromisoformat("2026-11-20T14:32:04Z")),
    ("1533", datetime.fromisoformat("2026-11-20T14:33:21Z")),
)


def ingest(root: Path, conn) -> None:
    if conn.execute("SELECT count(*) FROM source_ingestion_run").fetchone()[0]:
        raise RuntimeError("El arnés requiere una base inicialmente vacía")
    policy = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=5.0)
    for cut, instant in CUTS:
        for name in ("vehicle_positions", "trip_updates", "alerts"):
            body = (root / cut / f"{name}.json").read_bytes()
            result = run_cycle(
                FeedConfig(name, f"https://example.invalid/{name}.json"),
                conn,
                policy,
                fetcher=lambda url, timeout: body,
                now=lambda: instant,
            )
            if result.status != "ok":
                raise RuntimeError(result.error)
            print(cut, name, "entities", result.entity_count, "inserted", result.inserted_count)
        conn.commit()


def response(client: TestClient, endpoint: str, at: str | None = None) -> dict:
    reply = client.get(f"/api/v1/{endpoint}", params={"at": at} if at else None)
    reply.raise_for_status()
    return reply.json()


def replay_probe() -> None:
    def vehicle_feed(body: dict) -> dict | None:
        return next((feed for feed in body["feeds"] if feed["feed_name"] == "vehicle_positions"), None)

    with TestClient(main.app) as client:
        for at in (
            "2026-11-20T14:32:03Z",
            "2026-11-20T14:32:10Z",  # FRONTEND_UX_AUDIT.md §2 P0-1.
            "2026-11-20T14:33:40Z",
        ):
            result = response(client, "snapshot", at)
            times = [vehicle["timestamps"] for vehicle in result["vehicles"]]
            clock = datetime.fromisoformat(at)
            latest_gps = max(
                (datetime.fromisoformat(entry["gps_observed_at"]) for entry in times), default=None
            )
            print(json.dumps({
                "at": at,
                "snapshot_vehicle_feed": vehicle_feed(result),
                "health_vehicle_feed": vehicle_feed(response(client, "health", at)),
                "revision": result["revision"]["sequence"],
                "vehicles_total": len(times),
                "latest_gps_observed_at": latest_gps.isoformat() if latest_gps else None,
                "vehicles_received_after_at": sum(
                    datetime.fromisoformat(entry["received_at"]) > clock for entry in times
                ),
            }))


def live_probe() -> None:
    clock = datetime.fromisoformat("2026-12-10T12:00:00Z")

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock.astimezone(tz)

    with (
        patch.dict(os.environ, {"MADRID_PULSE_MODE": "live"}),
        patch.object(main, "now_utc", side_effect=lambda: clock),
        patch.object(gtfs_source, "datetime", FrozenDatetime),
        patch.object(snapshot, "datetime", FrozenDatetime),
        TestClient(main.app) as client,
    ):
        for instant in ("2026-12-10T12:00:00Z", "2026-12-18T12:00:00Z", "2026-12-20T12:00:00Z"):
            clock = datetime.fromisoformat(instant)
            for endpoint in ("health", "catalog", "snapshot"):
                result = response(client, endpoint)
                print(json.dumps({
                    "clock": instant,
                    "endpoint": endpoint,
                    "gtfs_status": result.get("gtfs_status"),
                    "gtfs_status_reason": result.get("gtfs_status_reason"),
                    "gtfs_valid_until": result.get("gtfs_valid_until"),
                }))


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("ingest", "probe"))
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    url = os.environ["MADRID_PULSE_DATABASE_URL"]
    if ApiConfig.from_env().database_dsn != url:
        raise RuntimeError("La API apunta a una URL distinta de la base desechable verificada")
    if Path(os.environ["MADRID_PULSE_GTFS_SOURCE"]).resolve() != (
        args.root / "fomento_transit.zip"
    ).resolve():
        raise RuntimeError("El GTFS debe ser el ZIP del kit congelado")
    conn = connect_disposable_or_skip()
    try:
        if args.action == "ingest":
            ingest(args.root, conn)
            return
    finally:
        conn.close()
    replay_probe()
    live_probe()


if __name__ == "__main__":
    run()
