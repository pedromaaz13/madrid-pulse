"""Casos sintéticos que no aparecen (o no se sabe si aparecen) en las fixtures reales.

MP-005 exige "tests de validación de esquema contra fixtures reales y sintéticas"
(docs/TASKS.md). Este fichero cubre los sintéticos: generación de JSON Schema,
rechazo de datos inválidos, y un caso multi-núcleo que las capturas reales no
contenían.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from packages.contracts.canonical import FeedHealth, ServiceAlert, VehiclePositionObservation
from packages.contracts.raw import RawVehiclePositionsFeed


class JsonSchemaExportTests(unittest.TestCase):
    """MP-005 pide explícitamente contrato 'Pydantic/JSON Schema' -- comprobamos
    que el JSON Schema se puede generar y declara los campos esperados."""

    def test_vehicle_position_observation_exports_json_schema(self) -> None:
        schema = VehiclePositionObservation.model_json_schema()
        self.assertEqual(schema["title"], "VehiclePositionObservation")
        for field in ("source_vehicle_id", "source_trip_id", "observed_at", "payload_hash"):
            self.assertIn(field, schema["properties"])

        # nucleo_prefix/nucleo_name son computed_field: Pydantic solo los incluye
        # en el esquema de SERIALIZACIÓN, no en el de validación (son de solo
        # lectura, no algo que un cliente pueda enviar). Deben aparecer ahí para
        # que un consumidor externo (API, MP-013) sepa que existen en la salida.
        serialization_schema = VehiclePositionObservation.model_json_schema(mode="serialization")
        self.assertIn("nucleo_prefix", serialization_schema["properties"])
        self.assertIn("nucleo_name", serialization_schema["properties"])


class InvalidInputRejectionTests(unittest.TestCase):
    """El contrato debe rechazar activamente datos que no cumplen el esquema --
    si estos tests pasaran con cualquier entrada, el contrato no estaría
    validando nada de verdad."""

    def test_latitude_as_non_numeric_string_is_rejected(self) -> None:
        payload = {
            "header": {"gtfsRealtimeVersion": "2.0", "timestamp": "1700000000"},
            "entity": [
                {
                    "id": "VP_BAD-1",
                    "vehicle": {
                        "trip": {"tripId": "1021X00002C5"},
                        "position": {"latitude": "no-es-un-numero", "longitude": -3.7},
                        "timestamp": "1700000000",
                        "vehicle": {"id": "00002", "label": "C5-00002"},
                    },
                }
            ],
        }
        with self.assertRaises(ValidationError):
            RawVehiclePositionsFeed.model_validate(payload)

    def test_vehicle_position_observation_rejects_missing_required_field(self) -> None:
        with self.assertRaises(ValidationError):
            VehiclePositionObservation(
                # falta source_vehicle_id, source_trip_id, observed_at, etc.
                raw_vehicle_label="C5-00000",
                payload_hash="deadbeef",
            )  # type: ignore[call-arg]


class UtcEnforcementTests(unittest.TestCase):
    """Hallazgo de la revisión de Codex en MP-005: el tipo `datetime` por sí solo
    no garantiza 'UTC siempre' -- estos tests prueban que el contrato lo rechaza
    de verdad, no solo que lo documenta en un comentario."""

    def _build(self, observed_at) -> VehiclePositionObservation:
        return VehiclePositionObservation(
            source_vehicle_id="1",
            source_trip_id="1021X00001C5",
            observed_at=observed_at,
            raw_vehicle_label="C5-00001",
            payload_hash="deadbeef",
        )

    def test_naive_datetime_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self._build(datetime(2026, 11, 18, 10, 0, 0))  # sin tzinfo

    def test_non_utc_offset_is_rejected(self) -> None:
        madrid_tz = timezone(timedelta(hours=1))
        with self.assertRaises(ValidationError):
            self._build(datetime(2026, 11, 18, 10, 0, 0, tzinfo=madrid_tz))

    def test_utc_datetime_is_accepted(self) -> None:
        obs = self._build(datetime(2026, 11, 18, 10, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(obs.observed_at.tzinfo, timezone.utc)

    def test_service_alert_end_accepts_none_but_rejects_naive(self) -> None:
        # None debe pasar (campo opcional, ver canonical.py); un valor naive no.
        alert = ServiceAlert(
            source_alert_id="X",
            active_period_start=datetime(2026, 11, 18, tzinfo=timezone.utc),
            active_period_end=None,
            affected_route_ids=["10T0047C5"],
            description_text="t",
            description_language="es",
            payload_hash="deadbeef",
        )
        self.assertIsNone(alert.active_period_end)
        with self.assertRaises(ValidationError):
            ServiceAlert(
                source_alert_id="X",
                active_period_start=datetime(2026, 11, 18, tzinfo=timezone.utc),
                active_period_end=datetime(2026, 11, 19),  # naive
                affected_route_ids=["10T0047C5"],
                description_text="t",
                description_language="es",
                payload_hash="deadbeef",
            )

    def test_feed_health_rejects_naive_source_timestamp(self) -> None:
        with self.assertRaises(ValidationError):
            FeedHealth(
                feed_name="vehicle_positions",
                source_timestamp=datetime(2026, 11, 18),
                entity_count=1,
            )


class SyntheticMultiNucleoAlertTests(unittest.TestCase):
    """Ninguna alerta real capturada en MP-003/MP-004 afecta a más de un núcleo
    a la vez; este caso sintético comprueba que, si Renfe alguna vez emitiera
    una así, `nucleo_prefixes` lo reflejaría correctamente como conjunto con
    más de un elemento, en vez de asumir siempre un único núcleo por alerta."""

    def test_alert_spanning_two_nuclei_reports_both_prefixes(self) -> None:
        alert = ServiceAlert(
            source_alert_id="AVISO_SINTETICO_MULTINUCLEO",
            active_period_start="2026-11-18T10:00:00+00:00",
            affected_route_ids=["10T0047C5", "20T0011C5"],
            description_text="Caso sintético: no observado en producción.",
            description_language="es",
            payload_hash="deadbeef",
        )
        self.assertEqual(alert.nucleo_prefixes, {"10", "20"})


if __name__ == "__main__":
    unittest.main()
