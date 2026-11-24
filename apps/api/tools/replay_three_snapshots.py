"""Evidencia reproducible de MP-019: tres snapshots sobre capturas REALES.

Ingesta las capturas congeladas `1532` y `1533` del kit de Hito 3 con el
colector real (`run_cycle` con un `fetcher` inyectado, mismo patrón que
`tests/e2e/test_replay.py`) y construye cuatro snapshots: dos normales, uno
parcial (el feed `trip_updates` devuelve JSON inválido) y uno congelado (el
colector se detiene y el reloj avanza una hora).

**No es un test del repositorio y no está en CI**: necesita `data/hito-03/`
(fuera de Git, se repone con `instalar.py --solo-datos`) y el ZIP GTFS completo
del núcleo. Debe ejecutarse contra un PostgreSQL **fresco y desechable**, no
contra la base de desarrollo: escribe y hace `commit` de verdad, porque el
objetivo es precisamente observar la revisión monotónica entre sondeos.

Resultado registrado en `docs/evidence/mp-019-tres-snapshots-replay.md`.

Uso:

    PYTHONPATH="$PWD" \
    MADRID_PULSE_GTFS_SOURCE="$PWD/data/hito-03/replay/fomento_transit.zip" \
    MADRID_PULSE_SHORT_NAME= MADRID_PULSE_MODE=replay \
    MADRID_PULSE_DATABASE_URL=postgresql://...:5434/madrid_pulse \
    MADRID_PULSE_DATABASE_DSN=postgresql://...:5434/madrid_pulse \
      .venv/bin/python -m apps.api.tools.replay_three_snapshots
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg

from apps.api import snapshot
from apps.api.config import ApiConfig
from apps.api.gtfs_source import load_network
from services.collector.collector import run_cycle
from services.collector.config import CollectorConfig, FeedConfig
from services.collector.http_client import RetryPolicy

REPLAY = Path("data/hito-03/replay")
POLICY = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=5.0)
CAP_1532 = datetime(2026, 11, 20, 14, 32, 4, tzinfo=timezone.utc)
CAP_1533 = datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc)

config = ApiConfig.from_env()
network = load_network(config)
conn = psycopg.connect(CollectorConfig.from_env().database_url, autocommit=False)


def ingest(sample: str, at: datetime) -> None:
    for feed_name in ("vehicle_positions", "trip_updates", "alerts"):
        body = (REPLAY / sample / f"{feed_name}.json").read_bytes()
        feed = FeedConfig(feed_name, f"https://example.invalid/{feed_name}.json")
        result = run_cycle(feed, conn, POLICY, fetcher=lambda url, timeout: body, now=lambda: at)
        print(f"  ingest {sample}/{feed_name}: status={result.status} "
              f"entities={result.entity_count} inserted={result.inserted_count} "
              f"deduped={result.deduped_count} skipped={result.skipped_count} "
              f"error={result.error}")
    conn.commit()


def summary(label: str, snap) -> dict:
    methods: dict[str, int] = {}
    spaces: dict[str, int] = {}
    for vehicle in snap.vehicles:
        methods[vehicle.rendered.rendering_method] = methods.get(vehicle.rendered.rendering_method, 0) + 1
        key = vehicle.rendered.coordinate_space or "none"
        spaces[key] = spaces.get(key, 0) + 1
    return {
        "label": label,
        "generated_at": snap.generated_at.isoformat(),
        "snapshot_id": snap.snapshot_id,
        "revision": {"scope": snap.revision.scope, "sequence": snap.revision.sequence},
        "vehicles_total": snap.counts.vehicles_total,
        "rendering_methods": dict(sorted(methods.items())),
        "coordinate_spaces": dict(sorted(spaces.items())),
        "with_operator_delay": snap.counts.with_operator_delay,
        "without_operator_delay": snap.counts.without_operator_delay,
        "feeds": {f.feed_name: f.status for f in snap.feeds},
        "degraded": [{"resource": d.resource, "status": d.status} for d in snap.degraded],
    }


print("== Ingesta de la captura 1532 ==")
ingest("1532", CAP_1532)
snap_a = snapshot.build_snapshot(conn, network, config, CAP_1532 + timedelta(seconds=10))
print(json.dumps(summary("A normal (1532)", snap_a), indent=1, ensure_ascii=False))

print("== Ingesta de la captura 1533 ==")
ingest("1533", CAP_1533)
snap_b = snapshot.build_snapshot(conn, network, config, CAP_1533 + timedelta(seconds=10))
print(json.dumps(summary("B normal (1533)", snap_b), indent=1, ensure_ascii=False))

# Movimiento real entre las dos capturas sobre un patrón validado.
by_id_a = {v.vehicle_id: v for v in snap_a.vehicles}
moved = []
for vehicle in snap_b.vehicles:
    before = by_id_a.get(vehicle.vehicle_id)
    if (
        before is not None
        and before.map_matched is not None
        and vehicle.map_matched is not None
        and vehicle.map_matched.progress_m != before.map_matched.progress_m
    ):
        moved.append(
            {
                "vehicle_id": vehicle.vehicle_id,
                "line": vehicle.line,
                "pattern_id": vehicle.pattern_id,
                "progress_m_1532": round(before.map_matched.progress_m, 1),
                "progress_m_1533": round(vehicle.map_matched.progress_m, 1),
                "distance_from_raw_m": round(vehicle.map_matched.distance_from_raw_m, 1),
                "rendering_method": vehicle.rendered.rendering_method,
                "envelope_speed_mps": (
                    round(vehicle.rendered.progress_envelope.speed_mps, 2)
                    if vehicle.rendered.progress_envelope
                    else None
                ),
            }
        )
print(f"== Vehículos map-matcheados que avanzaron entre 1532 y 1533: {len(moved)} ==")
print(json.dumps(moved[:5], indent=1, ensure_ascii=False))

# C) Fallo parcial: `trip_updates` devuelve JSON inválido en el sondeo siguiente.
print("== C) fallo parcial de trip_updates (JSON inválido) ==")
partial_at = CAP_1533 + timedelta(seconds=80)
feed = FeedConfig("trip_updates", "https://example.invalid/trip_updates.json")
result = run_cycle(
    feed, conn, POLICY, fetcher=lambda url, timeout: b"{not json", now=lambda: partial_at
)
print(f"  ciclo trip_updates: status={result.status} error={(result.error or '')[:70]}")
conn.commit()
snap_c = snapshot.build_snapshot(conn, network, config, partial_at + timedelta(seconds=5))
print(json.dumps(summary("C parcial", snap_c), indent=1, ensure_ascii=False))

# D) Congelado: el colector se detiene, el reloj avanza.
print("== D) congelado (colector detenido, reloj +1 h) ==")
frozen_at = CAP_1533 + timedelta(hours=1)
snap_d = snapshot.build_snapshot(conn, network, config, frozen_at)
print(json.dumps(summary("D congelado", snap_d), indent=1, ensure_ascii=False))

print("== Invariantes comprobadas ==")
checks = {
    "revision_monotonica_en_ambito": (
        snap_b.revision.sequence > snap_a.revision.sequence
        and snap_c.revision.sequence > snap_b.revision.sequence
        and snap_a.revision.scope == snap_d.revision.scope
    ),
    "snapshot_id_declarado_no_ordenable": snap_a.snapshot_id_is_sortable is False,
    "parcial_no_vacia_vehiculos": len(snap_c.vehicles) == len(snap_b.vehicles),
    "parcial_degrada_solo_el_recurso_afectado": [
        d.resource for d in snap_c.degraded
    ] == ["delays_and_eta"],
    "congelado_conserva_el_ultimo_dato": len(snap_d.vehicles) == len(snap_b.vehicles),
    "congelado_no_rejuvenece": all(
        v.timestamps.gps_observed_at
        == {x.vehicle_id: x for x in snap_b.vehicles}[v.vehicle_id].timestamps.gps_observed_at
        for v in snap_d.vehicles
    ),
    "congelado_todo_stale_frozen_o_schedule": all(
        v.rendered.rendering_method in {"stale_frozen", "schedule_only", "unlocated"}
        for v in snap_d.vehicles
    ),
}
print(json.dumps(checks, indent=1))

print("== Recuentos finales en el contenedor fresco ==")
with conn.cursor() as cur:
    cur.execute(
        "SELECT (SELECT count(*) FROM vehicle_position_observation),"
        " (SELECT count(*) FROM trip_update_observation),"
        " (SELECT count(*) FROM service_alert),"
        " (SELECT count(*) FROM source_ingestion_run),"
        " (SELECT count(*) FROM data_quality_event)"
    )
    print(cur.fetchone())
conn.close()
