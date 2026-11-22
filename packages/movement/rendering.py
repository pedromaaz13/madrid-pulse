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

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from packages.geo import Corridor, point_at_arc_length

from .model import MovementPosition, MovementThresholds, PositionMode
from .schedule import TripSchedule, service_seconds


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
    hold  = dwell_until or reference_at
    t0    = max(reference_at, hold)
    progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0),
                      max_progress_m)
    ```

    `speed_mps = 0.0` es un avance nulo **declarado** (el horario no autoriza
    avanzar dentro del horizonte), no un dato ausente; cuando no hay envolvente
    posible el campo entero es `None`.

    Limitación declarada: tras la espera del propio ancla, la envolvente usa
    una sola tasa media hasta el fin del horizonte, así que no reproduce las
    esperas *intermedias* que caigan dentro de él -- publicarlas exigiría el
    array de puntos futuros que el encargo de MP-019 prohíbe. El horizonte por
    defecto (`stale_after_s`, 180 s) acota ese efecto.
    """

    reference_at: datetime
    progress_m_at_reference: float
    speed_mps: float
    max_progress_m: float
    horizon_s: float
    dwell_until: datetime | None

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


def _envelope(
    *,
    schedule: TripSchedule,
    service_date: date,
    anchor_at: datetime,
    anchor_progress_m: float,
    horizon_end: datetime,
    max_speed_mps: float,
) -> ProgressEnvelope:
    anchor_s = service_seconds(anchor_at, service_date)
    temporal_offset_s = anchor_s - schedule.seconds_at_progress(anchor_progress_m)
    horizon_s = max(0.0, (horizon_end - anchor_at).total_seconds())
    if horizon_s == 0.0:
        return ProgressEnvelope(
            reference_at=anchor_at,
            progress_m_at_reference=anchor_progress_m,
            speed_mps=0.0,
            max_progress_m=anchor_progress_m,
            horizon_s=0.0,
            dwell_until=None,
        )
    horizon_schedule_s = service_seconds(horizon_end, service_date) - temporal_offset_s
    span_m = max(0.0, schedule.progress_at(horizon_schedule_s) - anchor_progress_m)

    # Espera programada del propio ancla: el tren no debe avanzar hasta que el
    # horario reanude. La envolvente la respeta de verdad (retiene el progreso)
    # en vez de publicar una espera y a la vez una velocidad que la contradiga.
    dwell_end_s = schedule.dwell_end_seconds(anchor_progress_m)
    dwell_until = None
    if dwell_end_s is not None:
        candidate = anchor_at + timedelta(seconds=dwell_end_s + temporal_offset_s - anchor_s)
        if anchor_at < candidate < horizon_end:
            dwell_until = candidate
    moving_from = dwell_until or anchor_at
    moving_s = max(0.0, (horizon_end - moving_from).total_seconds())
    speed_mps = min(span_m / moving_s, max_speed_mps) if moving_s > 0 else 0.0
    return ProgressEnvelope(
        reference_at=anchor_at,
        progress_m_at_reference=anchor_progress_m,
        speed_mps=speed_mps,
        max_progress_m=anchor_progress_m + speed_mps * moving_s,
        horizon_s=horizon_s,
        dwell_until=dwell_until,
    )


def _coordinate(corridor: Corridor, schedule: TripSchedule, progress_m: float) -> tuple[float, float]:
    return point_at_arc_length(
        list(corridor.segments[0]), schedule.physical_arc(progress_m)
    )


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
        horizon_s = (
            schedule_only_horizon_s
            if schedule_only_horizon_s is not None
            else thresholds.stale_after_s
        )
        horizon_end = movement.calculated_at + timedelta(seconds=horizon_s)
        envelope = _envelope(
            schedule=schedule,
            service_date=service_date,
            anchor_at=movement.calculated_at,
            anchor_progress_m=movement.progress_m,
            horizon_end=horizon_end,
            max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
        )
        progress_m = envelope.progress_at(display_at)
        latitude, longitude = _coordinate(corridor, schedule, progress_m)
        return RenderedPosition(
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
    valid_until = anchor_at + timedelta(seconds=thresholds.stale_after_s)

    # Congelación: ancla caducada (el motor ya la marcó `stale`) o horizonte
    # agotado. Se congela en el ANCLA, la última posición realmente confirmada,
    # nunca en una extrapolación posterior convertida en hecho.
    if movement.position_mode is PositionMode.STALE or display_at > valid_until:
        latitude, longitude = _coordinate(corridor, schedule, anchor_progress_m)
        return RenderedPosition(
            rendering_method=RenderingMethod.STALE_FROZEN,
            coordinate_space=CoordinateSpace.MAP_MATCHED,
            latitude=latitude,
            longitude=longitude,
            progress_m=anchor_progress_m,
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
        and anchor_at > previous_anchor.observed_at
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

    envelope = _envelope(
        schedule=schedule,
        service_date=service_date,
        anchor_at=anchor_at,
        anchor_progress_m=anchor_progress_m,
        horizon_end=valid_until,
        max_speed_mps=thresholds.max_estimated_speed_kmh / 3.6,
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
