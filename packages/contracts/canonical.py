"""Esquema canónico interno — desacoplado del formato bruto de Renfe.

Principios aplicados (ver AGENTS.md):
- UTC siempre (`timestamptz`); nunca se asume zona horaria local aquí.
- Un dato ausente se representa como `None`, nunca como `0` o cadena vacía.
- `nucleo_prefix` se deriva SIEMPRE de `source_trip_id`/`source_route_id` (ADR-0008/
  DEC-017), nunca se acepta como entrada independiente que pudiera desincronizarse.
- `speed_kmh` y `bearing` existen en el modelo porque el estándar GTFS-RT los define,
  pero están documentados como no observados en los feeds reales de Renfe capturados
  hasta ahora (MP-003/MP-004) — por eso son `Optional[float] = None` y no campos
  obligatorios; no inventar un valor cuando falten.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, computed_field, field_validator

from packages.contracts.nucleo import nucleo_name, nucleo_prefix


def epoch_to_utc(value: str) -> datetime:
    """Convierte un timestamp epoch (string, como lo da Renfe) a datetime UTC."""
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def require_utc(value: datetime) -> datetime:
    """Rechaza cualquier datetime que no sea explícitamente UTC-aware.

    El docstring del módulo promete "UTC siempre"; sin este validador, Pydantic
    aceptaría silenciosamente un `datetime` naive o con un offset distinto de UTC
    pasado directamente al modelo (fuera de las funciones de `normalize.py`, que
    sí usan siempre `epoch_to_utc`). Hallazgo de la revisión de Codex en MP-005:
    el tipo `datetime` por sí solo no garantiza la invariante declarada.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("datetime naive no permitido: todos los timestamps deben ser UTC-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(
            f"datetime con offset distinto de UTC no permitido (offset={value.utcoffset()})"
        )
    return value


def require_utc_or_none(value: Optional[datetime]) -> Optional[datetime]:
    """Como `require_utc`, pero deja pasar `None` para campos opcionales."""
    if value is None:
        return None
    return require_utc(value)


def canonical_payload_hash(raw_entity: dict) -> str:
    """Hash canónico (sha256) de una entidad bruta, para deduplicación (docs/DATA_MODEL.md).

    Usa claves ordenadas para que el mismo contenido produzca siempre el mismo hash
    independientemente del orden de las claves en el JSON de origen.
    """
    canonical_json = json.dumps(raw_entity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class VehiclePositionObservation(BaseModel):
    source_vehicle_id: str
    source_trip_id: str
    observed_at: datetime  # UTC, del timestamp de la entidad vehicle
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_status: Optional[str] = None
    current_stop_id: Optional[str] = None  # raw passthrough; resolver a stop_sequence es MP-010
    speed_kmh: Optional[float] = None  # no observado en feeds reales hasta ahora (ver docstring)
    bearing: Optional[float] = None  # ídem
    raw_vehicle_label: str
    payload_hash: str

    _validate_observed_at = field_validator("observed_at", mode="after")(require_utc)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nucleo_prefix(self) -> str:
        return nucleo_prefix(self.source_trip_id)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nucleo_name(self) -> str:
        return nucleo_name(self.nucleo_prefix)

    @property
    def has_position(self) -> bool:
        return self.latitude is not None and self.longitude is not None


class TripUpdateObservation(BaseModel):
    source_trip_id: str
    observed_at: datetime  # UTC, del header del feed (la entidad no lleva timestamp propio)
    schedule_relationship: Optional[str] = None
    delay_seconds: Optional[int] = None  # None, nunca 0, cuando no hay dato (ver DATA_QUALITY.md)
    delay_coverage: Literal["reported", "missing"]
    next_stop_id: Optional[str] = None
    payload_hash: str

    _validate_observed_at = field_validator("observed_at", mode="after")(require_utc)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nucleo_prefix(self) -> str:
        return nucleo_prefix(self.source_trip_id)


class ServiceAlert(BaseModel):
    source_alert_id: str
    active_period_start: datetime  # UTC
    active_period_end: Optional[datetime] = None
    affected_route_ids: list[str]
    description_text: str
    description_language: str
    payload_hash: str

    _validate_active_period_start = field_validator("active_period_start", mode="after")(
        require_utc
    )
    _validate_active_period_end = field_validator("active_period_end", mode="after")(
        require_utc_or_none
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nucleo_prefixes(self) -> set[str]:
        """Núcleos afectados, derivados de cada route_id informado.

        Una sola alerta puede listar rutas de varios núcleos en teoría; en los
        datos observados en MP-003/MP-004 cada alerta afecta a un único núcleo.
        """
        return {nucleo_prefix(route_id) for route_id in self.affected_route_ids}


class FeedHealth(BaseModel):
    feed_name: Literal["vehicle_positions", "trip_updates", "alerts"]
    source_timestamp: datetime  # UTC, del header del feed
    entity_count: int

    _validate_source_timestamp = field_validator("source_timestamp", mode="after")(require_utc)
