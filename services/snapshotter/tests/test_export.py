"""Tests puros (sin BD) de los límites de día de servicio Europe/Madrid.

Hallazgo real durante la implementación de MP-009: los datos reales del
soak test de MP-007 (`2026-11-18 23:31:42+00` a `23:51:42+00`) pertenecen al
día de servicio `2026-11-19` en Europe/Madrid (CET, UTC+1 en noviembre), NO
al `2026-11-18` que sugeriría leer la fecha UTC directamente. Estos tests
fijan ese comportamiento como regresión explícita.
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from services.snapshotter.export import service_date_utc_bounds


class ServiceDateBoundsTests(unittest.TestCase):
    def test_november_utc_offset_is_plus_one_hour(self) -> None:
        """España está en CET (UTC+1) en noviembre -- fuera del horario de verano."""
        start, end = service_date_utc_bounds(date(2026, 11, 19))
        self.assertEqual(start, datetime(2026, 11, 18, 23, 0, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2026, 11, 19, 23, 0, tzinfo=timezone.utc))

    def test_real_soak_test_timestamp_falls_in_the_following_madrid_day(self) -> None:
        """Regresión directa del hallazgo real: 23:31 UTC del 18-nov pertenece
        al día de servicio 19-nov en Europe/Madrid, no al 18."""
        soak_test_timestamp = datetime(2026, 11, 18, 23, 31, 42, tzinfo=timezone.utc)
        start_18, end_18 = service_date_utc_bounds(date(2026, 11, 18))
        start_19, end_19 = service_date_utc_bounds(date(2026, 11, 19))

        self.assertFalse(start_18 <= soak_test_timestamp < end_18)
        self.assertTrue(start_19 <= soak_test_timestamp < end_19)

    def test_august_utc_offset_is_plus_two_hours_dst(self) -> None:
        """España está en CEST (UTC+2) en agosto -- confirma que no se asume
        un offset fijo todo el año."""
        start, end = service_date_utc_bounds(date(2026, 8, 15))
        self.assertEqual(start, datetime(2026, 8, 14, 22, 0, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2026, 8, 15, 22, 0, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
