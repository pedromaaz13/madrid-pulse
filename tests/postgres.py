"""Conexión PostgreSQL verificada para las pruebas de integración."""

from __future__ import annotations

import os
import unittest

import psycopg

from packages.database import (
    DISPOSABLE_ENVIRONMENTS,
    DatabaseConfigurationError,
    database_settings_from_env,
    require_disposable_database,
)


def _database_test_error(message: str) -> AssertionError | unittest.SkipTest:
    if os.environ.get("MADRID_PULSE_REQUIRE_DB") == "1":
        return AssertionError(message)
    return unittest.SkipTest(message)


def connect_disposable_or_skip() -> psycopg.Connection:
    try:
        url, environment = database_settings_from_env()
        if environment not in DISPOSABLE_ENVIRONMENTS:
            raise DatabaseConfigurationError("Las pruebas PostgreSQL requieren MADRID_PULSE_ENV=test o replay.")
        conn = psycopg.connect(url, autocommit=False, connect_timeout=3)
        try:
            require_disposable_database(conn)
            conn.rollback()
        except BaseException:
            conn.close()
            raise
    except DatabaseConfigurationError as exc:
        raise _database_test_error(str(exc)) from None
    except psycopg.OperationalError:
        raise _database_test_error("PostgreSQL de integración no disponible.") from None
    return conn
