"""Configuración PostgreSQL y comprobación de aislamiento de Madrid Pulse."""

from __future__ import annotations

import os
from collections.abc import Mapping

import psycopg
from psycopg.conninfo import conninfo_to_dict

DATABASE_URL_ENV = "MADRID_PULSE_DATABASE_URL"
DATABASE_ENV = "MADRID_PULSE_ENV"
DISPOSABLE_ENVIRONMENTS = {"test", "replay"}
ENVIRONMENTS = DISPOSABLE_ENVIRONMENTS | {"dev", "live"}
ALLOW_SHARED_DEV_ENV = "MADRID_PULSE_ALLOW_SHARED_DEV_DB"
# Puerto del PostgreSQL de desarrollo compartido (infra/docker/docker-compose.yml).
SHARED_DEV_PORT = 5433
DISPOSABLE_MARKER = "madrid-pulse:disposable"

MARKER_QUERY = """
    SELECT pg_catalog.shobj_description(oid, 'pg_database')
    FROM pg_catalog.pg_database
    WHERE datname = current_database()
"""


class DatabaseConfigurationError(ValueError):
    """La configuración no satisface las reglas de conexión o aislamiento."""


def validate_database_url(
    url: str,
    environment: str,
    *,
    allow_shared_dev: bool = False,
    libpq_env: Mapping[str, str] | None = None,
) -> None:
    """Valida el destino efectivo de libpq sin resolver DNS ni abrir conexiones."""
    if not url.startswith(("postgresql://", "postgres://")):
        raise DatabaseConfigurationError(f"{DATABASE_URL_ENV} debe ser una URL PostgreSQL.")
    try:
        params = conninfo_to_dict(url)
    except psycopg.ProgrammingError:
        raise DatabaseConfigurationError(f"{DATABASE_URL_ENV} no es una URL PostgreSQL válida.") from None

    libpq_env = libpq_env or {}
    host = params.get("host", "")
    hostaddr = params.get("hostaddr", "")
    if not host or "," in host or "," in hostaddr:
        raise DatabaseConfigurationError(f"{DATABASE_URL_ENV} debe indicar un solo host PostgreSQL.")
    if "service" in params or libpq_env.get("PGSERVICE"):
        raise DatabaseConfigurationError(f"{DATABASE_URL_ENV} no admite servicios libpq.")
    if not hostaddr and libpq_env.get("PGHOSTADDR"):
        raise DatabaseConfigurationError(
            f"{DATABASE_URL_ENV} no admite un destino heredado de PGHOSTADDR."
        )
    if not params.get("port") and libpq_env.get("PGPORT"):
        raise DatabaseConfigurationError(f"Indica el puerto en {DATABASE_URL_ENV}, sin PGPORT.")
    port = (params.get("port") or "5432").lstrip("0")
    if not port.isascii() or not port.isdecimal() or len(port) > 5 or int(port) > 65535:
        raise DatabaseConfigurationError(f"El puerto de {DATABASE_URL_ENV} no es válido.")
    if (
        int(port) == SHARED_DEV_PORT
        and not (allow_shared_dev and environment in {"dev", "live"})
    ):
        raise DatabaseConfigurationError(
            f"Puerto PostgreSQL compartido ({SHARED_DEV_PORT}) rechazado en cualquier host. "
            f"Usa otro puerto o consulta {ALLOW_SHARED_DEV_ENV} para dev/live en "
            "docs/operations/DATABASE_ISOLATION.md."
        )


def database_settings_from_env() -> tuple[str, str]:
    """Devuelve (URL, entorno) obligatorios, validados antes de la conexión."""
    url = os.environ.get(DATABASE_URL_ENV, "").strip()
    if not url:
        message = f"Define {DATABASE_URL_ENV} con una URL PostgreSQL explícita."
        if "MADRID_PULSE_DATABASE_DSN" in os.environ:
            message += " MADRID_PULSE_DATABASE_DSN está obsoleta."
        raise DatabaseConfigurationError(message)

    environment = os.environ.get(DATABASE_ENV, "").strip()
    if environment not in ENVIRONMENTS:
        raise DatabaseConfigurationError(f"Define {DATABASE_ENV} como dev, test, replay o live.")

    validate_database_url(
        url,
        environment,
        allow_shared_dev=os.environ.get(ALLOW_SHARED_DEV_ENV) == "1",
        libpq_env=os.environ,
    )
    return url, environment


def require_disposable_database(conn: psycopg.Connection) -> None:
    """Consulta el comentario de la base activa antes de permitir escrituras."""
    if conn.execute(MARKER_QUERY).fetchone() != (DISPOSABLE_MARKER,):
        raise DatabaseConfigurationError(
            f"Base PostgreSQL sin marca desechable ({DISPOSABLE_MARKER}). "
            "Consulta docs/operations/DATABASE_ISOLATION.md."
        )
