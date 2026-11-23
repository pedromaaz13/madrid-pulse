"""AUD-04 (corrección post-revisión 2): ¿cuál es la ventana REAL de alcanzabilidad de `dwell_until`?

El revisor corrige la sobreafirmación «estructuralmente inalcanzable». Esta prueba
barre el progreso del ancla alrededor del tramo plano real de Fuenlabrada y mide, por
separado, las dos condiciones que tienen que cumplirse:
  1) `dwell_end_seconds` devuelve algo (tolerancia +-1,0 m), y
  2) la guarda `anchor_at < candidate < horizon_end` de `_envelope` no lo descarta.
"""
from __future__ import annotations
import sys
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.geo import build_madrid_corridor_catalog
from packages.gtfs import build_catalog, load_feed
from packages.movement.model import MovementThresholds
from packages.movement.rendering import _envelope
from packages.movement.schedule import build_trip_schedule, service_seconds

MADRID = ZoneInfo("Europe/Madrid"); TH = MovementThresholds()
R = Path("data/hito-03/replay"); TARGET = "1023V19656C5"
FLAT = 41193.35          # progreso del tramo plano (espera de 60 s en Fuenlabrada)
ANCHOR_REAL = 41198.73   # progreso del ancla real del corte 1533

topo = load_feed(R / "fomento_transit.zip", network_id="10")
cat = build_catalog(topo, gtfs_version="aud04")
corr = build_madrid_corridor_catalog(cat, topo, fixtures_root=Path("tests/fixtures"))
tr = {t.trip_id: t.route_id for t in topo.trips}
times = topo.stop_times_for_trip(TARGET)
cov = corr.coverage_for_stops(tr[TARGET], tuple(i.stop_id for i in times))
sch = build_trip_schedule(topo, cov.corridor, TARGET)

from datetime import datetime, timezone
anchor_at = datetime(2026, 11, 20, 14, 33, 21, tzinfo=timezone.utc)
sd = anchor_at.astimezone(MADRID).date()
horizon_end = anchor_at + timedelta(seconds=190)

print(f"tramo plano en {FLAT:.2f} m; ancla real del corte en {ANCHOR_REAL:.2f} m "
      f"(+{ANCHOR_REAL-FLAT:.2f} m)\n")
print(f"{'offset vs plano':>16} {'dwell_end_seconds':>18} {'dwell_until publicado':>22} "
      f"{'avance a 30 s':>14}")
ok_lo = ok_hi = None
for off in (-3.0, -2.0, -1.5, -1.01, -1.0, -0.999, -0.99, -0.95, -0.9, -0.5, -0.01, 0.0,
            0.01, 0.5, 0.99, 1.0, 1.01, 2.0, 5.38):
    prog = FLAT + off
    end = sch.dwell_end_seconds(prog)
    env = _envelope(schedule=sch, service_date=sd, anchor_at=anchor_at,
                    anchor_progress_m=prog, horizon_end=horizon_end,
                    max_speed_mps=TH.max_estimated_speed_kmh / 3.6)
    adv = env.progress_at(anchor_at + timedelta(seconds=30)) - prog
    pub = env.dwell_until is not None
    if pub:
        ok_lo = off if ok_lo is None else min(ok_lo, off)
        ok_hi = off if ok_hi is None else max(ok_hi, off)
    print(f"{off:>+14.3f} m {('None' if end is None else f'{end:.0f}'):>18} "
          f"{('SI' if pub else 'no'):>22} {adv:>12.1f} m")

print(f"\nventana en la que `dwell_until` SE PUEBLA: offset en [{ok_lo:+.3f}, {ok_hi:+.3f}] m "
      f"respecto al tramo plano (anchura ~1 m)")
print("  condicion 1 (dwell_end_seconds, tolerancia +-1,0 m): offset en [-1,00, +1,00]")
print("  condicion 2 (guarda anchor_at < candidate de _envelope): recorta el lado positivo")
print(f"=> la rama existe y es alcanzable, pero su anchura efectiva es de ~1 m "
      f"sobre un recorrido de {sch.points[-1].progress_m:.0f} m")
print(f"   el ancla real del corte quedo a +{ANCHOR_REAL-FLAT:.2f} m, fuera de la ventana")
