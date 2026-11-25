"""Configuración PostgreSQL y comprobación de aislamiento de Madrid Pulse."""

from __future__ import annotations

import os
import socket
from collections.abc import Mapping
from ipaddress import ip_address

import psycopg
from psycopg.conninfo import conninfo_to_dict

DATABASE_URL_ENV = "MADRID_PULSE_DATABASE_URL"
DATABASE_ENV = "MADRID_PULSE_ENV"
DISPOSABLE_ENVIRONMENTS = {"test", "replay"}
ENVIRONMENTS = DISPOSABLE_ENVIRONMENTS | {"dev", "live"}
ALLOW_SHARED_DEV_ENV = "MADRID_PULSE_ALLOW_SHARED_DEV_DB"
# Puerto reservado por infra/docker para el PostgreSQL de desarrollo compartido.
SHARED_DEV_PORT = 0x1539
DISPOSABLE_MARKER = "madrid-pulse:disposable"

MARKER_QUERY = """
    SELECT pg_catalog.shobj_description(oid, 'pg_database')
    FROM pg_catalog.pg_database
    WHERE datname = current_database()
"""


class DatabaseConfigurationError(ValueError):
    """La configuración no satisface las reglas de conexión o aislamiento."""


def _is_local(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host == "localhost" or host.startswith("/"):
        return True
    try:
        address = ip_address(host)
    except ValueError:
        try:
            # libpq también admite IPv4 abreviadas como 127.1.
            address = ip_address(socket.inet_aton(host))
        except OSError:
            return False
    address = getattr(address, "ipv4_mapped", None) or address
    return address.is_loopback or address.is_unspecified


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
        and _is_local(hostaddr or host)
        and (environment in DISPOSABLE_ENVIRONMENTS or not allow_shared_dev)
    ):
        raise DatabaseConfigurationError(
            f"Destino PostgreSQL local compartido (puerto {SHARED_DEV_PORT}) rechazado. "
            f"Usa otra base o consulta {ALLOW_SHARED_DEV_ENV} para dev/live."
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
