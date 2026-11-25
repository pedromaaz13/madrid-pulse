"""Catálogo completo de líneas y enumeración de servicios programados.

Dos responsabilidades, no una: (1) agrupar el GTFS estático completo de un
núcleo por línea/variante/patrón, conservando toda línea aunque no tenga
vehículos observados en un corte dado; (2) enumerar, para una fecha de
servicio concreta, qué instancias de viaje están realmente programadas --
aplicando `calendar.txt` + `calendar_dates.txt`, no el fallback
``PositionMode.SCHEDULED`` del motor de movimiento (que resuelve un único
``trip_id`` ya conocido, no enumera "todos los servicios del día").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .parser import Topology
from .topology import RoutePattern, validate_topology

_WEEKDAY_ATTRS = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)

OPERATOR = "Renfe"
"""Único operador integrado en el alcance actual del proyecto (DEC-006):
Cercanías Madrid se ingiere exclusivamente desde Renfe. No es un valor
inventado por circulación -- es una constante de alcance, documentada para
que un operador adicional futuro (CRTM u otro) no se confunda con un campo
ya resuelto dinámicamente."""


def _parse_gtfs_date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def scheduled_service_ids_for_date(topology: Topology, service_date: date) -> frozenset[str]:
    """``service_id`` activos en ``service_date`` según `calendar.txt` + excepciones.

    `calendar_dates.txt` es opcional en la fuente (el ZIP oficial de Renfe
    verificado en MP-017 no lo incluye -- ver docstring de `CalendarException`
    en `parser.py`); cuando está ausente, `topology.calendar_dates` es `()` y
    esta función se comporta exactamente como el único `calendar.txt`.
    """
    weekday_attr = _WEEKDAY_ATTRS[service_date.weekday()]
    base = {
        service.service_id
        for service in topology.calendar
        if getattr(service, weekday_attr)
        and _parse_gtfs_date(service.start_date) <= service_date <= _parse_gtfs_date(service.end_date)
    }
    added = {
        exception.service_id
        for exception in topology.calendar_dates
        if exception.exception_type == 1 and _parse_gtfs_date(exception.date) == service_date
    }
    removed = {
        exception.service_id
        for exception in topology.calendar_dates
        if exception.exception_type == 2 and _parse_gtfs_date(exception.date) == service_date
    }
    return frozenset((base | added) - removed)


@dataclass(frozen=True)
class ScheduledTripInstance:
    """Una ocurrencia real de un ``trip_id`` en una fecha de servicio concreta.

    Distinto de ``source_vehicle_id``/``source_trip_id`` del feed en vivo:
    esta instancia existe por horario, con o sin observación GPS asociada.
    Los horarios ``24:xx`` (madrugada del día siguiente, servicio del día
    anterior) se conservan tal cual los publica GTFS -- no se desplaza
    ``service_date``, que es la fecha de servicio, no la fecha de reloj de la
    última parada.

    ``network_id``/``operator`` dan la identidad completa de red/operador que
    exige `docs/hitos/hito-03/MATRIZ-CIERRE-MADRID.md` (MP-017) -- no basta
    con `trip_id`/`route_id`, que por sí solos no distinguen núcleos (ver
    ADR-0008/DEC-017: "C5" existe en varios núcleos de Renfe).
    """

    trip_id: str
    route_id: str
    network_id: str | None
    operator: str
    service_id: str
    service_date: date
    headsign: str
    first_stop_id: str
    first_departure_time: str
    last_stop_id: str
    last_arrival_time: str

    @property
    def crosses_midnight(self) -> bool:
        """``True`` si alguna hora del viaje es ``>= 24:00:00`` (GTFS extendido)."""
        return _hour_component(self.first_departure_time) >= 24 or _hour_component(
            self.last_arrival_time
        ) >= 24


def _hour_component(gtfs_time: str) -> int:
    return int(gtfs_time.split(":", 1)[0])


def scheduled_trip_instances_for_date(
    topology: Topology, service_date: date
) -> tuple[ScheduledTripInstance, ...]:
    """Enumera explícitamente los viajes programados de ``service_date``.

    A diferencia del fallback ``scheduled`` del motor de movimiento (que solo
    resuelve un ``trip_id`` ya observado en el feed en vivo), esto recorre
    *todo* ``topology.trips`` y no depende de que exista ninguna observación.
    Un ``trip_id`` sin ``stop_times`` (huérfano, ya señalado por
    `validate_topology`) no se fabrica como instancia: se omite.
    """
    active_services = scheduled_service_ids_for_date(topology, service_date)
    routes_by_id = {route.route_id: route for route in topology.routes}
    instances: list[ScheduledTripInstance] = []
    for trip in topology.trips:
        if trip.service_id not in active_services:
            continue
        times = topology.stop_times_for_trip(trip.trip_id)
        if not times:
            continue
        route = routes_by_id.get(trip.route_id)
        instances.append(
            ScheduledTripInstance(
                trip_id=trip.trip_id,
                route_id=trip.route_id,
                network_id=route.network_id if route is not None else None,
                operator=OPERATOR,
                service_id=trip.service_id,
                service_date=service_date,
                headsign=trip.headsign,
                first_stop_id=times[0].stop_id,
                first_departure_time=times[0].departure_time,
                last_stop_id=times[-1].stop_id,
                last_arrival_time=times[-1].arrival_time,
            )
        )
    return tuple(instances)


@dataclass(frozen=True)
class LineVariant:
    """Una línea comercial (``short_name``) con todas sus variantes de ``route_id``.

    Se conserva aunque ``patterns`` esté vacío (línea sin recorridos válidos
    observados en ``trips.txt``/``stop_times.txt`` en este corte del GTFS) o
    aunque no exista ningún vehículo en vivo para ninguno de sus patrones --
    eso se mide aparte (observaciones), no aquí (catálogo estático)."""

    short_name: str
    network_id: str | None
    route_ids: tuple[str, ...]
    patterns: tuple[RoutePattern, ...]


@dataclass(frozen=True)
class Catalog:
    """``gtfs_version`` es la procedencia exigida por
    `docs/hitos/hito-03/MATRIZ-CIERRE-MADRID.md` (MP-017: "versiones y
    procedencia") -- el mismo identificador que `/api/v1/health` ya publica
    (`packages/movement/profile.py::source_version`, hash SHA-256 del ZIP/directorio
    fuente), no un valor nuevo e inconsistente inventado aquí."""

    lines: tuple[LineVariant, ...]
    gtfs_version: str

    def line(self, short_name: str) -> LineVariant | None:
        return next((item for item in self.lines if item.short_name == short_name), None)


def build_catalog(topology: Topology, *, gtfs_version: str) -> Catalog:
    """Construye el catálogo completo de líneas/variantes/patrones de ``topology``.

    No filtra por observaciones en vivo: una línea con cero vehículos en un
    corte sigue apareciendo, con sus patrones (si el GTFS los valida) o vacía
    (si `validate_topology` no encontró ningún patrón válido para ninguno de
    sus `route_id`, p. ej. todos sus trips son huérfanos). ``gtfs_version`` es
    obligatorio -- sin procedencia, el catálogo no es trazable (MP-017)."""
    validation = validate_topology(topology)
    patterns_by_route: dict[str, list[RoutePattern]] = {}
    for pattern in validation.patterns:
        patterns_by_route.setdefault(pattern.route_id, []).append(pattern)

    lines = []
    for (network_id, short_name), routes in sorted(
        topology.route_groups().items(), key=lambda item: item[0][1]
    ):
        route_ids = tuple(route.route_id for route in routes)
        patterns = tuple(
            pattern for route_id in route_ids for pattern in patterns_by_route.get(route_id, ())
        )
        lines.append(
            LineVariant(
                short_name=short_name,
                network_id=network_id,
                route_ids=route_ids,
                patterns=patterns,
            )
        )
    return Catalog(lines=tuple(lines), gtfs_version=gtfs_version)
