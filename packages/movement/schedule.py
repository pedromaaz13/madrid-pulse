"""Progreso esperado por horario GTFS sobre un corredor ya resuelto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
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
    """Segundo de día de servicio GTFS de un instante, en reloj de pared local.

    El día de servicio se mide sobre el **reloj de pared** de Europe/Madrid, no
    sobre segundos reales transcurridos: una hora GTFS `HH:MM:SS` corresponde a
    la hora `HH:MM:SS` del calendario local (y `24:xx`, `25:xx` a la madrugada
    del día civil siguiente). Es la convención que publican las agencias y la
    que GTFS describe como «medianoche, salvo los días con cambio de hora»; por
    eso un día de cambio de horario tiene 23 o 25 horas reales pero sus horas
    GTFS siguen siendo las del horario publicado.

    Hallazgo de la revisión de MP-019: una versión anterior calculaba esta
    diferencia entre dos `datetime` *aware* con el mismo `tzinfo`, lo que Python
    resuelve de forma naive (ignora el huso) y daba por tanto el resultado
    correcto **por accidente**. Al escribir la inversa (`service_day_instant`)
    con aritmética sobre UTC, las dos funciones dejaban de ser inversas en los
    dos días de cambio de hora. Ahora la aritmética de reloj de pared es
    explícita en ambas direcciones y la propiedad de ida y vuelta está probada
    sobre las dos fechas de 2026.
    """
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("calculated_at debe ser timezone-aware")
    local = at.astimezone(MADRID).replace(tzinfo=None)
    return (local - datetime.combine(service_date, time.min)).total_seconds()


def service_day_instant(service_date: date, seconds: float) -> datetime:
    """Inversa de `service_seconds`: instante UTC de un segundo de día de servicio.

    Suma los segundos en el espacio de **reloj de pared** y localiza después, de
    modo que el cambio de hora se aplica con el desplazamiento real de cada
    fecha en vez de con un único offset fijo. Admite `seconds >= 86400`
    (horas GTFS `24:xx`/`25:xx`), que caen en el día civil siguiente.

    Dos casos límite del cambio de hora, resueltos de forma deliberada y no por
    omisión (`fold=0`):

    - **Hora inexistente** (adelanto: el 2026-03-29 el reloj local salta de
      02:00 a 03:00). Un horario en esa franja se resuelve con el offset previo
      al salto, lo que equivale a desplazarlo una hora hacia delante. La ida y
      vuelta no es exacta ahí porque ese reloj de pared no existe. El feed real
      de Renfe verificado no publica ninguna hora en esa franja (0 valores en
      `02:xx`/`26:xx` sobre 3,5 M de `stop_times`), así que es un caso
      documentado, no observado.
    - **Hora ambigua** (atraso: el 2026-10-25 el reloj local repite 02:00-03:00).
      Se toma la **primera** ocurrencia, coherente con `service_seconds`, que no
      puede distinguir las dos.
    """
    days, remainder = divmod(float(seconds), 86400.0)
    wall = datetime.combine(service_date + timedelta(days=int(days)), time.min) + timedelta(
        seconds=remainder
    )
    return wall.replace(tzinfo=MADRID).astimezone(timezone.utc)


@dataclass(frozen=True)
class SchedulePoint:
    seconds: float
    progress_m: float


@dataclass(frozen=True)
class StopOccurrence:
    stop_id: str
    stop_sequence: int
    progress_m: float
    arrival_s: float
    departure_s: float


@dataclass(frozen=True)
class TripSchedule:
    points: tuple[SchedulePoint, ...]
    corridor_length_m: float
    forward: bool
    stops: tuple[StopOccurrence, ...] = ()

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

    def dwell_end_seconds(self, progress_m: float, *, tolerance_m: float = 1.0) -> float | None:
        """Segundo de servicio en que el horario reanuda el avance tras ``progress_m``.

        Devuelve ``None`` cuando ``progress_m`` no cae en un tramo plano del
        horario (es decir, no hay espera declarada ahí) -- `None` significa
        "sin espera conocida", nunca "espera de cero segundos".
        """
        end: float | None = None
        for left, right in zip(self.points, self.points[1:]):
            flat = abs(right.progress_m - left.progress_m) <= tolerance_m
            at_progress = abs(left.progress_m - progress_m) <= tolerance_m
            if flat and at_progress:
                end = right.seconds
        return end

    def directed_progress(self, physical_arc_m: float) -> float:
        return physical_arc_m if self.forward else self.corridor_length_m - physical_arc_m

    def physical_arc(self, progress_m: float) -> float:
        return progress_m if self.forward else self.corridor_length_m - progress_m


def build_trip_schedule(topology: Topology, corridor: Corridor, trip_id: str) -> TripSchedule:
    """Horario proyectado sobre el corredor, con esperas reales en parada.

    Extensión de MP-019 (ADR-0014): cuando `arrival_time` y `departure_time` de
    una parada difieren, se emiten **dos** puntos con el mismo progreso (llegada
    y salida) en vez de uno solo con la salida. Sin esto el horario absorbía la
    espera -- en la fixture real de C5 hay 11 paradas con espera declarada
    (p. ej. 60 s en Madrid-Atocha, `stop_id` 18000) -- y un tramo plano no podía
    expresarse, de modo que el contrato de presentación no podía declarar
    `dwell_until` ni "detener en estación" sin inventarlo. Los tramos planos no
    rompen las validaciones de monotonía, que comparan con `<` estricto.
    """
    times = topology.stop_times_for_trip(trip_id)
    if len(times) < 2:
        raise ValueError(f"trip {trip_id!r} no tiene al menos dos stop_times")
    stops = {stop.stop_id: stop for stop in topology.stops}
    projected: list[tuple[float, float]] = []
    occurrences = []
    for item in times:
        stop = stops.get(item.stop_id)
        if stop is None:
            raise ValueError(f"stop_id {item.stop_id!r} no resuelto para {trip_id!r}")
        _, physical_arc = corridor.project_station(stop.latitude, stop.longitude)
        arrival = item.arrival_time or item.departure_time
        departure = item.departure_time or item.arrival_time
        arrival_s = parse_gtfs_time(arrival)
        departure_s = parse_gtfs_time(departure)
        occurrences.append((item, physical_arc, arrival_s, departure_s))
        if departure_s > arrival_s:
            projected.append((arrival_s, physical_arc))
        projected.append((departure_s, physical_arc))
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
    directed_stops = tuple(
        StopOccurrence(item.stop_id, item.stop_sequence, arc if forward else length_m - arc, arr, dep)
        for item, arc, arr, dep in occurrences
    )
    return TripSchedule(points, length_m, forward, directed_stops)
