"""Medir el salto al expirar con el mismo GPS y las mismas dos consultas."""
from datetime import timedelta

from apps.api import db, snapshot
from tests.e2e.test_stop_state import RealStops

RealStops.setUpClass()
for profile in (None, "discordante"):
    jumps = []
    for vid, pos in RealStops.second.items():
        row = db.ObservedRow(pos, pos.observed_at, ingestion_run_id=100, anchor_profile=profile)
        previous = RealStops.first[vid]
        history = db.VehicleHistory(vid, row, db.ObservedRow(previous, previous.observed_at))
        progress = []
        for age in (180, 181):
            at = pos.observed_at + timedelta(seconds=age)
            entry = snapshot.build_vehicle_entry(
                RealStops.network, RealStops.config, history, None, at, at,
                RealStops.network.service_date_resolver(at))
            progress.append(entry.rendered.progress_m)
        jumps.append(progress[0] - progress[1])
    print(f"huella={profile}, retrocesos={sum(d > 0 for d in jumps)}/{len(jumps)}, máximo={max(jumps):.6f} m")
