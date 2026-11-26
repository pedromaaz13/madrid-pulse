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


def distribution(values):
    ordered = sorted(values)
    result = {"n": len(ordered)}
    for label, q in (("p50", .50), ("p90", .90), ("p95", .95), ("max", 1)):
        index = (len(ordered) - 1) * q
        result[label] = (ordered[floor(index)] + (index % 1) *
                         (ordered[ceil(index)] - ordered[floor(index)])) if ordered else None
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
