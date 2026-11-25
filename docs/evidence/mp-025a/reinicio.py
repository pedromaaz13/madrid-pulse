"""Prueba manual F1 en tres procesos sobre PostgreSQL marcado y desechable.

Ejecutar desde la raíz con PYTHONPATH=. y las acciones seed, end y stale. Los runs confirmados sobreviven al proceso.
"""
import sys
from datetime import timedelta

from apps.api import db, snapshot
from services.collector import db as writer
from tests.e2e.test_stop_state import RealStops
from tests.postgres import connect_disposable_or_skip


def main(action):
    RealStops.setUpClass()
    network = RealStops.network
    pos = RealStops.second["19667"]
    pos = pos.model_copy(update={"source_vehicle_id": "mp025a-reinicio-19667"})
    anchor = pos.observed_at
    with connect_disposable_or_skip() as conn:
        if action == "seed":
            conn.execute("SELECT set_config('madrid_pulse.anchor_profile',%s,true)",
                         (network.anchor_profile(network.engine.thresholds),))
            run = writer.insert_ingestion_run(conn, feed_name="vehicle_positions",
                                              source_timestamp=anchor, started_at=anchor,
                                              finished_at=anchor, status="ok",entity_count=1,
                                              payload_hash=pos.payload_hash)
            writer.insert_vehicle_position_observation(conn, pos, received_at=anchor,
                                                       ingestion_run_id=run)
            return
        at = anchor + timedelta(seconds={"end": 180, "stale": 181}[action])
        hist = next(h for h in db.latest_vehicle_histories(conn, as_of=at)
                    if h.source_vehicle_id == pos.source_vehicle_id)
        vehicle = snapshot.build_vehicle_entry(network,RealStops.config,hist,None,at,at,
                                               network.service_date_resolver(at))
        rendered = vehicle.rendered
        assert rendered.progress_m > rendered.last_confirmed_progress_m
        if action == "stale":
            assert rendered.frozen_basis == "authorized_envelope_end"
        print(rendered.progress_m)


if __name__ == "__main__":
    main(sys.argv[1])
