"""Cortes Renfe reducidos. Todas las posiciones se calculan desde GPS bruto."""

import json
import hashlib
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from apps.api import db, snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import haversine_m
from packages.movement.schedule import service_day_instant

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DATA = FIXTURES / "mp025a"


def observations(cut):
    feed = RawVehiclePositionsFeed.model_validate_json((DATA / f"{cut}.json").read_bytes())
    return {p.source_vehicle_id: p for p in vehicle_positions_to_canonical(feed)}


class RealStops(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = ApiConfig(
            "",
            "10",
            "",
            DATA / "gtfs.zip",
            FIXTURES / "osm_c5_real/relation_3418150.json",
            FIXTURES,
            180,
            "replay",
            600,
            0,
            DATA,
        )
        cls.network = load_network(cls.config)
        cls.first, cls.second = observations(1532), observations(1533)

    def entry(
        self, pos, prev=None, age=10, *, lag=0, base=None, update=None, network=None, profile=None
    ):
        network = network or self.network
        at = pos.observed_at + timedelta(seconds=age)
        row = db.ObservedRow(pos, pos.observed_at)
        if hasattr(row, "anchor_profile"):
            row = replace(
                row,
                ingestion_run_id=100,
                anchor_profile=profile
                or self.network.anchor_profile(self.network.engine.thresholds),
            )
            if update:
                row = replace(row, known_relationship=update.schedule_relationship, known_observed_at=update.observed_at)
            if base:
                row = replace(row, base_relationship=base[0], base_observed_at=base[1], base_run=99)
        hist = db.VehicleHistory(
            pos.source_vehicle_id, row, replace(row,position=prev,received_at=prev.observed_at) if prev else None
        )
        return snapshot.build_vehicle_entry(
            network,
            self.config,
            hist,
            update,
            at,
            at - timedelta(seconds=lag),
            network.service_date_resolver(at),
        )

    def test_fixture_integrity(self):
        manifest = json.loads((DATA / "manifest.json").read_text())
        for name, digest in manifest["fixtures"].items():
            self.assertEqual(hashlib.sha256((DATA / name).read_bytes()).hexdigest(), digest)

    def test_real_cohorts(self):
        counts = {name: [] for name in ("M1", "M2", "M2b", "M3", "M4", "M5", "M6", "M7")}
        for vid, pos in self.second.items():
            prev = self.first[vid]
            item = self.entry(pos, prev)
            env = item.rendered.progress_envelope
            route = self.network.topology.resolve_trip_route_id(pos.source_trip_id)
            cov = snapshot.coverage_for_trip(self.network, pos.source_trip_id, route)
            schedule = self.network.engine_for(cov).trip_schedule(pos.source_trip_id)
            times = self.network.topology.stop_times_for_trip(pos.source_trip_id)
            start = service_day_instant(pos.observed_at.date(), schedule.points[0].seconds)
            end = service_day_instant(pos.observed_at.date(), schedule.points[-1].seconds)
            stopped = pos.current_status == "STOPPED_AT"
            moving = env.speed_mps > 0
            if stopped and (prev.latitude, prev.longitude) == (pos.latitude, pos.longitude):
                counts["M1"].append(moving)
            if pos.observed_at < start:
                self.assertTrue(stopped)
                counts["M2"].append(moving)
                until = min(start, item.rendered.valid_until)
                counts["M2b"].append(moving and until > (env.dwell_until or env.reference_at))
            if (
                stopped
                and pos.current_stop_id == times[0].stop_id
                and start <= pos.observed_at <= end
            ):
                counts["M3"].append(moving)
            if stopped and pos.current_stop_id != times[0].stop_id:
                counts["M4"].append(moving)
            counts["M5"].append(
                any(
                    env.progress_m_at_reference + 50 < p.progress_m < env.max_progress_m
                    for p in schedule.points
                )
            )
            if vid == "19656":
                counts["M6"].append(
                    self.entry(pos, prev, 30).rendered.progress_m != env.progress_m_at_reference
                )
            prev_env = self.entry(prev).rendered.progress_envelope
            if (
                prev.current_status in ("IN_TRANSIT_TO", "INCOMING_AT")
                and env.progress_m_at_reference - prev_env.progress_m_at_reference >= 100
            ):
                counts["M7"].append(
                    self.entry(prev, age=77).rendered.progress_m == prev_env.progress_m_at_reference
                )
        for name, total in zip(counts, (25, 17, 17, 4, 7, 44, 1, 9)):
            with self.subTest(name=name):
                self.assertEqual((sum(counts[name]), len(counts[name])), (0, total))

    def test_f1_and_one_coordinate(self):
        maximum = 0.0
        samples = 0
        for vid, pos in self.second.items():
            prev = self.first[vid]
            route = self.network.topology.resolve_trip_route_id(pos.source_trip_id)
            cov = snapshot.coverage_for_trip(self.network, pos.source_trip_id, route)
            schedule = self.network.engine_for(cov).trip_schedule(pos.source_trip_id)
            if (
                service_day_instant(pos.observed_at.date(), schedule.points[0].seconds)
                <= pos.observed_at
                <= service_day_instant(pos.observed_at.date(), schedule.points[-1].seconds)
            ):
                for age in range(61, 180):
                    data = self.entry(pos, prev, age).model_dump(mode="json")
                    p, r = data["position"], data["rendered"]
                    self.assertEqual(p["mode"], "estimated")
                    maximum = max(maximum, haversine_m(p["lat"], p["lon"], r["lat"], r["lon"]))
                    samples += 1
            end = self.entry(pos, prev, 180)
            frozen = self.entry(pos, prev, 181)
            with self.subTest(vid=vid):
                self.assertEqual(frozen.rendered.progress_m, end.rendered.progress_m)
            maximum = max(
                maximum,
                haversine_m(
                    frozen.position.lat,
                    frozen.position.lon,
                    frozen.rendered.lat,
                    frozen.rendered.lon,
                ),
            )
        self.assertEqual(samples, 2975)
        self.assertLessEqual(maximum, 0.01)

    def test_stop_state_uses_effective_observation_and_branches(self):
        from packages.contracts.canonical import TripUpdateObservation

        pos, prev = self.second["19664"], self.first["19664"]
        jumped = pos.model_copy(
            update=dict(latitude=pos.latitude + 0.27, current_status="STOPPED_AT")
        )
        rendered = self.entry(jumped, prev).rendered
        self.assertEqual(rendered.anchor_observed_at, prev.observed_at)
        self.assertEqual(rendered.stop_state.operator_status, prev.current_status)
        self.assertGreater(rendered.progress_envelope.speed_mps, 0)
        # Con el mismo reloj de origen el motor puede aceptar latest si previous
        # no tiene coordenadas. El estado se desempata por el payload efectivo.
        no_fix = prev.model_copy(update=dict(observed_at=pos.observed_at, latitude=None,
                                             longitude=None, current_status="STOPPED_AT"))
        tied = self.entry(pos, no_fix)
        self.assertEqual(tied.rendered.stop_state.operator_status, pos.current_status)
        pos = self.second["20849"]
        cancel = TripUpdateObservation(
            source_trip_id=pos.source_trip_id,
            observed_at=pos.observed_at,
            schedule_relationship="CANCELED",
            delay_coverage="missing",
            payload_hash="a" * 64,
        )
        missing = pos.model_copy(update=dict(latitude=None, longitude=None))
        self.assertEqual(self.entry(missing).rendered.rendering_method, "schedule_only")
        self.assertIsNone(self.entry(missing).rendered.stop_state.coherent)
        self.assertEqual(self.entry(missing, update=cancel).rendered.reason, "trip_canceled")
        unknown = pos.model_copy(update=dict(source_trip_id="10unknown"))
        raw = self.entry(unknown, update=cancel)
        self.assertEqual(
            (raw.rendered.coordinate_space, raw.schedule_relationship), ("raw", "CANCELED")
        )
        self.assertEqual((raw.rendered.lat, raw.rendered.lon), (pos.latitude, pos.longitude))
        interp = self.entry(self.second["19656"], self.first["19656"], lag=40)
        self.assertEqual(interp.rendered.rendering_method, "interpolated_between_known_anchors")

    def test_profile_mismatch(self):
        pos = self.second["19667"]
        net = self.network
        for gtfs, geom, threshold in (
            ("v2", net.geometry_catalog_version, net.engine.thresholds),
            (net.gtfs_version, "v2", net.engine.thresholds),
            (
                net.gtfs_version,
                net.geometry_catalog_version,
                replace(net.engine.thresholds, min_dwell_s=31),
            ),
        ):
            other = replace(net, gtfs_version=gtfs).anchor_profile(threshold)
            if geom != net.geometry_catalog_version:
                version, parameters, geometries = json.loads(other)
                other = json.dumps([version, parameters, dict.fromkeys(geometries, geom)])
            r = self.entry(pos, age=181, profile=other).rendered
            self.assertEqual(r.frozen_basis, "anchor_version_changed")
            self.assertEqual(r.progress_m, r.last_confirmed_progress_m)


class RecoveryMeasurement(unittest.TestCase):
    def test_recovery_relative_to_engine_estimate(self):
        from tests.e2e import test_mp022_synthetic_derived as mp022

        case = mp022.SyntheticDerivedRecoveryAcceptanceTests()
        case.setUpClass()
        f = case.fixture
        point = case.schedule.points[f["old_anchor_schedule_point_index"]]
        at = case.instant(point.seconds)
        old = case.observation(at=at, progress_m=point.progress_m, suffix="a")
        now = at + timedelta(seconds=f["estimated_after_s"])
        movement = case.engine.position(
            trip_id=f["trip_id"], service_date=case.service_date, calculated_at=now, latest=old
        )
        before = case.render(movement, now)
        recovered_at = at + timedelta(seconds=f["recovered_after_s"])
        gps = case.observation(
            at=recovered_at,
            progress_m=movement.progress_m + f["recovery_ahead_of_estimate_m"],
            suffix="b",
        )
        after_at = recovered_at + timedelta(seconds=1)
        recovered = case.engine.position(
            trip_id=f["trip_id"],
            service_date=case.service_date,
            calculated_at=after_at,
            latest=gps,
            previous=old,
        )
        jump = case.render(recovered, after_at).progress_m - before.progress_m
        self.assertGreater(movement.progress_m, before.progress_m)
        self.assertGreater(jump, 0)
        print(f"MP-022 GPS relativo al motor, salto presentado: {jump:.6f} m")
