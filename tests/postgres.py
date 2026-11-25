"""Conexión PostgreSQL verificada para las pruebas de integración."""

from __future__ import annotations

import unittest

import psycopg

from packages.database import (
    DISPOSABLE_ENVIRONMENTS,
    DatabaseConfigurationError,
    database_settings_from_env,
    require_disposable_database,
)


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
        raise unittest.SkipTest(str(exc)) from None
    except psycopg.OperationalError:
        raise unittest.SkipTest("PostgreSQL de integración no disponible.") from None
    return conn
