"""Regresión: disambiguación de núcleo para trip_id/route_id reales (MP-003/MP-007).

Ver `packages/contracts/nucleo.py` -- MP-007 encontró un formato de trip_id de
refuerzo (`SPECIAL_<núcleo>_<resto>`) en el feed en vivo que la muestra más
pequeña de MP-003/MP-004 no contenía. Verificado contra el GTFS estático real
(`fomento_transit.zip`): `SPECIAL_10_91567C2` no aparece en `trips.txt` --
es un tren añadido dinámicamente sin viaje programado correspondiente.
"""

from __future__ import annotations

import unittest

from packages.contracts.nucleo import is_madrid, nucleo_name, nucleo_prefix


class StandardFormatTests(unittest.TestCase):
    def test_route_id_prefix(self) -> None:
        self.assertEqual(nucleo_prefix("10T0047C5"), "10")

    def test_trip_id_prefix(self) -> None:
        self.assertEqual(nucleo_prefix("20T0011C5-001"), "20")


class SpecialReinforcementTripIdTests(unittest.TestCase):
    """Caso real capturado en vivo durante la verificación de MP-007
    (entidad 91567 del poll de `vehicle_positions.json` del 2026-11-18)."""

    def test_special_prefixed_trip_id_extracts_embedded_nucleo(self) -> None:
        self.assertEqual(nucleo_prefix("SPECIAL_10_91567C2"), "10")

    def test_special_prefixed_trip_id_is_madrid(self) -> None:
        self.assertTrue(is_madrid("SPECIAL_10_91567C2"))

    def test_special_prefixed_trip_id_resolves_nucleo_name(self) -> None:
        self.assertEqual(nucleo_name(nucleo_prefix("SPECIAL_10_91567C2")), "Madrid")

    def test_special_prefixed_trip_id_non_madrid_nucleo(self) -> None:
        self.assertEqual(nucleo_prefix("SPECIAL_20_12345C1"), "20")

    def test_naive_slice_would_have_failed(self) -> None:
        """Documenta el bug corregido: tomar los 2 primeros caracteres literales
        de un trip_id `SPECIAL_...` da "SP", no un núcleo válido."""
        self.assertEqual("SPECIAL_10_91567C2"[:2], "SP")
        self.assertNotEqual(nucleo_prefix("SPECIAL_10_91567C2"), "SP")


if __name__ == "__main__":
    unittest.main()
