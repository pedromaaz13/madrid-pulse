"""Tests del catálogo completo y la enumeración de servicios programados (MP-017)."""

from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from packages.gtfs import (
    CalendarException,
    CalendarService,
    Route,
    Stop,
    StopTime,
    Topology,
    Trip,
    build_catalog,
    load_feed,
    scheduled_service_ids_for_date,
    scheduled_trip_instances_for_date,
)

# Dos ubicaciones reales posibles del ZIP GTFS oficial completo, ambas fuera de
# Git (ver .gitignore `/data/`): la copia que descarga apps/api/tools/
# fetch_gtfs_static.py para operar en vivo, y la congelada del kit de Hito 3
# (data/hito-03/replay/, instalada con --solo-datos). Ninguna se versiona --
# si ninguna está presente localmente, los tests de esta clase se saltan
# explícitamente en vez de fallar (igual criterio que el soak real de MP-007,
# ver apps/api/tests/test_api_contract.py).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_OFFICIAL_ZIP_CANDIDATES = (
    _REPO_ROOT / "data" / "hito-03" / "replay" / "fomento_transit.zip",
    _REPO_ROOT / "data" / "gtfs_static" / "fomento_transit.zip",
)


def _find_official_zip() -> Path | None:
    return next((path for path in _OFFICIAL_ZIP_CANDIDATES if path.is_file()), None)


class ScheduledServiceIdsSyntheticTests(unittest.TestCase):
    """Lógica de `calendar.txt` + `calendar_dates.txt` con una topología mínima
    construida a mano -- no depende de ningún fichero externo. El ZIP oficial
    verificado en MP-017 no incluye `calendar_dates.txt` (ver docstring de
    `CalendarException`), por lo que esta es la única vía realista de probar
    las excepciones de calendario hoy."""

    def _topology(self, calendar_dates: tuple[CalendarException, ...] = ()) -> Topology:
        return Topology(
            routes=(Route("10T9999C9", "C9", "Línea sintética", 2, "000000", "ffffff"),),
            trips=(
                Trip("10T9999C9", "WEEKDAY", "trip-weekday", "Destino", 1, "", "shape-1"),
                Trip("10T9999C9", "WEEKEND_ONLY", "trip-weekend", "Destino", 1, "", "shape-1"),
            ),
            stops=(Stop("90001", "Origen sintético", 40.0, -3.0, 1),
                   Stop("90002", "Destino sintético", 40.1, -3.1, 1)),
            stop_times=(
                StopTime("trip-weekday", "08:00:00", "08:00:00", "90001", 1),
                StopTime("trip-weekday", "08:30:00", "08:30:00", "90002", 2),
                StopTime("trip-weekend", "09:00:00", "09:00:00", "90001", 1),
                StopTime("trip-weekend", "09:30:00", "09:30:00", "90002", 2),
            ),
            shape_points=(),
            calendar=(
                CalendarService(
                    "WEEKDAY", True, True, True, True, True, False, False, "20260101", "20261231"
                ),
                CalendarService(
                    "WEEKEND_ONLY", False, False, False, False, False, True, True,
                    "20260101", "20261231",
                ),
            ),
            calendar_dates=calendar_dates,
        )

    def test_weekday_service_is_not_active_on_saturday(self) -> None:
        saturday = date(2026, 11, 21)
        self.assertEqual(saturday.weekday(), 5)
        active = scheduled_service_ids_for_date(self._topology(), saturday)
        self.assertEqual(active, {"WEEKEND_ONLY"})

    def test_calendar_dates_exception_type_1_adds_a_service_outside_its_weekday(self) -> None:
        saturday = date(2026, 11, 21)
        topology = self._topology(
            calendar_dates=(CalendarException("WEEKDAY", "20261121", exception_type=1),)
        )
        active = scheduled_service_ids_for_date(topology, saturday)
        self.assertEqual(active, {"WEEKDAY", "WEEKEND_ONLY"})

    def test_calendar_dates_exception_type_2_removes_a_service_within_its_weekday(self) -> None:
        monday = date(2026, 11, 23)
        self.assertEqual(monday.weekday(), 0)
        topology = self._topology(
            calendar_dates=(CalendarException("WEEKDAY", "20261123", exception_type=2),)
        )
        active = scheduled_service_ids_for_date(topology, monday)
        self.assertEqual(active, set())

    def test_absent_calendar_dates_behaves_exactly_like_calendar_only(self) -> None:
        monday = date(2026, 11, 23)
        active = scheduled_service_ids_for_date(self._topology(), monday)
        self.assertEqual(active, {"WEEKDAY"})

    def test_scheduled_trip_instances_never_fabricates_an_orphan_trip(self) -> None:
        topology = Topology(
            routes=(Route("10T9998C8", "C8", "Huérfana", 2, "000000", "ffffff"),),
            trips=(Trip("10T9998C8", "WEEKDAY", "orphan-trip", "Destino", 1, "", "shape-1"),),
            stops=(),
            stop_times=(),  # sin stop_times: huérfano, no se fabrica una instancia
            shape_points=(),
            calendar=(
                CalendarService(
                    "WEEKDAY", True, True, True, True, True, False, False, "20260101", "20261231"
                ),
            ),
        )
        instances = scheduled_trip_instances_for_date(topology, date(2026, 11, 23))
        self.assertEqual(instances, ())

    def test_build_catalog_keeps_a_line_with_zero_valid_patterns(self) -> None:
        topology = Topology(
            routes=(Route("10T9998C8", "C8", "Huérfana", 2, "000000", "ffffff"),),
            trips=(Trip("10T9998C8", "WEEKDAY", "orphan-trip", "Destino", 1, "", "shape-1"),),
            stops=(),
            stop_times=(),
            shape_points=(),
            calendar=(),
        )
        catalog = build_catalog(topology)
        line = catalog.line("C8")
        self.assertIsNotNone(line)
        self.assertEqual(line.patterns, ())
        self.assertEqual(line.route_ids, ("10T9998C8",))


@unittest.skipIf(_find_official_zip() is None, "ZIP GTFS oficial completo no presente localmente")
class FullMadridCatalogRealFeedTests(unittest.TestCase):
    """Catálogo completo contra el ZIP oficial real (no la fixture reducida de
    15 trips de MP-010, que solo cubre C5). Se salta si el ZIP no está
    presente localmente -- no es un fichero versionado (DEC-023/.gitignore);
    reproducible instalando el kit de Hito 3 o ejecutando
    `apps.api.tools.fetch_gtfs_static`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.zip_path = _find_official_zip()
        cls.topology = load_feed(cls.zip_path, network_id="10")
        cls.catalog = build_catalog(cls.topology)

    def test_42_route_ids_group_into_12_line_names(self) -> None:
        self.assertEqual(len(self.topology.routes), 42)
        self.assertEqual(len(self.catalog.lines), 12)
        self.assertEqual(
            {line.short_name for line in self.catalog.lines},
            {"C1", "C2", "C3", "C4", "C4a", "C4b", "C5", "C7", "C8a", "C8b", "C9", "C10"},
        )

    def test_station_60104_valdemoro_belongs_to_madrid_network(self) -> None:
        """`stopId=60104` es la estación real (Valdemoro) del hallazgo P1 de
        `docs/hitos/hito-03/referencia/01-auditoria-live.md` (aviso de estación
        sin routeId) -- confirma que el filtro de avisos por estación (MP-017,
        `services/collector/collector.py::_persist_alerts`) puede resolverla
        contra un catálogo real, no inventado."""
        self.assertIn("60104", {stop.stop_id for stop in self.topology.stops})

    def test_real_24xx_trip_crosses_midnight_without_shifting_service_date(self) -> None:
        """`1023V19788C5` tiene paradas reales a las `24:02`/`24:05`/`24:08`
        (verificado directamente contra el ZIP oficial en esta tarea) -- debe
        aparecer como instancia programada de su propia fecha de servicio,
        marcada `crosses_midnight`, sin desplazar `service_date` al día
        calendario siguiente."""
        trip = next(t for t in self.topology.trips if t.trip_id == "1023V19788C5")
        # `calendar.txt` real de este trip (verificado en esta tarea): servicio
        # `1023V`, activo únicamente el viernes 2026-11-20 (`start_date` ==
        # `end_date`, calendario de un solo día -- mismo patrón ya observado en
        # otras fixtures reales del proyecto). No se adivina una fecha: se lee
        # del propio `calendar.txt`.
        service = next(c for c in self.topology.calendar if c.service_id == trip.service_id)
        self.assertEqual(service.start_date, service.end_date)
        service_date = date(2026, 11, 20)
        active = scheduled_service_ids_for_date(self.topology, service_date)
        self.assertIn(trip.service_id, active)
        instances = scheduled_trip_instances_for_date(self.topology, service_date)
        instance = next(item for item in instances if item.trip_id == "1023V19788C5")
        self.assertTrue(instance.crosses_midnight)
        self.assertEqual(instance.service_date, service_date)

    def test_special_reinforcement_trip_never_appears_as_scheduled(self) -> None:
        """Un refuerzo `SPECIAL_` no existe en `trips.txt` (ver `nucleo.py`) --
        no debe fabricarse ninguna instancia programada para él en ninguna
        fecha, y la resolución literal debe devolver `None`."""
        self.assertIsNone(self.topology.resolve_trip_route_id("SPECIAL_10_91567C2"))
        instances = scheduled_trip_instances_for_date(self.topology, date(2026, 11, 23))
        self.assertFalse(any(item.trip_id.startswith("SPECIAL_") for item in instances))


if __name__ == "__main__":
    unittest.main()
