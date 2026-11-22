"""Modelos Pydantic que reflejan EXACTAMENTE el esquema bruto observado en MP-003/MP-004.

Estos modelos no deben contener ningún campo que no se haya observado
realmente en una respuesta HTTP de Renfe (ver docs/research/MP-003-probe-findings.md
y tests/fixtures/). Si Renfe añade un campo nuevo en el futuro, estos modelos
lo ignorarán por defecto (Pydantic ignora extras no declarados) en vez de fallar
-- la ingestión no debe romperse por un campo adicional no crítico, pero
cualquier campo nuevo relevante debe añadirse aquí explícitamente tras verificarlo,
no asumirse.

Nombres de atributo en snake_case; alias en camelCase tal como los devuelve Renfe.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RawModel(BaseModel):
    """Base común: acepta el nombre Python o el alias camelCase de Renfe."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class RawHeader(RawModel):
    gtfs_realtime_version: str = Field(alias="gtfsRealtimeVersion")
    timestamp: str  # epoch segundos como string, tal como lo devuelve Renfe


# --- vehicle_positions.json -------------------------------------------------


class RawPosition(RawModel):
    latitude: float
    longitude: float


class RawTripDescriptor(RawModel):
    trip_id: str = Field(alias="tripId")
    schedule_relationship: Optional[str] = Field(default=None, alias="scheduleRelationship")


class RawVehicleIdentity(RawModel):
    id: str
    label: str


class RawVehiclePosition(RawModel):
    trip: RawTripDescriptor
    # `position` está ausente quedó documentado como caso real en MP-003 (1/403 entidades);
    # el modelo debe aceptar ese caso sin fallar.
    position: Optional[RawPosition] = None
    current_status: Optional[str] = Field(default=None, alias="currentStatus")
    timestamp: str
    stop_id: Optional[str] = Field(default=None, alias="stopId")
    vehicle: RawVehicleIdentity


class RawVehiclePositionEntity(RawModel):
    id: str
    vehicle: RawVehiclePosition


class RawVehiclePositionsFeed(RawModel):
    header: RawHeader
    # Hallazgo real de MP-007 (soak test del colector contra el feed en vivo):
    # una respuesta real omitió la clave `entity` por completo (0 vehículos
    # activos en ese instante), no un array vacío `[]`. Con default
    # obligatorio, Pydantic rechazaba un payload real y válido. `default_factory`
    # trata la ausencia como lista vacía, que es semánticamente correcto.
    entity: list[RawVehiclePositionEntity] = Field(default_factory=list)


# --- trip_updates.json ------------------------------------------------------


class RawStopTimeArrival(RawModel):
    # Hallazgo real de MP-007 (colector contra el feed en vivo): un
    # `stopTimeUpdate.arrival` de un tren de refuerzo ("TUADDED_SPECIAL_...",
    # `scheduleRelationship == "ADDED"`) solo trae `time`, sin `delay`. No se
    # observó en las fixtures más pequeñas de MP-003/MP-004. `delay` no se usa
    # en `normalize.py` (solo el `delay` de nivel `TripUpdate`, ya `Optional`),
    # así que esto solo corrige el modelo para que no rechace un payload real.
    delay: Optional[int] = None
    time: str


class RawStopTimeUpdate(RawModel):
    stop_id: str = Field(alias="stopId")
    # Renfe omite arrival en paradas SKIPPED (captura del 20-11-2026).
    arrival: Optional[RawStopTimeArrival] = None
    schedule_relationship: Optional[str] = Field(
        default=None, alias="scheduleRelationship", exclude_if=lambda value: value is None
    )


class RawTripUpdateVehicle(RawModel):
    wheelchair_accessible: Optional[str] = Field(default=None, alias="wheelchairAccessible")


class RawTripUpdate(RawModel):
    trip: RawTripDescriptor
    # `stopTimeUpdate` y `delay` están ausentes cuando scheduleRelationship == "CANCELED"
    # (observado en MP-004 fixtures) -- nunca asumir que siempre hay delay.
    stop_time_update: Optional[list[RawStopTimeUpdate]] = Field(default=None, alias="stopTimeUpdate")
    vehicle: Optional[RawTripUpdateVehicle] = None
    delay: Optional[int] = None


class RawTripUpdateEntity(RawModel):
    id: str
    trip_update: RawTripUpdate = Field(alias="tripUpdate")


class RawTripUpdatesFeed(RawModel):
    header: RawHeader
    # Ver nota en RawVehiclePositionsFeed.entity -- mismo hallazgo de MP-007,
    # aplicado aquí por consistencia aunque no se observó directamente en
    # trip_updates (ambos feeds comparten la misma estructura de header/entity).
    entity: list[RawTripUpdateEntity] = Field(default_factory=list)


# --- alerts.json -------------------------------------------------------------


class RawActivePeriod(RawModel):
    # El estándar GTFS-RT Alert.ActivePeriod también define `end`, pero NO se ha
    # observado en ninguna de las capturas reales de MP-003/MP-004 (82+76+3 alertas
    # revisadas, todas solo con `start`). A diferencia de `canonical.py` (pensado
    # como esquema interno estable, con margen para campos del estándar todavía no
    # vistos), este módulo `raw` existe específicamente para reflejar la realidad
    # observada sin especular -- ver el docstring del módulo. Por eso `end` NO se
    # declara aquí: añadirlo "por si acaso" habría repetido el mismo error que este
    # módulo existe para evitar (hallazgo de la 2ª revisión de Codex en MP-005; la
    # 1ª ronda lo había dejado como campo opcional con un comentario, lo cual
    # documentaba la contradicción en vez de resolverla). Si una captura futura
    # confirma `end`, se añade aquí entonces, no antes.
    start: str


class RawInformedEntity(RawModel):
    # Observado: solo `routeId`. Renfe no emite stop_id/trip_id/agency_id en
    # informedEntity en los datos capturados hasta ahora.
    route_id: Optional[str] = Field(default=None, alias="routeId")


class RawTranslation(RawModel):
    text: str
    language: str


class RawDescriptionText(RawModel):
    translation: list[RawTranslation]


class RawAlert(RawModel):
    active_period: list[RawActivePeriod] = Field(alias="activePeriod")
    informed_entity: list[RawInformedEntity] = Field(alias="informedEntity")
    description_text: RawDescriptionText = Field(alias="descriptionText")
    # NOTA (hallazgo MP-005, ver docs/DECISIONS.md): el GTFS-RT estándar define
    # `effect`, `cause` y `headerText` para Alert. Ninguno de los tres aparece en
    # las capturas reales de Renfe (MP-003/MP-004) -- no se modelan aquí porque
    # añadirlos sin evidencia sería inventar un campo. Si aparecen en una captura
    # futura, añadirlos aquí tras verificarlo, no antes.


class RawAlertEntity(RawModel):
    id: str
    alert: RawAlert


class RawAlertsFeed(RawModel):
    header: RawHeader
    # Ver nota en RawVehiclePositionsFeed.entity.
    entity: list[RawAlertEntity] = Field(default_factory=list)
