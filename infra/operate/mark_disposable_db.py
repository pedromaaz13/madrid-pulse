"""Marca una base recién creada: python -m infra.operate.mark_disposable_db."""

import psycopg
from psycopg import sql

from packages.database import (
    DISPOSABLE_ENVIRONMENTS,
    DISPOSABLE_MARKER,
    DatabaseConfigurationError,
    database_settings_from_env,
)


def main() -> None:
    try:
        url, environment = database_settings_from_env()
        if environment not in DISPOSABLE_ENVIRONMENTS:
            raise DatabaseConfigurationError("Para marcar la base, usa MADRID_PULSE_ENV=test o replay.")
    except DatabaseConfigurationError as exc:
        raise SystemExit(str(exc)) from None

    with psycopg.connect(url) as conn:
        conn.execute(
            sql.SQL("COMMENT ON DATABASE {} IS {}").format(
                sql.Identifier(conn.info.dbname), sql.Literal(DISPOSABLE_MARKER),
            )
        )
    print("Base PostgreSQL marcada como desechable.")


if __name__ == "__main__":
    main()
