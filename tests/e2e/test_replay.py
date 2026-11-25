"""Replay E2E determinista (MP-015): ingestión real -> PostgreSQL -> API real.

Nunca llama a Renfe/CRTM en vivo -- el "replay" consiste en inyectar bytes de
fixtures reales (congeladas en MP-004, mismo esquema que produce
`services/collector/http_client.fetch_with_retry`) como respuesta del
`fetcher` inyectable de `run_cycle`, exactamente como ya hace
`services/collector/tests/test_collector_cycle.py`. La diferencia de este
test: no se detiene en "se persistió correctamente" -- continúa la misma
cadena hasta `apps.api.service` (la capa que consume el frontend real de
MP-014), para probar el pipeline completo de un extremo a otro en una sola
pasada: JSON crudo con forma de Renfe -> colector (parseo/normalización/
calidad/persistencia) -> PostgreSQL real -> resolución de topología GTFS
-> respuesta de API real.

Dos escenarios, ambos reales:
1. La fixture de MP-004 tal cual (10 vehículos, de los que el colector
   persiste 7 -- los otros 3 son de otros núcleos y se descartan, ver
   `test_collector_cycle.py`; 0 de los 7 persistidos coinciden con la GTFS
   reducida de MP-010 -- hallazgo ya documentado, DEC-029 en producción):
   prueba que el pipeline completo nunca fabrica una resolución cuando no
   la hay.
2. Un payload sintético mínimo, pero con la forma real exacta observada en
   MP-003 (mismo esquema que la fixture de MP-004), para un `trip_id` que SÍ
   existe en la GTFS reducida (`1022J19502C5`): prueba que el pipeline
   completo SÍ resuelve `route_id`/posición cuando corresponde.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from apps.api.service import list_vehicles
from services.collector.collector import run_cycle
from services.collector.config import FeedConfig
from services.collector.http_client import RetryPolicy
from tests.postgres import connect_disposable_or_skip

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_POLICY = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=5.0)
_NOW = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)


class FullPipelineReplayTests(unittest.TestCase):
    """Igual que `test_collector_cycle.py`: transacción ambiente + rollback,
    nunca se compromete nada real."""

    def setUp(self) -> None:
        self.conn = connect_disposable_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.network = load_network(ApiConfig.from_env())

    def _run_vehicle_positions_cycle(self, body: bytes) -> None:
        feed = FeedConfig("vehicle_positions", "https://example.invalid/vehicle_positions.json")
        fetcher = lambda url, timeout: body  # noqa: E731
        result = run_cycle(feed, self.conn, _POLICY, fetcher=fetcher, now=lambda: _NOW)
        self.assertEqual(result.status, "ok", f"ciclo del colector falló: {result.error}")

    def test_real_fixture_never_fabricates_a_resolution_end_to_end(self) -> None:
        """La fixture real de MP-004 (10 vehículos, 7 persistidos) no coincide con ningún
        `trip_id` de la GTFS reducida de MP-010 -- mismo hallazgo que DEC-029
        en producción, reproducido aquí de extremo a extremo con datos
        deterministas, no con el soak real."""
        # Una sesión local puede devolver timestamptz con el huso del sistema.
        self.conn.execute("SET LOCAL TIME ZONE 'Europe/Madrid'")
        body = (FIXTURES_DIR / "vehicle_positions.json").read_bytes()
        self._run_vehicle_positions_cycle(body)

        fixture_vehicle_ids = {
            e["vehicle"]["vehicle"]["id"]
            for e in json.loads(body)["entity"]
        }
        self.assertEqual(len(fixture_vehicle_ids), 10, "la fixture de MP-004 tiene 10 entidades")
        # La base compartida ya tiene datos reales de sesiones anteriores
        # (soak de MP-007 en adelante) -- se filtra a los vehículos de ESTA
        # fixture, nunca se asume que la tabla esté vacía.
        all_vehicles = list_vehicles(self.conn, self.network, _NOW)
        vehicles = [v for v in all_vehicles if v.vehicle_id in fixture_vehicle_ids]
        # Solo 7/10 llegan a persistirse: la fixture mezcla deliberadamente
        # 7 entidades de Madrid (núcleo "10") con 3 de otros núcleos
        # (20/30/40, ver test_collector_cycle.py) que el colector descarta
        # antes de guardarlas (ADR-0001/ADR-0008) -- no un fallo de este test.
        self.assertEqual(len(vehicles), 7, "el colector descarta los 3 vehículos fuera del núcleo de Madrid")
        for vehicle in vehicles:
            self.assertIsNone(
                vehicle.route_id,
                f"{vehicle.vehicle_id}: ningún trip_id de esta fixture existe en la GTFS "
                f"reducida de MP-010 -- un route_id no-None aquí sería una resolución fabricada",
            )
            self.assertIsNone(vehicle.position)
            self.assertIsNotNone(
                vehicle.observation.age_s,
                "la edad de la observación cruda debe calcularse aunque la ruta no resuelva (MP-013)",
            )

    def test_synthetic_payload_with_real_shape_resolves_a_known_real_trip(self) -> None:
        """Mismo esquema exacto observado en MP-003 (ver docstring del módulo),
        pero con un `trip_id`/`stopId` reales de la GTFS reducida de MP-010
        para que SÍ resuelva de extremo a extremo."""
        payload = {
            "header": {"gtfsRealtimeVersion": "2.0", "timestamp": "1795017707"},
            "entity": [
                {
                    "id": "VP_E2E-TEST",
                    "vehicle": {
                        "trip": {"tripId": "1022J19502C5"},
                        "position": {"latitude": 40.331064, "longitude": -3.882456},
                        "currentStatus": "STOPPED_AT",
                        "timestamp": "1795017707",
                        "stopId": "35607",
                        "vehicle": {"id": "e2e-test-vehicle", "label": "E2E test"},
                    },
                }
            ],
        }
        self._run_vehicle_positions_cycle(json.dumps(payload).encode("utf-8"))

        all_vehicles = list_vehicles(self.conn, self.network, _NOW)
        matches = [v for v in all_vehicles if v.vehicle_id == "e2e-test-vehicle"]
        self.assertEqual(len(matches), 1, "debe aparecer exactamente el vehículo de este test")
        vehicle = matches[0]
        self.assertEqual(vehicle.route_id, "10T0017C5")
        self.assertEqual(vehicle.line, "C5")
        self.assertIsNotNone(vehicle.position, "un trip real conocido con posición cercana al corredor debe resolver")
        self.assertIn(vehicle.position.mode, ("observed", "estimated", "stale", "scheduled"))


if __name__ == "__main__":
    unittest.main()
