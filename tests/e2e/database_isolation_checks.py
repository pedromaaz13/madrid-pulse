"""Regresión MP-023. Ejecutar el primer grupo antes de marcar la base."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from urllib.parse import urlsplit

import psycopg
from fastapi.testclient import TestClient

from apps.api.config import ApiConfig
from apps.api.main import app
from apps.api.tests import test_api_contract
from services.collector import __main__ as collector_main
from services.collector.collector import run_cycle
from services.collector.config import CollectorConfig
from services.collector.http_client import RetryPolicy
from services.snapshotter import __main__ as snapshotter_main
from services.snapshotter.config import SnapshotterConfig

URL_ENV = "MADRID_PULSE_DATABASE_URL"
MODE_ENV = "MADRID_PULSE_ENV"
ISOLATED_PORT = 5451
SHARED_DEV_PORT = 5433


def _isolated_url() -> str:
    url = os.environ[URL_ENV]
    address = urlsplit(url)
    if (address.hostname, address.port) != ("127.0.0.1", ISOLATED_PORT) or address.query:
        raise AssertionError("La regresión requiere el PostgreSQL desechable local en el puerto 5451.")
    return url


def _start_api() -> None:
    with TestClient(app):
        pass


class SafeConfigurationRegressionTests(unittest.TestCase):
    def test_missing_url_stops_each_service_before_io(self) -> None:
        for service in (collector_main.main, _start_api, snapshotter_main.main):
            for env in ({}, {URL_ENV: "  ", MODE_ENV: "test"}):
                with (
                    self.subTest(service=service.__module__, env=env),
                    mock.patch.dict(os.environ, env, clear=True),
                    mock.patch.object(sys, "argv", ["snapshotter", "2026-11-19"]),
                    mock.patch("psycopg.connect", side_effect=AssertionError("intentó conectar")),
                    mock.patch.object(
                        snapshotter_main, "export_service_date",
                        side_effect=AssertionError("intentó exportar"),
                    ),
                    self.assertRaisesRegex((SystemExit, ValueError), URL_ENV),
                ):
                    service()

    def test_suite_refuses_an_unmarked_database(self) -> None:
        url = _isolated_url()
        # El código anterior pide su propia variable para la API. Ambas se
        # fijan al contenedor de la prueba para que RED no use su valor implícito.
        env = {URL_ENV: url, MODE_ENV: "test", "MADRID_PULSE_DATABASE_DSN": url}
        name = "test_stations_endpoint_matches_real_gtfs_fixture"
        with mock.patch.dict(os.environ, env, clear=True):
            result = test_api_contract.ApiContractTests(name).run()
        self.assertFalse(result.errors)
        self.assertFalse(result.failures)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn("sin marca desechable", result.skipped[0][1])

    def test_shared_target_is_rejected_before_connection(self) -> None:
        targets = (
            f"postgresql://test@127.0.0.1:{SHARED_DEV_PORT}/sandbox",
            f"postgresql://test@localhost:0{SHARED_DEV_PORT}/sandbox",
            f"postgresql://test@some-host:{SHARED_DEV_PORT}/sandbox?hostaddr=127.0.0.1",
        )
        for config in (CollectorConfig, ApiConfig, SnapshotterConfig):
            for url in targets:
                with (
                    self.subTest(config=config.__name__, url=url),
                    mock.patch.dict(os.environ, {URL_ENV: url, MODE_ENV: "dev"}, clear=True),
                    mock.patch("psycopg.connect", side_effect=AssertionError("intentó conectar")),
                    self.assertRaisesRegex(ValueError, "compartido"),
                ):
                    config.from_env()


class SafeConfigurationTests(unittest.TestCase):
    def test_legacy_url_mentions_the_replacement(self) -> None:
        env = {"MADRID_PULSE_DATABASE_DSN": "postgresql://legacy@127.0.0.1/sandbox"}
        with (
            mock.patch.dict(os.environ, env, clear=True),
            self.assertRaisesRegex(ValueError, f"{URL_ENV}.*obsoleta"),
        ):
            _start_api()

    def test_environment_is_required_and_valid(self) -> None:
        for environment in ("", "prod"):
            env = {URL_ENV: "postgresql://test@127.0.0.1/sandbox", MODE_ENV: environment}
            with (
                self.subTest(environment=environment),
                mock.patch.dict(os.environ, env, clear=True),
                self.assertRaisesRegex(ValueError, MODE_ENV),
            ):
                CollectorConfig.from_env()

    def test_confirmation_is_only_valid_for_dev_or_live(self) -> None:
        from packages.database import validate_database_url

        url = f"postgresql://test@127.0.0.1:{SHARED_DEV_PORT}/sandbox"
        for environment in ("test", "replay"):
            with self.assertRaisesRegex(ValueError, "compartido"):
                validate_database_url(url, environment, allow_shared_dev=True)
        for environment in ("dev", "live"):
            validate_database_url(url, environment, allow_shared_dev=True)

    def test_reserved_port_is_rejected_for_every_host_without_connecting(self) -> None:
        from packages.database import validate_database_url

        hosts = (
            "host.docker.internal", "foo.localhost", "localhost.localdomain", "ip6-localhost",
            socket.gethostname(), "db.example.invalid", "192.0.2.1", "[2001:db8::1]",
        )
        for host in hosts:
            url = f"postgresql://test@{host}:{SHARED_DEV_PORT}/sandbox"
            for environment in ("dev", "live", "test", "replay"):
                with (
                    self.subTest(host=host, environment=environment),
                    self.assertRaisesRegex(ValueError, r"docs/operations/DATABASE_ISOLATION\.md"),
                ):
                    validate_database_url(url, environment)
            for environment in ("dev", "live"):
                validate_database_url(url, environment, allow_shared_dev=True)
            validate_database_url(f"postgresql://test@{host}:{ISOLATED_PORT}/sandbox", "test")

    def test_replay_tools_report_missing_config_and_mark_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            matrix = (
                "apps.api.tools.build_closure_matrix",
                "--captured-at", "2026-11-19T15:00:00Z", "--service-date", "2026-11-19",
                "--csv", str(Path(directory) / "matrix.csv"),
                "--markdown", str(Path(directory) / "matrix.md"),
            )
            replay = ("apps.api.tools.replay_three_snapshots",)
            for command in (matrix, replay):
                unavailable_db = _isolated_url().rsplit("/", 1)[0] + "/mp023_missing"
                for env, message in (
                    ({}, URL_ENV),
                    ({URL_ENV: _isolated_url(), MODE_ENV: "dev"}, "sin marca desechable"),
                    ({URL_ENV: unavailable_db, MODE_ENV: "replay"}, "PostgreSQL no disponible"),
                ):
                    with self.subTest(tool=command[0], diagnostic=message):
                        result = subprocess.run(
                            [sys.executable, "-m", *command], env=env,
                            capture_output=True, text=True, timeout=15, check=False,
                        )
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn(message, result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
                        print(f"{command[0]}: salida {result.returncode}, {result.stderr.strip()}")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_required_database_errors_are_failures(self) -> None:
        from tests.postgres import connect_disposable_or_skip

        for settings, message in (
            ({}, URL_ENV),
            ({URL_ENV: _isolated_url(), MODE_ENV: "invalid"}, MODE_ENV),
            ({URL_ENV: _isolated_url(), MODE_ENV: "test"}, "sin marca desechable"),
        ):
            for strict, expected in (("0", unittest.SkipTest), ("1", AssertionError)):
                with (
                    self.subTest(strict=strict, diagnostic=message),
                    mock.patch.dict(os.environ, {**settings, "MADRID_PULSE_REQUIRE_DB": strict}, clear=True),
                    self.assertRaisesRegex(expected, message),
                ):
                    connect_disposable_or_skip()

    def test_required_database_unavailable_is_a_failure(self) -> None:
        from tests.postgres import connect_disposable_or_skip

        with (
            mock.patch.dict(os.environ, {
                URL_ENV: _isolated_url(), MODE_ENV: "test", "MADRID_PULSE_REQUIRE_DB": "1",
            }, clear=True),
            mock.patch("psycopg.connect", side_effect=psycopg.OperationalError),
            self.assertRaisesRegex(AssertionError, "PostgreSQL de integración no disponible"),
        ):
            connect_disposable_or_skip()

    def test_unmarked_database_stops_writers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env = {URL_ENV: _isolated_url(), MODE_ENV: "replay", "SNAPSHOTTER_OUTPUT_DIR": directory}
            with (
                mock.patch.dict(os.environ, env, clear=True),
                mock.patch.object(sys, "argv", ["snapshotter", "2026-11-19"]),
                mock.patch.object(
                    collector_main, "run_cycle", side_effect=AssertionError("intentó ingestar"),
                ) as cycle,
                mock.patch.object(
                    snapshotter_main, "export_service_date",
                    side_effect=AssertionError("intentó exportar"),
                ) as export,
            ):
                for service in (collector_main.main, snapshotter_main.main):
                    with (
                        self.subTest(service=service.__module__),
                        self.assertRaisesRegex(SystemExit, "sin marca desechable"),
                    ):
                        service()
                cycle.assert_not_called()
                export.assert_not_called()
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_real_startups_fail_with_no_variables_and_leave_zero_rows(self) -> None:
        commands = (
            ("services.collector",),
            ("uvicorn", "apps.api.main:app", "--lifespan", "on", "--port", "0"),
            ("services.snapshotter", "2026-11-19"),
        )
        query = """
            SELECT (SELECT count(*) FROM vehicle_position_observation),
                   (SELECT count(*) FROM trip_update_observation),
                   (SELECT count(*) FROM service_alert),
                   (SELECT count(*) FROM source_ingestion_run),
                   (SELECT count(*) FROM data_quality_event)
        """
        with psycopg.connect(_isolated_url(), autocommit=True) as conn:
            self.assertEqual(conn.execute(query).fetchone(), (0, 0, 0, 0, 0))
            for args in commands:
                with self.subTest(command=args), tempfile.TemporaryDirectory() as directory:
                    result = subprocess.run(
                        [sys.executable, "-m", *args],
                        env={"SNAPSHOTTER_OUTPUT_DIR": directory},
                        capture_output=True, text=True, timeout=15, check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(URL_ENV, result.stderr)
                    self.assertEqual(list(Path(directory).iterdir()), [])
                    print(f"{' '.join(args)}: salida {result.returncode}, diagnóstico {URL_ENV}")
            after = conn.execute(query).fetchone()
            self.assertEqual(after, (0, 0, 0, 0, 0))
            print(f"Recuentos finales de las cinco tablas hot: {after}")


class CanonicalUrlIntegrationTest(unittest.TestCase):
    def test_collector_writes_and_api_reads_via_the_same_url(self) -> None:
        from packages.database import require_disposable_database
        from services.collector.config import FeedConfig

        url = _isolated_url()
        env = {
            URL_ENV: url, MODE_ENV: "test", "MADRID_PULSE_MODE": "replay",
            "MADRID_PULSE_DATABASE_DSN": "postgresql://legacy@invalid.invalid/discarded",
        }
        now = datetime(2026, 11, 19, 15, tzinfo=timezone.utc)
        timestamp = str(int(now.timestamp()))
        vehicle_id = "mp023-isolation"
        payload = json.dumps({
            "header": {"gtfsRealtimeVersion": "2.0", "timestamp": timestamp},
            "entity": [{
                "id": "VP_MP023",
                "vehicle": {
                    "trip": {"tripId": "1022J19502C5"},
                    "position": {"latitude": 40.331064, "longitude": -3.882456},
                    "currentStatus": "STOPPED_AT",
                    "timestamp": timestamp,
                    "stopId": "35607",
                    "vehicle": {"id": vehicle_id, "label": "MP-023"},
                },
            }],
        }).encode()
        with psycopg.connect(url, autocommit=True) as conn:
            require_disposable_database(conn)

        def ingest_once(
            feed: FeedConfig,
            conn: psycopg.Connection,
            policy: RetryPolicy,
            *,
            madrid_stop_ids: frozenset[str] | None,
        ) -> None:
            self.assertEqual(feed.name, "vehicle_positions")
            result = run_cycle(
                feed, conn, policy, fetcher=lambda *_: payload, now=lambda: now,
                madrid_stop_ids=madrid_stop_ids,
            )
            self.assertEqual(result.inserted_count, 1)
            raise KeyboardInterrupt

        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(collector_main, "run_cycle", side_effect=ingest_once),
        ):
            self.assertEqual(ApiConfig.from_env().database_dsn, url)
            self.assertEqual(SnapshotterConfig.from_env().database_url, url)
            with self.assertRaises(KeyboardInterrupt):
                collector_main.main()
            with TestClient(app) as client:
                response = client.get(f"/api/v1/live/vehicles/{vehicle_id}")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["vehicle_id"], vehicle_id)
