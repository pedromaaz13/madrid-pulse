"""Reloj explícito para pruebas, acotado a los módulos que lo consumen."""

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import patch


def frozen_datetime(instant: datetime) -> type[datetime]:
    if instant.utcoffset() is None:
        raise ValueError("El reloj de pruebas requiere zona horaria explícita")

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return instant.astimezone().replace(tzinfo=None)
            return instant.astimezone(tz)

    return FrozenDatetime


@contextmanager
def api_wall_clock(instant: datetime):
    from apps.api import gtfs_source, main, snapshot

    clock = frozen_datetime(instant)
    with (
        patch.object(main, "now_utc", lambda: clock.now(timezone.utc)),
        patch.object(gtfs_source, "datetime", clock),
        patch.object(snapshot, "datetime", clock),
    ):
        yield
