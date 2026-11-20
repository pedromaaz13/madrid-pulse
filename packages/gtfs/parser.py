"""Parser fiel a las seis tablas observadas en el GTFS estático de Renfe.

El feed nacional es grande (``stop_times.txt`` supera 273 MB descomprimido),
por lo que se recorre en streaming y solo se retienen las rutas seleccionadas.
La selección es genérica: IDs completos, prefijo de red y/o nombre corto; la
lógica no contiene identificadores de una línea concreta.
"""

from __future__ import annotations

import csv
import re
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, TextIO
from zipfile import ZipFile


class GtfsSchemaError(ValueError):
    """El fichero no contiene el esquema mínimo observado y requerido."""


@dataclass(frozen=True)
class Route:
    route_id: str
    short_name: str
    long_name: str
    route_type: int
    color: str
    text_color: str

    @property
    def network_id(self) -> str | None:
        """Prefijo numérico de dos cifras observado como núcleo de Renfe."""
        match = re.match(r"^(\d{2})", self.route_id)
        return match.group(1) if match else None


@dataclass(frozen=True)
class Trip:
    route_id: str
    service_id: str
    trip_id: str
    headsign: str
    wheelchair_accessible: int
    block_id: str
    shape_id: str


@dataclass(frozen=True)
class Stop:
    stop_id: str
    name: str
    latitude: float
    longitude: float
    wheelchair_boarding: int


@dataclass(frozen=True)
class StopTime:
    trip_id: str
    arrival_time: str
    departure_time: str
    stop_id: str
    stop_sequence: int


@dataclass(frozen=True)
class ShapePoint:
    shape_id: str
    latitude: float
    longitude: float
    sequence: int


@dataclass(frozen=True)
class CalendarService:
    service_id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start_date: str
    end_date: str


_REQUIRED_COLUMNS: Mapping[str, tuple[str, ...]] = {
    "routes.txt": (
        "route_id",
        "route_short_name",
        "route_long_name",
        "route_type",
        "route_color",
        "route_text_color",
    ),
    "trips.txt": (
        "route_id",
        "service_id",
        "trip_id",
        "trip_headsign",
        "wheelchair_accessible",
        "block_id",
        "shape_id",
    ),
    "stops.txt": (
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "wheelchair_boarding",
    ),
    "stop_times.txt": (
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    ),
    "shapes.txt": ("shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"),
    "calendar.txt": (
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ),
}


def _integer(value: str, *, field: str, row_id: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise GtfsSchemaError(f"{field} no es entero para {row_id}: {value!r}") from exc


def _decimal(value: str, *, field: str, row_id: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise GtfsSchemaError(f"{field} no es decimal para {row_id}: {value!r}") from exc


def _boolean(value: str, *, field: str, row_id: str) -> bool:
    parsed = _integer(value, field=field, row_id=row_id)
    if parsed not in (0, 1):
        raise GtfsSchemaError(f"{field} no es 0/1 para {row_id}: {value!r}")
    return bool(parsed)


@contextmanager
def _feed_files(source: str | Path) -> Iterator[Mapping[str, TextIO]]:
    path = Path(source)
    with ExitStack() as stack:
        result: dict[str, TextIO] = {}
        if path.is_dir():
            for name in _REQUIRED_COLUMNS:
                try:
                    result[name] = stack.enter_context(
                        (path / name).open(encoding="utf-8-sig", newline="")
                    )
                except FileNotFoundError as exc:
                    raise GtfsSchemaError(f"falta {name} en {path}") from exc
        else:
            archive = stack.enter_context(ZipFile(path))
            names = set(archive.namelist())
            for name in _REQUIRED_COLUMNS:
                if name not in names:
                    raise GtfsSchemaError(f"falta {name} en {path}")
                binary = stack.enter_context(archive.open(name))
                import io

                result[name] = stack.enter_context(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
        yield result


def _rows(handle: TextIO, name: str) -> Iterator[dict[str, str]]:
    reader = csv.DictReader(handle)
    actual = tuple((column or "").strip() for column in (reader.fieldnames or ()))
    missing = set(_REQUIRED_COLUMNS[name]) - set(actual)
    if missing:
        raise GtfsSchemaError(f"{name}: faltan columnas {sorted(missing)}; observadas {actual}")
    for raw in reader:
        yield {(key or "").strip(): (value or "").strip() for key, value in raw.items()}


@dataclass(frozen=True)
class Topology:
    routes: tuple[Route, ...]
    trips: tuple[Trip, ...]
    stops: tuple[Stop, ...]
    stop_times: tuple[StopTime, ...]
    shape_points: tuple[ShapePoint, ...]
    calendar: tuple[CalendarService, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_routes_by_id", _unique(self.routes, "route_id"))
        object.__setattr__(self, "_trips_by_id", _unique(self.trips, "trip_id"))
        object.__setattr__(self, "_stops_by_id", _unique(self.stops, "stop_id"))
        by_trip: dict[str, list[StopTime]] = {}
        for item in self.stop_times:
            by_trip.setdefault(item.trip_id, []).append(item)
        object.__setattr__(
            self,
            "_stop_times_by_trip",
            {key: tuple(sorted(values, key=lambda item: item.stop_sequence)) for key, values in by_trip.items()},
        )

    def route_groups(self) -> dict[tuple[str | None, str], tuple[Route, ...]]:
        """Agrupa variantes por ``(network_id, short_name)`` sin colapsar IDs."""
        groups: dict[tuple[str | None, str], list[Route]] = {}
        for route in self.routes:
            groups.setdefault((route.network_id, route.short_name), []).append(route)
        return {key: tuple(sorted(value, key=lambda route: route.route_id)) for key, value in groups.items()}

    def resolve_trip_route_id(
        self, trip_id: str, *, explicit_route_id: str | None = None
    ) -> str | None:
        """Resuelve un trip vivo por igualdad literal contra ``trips.txt``.

        Los refuerzos ``ADDED`` pueden no existir en estático; en ese caso se
        admite el ``routeId`` explícito del GTFS-RT solo si la ruta está en el
        catálogo cargado. Una contradicción entre ambos orígenes se rechaza.
        """
        trip = self._trips_by_id.get(trip_id)
        static_route_id = trip.route_id if trip else None
        if static_route_id and explicit_route_id and static_route_id != explicit_route_id:
            raise ValueError(
                f"route_id contradictorio para {trip_id}: estático={static_route_id}, "
                f"explícito={explicit_route_id}"
            )
        if static_route_id:
            return static_route_id
        if explicit_route_id in self._routes_by_id:
            return explicit_route_id
        return None

    def resolve_trip_route(self, trip_id: str, *, explicit_route_id: str | None = None) -> Route | None:
        route_id = self.resolve_trip_route_id(trip_id, explicit_route_id=explicit_route_id)
        return self._routes_by_id.get(route_id) if route_id else None

    def stop_times_for_trip(self, trip_id: str) -> tuple[StopTime, ...]:
        return self._stop_times_by_trip.get(trip_id, ())

    def resolve_stop_sequences(self, trip_id: str, stop_id: str) -> tuple[int, ...]:
        """Resuelve ``stopId`` vivo a todas sus secuencias reales del trip."""
        return tuple(
            item.stop_sequence for item in self.stop_times_for_trip(trip_id) if item.stop_id == stop_id
        )


def _unique(items: Iterable[object], attribute: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in items:
        key = str(getattr(item, attribute))
        if key in result:
            raise GtfsSchemaError(f"identificador duplicado {attribute}={key!r}")
        result[key] = item
    return result


def load_feed(
    source: str | Path,
    *,
    route_ids: Iterable[str] | None = None,
    network_id: str | None = None,
    short_name: str | None = None,
) -> Topology:
    """Carga un subconjunto del ZIP o directorio GTFS oficial.

    Los filtros se combinan mediante AND. Si no se pasa ninguno se carga todo
    el feed (puede consumir mucha memoria); producción debe filtrar por datos o
    configuración, no mediante literales de línea embebidos en esta función.
    """
    wanted_ids = set(route_ids) if route_ids is not None else None
    with _feed_files(source) as files:
        routes: list[Route] = []
        for row in _rows(files["routes.txt"], "routes.txt"):
            prefix_match = re.match(r"^(\d{2})", row["route_id"])
            row_network = prefix_match.group(1) if prefix_match else None
            if wanted_ids is not None and row["route_id"] not in wanted_ids:
                continue
            if network_id is not None and row_network != network_id:
                continue
            if short_name is not None and row["route_short_name"] != short_name:
                continue
            routes.append(
                Route(
                    route_id=row["route_id"],
                    short_name=row["route_short_name"],
                    long_name=row["route_long_name"],
                    route_type=_integer(row["route_type"], field="route_type", row_id=row["route_id"]),
                    color=row["route_color"],
                    text_color=row["route_text_color"],
                )
            )

        selected_route_ids = {route.route_id for route in routes}
        trips: list[Trip] = []
        for row in _rows(files["trips.txt"], "trips.txt"):
            if row["route_id"] not in selected_route_ids:
                continue
            trips.append(
                Trip(
                    route_id=row["route_id"],
                    service_id=row["service_id"],
                    trip_id=row["trip_id"],
                    headsign=row["trip_headsign"],
                    wheelchair_accessible=_integer(
                        row["wheelchair_accessible"], field="wheelchair_accessible", row_id=row["trip_id"]
                    ),
                    block_id=row["block_id"],
                    shape_id=row["shape_id"],
                )
            )

        trip_ids = {trip.trip_id for trip in trips}
        stop_times: list[StopTime] = []
        for row in _rows(files["stop_times.txt"], "stop_times.txt"):
            if row["trip_id"] not in trip_ids:
                continue
            stop_times.append(
                StopTime(
                    trip_id=row["trip_id"],
                    arrival_time=row["arrival_time"],
                    departure_time=row["departure_time"],
                    stop_id=row["stop_id"],
                    stop_sequence=_integer(
                        row["stop_sequence"], field="stop_sequence", row_id=row["trip_id"]
                    ),
                )
            )

        stop_ids = {item.stop_id for item in stop_times}
        stops = tuple(
            Stop(
                stop_id=row["stop_id"],
                name=row["stop_name"],
                latitude=_decimal(row["stop_lat"], field="stop_lat", row_id=row["stop_id"]),
                longitude=_decimal(row["stop_lon"], field="stop_lon", row_id=row["stop_id"]),
                wheelchair_boarding=_integer(
                    row["wheelchair_boarding"], field="wheelchair_boarding", row_id=row["stop_id"]
                ),
            )
            for row in _rows(files["stops.txt"], "stops.txt")
            if row["stop_id"] in stop_ids
        )

        shape_ids = {trip.shape_id for trip in trips}
        shape_points = tuple(
            ShapePoint(
                shape_id=row["shape_id"],
                latitude=_decimal(row["shape_pt_lat"], field="shape_pt_lat", row_id=row["shape_id"]),
                longitude=_decimal(row["shape_pt_lon"], field="shape_pt_lon", row_id=row["shape_id"]),
                sequence=_integer(
                    row["shape_pt_sequence"], field="shape_pt_sequence", row_id=row["shape_id"]
                ),
            )
            for row in _rows(files["shapes.txt"], "shapes.txt")
            if row["shape_id"] in shape_ids
        )

        service_ids = {trip.service_id for trip in trips}
        calendar = tuple(
            CalendarService(
                service_id=row["service_id"],
                monday=_boolean(row["monday"], field="monday", row_id=row["service_id"]),
                tuesday=_boolean(row["tuesday"], field="tuesday", row_id=row["service_id"]),
                wednesday=_boolean(row["wednesday"], field="wednesday", row_id=row["service_id"]),
                thursday=_boolean(row["thursday"], field="thursday", row_id=row["service_id"]),
                friday=_boolean(row["friday"], field="friday", row_id=row["service_id"]),
                saturday=_boolean(row["saturday"], field="saturday", row_id=row["service_id"]),
                sunday=_boolean(row["sunday"], field="sunday", row_id=row["service_id"]),
                start_date=row["start_date"],
                end_date=row["end_date"],
            )
            for row in _rows(files["calendar.txt"], "calendar.txt")
            if row["service_id"] in service_ids
        )

    return Topology(
        routes=tuple(routes),
        trips=tuple(trips),
        stops=stops,
        stop_times=tuple(stop_times),
        shape_points=shape_points,
        calendar=calendar,
    )
