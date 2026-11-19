"""Progreso esperado por horario GTFS sobre un corredor ya resuelto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from packages.geo import Corridor, corridor_length_m
from packages.gtfs import Topology

MADRID = ZoneInfo("Europe/Madrid")


def parse_gtfs_time(value: str) -> float:
    """Segundos desde inicio del día de servicio; admite horas GTFS > 24."""
    try:
        hours, minutes, seconds = (int(part) for part in value.split(":"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"hora GTFS inválida: {value!r}") from exc
    if hours < 0 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
        raise ValueError(f"hora GTFS inválida: {value!r}")
    return float(hours * 3600 + minutes * 60 + seconds)


def service_seconds(at: datetime, service_date: date) -> float:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("calculated_at debe ser timezone-aware")
    local = at.astimezone(MADRID)
    start = datetime.combine(service_date, time.min, tzinfo=MADRID)
    return (local - start).total_seconds()


@dataclass(frozen=True)
class SchedulePoint:
    seconds: float
    progress_m: float


@dataclass(frozen=True)
class TripSchedule:
    points: tuple[SchedulePoint, ...]
    corridor_length_m: float
    forward: bool

    def progress_at(self, seconds: float) -> float:
        if seconds <= self.points[0].seconds:
            return self.points[0].progress_m
        if seconds >= self.points[-1].seconds:
            return self.points[-1].progress_m
        for left, right in zip(self.points, self.points[1:]):
            if seconds <= right.seconds:
                if right.seconds == left.seconds:
                    return right.progress_m
                fraction = (seconds - left.seconds) / (right.seconds - left.seconds)
                return left.progress_m + fraction * (right.progress_m - left.progress_m)
        return self.points[-1].progress_m

    def seconds_at_progress(self, progress_m: float) -> float:
        if progress_m <= self.points[0].progress_m:
            return self.points[0].seconds
        if progress_m >= self.points[-1].progress_m:
            return self.points[-1].seconds
        for left, right in zip(self.points, self.points[1:]):
            if progress_m <= right.progress_m:
                span = right.progress_m - left.progress_m
                if span == 0:
                    return right.seconds
                fraction = (progress_m - left.progress_m) / span
                return left.seconds + fraction * (right.seconds - left.seconds)
        return self.points[-1].seconds

    def directed_progress(self, physical_arc_m: float) -> float:
        return physical_arc_m if self.forward else self.corridor_length_m - physical_arc_m

    def physical_arc(self, progress_m: float) -> float:
        return progress_m if self.forward else self.corridor_length_m - progress_m


def build_trip_schedule(topology: Topology, corridor: Corridor, trip_id: str) -> TripSchedule:
    times = topology.stop_times_for_trip(trip_id)
    if len(times) < 2:
        raise ValueError(f"trip {trip_id!r} no tiene al menos dos stop_times")
    stops = {stop.stop_id: stop for stop in topology.stops}
    projected: list[tuple[float, float]] = []
    for item in times:
        stop = stops.get(item.stop_id)
        if stop is None:
            raise ValueError(f"stop_id {item.stop_id!r} no resuelto para {trip_id!r}")
        _, physical_arc = corridor.project_station(stop.latitude, stop.longitude)
        projected.append(
            (parse_gtfs_time(item.departure_time or item.arrival_time), physical_arc)
        )
    forward = projected[-1][1] >= projected[0][1]
    length_m = corridor_length_m(corridor)
    points = tuple(
        SchedulePoint(seconds=seconds, progress_m=arc if forward else length_m - arc)
        for seconds, arc in projected
    )
    if any(right.seconds < left.seconds for left, right in zip(points, points[1:])):
        raise ValueError(f"horario no monótono para {trip_id!r}")
    if any(right.progress_m < left.progress_m for left, right in zip(points, points[1:])):
        raise ValueError(f"paradas no monótonas sobre el corredor para {trip_id!r}")
    return TripSchedule(points=points, corridor_length_m=length_m, forward=forward)
