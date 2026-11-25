"""Capa de presentación `rendered` del anexo de Hito 3 — ADR-0014.

Tercera coordenada del contrato, distinta de `raw` (lo que publicó Renfe) y de
`map_matched` (la proyección sobre el patrón verificado). Aquí no se decide qué
observación es utilizable, ni se proyecta, ni se filtra un salto del feed: eso
lo hace `MovementEngine` (MP-012) y es su única implementación. Este módulo
**traduce** su resultado en lo que un cliente necesita para dibujar movimiento
continuo sin fabricar observaciones:

- una `ProgressEnvelope` compacta (regla única, acotada y monótona), no un array
  de puntos futuros;
- `rendering_method` con los seis valores exigidos por
  `docs/hitos/hito-03/ANEXO-CRITICO-POSICION-Y-RELOJ.md`;
- los instantes separados (`calculated_at`, `display_at`, `valid_until`,
  `last_confirmed_at`) y la edad real del ancla.

Ningún frame de cliente vuelve nunca a esta capa: es de solo lectura y no se
archiva como observación de origen.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from packages.geo import Corridor, point_at_arc_length

from .model import MovementPosition, MovementThresholds, PositionMode
from .schedule import TripSchedule, service_day_instant


class RenderingMethod(StrEnum):
    ANCHOR = "anchor"
    INTERPOLATED_BETWEEN_KNOWN_ANCHORS = "interpolated_between_known_anchors"
    EXTRAPOLATED_FROM_LAST_ANCHOR = "extrapolated_from_last_anchor"
    SCHEDULE_ONLY = "schedule_only"
    STALE_FROZEN = "stale_frozen"
    UNLOCATED = "unlocated"


class CoordinateSpace(StrEnum):
    """Espacio al que pertenece la coordenada publicada en `rendered`.

    `RAW` es deliberadamente posible: cuando el patrón no tiene corredor
    validado (72 de 103 patrones siguen `pending` tras MP-018) la única
    coordenada defendible es el punto bruto etiquetado como tal. Nunca se
    proyecta sobre un corredor ajeno para que "quede bonito".
    """

    MAP_MATCHED = "map_matched"
    RAW = "raw"
    SCHEDULE = "schedule"


@dataclass(frozen=True)
class AnchorSample:
    """Ancla real (observación map-matcheada) para el caso de replay/búfer."""

    observed_at: datetime
    progress_m: float


@dataclass(frozen=True)
class ProgressEnvelope:
    """Plan de progreso compacto: una sola expresión, acotada y monótona.

    Expresión única, con una sola discontinuidad declarada (la espera):

    ```text
    t0 = dwell_until or reference_at
    progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0),
                      max_progress_m)
    ```

    `speed_mps = 0.0` es un avance nulo **declarado** (el horario no autoriza
    avanzar dentro del horizonte), no un dato ausente; cuando no hay envolvente
    posible el campo entero es `None`.

    """

    reference_at: datetime
    progress_m_at_reference: float
    speed_mps: float
    max_progress_m: float
    horizon_s: float
    dwell_until: datetime | None
    hold_reason: str | None = None
    cap_stop_id: str | None = None
    cap_kind: str | None = None
    cap_reached_at: datetime | None = None
    envelope_id: str | None = None
    coherent: bool | None = None
    dwell_basis: str | None = None

    def phase(self, at: datetime) -> str:
        if self.speed_mps == 0 or at < self.moving_from:
            return f"hold:{self.hold_reason}"
        if self.cap_reached_at is not None and at >= self.cap_reached_at:
            return f"cap:{self.cap_kind}"
        return "moving"

    def __post_init__(self) -> None:
        if self.speed_mps < 0:
            raise ValueError("la envolvente nunca retrocede: speed_mps >= 0")
        if self.horizon_s < 0:
            raise ValueError("horizon_s no puede ser negativo")
        if self.max_progress_m < self.progress_m_at_reference:
            raise ValueError("max_progress_m no puede quedar por detrás del ancla")
        if self.dwell_until is not None and self.dwell_until < self.reference_at:
            raise ValueError("dwell_until no puede ser anterior al ancla")

    @property
    def moving_from(self) -> datetime:
        """Instante desde el que la envolvente autoriza avanzar."""
        return self.dwell_until if self.dwell_until is not None else self.reference_at

    def progress_at(self, at: datetime) -> float:
        elapsed = max(0.0, (at - self.moving_from).total_seconds())
        return min(
            self.progress_m_at_reference + self.speed_mps * elapsed, self.max_progress_m
        )


@dataclass(frozen=True)
class RenderedPosition:
    """Coordenada de presentación con procedencia completa.

    `geometry_version` se publica **solo** cuando la coordenada vive en
    `map_matched`; para un fallback bruto se usa
    `geometry_candidate_version`, que es la versión de la geometría
    candidata/contextual del patrón y no acredita que haya habido proyección
    (nota no bloqueante que MP-018 dejó abierta para MP-019).
    """

    rendering_method: RenderingMethod
    coordinate_space: CoordinateSpace | None
    latitude: float | None
    longitude: float | None
    progress_m: float | None
    pattern_id: str | None
    geometry_version: str | None
    geometry_candidate_version: str | None
    confidence_index: float | None
    calculated_at: datetime
    display_at: datetime
    valid_until: datetime | None
    last_confirmed_at: datetime | None
    anchor_observed_at: datetime | None
    anchor_age_s: float | None
    anchor_distance_from_raw_m: float | None
    progress_envelope: ProgressEnvelope | None
    reason: str | None
    frozen_basis: str | None = None
    last_confirmed_progress_m: float | None = None
    dwell_basis: str | None = None
    stop_state: dict | None = None

    def __post_init__(self) -> None:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitud y longitud deben estar ambas presentes o ambas ausentes")
        if self.rendering_method is RenderingMethod.UNLOCATED and self.latitude is not None:
            raise ValueError("unlocated no puede publicar coordenada")
        if self.coordinate_space is not CoordinateSpace.MAP_MATCHED and self.geometry_version:
            raise ValueError(
                "geometry_version solo es lícito con coordenada map_matched; "
                "usar geometry_candidate_version"
            )
        if self.anchor_age_s is not None and self.anchor_age_s < 0:
            raise ValueError("anchor_age_s no puede ser negativo")


def _millisecond(value: datetime) -> datetime:
    return value.replace(microsecond=value.microsecond // 1000 * 1000)


def _envelope(
    *,
    schedule: TripSchedule,
    service_date: date,
    anchor_at: datetime,
    anchor_progress_m: float,
    horizon_end: datetime,
    max_speed_mps: float,
    thresholds: MovementThresholds = MovementThresholds(),
    status: str | None = None,
    stop_id: str | None = None,
    previous_anchor: AnchorSample | None = None,
    canceled: bool = False,
    identity: tuple = (),
) -> ProgressEnvelope:
    reference = _millisecond(anchor_at)
    end = _millisecond(horizon_end)
    horizon_s = (end - reference).total_seconds()
    a = anchor_progress_m
    status = status.upper() if status else None
    stops = schedule.stops
    tau = thresholds.stop_zone_radius_m

    def nearest(progress, candidates):
        return min(
            candidates, key=lambda s: (abs(s.progress_m - progress), s.stop_sequence), default=None
        )

    def zone(progress):
        return nearest(progress, (s for s in stops if abs(s.progress_m - progress) <= tau))

    def instant(seconds):
        return service_day_instant(service_date, seconds)

    declared = nearest(a, (s for s in stops if s.stop_id == stop_id))
    coherent = None
    if not canceled and stop_id and status in {"STOPPED_AT", "INCOMING_AT", "IN_TRANSIT_TO"}:
        coherent = declared is not None
        if declared is not None:
            gap = declared.progress_m - a
            coherent = not (
                (status == "STOPPED_AT" and abs(gap) > tau)
                or (status == "INCOMING_AT" and gap < -tau)
            )

    basis = None
    key = (
        identity,
        anchor_at.isoformat(),
        a,
        status,
        stop_id,
        service_date.isoformat(),
        asdict(thresholds),
        canceled,
        asdict(previous_anchor) if previous_anchor else None,
    )
    envelope_id = hashlib.sha256(json.dumps(key, default=str, sort_keys=True).encode()).hexdigest()

    def hold(reason):
        return ProgressEnvelope(
            reference,
            a,
            0.0,
            a,
            horizon_s,
            None,
            reason,
            envelope_id=envelope_id,
            coherent=coherent,
            dwell_basis=basis,
        )

    if canceled:
        return hold("trip_canceled")
    if coherent and status == "STOPPED_AT":
        return hold("operator_stopped_at")
    if coherent and status == "INCOMING_AT" and abs(declared.progress_m - a) <= tau:
        return hold("operator_incoming_at")
    if not stops:
        return hold("schedule_incoherent")
    if a < stops[0].progress_m - tau:
        return hold("outside_schedule_extent")
    if a >= stops[-1].progress_m - tau:
        return hold("terminal")

    start = reference
    reason = None
    departure = instant(stops[0].departure_s)
    if reference < departure:
        start, reason = departure, "before_first_departure"
    elif not coherent and (station := zone(a)) is not None:
        entry = reference
        basis = "ancla"
        if (
            previous_anchor
            and previous_anchor.observed_at < anchor_at
            and zone(previous_anchor.progress_m) == station
        ):
            entry = _millisecond(previous_anchor.observed_at)
            basis = "muestras"
        dwell = (instant(station.departure_s) - instant(station.arrival_s)).total_seconds()
        until = _millisecond(entry + timedelta(seconds=max(thresholds.min_dwell_s, dwell)))
        if until > reference:
            start, reason = until, "schedule_stop_zone"
    if start >= end:
        return hold(reason or "horizon_exhausted")

    j = next(i for i, stop in enumerate(stops) if stop.progress_m > a + tau)
    prev, cap = stops[j - 1], stops[j]
    for target in stops[j:]:
        duration = (instant(target.arrival_s) - instant(prev.departure_s)).total_seconds()
        distance = target.progress_m - prev.progress_m
        if duration > 0 and distance > 0:
            speed = min(max_speed_mps, distance / duration)
            break
    else:
        return hold("schedule_incoherent")
    reach = min(cap.progress_m, a + speed * (end - start).total_seconds())
    kind = "stop" if reach == cap.progress_m else "horizon"
    reached = (
        start + timedelta(milliseconds=math.ceil(1000 * (reach - a) / speed))
        if kind == "stop"
        else end
    )
    return ProgressEnvelope(
        reference,
        a,
        speed,
        reach,
        horizon_s,
        start if reason else None,
        reason,
        cap.stop_id,
        kind,
        reached,
        envelope_id,
        coherent,
        basis,
    )


def _coordinate(
    corridor: Corridor, schedule: TripSchedule, progress_m: float
) -> tuple[float, float]:
    return point_at_arc_length(list(corridor.segments[0]), schedule.physical_arc(progress_m))


def render_from_movement(
    movement: MovementPosition,
    *,
    schedule: TripSchedule,
    corridor: Corridor,
    service_date: date,
    display_at: datetime,
    pattern_id: str | None,
    geometry_version: str | None,
    thresholds: MovementThresholds = MovementThresholds(),
    previous_anchor: AnchorSample | None = None,
    anchor_distance_from_raw_m: float | None = None,
    status: str | None = None,
    stop_id: str | None = None,
    canceled: bool = False,
    identity: tuple = (),
    versions_match: bool = True,
    zone_sample: AnchorSample | None = None,
    schedule_only_horizon_s: float | None = None,
) -> RenderedPosition:
    """Traduce un `MovementPosition` del motor a la coordenada de presentación.

    `display_at` es el instante que el cliente va a dibujar; puede ser anterior
    a `movement.calculated_at` (replay con retraso de presentación declarado) o
    posterior (el cliente avanza con la envolvente entre dos sondeos).
    """
    anchor_at = movement.observed_at
    anchor_progress_m = movement.anchor_progress_m

    if (
        movement.position_mode is PositionMode.SCHEDULED
        or anchor_at is None
        or anchor_progress_m is None
    ):
        if canceled:
            return render_unlocated(calculated_at=movement.calculated_at, display_at=display_at,
                                    pattern_id=pattern_id, geometry_candidate_version=geometry_version,
                                    reason="trip_canceled")
        horizon_s = (
            schedule_only_horizon_s
            if schedule_only_horizon_s is not None
            else thresholds.stale_after_s
        )
        horizon_end = _millisecond(movement.calculated_at + timedelta(seconds=horizon_s))
        envelope = _envelope(
            schedule=schedule,
            service_date=service_date,
            thresholds=thresholds,
            identity=(movement.trip_id, geometry_version, *identity),
            anchor_at=movement.calculated_at,
            anchor_progress_m=movement.progress_m,
            horizon_end=horizon_end,
            max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
        )
        progress_m = envelope.progress_at(display_at)
        latitude, longitude = _coordinate(corridor, schedule, progress_m)
        return RenderedPosition(
            stop_state=dict(source="schedule", operator_status=None, operator_stop_id=None, observation_observed_at=None, coherent=None),
            dwell_basis=envelope.dwell_basis,
            rendering_method=RenderingMethod.SCHEDULE_ONLY,
            coordinate_space=CoordinateSpace.SCHEDULE,
            latitude=latitude,
            longitude=longitude,
            progress_m=progress_m,
            pattern_id=pattern_id,
            geometry_version=None,
            geometry_candidate_version=geometry_version,
            confidence_index=movement.confidence,
            calculated_at=movement.calculated_at,
            display_at=display_at,
            valid_until=horizon_end,
            last_confirmed_at=None,
            anchor_observed_at=movement.observed_at,
            anchor_age_s=movement.age_s,
            anchor_distance_from_raw_m=None,
            progress_envelope=envelope,
            reason="sin observación utilizable: posición derivada solo del horario",
        )

    anchor_age_s = max(0.0, (display_at - anchor_at).total_seconds())
    valid_until = _millisecond(anchor_at + timedelta(seconds=thresholds.stale_after_s))

    envelope = _envelope(
        schedule=schedule, thresholds=thresholds, previous_anchor=zone_sample,
        status=status, stop_id=stop_id, canceled=canceled,
        identity=(movement.trip_id, geometry_version, *identity),
        service_date=service_date,
        anchor_at=anchor_at,
        anchor_progress_m=anchor_progress_m,
        horizon_end=valid_until,
        max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
    )
    stop_state = dict(source="trip_update" if canceled else "operator" if envelope.coherent else "schedule",
                      operator_status=status, operator_stop_id=stop_id,
                      observation_observed_at=anchor_at, coherent=envelope.coherent)
    if display_at > valid_until:
        frozen = envelope.progress_at(valid_until) if versions_match and schedule.stops else anchor_progress_m
        basis = "authorized_envelope_end" if versions_match and schedule.stops else "anchor_version_changed"
        latitude, longitude = _coordinate(corridor, schedule, frozen)
        return RenderedPosition(
            rendering_method=RenderingMethod.STALE_FROZEN,
            coordinate_space=CoordinateSpace.MAP_MATCHED,
            latitude=latitude,
            longitude=longitude,
            progress_m=frozen,
            frozen_basis=basis,
            last_confirmed_progress_m=anchor_progress_m,
            stop_state=stop_state,
            dwell_basis=envelope.dwell_basis,
            pattern_id=pattern_id,
            geometry_version=geometry_version,
            geometry_candidate_version=None,
            confidence_index=movement.confidence,
            calculated_at=movement.calculated_at,
            display_at=display_at,
            valid_until=None,
            last_confirmed_at=anchor_at,
            anchor_observed_at=anchor_at,
            anchor_age_s=anchor_age_s,
            anchor_distance_from_raw_m=anchor_distance_from_raw_m,
            progress_envelope=None,
            reason="ancla fuera de horizonte de confianza: congelada, sin avance",
        )

    # Replay/búfer: `display_at` cae entre dos anclas reales. Es el único caso
    # en que la etiqueta `interpolated` es cierta.
    if (
        previous_anchor is not None
        and previous_anchor.observed_at < display_at < anchor_at
        and (anchor_at - previous_anchor.observed_at).total_seconds() <= thresholds.stale_after_s
    ):
        span_s = (anchor_at - previous_anchor.observed_at).total_seconds()
        fraction = (display_at - previous_anchor.observed_at).total_seconds() / span_s
        progress_m = previous_anchor.progress_m + fraction * (
            anchor_progress_m - previous_anchor.progress_m
        )
        latitude, longitude = _coordinate(corridor, schedule, progress_m)
        return RenderedPosition(
            rendering_method=RenderingMethod.INTERPOLATED_BETWEEN_KNOWN_ANCHORS,
            coordinate_space=CoordinateSpace.MAP_MATCHED,
            latitude=latitude,
            longitude=longitude,
            progress_m=progress_m,
            pattern_id=pattern_id,
            geometry_version=geometry_version,
            geometry_candidate_version=None,
            confidence_index=movement.confidence,
            calculated_at=movement.calculated_at,
            display_at=display_at,
            valid_until=valid_until,
            last_confirmed_at=anchor_at,
            anchor_observed_at=anchor_at,
            anchor_age_s=0.0,
            anchor_distance_from_raw_m=anchor_distance_from_raw_m,
            progress_envelope=None,
            reason="retraso de presentación declarado: entre dos anclas reales",
        )

    progress_m = envelope.progress_at(display_at)
    advanced = progress_m > anchor_progress_m
    method = (
        RenderingMethod.EXTRAPOLATED_FROM_LAST_ANCHOR
        if advanced
        else RenderingMethod.ANCHOR
    )
    if advanced:
        reason = "sin ancla futura: avance estimado desde la última ancla"
    elif envelope.dwell_until is not None:
        reason = "espera programada en parada: la coordenada sigue siendo el ancla"
    else:
        reason = "el horario no autoriza avance todavía: la coordenada es el ancla"
    latitude, longitude = _coordinate(corridor, schedule, progress_m)
    return RenderedPosition(
        rendering_method=method,
        stop_state=stop_state,
        dwell_basis=envelope.dwell_basis,
        last_confirmed_progress_m=anchor_progress_m,
        coordinate_space=CoordinateSpace.MAP_MATCHED,
        latitude=latitude,
        longitude=longitude,
        progress_m=progress_m,
        pattern_id=pattern_id,
        geometry_version=geometry_version,
        geometry_candidate_version=None,
        confidence_index=movement.confidence,
        calculated_at=movement.calculated_at,
        display_at=display_at,
        valid_until=valid_until,
        last_confirmed_at=anchor_at,
        anchor_observed_at=anchor_at,
        anchor_age_s=anchor_age_s,
        anchor_distance_from_raw_m=anchor_distance_from_raw_m,
        progress_envelope=envelope,
        reason=reason,
    )


def render_raw_anchor(
    *,
    raw_lat: float,
    raw_lon: float,
    observed_at: datetime,
    calculated_at: datetime,
    display_at: datetime,
    pattern_id: str | None,
    geometry_candidate_version: str | None,
    reason: str,
    thresholds: MovementThresholds = MovementThresholds(),
) -> RenderedPosition:
    """Punto bruto etiquetado: patrón sin corredor validado, sin proyección.

    No se construye envolvente: sin geometría validada no existe longitud de
    arco sobre la que avanzar, y una recta entre estaciones sería un trazado
    inventado. El punto se congela cuando supera `stale_after_s`.
    """
    age_s = max(0.0, (display_at - observed_at).total_seconds())
    frozen = age_s > thresholds.stale_after_s
    return RenderedPosition(
        rendering_method=(
            RenderingMethod.STALE_FROZEN if frozen else RenderingMethod.ANCHOR
        ),
        coordinate_space=CoordinateSpace.RAW,
        frozen_basis="anchor_version_changed" if frozen else None,
        latitude=raw_lat,
        longitude=raw_lon,
        progress_m=None,
        pattern_id=pattern_id,
        geometry_version=None,
        geometry_candidate_version=geometry_candidate_version,
        confidence_index=None,
        calculated_at=calculated_at,
        display_at=display_at,
        valid_until=None,
        last_confirmed_at=observed_at,
        anchor_observed_at=observed_at,
        anchor_age_s=age_s,
        anchor_distance_from_raw_m=None,
        progress_envelope=None,
        reason=reason,
    )


def render_unlocated(
    *,
    calculated_at: datetime,
    display_at: datetime,
    pattern_id: str | None,
    geometry_candidate_version: str | None,
    reason: str,
    observed_at: datetime | None = None,
) -> RenderedPosition:
    """Sin coordenada defendible: el tren sigue en lista/tablero, no en el mapa."""
    return RenderedPosition(
        rendering_method=RenderingMethod.UNLOCATED,
        coordinate_space=None,
        latitude=None,
        longitude=None,
        progress_m=None,
        pattern_id=pattern_id,
        geometry_version=None,
        geometry_candidate_version=geometry_candidate_version,
        confidence_index=None,
        calculated_at=calculated_at,
        display_at=display_at,
        valid_until=None,
        last_confirmed_at=None,
        anchor_observed_at=observed_at,
        anchor_age_s=(
            max(0.0, (display_at - observed_at).total_seconds())
            if observed_at is not None
            else None
        ),
        anchor_distance_from_raw_m=None,
        progress_envelope=None,
        reason=reason,
    )
