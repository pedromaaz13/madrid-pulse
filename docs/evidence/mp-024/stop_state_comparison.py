"""MP-024 (H4-00): evidencia comparativa offline del modelo de estado de parada.

Aplica la envolvente de PRODUCCIÓN (`beb9434`) y tres alternativas de diseño
(A: estado de parada del operador + ventana del viaje + tope por tramo;
B: acotación de `temporal_offset_s`, con y sin ventana de pre-salida;
C: segmentos hold/travel derivados solo del horario) a:

1. los cortes reales congelados `1532`/`1533` (2026-11-20, Renfe, núcleo 10),
   verificados por SHA-256 contra su `manifest.json`;
2. casos sintéticos (pre-salida, salida retrasada, parada intermedia,
   cancelación, stale, incoherencia GTFS y los dos cambios de hora de 2027).

Validación del arnés (ORCHESTRATION_POLICY §3.4), que el guion ejecuta y aborta
si falla:
  (a) cada constante de producción usada se localiza con `archivo:línea` y se
      comprueba contra el valor en tiempo de ejecución;
  (b) las entradas llevan SHA-256 y se verifican contra el manifiesto;
  (c) la línea base es `render_from_movement`/`_envelope` de producción (se
      comprueba que la envolvente publicada coincide 44/44 con `_envelope`
      evaluada en `valid_until`); las alternativas reutilizan primitivas de
      producción (`MovementEngine`, `TripSchedule`, `service_day_instant`,
      `ProgressEnvelope`) y solo añaden la regla de decisión que se compara;
  (d) se imprime el HEAD y se comprueba que `packages/`, `apps/`, `services/` e
      `infra/` son idénticos a `beb9434`.

Las alternativas son PROTOTIPOS DE DISEÑO para comparar criterios, no la
implementación de MP-025a. Las constantes de las alternativas (`TAU_STOP_M`,
`D_MIN_S`, `OFFSET_*`) son valores de arnés con barrido de sensibilidad, a
calibrar por MP-028; no son valores de diseño.

Sin red, sin base de datos, sin escritura salvo `--json <ruta>`.

Uso:
    python3 docs/evidence/mp-024/stop_state_comparison.py \
        --replay /ruta/a/data/hito-03/replay [--json salida.json]
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
import statistics
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from packages.contracts.canonical import VehiclePositionObservation
from packages.contracts.normalize import vehicle_positions_to_canonical
from packages.contracts.raw import RawVehiclePositionsFeed
from packages.geo import build_madrid_corridor_catalog, haversine_m
from packages.gtfs import Topology, build_catalog, load_feed
from packages.movement import MovementEngine
from packages.movement.model import MovementThresholds, PositionMode
from packages.movement.rendering import (
    ProgressEnvelope,
    _coordinate,
    _envelope,
    render_from_movement,
)
from packages.movement.schedule import (
    SchedulePoint,
    TripSchedule,
    build_trip_schedule,
    parse_gtfs_time,
    service_day_instant,
    service_seconds,
)

MADRID = ZoneInfo("Europe/Madrid")
BASELINE_COMMIT = "beb9434"
TH = MovementThresholds()
MAX_SPEED_MPS = TH.max_estimated_speed_kmh / 3.6
CALC_DELAY_S = 10.0  # reloj de la evidencia MP-019/AUD-09: calculated_at = ancla + 10 s
ADVANCE_EPS_M = 1.0  # «con avance» = más de 1 m sobre el ancla dentro del horizonte

# --- Constantes de ARNÉS (no de diseño): a calibrar por MP-028 --------------
TAU_STOP_M = 50.0  # radio de «zona de parada» sobre el progreso dirigido
TAU_SWEEP = (5.0, 20.8, 40.0, 50.0, 100.0)  # 20,8 m = p95 del error de proyección (AUD-04 §0.3)
D_MIN_S = 30.0  # retención mínima en parada de la alternativa C
D_MIN_SWEEP = (0.0, 30.0, 60.0, 180.0)
OFFSET_SYM_S = 600.0  # B1: ±operator_delay_max_age_s (apps/api/config.py), propuesta literal de AUD-01

# --- (a) constantes de producción con archivo:línea -----------------------
PRODUCTION_CONSTANTS = (
    ("packages/movement/model.py", r"observed_max_age_s: float = 60\.0", "observed_max_age_s", 60.0),
    ("packages/movement/model.py", r"stale_after_s: float = 180\.0", "stale_after_s", 180.0),
    ("packages/movement/model.py", r"max_estimated_speed_kmh: float = 160\.0", "max_estimated_speed_kmh", 160.0),
    ("packages/movement/model.py", r"max_estimated_acceleration_mps2: float = 1\.2",
     "max_estimated_acceleration_mps2", 1.2),
    ("packages/movement/schedule.py", r"def dwell_end_seconds\(.*tolerance_m: float = 1\.0", "tolerance_m", 1.0),
    ("packages/movement/rendering.py",
     r"valid_until = anchor_at \+ timedelta\(seconds=thresholds\.stale_after_s\)", "horizon=valid_until", None),
    ("packages/movement/rendering.py", r"horizon_end=valid_until,", "horizon_end=valid_until", None),
    ("packages/movement/rendering.py", r"if anchor_at < candidate < horizon_end:", "guarda dwell", None),
    ("apps/api/config.py", r'MADRID_PULSE_OPERATOR_DELAY_MAX_AGE_S", "600"', "operator_delay_max_age_s", 600.0),
    ("apps/api/config.py", r'MADRID_PULSE_DISPLAY_LAG_S", "0"', "display_lag_s", 0.0),
)


def locate(path: str, pattern: str) -> int:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]
    if len(hits) != 1:
        raise SystemExit(f"ARNÉS INVÁLIDO: {path} /{pattern}/ aparece {len(hits)} veces")
    return hits[0]


def validate_harness(replay: Path) -> dict:
    report: dict = {"constants": [], "inputs": {}, "head": None, "product_equals_baseline": None}
    runtime = {
        "observed_max_age_s": TH.observed_max_age_s,
        "stale_after_s": TH.stale_after_s,
        "max_estimated_speed_kmh": TH.max_estimated_speed_kmh,
        "max_estimated_acceleration_mps2": TH.max_estimated_acceleration_mps2,
        "tolerance_m": inspect.signature(TripSchedule.dwell_end_seconds).parameters["tolerance_m"].default,
    }
    for path, pattern, name, expected in PRODUCTION_CONSTANTS:
        line = locate(path, pattern)
        if expected is not None and name in runtime and runtime[name] != expected:
            raise SystemExit(f"ARNÉS INVÁLIDO: {name} vale {runtime[name]} en ejecución, se esperaba {expected}")
        report["constants"].append({"name": name, "where": f"{path}:{line}", "value": expected})
    manifest = json.loads((replay / "manifest.json").read_text())
    for name, digest in manifest["sha256"].items():
        actual = hashlib.sha256((replay / name).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"ARNÉS INVÁLIDO: SHA-256 de {name} = {actual} != manifiesto {digest}")
        report["inputs"][name] = actual
    report["inputs"]["manifest.json"] = hashlib.sha256((replay / "manifest.json").read_bytes()).hexdigest()
    git = ["git", "-C", str(ROOT)]
    report["head"] = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True,
                                    check=True).stdout.strip()
    diff = subprocess.run(git + ["diff", "--quiet", BASELINE_COMMIT, "--", "packages", "apps",
                                 "services", "infra"], check=False)
    report["product_equals_baseline"] = diff.returncode == 0
    if not report["product_equals_baseline"]:
        raise SystemExit(f"ARNÉS INVÁLIDO: el código de producto difiere de {BASELINE_COMMIT}")
    return report


# --- Contexto común por circulación ---------------------------------------
@dataclass(frozen=True)
class StopInfo:
    stop_id: str
    progress_m: float
    arrival_s: float
    departure_s: float


@dataclass
class Ctx:
    trip_id: str
    schedule: TripSchedule
    stops: tuple[StopInfo, ...]
    service_date: date
    anchor_at: datetime
    anchor_progress_m: float
    horizon_end: datetime
    status: str | None
    current_stop_id: str | None
    canceled: bool = False
    label: str = ""
    extra: dict = field(default_factory=dict)

    def instant(self, seconds: float) -> datetime:
        return service_day_instant(self.service_date, seconds)


def stops_for_trip(topo: Topology, corridor, schedule: TripSchedule, trip_id: str) -> tuple[StopInfo, ...]:
    """Paradas proyectadas con las MISMAS primitivas que `build_trip_schedule`."""
    by_id = {stop.stop_id: stop for stop in topo.stops}
    out = []
    for item in topo.stop_times_for_trip(trip_id):
        stop = by_id[item.stop_id]
        _, arc = corridor.project_station(stop.latitude, stop.longitude)
        arrival = parse_gtfs_time(item.arrival_time or item.departure_time)
        departure = parse_gtfs_time(item.departure_time or item.arrival_time)
        out.append(StopInfo(item.stop_id, schedule.directed_progress(arc), arrival, departure))
    sched_progress = sorted({round(p.progress_m, 6) for p in schedule.points})
    mine = sorted({round(s.progress_m, 6) for s in out})
    if sched_progress != mine:
        raise SystemExit(f"ARNÉS INVÁLIDO: paradas de {trip_id} no coinciden con TripSchedule")
    return tuple(out)


# --- Primitivas de envolvente (ProgressEnvelope de producción) -------------
def hold(ctx: Ctx, dwell_until: datetime | None = None) -> ProgressEnvelope:
    """Sin avance en todo el horizonte (retención abierta hasta nueva observación)."""
    return ProgressEnvelope(
        reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m, speed_mps=0.0,
        max_progress_m=ctx.anchor_progress_m,
        horizon_s=max(0.0, (ctx.horizon_end - ctx.anchor_at).total_seconds()), dwell_until=dwell_until)


def leg_index(ctx: Ctx, tau: float) -> int:
    """Índice de la última parada con progreso <= ancla + tau (−1 si ninguna)."""
    idx = -1
    for i, s in enumerate(ctx.stops):
        if s.progress_m <= ctx.anchor_progress_m + tau:
            idx = i
    return idx


def leg_speed(ctx: Ctx, i: int) -> float:
    """Velocidad media programada del tramo i→i+1 en segundos REALES (DST-correcto)."""
    a, b = ctx.stops[i], ctx.stops[i + 1]
    dur = (ctx.instant(b.arrival_s) - ctx.instant(a.departure_s)).total_seconds()
    dist = b.progress_m - a.progress_m
    if dur <= 0:
        return MAX_SPEED_MPS if dist > 0 else 0.0
    return min(dist / dur, MAX_SPEED_MPS)


def travel(ctx: Ctx, tau: float, moving_from: datetime | None = None) -> ProgressEnvelope:
    """Avance a velocidad de tramo, con tope en la siguiente parada (horizonte por tramo)."""
    i = leg_index(ctx, tau)
    i = max(i, 0)
    if i >= len(ctx.stops) - 1:
        return hold(ctx)
    cap = ctx.stops[i + 1].progress_m
    if cap <= ctx.anchor_progress_m:
        return hold(ctx)
    speed = leg_speed(ctx, i)
    start = moving_from or ctx.anchor_at
    moving_s = max(0.0, (ctx.horizon_end - start).total_seconds())
    if moving_s <= 0 or speed <= 0:
        return hold(ctx, dwell_until=moving_from if moving_from and moving_from > ctx.anchor_at else None)
    reach = min(cap, ctx.anchor_progress_m + speed * moving_s)
    dwell = moving_from if moving_from is not None and moving_from > ctx.anchor_at else None
    return ProgressEnvelope(
        reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m, speed_mps=speed,
        max_progress_m=reach, horizon_s=max(0.0, (ctx.horizon_end - ctx.anchor_at).total_seconds()),
        dwell_until=dwell)


def before_first_departure(ctx: Ctx) -> datetime | None:
    first_dep = ctx.instant(ctx.stops[0].departure_s)
    return first_dep if ctx.anchor_at < first_dep else None


def predeparture(ctx: Ctx, tau: float) -> ProgressEnvelope:
    first_dep = ctx.instant(ctx.stops[0].departure_s)
    if first_dep >= ctx.horizon_end:
        return hold(ctx)
    return travel(ctx, tau, moving_from=first_dep)


# --- Alternativas -----------------------------------------------------------
def alt_baseline(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
    """Producción beb9434 (`_envelope`, idéntica a la publicada: comprobación 0)."""
    env = _envelope(schedule=ctx.schedule, service_date=ctx.service_date, anchor_at=ctx.anchor_at,
                    anchor_progress_m=ctx.anchor_progress_m, horizon_end=ctx.horizon_end,
                    max_speed_mps=MAX_SPEED_MPS)
    return env, "beb9434"


def envelope_offset_clamped(ctx: Ctx, lo: float, hi: float, tolerance_m: float = 1.0) -> ProgressEnvelope:
    """Variante de `_envelope` con `temporal_offset_s` acotado a [lo, hi].

    Con lo=-inf, hi=+inf reproduce `_envelope` (comprobado en la validación).
    """
    sched = ctx.schedule
    anchor_s = service_seconds(ctx.anchor_at, ctx.service_date)
    offset = anchor_s - sched.seconds_at_progress(ctx.anchor_progress_m)
    offset = min(max(offset, lo), hi)
    horizon_s = max(0.0, (ctx.horizon_end - ctx.anchor_at).total_seconds())
    if horizon_s == 0.0:
        return hold(ctx)
    horizon_schedule_s = service_seconds(ctx.horizon_end, ctx.service_date) - offset
    span_m = max(0.0, sched.progress_at(horizon_schedule_s) - ctx.anchor_progress_m)
    dwell_end_s = sched.dwell_end_seconds(ctx.anchor_progress_m, tolerance_m=tolerance_m)
    dwell_until = None
    if dwell_end_s is not None:
        candidate = ctx.anchor_at + timedelta(seconds=dwell_end_s + offset - anchor_s)
        if ctx.anchor_at < candidate < ctx.horizon_end:
            dwell_until = candidate
    moving_from = dwell_until or ctx.anchor_at
    moving_s = max(0.0, (ctx.horizon_end - moving_from).total_seconds())
    speed = min(span_m / moving_s, MAX_SPEED_MPS) if moving_s > 0 else 0.0
    return ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m,
                            speed_mps=speed, max_progress_m=ctx.anchor_progress_m + speed * moving_s,
                            horizon_s=horizon_s, dwell_until=dwell_until)


def alt_d(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
    """D (descartada, contrafactual B de AUD-04): solo subir `tolerance_m` de 1,0 a TAU_STOP_M."""
    return envelope_offset_clamped(ctx, float("-inf"), float("inf"), tolerance_m=TAU_STOP_M), "tolerancia"


def alt_b1(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
    """B1: acotar `temporal_offset_s` a ±operator_delay_max_age_s (AUD-01 (A) literal)."""
    return envelope_offset_clamped(ctx, -OFFSET_SYM_S, OFFSET_SYM_S), "offset_clamp_sym"


def alt_b2(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
    """B2: B1 + ventana de pre-salida (AUD-01 (A)+(B)): retener hasta la primera salida."""
    if before_first_departure(ctx) is not None:
        first_dep = ctx.instant(ctx.stops[0].departure_s)
        if first_dep >= ctx.horizon_end:
            return hold(ctx), "pre_salida"
        env = envelope_offset_clamped(ctx, -OFFSET_SYM_S, OFFSET_SYM_S)
        moving_s = max(0.0, (ctx.horizon_end - first_dep).total_seconds())
        reach = env.max_progress_m - ctx.anchor_progress_m
        speed = min(reach / moving_s, MAX_SPEED_MPS) if moving_s > 0 else 0.0
        return ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m,
                                speed_mps=speed, max_progress_m=ctx.anchor_progress_m + speed * moving_s,
                                horizon_s=env.horizon_s, dwell_until=first_dep), "pre_salida"
    return envelope_offset_clamped(ctx, -OFFSET_SYM_S, OFFSET_SYM_S), "offset_clamp_sym"


def make_alt_c(tau: float, d_min: float) -> Callable[[Ctx], tuple[ProgressEnvelope, str]]:
    def alt_c(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
        """C: segmentos hold/travel solo con horario + zona de parada geométrica (sin operador)."""
        if ctx.canceled:
            return hold(ctx), "cancelada"
        if before_first_departure(ctx) is not None:
            return predeparture(ctx, tau), "pre_salida"
        i = leg_index(ctx, tau)
        at_stop = i >= 0 and abs(ctx.anchor_progress_m - ctx.stops[i].progress_m) <= tau
        if at_stop:
            if i == len(ctx.stops) - 1:
                return hold(ctx), "terminal"
            dwell = max(d_min, ctx.stops[i].departure_s - ctx.stops[i].arrival_s)
            until = ctx.anchor_at + timedelta(seconds=dwell)
            if until >= ctx.horizon_end:
                return hold(ctx), "zona_parada"
            return travel(ctx, tau, moving_from=until), "zona_parada"
        return travel(ctx, tau), "tramo"
    return alt_c


def make_alt_a(tau: float) -> Callable[[Ctx], tuple[ProgressEnvelope, str]]:
    fallback = make_alt_c(tau, D_MIN_S)

    def alt_a(ctx: Ctx) -> tuple[ProgressEnvelope, str]:
        """A: estado del operador + ventana del viaje + tope por tramo (semántica OBSERVADA)."""
        if ctx.canceled:
            return hold(ctx), "cancelada"
        by_id = {s.stop_id: s for s in ctx.stops}
        stop = by_id.get(ctx.current_stop_id or "")
        status = (ctx.status or "").upper()
        if status not in ("STOPPED_AT", "INCOMING_AT", "IN_TRANSIT_TO") or stop is None:
            env, why = fallback(ctx)
            return env, f"incoherente->C:{why}"
        gap = stop.progress_m - ctx.anchor_progress_m
        # STOPPED_AT coherente prevalece sobre la ventana: un tren que el operador
        # declara parado no sale a su hora programada si sigue parado.
        if status == "STOPPED_AT":
            if abs(gap) <= tau:
                return hold(ctx), "operador_STOPPED_AT"
            env, why = fallback(ctx)
            return env, f"incoherente->C:{why}"
        if before_first_departure(ctx) is not None:
            return predeparture(ctx, tau), "pre_salida"
        if status == "INCOMING_AT":
            if abs(gap) <= tau:
                return hold(ctx), "operador_INCOMING_AT_en_parada"
            if gap > tau:
                return travel(ctx, tau), "operador_INCOMING_AT_tramo"
            env = travel(ctx, tau)
            return env, "incoherente(parada_atras)->tramo"
        # IN_TRANSIT_TO: en este corte current_stop_id apunta a la parada ya dejada
        # (4/8 con >1 km por detrás) o a la parada en la que está (4/8 a <=5,4 m): se
        # usa solo como pista y el tope es la siguiente parada por delante.
        if ctx.stops[-1].progress_m - ctx.anchor_progress_m <= tau:
            return hold(ctx), "terminal"
        return travel(ctx, tau), "operador_IN_TRANSIT_TO_tramo"
    return alt_a


ALTERNATIVES: dict[str, Callable[[Ctx], tuple[ProgressEnvelope, str]]] = {
    "BASE(beb9434)": alt_baseline,
    f"D(tolerancia={TAU_STOP_M:g})": alt_d,
    "B1(offset±600)": alt_b1,
    "B2(offset+ventana)": alt_b2,
    f"C(τ={TAU_STOP_M:g},Dmin={D_MIN_S:g})": make_alt_c(TAU_STOP_M, D_MIN_S),
    f"A(τ={TAU_STOP_M:g})": make_alt_a(TAU_STOP_M),
}


# --- Cortes reales ----------------------------------------------------------
def load_cut(replay: Path, name: str) -> dict[str, VehiclePositionObservation]:
    raw = RawVehiclePositionsFeed.model_validate_json((replay / name / "vehicle_positions.json").read_bytes())
    return {o.source_vehicle_id: o for o in vehicle_positions_to_canonical(raw)}


@dataclass
class RealCase:
    vid: str
    ctx: Ctx
    cohort: str
    same_gps: bool
    at_origin: bool
    prod_envelope: ProgressEnvelope
    prod_valid_until: datetime
    engine: MovementEngine
    corridor: object
    latest: VehiclePositionObservation


def build_real(replay: Path) -> tuple[list[RealCase], list[tuple[Ctx, float, ProgressEnvelope, str]], dict]:
    topo = load_feed(replay / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="mp024")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=ROOT / "tests" / "fixtures")
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    prev_cut, last_cut = load_cut(replay, "1532"), load_cut(replay, "1533")
    cases: list[RealCase] = []
    pairs: list[tuple[Ctx, float, ProgressEnvelope, str]] = []
    facts = {"status_present": 0, "stop_in_trip": 0, "n": 0, "in_transit_stop_behind_gt_1km": 0,
             "in_transit_total": 0, "rendered_vs_map_matched_m": []}
    for vid, latest in sorted(last_cut.items()):
        trip_id = latest.source_trip_id
        route_id = trip_route.get(trip_id)
        times = topo.stop_times_for_trip(trip_id) if route_id else ()
        if not times:
            continue
        cov = corridors.coverage_for_stops(route_id, tuple(t.stop_id for t in times))
        if not cov.can_map_match or cov.corridor is None:
            continue
        engine = MovementEngine(topo, cov.corridor, thresholds=TH)
        schedule = build_trip_schedule(topo, cov.corridor, trip_id)
        stops = stops_for_trip(topo, cov.corridor, schedule, trip_id)
        previous = prev_cut.get(vid)
        if previous is not None and previous.source_trip_id != trip_id:
            previous = None
        sd = latest.observed_at.astimezone(MADRID).date()
        now = latest.observed_at + timedelta(seconds=CALC_DELAY_S)
        mv = engine.position(trip_id=trip_id, service_date=sd, calculated_at=now, latest=latest,
                             previous=previous)
        rd = render_from_movement(mv, schedule=schedule, corridor=cov.corridor, service_date=sd,
                                  display_at=now, pattern_id=cov.identity.pattern_id,
                                  geometry_version=cov.geometry_version, thresholds=TH)
        if rd.progress_envelope is None or rd.valid_until is None or mv.anchor_progress_m is None:
            continue
        anchor_s = service_seconds(latest.observed_at, sd)
        cohort = ("pre_salida" if anchor_s < schedule.points[0].seconds
                  else "post_llegada" if anchor_s > schedule.points[-1].seconds else "en_ventana")
        ctx = Ctx(trip_id=trip_id, schedule=schedule, stops=stops, service_date=sd,
                  anchor_at=latest.observed_at, anchor_progress_m=mv.anchor_progress_m,
                  horizon_end=rd.valid_until, status=latest.current_status,
                  current_stop_id=latest.current_stop_id, label=trip_id)
        same_gps = (previous is not None and previous.latitude == latest.latitude
                    and previous.longitude == latest.longitude)
        cases.append(RealCase(vid, ctx, cohort, same_gps, latest.current_stop_id == stops[0].stop_id,
                              rd.progress_envelope, rd.valid_until, engine, cov.corridor, latest))
        facts["n"] += 1
        facts["status_present"] += latest.current_status is not None
        sids = {s.stop_id: s for s in stops}
        facts["stop_in_trip"] += latest.current_stop_id in sids
        if (latest.current_status or "").upper() == "IN_TRANSIT_TO":
            facts["in_transit_total"] += 1
            st = sids.get(latest.current_stop_id or "")
            if st is not None and ctx.anchor_progress_m - st.progress_m > 1000:
                facts["in_transit_stop_behind_gt_1km"] += 1
                facts.setdefault("in_transit_behind_detail(trip,stop,m_por_detras)", []).append(
                    (trip_id, st.stop_id, round(ctx.anchor_progress_m - st.progress_m, 1)))
        if (latest.current_status or "").upper() == "STOPPED_AT" and latest.current_stop_id in sids:
            gap = round(sids[latest.current_stop_id].progress_m - ctx.anchor_progress_m, 1)
            key = ("stopped_gap_origin_m" if latest.current_stop_id == stops[0].stop_id
                   else "stopped_gap_intermediate_m")
            facts.setdefault(key, []).append(gap)
        m = corridors.match_position(cov.identity.pattern_id, raw_lat=latest.latitude, raw_lon=latest.longitude)
        if m.projection is not None:
            lat, lon = _coordinate(cov.corridor, schedule, mv.anchor_progress_m)
            facts["rendered_vs_map_matched_m"].append(haversine_m(lat, lon, m.projection.lat, m.projection.lon))
        # Par 1532 -> 1533: el ancla es la observación 1532; la verdad, la 1533.
        if previous is not None:
            sd0 = previous.observed_at.astimezone(MADRID).date()
            now0 = previous.observed_at + timedelta(seconds=CALC_DELAY_S)
            mv0 = engine.position(trip_id=trip_id, service_date=sd0, calculated_at=now0, latest=previous)
            rd0 = render_from_movement(mv0, schedule=schedule, corridor=cov.corridor, service_date=sd0,
                                       display_at=now0, pattern_id=cov.identity.pattern_id,
                                       geometry_version=cov.geometry_version, thresholds=TH)
            if rd0.progress_envelope is not None and mv0.anchor_progress_m is not None and rd0.valid_until:
                ctx0 = Ctx(trip_id=trip_id, schedule=schedule, stops=stops, service_date=sd0,
                           anchor_at=previous.observed_at, anchor_progress_m=mv0.anchor_progress_m,
                           horizon_end=rd0.valid_until, status=previous.current_status,
                           current_stop_id=previous.current_stop_id, label=trip_id,
                           extra={"t1": latest.observed_at})
                pairs.append((ctx0, mv.anchor_progress_m, rd0.progress_envelope, previous.current_status or ""))
    return cases, pairs, facts


def advance(env: ProgressEnvelope, at: datetime) -> float:
    return env.progress_at(at) - env.progress_m_at_reference


def crossed_stops(ctx: Ctx, env: ProgressEnvelope, margin_m: float = 1.0) -> int:
    """Paradas superadas ESTRICTAMENTE antes de valid_until (definición de aud09 v2 con 1 m).

    Con `margin_m = TAU_STOP_M` se excluye la parada en cuya zona ya está el tren
    (la que está dejando), que no es un cruce sino ruido de proyección."""
    p0, p1 = env.progress_m_at_reference, env.progress_at(ctx.horizon_end)
    return sum(1 for s in ctx.stops if p0 + margin_m < s.progress_m < p1)


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    k = (len(ordered) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def real_metrics(name: str, alt, cases: list[RealCase], pairs) -> dict:
    stopped = [c for c in cases if (c.ctx.status or "").upper() == "STOPPED_AT"]
    res: dict = {"alternative": name}
    envs = {c.vid: alt(c.ctx)[0] for c in cases}
    moving = lambda c: advance(envs[c.vid], c.ctx.horizon_end) > ADVANCE_EPS_M
    res["M1_stopped_same_gps_with_advance"] = (sum(moving(c) for c in stopped if c.same_gps),
                                               sum(1 for c in stopped if c.same_gps))
    pre = [c for c in cases if c.cohort == "pre_salida"]
    res["M2_predeparture_with_advance"] = (sum(moving(c) for c in pre), len(pre))
    late = [c for c in stopped if c.at_origin and c.cohort == "en_ventana"]
    res["M3_delayed_origin_with_advance"] = (sum(moving(c) for c in late), len(late))
    mid = [c for c in stopped if not c.at_origin]
    res["M4_intermediate_stopped_with_advance"] = (sum(moving(c) for c in mid), len(mid))
    res["M1b_stopped_any_with_advance"] = (sum(moving(c) for c in stopped), len(stopped))
    res["M5_cross_stop_within_horizon"] = (sum(crossed_stops(c.ctx, envs[c.vid]) > 0 for c in cases), len(cases))
    res["M5_detail(trip,stop,m_por_delante)"] = [
        (c.ctx.trip_id, st.stop_id, round(st.progress_m - c.ctx.anchor_progress_m, 1))
        for c in cases for st in c.ctx.stops
        if c.ctx.anchor_progress_m + 1.0 < st.progress_m < envs[c.vid].progress_at(c.ctx.horizon_end)
    ] if name.startswith("A(") else "solo se detalla para A"
    res["M5b_cross_stop_beyond_tau"] = (sum(crossed_stops(c.ctx, envs[c.vid], TAU_STOP_M) > 0 for c in cases),
                                        len(cases))
    c19656 = next(c for c in cases if c.ctx.trip_id == "1023V19656C5")
    e = envs[c19656.vid]
    res["M6_19656_advance_30s_60s"] = (round(advance(e, c19656.ctx.anchor_at + timedelta(seconds=30)), 1),
                                       round(advance(e, c19656.ctx.anchor_at + timedelta(seconds=60)), 1))
    regress = [advance(envs[c.vid], c.ctx.horizon_end) for c in cases]
    res["M8_regress_at_expiry_if_frozen_at_anchor_p50_max"] = (round(statistics.median(regress), 1),
                                                                 round(max(regress), 1))
    errors, lost, over, h2b_lost, h2b_n = [], 0, 0, 0, 0
    lost_ids: list[tuple[str, str, float]] = []
    for ctx0, truth, prod_env, status0 in pairs:
        env0 = prod_env if name.startswith("BASE") else alt(ctx0)[0]
        t1 = ctx0.extra["t1"]
        pred = advance(env0, t1)
        obs = truth - ctx0.anchor_progress_m
        errors.append(abs(pred - obs))
        if obs >= 100 and pred <= ADVANCE_EPS_M:
            lost += 1
            lost_ids.append((ctx0.trip_id, status0, round(obs, 1)))
        if pred - obs > 100:
            over += 1
        if status0.upper() in ("IN_TRANSIT_TO", "INCOMING_AT") and obs >= 100:
            h2b_n += 1
            h2b_lost += pred <= ADVANCE_EPS_M
    res["M7_snap_77s_p50_p90_max"] = (round(statistics.median(errors), 1), round(pct(errors, 0.9), 1),
                                      round(max(errors), 1))
    res["M7_n_pairs"] = len(pairs)
    res["M7_lost_legit_advance_any_status"] = lost
    res["M7_lost_detail(trip,status_1532,avance_observado_m)"] = lost_ids
    res["M7_over_advance_gt100m"] = over
    res["M7_H2b_transit_or_incoming_lost"] = (h2b_lost, h2b_n)
    reasons: dict[str, int] = {}
    for c in cases:
        why = alt(c.ctx)[1]
        reasons[why] = reasons.get(why, 0) + 1
    res["reasons"] = dict(sorted(reasons.items()))
    return res


def equivalence_check(cases: list[RealCase]) -> tuple[int, int]:
    ok = 0
    for c in cases:
        mine = _envelope(schedule=c.ctx.schedule, service_date=c.ctx.service_date, anchor_at=c.ctx.anchor_at,
                         anchor_progress_m=c.prod_envelope.progress_m_at_reference,
                         horizon_end=c.prod_valid_until, max_speed_mps=MAX_SPEED_MPS)
        clamp = envelope_offset_clamped(c.ctx, float("-inf"), float("inf"))
        same = (abs(mine.speed_mps - c.prod_envelope.speed_mps) < 1e-9
                and mine.dwell_until == c.prod_envelope.dwell_until
                and abs(clamp.speed_mps - c.prod_envelope.speed_mps) < 1e-9
                and clamp.dwell_until == c.prod_envelope.dwell_until)
        ok += same
    return ok, len(cases)


def baseline_expiry_and_two_coords(cases: list[RealCase]) -> dict:
    """Línea base de FR-05 (retroceso 179→181 s) y FR-27 (|position − rendered| a 61–179 s)."""
    regress, gaps = [], []
    for c in cases:
        if c.cohort != "en_ventana":
            continue
        sched, sd = c.ctx.schedule, c.ctx.service_date
        out = {}
        for age in (179, 181):
            t = c.latest.observed_at + timedelta(seconds=age)
            mv = c.engine.position(trip_id=c.ctx.trip_id, service_date=sd, calculated_at=t, latest=c.latest)
            rd = render_from_movement(mv, schedule=sched, corridor=c.corridor, service_date=sd, display_at=t,
                                      pattern_id=None, geometry_version=None, thresholds=TH)
            out[age] = rd.progress_m
        regress.append(out[179] - out[181])
        for age in range(61, 180, 2):
            t = c.latest.observed_at + timedelta(seconds=age)
            mv = c.engine.position(trip_id=c.ctx.trip_id, service_date=sd, calculated_at=t, latest=c.latest)
            if mv.position_mode is not PositionMode.ESTIMATED:
                continue
            rd = render_from_movement(mv, schedule=sched, corridor=c.corridor, service_date=sd, display_at=t,
                                      pattern_id=None, geometry_version=None, thresholds=TH)
            gaps.append(abs(rd.progress_m - mv.progress_m))
    return {"FR05_regress_179_181_n_gt1m": (sum(r > 1 for r in regress), len(regress)),
            "FR05_regress_p50_max": (round(statistics.median(regress), 1), round(max(regress), 1)),
            "FR27_position_vs_rendered_max_m": round(max(gaps), 1) if gaps else None}


# --- Casos sintéticos -------------------------------------------------------
def synthetic_cases(real: list[RealCase]) -> list[tuple[str, Ctx, str, Callable[[ProgressEnvelope, Ctx], tuple[bool, str]]]]:
    """Casos sobre el horario REAL de 1023V19656C5 (paradas con espera de 60 s) y dos
    horarios sintéticos de cambio de hora. Cada caso trae su criterio de aceptación."""
    base = next(c for c in real if c.ctx.trip_id == "1023V19656C5").ctx
    stops = base.stops
    first = stops[0]
    dwell_stop = next(s for s in stops[1:-1] if s.departure_s > s.arrival_s)
    plain_i = next(i for i, s in enumerate(stops[1:-1], 1) if s.departure_s == s.arrival_s)
    plain = stops[plain_i]
    sd = base.service_date
    inst = lambda s: service_day_instant(sd, s)

    def mk(label: str, at: datetime, progress: float, status: str | None, stop_id: str | None, **kw) -> Ctx:
        return Ctx(trip_id=base.trip_id, schedule=base.schedule, stops=stops, service_date=sd, anchor_at=at,
                   anchor_progress_m=progress, horizon_end=at + timedelta(seconds=TH.stale_after_s),
                   status=status, current_stop_id=stop_id, label=label, **kw)

    def no_adv_until(t_rel: float):
        def check(env: ProgressEnvelope, ctx: Ctx) -> tuple[bool, str]:
            a = advance(env, ctx.anchor_at + timedelta(seconds=t_rel))
            return a <= ADVANCE_EPS_M, f"avance a {t_rel:g} s = {a:.1f} m"
        return check

    def no_adv_before_first_dep(env: ProgressEnvelope, ctx: Ctx) -> tuple[bool, str]:
        t = inst(first.departure_s) - timedelta(seconds=1)
        a = advance(env, t)
        return a <= ADVANCE_EPS_M, f"avance 1 s antes de la salida = {a:.1f} m"

    def moves(env: ProgressEnvelope, ctx: Ctx) -> tuple[bool, str]:
        a = advance(env, ctx.horizon_end)
        return a > ADVANCE_EPS_M, f"avance en el horizonte = {a:.1f} m"

    out = []
    out.append(("S1 pre-salida (−300 s, STOPPED_AT origen)",
                mk("S1", inst(first.departure_s - 300), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "0 m en todo el horizonte", no_adv_until(TH.stale_after_s)))
    out.append(("S2 pre-salida (−60 s): sin avance antes de la salida",
                mk("S2", inst(first.departure_s - 60), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "0 m hasta la hora de salida", no_adv_before_first_dep))
    out.append(("S3 salida retrasada (+120 s, STOPPED_AT origen)",
                mk("S3", inst(first.departure_s + 120), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "0 m mientras el operador diga STOPPED_AT", no_adv_until(TH.stale_after_s)))
    out.append(("S4 parada intermedia con espera 60 s (+5,4 m, STOPPED_AT)",
                mk("S4", inst(dwell_stop.arrival_s + 20), dwell_stop.progress_m + 5.38, "STOPPED_AT",
                   dwell_stop.stop_id),
                "0 m a los 30 s", no_adv_until(30)))
    out.append(("S5 parada intermedia SIN espera programada (STOPPED_AT)",
                mk("S5", inst(plain.arrival_s + 30), plain.progress_m - 3.0, "STOPPED_AT", plain.stop_id),
                "0 m en todo el horizonte", no_adv_until(TH.stale_after_s)))
    mid_p = (stops[plain_i].progress_m + stops[plain_i + 1].progress_m) / 2
    mid_t = (stops[plain_i].departure_s + stops[plain_i + 1].arrival_s) / 2
    out.append(("S6 cancelada (CANCELED, IN_TRANSIT_TO a mitad de tramo)",
                mk("S6", inst(mid_t), mid_p, "IN_TRANSIT_TO", stops[plain_i].stop_id, canceled=True),
                "0 m (R-CANCEL)", no_adv_until(TH.stale_after_s)))
    out.append(("S6b en marcha a mitad de tramo (control: no se debe retener)",
                mk("S6b", inst(mid_t), mid_p, "IN_TRANSIT_TO", stops[plain_i].stop_id),
                "> 1 m en el horizonte", moves))
    out.append(("S7 incoherencia GTFS: STOPPED_AT con stop_id ajeno al viaje, a mitad de tramo",
                mk("S7", inst(mid_t), mid_p, "STOPPED_AT", "99999"),
                "no aplica la retención del operador; degrada declarado (motivo 'incoherente')",
                "INCOHERENT"))
    behind_m = mid_p - stops[plain_i].progress_m
    out.append((f"S10 INCOMING_AT con current_stop_id {behind_m:.0f} m POR DETRÁS del ancla",
                mk("S10", inst(mid_t), mid_p, "INCOMING_AT", stops[plain_i].stop_id),
                "no retiene (avance > 1 m) y declara la incoherencia", "INCOHERENT_MOVES"))
    # Cambios de hora 2027 con horarios sintéticos de un tramo de 20 000 m.
    for label, d, dep, arr, anchor_utc, expect_rate in (
        ("S8 DST adelanto 2027-03-28 (01:50→02:10)", date(2027, 3, 28), "01:50:00", "02:10:00",
         datetime(2027, 3, 28, 0, 58, 0, tzinfo=timezone.utc), None),
        ("S9 DST atraso 2027-10-31 (01:30→03:30)", date(2027, 10, 31), "01:30:00", "03:30:00",
         datetime(2027, 10, 31, 0, 59, 0, tzinfo=timezone.utc), None),
    ):
        dep_s, arr_s = parse_gtfs_time(dep), parse_gtfs_time(arr)
        sch = TripSchedule(points=(SchedulePoint(dep_s, 0.0), SchedulePoint(arr_s, 20000.0)),
                           corridor_length_m=20000.0, forward=True)
        st = (StopInfo("X0", 0.0, dep_s, dep_s), StopInfo("X1", 20000.0, arr_s, arr_s))
        real_rate = 20000.0 / (service_day_instant(d, arr_s) - service_day_instant(d, dep_s)).total_seconds()
        anchor_p = real_rate * (anchor_utc - service_day_instant(d, dep_s)).total_seconds()
        ctx = Ctx(trip_id="SYN", schedule=sch, stops=st, service_date=d, anchor_at=anchor_utc,
                  anchor_progress_m=anchor_p, horizon_end=anchor_utc + timedelta(seconds=TH.stale_after_s),
                  status="IN_TRANSIT_TO", current_stop_id="X0", label=label)
        expected = real_rate * TH.stale_after_s

        def check(env: ProgressEnvelope, c: Ctx, expected=expected) -> tuple[bool, str]:
            a = advance(env, c.horizon_end)
            return abs(a - expected) <= ADVANCE_EPS_M, f"avance {a:.1f} m (esperado {expected:.1f} m en tiempo real)"
        out.append((label, ctx, f"avance = {expected:.1f} ± 1 m", check))
    return out


def stale_rule_demo(cases: list[RealCase], alt) -> tuple[float, float]:
    """FR-05 con la regla F1 (congelar en el final autorizado): retroceso 179→181 s."""
    worst: list[float] = []
    for c in cases:
        env = alt(c.ctx)[0]
        p179 = env.progress_at(c.ctx.anchor_at + timedelta(seconds=179))
        frozen = env.progress_at(c.ctx.horizon_end)
        worst.append(max(0.0, p179 - frozen))
    return (round(statistics.median(worst), 3), round(max(worst), 3))


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    replay = args.replay.resolve()

    out: dict = {}
    out["validation"] = validate_harness(replay)
    print("== 0) validación del arnés (ORCHESTRATION_POLICY §3.4) ==")
    print(f"   HEAD={out['validation']['head']}  producto idéntico a {BASELINE_COMMIT}: "
          f"{out['validation']['product_equals_baseline']}")
    for item in out["validation"]["constants"]:
        print(f"   {item['name']:34s} {item['where']}  valor={item['value']}")
    for name, digest in sorted(out["validation"]["inputs"].items()):
        print(f"   sha256 {name:28s} {digest}")

    cases, pairs, facts = build_real(replay)
    eq_ok, eq_n = equivalence_check(cases)
    out["equivalence"] = (eq_ok, eq_n)
    print(f"   equivalencia: envolvente publicada == _envelope(valid_until) == variante B(±∞): {eq_ok}/{eq_n}")
    if eq_ok != eq_n:
        raise SystemExit("ARNÉS INVÁLIDO: la línea base no reproduce producción")

    rvm = facts.pop("rendered_vs_map_matched_m")
    for key in ("stopped_gap_origin_m", "stopped_gap_intermediate_m"):
        gaps = facts.pop(key, [])
        facts[key.replace("_m", "_min_max_m")] = (min(gaps), max(gaps), len(gaps)) if gaps else None
    facts["rendered_anchor_vs_map_matched_p50_max_m"] = (round(statistics.median(rvm), 2), round(max(rvm), 2))
    out["facts"] = facts
    print("\n== 1) hechos del corte 1533 (circulaciones con cadena raw→matched→rendered) ==")
    for k, v in facts.items():
        print(f"   {k}: {v}")
    base = baseline_expiry_and_two_coords(cases)
    out["baseline_fr05_fr27"] = base
    for k, v in base.items():
        print(f"   [línea base] {k}: {v}")

    print("\n== 2) cortes reales: alternativas ==")
    out["real"] = []
    for name, alt in ALTERNATIVES.items():
        m = real_metrics(name, alt, cases, pairs)
        m["FR05_regress_with_F1_p50_max"] = (
            "N/A: beb9434 congela en el ancla (ver §1)" if name.startswith("BASE")
            else stale_rule_demo(cases, alt))
        out["real"].append(m)
        print(f"-- {name}")
        for k, v in m.items():
            if k != "alternative":
                print(f"   {k}: {v}")

    print("\n== 3) sensibilidad (cortes reales) ==")
    out["sensitivity"] = []
    for tau in TAU_SWEEP:
        m = real_metrics(f"A(τ={tau:g})", make_alt_a(tau), cases, pairs)
        row = {k: m[k] for k in ("alternative", "M1_stopped_same_gps_with_advance", "M1b_stopped_any_with_advance",
                                 "M5_cross_stop_within_horizon", "M6_19656_advance_30s_60s",
                                 "M7_snap_77s_p50_p90_max", "M7_H2b_transit_or_incoming_lost")}
        row["incoherent"] = sum(v for k, v in m["reasons"].items() if k.startswith("incoherente"))
        out["sensitivity"].append(row)
        print(f"   {row}")
    for d_min in D_MIN_SWEEP:
        m = real_metrics(f"C(τ={TAU_STOP_M:g},Dmin={d_min:g})", make_alt_c(TAU_STOP_M, d_min), cases, pairs)
        row = {k: m[k] for k in ("alternative", "M1_stopped_same_gps_with_advance", "M3_delayed_origin_with_advance",
                                 "M4_intermediate_stopped_with_advance", "M7_snap_77s_p50_p90_max",
                                 "M7_H2b_transit_or_incoming_lost")}
        out["sensitivity"].append(row)
        print(f"   {row}")

    print("\n== 4) casos sintéticos (criterio de aceptación por caso) ==")
    out["synthetic"] = []
    for label, ctx, criterion, check in synthetic_cases(cases):
        print(f"-- {label}  [criterio: {criterion}]")
        row = {"case": label, "criterion": criterion, "results": {}}
        for name, alt in ALTERNATIVES.items():
            env, why = alt(ctx)
            if check in ("INCOHERENT", "INCOHERENT_MOVES"):
                a = advance(env, ctx.horizon_end)
                declared = "incoherente" in why
                ok = declared and (check == "INCOHERENT" or a > ADVANCE_EPS_M)
                if not name.startswith("A("):
                    ok = None  # la alternativa no lee el estado del operador: no aplica
                detail = f"avance en el horizonte = {a:.1f} m; motivo declarado = {declared}"
            else:
                ok, detail = check(env, ctx)
            row["results"][name] = {"pass": ok, "detail": detail, "reason": why}
            tag = "N/A " if ok is None else ("PASS" if ok else "FAIL")
            print(f"   {tag}  {name:24s} {detail}  ({why})")
        out["synthetic"].append(row)

    print("\n== 5) criterios de aceptación de MP-025a (prototipos; ROJO esperado en BASE) ==")
    syn = {r["case"].split(" ")[0]: r["results"] for r in out["synthetic"]}
    out["acceptance"] = {}
    for m in out["real"]:
        name = m["alternative"]
        ac = {
            "AC-1 0/25 STOPPED_AT GPS idéntico con avance": m["M1_stopped_same_gps_with_advance"][0] == 0,
            "AC-2 0/17 pre-salida y 0/4 salida retrasada con avance":
                m["M2_predeparture_with_advance"][0] == 0 and m["M3_delayed_origin_with_advance"][0] == 0,
            "AC-3 0/7 STOPPED_AT intermedias con avance": m["M4_intermediate_stopped_with_advance"][0] == 0,
            "AC-4 0 IN_TRANSIT_TO/INCOMING_AT que avanzaron pierden avance":
                m["M7_H2b_transit_or_incoming_lost"][0] == 0,
            "AC-5 19656: 0 m a los 30 s (≤1 m)": m["M6_19656_advance_30s_60s"][0] <= ADVANCE_EPS_M,
            "AC-6 retroceso al expirar ≤1 m (con la regla transversal R-STALE F1)":
                (not name.startswith("BASE")) and m["FR05_regress_with_F1_p50_max"][1] <= 1.0,
            "AC-7 DST 2027-03-28 sin avance fabricado": bool(syn["S8"][name]["pass"]),
            "AC-8 DST 2027-10-31 sin congelación": bool(syn["S9"][name]["pass"]),
            "AC-9 cancelada sin avance": bool(syn["S6"][name]["pass"]),
            "AC-11 0/44 atraviesan una parada (> τ por delante) antes de valid_until":
                m["M5b_cross_stop_beyond_tau"][0] == 0,
            "AC-12 S3 salida retrasada / S5 parada sin espera retenidas":
                bool(syn["S3"][name]["pass"]) and bool(syn["S5"][name]["pass"]),
        }
        out["acceptance"][name] = ac
        passed = sum(ac.values())
        print(f"-- {name}: {passed}/{len(ac)} PASS")
        for k, v in ac.items():
            print(f"   {'PASS' if v else 'FAIL'}  {k}")
    print("   AC-10 (FR-27, una coordenada por instante) es por construcción de la regla R-ONECOORD; "
          "solo se mide la línea base (ver §1).")

    if args.json:
        args.json.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n")
        print(f"\nJSON escrito en {args.json}")


if __name__ == "__main__":
    main()
