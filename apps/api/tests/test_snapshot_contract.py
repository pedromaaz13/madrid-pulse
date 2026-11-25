"""Contrato de snapshot/catálogo/tablero de MP-019 (ADR-0014).

Dos clases de prueba, deliberadamente separadas:

- las que solo necesitan la fixture GTFS/OSM congelada (deterministas, sin red
  y sin PostgreSQL);
- las que necesitan PostgreSQL real, que insertan en una transacción ambiente
  y **siempre** hacen `rollback` -- mismo patrón que MP-007/MP-015: nunca se
  compromete nada en la base de desarrollo.

Toda observación construida aquí es sintética y se etiqueta como tal en
`raw_vehicle_label`; ninguna se presenta como captura de Renfe.
"""

from __future__ import annotations

import hashlib
import os
import unittest
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("MADRID_PULSE_GTFS_SOURCE", str(ROOT / "tests" / "fixtures" / "gtfs_c5_real"))
os.environ.setdefault(
    "MADRID_PULSE_OSM_RELATION",
    str(ROOT / "tests" / "fixtures" / "osm_c5_real" / "relation_3418150.json"),
)

from apps.api import db, service, snapshot  # noqa: E402
from apps.api.config import ApiConfig  # noqa: E402
from apps.api.gtfs_source import load_network  # noqa: E402
from apps.api.main import app  # noqa: E402
from packages.contracts.canonical import (  # noqa: E402
    TripUpdateObservation,
    VehiclePositionObservation,
)
from packages.geo import point_at_arc_length  # noqa: E402
from services.collector import db as collector_db  # noqa: E402
from tests.clock import api_wall_clock  # noqa: E402
from tests.postgres import connect_disposable_or_skip  # noqa: E402

MADRID = ZoneInfo("Europe/Madrid")
TRIP_ID = "1022J19502C5"
"""Trip real de la fixture reducida (`10T0017C5`), con calendario de un solo
día: `2026-11-19` (ver `ResolvedTripEndToEndTests` de MP-017)."""
SERVICE_DATE = date(2026, 11, 19)
ATOCHA = "18000"


def _instant(seconds: float) -> datetime:
    midnight = datetime.combine(SERVICE_DATE, time.min, tzinfo=MADRID).astimezone(timezone.utc)
    return midnight + timedelta(seconds=seconds)


class CountingConnection:
    """Proxy que cuenta `execute` reales, para probar la ausencia de N+1."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn
        self.executed: list[str] = []

    def cursor(self, *args, **kwargs):
        inner = self._conn.cursor(*args, **kwargs)
        executed = self.executed

        class _Cursor:
            def __enter__(self_inner):
                inner.__enter__()
                return self_inner

            def __exit__(self_inner, *exc):
                return inner.__exit__(*exc)

            def execute(self_inner, query, *params, **kw):
                executed.append(str(query).strip().split("\n")[0][:60])
                return inner.execute(query, *params, **kw)

            def fetchall(self_inner):
                return inner.fetchall()

            def fetchone(self_inner):
                return inner.fetchone()

        return _Cursor()

    def rollback(self) -> None:
        self._conn.rollback()


class NetworkFixtureMixin:
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = ApiConfig.from_env()
        cls.network = load_network(cls.config)
        cls.coverage = snapshot.coverage_for_trip(
            cls.network, TRIP_ID, cls.network.topology.resolve_trip_route_id(TRIP_ID)
        )
        assert cls.coverage is not None and cls.coverage.can_map_match
        cls.engine = cls.network.engine_for(cls.coverage)
        cls.schedule = cls.engine.trip_schedule(TRIP_ID)
        cls.polyline = list(cls.coverage.corridor.segments[0])

    def observation_on_corridor(
        self, *, at: datetime, progress_m: float, vehicle_id: str = "snapshot-test"
    ) -> VehiclePositionObservation:
        lat, lon = point_at_arc_length(self.polyline, self.schedule.physical_arc(progress_m))
        return VehiclePositionObservation(
            source_vehicle_id=vehicle_id,
            source_trip_id=TRIP_ID,
            observed_at=at,
            latitude=lat,
            longitude=lon,
            raw_vehicle_label="synthetic deterministic snapshot contract test",
            payload_hash=hashlib.sha256(f"{vehicle_id}{at}".encode()).hexdigest(),
        )

    def history(
        self, latest: VehiclePositionObservation, *, received_at: datetime, published_at=None
    ) -> db.VehicleHistory:
        return db.VehicleHistory(
            source_vehicle_id=latest.source_vehicle_id,
            latest=db.ObservedRow(
                position=latest, received_at=received_at, feed_published_at=published_at
            ),
            previous=None,
        )

    def vehicle_entry(
        self,
        latest: VehiclePositionObservation,
        *,
        now: datetime,
        trip_update: TripUpdateObservation | None = None,
        display_at: datetime | None = None,
    ):
        return snapshot.build_vehicle_entry(
            self.network,
            self.config,
            self.history(latest, received_at=now, published_at=now),
            trip_update,
            now,
            display_at or now,
            self.network.service_date_resolver(now),
        )


class RawMatchedRenderedTests(NetworkFixtureMixin, unittest.TestCase):
    """Las tres coordenadas del anexo, separadas y con procedencia."""

    def test_three_coordinates_are_distinct_blocks_with_their_own_provenance(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        now = anchor_at + timedelta(seconds=10)
        # Punto bruto desplazado del eje: la proyección debe ser distinta.
        on_axis = self.observation_on_corridor(
            at=anchor_at, progress_m=self.schedule.points[5].progress_m
        )
        latest = on_axis.model_copy(update={"latitude": on_axis.latitude + 0.0005})
        entry = self.vehicle_entry(latest, now=now)

        self.assertEqual(entry.raw.lat, latest.latitude)
        self.assertEqual(entry.raw.gps_observed_at, anchor_at)
        self.assertEqual(entry.raw.payload_hash, latest.payload_hash)

        self.assertIsNotNone(entry.map_matched)
        self.assertEqual(entry.map_matched.resolution, "map_matched")
        self.assertGreater(entry.map_matched.distance_from_raw_m, 0.0)
        self.assertNotEqual(entry.map_matched.lat, entry.raw.lat)
        self.assertEqual(entry.map_matched.geometry_version, self.coverage.geometry_version)

        self.assertEqual(entry.rendered.coordinate_space, "map_matched")
        self.assertEqual(entry.rendered.anchor_observed_at, anchor_at)
        self.assertEqual(entry.rendered.geometry_version, self.coverage.geometry_version)
        self.assertIsNone(entry.rendered.geometry_candidate_version)
        # Compatibilidad: la vista de cuatro estados sigue publicada.
        self.assertEqual(entry.position.mode, "observed")

    def test_five_timestamps_are_published_separately(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        now = anchor_at + timedelta(seconds=10)
        published = anchor_at + timedelta(seconds=2)
        history = self.history(
            self.observation_on_corridor(
                at=anchor_at, progress_m=self.schedule.points[5].progress_m
            ),
            received_at=anchor_at + timedelta(seconds=3),
            published_at=published,
        )
        entry = snapshot.build_vehicle_entry(
            self.network,
            self.config,
            history,
            None,
            now,
            now - timedelta(seconds=4),
            self.network.service_date_resolver(now),
        )
        stamps = entry.timestamps
        self.assertEqual(stamps.gps_observed_at, anchor_at)
        self.assertEqual(stamps.received_at, anchor_at + timedelta(seconds=3))
        self.assertEqual(stamps.feed_published_at, published)
        self.assertEqual(stamps.snapshot_generated_at, now)
        self.assertEqual(stamps.display_at, now - timedelta(seconds=4))
        self.assertEqual(len({stamps.gps_observed_at, stamps.received_at, published, now}), 4)

    def test_absent_raw_position_never_becomes_zero_zero(self) -> None:
        """Observación sin posición pero con horario resoluble: `schedule_only`
        etiquetado, nunca `(0, 0)` ni un `map_matched` fabricado. `unlocated`
        queda para cuando tampoco hay horario (prueba siguiente)."""
        anchor_at = _instant(self.schedule.points[5].seconds)
        latest = self.observation_on_corridor(at=anchor_at, progress_m=0.0).model_copy(
            update={"latitude": None, "longitude": None}
        )
        entry = self.vehicle_entry(latest, now=anchor_at + timedelta(seconds=5))
        self.assertIsNone(entry.raw.lat)
        self.assertIsNone(entry.raw.lon)
        self.assertIsNone(entry.map_matched)
        self.assertEqual(entry.rendered.rendering_method, "schedule_only")
        self.assertEqual(entry.rendered.coordinate_space, "schedule")
        self.assertIsNone(entry.rendered.last_confirmed_at)
        self.assertIsNone(entry.rendered.geometry_version)
        self.assertEqual(entry.position.mode, "scheduled")
        self.assertTrue(entry.quality.stale)

    def test_unlocated_when_there_is_neither_position_nor_resolvable_schedule(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        latest = VehiclePositionObservation(
            source_vehicle_id="snapshot-unlocated",
            source_trip_id="SPECIAL_10_99998C2",
            observed_at=anchor_at,
            latitude=None,
            longitude=None,
            raw_vehicle_label="synthetic unlocated test",
            payload_hash="f" * 64,
        )
        entry = self.vehicle_entry(latest, now=anchor_at + timedelta(seconds=5))
        self.assertEqual(entry.rendered.rendering_method, "unlocated")
        self.assertIsNone(entry.rendered.lat)
        self.assertIsNone(entry.rendered.lon)
        self.assertIsNone(entry.rendered.coordinate_space)
        self.assertIsNone(entry.position)
        self.assertTrue(entry.quality.stale)

    def test_unresolvable_trip_keeps_raw_and_never_fabricates_a_pattern(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        latest = VehiclePositionObservation(
            source_vehicle_id="snapshot-unresolved",
            source_trip_id="SPECIAL_10_99999C2",
            observed_at=anchor_at,
            latitude=40.4,
            longitude=-3.7,
            raw_vehicle_label="synthetic unresolvable trip",
            payload_hash="b" * 64,
        )
        entry = self.vehicle_entry(latest, now=anchor_at + timedelta(seconds=5))
        self.assertIsNone(entry.route_id)
        self.assertIsNone(entry.pattern_id)
        self.assertIsNone(entry.map_matched)
        self.assertIsNone(entry.position)
        self.assertEqual(entry.circulation_status, "unresolved")
        self.assertEqual(entry.rendered.coordinate_space, "raw")
        self.assertEqual(entry.rendered.lat, 40.4)
        self.assertIsNone(entry.rendered.geometry_version)

    def test_delay_absent_is_null_and_declared_missing(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        latest = self.observation_on_corridor(
            at=anchor_at, progress_m=self.schedule.points[5].progress_m
        )
        entry = self.vehicle_entry(latest, now=anchor_at + timedelta(seconds=5))
        self.assertIsNone(entry.delay.seconds)
        self.assertEqual(entry.delay.coverage, "missing")
        self.assertIsNone(entry.delay.age_s)
        self.assertIsNone(entry.delay.source)
        self.assertFalse(entry.delay.expired)
        self.assertIsNone(entry.delay.approximation)

    def test_trip_level_delay_declares_its_approximation(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        now = anchor_at + timedelta(seconds=5)
        update = TripUpdateObservation(
            source_trip_id=TRIP_ID,
            observed_at=anchor_at,
            schedule_relationship=None,
            delay_seconds=184,
            delay_coverage="reported",
            next_stop_id=ATOCHA,
            payload_hash="c" * 64,
        )
        entry = self.vehicle_entry(
            self.observation_on_corridor(
                at=anchor_at, progress_m=self.schedule.points[5].progress_m
            ),
            now=now,
            trip_update=update,
        )
        self.assertEqual(entry.delay.seconds, 184)
        self.assertEqual(entry.delay.source, "operator_trip_update")
        self.assertEqual(entry.delay.approximation, "trip_level_delay_applied_to_all_stops")
        self.assertFalse(entry.delay.expired)

    def test_expired_operator_delay_is_published_with_its_age_not_applied(self) -> None:
        anchor_at = _instant(self.schedule.points[5].seconds)
        now = anchor_at + timedelta(seconds=5)
        update = TripUpdateObservation(
            source_trip_id=TRIP_ID,
            observed_at=now - timedelta(seconds=self.config.operator_delay_max_age_s + 60),
            schedule_relationship=None,
            delay_seconds=300,
            delay_coverage="reported",
            next_stop_id=None,
            payload_hash="d" * 64,
        )
        entry = self.vehicle_entry(
            self.observation_on_corridor(
                at=anchor_at, progress_m=self.schedule.points[5].progress_m
            ),
            now=now,
            trip_update=update,
        )
        self.assertTrue(entry.delay.expired)
        self.assertEqual(entry.delay.seconds, 300)
        self.assertGreater(entry.delay.age_s, self.config.operator_delay_max_age_s)


class EtaProvenanceTests(unittest.TestCase):
    """Cada caso del encargo con causa explícita, nunca un valor fabricado."""

    def setUp(self) -> None:
        self.now = _instant(20_000)
        self.scheduled_at = self.now + timedelta(minutes=10)

    def _update(self, **kwargs) -> TripUpdateObservation:
        base = dict(
            source_trip_id=TRIP_ID,
            observed_at=self.now,
            schedule_relationship=None,
            delay_seconds=None,
            delay_coverage="missing",
            next_stop_id=None,
            payload_hash="e" * 64,
        )
        base.update(kwargs)
        return TripUpdateObservation(**base)

    def test_missing_delay_falls_back_to_schedule_with_explicit_reason(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=self.scheduled_at,
            trip_update=None,
            now=self.now,
            max_age_s=600,
            relative=None,
        )
        self.assertEqual(eta.method, "schedule")
        self.assertEqual(eta.eta_at, self.scheduled_at)
        self.assertIsNone(eta.delay_seconds)
        self.assertEqual(eta.reason, "no_operator_delay_reported")

    def test_operator_delay_is_applied_on_schedule_and_declared(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=self.scheduled_at,
            trip_update=self._update(delay_seconds=120, delay_coverage="reported"),
            now=self.now,
            max_age_s=600,
            relative="after",
        )
        self.assertEqual(eta.method, "operator_delay_on_schedule")
        self.assertEqual(eta.eta_at, self.scheduled_at + timedelta(seconds=120))
        self.assertEqual(eta.approximation, "trip_level_delay_applied_to_all_stops")
        self.assertEqual(eta.delay_age_s, 0.0)

    def test_cancellation_removes_the_eta_and_keeps_the_schedule(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=self.scheduled_at,
            trip_update=self._update(schedule_relationship="CANCELED"),
            now=self.now,
            max_age_s=600,
            relative=None,
        )
        self.assertEqual(eta.method, "unavailable")
        self.assertIsNone(eta.eta_at)
        self.assertEqual(eta.scheduled_at, self.scheduled_at)
        self.assertEqual(eta.reason, "trip_canceled")

    def test_outdated_eta_is_not_applied_and_says_why(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=self.scheduled_at,
            trip_update=self._update(
                observed_at=self.now - timedelta(seconds=900),
                delay_seconds=240,
                delay_coverage="reported",
            ),
            now=self.now,
            max_age_s=600,
            relative=None,
        )
        self.assertEqual(eta.method, "schedule")
        self.assertEqual(eta.eta_at, self.scheduled_at)
        self.assertEqual(eta.reason, "operator_delay_expired")
        self.assertEqual(eta.delay_seconds, 240)
        self.assertEqual(eta.delay_age_s, 900.0)

    def test_a_stop_before_the_operator_next_stop_has_no_eta(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=self.scheduled_at,
            trip_update=self._update(delay_seconds=60, delay_coverage="reported", next_stop_id=ATOCHA),
            now=self.now,
            max_age_s=600,
            relative="before",
        )
        self.assertEqual(eta.method, "unavailable")
        self.assertIsNone(eta.eta_at)
        self.assertEqual(eta.reason, "passed_or_skipped_per_operator_next_stop")

    def test_missing_schedule_time_never_invents_an_eta(self) -> None:
        eta = snapshot.build_eta(
            scheduled_at=None,
            trip_update=self._update(delay_seconds=60, delay_coverage="reported"),
            now=self.now,
            max_age_s=600,
            relative=None,
        )
        self.assertEqual(eta.method, "unavailable")
        self.assertIsNone(eta.eta_at)
        self.assertEqual(eta.reason, "schedule_time_missing")


class CatalogContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.enterContext(api_wall_clock(datetime(2026, 11, 25, 12, tzinfo=timezone.utc)))
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_catalog_is_cacheable_by_representation_and_answers_304(self) -> None:
        response = self.client.get("/api/v1/catalog")
        self.assertEqual(response.status_code, 200)
        etag = response.headers["etag"]
        payload = response.json()
        self.assertEqual(
            etag,
            f'"{payload["catalog_version"]}.{payload["mode"]}.{payload["gtfs_status"]}.{payload["schema_version"]}"',
        )
        again = self.client.get("/api/v1/catalog", headers={"If-None-Match": etag})
        self.assertEqual(again.status_code, 304)

    def test_catalog_version_covers_gtfs_and_geometry(self) -> None:
        payload = self.client.get("/api/v1/catalog").json()
        network = load_network(ApiConfig.from_env())
        self.assertEqual(payload["gtfs_version"], network.gtfs_version)
        self.assertEqual(payload["geometry_catalog_version"], network.geometry_catalog_version)
        self.assertNotEqual(payload["gtfs_version"], payload["geometry_catalog_version"])
        self.assertNotEqual(payload["catalog_version"], payload["gtfs_version"])

    def test_physical_geometry_is_published_once_and_referenced(self) -> None:
        payload = self.client.get("/api/v1/catalog").json()
        versions = [item["geometry_version"] for item in payload["geometries"]]
        self.assertEqual(len(versions), len(set(versions)))
        referenced = {
            pattern["geometry"]["geometry_version"]
            for line in payload["lines"]
            for pattern in line["patterns"]
            if pattern["geometry"]["can_map_match"]
        }
        self.assertTrue(referenced)
        self.assertTrue(referenced.issubset(set(versions)))
        for geometry in payload["geometries"]:
            self.assertTrue(geometry["attribution"])
            self.assertGreater(geometry["length_m"], 0)
            self.assertTrue(all(len(segment) >= 2 for segment in geometry["segments"]))

    def test_coverage_is_honest_and_distance_is_null_without_a_corridor(self) -> None:
        payload = self.client.get("/api/v1/catalog").json()
        coverage = payload["coverage"]
        self.assertEqual(
            coverage["total_patterns"],
            coverage["validated"] + coverage["partial"] + coverage["pending"],
        )
        patterns = [pattern for line in payload["lines"] for pattern in line["patterns"]]
        self.assertEqual(len(patterns), coverage["total_patterns"])
        for pattern in patterns:
            can_match = pattern["geometry"]["can_map_match"]
            for station in pattern["stations"]:
                if can_match:
                    self.assertIsNotNone(station["distance_along_m"])
                else:
                    self.assertIsNone(
                        station["distance_along_m"],
                        "sin corredor validado no hay longitud de arco real: debe ser NULL",
                    )

    def test_catalog_carries_no_operational_state(self) -> None:
        body = self.client.get("/api/v1/catalog").text
        for forbidden in ("snapshot_id", "rendered", "delay", "gps_observed_at"):
            self.assertNotIn(forbidden, body)


class ReplayClockTests(unittest.TestCase):
    def setUp(self) -> None:
        connect_disposable_or_skip().close()
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_explicit_clock_is_accepted_in_replay(self) -> None:
        response = self.client.get("/api/v1/snapshot", params={"at": "2026-11-19T08:00:00Z"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["generated_at"], "2026-11-19T08:00:00Z")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_explicit_clock_is_rejected_outside_replay(self) -> None:
        network = load_network(ApiConfig.from_env())
        with self.assertRaisesRegex(ValueError, "solo se admite en modo replay"):
            snapshot.resolve_clock(
                ApiConfig.from_env(),
                replace(network, mode="live"),
                datetime(2026, 11, 19, 8, tzinfo=timezone.utc),
            )

    def test_naive_clock_is_rejected(self) -> None:
        network = load_network(ApiConfig.from_env())
        with self.assertRaisesRegex(ValueError, "zona horaria explícita"):
            snapshot.resolve_clock(ApiConfig.from_env(), network, datetime(2026, 11, 19, 8))


class SnapshotPostgresTests(NetworkFixtureMixin, unittest.TestCase):
    """Tres snapshots (normal/parcial/congelado), revisión y ausencia de N+1
    contra PostgreSQL real, siempre con `rollback`."""

    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        # Mantener el reloj dentro de la vigencia de la fixture C5.
        self.base = datetime(2026, 11, 25, 12, tzinfo=timezone.utc)

    def _ingest_vehicle(
        self,
        *,
        observed_at: datetime,
        started_at: datetime,
        progress_m: float,
        vehicle_id: str,
        source_timestamp: datetime | None = None,
    ) -> None:
        run_id = collector_db.insert_ingestion_run(
            self.conn,
            feed_name="vehicle_positions",
            source_timestamp=source_timestamp or observed_at,
            started_at=started_at,
            finished_at=started_at,
            status="ok",
            entity_count=1,
            payload_hash=hashlib.sha256(f"{vehicle_id}{observed_at}".encode()).hexdigest(),
        )
        collector_db.insert_vehicle_position_observation(
            self.conn,
            self.observation_on_corridor(
                at=observed_at, progress_m=progress_m, vehicle_id=vehicle_id
            ),
            received_at=started_at,
            ingestion_run_id=run_id,
            quality_flags=[],
        )

    def _ingest_feed_run(
        self, *, feed_name: str, started_at: datetime, status: str, source_timestamp=None
    ) -> int:
        return collector_db.insert_ingestion_run(
            self.conn,
            feed_name=feed_name,
            source_timestamp=source_timestamp,
            started_at=started_at,
            finished_at=started_at,
            status=status,
            entity_count=0 if status == "ok" else None,
            payload_hash=hashlib.sha256(f"{feed_name}{started_at}{status}".encode()).hexdigest(),
        )

    def test_three_snapshots_are_distinguished_and_none_rejuvenates_data(self) -> None:
        observed_at = self.base - timedelta(seconds=10)
        self._ingest_vehicle(
            observed_at=observed_at,
            started_at=self.base,
            progress_m=self.schedule.points[5].progress_m,
            vehicle_id="snapshot-normal",
        )
        self._ingest_feed_run(
            feed_name="trip_updates", started_at=self.base, status="ok", source_timestamp=self.base
        )
        self._ingest_feed_run(
            feed_name="alerts", started_at=self.base, status="ok", source_timestamp=self.base
        )

        normal = snapshot.build_snapshot(self.conn, self.network, self.config, self.base)
        self.assertTrue(normal.vehicles)
        ours = next(v for v in normal.vehicles if v.vehicle_id == "snapshot-normal")
        self.assertEqual(ours.timestamps.gps_observed_at, observed_at)
        self.assertEqual([d.resource for d in normal.degraded], [])

        # Parcial: `trip_updates` falla; `vehicle_positions` sigue bien y con
        # una ejecución NUEVA posterior. El recurso degradado no se vacía y la
        # edad del GPS no rejuvenece por el sondeo nuevo del otro feed.
        partial_at = self.base + timedelta(seconds=30)
        self._ingest_feed_run(
            feed_name="trip_updates", started_at=partial_at, status="error", source_timestamp=None
        )
        partial = snapshot.build_snapshot(self.conn, self.network, self.config, partial_at)
        degraded = {d.resource: d for d in partial.degraded}
        self.assertIn("delays_and_eta", degraded)
        self.assertEqual(degraded["delays_and_eta"].status, "error")
        self.assertEqual(
            len(partial.vehicles), len(normal.vehicles), "un fallo parcial no vacía vehículos"
        )
        partial_ours = next(v for v in partial.vehicles if v.vehicle_id == "snapshot-normal")
        self.assertEqual(
            partial_ours.timestamps.gps_observed_at,
            observed_at,
            "la observación conserva su timestamp de origen: nada la rejuvenece",
        )
        self.assertGreater(
            partial_ours.rendered.anchor_age_s,
            ours.rendered.anchor_age_s,
            "el ancla envejece de verdad entre snapshots",
        )

        # Congelado: colector detenido, el reloj avanza más allá del horizonte.
        frozen_at = self.base + timedelta(hours=1)
        frozen = snapshot.build_snapshot(self.conn, self.network, self.config, frozen_at)
        frozen_ours = next(v for v in frozen.vehicles if v.vehicle_id == "snapshot-normal")
        self.assertEqual(frozen_ours.rendered.rendering_method, "stale_frozen")
        self.assertIsNone(frozen_ours.rendered.progress_envelope)
        self.assertEqual(frozen_ours.rendered.last_confirmed_at, observed_at)
        self.assertTrue(frozen.vehicles, "congelado no es vacío: conserva el último dato válido")
        self.assertTrue(
            all(feed.status in {"stale", "error", "unknown"} for feed in frozen.feeds)
        )
        # Las dos particiones son cortes exactos del mismo total, no un mismo
        # criterio mezclado: una circulación congelada sobre el corredor cuenta
        # en `stale_frozen` y en `map_matched` a la vez, y cada diccionario
        # suma `vehicles_total`.
        self.assertEqual(
            sum(frozen.counts.by_rendering_method.values()), frozen.counts.vehicles_total
        )
        self.assertEqual(
            sum(frozen.counts.by_coordinate_space.values()), frozen.counts.vehicles_total
        )
        self.assertEqual(
            set(frozen.counts.by_rendering_method), {"stale_frozen"},
            "con el colector detenido y el horizonte agotado, todo queda congelado",
        )
        self.assertEqual(
            frozen_ours.rendered.progress_m,
            ours.map_matched.progress_m if ours.map_matched else None,
        )

    def test_revision_is_monotonic_in_scope_and_snapshot_id_is_content_identity(self) -> None:
        self._ingest_vehicle(
            observed_at=self.base - timedelta(seconds=5),
            started_at=self.base,
            progress_m=self.schedule.points[4].progress_m,
            vehicle_id="snapshot-rev-a",
        )
        first = snapshot.build_snapshot(self.conn, self.network, self.config, self.base)
        again = snapshot.build_snapshot(
            self.conn, self.network, self.config, self.base + timedelta(seconds=1)
        )
        self.assertEqual(
            first.snapshot_id,
            again.snapshot_id,
            "mismos datos, misma identidad: `snapshot_id` no es una marca de tiempo",
        )
        self.assertEqual(first.revision.sequence, again.revision.sequence)
        self.assertEqual(first.revision.scope, again.revision.scope)
        self.assertFalse(first.snapshot_id_is_sortable)
        self.assertEqual(first.revision.tiebreak, first.snapshot_id)

        self._ingest_vehicle(
            observed_at=self.base + timedelta(seconds=20),
            started_at=self.base + timedelta(seconds=25),
            progress_m=self.schedule.points[6].progress_m,
            vehicle_id="snapshot-rev-b",
        )
        newer = snapshot.build_snapshot(
            self.conn, self.network, self.config, self.base + timedelta(seconds=30)
        )
        self.assertNotEqual(newer.snapshot_id, first.snapshot_id)
        self.assertGreater(newer.revision.sequence, first.revision.sequence)
        self.assertEqual(newer.revision.scope, first.revision.scope)
        self.assertIn(
            newer.revision.scope_source, {"database_system_identifier", "database_oid"}
        )

    def test_a_lower_revision_is_detectable_as_out_of_order(self) -> None:
        """El cliente de MP-020 debe poder descartar una respuesta antigua: la
        comparación es `(scope, sequence)`, nunca el hash."""
        self._ingest_vehicle(
            observed_at=self.base - timedelta(seconds=5),
            started_at=self.base,
            progress_m=self.schedule.points[4].progress_m,
            vehicle_id="snapshot-order-a",
        )
        older = snapshot.build_snapshot(self.conn, self.network, self.config, self.base)
        self._ingest_vehicle(
            observed_at=self.base + timedelta(seconds=10),
            started_at=self.base + timedelta(seconds=12),
            progress_m=self.schedule.points[6].progress_m,
            vehicle_id="snapshot-order-b",
        )
        newer = snapshot.build_snapshot(
            self.conn, self.network, self.config, self.base + timedelta(seconds=15)
        )

        def supersedes(candidate, current) -> bool:
            if candidate.revision.scope != current.revision.scope:
                return False
            if candidate.revision.sequence != current.revision.sequence:
                return candidate.revision.sequence > current.revision.sequence
            return candidate.revision.generated_at > current.revision.generated_at

        self.assertTrue(supersedes(newer, older))
        self.assertFalse(supersedes(older, newer))
        self.assertFalse(
            supersedes(
                older.model_copy(
                    update={"revision": older.revision.model_copy(update={"scope": "pg:other"})}
                ),
                newer,
            ),
            "ámbitos distintos no se comparan por secuencia",
        )

    def test_snapshot_does_not_query_once_per_vehicle(self) -> None:
        for index in range(1, 7):
            self._ingest_vehicle(
                observed_at=self.base - timedelta(seconds=index),
                started_at=self.base,
                progress_m=self.schedule.points[index].progress_m,
                vehicle_id=f"snapshot-nplus1-{index}",
            )
        counting = CountingConnection(self.conn)
        snapshot.build_snapshot(counting, self.network, self.config, self.base)
        with_six = len(counting.executed)

        for index in range(7, 19):
            self._ingest_vehicle(
                observed_at=self.base - timedelta(seconds=index),
                started_at=self.base,
                progress_m=self.schedule.points[index % len(self.schedule.points)].progress_m,
                vehicle_id=f"snapshot-nplus1-{index}",
            )
        counting = CountingConnection(self.conn)
        result = snapshot.build_snapshot(counting, self.network, self.config, self.base)
        with_eighteen = len(counting.executed)

        self.assertGreaterEqual(result.counts.vehicles_total, 18)
        self.assertEqual(
            sum(result.counts.by_rendering_method.values()), result.counts.vehicles_total
        )
        self.assertEqual(
            sum(result.counts.by_coordinate_space.values()), result.counts.vehicles_total
        )
        self.assertEqual(
            with_six,
            with_eighteen,
            f"el número de consultas debe ser constante: {counting.executed}",
        )
        self.assertLessEqual(with_eighteen, 8)

    def test_live_vehicles_endpoint_also_lost_its_n_plus_one(self) -> None:
        for index in range(1, 5):
            self._ingest_vehicle(
                observed_at=self.base - timedelta(seconds=index),
                started_at=self.base,
                progress_m=self.schedule.points[index].progress_m,
                vehicle_id=f"legacy-nplus1-{index}",
            )
        counting = CountingConnection(self.conn)
        service.list_vehicles(counting, self.network, self.base)
        few = len(counting.executed)
        for index in range(5, 15):
            self._ingest_vehicle(
                observed_at=self.base - timedelta(seconds=index),
                started_at=self.base,
                progress_m=self.schedule.points[index % len(self.schedule.points)].progress_m,
                vehicle_id=f"legacy-nplus1-{index}",
            )
        counting = CountingConnection(self.conn)
        service.list_vehicles(counting, self.network, self.base)
        self.assertEqual(few, len(counting.executed))
        self.assertLessEqual(len(counting.executed), 3)

    def test_batch_trip_updates_return_the_same_row_as_the_single_query(self) -> None:
        observed_at = self.base - timedelta(seconds=30)
        run_id = self._ingest_feed_run(
            feed_name="trip_updates", started_at=observed_at, status="ok",
            source_timestamp=observed_at,
        )
        for delay in (60, 180):
            collector_db.insert_trip_update_observation(
                self.conn,
                TripUpdateObservation(
                    source_trip_id=TRIP_ID,
                    observed_at=observed_at + timedelta(seconds=delay),
                    schedule_relationship=None,
                    delay_seconds=delay,
                    delay_coverage="reported",
                    next_stop_id=None,
                    payload_hash=hashlib.sha256(f"tu{delay}".encode()).hexdigest(),
                ),
                received_at=observed_at + timedelta(seconds=delay),
                ingestion_run_id=run_id,
            )
        cutoff = self.base - timedelta(hours=20)
        single = db.latest_trip_update(self.conn, TRIP_ID, observed_after=cutoff)
        batch = db.latest_trip_updates(self.conn, [TRIP_ID, "nonexistent"], observed_after=cutoff)
        self.assertIsNotNone(single)
        self.assertEqual(batch[TRIP_ID].payload_hash, single.payload_hash)
        self.assertEqual(batch[TRIP_ID].delay_seconds, 180)
        self.assertNotIn("nonexistent", batch, "ausencia es ausencia, no retraso cero")


class StationBoardPostgresTests(NetworkFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        # Instante dentro del día de servicio real de la fixture.
        self.now = _instant(5 * 3600 + 20 * 60)

    def test_board_is_built_from_calendar_and_services_not_from_nearby_trains(self) -> None:
        board = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        self.assertIsNotNone(board)
        self.assertEqual(board.station_id, ATOCHA)
        self.assertEqual(board.service_date, SERVICE_DATE.isoformat())
        self.assertIn("gtfs_calendar", board.calculated_from)
        self.assertTrue(board.entries, "la fixture tiene servicios programados en esta franja")
        for entry in board.entries:
            self.assertTrue(entry.trip_id)
            self.assertEqual(entry.operator, "Renfe")
            self.assertIsNotNone(entry.scheduled_departure_at or entry.scheduled_arrival_at)
        # Sin observaciones insertadas: todo es "solo programado", nunca Live.
        self.assertTrue(
            all(entry.circulation_source == "scheduled_only" for entry in board.entries)
        )
        self.assertTrue(all(entry.vehicle_id is None for entry in board.entries))
        self.assertTrue(all(not entry.position_available for entry in board.entries))

    def test_board_entries_appear_even_without_any_gps(self) -> None:
        board = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        for entry in board.entries:
            self.assertEqual(entry.departure.method, "schedule")
            self.assertIsNotNone(entry.departure.scheduled_at)
            self.assertIsNone(entry.departure.delay_seconds)

    def test_board_coverage_is_null_when_the_denominator_is_zero(self) -> None:
        empty = snapshot.build_station_board(
            self.conn,
            self.network,
            self.config,
            ATOCHA,
            self.now,
            lookback_s=0,
            lookahead_s=0,
        )
        self.assertEqual(empty.entries, [])
        self.assertIsNone(
            empty.coverage.operator_delay_coverage_pct,
            "un porcentaje sin muestra es NULL, nunca 0.0 (DEC-009)",
        )

    def test_board_declares_the_skipped_limitation_instead_of_inventing_it(self) -> None:
        board = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        joined = " ".join(board.limitations)
        self.assertIn("stop_time_update", joined)
        self.assertIn("SKIPPED", joined)

    def test_observed_circulation_is_distinguished_from_scheduled_only(self) -> None:
        board = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        target = next(entry for entry in board.entries if entry.trip_id == TRIP_ID)
        self.assertEqual(target.circulation_source, "scheduled_only")

        run_id = collector_db.insert_ingestion_run(
            self.conn,
            feed_name="vehicle_positions",
            source_timestamp=self.now,
            started_at=self.now,
            finished_at=self.now,
            status="ok",
            entity_count=1,
            payload_hash=hashlib.sha256(b"board-observed").hexdigest(),
        )
        collector_db.insert_vehicle_position_observation(
            self.conn,
            self.observation_on_corridor(
                at=self.now, progress_m=self.schedule.points[5].progress_m,
                vehicle_id="board-observed",
            ),
            received_at=self.now,
            ingestion_run_id=run_id,
            quality_flags=[],
        )
        refreshed = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        target = next(entry for entry in refreshed.entries if entry.trip_id == TRIP_ID)
        self.assertEqual(target.circulation_source, "observed")
        self.assertEqual(target.vehicle_id, "board-observed")
        self.assertTrue(target.position_available)

    def test_cancellation_and_operator_next_stop_reach_the_board(self) -> None:
        run_id = collector_db.insert_ingestion_run(
            self.conn,
            feed_name="trip_updates",
            source_timestamp=self.now,
            started_at=self.now,
            finished_at=self.now,
            status="ok",
            entity_count=1,
            payload_hash=hashlib.sha256(b"board-canceled").hexdigest(),
        )
        collector_db.insert_trip_update_observation(
            self.conn,
            TripUpdateObservation(
                source_trip_id=TRIP_ID,
                observed_at=self.now,
                schedule_relationship="CANCELED",
                delay_seconds=None,
                delay_coverage="missing",
                next_stop_id=None,
                payload_hash=hashlib.sha256(b"board-canceled-tu").hexdigest(),
            ),
            received_at=self.now,
            ingestion_run_id=run_id,
        )
        board = snapshot.build_station_board(
            self.conn, self.network, self.config, ATOCHA, self.now
        )
        target = next(entry for entry in board.entries if entry.trip_id == TRIP_ID)
        self.assertEqual(target.schedule_relationship, "CANCELED")
        self.assertEqual(target.departure.method, "unavailable")
        self.assertEqual(target.departure.reason, "trip_canceled")
        self.assertIsNotNone(target.departure.scheduled_at)
        self.assertGreaterEqual(board.coverage.eta_unavailable, 1)

    def test_board_does_not_query_once_per_entry(self) -> None:
        counting = CountingConnection(self.conn)
        small = snapshot.build_station_board(
            counting, self.network, self.config, ATOCHA, self.now, limit=2
        )
        few = len(counting.executed)
        counting = CountingConnection(self.conn)
        large = snapshot.build_station_board(
            counting, self.network, self.config, ATOCHA, self.now, limit=20
        )
        self.assertGreater(len(large.entries), len(small.entries))
        self.assertEqual(few, len(counting.executed))

    def test_unknown_station_is_not_invented(self) -> None:
        self.assertIsNone(
            snapshot.build_station_board(
                self.conn, self.network, self.config, "does-not-exist", self.now
            )
        )


if __name__ == "__main__":
    unittest.main()


EXTENDED_FIXTURE = ROOT / "tests" / "fixtures" / "gtfs_24h_real"
EXTENDED_TRIP_C4 = "1023V20533C4"
"""C4 real, 23:50 -> 24:32, patrón `validated` contra la relación OSM 11332."""
EXTENDED_TRIP_C1 = "1023V19940C1"
"""C1 real, con paradas en 24:00 y 24:05; patrón sin geometría (`pending`)."""
EXTENDED_SERVICE_DATE = date(2026, 11, 20)
"""Único día programado de `1023V` (viernes), según su `calendar.txt`."""


class ExtendedHoursAfterMidnightTests(unittest.TestCase):
    """Regresión del segundo hallazgo bloqueante de la revisión de MP-019.

    A las `00:02` del 21 de noviembre, una circulación del día de servicio del
    20 con paradas a las `24:00`/`24:05` seguía siendo suya; resolver la fecha
    de servicio por reloj civil la mandaba al día siguiente, de modo que
    `service_seconds` pasaba de 86 520 a 120 y el motor situaba el tren a más
    de 10 km de su posición real, además de marcarlo `expired`.

    Usa la fixture real `tests/fixtures/gtfs_24h_real/` (dos circulaciones
    extraídas literalmente del ZIP oficial, ver su `MANIFEST.md`), no datos
    sintéticos.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = replace(
            ApiConfig.from_env(), gtfs_fixture_dir=EXTENDED_FIXTURE, short_name=""
        )
        cls.network = load_network(cls.config)
        cls.just_after_midnight = datetime(2026, 11, 21, 0, 2, tzinfo=MADRID).astimezone(
            timezone.utc
        )

    def test_the_horizon_comes_from_the_feed_not_from_a_magic_number(self) -> None:
        # El máximo real de la fixture es 24:32:00 -> 32 min por encima de 24 h.
        self.assertEqual(self.network.extended_service_horizon_s, 32 * 60.0)

    def test_a_24xx_trip_still_belongs_to_the_previous_service_day(self) -> None:
        resolver = self.network.service_date_resolver(self.just_after_midnight)
        self.assertEqual(resolver.primary, date(2026, 11, 21), "la fecha civil sigue siendo el 21")
        self.assertEqual(resolver.candidates, (EXTENDED_SERVICE_DATE, date(2026, 11, 21)))
        self.assertEqual(resolver.for_trip(EXTENDED_TRIP_C4), EXTENDED_SERVICE_DATE)
        self.assertEqual(resolver.for_trip(EXTENDED_TRIP_C1), EXTENDED_SERVICE_DATE)

    def test_outside_the_window_there_is_no_ambiguity_left(self) -> None:
        """A las 02:00 locales el horizonte del feed (24:32) ya no alcanza:
        la ventana se cierra y la fecha civil vuelve a ser la única."""
        late = datetime(2026, 11, 21, 2, 0, tzinfo=MADRID).astimezone(timezone.utc)
        resolver = self.network.service_date_resolver(late)
        self.assertEqual(resolver.candidates, (date(2026, 11, 21),))
        self.assertEqual(resolver.for_trip(EXTENDED_TRIP_C4), date(2026, 11, 21))

    def test_a_daytime_trip_of_the_new_civil_day_does_not_migrate_backwards(self) -> None:
        """La ventana no arrastra al día anterior cualquier circulación: solo
        aquellas cuyo horario publicado contiene realmente `now`."""
        midday = datetime(2026, 11, 20, 12, 0, tzinfo=MADRID).astimezone(timezone.utc)
        resolver = self.network.service_date_resolver(midday)
        self.assertEqual(resolver.candidates, (date(2026, 11, 20),))
        self.assertEqual(resolver.for_trip(EXTENDED_TRIP_C4), date(2026, 11, 20))

    def test_service_date_is_never_fabricated_for_an_unscheduled_day(self) -> None:
        """`1023V` solo está programado el 2026-11-20. A las 00:02 del 22 de
        noviembre (fuera de su calendario) no se inventa ninguna pertenencia."""
        later_night = datetime(2026, 11, 22, 0, 2, tzinfo=MADRID).astimezone(timezone.utc)
        resolver = self.network.service_date_resolver(later_night)
        self.assertEqual(resolver.candidates, (date(2026, 11, 21), date(2026, 11, 22)))
        self.assertEqual(
            resolver.for_trip(EXTENDED_TRIP_C4),
            date(2026, 11, 22),
            "sin servicio programado en ningún candidato, se conserva la fecha civil",
        )

    def test_position_of_a_24xx_trip_is_right_and_the_civil_date_is_wrong(self) -> None:
        from packages.geo import haversine_m
        from packages.movement import service_seconds

        coverage = snapshot.coverage_for_trip(
            self.network, EXTENDED_TRIP_C4, "10T0012C4"
        )
        self.assertIsNotNone(coverage)
        self.assertTrue(coverage.can_map_match, "el patrón C4 debe estar validado (relación 11332)")
        engine = self.network.engine_for(coverage)
        resolver = self.network.service_date_resolver(self.just_after_midnight)
        resolved = resolver.for_trip(EXTENDED_TRIP_C4)
        self.assertEqual(resolved, EXTENDED_SERVICE_DATE)

        self.assertEqual(service_seconds(self.just_after_midnight, resolved), 86_520.0)
        self.assertEqual(
            service_seconds(self.just_after_midnight, date(2026, 11, 21)), 120.0
        )

        correct = engine.position(
            trip_id=EXTENDED_TRIP_C4,
            service_date=resolved,
            calculated_at=self.just_after_midnight,
        )
        civil = engine.position(
            trip_id=EXTENDED_TRIP_C4,
            service_date=date(2026, 11, 21),
            calculated_at=self.just_after_midnight,
        )
        self.assertGreater(correct.progress_m, 12_000)
        self.assertLess(civil.progress_m, 100, "la fecha civil lo sitúa al inicio del recorrido")
        self.assertGreater(
            haversine_m(correct.latitude, correct.longitude, civil.latitude, civil.longitude),
            10_000,
            "el error del hallazgo era de más de 10 km: la regresión debe ser inequívoca",
        )

    def test_snapshot_entry_publishes_the_resolved_service_day_and_stays_active(self) -> None:
        coverage = snapshot.coverage_for_trip(self.network, EXTENDED_TRIP_C4, "10T0012C4")
        engine = self.network.engine_for(coverage)
        schedule = engine.trip_schedule(EXTENDED_TRIP_C4)
        polyline = list(coverage.corridor.segments[0])
        from packages.movement import service_seconds

        observed_at = self.just_after_midnight - timedelta(seconds=15)
        # La observación se sitúa donde el horario dice que estaba el tren en su
        # propio instante, para que el ancla sea físicamente coherente.
        progress = schedule.progress_at(service_seconds(observed_at, EXTENDED_SERVICE_DATE))
        lat, lon = point_at_arc_length(polyline, schedule.physical_arc(progress))
        latest = VehiclePositionObservation(
            source_vehicle_id="extended-hours-test",
            source_trip_id=EXTENDED_TRIP_C4,
            observed_at=observed_at,
            latitude=lat,
            longitude=lon,
            raw_vehicle_label="synthetic observation on a real 24:xx trip",
            payload_hash="1" * 64,
        )
        history = db.VehicleHistory(
            source_vehicle_id=latest.source_vehicle_id,
            latest=db.ObservedRow(
                position=latest, received_at=observed_at, feed_published_at=observed_at
            ),
            previous=None,
        )
        entry = snapshot.build_vehicle_entry(
            self.network,
            self.config,
            history,
            None,
            self.just_after_midnight,
            self.just_after_midnight,
            self.network.service_date_resolver(self.just_after_midnight),
        )
        self.assertEqual(entry.service_date, EXTENDED_SERVICE_DATE.isoformat())
        self.assertEqual(
            entry.circulation_status,
            "active",
            "una circulación 24:xW en curso no es `expired`: su servicio está programado el 20",
        )
        self.assertIsNotNone(entry.map_matched)
        self.assertGreater(entry.map_matched.progress_m, 12_000)
        self.assertEqual(entry.rendered.coordinate_space, "map_matched")


class ExtendedHoursBoardTests(unittest.TestCase):
    """El tablero tras medianoche no pierde las llamadas `24:xx` del día anterior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = replace(
            ApiConfig.from_env(), gtfs_fixture_dir=EXTENDED_FIXTURE, short_name=""
        )
        cls.network = load_network(cls.config)

    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.now = datetime(2026, 11, 21, 0, 2, tzinfo=MADRID).astimezone(timezone.utc)

    def _board(self, station_id: str, **kwargs):
        return snapshot.build_station_board(
            self.conn, self.network, self.config, station_id, self.now, **kwargs
        )

    def test_a_24xx_call_appears_with_its_own_service_date(self) -> None:
        board = self._board("98304", lookback_s=1800, lookahead_s=1800, limit=50)
        self.assertIsNotNone(board)
        self.assertEqual(board.service_date, "2026-11-21", "la fecha principal sigue siendo la civil")
        self.assertEqual(
            board.service_dates_considered, ["2026-11-20", "2026-11-21"]
        )
        entry = next(item for item in board.entries if item.trip_id == EXTENDED_TRIP_C1)
        self.assertEqual(entry.service_date, EXTENDED_SERVICE_DATE.isoformat())
        self.assertEqual(entry.scheduled_departure_time, "24:00:00")
        self.assertEqual(
            entry.scheduled_departure_at.astimezone(MADRID).isoformat(),
            "2026-11-21T00:00:00+01:00",
            "24:00 del día de servicio 20 es la medianoche del 21 en reloj de pared",
        )
        self.assertEqual(entry.circulation_source, "scheduled_only")
        self.assertEqual(entry.departure.method, "schedule")

    def test_the_second_extended_call_is_also_kept(self) -> None:
        board = self._board("98305", lookback_s=1800, lookahead_s=1800, limit=50)
        entry = next(item for item in board.entries if item.trip_id == EXTENDED_TRIP_C1)
        self.assertEqual(entry.scheduled_arrival_time, "24:05:00")
        self.assertEqual(
            entry.scheduled_arrival_at.astimezone(MADRID).isoformat(),
            "2026-11-21T00:05:00+01:00",
        )

    def test_extended_calls_are_not_duplicated_across_candidate_days(self) -> None:
        board = self._board("17000", lookback_s=3600, lookahead_s=3600, limit=200)
        keys = [(item.trip_id, item.stop_sequence, item.service_date) for item in board.entries]
        self.assertEqual(len(keys), len(set(keys)), "ninguna llamada aparece dos veces")
        self.assertEqual(board.coverage.returned, len(board.entries))

    def test_outside_the_window_the_board_considers_only_the_civil_day(self) -> None:
        board = snapshot.build_station_board(
            self.conn,
            self.network,
            self.config,
            "98304",
            datetime(2026, 11, 21, 2, 0, tzinfo=MADRID).astimezone(timezone.utc),
            lookback_s=1800,
            lookahead_s=1800,
        )
        self.assertEqual(board.service_dates_considered, ["2026-11-21"])
        self.assertEqual(board.entries, [])
        self.assertIsNone(board.coverage.operator_delay_coverage_pct)


class BoardWindowCoversItsCandidateServiceDaysTests(unittest.TestCase):
    """Regresión del tercer hallazgo bloqueante de la revisión de MP-019.

    Los días de servicio candidatos del tablero se calculaban **solo con
    `now`**, no con la ventana realmente pedida. En cuanto `now` rebasaba el
    horizonte de horas extendidas del feed, el tablero dejaba de consultar el
    día anterior aunque `lookback_s` todavía lo cubriera: la llamada real de las
    `24:32` (las `00:32` en reloj de pared) aparecía a las `00:32` y
    **desaparecía a las `00:33`**, un minuto después de ocurrir y con 600 s de
    retrospectiva solicitados.

    El mismo error existía en el sentido contrario, y también se prueba aquí: la
    ventana hacia delante no consultaba el día de servicio siguiente.
    """

    EXTENDED_CALL_WALL_CLOCK = "00:32"
    """Reloj de pared de la llamada `24:32` de `1023V20533C4` en la estación
    `17000`, el día de servicio 2026-11-20."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = replace(
            ApiConfig.from_env(), gtfs_fixture_dir=EXTENDED_FIXTURE, short_name=""
        )
        cls.network = load_network(cls.config)

    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)

    def _board_at(self, hour: int, minute: int, **kwargs):
        now = datetime(2026, 11, 21, hour, minute, tzinfo=MADRID).astimezone(timezone.utc)
        return snapshot.build_station_board(
            self.conn, self.network, self.config, "17000", now, **kwargs
        )

    def test_the_exact_minute_where_the_call_used_to_disappear(self) -> None:
        """`00:33` con `lookback_s=600`: el minuto exacto del hallazgo."""
        board = self._board_at(0, 33, lookback_s=600, lookahead_s=600, limit=50)
        self.assertIn(
            EXTENDED_SERVICE_DATE.isoformat(),
            board.service_dates_considered,
            "la ventana de 600 s sigue alcanzando el día de servicio anterior",
        )
        entry = next(
            (item for item in board.entries if item.trip_id == EXTENDED_TRIP_C4), None
        )
        self.assertIsNotNone(
            entry,
            "la llamada de las 24:32 ocurrió hace un minuto: debe seguir en el tablero",
        )
        self.assertEqual(entry.service_date, EXTENDED_SERVICE_DATE.isoformat())
        self.assertEqual(entry.scheduled_departure_time, "24:32:00")
        self.assertEqual(
            entry.scheduled_departure_at.astimezone(MADRID).isoformat(),
            "2026-11-21T00:32:00+01:00",
        )

    def test_the_call_survives_exactly_as_long_as_the_requested_lookback(self) -> None:
        """Minuto a minuto: la llamada de las `00:32` con `lookback_s=600` debe
        verse hasta las `00:42` inclusive y desaparecer a las `00:43`, es decir
        en el borde de la **ventana pedida**, no en el del horizonte del feed
        (que con esta fixture se agota a las `00:32`)."""
        self.assertEqual(
            self.network.extended_service_horizon_s,
            32 * 60.0,
            "el horizonte del feed se agota justo en la llamada: es lo que hacía visible el fallo",
        )
        for minute in range(31, 43):
            with self.subTest(minute=minute):
                board = self._board_at(0, minute, lookback_s=600, lookahead_s=600, limit=50)
                self.assertIn(
                    EXTENDED_TRIP_C4,
                    {item.trip_id for item in board.entries},
                    f"a las 00:{minute:02d} la llamada sigue dentro de los 600 s pedidos",
                )
        board = self._board_at(0, 43, lookback_s=600, lookahead_s=600, limit=50)
        self.assertNotIn(
            EXTENDED_TRIP_C4,
            {item.trip_id for item in board.entries},
            "a las 00:43 la llamada ya salió de la ventana de 600 s: debe desaparecer",
        )

    def test_a_shorter_lookback_drops_it_earlier_as_requested(self) -> None:
        """La ventana manda: con `lookback_s=60` la misma llamada solo sobrevive
        un minuto, y con `lookback_s=0` desaparece en cuanto pasa."""
        self.assertIn(
            EXTENDED_TRIP_C4,
            {item.trip_id for item in self._board_at(0, 33, lookback_s=60, lookahead_s=600).entries},
        )
        self.assertNotIn(
            EXTENDED_TRIP_C4,
            {item.trip_id for item in self._board_at(0, 34, lookback_s=60, lookahead_s=600).entries},
        )

    def test_the_forward_window_also_reaches_the_next_service_day(self) -> None:
        """Lado simétrico: a las `23:55` del 19, con anticipación suficiente, el
        tablero consulta el día de servicio del 20 y publica su llamada real de
        las `23:50`, que de otro modo quedaba fuera de los candidatos."""
        now = datetime(2026, 11, 19, 23, 55, tzinfo=MADRID).astimezone(timezone.utc)
        board = snapshot.build_station_board(
            self.conn,
            self.network,
            self.config,
            "17000",
            now,
            lookback_s=600,
            lookahead_s=86_400,
            limit=50,
        )
        self.assertIn("2026-11-20", board.service_dates_considered)
        entry = next(
            (item for item in board.entries if item.trip_id == EXTENDED_TRIP_C1), None
        )
        self.assertIsNotNone(entry, "la llamada del día de servicio siguiente debe aparecer")
        self.assertEqual(entry.service_date, "2026-11-20")
        self.assertEqual(entry.scheduled_departure_time, "23:50:00")

    def test_calls_of_two_service_days_are_ordered_by_absolute_instant(self) -> None:
        board = self._board_at(0, 33, lookback_s=3600, lookahead_s=3600, limit=100)
        instants = [
            item.scheduled_departure_at or item.scheduled_arrival_at for item in board.entries
        ]
        self.assertEqual(instants, sorted(instants), "mezclar días de servicio no rompe el orden")
        keys = [(item.trip_id, item.stop_sequence, item.service_date) for item in board.entries]
        self.assertEqual(len(keys), len(set(keys)))


class ServiceDatesCoveringTests(unittest.TestCase):
    """`service_dates_covering` como función pura, sin base de datos."""

    HORIZON = 32 * 60.0
    """El de `tests/fixtures/gtfs_24h_real/` (máximo real `24:32`)."""

    def _covering(self, start: datetime, end: datetime, horizon: float | None = None):
        return [
            item.isoformat()
            for item in service.service_dates_covering(
                start, end, extended_horizon_s=self.HORIZON if horizon is None else horizon
            )
        ]

    def test_a_degenerate_window_matches_the_per_trip_resolver(self) -> None:
        """Con `start == end` la cobertura es exactamente la del resolver de una
        circulación, que es como se usa en el snapshot."""
        for hour, minute, expected in (
            (0, 2, ["2026-11-20", "2026-11-21"]),
            (0, 32, ["2026-11-20", "2026-11-21"]),
            (0, 33, ["2026-11-21"]),
            (12, 0, ["2026-11-21"]),
        ):
            instant = datetime(2026, 11, 21, hour, minute, tzinfo=MADRID).astimezone(timezone.utc)
            with self.subTest(at=f"{hour:02d}:{minute:02d}"):
                self.assertEqual(self._covering(instant, instant), expected)

    def test_the_lookback_edge_extends_the_coverage_backwards(self) -> None:
        now = datetime(2026, 11, 21, 0, 33, tzinfo=MADRID).astimezone(timezone.utc)
        self.assertEqual(self._covering(now, now), ["2026-11-21"])
        self.assertEqual(
            self._covering(now - timedelta(seconds=600), now),
            ["2026-11-20", "2026-11-21"],
        )

    def test_the_lookahead_edge_extends_the_coverage_forwards(self) -> None:
        now = datetime(2026, 11, 20, 23, 55, tzinfo=MADRID).astimezone(timezone.utc)
        self.assertEqual(self._covering(now, now), ["2026-11-20"])
        self.assertEqual(
            self._covering(now, now + timedelta(seconds=600)),
            ["2026-11-20", "2026-11-21"],
        )

    def test_a_feed_without_extended_hours_has_no_overlap(self) -> None:
        """Sin horas `24:xx` el horizonte es `0.0` y cada día de servicio
        termina en su propia medianoche: no hay solape que cubrir."""
        instant = datetime(2026, 11, 21, 0, 2, tzinfo=MADRID).astimezone(timezone.utc)
        self.assertEqual(self._covering(instant, instant, horizon=0.0), ["2026-11-21"])

    def test_inverted_windows_are_tolerated(self) -> None:
        start = datetime(2026, 11, 21, 0, 33, tzinfo=MADRID).astimezone(timezone.utc)
        end = start - timedelta(seconds=600)
        self.assertEqual(self._covering(start, end), self._covering(end, start))

    def test_coverage_is_computed_with_real_offsets_on_both_dst_dates(self) -> None:
        """Los límites de cada día de servicio se calculan con
        `service_day_instant`, así que un día de 23 h o de 25 h se cubre con su
        duración real y no con un offset fijo."""
        # Adelanto: el día de servicio 2026-03-29 dura 23 h de reloj real, así
        # que su horizonte extendido alcanza menos lejos en tiempo absoluto.
        spring_night = datetime(2026, 3, 30, 0, 20, tzinfo=MADRID).astimezone(timezone.utc)
        self.assertEqual(
            self._covering(spring_night, spring_night), ["2026-03-29", "2026-03-30"]
        )
        # Atraso: el día 2026-10-25 dura 25 h reales.
        autumn_night = datetime(2026, 10, 26, 0, 20, tzinfo=MADRID).astimezone(timezone.utc)
        self.assertEqual(
            self._covering(autumn_night, autumn_night), ["2026-10-25", "2026-10-26"]
        )
