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
    entity: list[RawVehiclePositionEntity]


# --- trip_updates.json ------------------------------------------------------


class RawStopTimeArrival(RawModel):
    delay: int
    time: str


class RawStopTimeUpdate(RawModel):
    stop_id: str = Field(alias="stopId")
    arrival: RawStopTimeArrival


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
    entity: list[RawTripUpdateEntity]


# --- alerts.json -------------------------------------------------------------


class RawActivePeriod(RawModel):
    start: str
    # `end` es parte del estándar GTFS-RT Alert.ActivePeriod, pero NO se ha observado
    # en ninguna de las capturas reales de MP-003/MP-004 (82+76+3 alertas revisadas,
    # todas solo con `start`). Se mantiene como Optional[None por defecto] en vez de
    # eliminarlo porque es plausible que Renfe lo emita para una alerta con fecha de
    # fin conocida que no hemos capturado todavía -- pero ningún código debe asumir
    # que está poblado. Hallazgo de la revisión de Codex en MP-005: esta nota faltaba
    # y la ausencia quedaba sin documentar, a diferencia de los demás campos opcionales
    # de este módulo.
    end: Optional[str] = None


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
    entity: list[RawAlertEntity]
