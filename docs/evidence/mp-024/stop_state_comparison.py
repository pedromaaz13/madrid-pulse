"""MP-024 (H4-00), v2: evidencia offline del modelo de estado de parada.

Ronda 2, tras CHANGES_REQUESTED de Codex `gpt-6.2-astra` · high sobre `f0f8224`.

Compara la envolvente de PRODUCCIÓN (`beb9434`) con las alternativas de diseño
(A: estado del operador + ventana + tope por tramo, con orden TOTAL de
precedencia; B1/B2: acotación de `temporal_offset_s`; C: segmentos solo por
horario, que es también la degradación R8 de A; D: subir la tolerancia) y
ejecuta las pruebas de contrato de la enmienda:

1. cortes reales congelados `1532`/`1533` (SHA-256 contra `manifest.json`);
2. pruebas sintéticas de reglas (precedencia, casos límite, DST en tramo Y en
   espera, cancelación);
3. el CAMINO STALE real (F1/F2) con actualizaciones de `trip_update`
   admisibles e inadmisibles, reinicio y cambio de versión;
4. las ramas de presentación con el motor real (ancla `previous` cuando el
   motor rechaza `latest`, `schedule_only`, `CANCELED` sin ancla, solo `raw`,
   interpolación con `display_lag`);
5. las fases de `hold_reason` (antes / durante / después) y un fixture para
   AC-15 que `ts_equivalence.cjs` evalúa con el `progressAt` de PRODUCCIÓN.

Validación del arnés (ORCHESTRATION_POLICY §3.4): constantes con
`archivo:línea` y valor en ejecución (incluidos los defaults de `ApiConfig`
con una DSN ficticia y SIN conectar), conjunto esperado de 7 entradas con
SHA-256, igualdad COMPLETA de campos de la envolvente publicada frente a
`_envelope` y a la variante B(±∞), denominadores comprobados con `assert`,
HEAD y producto idéntico a `beb9434`.

Las alternativas son PROTOTIPOS de diseño, no MP-025a. `TAU_STOP_M` y
`MIN_DWELL_S` forman el PERFIL DE ENSAYO P-024 (τ = 50 m, 30 s), fijo hasta que
MP-028 calibre; no son valores de diseño.

Sin red, sin base de datos. Escribe solo `--json` y `--fixture-out`.

Uso:
    python3 docs/evidence/mp-024/stop_state_comparison.py --replay DIR \
        [--json results.json] [--fixture-out fixture.json]
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from itertools import pairwise
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
    AnchorSample,
    ProgressEnvelope,
    RenderingMethod,
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
VMAX = TH.max_estimated_speed_kmh / 3.6
CALC_DELAY_S = 10.0  # reloj de la evidencia MP-019/AUD-09: calculated_at = ancla + 10 s
LOST_OBS_M = 100.0  # «avanzó» entre cortes = al menos 100 m observados

# Perfil de ensayo P-024 (no de diseño): fijo hasta la calibración de MP-028.
TAU_STOP_M = 50.0
MIN_DWELL_S = 30.0
TAU_SWEEP = (5.0, 5.3, 5.5, 10.0, 20.8, 30.0, 37.9, 38.1, 40.0, 50.0, 75.0, 100.0, 150.0)
D_MIN_SWEEP = (0.0, 30.0, 60.0, 180.0)
OFFSET_SYM_S = 600.0
CANCEL_MAX_AGE_S = 600.0  # P-024 provisional (§6): edad máxima de una cancelación aplicable

EXPECTED_INPUTS = {
    "1532/alerts.json", "1532/trip_updates.json", "1532/vehicle_positions.json",
    "1533/alerts.json", "1533/trip_updates.json", "1533/vehicle_positions.json", "fomento_transit.zip",
}
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


# =========================================================================
# 0. Validación del arnés
# =========================================================================
def locate(path: str, pattern: str) -> int:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]
    if len(hits) != 1:
        raise SystemExit(f"ARNÉS INVÁLIDO: {path} /{pattern}/ aparece {len(hits)} veces")
    return hits[0]


def api_defaults() -> dict[str, float]:
    """Defaults efectivos de `ApiConfig.from_env` SIN overrides y SIN conectar.

    `from_env` trae por defecto la DSN de 5433; se sustituye por una DSN
    ficticia para que ni siquiera la cadena apunte a la base compartida. No se
    abre ninguna conexión: solo se construye el objeto de configuración.
    """
    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("MADRID_PULSE_")}
    os.environ["MADRID_PULSE_DATABASE_DSN"] = "postgresql://mp024-no-connect.invalid:1/none"
    try:
        from apps.api.config import ApiConfig
        cfg = ApiConfig.from_env()
    finally:
        os.environ.pop("MADRID_PULSE_DATABASE_DSN", None)
        os.environ.update(saved)
    return {"operator_delay_max_age_s": cfg.operator_delay_max_age_s, "display_lag_s": cfg.display_lag_s}


def validate_harness(replay: Path) -> dict:
    report: dict = {"constants": [], "inputs": {}, "manifest_sha256": None}
    runtime = {
        "observed_max_age_s": TH.observed_max_age_s,
        "stale_after_s": TH.stale_after_s,
        "max_estimated_speed_kmh": TH.max_estimated_speed_kmh,
        "max_estimated_acceleration_mps2": TH.max_estimated_acceleration_mps2,
        "tolerance_m": inspect.signature(TripSchedule.dwell_end_seconds).parameters["tolerance_m"].default,
        **api_defaults(),
    }
    for path, pattern, name, expected in PRODUCTION_CONSTANTS:
        line = locate(path, pattern)
        checked = "texto"
        if expected is not None and name in runtime:
            if runtime[name] != expected:
                raise SystemExit(f"ARNÉS INVÁLIDO: {name} = {runtime[name]} en ejecución, se esperaba {expected}")
            checked = "texto+ejecución"
        report["constants"].append({"name": name, "where": f"{path}:{line}", "value": expected, "checked": checked})
    # Identidad del manifiesto (su propio hash) separada de su validación interna.
    report["manifest_sha256"] = hashlib.sha256((replay / "manifest.json").read_bytes()).hexdigest()
    manifest = json.loads((replay / "manifest.json").read_text())
    if set(manifest["sha256"]) != EXPECTED_INPUTS:
        raise SystemExit(f"ARNÉS INVÁLIDO: entradas del manifiesto {sorted(manifest['sha256'])}")
    for name, digest in sorted(manifest["sha256"].items()):
        actual = hashlib.sha256((replay / name).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"ARNÉS INVÁLIDO: SHA-256 de {name} = {actual} != manifiesto {digest}")
        report["inputs"][name] = actual
    git = ["git", "-C", str(ROOT)]
    report["head"] = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True,
                                    check=True).stdout.strip()
    diff = subprocess.run(git + ["diff", "--quiet", BASELINE_COMMIT, "--", "packages", "apps", "services", "infra"],
                          check=False)
    report["product_equals_baseline"] = diff.returncode == 0
    if not report["product_equals_baseline"]:
        raise SystemExit(f"ARNÉS INVÁLIDO: el código de producto difiere de {BASELINE_COMMIT}")
    return report


# =========================================================================
# 1. Estructuras comunes
# =========================================================================
@dataclass(frozen=True)
class StopInfo:
    stop_id: str
    progress_m: float
    arrival_s: float
    departure_s: float
    index: int


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
    zone_entry_at: datetime | None = None
    anchor_run: int = 100  # ingestion_run_id del ancla (modelo de disponibilidad por run, §4.4)
    label: str = ""
    extra: dict = field(default_factory=dict)

    def instant(self, seconds: float) -> datetime:
        return service_day_instant(self.service_date, seconds)


@dataclass(frozen=True)
class Plan:
    """Envolvente de PRODUCCIÓN (`ProgressEnvelope`) + campos aditivos de la enmienda."""

    env: ProgressEnvelope
    rule: str
    hold_reason: str | None = None
    cap_stop_id: str | None = None
    cap_kind: str | None = None  # stop | horizon | trip_canceled | None (sin avance)
    cap_reached_at: datetime | None = None
    coherent: bool | None = None  # True coherente · False contradictorio · None ausente
    dwell_basis: str | None = None


def ceil_ms(dt: datetime) -> datetime:
    rem = dt.microsecond % 1000
    return dt if rem == 0 else dt + timedelta(microseconds=1000 - rem)


def advance(env: ProgressEnvelope, at: datetime) -> float:
    return env.progress_at(at) - env.progress_m_at_reference


def horizon_s(ctx: Ctx) -> float:
    return max(0.0, (ctx.horizon_end - ctx.anchor_at).total_seconds())


def stops_for_trip(topo: Topology, corridor, schedule: TripSchedule, trip_id: str) -> tuple[StopInfo, ...]:
    """Paradas proyectadas con las MISMAS primitivas que `build_trip_schedule`."""
    by_id = {stop.stop_id: stop for stop in topo.stops}
    out = []
    for index, item in enumerate(topo.stop_times_for_trip(trip_id)):
        stop = by_id[item.stop_id]
        _, arc = corridor.project_station(stop.latitude, stop.longitude)
        out.append(StopInfo(item.stop_id, schedule.directed_progress(arc),
                            parse_gtfs_time(item.arrival_time or item.departure_time),
                            parse_gtfs_time(item.departure_time or item.arrival_time), index))
    if sorted({round(p.progress_m, 6) for p in schedule.points}) != sorted({round(s.progress_m, 6) for s in out}):
        raise SystemExit(f"ARNÉS INVÁLIDO: paradas de {trip_id} no coinciden con TripSchedule")
    return tuple(out)


# =========================================================================
# 2. Prototipo A (orden TOTAL de precedencia, §4.2 de la enmienda) y C (= R8)
# =========================================================================
KNOWN_STATUS = ("STOPPED_AT", "INCOMING_AT", "IN_TRANSIT_TO")


def hold(ctx: Ctx, reason: str, rule: str, coherent: bool | None, dwell_basis: str | None = None) -> Plan:
    env = ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m,
                           speed_mps=0.0, max_progress_m=ctx.anchor_progress_m, horizon_s=horizon_s(ctx),
                           dwell_until=None)
    return Plan(env, rule, hold_reason=reason, coherent=coherent, dwell_basis=dwell_basis)


def leg(ctx: Ctx, tau: float, rule: str, coherent: bool | None, moving_from: datetime | None = None,
        hold_reason: str | None = None, dwell_basis: str | None = None) -> Plan:
    """R5: avance a velocidad de tramo con tope en la primera parada > ancla + τ.

    - `prev` = última ocurrencia con progreso <= ancla + τ; `cap` = primera ocurrencia
      posterior con progreso > ancla + τ (paradas coincidentes o solapadas: se salta
      todo lo que está dentro de la zona).
    - Velocidad: tramo prev→cap en segundos REALES; si su duración real es <= 0 se
      fusiona con los siguientes hasta la primera duración > 0 (el tope no cambia);
      si no existe ninguna, retención `schedule_incoherent`.
    """
    a = ctx.anchor_progress_m
    i = max(k for k, s in enumerate(ctx.stops) if s.progress_m <= a + tau)
    j = next(k for k in range(i + 1, len(ctx.stops)) if ctx.stops[k].progress_m > a + tau)
    dep_i = ctx.instant(ctx.stops[i].departure_s)
    speed = 0.0
    for k in range(j, len(ctx.stops)):
        dur = (ctx.instant(ctx.stops[k].arrival_s) - dep_i).total_seconds()
        dist = ctx.stops[k].progress_m - ctx.stops[i].progress_m
        if dur > 0 and dist > 0:
            speed = min(dist / dur, VMAX)
            break
    if speed == 0.0:
        return hold(ctx, "schedule_incoherent", rule + ":sin_duracion_positiva", coherent)
    start = moving_from if moving_from is not None and moving_from > ctx.anchor_at else ctx.anchor_at
    moving_s = (ctx.horizon_end - start).total_seconds()
    if moving_s <= 0:
        return hold(ctx, hold_reason or "horizon_exhausted", rule, coherent, dwell_basis)
    cap = ctx.stops[j].progress_m
    reach = min(cap, a + speed * moving_s)
    env = ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=a, speed_mps=speed,
                           max_progress_m=reach, horizon_s=horizon_s(ctx),
                           dwell_until=start if start > ctx.anchor_at else None)
    return Plan(env, rule, hold_reason=hold_reason if start > ctx.anchor_at else None,
                cap_stop_id=ctx.stops[j].stop_id, cap_kind="stop" if reach >= cap else "horizon",
                cap_reached_at=ceil_ms(start + timedelta(seconds=(reach - a) / speed)),
                coherent=coherent, dwell_basis=dwell_basis)


def schedule_rules(ctx: Ctx, tau: float, coherent: bool | None, prefix: str, min_dwell: float | None) -> Plan:
    """Pasos comunes por posición/horario: R6x, R6, R2, [zona R8], R5."""
    a = ctx.anchor_progress_m
    if a < ctx.stops[0].progress_m - tau:
        return hold(ctx, "outside_schedule_extent", prefix + "R6x", coherent)
    if a >= ctx.stops[-1].progress_m - tau:
        return hold(ctx, "terminal", prefix + "R6", coherent)
    first_dep = ctx.instant(ctx.stops[0].departure_s)
    if ctx.anchor_at < first_dep:
        if first_dep >= ctx.horizon_end:
            return hold(ctx, "before_first_departure", prefix + "R2", coherent)
        return leg(ctx, tau, prefix + "R2+R5", coherent, moving_from=first_dep, hold_reason="before_first_departure")
    if min_dwell is not None:  # solo la degradación R8 (alternativa C) retiene por zona de parada
        zone = [s for s in ctx.stops if abs(s.progress_m - a) <= tau]
        if zone:
            k = min(zone, key=lambda s: (abs(s.progress_m - a), s.index))
            dwell_real = (ctx.instant(k.departure_s) - ctx.instant(k.arrival_s)).total_seconds()  # R-DST
            entry = ctx.zone_entry_at or ctx.anchor_at
            basis = "muestras" if ctx.zone_entry_at is not None else "ancla"
            until = entry + timedelta(seconds=max(min_dwell, dwell_real))
            if until >= ctx.horizon_end:
                return hold(ctx, "schedule_stop_zone", prefix + "R8-zona", coherent, basis)
            if until > ctx.anchor_at:
                return leg(ctx, tau, prefix + "R8-zona", coherent, moving_from=until,
                           hold_reason="schedule_stop_zone", dwell_basis=basis)
            return leg(ctx, tau, prefix + "R8-zona-consumida", coherent, dwell_basis=basis)
    return leg(ctx, tau, prefix + "R5", coherent)


def zone_entry_from_history(stops: tuple[StopInfo, ...], tau: float,
                            history: list[tuple[datetime, float]]) -> tuple[datetime | None, int]:
    """Entrada en zona PROBADA por las muestras (§4.6): la observación más antigua de la racha
    consecutiva final (mismo viaje) cuya parada de zona es la del ancla. `history` va de la
    más antigua a la más reciente y termina en el ancla. Devuelve (entrada, n_muestras); la
    entrada real es <= la devuelta (cota superior), nunca posterior."""
    def zone_of(p: float) -> StopInfo | None:
        z = [s for s in stops if abs(s.progress_m - p) <= tau]
        return min(z, key=lambda s: (abs(s.progress_m - p), s.index)) if z else None
    anchor_at, anchor_p = history[-1]
    k = zone_of(anchor_p)
    if k is None:
        return None, 0
    entry, n = anchor_at, 1
    for obs_at, prog in reversed(history[:-1]):
        z = zone_of(prog)
        if z is None or z.index != k.index:
            break
        entry, n = obs_at, n + 1
    return entry, n


def classify(ctx: Ctx, tau: float) -> tuple[str, StopInfo | None, str]:
    status = (ctx.status or "").upper()
    if status not in KNOWN_STATUS or not ctx.current_stop_id:
        return "ABSENT", None, "estado_ausente"
    occurrences = [s for s in ctx.stops if s.stop_id == ctx.current_stop_id]
    if not occurrences:
        return "INCOHERENT", None, "stop_ajeno_al_viaje"
    x = min(occurrences, key=lambda s: (abs(s.progress_m - ctx.anchor_progress_m), s.index))
    gap = x.progress_m - ctx.anchor_progress_m
    if status == "STOPPED_AT" and abs(gap) > tau:
        return "INCOHERENT", x, "stopped_fuera_de_zona"
    if status == "INCOMING_AT" and gap < -tau:
        return "INCOHERENT", x, "incoming_parada_por_detras"
    return "COHERENT", x, status


def make_plan_c(tau: float, min_dwell: float) -> Callable[[Ctx], Plan]:
    def plan_c(ctx: Ctx) -> Plan:
        """C / R8: segmentos solo por horario, sin estado del operador."""
        if ctx.canceled:
            return hold(ctx, "trip_canceled", "R-CANCEL", None)
        return schedule_rules(ctx, tau, None, "R8:", min_dwell)
    return plan_c


def make_plan_a(tau: float, min_dwell: float = MIN_DWELL_S) -> Callable[[Ctx], Plan]:
    def plan_a(ctx: Ctx) -> Plan:
        """A, orden total: R-CANCEL > R7/R8 (ausente/incoherente) > R1 > R4 > R6x > R6 > R2 > R5."""
        if ctx.canceled:
            return hold(ctx, "trip_canceled", "R-CANCEL", None)
        state, x, why = classify(ctx, tau)
        if state == "ABSENT":
            return schedule_rules(ctx, tau, None, "R8(ausente):", min_dwell)
        if state == "INCOHERENT":
            return schedule_rules(ctx, tau, False, f"R7({why})->R8:", min_dwell)
        assert x is not None
        status = (ctx.status or "").upper()
        if status == "STOPPED_AT":
            return hold(ctx, "operator_stopped_at", "R1", True)
        if status == "INCOMING_AT" and abs(x.progress_m - ctx.anchor_progress_m) <= tau:
            return hold(ctx, "operator_incoming_at", "R4", True)
        return schedule_rules(ctx, tau, True, "", None)
    return plan_a


# --- alternativas de comparación (sin campos aditivos) ----------------------
def wrap(env: ProgressEnvelope, rule: str) -> Plan:
    return Plan(env, rule)


def envelope_offset_clamped(ctx: Ctx, lo: float, hi: float, tolerance_m: float = 1.0) -> ProgressEnvelope:
    """Variante de `_envelope` con `temporal_offset_s` acotado; con ±∞ reproduce producción."""
    sched = ctx.schedule
    anchor_s = service_seconds(ctx.anchor_at, ctx.service_date)
    offset = min(max(anchor_s - sched.seconds_at_progress(ctx.anchor_progress_m), lo), hi)
    hs = horizon_s(ctx)
    if hs == 0.0:
        return hold(ctx, "", "", None).env
    span_m = max(0.0, sched.progress_at(service_seconds(ctx.horizon_end, ctx.service_date) - offset)
                 - ctx.anchor_progress_m)
    dwell_end_s = sched.dwell_end_seconds(ctx.anchor_progress_m, tolerance_m=tolerance_m)
    dwell_until = None
    if dwell_end_s is not None:
        candidate = ctx.anchor_at + timedelta(seconds=dwell_end_s + offset - anchor_s)
        if ctx.anchor_at < candidate < ctx.horizon_end:
            dwell_until = candidate
    moving_s = max(0.0, (ctx.horizon_end - (dwell_until or ctx.anchor_at)).total_seconds())
    speed = min(span_m / moving_s, VMAX) if moving_s > 0 else 0.0
    return ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m,
                            speed_mps=speed, max_progress_m=ctx.anchor_progress_m + speed * moving_s,
                            horizon_s=hs, dwell_until=dwell_until)


def alt_base(ctx: Ctx) -> Plan:
    return wrap(_envelope(schedule=ctx.schedule, service_date=ctx.service_date, anchor_at=ctx.anchor_at,
                          anchor_progress_m=ctx.anchor_progress_m, horizon_end=ctx.horizon_end,
                          max_speed_mps=VMAX), "beb9434")


def alt_d(ctx: Ctx) -> Plan:
    return wrap(envelope_offset_clamped(ctx, -math.inf, math.inf, tolerance_m=TAU_STOP_M), "tolerancia")


def alt_b1(ctx: Ctx) -> Plan:
    return wrap(envelope_offset_clamped(ctx, -OFFSET_SYM_S, OFFSET_SYM_S), "offset±600")


def alt_b2(ctx: Ctx) -> Plan:
    first_dep = ctx.instant(ctx.stops[0].departure_s)
    if ctx.anchor_at >= first_dep:
        return alt_b1(ctx)
    if first_dep >= ctx.horizon_end:
        return wrap(hold(ctx, "", "", None).env, "pre_salida")
    env = envelope_offset_clamped(ctx, -OFFSET_SYM_S, OFFSET_SYM_S)
    moving_s = (ctx.horizon_end - first_dep).total_seconds()
    speed = min((env.max_progress_m - ctx.anchor_progress_m) / moving_s, VMAX)
    return wrap(ProgressEnvelope(reference_at=ctx.anchor_at, progress_m_at_reference=ctx.anchor_progress_m,
                                 speed_mps=speed, max_progress_m=ctx.anchor_progress_m + speed * moving_s,
                                 horizon_s=env.horizon_s, dwell_until=first_dep), "pre_salida")


ALTERNATIVES: dict[str, Callable[[Ctx], Plan]] = {
    "BASE(beb9434)": alt_base,
    f"D(tolerancia={TAU_STOP_M:g})": alt_d,
    "B1(offset±600)": alt_b1,
    "B2(offset+ventana)": alt_b2,
    f"C(τ={TAU_STOP_M:g},Dmin={MIN_DWELL_S:g})": make_plan_c(TAU_STOP_M, MIN_DWELL_S),
    f"A(τ={TAU_STOP_M:g})": make_plan_a(TAU_STOP_M),
}
A_NAME = f"A(τ={TAU_STOP_M:g})"
C_NAME = f"C(τ={TAU_STOP_M:g},Dmin={MIN_DWELL_S:g})"


def phase(plan: Plan, at: datetime) -> str:
    """Fase del FOTOGRAMA `at` (§4.3 b): función pura de la envolvente publicada."""
    env = plan.env
    t0 = env.dwell_until or env.reference_at
    if env.speed_mps == 0.0 or at < t0:
        return f"hold:{plan.hold_reason}"
    if plan.cap_reached_at is not None and at >= plan.cap_reached_at:
        return f"cap:{plan.cap_kind}"
    return "moving"


# =========================================================================
# 3. Cortes reales
# =========================================================================
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
    engine: MovementEngine
    corridor: object
    pattern_id: str
    geometry_version: str | None
    latest: VehiclePositionObservation
    previous: VehiclePositionObservation | None


@dataclass
class Pair:
    ctx0: Ctx
    truth_progress_m: float
    prod_envelope: ProgressEnvelope
    status0: str


def build_real(replay: Path) -> tuple[list[RealCase], list[Pair], dict, Topology]:
    topo = load_feed(replay / "fomento_transit.zip", network_id="10")
    cat = build_catalog(topo, gtfs_version="mp024")
    corridors = build_madrid_corridor_catalog(cat, topo, fixtures_root=ROOT / "tests" / "fixtures")
    trip_route = {t.trip_id: t.route_id for t in topo.trips}
    prev_cut, last_cut = load_cut(replay, "1532"), load_cut(replay, "1533")
    cases: list[RealCase] = []
    pairs: list[Pair] = []
    facts: dict = {"in_transit_behind_detail(trip,stop,m_por_detras)": [], "reproj_m": []}
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
        mv = engine.position(trip_id=trip_id, service_date=sd, calculated_at=now, latest=latest, previous=previous)
        rd = render_from_movement(mv, schedule=schedule, corridor=cov.corridor, service_date=sd, display_at=now,
                                  pattern_id=cov.identity.pattern_id, geometry_version=cov.geometry_version,
                                  thresholds=TH)
        if rd.progress_envelope is None or rd.valid_until is None or mv.anchor_progress_m is None:
            continue
        assert mv.observed_at == latest.observed_at, "el motor no debería rechazar ninguna observación del corte"
        anchor_s = service_seconds(latest.observed_at, sd)
        cohort = ("pre_salida" if anchor_s < schedule.points[0].seconds
                  else "post_llegada" if anchor_s > schedule.points[-1].seconds else "en_ventana")
        history = [(latest.observed_at, mv.anchor_progress_m)]
        if previous is not None:
            history.insert(0, (previous.observed_at,
                               schedule.directed_progress(engine.map_match(previous).physical_arc_m)))
        entry, n_samples = zone_entry_from_history(stops, TAU_STOP_M, history)
        facts["zona_con_2_muestras_consecutivas"] = facts.get("zona_con_2_muestras_consecutivas", 0) + (n_samples >= 2)
        ctx = Ctx(trip_id=trip_id, schedule=schedule, stops=stops, service_date=sd, anchor_at=latest.observed_at,
                  anchor_progress_m=mv.anchor_progress_m, horizon_end=rd.valid_until, status=latest.current_status,
                  current_stop_id=latest.current_stop_id, label=trip_id,
                  zone_entry_at=entry if n_samples >= 2 else None)
        same_gps = (previous is not None and previous.latitude == latest.latitude
                    and previous.longitude == latest.longitude)
        cases.append(RealCase(vid, ctx, cohort, same_gps, latest.current_stop_id == stops[0].stop_id,
                              rd.progress_envelope, engine, cov.corridor, cov.identity.pattern_id,
                              cov.geometry_version, latest, previous))
        if (latest.current_status or "").upper() == "IN_TRANSIT_TO":
            occ = [s for s in stops if s.stop_id == latest.current_stop_id]
            if occ:
                x = min(occ, key=lambda s: abs(s.progress_m - ctx.anchor_progress_m))
                if ctx.anchor_progress_m - x.progress_m > 1000:
                    facts["in_transit_behind_detail(trip,stop,m_por_detras)"].append(
                        (trip_id, x.stop_id, round(ctx.anchor_progress_m - x.progress_m, 2)))
        m = corridors.match_position(cov.identity.pattern_id, raw_lat=latest.latitude, raw_lon=latest.longitude)
        if m.projection is not None:
            lat, lon = _coordinate(cov.corridor, schedule, mv.anchor_progress_m)
            facts["reproj_m"].append(haversine_m(lat, lon, m.projection.lat, m.projection.lon))
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
                pairs.append(Pair(ctx0, mv.anchor_progress_m, rd0.progress_envelope, previous.current_status or ""))
    return cases, pairs, facts, topo


def equivalence_check(cases: list[RealCase]) -> int:
    """Igualdad COMPLETA de campos: publicada == `_envelope` == variante B(±∞)."""
    ok = 0
    for c in cases:
        mine = alt_base(c.ctx).env
        clamp = envelope_offset_clamped(c.ctx, -math.inf, math.inf)
        ok += c.prod_envelope == mine == clamp
    return ok


def gtfs_structure(cases: list[RealCase], tau: float) -> dict:
    repeated, coincident, overlap, zero_legs, legs = 0, 0, 0, 0, 0
    for c in cases:
        ids = [s.stop_id for s in c.ctx.stops]
        repeated += len(ids) - len(set(ids))
        for a, b in zip(c.ctx.stops, c.ctx.stops[1:]):
            legs += 1
            sep = b.progress_m - a.progress_m
            coincident += sep <= tau
            overlap += sep <= 2 * tau
            zero_legs += (c.ctx.instant(b.arrival_s) - c.ctx.instant(a.departure_s)).total_seconds() <= 0
    return {"trips": len(cases), "legs": legs, "stop_id_repetidos": repeated,
            f"tramos_sep<=τ({tau:g})": coincident, f"tramos_sep<=2τ({2 * tau:g})": overlap,
            "tramos_duracion_real<=0": zero_legs}


def real_metrics(name: str, alt: Callable[[Ctx], Plan], cases: list[RealCase], pairs: list[Pair],
                 tau: float = TAU_STOP_M) -> dict:
    """Predicados exactos, sin redondeo, con denominadores comprobados."""
    plans = {c.vid: alt(c.ctx) for c in cases}
    pub = lambda c: plans[c.vid].env.speed_mps > 0.0
    adv = lambda c: advance(plans[c.vid].env, c.ctx.horizon_end) > 0.0
    stopped = [c for c in cases if (c.ctx.status or "").upper() == "STOPPED_AT"]
    same = [c for c in stopped if c.same_gps]
    pre = [c for c in cases if c.cohort == "pre_salida"]
    late = [c for c in stopped if c.at_origin and c.cohort == "en_ventana"]
    mid = [c for c in stopped if not c.at_origin]
    assert (len(cases), len(stopped), len(same), len(pre), len(late), len(mid)) == (44, 28, 25, 17, 4, 7)
    res: dict = {"alternative": name}
    res["M1_stopped_same_gps_speed_gt0"] = (sum(map(pub, same)), len(same))
    res["M1_stopped_same_gps_advance_gt0"] = (sum(map(adv, same)), len(same))
    assert all((c.ctx.status or "").upper() == "STOPPED_AT" for c in pre), "las 17 pre-salidas son STOPPED_AT"
    res["M2a_R1_pre_salida_STOPPED_AT_speed_gt0"] = (sum(map(pub, pre)), len(pre))
    before_dep = lambda c: advance(plans[c.vid].env, min(c.ctx.horizon_end,
                                                         c.ctx.instant(c.ctx.stops[0].departure_s))) > 0.0
    res["M2b_R2_avance_hasta_min(salida,horizonte)_gt0"] = (sum(map(before_dep, pre)), len(pre))
    res["M3_delayed_origin_speed_gt0"] = (sum(map(pub, late)), len(late))
    res["M4_intermediate_stopped_speed_gt0"] = (sum(map(pub, mid)), len(mid))

    def crossed(c: RealCase, margin: float) -> list[tuple[str, float]]:
        env = plans[c.vid].env
        p0, p1 = env.progress_m_at_reference, env.progress_at(c.ctx.horizon_end)
        return [(s.stop_id, s.progress_m - p0) for s in c.ctx.stops if p0 + margin < s.progress_m < p1]
    res["M5_cross_stop_margin_1m"] = (sum(bool(crossed(c, 1.0)) for c in cases), len(cases))
    res["M5b_cross_stop_beyond_tau"] = (sum(bool(crossed(c, tau)) for c in cases), len(cases))
    res["M5_detail_within_tau(trip,stop,m)"] = [
        (c.ctx.trip_id, s, round(d, 2)) for c in cases for s, d in crossed(c, 1.0) if d <= tau]
    c19656 = next(c for c in cases if c.ctx.trip_id == "1023V19656C5")
    e = plans[c19656.vid].env
    res["M6_19656_advance_30s_60s"] = (advance(e, c19656.ctx.anchor_at + timedelta(seconds=30)),
                                       advance(e, c19656.ctx.anchor_at + timedelta(seconds=60)))
    assert len(pairs) == 44 and {(p.ctx0.extra["t1"] - p.ctx0.anchor_at).total_seconds() for p in pairs} == {77.0}
    errors, guard, guard_n, cost, cost_n, over = [], [], 0, [], 0, 0
    for p in pairs:
        env0 = p.prod_envelope if name.startswith("BASE") else alt(p.ctx0).env
        pred = advance(env0, p.ctx0.extra["t1"])
        obs = p.truth_progress_m - p.ctx0.anchor_progress_m
        errors.append(abs(pred - obs))
        over += pred - obs > LOST_OBS_M
        status0 = p.status0.upper()
        if status0 in ("IN_TRANSIT_TO", "INCOMING_AT") and obs >= LOST_OBS_M:
            guard_n += 1
            if pred == 0.0:
                guard.append(p.ctx0.trip_id)
        if status0 == "STOPPED_AT":
            cost_n += 1
            if obs >= LOST_OBS_M and pred == 0.0:
                cost.append((p.ctx0.trip_id, round(obs, 1)))
    assert guard_n == 9 and cost_n == 27
    res["M7_guard_transit_incoming_moved_pred_eq0"] = (len(guard), guard_n)
    res["COST_stopped1532_departed_pred_eq0"] = (len(cost), cost_n, cost)
    res["M7_snap_77s_p50_p90_max"] = (statistics.median(errors), quantile(errors, 0.9), max(errors))
    res["M7_over_advance_gt100m"] = (over, len(pairs))
    regress = [advance(plans[c.vid].env, c.ctx.horizon_end) for c in cases]
    res["M8_rewind_if_frozen_at_anchor_p50_max"] = (statistics.median(regress), max(regress))
    rules: dict[str, int] = {}
    for c in cases:
        rules[plans[c.vid].rule] = rules.get(plans[c.vid].rule, 0) + 1
    res["rules"] = dict(sorted(rules.items()))
    res["GROUP_M_pass"] = {
        "AC-M1 0/25 STOPPED_AT GPS idéntico con speed_mps>0": res["M1_stopped_same_gps_speed_gt0"][0] == 0,
        "AC-M2 (R1) 0/17 pre-salida STOPPED_AT con speed_mps>0": res["M2a_R1_pre_salida_STOPPED_AT_speed_gt0"][0] == 0,
        "AC-M3 0/4 salida retrasada con speed_mps>0": res["M3_delayed_origin_speed_gt0"][0] == 0,
        "AC-M4 0/7 intermedias con speed_mps>0": res["M4_intermediate_stopped_speed_gt0"][0] == 0,
        "AC-M5 0/44 cruzan parada > τ": res["M5b_cross_stop_beyond_tau"][0] == 0,
        "AC-M6 19656 avance a 30 s == 0": res["M6_19656_advance_30s_60s"][0] == 0.0,
        "AC-M7 guarda 0/9 IN_TRANSIT_TO/INCOMING_AT que avanzaron con predicción == 0": not guard,
    }
    alt_m = dict(res["GROUP_M_pass"])
    alt_m.pop("AC-M2 (R1) 0/17 pre-salida STOPPED_AT con speed_mps>0")
    alt_m["M2b (R2) 0/17 con avance antes de la salida"] = res["M2b_R2_avance_hasta_min(salida,horizonte)_gt0"][0] == 0
    res["GROUP_M_si_M2b_sustituye_a_M2a"] = sum(alt_m.values())
    return res


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    k = (len(ordered) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


# =========================================================================
# 4. Camino STALE (R-STALE F1/F2), actualizaciones de trip_update, reinicio
# =========================================================================
@dataclass(frozen=True)
class Update:
    """Una `trip_update` con sus tres relojes (§4.4).

    - `observed_at`: cuándo OCURRIÓ según la fuente (cabecera del feed);
    - `received_at`: cuándo la recibió el colector (`0001_init.up.sql:110`);
    - `run`: `ingestion_run_id` del ciclo que la confirmó;
    - `visible_at`: cuándo quedó visible para una consulta (commit del ciclo). Con un
      único colector y un commit por ciclo (`collector.py:115-118`), `visible_at` sigue el
      orden de `run`; los escenarios «condición violada» rompen esa hipótesis a propósito.
    """

    observed_at: datetime
    received_at: datetime
    run: int
    visible_at: datetime
    kind: str  # CANCELED | SCHEDULED


def authorized_plan(ctx: Ctx, plan_fn: Callable[[Ctx], Plan], updates: Iterable[Update], query_at: datetime,
                    policy: str = "inmutable") -> tuple[Plan, str]:
    """Envolvente autorizada para el ancla vista por una consulta en `query_at`.

    `inmutable` (política adoptada, §4.4): solo cuentan las filas con `run <= anchor_run`
    (estado disponible cuando el ancla lo estuvo); de ellas, la última por `(run, observed_at)`;
    una CANCELED solo aplica si `anchor_at - observed_at <= CANCEL_MAX_AGE_S`. Ninguna fila
    posterior al run del ancla modifica esta envolvente ni su congelación: se aplica a la
    SIGUIENTE ancla. `observed` reproduce la política de la ronda 2 (recorte en `observed_at`)
    solo para mostrar el contraejemplo del revisor.
    """
    seen = [u for u in updates if u.visible_at <= query_at]
    if policy == "observed":
        base = [u for u in seen if u.observed_at <= ctx.anchor_at]
        canceled = bool(base) and max(base, key=lambda u: u.observed_at).kind == "CANCELED"
        plan = plan_fn(replace(ctx, canceled=canceled or ctx.canceled))
        for u in sorted(seen, key=lambda u: u.observed_at):
            if ctx.anchor_at < u.observed_at <= min(ctx.horizon_end, query_at) and u.kind == "CANCELED" \
                    and plan.env.speed_mps > 0.0:
                env = plan.env
                cut = max(env.progress_m_at_reference, min(env.max_progress_m, env.progress_at(u.observed_at)))
                return replace(plan, env=replace(env, max_progress_m=cut), cap_kind="trip_canceled"), "recorte"
        return plan, "sin_recorte"
    base = sorted((u for u in seen if u.run <= ctx.anchor_run), key=lambda u: (u.run, u.observed_at))
    last = base[-1] if base else None
    fresh = last is not None and (ctx.anchor_at - last.observed_at).total_seconds() <= CANCEL_MAX_AGE_S
    canceled = last is not None and last.kind == "CANCELED" and fresh
    why = ("cancelada" if canceled else "cancelacion_caducada" if last is not None and last.kind == "CANCELED"
           else "sin_cancelacion")
    return plan_fn(replace(ctx, canceled=canceled or ctx.canceled)), why


def present(ctx: Ctx, plan_fn: Callable[[Ctx], Plan], display_at: datetime, *, rule: str = "F1",
            updates: Iterable[Update] = (), versions_match: bool = True, policy: str = "inmutable") -> dict:
    """Coordenada publicada (progreso) en `display_at`; el reloj de disponibilidad es `display_at`."""
    plan, why = authorized_plan(ctx, plan_fn, updates, display_at, policy)
    if display_at <= ctx.horizon_end:
        p = plan.env.progress_at(display_at)
        method = "extrapolated_from_last_anchor" if p > ctx.anchor_progress_m else "anchor"
        return {"method": method, "progress_m": p, "base": why}
    if not versions_match:
        return {"method": "stale_frozen", "progress_m": ctx.anchor_progress_m, "frozen_basis": "anchor_version_changed"}
    end = plan.env.progress_at(ctx.horizon_end)
    if rule == "F1":
        return {"method": "stale_frozen", "progress_m": end, "frozen_basis": "authorized_envelope_end",
                "last_confirmed_progress_m": ctx.anchor_progress_m, "base": why}
    return {"method": "stale_frozen", "progress_m": ctx.anchor_progress_m, "frozen_basis": "anchor",
            "rewound_from_progress_m": end, "rewind_m": end - ctx.anchor_progress_m, "base": why}


def stale_tests(cases: list[RealCase]) -> dict:
    """Camino stale con disponibilidad que VARÍA entre consultas (cada consulta ve solo las
    filas con `visible_at <= display_at`), 25 en ventana, muestreo cada 0,5 s de 0 a 400 s."""
    plan_a = make_plan_a(TAU_STOP_M)
    win = [c for c in cases if c.cohort == "en_ventana"]
    assert len(win) == 25

    def up(a: datetime, obs: float, run: int, vis: float, kind: str = "CANCELED", rec: float | None = None) -> Update:
        return Update(a + timedelta(seconds=obs), a + timedelta(seconds=obs if rec is None else rec), run,
                      a + timedelta(seconds=vis), kind)
    scenarios: dict[str, Callable[[datetime], list[Update]]] = {
        "sin_cambio": lambda a: [],
        "posterior_obs+20_visible+20": lambda a: [up(a, 20, 101, 20)],
        "posterior_obs+20_visible+181(contraejemplo)": lambda a: [up(a, 20, 101, 181, rec=181)],
        "posterior_obs+60_y_anulada+150": lambda a: [up(a, 60, 101, 60), up(a, 150, 102, 150, "SCHEDULED")],
        "base_obs−300(reciente)": lambda a: [up(a, -300, 99, -300)],
        "base_obs−86400(ayer)": lambda a: [up(a, -86400, 50, -86400)],
        "base_obs−700_recibida−5(edad>umbral)": lambda a: [up(a, -700, 99, -5, rec=-5)],
        "CONDICION_VIOLADA_base_run99_visible+100": lambda a: [up(a, -10, 99, 100)],
    }
    out: dict = {}
    for sname, mk in scenarios.items():
        back_f1, f2_mismatch, rewind_pos, restart, base_counts = 0.0, 0.0, 0, 0, {}
        for c in win:
            ups = mk(c.ctx.anchor_at)
            series = []
            for k in range(801):
                t = c.ctx.anchor_at + timedelta(seconds=k * 0.5)
                series.append(present(c.ctx, plan_a, t, rule="F1", updates=ups)["progress_m"])
            back_f1 = max([back_f1] + [a - b for a, b in pairwise(series)])
            before = present(c.ctx, plan_a, c.ctx.horizon_end, rule="F2", updates=ups)["progress_m"]
            after = present(c.ctx, plan_a, c.ctx.horizon_end + timedelta(milliseconds=1), rule="F2", updates=ups)
            f2_mismatch = max(f2_mismatch, abs((before - after["progress_m"]) - after["rewind_m"]))
            rewind_pos += after["rewind_m"] > 0.0
            fresh = present(c.ctx, plan_a, c.ctx.horizon_end + timedelta(seconds=1), rule="F1", updates=ups)
            restart += fresh["progress_m"] != series[362]
            why = fresh["base"]
            base_counts[why] = base_counts.get(why, 0) + 1
        out[sname] = {"n": len(win), "base": base_counts, "F1_max_retroceso_m": back_f1,
                      "F2_|salto−rewind_m|_max": f2_mismatch, "F2_con_rewind>0": rewind_pos,
                      "reinicio_distinto": restart}
    c = win[0]
    v = present(c.ctx, plan_a, c.ctx.horizon_end + timedelta(seconds=1), versions_match=False)
    out["cambio_de_version"] = {"frozen_basis": v["frozen_basis"], "en_ancla": v["progress_m"] == c.ctx.anchor_progress_m}
    # Contraejemplo del revisor en 19667: la cancelación (observed_at = +20 s) no estaba disponible
    # a +179 s y sí a +181 s. Se consulta con la lista de filas que cada consulta VE realmente.
    x = next(c for c in win if c.ctx.trip_id == "1023V19667C5").ctx
    late = [up(x.anchor_at, 20, 101, 181, rec=181)]
    res = {}
    for policy in ("observed", "inmutable"):
        p179 = present(x, plan_a, x.anchor_at + timedelta(seconds=179), updates=late, policy=policy)["progress_m"]
        p181 = present(x, plan_a, x.anchor_at + timedelta(seconds=181), updates=late, policy=policy)["progress_m"]
        res[policy] = {"+179_m": p179 - x.anchor_progress_m, "+181_m": p181 - x.anchor_progress_m,
                       "retroceso_m": p179 - p181}
    out["contraejemplo_19667"] = res
    return out


def baseline_expiry_and_two_coords(cases: list[RealCase]) -> dict:
    """Producción: FR-05 (179→181 s, camino stale REAL) y FR-27 en progreso Y en coordenadas."""
    regress, dprog, dcoord, n = [], [], [], 0
    for c in cases:
        if c.cohort != "en_ventana":
            continue
        sd, sched = c.ctx.service_date, c.ctx.schedule
        out = {}
        for age in (179, 181):
            t = c.latest.observed_at + timedelta(seconds=age)
            mv = c.engine.position(trip_id=c.ctx.trip_id, service_date=sd, calculated_at=t, latest=c.latest)
            rd = render_from_movement(mv, schedule=sched, corridor=c.corridor, service_date=sd, display_at=t,
                                      pattern_id=None, geometry_version=None, thresholds=TH)
            out[age] = rd
        assert out[181].rendering_method is RenderingMethod.STALE_FROZEN
        regress.append(out[179].progress_m - out[181].progress_m)
        for age in range(61, 180):
            t = c.latest.observed_at + timedelta(seconds=age)
            mv = c.engine.position(trip_id=c.ctx.trip_id, service_date=sd, calculated_at=t, latest=c.latest)
            if mv.position_mode is not PositionMode.ESTIMATED:
                continue
            rd = render_from_movement(mv, schedule=sched, corridor=c.corridor, service_date=sd, display_at=t,
                                      pattern_id=None, geometry_version=None, thresholds=TH)
            n += 1
            dprog.append(abs(rd.progress_m - mv.progress_m))
            dcoord.append(haversine_m(rd.latitude, rd.longitude, mv.latitude, mv.longitude))
    return {"FR05_retroceso_179_181_n_gt0": (sum(r > 0 for r in regress), len(regress)),
            "FR05_retroceso_p50_max_m": (statistics.median(regress), max(regress)),
            "FR27_muestras(edades_enteras_61-179,estimated)": n,
            "FR27_|Δprogreso|_max_m": max(dprog), "FR27_distancia_lat/lon_max_m": max(dcoord)}


# =========================================================================
# 5. Ramas de presentación con el motor real
# =========================================================================
def presentation_tests(cases: list[RealCase], topo: Topology) -> dict:
    out: dict = {}
    plan_a = make_plan_a(TAU_STOP_M)
    # P1: el motor rechaza `latest` (salto imposible) y usa `previous`: el estado de
    # parada debe ser el de la observación EFECTIVA (la de `observed_at` del ancla).
    c = next(c for c in cases if c.ctx.trip_id == "1023V19664C5")
    prev, latest = c.previous, c.latest
    assert prev is not None
    sd = latest.observed_at.astimezone(MADRID).date()
    p_prev = c.ctx.schedule.directed_progress(c.engine.map_match(prev).physical_arc_m)
    near = min(c.ctx.stops, key=lambda s: abs(s.progress_m - p_prev))
    jumped = latest.model_copy(update={"latitude": latest.latitude + 0.27, "current_status": "STOPPED_AT",
                                       "current_stop_id": near.stop_id})
    now = latest.observed_at + timedelta(seconds=CALC_DELAY_S)
    mv = c.engine.position(trip_id=c.ctx.trip_id, service_date=sd, calculated_at=now, latest=jumped, previous=prev)
    effective = prev if mv.observed_at == prev.observed_at else jumped
    base = replace(c.ctx, anchor_at=mv.observed_at, anchor_progress_m=mv.anchor_progress_m,
                   horizon_end=mv.observed_at + timedelta(seconds=TH.stale_after_s))
    right = plan_a(replace(base, status=effective.current_status, current_stop_id=effective.current_stop_id))
    wrong = plan_a(replace(base, status=jumped.current_status, current_stop_id=jumped.current_stop_id))
    out["P1_motor_usa_previous"] = mv.observed_at == prev.observed_at
    out["P1_estado_de_la_observacion_efectiva"] = (effective.current_status, right.rule, right.env.speed_mps > 0)
    out["P1_si_se_usara_latest(erroneo)"] = (jumped.current_status, wrong.rule, wrong.env.speed_mps > 0)
    out["P1_resultados_distintos"] = right.env != wrong.env
    # P2: sin ancla utilizable (motor SCHEDULED): schedule_only con R8 sobre el punto
    # de horario; si CANCELED, `unlocated` sin coordenada.
    c2 = next(c for c in cases if c.ctx.trip_id == "1023V20849C5")
    now2 = c2.latest.observed_at + timedelta(seconds=CALC_DELAY_S)
    mv2 = c2.engine.position(trip_id=c2.ctx.trip_id, service_date=c2.ctx.service_date, calculated_at=now2)
    assert mv2.position_mode is PositionMode.SCHEDULED and mv2.anchor_progress_m is None
    sched_ctx = replace(c2.ctx, anchor_at=now2, anchor_progress_m=mv2.progress_m, status=None,
                        current_stop_id=None, horizon_end=now2 + timedelta(seconds=TH.stale_after_s))
    sp = plan_a(sched_ctx)
    out["P2_schedule_only_regla"] = (sp.rule, sp.coherent)
    out["P2_CANCELED_sin_ancla"] = present_branch(has_corridor=True, anchor=None, canceled=True)
    # P3: solo raw (patrón sin corredor): sin envolvente; CANCELED solo rotula.
    out["P3_solo_raw"] = present_branch(has_corridor=False, anchor="raw", canceled=False)
    out["P3_solo_raw_CANCELED"] = present_branch(has_corridor=False, anchor="raw", canceled=True)
    # P4: display_lag con dos anclas reales: interpolación; se compara con PRODUCCIÓN.
    c4 = next(c for c in cases if c.ctx.trip_id == "1023V19656C5")
    assert c4.previous is not None
    p0 = c4.ctx.schedule.directed_progress(c4.engine.map_match(c4.previous).physical_arc_m)
    disp = c4.latest.observed_at - timedelta(seconds=30)
    mv4 = c4.engine.position(trip_id=c4.ctx.trip_id, service_date=c4.ctx.service_date,
                             calculated_at=c4.latest.observed_at + timedelta(seconds=CALC_DELAY_S),
                             latest=c4.latest, previous=c4.previous)
    rd4 = render_from_movement(mv4, schedule=c4.ctx.schedule, corridor=c4.corridor,
                               service_date=c4.ctx.service_date, display_at=disp, pattern_id=None,
                               geometry_version=None, thresholds=TH,
                               previous_anchor=AnchorSample(c4.previous.observed_at, p0))
    span = (c4.latest.observed_at - c4.previous.observed_at).total_seconds()
    mine = p0 + (disp - c4.previous.observed_at).total_seconds() / span * (c4.ctx.anchor_progress_m - p0)
    out["P4_interpolacion_metodo_produccion"] = rd4.rendering_method.value
    out["P4_|prototipo−produccion|_m"] = abs(mine - rd4.progress_m)
    out["P4_span_s(<=stale_after_s_exigido)"] = span
    return out


def present_branch(*, has_corridor: bool, anchor: str | None, canceled: bool) -> dict:
    """Tabla de precedencia de ramas (§4.6) como función pura, para las ramas sin envolvente."""
    if anchor is None:
        if canceled:
            return {"method": "unlocated", "lat": None, "reason": "trip_canceled", "envelope": None}
        return {"method": "schedule_only" if has_corridor else "unlocated", "envelope": "R8"}
    if anchor == "raw" or not has_corridor:
        return {"method": "anchor", "coordinate_space": "raw", "envelope": None,
                "reason": "trip_canceled" if canceled else "sin_corredor", "rewind_m": 0.0}
    return {"method": "envelope"}


# =========================================================================
# 6. Casos sintéticos
# =========================================================================
def synthetic_cases(real: list[RealCase]) -> list[tuple[str, Ctx, str, Callable[[Plan, Ctx], tuple[bool | None, str]]]]:
    base = next(c for c in real if c.ctx.trip_id == "1023V19656C5").ctx
    stops = base.stops
    first = stops[0]
    dwell_stop = next(s for s in stops[1:-1] if s.departure_s > s.arrival_s)
    plain_i = next(i for i, s in enumerate(stops[1:-1], 1) if s.departure_s == s.arrival_s)
    plain = stops[plain_i]
    sd = base.service_date
    inst = lambda s: service_day_instant(sd, s)
    plan_c = make_plan_c(TAU_STOP_M, MIN_DWELL_S)

    def mk(label: str, at: datetime, progress: float, status: str | None, stop_id: str | None, **kw) -> Ctx:
        return Ctx(trip_id=base.trip_id, schedule=base.schedule, stops=stops, service_date=sd, anchor_at=at,
                   anchor_progress_m=progress, horizon_end=at + timedelta(seconds=TH.stale_after_s),
                   status=status, current_stop_id=stop_id, label=label, **kw)

    def zero_until(t_rel: float, reason: str | None = None):
        def check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
            a = advance(p.env, ctx.anchor_at + timedelta(seconds=t_rel))
            ok = a == 0.0 and (reason is None or p.hold_reason == reason or p.hold_reason is None and reason == "")
            return ok, f"avance a {t_rel:g} s = {a!r} m; hold_reason={p.hold_reason}; regla={p.rule}"
        return check

    def equals_fallback(expect_move: bool):
        def check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
            fb = plan_c(ctx)
            a = advance(p.env, ctx.horizon_end)
            ok = p.rule.startswith("R7") and p.coherent is False and p.env == fb.env and ((a > 0.0) == expect_move)
            return ok, f"regla={p.rule}; coherent={p.coherent}; envolvente==R8: {p.env == fb.env}; avance={a!r} m"
        return check

    out = []
    out.append(("S1 pre-salida −300 s, STOPPED_AT origen",
                mk("S1", inst(first.departure_s - 300), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "avance == 0 en todo el horizonte", zero_until(TH.stale_after_s)))

    def s2_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        a = advance(p.env, inst(first.departure_s) - timedelta(milliseconds=1))
        return a == 0.0, f"avance 1 ms antes de la salida = {a!r} m"
    out.append(("S2 pre-salida −60 s, STOPPED_AT origen",
                mk("S2", inst(first.departure_s - 60), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "avance == 0 antes de la salida", s2_check))

    def s2b_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        dep = inst(first.departure_s)
        a_before = advance(p.env, dep - timedelta(milliseconds=1))
        a_after = advance(p.env, dep + timedelta(seconds=30))
        phases = [phase(p, t) for t in (ctx.anchor_at, dep - timedelta(milliseconds=1), dep,
                                        (p.cap_reached_at or dep) - timedelta(milliseconds=1),
                                        p.cap_reached_at or dep, ctx.horizon_end)]
        at_cap = p.env.progress_at(p.cap_reached_at) == p.env.max_progress_m if p.cap_reached_at else False
        ok = (a_before == 0.0 and a_after > 0.0 and p.hold_reason == "before_first_departure"
              and phases[0] == phases[1] == "hold:before_first_departure" and phases[2] == "moving"
              and phases[4].startswith("cap:") and at_cap)
        return ok, f"antes={a_before!r} m, +30 s={a_after:.3f} m, fases={phases}, en_tope_exacto={at_cap}"
    out.append(("S2b R2 sin STOPPED_AT (IN_TRANSIT_TO), salida a +60 s dentro del horizonte",
                mk("S2b", inst(first.departure_s - 60), first.progress_m + 4.4, "IN_TRANSIT_TO", first.stop_id),
                "0 antes de la salida, > 0 después, fases hold→moving→cap", s2b_check))
    out.append(("S3 salida retrasada +120 s, STOPPED_AT origen",
                mk("S3", inst(first.departure_s + 120), first.progress_m + 4.4, "STOPPED_AT", first.stop_id),
                "avance == 0", zero_until(TH.stale_after_s)))
    out.append(("S4 intermedia con espera 60 s, ancla +5,38 m, STOPPED_AT",
                mk("S4", inst(dwell_stop.arrival_s + 20), dwell_stop.progress_m + 5.38, "STOPPED_AT",
                   dwell_stop.stop_id), "avance == 0 a 30 s", zero_until(30)))
    out.append(("S5 intermedia SIN espera programada, STOPPED_AT",
                mk("S5", inst(plain.arrival_s + 30), plain.progress_m - 3.0, "STOPPED_AT", plain.stop_id),
                "avance == 0", zero_until(TH.stale_after_s)))
    out.append(("S5b contraejemplo del revisor: INCOMING_AT a la parada ANTERIOR, ancla en zona de S5",
                mk("S5b", inst(plain.arrival_s + 30), plain.progress_m - 3.0, "INCOMING_AT",
                   stops[plain_i - 1].stop_id),
                "R7 → R8 idéntico a C, avance a 20 s == 0", lambda p, ctx: (
                    equals_fallback(True)(p, ctx)[0] and advance(p.env, ctx.anchor_at + timedelta(seconds=20)) == 0.0,
                    equals_fallback(True)(p, ctx)[1]
                    + f"; avance 20 s = {advance(p.env, ctx.anchor_at + timedelta(seconds=20))!r} m")))
    mid_p = (stops[plain_i].progress_m + stops[plain_i + 1].progress_m) / 2
    mid_t = (stops[plain_i].departure_s + stops[plain_i + 1].arrival_s) / 2
    out.append(("S6 CANCELED, IN_TRANSIT_TO a mitad de tramo",
                mk("S6", inst(mid_t), mid_p, "IN_TRANSIT_TO", plain.stop_id, canceled=True),
                "avance == 0 y hold_reason=trip_canceled", zero_until(TH.stale_after_s, "trip_canceled")))

    def moves(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        a = advance(p.env, ctx.horizon_end)
        return a > 0.0, f"avance en el horizonte = {a:.3f} m"
    out.append(("S6b control: en marcha a mitad de tramo",
                mk("S6b", inst(mid_t), mid_p, "IN_TRANSIT_TO", plain.stop_id), "avance > 0", moves))
    out.append(("S7 STOPPED_AT con stop_id ajeno, a mitad de tramo",
                mk("S7", inst(mid_t), mid_p, "STOPPED_AT", "99999"),
                "R7 → R8: envolvente idéntica a C, coherent=false, avanza", equals_fallback(True)))
    out.append((f"S10 INCOMING_AT con parada {mid_p - plain.progress_m:.0f} m POR DETRÁS",
                mk("S10", inst(mid_t), mid_p, "INCOMING_AT", plain.stop_id),
                "R7 → R8: idéntica a C, coherent=false, avanza", equals_fallback(True)))
    out.append(("S11 ancla 500 m ANTES de la primera parada (fuera de zona), en ventana",
                mk("S11", inst(first.departure_s + 60), first.progress_m - 500.0, "IN_TRANSIT_TO", first.stop_id),
                "retención outside_schedule_extent", zero_until(TH.stale_after_s, "outside_schedule_extent")))
    # Horarios sintéticos de geometría controlada (S12–S15) y DST (S8, S9, S15).
    def synth(d: date, pts: list[tuple[str, float, str, str]], status: str | None, stop_id: str | None,
              anchor_utc: datetime, anchor_p: float, label: str, **kw) -> Ctx:
        st = tuple(StopInfo(sid, p, parse_gtfs_time(arr), parse_gtfs_time(dep), i)
                   for i, (sid, p, arr, dep) in enumerate(pts))
        points = []
        for s in st:
            if s.departure_s > s.arrival_s:
                points.append(SchedulePoint(s.arrival_s, s.progress_m))
            points.append(SchedulePoint(s.departure_s, s.progress_m))
        sch = TripSchedule(points=tuple(points), corridor_length_m=st[-1].progress_m, forward=True)
        return Ctx(trip_id="SYN", schedule=sch, stops=st, service_date=d, anchor_at=anchor_utc,
                   anchor_progress_m=anchor_p, horizon_end=anchor_utc + timedelta(seconds=TH.stale_after_s),
                   status=status, current_stop_id=stop_id, label=label, **kw)
    d0 = date(2026, 11, 20)
    t0 = service_day_instant(d0, parse_gtfs_time("10:00:00"))

    def s12_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        ok = p.cap_stop_id == "Z2" and p.rule == "R5" and advance(p.env, ctx.horizon_end) > 0.0
        return ok, f"tope={p.cap_stop_id}, regla={p.rule}"
    out.append(("S12 zonas solapadas: paradas a 0 y 60 m (≤ 2τ), ancla en 40 m, IN_TRANSIT_TO",
                synth(d0, [("Z0", 0.0, "10:00:00", "10:00:00"), ("Z1", 60.0, "10:00:30", "10:00:30"),
                           ("Z2", 3000.0, "10:04:00", "10:04:00")], "IN_TRANSIT_TO", "Z0",
                      t0 + timedelta(seconds=20), 40.0, "S12"),
                "tope = primera parada > ancla + τ (Z2)", s12_check))

    def s13_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        expected = 3000.0 / 180.0
        ok = p.cap_stop_id == "T1" and abs(p.env.speed_mps - expected) <= 1e-12
        return ok, f"speed={p.env.speed_mps!r} (esperada {expected!r}), tope={p.cap_stop_id}"
    out.append(("S13 tramo de duración real 0 (T0→T1 misma hora): fusión con el siguiente",
                synth(d0, [("T0", 0.0, "10:00:00", "10:00:00"), ("T1", 1000.0, "10:00:00", "10:00:00"),
                           ("T2", 3000.0, "10:03:00", "10:03:00")], "IN_TRANSIT_TO", "T0", t0, 0.0, "S13"),
                "speed = 3000/180 m/s, tope T1 (no 160 km/h)", s13_check))

    def s14_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        return (p.rule == "R1" and p.coherent is True), f"regla={p.rule}, coherent={p.coherent}"
    out.append(("S14 stop_id repetido (X en 0 y 4000 m), STOPPED_AT X con ancla en 10 m",
                synth(d0, [("X", 0.0, "10:00:00", "10:00:00"), ("Y", 2000.0, "10:02:00", "10:02:00"),
                           ("X", 4000.0, "10:04:00", "10:04:00")], "STOPPED_AT", "X",
                      t0 + timedelta(seconds=5), 10.0, "S14"),
                "ocurrencia más cercana (0 m): R1 coherente", s14_check))
    for label, d, dep, arr, anchor_utc in (
        ("S8 DST adelanto 2027-03-28, tramo 01:50→02:10", date(2027, 3, 28), "01:50:00", "02:10:00",
         datetime(2027, 3, 28, 0, 58, 0, tzinfo=timezone.utc)),
        ("S9 DST atraso 2027-10-31, tramo 01:30→03:30", date(2027, 10, 31), "01:30:00", "03:30:00",
         datetime(2027, 10, 31, 0, 59, 0, tzinfo=timezone.utc)),
    ):
        real = (service_day_instant(d, parse_gtfs_time(arr)) - service_day_instant(d, parse_gtfs_time(dep)))
        rate = 20000.0 / real.total_seconds()
        anchor_p = rate * (anchor_utc - service_day_instant(d, parse_gtfs_time(dep))).total_seconds()
        ctx = synth(d, [("X0", 0.0, dep, dep), ("X1", 20000.0, arr, arr)], "IN_TRANSIT_TO", "X0",
                    anchor_utc, anchor_p, label)
        expected = rate * TH.stale_after_s

        def check(p: Plan, c: Ctx, expected=expected) -> tuple[bool | None, str]:
            a = advance(p.env, c.horizon_end)
            return abs(a - expected) <= 1e-6, f"avance {a!r} m (esperado {expected!r})"
        crit = ("avance = 1000/3 m (333,333 333…) ± 1e-6 m en 180 s reales" if "2027-10-31" in label
                else f"avance = {expected:.6f} ± 1e-6 m en 180 s reales")
        out.append((label, ctx, crit, check))
    # S15: espera en la degradación R8 que cruza el atraso de hora (01:30→03:30 de pared = 10 800 s reales).
    d15 = date(2027, 10, 31)
    arr1 = service_day_instant(d15, parse_gtfs_time("01:30:00"))
    pts15 = [("W0", 0.0, "01:00:00", "01:00:00"), ("W1", 10000.0, "01:30:00", "03:30:00"),
             ("W2", 20000.0, "04:00:00", "04:00:00")]
    anchor15 = arr1 + timedelta(seconds=10700)

    def s15_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        dwell = (ctx.instant(ctx.stops[1].departure_s) - ctx.instant(ctx.stops[1].arrival_s)).total_seconds()
        ok = (dwell == 10800.0 and p.env.dwell_until == anchor15 + timedelta(seconds=100)
              and advance(p.env, anchor15 + timedelta(seconds=90)) == 0.0
              and advance(p.env, anchor15 + timedelta(seconds=180)) > 0.0 and p.dwell_basis == "muestras")
        return ok, (f"espera real={dwell} s (pared 7200), dwell_until=+{(p.env.dwell_until - anchor15).total_seconds() if p.env.dwell_until else None} s, "
                    f"+90 s={advance(p.env, anchor15 + timedelta(seconds=90))!r} m, "
                    f"+180 s={advance(p.env, anchor15 + timedelta(seconds=180)):.3f} m, base={p.dwell_basis}")
    entry15, n15 = zone_entry_from_history(
        tuple(StopInfo(sid, pr, parse_gtfs_time(a), parse_gtfs_time(b), i) for i, (sid, pr, a, b) in enumerate(pts15)),
        TAU_STOP_M, [(arr1, 10001.0), (anchor15, 10003.0)])
    assert entry15 == arr1 and n15 == 2
    out.append(("S15 DST en la ESPERA del fallback: W1 01:30→03:30 del 2027-10-31, estado ausente, entrada por muestras",
                synth(d15, pts15, None, None, anchor15, 10003.0, "S15", zone_entry_at=entry15),
                "espera 10 800 s reales; sin avance a +90 s; avanza a +180 s", s15_check))

    def s15b_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        a = advance(p.env, ctx.horizon_end)
        return (a == 0.0 and p.dwell_basis == "ancla"), f"avance={a!r} m, base={p.dwell_basis}"
    out.append(("S15b igual que S15 sin muestra previa en la zona (reinicio): la espera empieza en el ancla y se DECLARA",
                synth(d15, pts15, None, None, anchor15, 10003.0, "S15b"),
                "retención con dwell_basis=ancla", s15b_check))
    # S16: tres observaciones consecutivas en la misma zona (entrada real e0, luego e0+20 y e0+40).
    pts16 = [("V0", 0.0, "10:00:00", "10:00:00"), ("V1", 5000.0, "10:05:00", "10:07:00"),
             ("V2", 9000.0, "10:10:00", "10:10:00")]
    st16 = tuple(StopInfo(sid, pr, parse_gtfs_time(a), parse_gtfs_time(b), i) for i, (sid, pr, a, b) in enumerate(pts16))
    e0 = service_day_instant(d0, parse_gtfs_time("10:05:30"))
    obs16 = [(e0, 5002.0), (e0 + timedelta(seconds=20), 5001.0), (e0 + timedelta(seconds=40), 5003.0)]
    entry_pair, n_pair = zone_entry_from_history(st16, TAU_STOP_M, obs16[1:])
    entry_all, n_all = zone_entry_from_history(st16, TAU_STOP_M, obs16)

    def s16_check(p: Plan, ctx: Ctx) -> tuple[bool | None, str]:
        full = make_plan_c(TAU_STOP_M, MIN_DWELL_S)(replace(ctx, zone_entry_at=entry_all))
        ok = (entry_pair == obs16[1][0] and n_pair == 2 and entry_all == e0 and n_all == 3
              and p.env.dwell_until == entry_pair + timedelta(seconds=120)
              and full.env.dwell_until == e0 + timedelta(seconds=120)
              and p.env.dwell_until > full.env.dwell_until)
        return ok, (f"par latest+previous → entrada e0+{(entry_pair - e0).total_seconds():g} s, dwell_until "
                    f"e0+{(p.env.dwell_until - e0).total_seconds():g} s; con 3 muestras → entrada e0, dwell_until "
                    f"e0+{(full.env.dwell_until - e0).total_seconds():g} s (el par retiene 20 s MÁS, nunca menos)")
    out.append(("S16 tres observaciones consecutivas en zona (e0, +20, +40), espera programada 120 s, estado ausente",
                synth(d0, pts16, None, None, obs16[2][0], obs16[2][1], "S16", zone_entry_at=entry_pair),
                "el par (latest+previous) prueba la entrada e0+20; la espera nunca termina antes de lo probado",
                s16_check))
    return out


# =========================================================================
# 7. Fixture AC-15 (Python↔TS) y fases
# =========================================================================
def ms(dt: datetime) -> int:
    return int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))


def iso(dt: datetime | None, spec: str = "milliseconds") -> str | None:
    return None if dt is None else dt.astimezone(timezone.utc).isoformat(timespec=spec)


def build_fixture(cases: list[RealCase], synth: list) -> dict:
    plan_a = make_plan_a(TAU_STOP_M)
    plans = [(c.ctx.trip_id, plan_a(c.ctx), c.ctx) for c in cases]
    plans += [(lbl.split(" ")[0], plan_a(ctx), ctx) for lbl, ctx, _, _ in synth]
    items, micro = [], []
    for name, p, ctx in plans:
        e = p.env
        for dt in (e.reference_at, e.dwell_until, p.cap_reached_at):
            assert dt is None or dt.microsecond % 1000 == 0, f"instante no alineado a ms en {name}"
        instants = {e.reference_at, ctx.horizon_end, e.reference_at + timedelta(milliseconds=1),
                    e.reference_at + timedelta(seconds=30), e.reference_at + timedelta(seconds=90)}
        for t in (e.dwell_until, p.cap_reached_at):
            if t is not None:
                instants |= {t - timedelta(milliseconds=1), t, t + timedelta(milliseconds=1)}
        samples = []
        for t in sorted(instants):
            samples.append({"at_ms": ms(t), "progress_m": e.progress_at(t), "phase": phase(p, t)})
        env_json = {"reference_at": iso(e.reference_at), "progress_m_at_reference": e.progress_m_at_reference,
                    "speed_mps": e.speed_mps, "max_progress_m": e.max_progress_m, "horizon_s": e.horizon_s,
                    "dwell_until": iso(e.dwell_until)}
        items.append({"name": name, "envelope": env_json, "hold_reason": p.hold_reason,
                      "cap_kind": p.cap_kind, "cap_reached_at": iso(p.cap_reached_at), "samples": samples})
        if e.speed_mps > 0:  # variante submilisegundo: referencia +0,7 ms serializada con µs
            shifted = replace(e, reference_at=e.reference_at + timedelta(microseconds=700),
                              dwell_until=e.dwell_until + timedelta(microseconds=700) if e.dwell_until else None)
            t = shifted.reference_at + timedelta(seconds=30)
            micro.append({"name": name, "envelope": {**env_json, "reference_at": iso(shifted.reference_at, "microseconds"),
                                                     "dwell_until": iso(shifted.dwell_until, "microseconds")},
                          "samples": [{"at_ms": ms(t), "progress_m": shifted.progress_at(
                              datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=ms(t)))}]})
    return {"ms": items, "micro": micro}


# =========================================================================
# 8. Programa principal
# =========================================================================
def fmt(v):
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, tuple):
        return "(" + ", ".join(fmt(x) for x in v) + ")"
    return str(v)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--fixture-out", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    replay = args.replay.resolve()
    out: dict = {}

    out["validation"] = validate_harness(replay)
    v = out["validation"]
    print("== 0) validación del arnés (ORCHESTRATION_POLICY §3.4) ==")
    print(f"   HEAD={v['head']}  producto idéntico a {BASELINE_COMMIT}: {v['product_equals_baseline']}")
    for item in v["constants"]:
        print(f"   {item['name']:34s} {item['where']}  valor={item['value']}  comprobado={item['checked']}")
    print(f"   identidad del manifiesto: sha256(manifest.json)={v['manifest_sha256']}")
    print(f"   entradas esperadas (7) == manifiesto: True; SHA-256 verificados: {len(v['inputs'])}/7")
    for name, digest in v["inputs"].items():
        print(f"   sha256 {name:28s} {digest}")
    cases, pairs, facts, topo = build_real(replay)
    eq = equivalence_check(cases)
    assert len(cases) == 44 and eq == 44, "la línea base no reproduce producción"
    out["equivalence_full_fields"] = (eq, len(cases))
    print(f"   igualdad COMPLETA de campos publicada == _envelope == B(±∞): {eq}/{len(cases)}")
    reproj = facts.pop("reproj_m")
    facts["reproyeccion_n_max_m"] = (len(reproj), max(reproj))
    facts["estructura_gtfs_44_viajes"] = gtfs_structure(cases, TAU_STOP_M)
    for d_min in (MIN_DWELL_S, 180.0):
        pc = make_plan_c(TAU_STOP_M, d_min)
        changed = [c.ctx.trip_id for c in cases
                   if c.ctx.zone_entry_at is not None and pc(c.ctx).env != pc(replace(c.ctx, zone_entry_at=None)).env]
        facts[f"C(Dmin={d_min:g})_envolventes_que_cambian_con_entrada_por_muestras"] = (len(changed), changed)
    out["facts"] = facts
    print("\n== 1) hechos del corte 1533 ==")
    for k, val in facts.items():
        print(f"   {k}: {fmt(val)}")
    base = baseline_expiry_and_two_coords(cases)
    out["baseline_fr05_fr27"] = base
    for k, val in base.items():
        print(f"   [producción] {k}: {fmt(val)}")

    print("\n== 2) cortes reales: grupo M (hechos de movimiento discriminantes) y coste ==")
    out["real"] = []
    for name, alt in ALTERNATIVES.items():
        m = real_metrics(name, alt, cases, pairs)
        out["real"].append(m)
        print(f"-- {name}: grupo M {sum(m['GROUP_M_pass'].values())}/{len(m['GROUP_M_pass'])} PASS")
        for k, val in m.items():
            if k not in ("alternative", "GROUP_M_pass"):
                print(f"   {k}: {fmt(val)}")
        for k, ok in m["GROUP_M_pass"].items():
            print(f"   {'PASS' if ok else 'FAIL'}  {k}")

    print("\n== 3) sensibilidad (barrido DISCRETO; no prueba invariancia en el continuo) ==")
    out["sensitivity"] = []
    for tau in TAU_SWEEP:
        m = real_metrics(f"A(τ={tau:g})", make_plan_a(tau), cases, pairs, tau)
        row = {"alternative": m["alternative"], "grupo_M": sum(m["GROUP_M_pass"].values()),
               "M1": m["M1_stopped_same_gps_speed_gt0"], "M5b": m["M5b_cross_stop_beyond_tau"],
               "M6_30s": m["M6_19656_advance_30s_60s"][0], "coste": m["COST_stopped1532_departed_pred_eq0"][:2],
               "R7/R8": sum(v for k, v in m["rules"].items() if k.startswith(("R7", "R8")))}
        out["sensitivity"].append(row)
        print(f"   {fmt(row)}")
    for d_min in D_MIN_SWEEP:
        m = real_metrics(f"C(Dmin={d_min:g})", make_plan_c(TAU_STOP_M, d_min), cases, pairs)
        row = {"alternative": m["alternative"], "grupo_M": sum(m["GROUP_M_pass"].values()),
               "grupo_M_con_M2b": m["GROUP_M_si_M2b_sustituye_a_M2a"],
               "M1": m["M1_stopped_same_gps_speed_gt0"], "M2a": m["M2a_R1_pre_salida_STOPPED_AT_speed_gt0"],
               "M2b": m["M2b_R2_avance_hasta_min(salida,horizonte)_gt0"],
               "M3": m["M3_delayed_origin_speed_gt0"], "M4": m["M4_intermediate_stopped_speed_gt0"],
               "guarda": m["M7_guard_transit_incoming_moved_pred_eq0"]}
        out["sensitivity"].append(row)
        print(f"   {fmt(row)}")

    print("\n== 4) grupo S: pruebas sintéticas de reglas (predicados exactos) ==")
    synth = synthetic_cases(cases)
    out["synthetic"] = []
    for label, ctx, criterion, check in synth:
        print(f"-- {label}  [criterio: {criterion}]")
        row = {"case": label, "criterion": criterion, "results": {}}
        key = label.split(" ")[0]
        if key in ("S1", "S2", "S3", "S4", "S5", "S6", "S6b", "S8", "S9"):
            names = list(ALTERNATIVES)
        elif key in ("S5b", "S7", "S10", "S15", "S15b", "S16"):
            names = [C_NAME, A_NAME]
        else:
            names = [A_NAME]
        for name in names:
            p = ALTERNATIVES[name](ctx)
            ok, detail = check(p, ctx)
            if label.startswith(("S5b", "S7", "S10")) and name != A_NAME:
                ok, detail = None, f"no lee el estado del operador; regla={p.rule}"
            row["results"][name] = {"pass": ok, "detail": detail}
            print(f"   {'N/A ' if ok is None else ('PASS' if ok else 'FAIL')}  {name:24s} {detail}")
        out["synthetic"].append(row)

    print("\n== 5) grupo T: camino STALE real (R-STALE) con el prototipo A, 25 en ventana ==")
    out["stale"] = stale_tests(cases)
    for k, val in out["stale"].items():
        print(f"   {k}: {fmt(val) if not isinstance(val, dict) else {kk: fmt(vv) for kk, vv in val.items()}}")

    print("\n== 6) ramas de presentación (motor real) ==")
    out["presentation"] = presentation_tests(cases, topo)
    for k, val in out["presentation"].items():
        print(f"   {k}: {fmt(val)}")

    if args.fixture_out:
        args.fixture_out.write_text(json.dumps(build_fixture(cases, synth), ensure_ascii=False, indent=1) + "\n")
        print(f"\nfixture AC-15 escrito en {args.fixture_out.name}")
    if args.json:
        args.json.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n")
        print(f"JSON escrito en {args.json.name}")


if __name__ == "__main__":
    main()
