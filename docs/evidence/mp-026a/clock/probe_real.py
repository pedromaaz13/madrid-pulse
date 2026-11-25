"""Comprueba la vigencia con el ZIP real congelado y el reloj de la API simulado."""

import os
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app
from tests.clock import api_wall_clock
from tests.postgres import connect_disposable_or_skip

ENDPOINTS = ("health", "catalog", "snapshot")


def check(client: TestClient, wall: str, at: str | None, expected: str) -> None:
    for endpoint in ENDPOINTS:
        reply = client.get(f"/api/v1/{endpoint}", params={"at": at} if at else None)
        reply.raise_for_status()
        body = reply.json()
        actual = body["gtfs_status"]
        print(f"pared={wall} at={at} {endpoint} HTTP={reply.status_code} gtfs_status={actual}")
        if actual != expected:
            raise AssertionError(f"{endpoint}: esperado {expected}, observado {actual}")
        if endpoint == "snapshot":
            if body["generated_at"] != (at or wall):
                raise AssertionError(f"generated_at inesperado: {body['generated_at']}")
        elif (body["gtfs_valid_from"], body["gtfs_valid_until"]) != ("2026-11-20", "2026-12-19"):
            raise AssertionError("El ZIP cargado tiene una ventana de vigencia distinta")


def main() -> None:
    connect_disposable_or_skip().close()
    with patch.dict(os.environ, {"MADRID_PULSE_MODE": "replay"}):
        for wall in ("2026-12-20T12:00:00Z", "2027-01-15T12:00:00Z"):
            with api_wall_clock(datetime.fromisoformat(wall)), TestClient(app) as client:
                for at, status in (
                    ("2026-11-19T22:59:59Z", "not_yet_valid"),
                    ("2026-11-19T23:00:00Z", "valid"),
                    ("2026-11-20T14:32:10Z", "valid"),
                    ("2026-12-18T12:00:00Z", "expiring"),
                    ("2026-12-19T22:59:59Z", "expiring"),
                    ("2026-12-19T23:00:00Z", "expired"),
                    ("2026-12-20T12:00:00Z", "expired"),
                    (None, "expired"),
                ):
                    check(client, wall, at, status)

    with (
        patch.dict(os.environ, {"MADRID_PULSE_MODE": "live"}),
        api_wall_clock(datetime.fromisoformat("2026-12-18T12:00:00Z")),
        TestClient(app) as client,
    ):
        for wall, status in (
            ("2026-12-18T12:00:00Z", "expiring"),
            ("2026-12-19T22:59:59Z", "expiring"),
            ("2026-12-19T23:00:00Z", "expired"),
            ("2026-12-20T12:00:00Z", "expired"),
            ("2027-01-15T12:00:00Z", "expired"),
        ):
            with api_wall_clock(datetime.fromisoformat(wall)):
                check(client, wall, None, status)


if __name__ == "__main__":
    main()
