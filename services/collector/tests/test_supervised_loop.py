"""Comportamiento del bucle del colector ante fallos (MP-021).

Lo que se fija aquí es la diferencia -- encontrada operando de verdad -- entre
dos fallos que antes se trataban igual:

- un **fallo de un feed** (red, payload raro) no debe tumbar el colector: se
  registra y el bucle sigue con el siguiente feed. Comportamiento de MP-006,
  intacto;
- una **conexión perdida con PostgreSQL** sí debe terminar el proceso, porque
  la conexión vive fuera del bucle y ningún ciclo posterior podrá escribir.
  Reproducido reiniciando el contenedor de PostgreSQL con el colector en
  marcha: el proceso seguía vivo 90 s después, consumiendo los tres feeds cada
  30 s y descartándolos, con el recuento de `source_ingestion_run` congelado.
  Un proceso vivo que no ingiere es peor que uno muerto: nadie lo reinicia
  porque nadie lo ve caer.

Sin PostgreSQL ni red: se sustituyen `psycopg.connect`, `run_cycle`,
`load_feed` y `time.sleep`, porque lo que se prueba es el **manejo de errores
del bucle**, no la ingesta (que ya tiene sus tests de integración reales en
`test_collector_cycle.py`).
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest import mock

import psycopg

from services.collector import __main__ as collector_main


@contextmanager
def _fake_connection():
    yield mock.MagicMock(name="connection")


class SupervisedLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        patches = [
            mock.patch.dict("os.environ", {
                "MADRID_PULSE_ENV": "test",
                "MADRID_PULSE_DATABASE_URL": "postgresql://integration@127.0.0.1/integration",
            }, clear=True),
            mock.patch.object(collector_main.psycopg, "connect", lambda *a, **k: _fake_connection()),
            mock.patch.object(collector_main, "require_disposable_database"),
            mock.patch.object(collector_main, "_load_madrid_stop_ids", lambda source: None),
            mock.patch.object(collector_main.time, "sleep", lambda seconds: None),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_a_lost_database_connection_exits_with_ex_tempfail(self) -> None:
        with mock.patch.object(
            collector_main, "run_cycle", side_effect=psycopg.OperationalError("the connection is lost")
        ) as run_cycle:
            with self.assertRaises(SystemExit) as raised:
                collector_main.main()
        self.assertEqual(raised.exception.code, collector_main.EXIT_DATABASE_LOST)
        self.assertEqual(raised.exception.code, 75, "EX_TEMPFAIL: fallo temporal, reintentar tiene sentido")
        self.assertEqual(
            run_cycle.call_count,
            1,
            "no debe intentarse con los demás feeds: la conexión está perdida para todos",
        )

    def test_a_single_feed_failure_does_not_stop_the_collector(self) -> None:
        """Comportamiento de MP-006, que esta tarea NO cambia."""
        calls: list[str] = []

        def flaky(feed, conn, policy, madrid_stop_ids=None):
            calls.append(feed.name)
            if len(calls) == 1:
                raise RuntimeError("payload inesperado en el primer feed")
            if len(calls) >= 3:
                # Corta el bucle infinito una vez probado lo que interesa: los
                # tres feeds del ciclo se intentaron pese al fallo del primero.
                raise KeyboardInterrupt
            return None

        with mock.patch.object(collector_main, "run_cycle", side_effect=flaky):
            with self.assertRaises(KeyboardInterrupt):
                collector_main.main()
        self.assertEqual(
            calls,
            ["vehicle_positions", "trip_updates", "alerts"],
            "un fallo en el primer feed no debe impedir los otros dos",
        )


if __name__ == "__main__":
    unittest.main()
