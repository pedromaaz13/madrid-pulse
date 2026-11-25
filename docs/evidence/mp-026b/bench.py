"""Mide ambos endpoints HTTP con el reloj fijo y una conexión por petición."""

import json
import platform

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.tools.bench_snapshot import measure
from tests.postgres import connect_disposable_or_skip

at = "2026-11-19T04:20:00Z"
paths = [f"/api/v1/snapshot?at={at}", f"/api/v1/stations/18000/board?at={at}"]
conn = connect_disposable_or_skip()
with conn:
    for table in ("source_ingestion_run", "vehicle_position_observation", "trip_update_observation"):
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
print(f"Python {platform.python_version()}, {platform.platform()}")
with TestClient(app) as client:
    for path in paths:
        for _ in range(10):
            client.get(path).raise_for_status()
    for path in paths:
        response = client.get(path)
        response.raise_for_status()
        body = response.json()
        print(f"{path}: sequence={body['revision']['sequence']}")
        if "entries" in body:
            assert body["coverage"]["observed_circulations"] > 0, body["coverage"]
            assert body["coverage"]["with_operator_delay"] > 0, body["coverage"]
            print(body["coverage"])
        else:
            assert body["counts"]["vehicles_total"] == 100, body["counts"]
            print(body["counts"])
        result = measure(client, path, 60)
        assert result["status_codes"] == [200], result
        print(json.dumps(result, sort_keys=True))
