"""EXPLAIN y latencia de la consulta de producción, con el instante de la revisión."""

from datetime import datetime, timezone
from time import perf_counter
from unittest.mock import MagicMock

from apps.api import db
from tests.postgres import connect_disposable_or_skip

at = datetime(2026, 11, 24, 8, tzinfo=timezone.utc)
with connect_disposable_or_skip() as conn:
    # Capturar el SQL real sin mantener una copia separada.
    mock = MagicMock()
    db.latest_vehicle_histories(mock, as_of=at)
    query, params = mock.cursor.return_value.__enter__.return_value.execute.call_args.args
    for row in conn.execute("EXPLAIN (ANALYZE, BUFFERS) " + query, params):
        print(row[0], flush=True)
    for _ in range(3):
        start = perf_counter()
        histories = db.latest_vehicle_histories(conn, as_of=at)
        print(
            len(histories), "vehículos", round((perf_counter() - start) * 1000, 2), "ms", flush=True
        )
