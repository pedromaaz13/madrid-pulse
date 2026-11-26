"""Agregación del replay MP-025b. Las distancias son progreso dirigido en metros."""

from dataclasses import dataclass
from datetime import datetime
from math import ceil, floor

from packages.movement.rendering import ProgressEnvelope


@dataclass
class Anchor:
    vehicle: str
    trip: str
    observed: datetime
    visible: datetime
    status: str | None
    stop: str | None
    digest: str
    run: int
    day: str | None = None
    corridor: bool = False
    projected: float | None = None
    plan: ProgressEnvelope | None = None
    classification: str = "sin_clasificar"
    coherent: bool | None = None
    matched_row: bool = False
    raw_xy: tuple[float, float] | None = None
    declared_progress: float | None = None


def distribution(values):
    ordered = sorted(values)
    result = {"n": len(ordered)}
    for label, q in (("p50", 0.50), ("p90", 0.90), ("p95", 0.95), ("max", 1)):
        index = (len(ordered) - 1) * q
        result[label] = (
            (
                ordered[floor(index)]
                + (index % 1) * (ordered[ceil(index)] - ordered[floor(index)])
            )
            if ordered
            else None
        )
    return result


def exclusion(a, b, horizon):
    if a.trip != b.trip or (a.day and b.day and a.day != b.day):
        return "otra_circulacion"
    seconds = (b.observed - a.observed).total_seconds()
    if seconds <= 0:
        return "empate_reloj"
    if seconds > horizon:
        return "intervalo_largo"
    if not a.matched_row or not b.matched_row:
        return "fila_no_seleccionada"
    if not a.corridor or not b.corridor:
        return "sin_corredor"
    if a.projected is None or b.projected is None:
        return "sin_proyeccion_valida"
    if a.plan is None:
        return "sin_plan_del_ancla"
    return None


def gate(jumps):
    if jumps["n"] < 500:
        return "insuficiente"
    return "cumple_umbral_mediana" if jumps["p50"] <= 200 else "incumple_umbral_mediana"


def first_departure_frame(frames, a, b):
    """Primera confirmación efectiva desde el GPS desplazado, en este segmento."""
    for at, trip, day, stamp, confirmed, shown in frames:
        if at < b.visible:
            continue
        if (trip, day) != (a.trip, a.day):
            break
        if stamp is None or stamp < b.observed or confirmed is None or shown is None:
            continue
        # Si la siguiente ancla efectiva vuelve a la posición inicial, el episodio
        # terminó. Una salida posterior ya no mide la latencia de este GPS.
        if (
            confirmed > a.plan.progress_m_at_reference
            and shown > a.plan.progress_m_at_reference
        ):
            return at
        break
    return None


def movement_opportunity(status, displacement):
    if status in ("IN_TRANSIT_TO", "INCOMING_AT") and displacement >= 100:
        return "M7"
    if status == "STOPPED_AT" and displacement > 0:
        return "salida"
    return None


def jump_strata(a, b):
    """Estratos solapados del mismo conjunto H1. Progreso dirigido, en metros."""
    displacement = b.projected - a.projected
    if abs(displacement) >= 100:
        yield "desplazamiento_absoluto_100m"
    if displacement >= 100:
        yield "avance_dirigido_100m"
    if abs(displacement) < 1:
        yield "desplazamiento_inferior_1m"
    if a.raw_xy is not None and a.raw_xy == b.raw_xy:
        yield "gps_identico"
    if a.status == "IN_TRANSIT_TO":
        yield "in_transit_to"
    if b.plan is not None:
        yield "segundo_aceptado"
        if abs(displacement) >= 100:
            yield "segundo_aceptado_desplazamiento_absoluto_100m"
        if abs(displacement) < 1:
            yield "segundo_aceptado_desplazamiento_inferior_1m"
        if a.status == "IN_TRANSIT_TO":
            yield "segundo_aceptado_in_transit_to"
