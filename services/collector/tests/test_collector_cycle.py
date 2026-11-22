"""Tests de integración real contra PostgreSQL/PostGIS local (MP-006).

Requieren el contenedor `madrid-pulse` levantado con el esquema de
`infra/migrations/0001_init.up.sql` ya aplicado (ver `infra/docker/README.md`).
No usan mocks de base de datos: igual que en la revisión de MP-006, la
idempotencia se prueba contra una base real, no simulada.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import psycopg

from services.collector.collector import run_cycle
from services.collector.config import CollectorConfig, FeedConfig
from services.collector.http_client import RetryPolicy

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
_POLICY = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=5.0)


def _load_fixture_bytes(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def _connect_or_skip() -> psycopg.Connection:
    # `.from_env()`, no `CollectorConfig()` a secas -- ver hallazgo de MP-015
    # en `services/snapshotter/tests/test_export_replay.py`.
    try:
        return psycopg.connect(
            CollectorConfig.from_env().database_url, autocommit=False, connect_timeout=3
        )
    except psycopg.OperationalError as exc:
        raise unittest.SkipTest(
            f"PostgreSQL local no disponible (levantar infra/docker/docker-compose.yml): {exc}"
        )


class VehiclePositionIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        # Abrir una transacción ambiente ANTES de cualquier `run_cycle`: así,
        # cada `with conn.transaction()` interno de `db.py` se anida como
        # SAVEPOINT de esta transacción en vez de hacer su propio COMMIT de
        # nivel superior (lo que ocurriría si fuera la primera instrucción de
        # la conexión) -- de lo contrario `self.conn.rollback()` no deshace
        # esos commits aislados y el test deja filas huérfanas en la base real.
        self.conn.execute("SELECT 1")
        # addCleanup es LIFO: registrar close() primero para que rollback()
        # (registrado después) se ejecute antes, sobre una conexión aún abierta.
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.feed = FeedConfig("vehicle_positions", "https://example.invalid/vehicle_positions.json")
        self.body = _load_fixture_bytes("vehicle_positions.json")

    def test_schema_failure_records_payload_hash_and_no_source_time(self) -> None:
        body = b'{"header":{"unexpected":"schema"}}'
        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=lambda *_: body)
        self.assertEqual(result.status, "error")
        row = self.conn.execute(
            "SELECT status, source_timestamp FROM source_ingestion_run "
            "WHERE feed_name = %s AND payload_hash = %s ORDER BY id DESC LIMIT 1",
            (self.feed.name, hashlib.sha256(body).hexdigest()),
        ).fetchone()
        self.assertEqual(row, ("error", None))

    def test_broken_json_is_an_error_but_does_not_delete_existing_observations(self) -> None:
        before = self.conn.execute("SELECT count(*) FROM vehicle_position_observation").fetchone()[0]
        body = b'{"header":'
        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=lambda *_: body)
        after = self.conn.execute("SELECT count(*) FROM vehicle_position_observation").fetchone()[0]
        self.assertEqual(result.status, "error")
        self.assertEqual(after, before)

    def test_valid_empty_feed_is_success_not_network_failure(self) -> None:
        body = (
            b'{"header":{"gtfsRealtimeVersion":"2.0",'
            b'"timestamp":"1795185124"},"entity":[]}'
        )
        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=lambda *_: body)
        self.assertEqual((result.status, result.entity_count, result.inserted_count), ("ok", 0, 0))

    def test_out_of_scope_nucleos_are_skipped_not_stored(self) -> None:
        """La fixture de MP-004 mezcla deliberadamente 7 entidades de Madrid
        (prefijo `10`) con 3 de otros núcleos (`20`/`30`/`40`) para probar la
        colisión C5. El colector debe descartarlas (ADR-0008/ADR-0001: MVP
        acotado a Madrid), no almacenarlas."""
        fetcher = lambda url, timeout: self.body  # noqa: E731
        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=fetcher)

        self.assertEqual(result.inserted_count, 7)
        self.assertEqual(result.skipped_count, 3)

        # Filtrado por `ingestion_run_id`, no por el total de la tabla: la base
        # local puede ya contener datos reales de ejecuciones previas del
        # colector (p. ej. un soak test), y ese dato real no debe invalidar
        # este test ni este test debe borrarlo para "limpiar".
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM vehicle_position_observation WHERE ingestion_run_id = %s",
                (result.run_id,),
            )
            (stored_rows,) = cur.fetchone()
        self.assertEqual(stored_rows, 7)

    def test_repeated_identical_payload_stores_a_single_row_per_entity(self) -> None:
        fetcher = lambda url, timeout: self.body  # noqa: E731

        first = run_cycle(self.feed, self.conn, _POLICY, fetcher=fetcher)
        self.assertEqual(first.status, "ok")
        self.assertGreater(first.inserted_count, 0)
        self.assertEqual(first.deduped_count, 0)

        second = run_cycle(self.feed, self.conn, _POLICY, fetcher=fetcher)
        self.assertEqual(second.status, "ok")
        self.assertEqual(second.inserted_count, 0, "un payload idéntico no debe insertar filas nuevas")
        self.assertEqual(second.deduped_count, first.inserted_count)

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM vehicle_position_observation WHERE ingestion_run_id = %s",
                (first.run_id,),
            )
            (stored_rows,) = cur.fetchone()
        self.assertEqual(
            stored_rows,
            first.inserted_count,
            "las filas del primer ciclo deben ser exactamente una por entidad",
        )

    def test_changed_entity_inserts_exactly_one_new_row(self) -> None:
        fetcher = lambda url, timeout: self.body  # noqa: E731
        first = run_cycle(self.feed, self.conn, _POLICY, fetcher=fetcher)

        payload = json.loads(self.body)
        payload["entity"][0]["vehicle"]["currentStatus"] = "IN_TRANSIT_TO"
        modified_body = json.dumps(payload).encode("utf-8")
        modified_fetcher = lambda url, timeout: modified_body  # noqa: E731

        second = run_cycle(self.feed, self.conn, _POLICY, fetcher=modified_fetcher)
        self.assertEqual(second.inserted_count, 1)
        self.assertEqual(second.deduped_count, first.inserted_count - 1)

    def test_tied_observed_at_does_not_break_dedup_on_third_cycle(self) -> None:
        """Regresión (hallazgo real de la revisión de Codex en MP-007,
        reproducido de forma independiente): la fixture no cambia el campo
        `timestamp` de la entidad al simular un cambio real, así que el
        `observed_at` del ciclo 1 y el ciclo 2 (cambiado) quedan EMPATADOS
        para el mismo vehículo. Sin un desempate determinista en
        `latest_payload_hash` (`ORDER BY observed_at DESC` sin más), un
        tercer ciclo que repite el payload cambiado podía compararse contra
        la fila vieja (empatada) en vez de la nueva, insertando una fila
        duplicada en vez de deduplicar. `id DESC` como desempate lo corrige."""
        fetcher = lambda url, timeout: self.body  # noqa: E731
        first = run_cycle(self.feed, self.conn, _POLICY, fetcher=fetcher)

        payload = json.loads(self.body)
        payload["entity"][0]["vehicle"]["currentStatus"] = "IN_TRANSIT_TO"
        changed_body = json.dumps(payload).encode("utf-8")
        changed_fetcher = lambda url, timeout: changed_body  # noqa: E731

        second = run_cycle(self.feed, self.conn, _POLICY, fetcher=changed_fetcher)
        self.assertEqual((second.inserted_count, second.deduped_count), (1, first.inserted_count - 1))

        third = run_cycle(self.feed, self.conn, _POLICY, fetcher=changed_fetcher)
        self.assertEqual(
            (third.inserted_count, third.deduped_count),
            (0, first.inserted_count),
            "repetir el mismo payload cambiado no debe insertar una fila nueva",
        )

        changed_vehicle_id = json.loads(self.body)["entity"][0]["vehicle"]["vehicle"]["id"]
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM vehicle_position_observation "
                "WHERE source_vehicle_id = %s AND ingestion_run_id IN (%s, %s, %s)",
                (changed_vehicle_id, first.run_id, second.run_id, third.run_id),
            )
            (rows_for_vehicle,) = cur.fetchone()
        self.assertEqual(rows_for_vehicle, 2, "1 fila del estado inicial + 1 del cambio, nunca 3")


class StationAlertPersistenceTests(unittest.TestCase):
    """Hallazgo real de MP-017 (`docs/hitos/hito-03/referencia/01-auditoria-live.md`,
    P1 "Avisos de estación"): Renfe publica avisos por `stopId` sin `routeId`
    -- el cuerpo del payload de abajo es la fila real capturada
    (`AVISO_527127`, `stopId=60104`, Valdemoro, captura del kit de Hito 3 del
    2026-11-20), no un invento; se incluye aquí embebida para no depender de
    `data/hito-03/` (fuera de Git) en los tests de CI."""

    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        self.conn.execute("SELECT 1")
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.feed = FeedConfig("alerts", "https://example.invalid/alerts.json")

    def _alerts_body(self, informed_entity: list[dict]) -> bytes:
        return json.dumps(
            {
                "header": {"gtfsRealtimeVersion": "2.0", "timestamp": "1795075500"},
                "entity": [
                    {
                        "id": "AVISO_527127",
                        "alert": {
                            "activePeriod": [{"start": "1795075500"}],
                            "informedEntity": informed_entity,
                            "descriptionText": {
                                "translation": [
                                    {
                                        "text": "Ascensor de la estación de Valdemoro fuera de servicio.",
                                        "language": "es",
                                    }
                                ]
                            },
                        },
                    }
                ],
            }
        ).encode()

    def test_station_alert_without_route_id_is_skipped_when_no_catalog_given(self) -> None:
        """Comportamiento anterior conservado por defecto: sin `madrid_stop_ids`,
        un aviso solo por `stopId` sigue descartándose como fuera de alcance --
        documentado, no silenciosamente "arreglado" sin que el llamante aporte
        el catálogo real."""
        body = self._alerts_body([{"stopId": "60104"}])
        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=lambda *_: body)
        self.assertEqual((result.status, result.inserted_count, result.skipped_count), ("ok", 0, 1))

    def test_station_alert_without_route_id_is_persisted_with_madrid_stop_catalog(self) -> None:
        body = self._alerts_body([{"stopId": "60104"}])
        result = run_cycle(
            self.feed,
            self.conn,
            _POLICY,
            fetcher=lambda *_: body,
            madrid_stop_ids=frozenset({"60104"}),
        )
        self.assertEqual((result.status, result.inserted_count, result.skipped_count), ("ok", 1, 0))

    def test_station_alert_for_a_stop_outside_the_given_catalog_is_still_skipped(self) -> None:
        """No se "adivina" Madrid por tener cualquier `stopId`: solo se acepta
        si el `stop_id` está realmente en el catálogo cargado."""
        body = self._alerts_body([{"stopId": "99999"}])
        result = run_cycle(
            self.feed,
            self.conn,
            _POLICY,
            fetcher=lambda *_: body,
            madrid_stop_ids=frozenset({"60104"}),
        )
        self.assertEqual((result.status, result.inserted_count, result.skipped_count), ("ok", 0, 1))


class FetchFailureHandlingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = _connect_or_skip()
        # Abrir una transacción ambiente ANTES de cualquier `run_cycle`: así,
        # cada `with conn.transaction()` interno de `db.py` se anida como
        # SAVEPOINT de esta transacción en vez de hacer su propio COMMIT de
        # nivel superior (lo que ocurriría si fuera la primera instrucción de
        # la conexión) -- de lo contrario `self.conn.rollback()` no deshace
        # esos commits aislados y el test deja filas huérfanas en la base real.
        self.conn.execute("SELECT 1")
        # addCleanup es LIFO: registrar close() primero para que rollback()
        # (registrado después) se ejecute antes, sobre una conexión aún abierta.
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.feed = FeedConfig("vehicle_positions", "https://example.invalid/vehicle_positions.json")

    def test_persistent_network_failure_is_recorded_without_raising(self) -> None:
        def always_fails(url: str, timeout: float) -> bytes:
            raise ConnectionError("simulated network outage")

        result = run_cycle(self.feed, self.conn, _POLICY, fetcher=always_fails)

        self.assertEqual(result.status, "error")
        self.assertEqual(result.inserted_count, 0)
        self.assertIsNotNone(result.error)

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM source_ingestion_run WHERE feed_name = %s ORDER BY id DESC LIMIT 1",
                (self.feed.name,),
            )
            (status,) = cur.fetchone()
        self.assertEqual(status, "error")


if __name__ == "__main__":
    unittest.main()
