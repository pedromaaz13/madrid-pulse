"""Pipeline completo de ADR-0004, sin ocultar estimaciones como observaciones."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

from packages.contracts.canonical import VehiclePositionObservation, require_utc
from packages.geo import Corridor, point_at_arc_length
from packages.gtfs import Topology

from .model import (
    MapMatch,
    MovementAnomaly,
    MovementPosition,
    MovementSource,
    MovementThresholds,
    PositionMode,
)
from .schedule import TripSchedule, build_trip_schedule, service_seconds


class MovementEngine:
    def __init__(
        self,
        topology: Topology,
        corridor: Corridor,
        *,
        thresholds: MovementThresholds = MovementThresholds(),
    ) -> None:
        if not corridor.is_continuous or len(corridor.segments) != 1:
            raise ValueError("el motor requiere un corredor continuo para un trip")
        self.topology = topology
        self.corridor = corridor
        self.thresholds = thresholds

    def map_match(self, observation: VehiclePositionObservation) -> MapMatch | None:
        """Map-match público para diagnóstico e integración con observaciones reales."""
        if not observation.has_position:
            return None
        assert observation.latitude is not None and observation.longitude is not None
        projection, arc_m = self.corridor.project_station(
            observation.latitude, observation.longitude
        )
        return MapMatch(
            latitude=projection.lat,
            longitude=projection.lon,
            physical_arc_m=arc_m,
            distance_from_track_m=projection.distance_m,
        )

    def position(
        self,
        *,
        trip_id: str,
        service_date: date,
        calculated_at: datetime,
        latest: VehiclePositionObservation | None = None,
        previous: VehiclePositionObservation | None = None,
        explicit_route_id: str | None = None,
    ) -> MovementPosition:
        require_utc(calculated_at)
        route_id = self.topology.resolve_trip_route_id(
            trip_id, explicit_route_id=explicit_route_id
        )
        if route_id is None:
            raise ValueError(f"trip_id no resoluble: {trip_id!r}")
        schedule = build_trip_schedule(self.topology, self.corridor, trip_id)
        now_s = service_seconds(calculated_at, service_date)

        if latest is None:
            return self._scheduled(
                trip_id, route_id, schedule, calculated_at, now_s, anomalies=()
            )
        if latest.source_trip_id != trip_id:
            raise ValueError("latest pertenece a otro trip")
        if previous is not None and previous.source_trip_id != trip_id:
            raise ValueError("previous pertenece a otro trip")
        age_s = (calculated_at - latest.observed_at).total_seconds()
        if age_s < 0:
            raise ValueError("latest está en el futuro respecto a calculated_at")

        latest_match = self.map_match(latest)
        previous_match = self.map_match(previous) if previous is not None else None
        anomalies = self._anomalies(
            trip_id, schedule, latest, latest_match, previous, previous_match
        )
        if latest_match is None or self._is_unusable(
            schedule, latest, latest_match, previous, previous_match
        ):
            # Una observación nueva imposible no borra la última posición
            # plausible. Reutilizamos explícitamente la anterior con su edad
            # real y conservamos los flags de la muestra rechazada.
            if previous is not None and previous.source_trip_id == trip_id:
                fallback = self.position(
                    trip_id=trip_id,
                    service_date=service_date,
                    calculated_at=calculated_at,
                    latest=previous,
                    explicit_route_id=explicit_route_id,
                )
                return replace(fallback, anomalies=anomalies + fallback.anomalies)
            return self._scheduled(
                trip_id,
                route_id,
                schedule,
                calculated_at,
                now_s,
                anomalies=anomalies,
                unusable_age_s=age_s,
                unusable_observed_at=latest.observed_at,
            )

        latest_progress = schedule.directed_progress(latest_match.physical_arc_m)
        if age_s <= self.thresholds.observed_max_age_s:
            confidence = 1.0 - 0.25 * age_s / max(self.thresholds.observed_max_age_s, 1.0)
            return MovementPosition(
                trip_id=trip_id,
                route_id=route_id,
                latitude=latest_match.latitude,
                longitude=latest_match.longitude,
                progress_m=latest_progress,
                position_mode=PositionMode.OBSERVED,
                confidence=confidence,
                age_s=age_s,
                source=MovementSource.VEHICLE_POSITION,
                calculated_at=calculated_at,
                observed_at=latest.observed_at,
                anomalies=anomalies,
            )
        if age_s > self.thresholds.stale_after_s:
            return MovementPosition(
                trip_id=trip_id,
                route_id=route_id,
                latitude=latest_match.latitude,
                longitude=latest_match.longitude,
                progress_m=latest_progress,
                position_mode=PositionMode.STALE,
                confidence=max(0.0, 0.2 * self.thresholds.stale_after_s / age_s),
                age_s=age_s,
                source=MovementSource.LAST_VEHICLE_POSITION,
                calculated_at=calculated_at,
                observed_at=latest.observed_at,
                anomalies=anomalies,
            )

        observed_s = service_seconds(latest.observed_at, service_date)
        scheduled_at_observation = schedule.seconds_at_progress(latest_progress)
        temporal_offset_s = observed_s - scheduled_at_observation
        desired = schedule.progress_at(now_s - temporal_offset_s)
        progress = self._limit_estimate(
            desired=desired,
            latest_progress=latest_progress,
            age_s=age_s,
            latest=latest,
            previous=previous,
            schedule=schedule,
            latest_match=latest_match,
            previous_match=previous_match,
        )
        lat, lon = point_at_arc_length(
            list(self.corridor.segments[0]), schedule.physical_arc(progress)
        )
        window = self.thresholds.stale_after_s - self.thresholds.observed_max_age_s
        decay = (age_s - self.thresholds.observed_max_age_s) / window
        return MovementPosition(
            trip_id=trip_id,
            route_id=route_id,
            latitude=lat,
            longitude=lon,
            progress_m=progress,
            position_mode=PositionMode.ESTIMATED,
            confidence=0.75 - 0.5 * decay,
            age_s=age_s,
            source=MovementSource.VEHICLE_POSITION_AND_SCHEDULE,
            calculated_at=calculated_at,
            observed_at=latest.observed_at,
            anomalies=anomalies,
        )

    def _scheduled(
        self,
        trip_id: str,
        route_id: str,
        schedule: TripSchedule,
        calculated_at: datetime,
        now_s: float,
        *,
        anomalies: tuple[MovementAnomaly, ...],
        unusable_age_s: float | None = None,
        unusable_observed_at: datetime | None = None,
    ) -> MovementPosition:
        progress = schedule.progress_at(now_s)
        lat, lon = point_at_arc_length(
            list(self.corridor.segments[0]), schedule.physical_arc(progress)
        )
        return MovementPosition(
            trip_id=trip_id,
            route_id=route_id,
            latitude=lat,
            longitude=lon,
            progress_m=progress,
            position_mode=PositionMode.SCHEDULED,
            confidence=0.2,
            age_s=unusable_age_s,
            source=MovementSource.SCHEDULE,
            calculated_at=calculated_at,
            observed_at=unusable_observed_at,
            anomalies=anomalies,
        )

    def _anomalies(
        self,
        trip_id: str,
        schedule: TripSchedule,
        latest: VehiclePositionObservation,
        latest_match: MapMatch | None,
        previous: VehiclePositionObservation | None,
        previous_match: MapMatch | None,
    ) -> tuple[MovementAnomaly, ...]:
        result: list[MovementAnomaly] = []
        if (
            latest_match is not None
            and latest_match.distance_from_track_m > self.thresholds.off_track_distance_m
        ):
            result.append(
                MovementAnomaly(
                    "off_track",
                    {
                        "distance_m": latest_match.distance_from_track_m,
                        "threshold_m": self.thresholds.off_track_distance_m,
                    },
                )
            )
        if previous is not None and latest_match is not None and previous_match is not None:
            elapsed = (latest.observed_at - previous.observed_at).total_seconds()
            delta = (
                schedule.directed_progress(latest_match.physical_arc_m)
                - schedule.directed_progress(previous_match.physical_arc_m)
            )
            if delta < -self.thresholds.backward_jump_m:
                result.append(
                    MovementAnomaly(
                        "backward_jump",
                        {
                            "progress_delta_m": delta,
                            "threshold_m": self.thresholds.backward_jump_m,
                        },
                    )
                )
            if elapsed > 0:
                speed_kmh = abs(delta) / elapsed * 3.6
                if speed_kmh > self.thresholds.unusable_jump_speed_kmh:
                    result.append(
                        MovementAnomaly(
                            "implausible_speed",
                            {
                                "map_matched_speed_kmh": speed_kmh,
                                "threshold_kmh": self.thresholds.unusable_jump_speed_kmh,
                            },
                        )
                    )
        if previous is not None and latest.current_stop_id and previous.current_stop_id:
            current_sequences = self.topology.resolve_stop_sequences(
                trip_id, latest.current_stop_id
            )
            previous_sequences = self.topology.resolve_stop_sequences(
                trip_id, previous.current_stop_id
            )
            if current_sequences and previous_sequences:
                jump = min(current_sequences) - max(previous_sequences)
                if jump > 1:
                    result.append(
                        MovementAnomaly(
                            "station_skip_anomaly",
                            {
                                "from_stop_id": previous.current_stop_id,
                                "to_stop_id": latest.current_stop_id,
                                "sequence_jump": jump,
                            },
                        )
                    )
        return tuple(result)

    def _is_unusable(
        self,
        schedule: TripSchedule,
        latest: VehiclePositionObservation,
        latest_match: MapMatch,
        previous: VehiclePositionObservation | None,
        previous_match: MapMatch | None,
    ) -> bool:
        if latest_match.distance_from_track_m > self.thresholds.off_track_distance_m:
            return True
        if previous is None or previous_match is None:
            return False
        elapsed = (latest.observed_at - previous.observed_at).total_seconds()
        if elapsed <= 0:
            return True
        delta = (
            schedule.directed_progress(latest_match.physical_arc_m)
            - schedule.directed_progress(previous_match.physical_arc_m)
        )
        return (
            delta < -self.thresholds.unusable_backward_jump_m
            or abs(delta) / elapsed * 3.6 > self.thresholds.unusable_jump_speed_kmh
        )

    def _limit_estimate(
        self,
        *,
        desired: float,
        latest_progress: float,
        age_s: float,
        latest: VehiclePositionObservation,
        previous: VehiclePositionObservation | None,
        schedule: TripSchedule,
        latest_match: MapMatch,
        previous_match: MapMatch | None,
    ) -> float:
        initial_speed_mps = 0.0
        if previous is not None and previous_match is not None:
            elapsed = (latest.observed_at - previous.observed_at).total_seconds()
            if elapsed > 0:
                previous_progress = schedule.directed_progress(previous_match.physical_arc_m)
                initial_speed_mps = max(0.0, (latest_progress - previous_progress) / elapsed)
        max_speed_mps = self.thresholds.max_estimated_speed_kmh / 3.6
        initial_speed_mps = min(initial_speed_mps, max_speed_mps)
        acceleration_limited = (
            initial_speed_mps * age_s
            + 0.5 * self.thresholds.max_estimated_acceleration_mps2 * age_s * age_s
        )
        max_distance = min(max_speed_mps * age_s, acceleration_limited)
        # La estimación nunca inventa un retroceso: conserva la última posición
        # plausible hasta que el horario vuelva a superarla.
        return min(max(desired, latest_progress), latest_progress + max_distance)
