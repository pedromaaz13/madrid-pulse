"""Modelos de respuesta — conformes a docs/DATA_CONTRACTS.md."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_serializer


class PositionOut(BaseModel):
    lat: float
    lon: float
    mode: Literal["observed", "estimated", "stale", "scheduled"]
    confidence: float


class DelayOut(BaseModel):
    seconds: int | None
    coverage: Literal["reported", "missing"]


class ObservationOut(BaseModel):
    reported_at: datetime | None
    received_at: datetime | None
    age_s: float | None


class QualityOut(BaseModel):
    stale: bool
    flags: list[str]


class VehicleOut(BaseModel):
    vehicle_id: str
    trip_id: str
    route_id: str | None
    """``None`` cuando el ``trip_id`` en vivo no resuelve contra el GTFS
    estático cargado (p. ej. una fixture reducida sin ese trip) -- nunca se
    inventa un valor."""
    line: str | None
    position: PositionOut | None
    """``None`` cuando no hay suficiente información (route_id sin resolver)
    para map-matchear o calcular horario; la fila se devuelve igualmente con
    los datos crudos que sí se conocen, no se oculta."""
    delay: DelayOut
    observation: ObservationOut
    quality: QualityOut
    circulation_status: Literal["active", "expired", "unresolved"]
    """Hallazgo MP-017: distinto de `quality.stale` (que mide antigüedad del
    GPS). `active` = el `service_id` del viaje está programado para la fecha
    de servicio actual (`packages.gtfs.catalog.scheduled_service_ids_for_date`).
    `expired` = el viaje resuelve contra el GTFS pero su `service_id` no está
    programado hoy (circulación de un día de servicio anterior que nunca se
    reasignó). `unresolved` = `route_id` no resuelto, no se puede determinar
    (nunca se fabrica `active`/`expired` sin resolución real)."""


class FeedHealthOut(BaseModel):
    feed_name: str
    status: Literal["ok", "stale", "error", "unknown"]
    source_timestamp: datetime | None
    data_age_s: float | None
    poll_age_s: float | None
    unchanged_for_s: float | None
    entities: int | None
    rejected: int
    reason: Literal["no_ingestion_at_or_before_clock", "source_timestamp_in_future"] | None = None


GtfsStatus = Literal["valid", "expiring", "expired", "not_yet_valid"]
GtfsStatusReason = Literal[
    "gtfs_expiry_approaching", "gtfs_validity_ended", "gtfs_validity_not_started"
]


class GtfsValidityOut(BaseModel):
    gtfs_status: GtfsStatus
    gtfs_status_reason: GtfsStatusReason | None


class HealthOut(BaseModel):
    feeds: list[FeedHealthOut]
    mode: Literal["live", "replay"] | None = None
    gtfs_version: str | None = None
    gtfs_valid_from: str | None = None
    gtfs_valid_until: str | None = None
    gtfs_status: GtfsStatus | None = None
    gtfs_status_reason: GtfsStatusReason | None = None


class CoordinateOut(BaseModel):
    lat: float
    lon: float


class LineStationOut(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    distance_along_m: float


class LineGeometryOut(BaseModel):
    """Corredor OSM real: cada elemento de ``segments`` es continuo.

    Los tramos nunca deben concatenarse en el cliente, porque una separación
    entre ellos representa un hueco real de la geometría cargada.
    """

    segments: list[list[CoordinateOut]]
    stations: list[LineStationOut]


class LineOut(BaseModel):
    line_id: str
    network_id: str
    route_ids: list[str]
    geometry: LineGeometryOut | None


class StationOut(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float


# --------------------------------------------------------------------------
# MP-019 (ADR-0014): catálogo cacheable, snapshot operativo y tablero.
# Todo lo siguiente es aditivo sobre `/api/v1`: ningún campo existente cambia
# de nombre, tipo ni significado, así que no se rompe compatibilidad ni hace
# falta `/api/v2` (ADR-0005).
# --------------------------------------------------------------------------

SNAPSHOT_SCHEMA_VERSION = "1.1"
CATALOG_SCHEMA_VERSION = "1.1"
BOARD_SCHEMA_VERSION = "1.0"

RenderingMethodLiteral = Literal[
    "anchor",
    "interpolated_between_known_anchors",
    "extrapolated_from_last_anchor",
    "schedule_only",
    "stale_frozen",
    "unlocated",
]


class CatalogGeometryOut(BaseModel):
    """Geometría física publicada **una sola vez** y referenciada por patrón.

    Dos patrones (o dos líneas con tramo compartido) que usan la misma relación
    OSM comparten esta entrada: la identidad del tramo está separada del color
    comercial y de los offsets de visualización, como exige
    `docs/hitos/hito-03/AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md`.
    """

    geometry_version: str
    relation_id: int
    attribution: str
    source_captured_at: str | None
    length_m: float
    segments: list[list[CoordinateOut]]
    """Tramos continuos reales: nunca se concatenan atravesando un hueco."""


class PatternGeometryOut(BaseModel):
    status: Literal["validated", "partial", "pending"]
    reason: str
    geometry_version: str | None
    """``None`` salvo que exista una fuente real asociada al patrón. En estado
    `partial` identifica la geometría **candidata**, que no autoriza a afirmar
    que hubo map-matching."""
    relation_id: int | None
    max_stop_distance_m: float | None
    source_captured_at: str | None
    attribution: str | None
    can_map_match: bool


class PatternStationOut(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    stop_sequence: int
    distance_along_m: float | None
    """``None`` cuando el patrón no tiene corredor validado: no hay longitud de
    arco real que publicar y no se estima una."""


class PatternOut(BaseModel):
    pattern_id: str
    route_id: str
    direction_key: str
    origin_stop_id: str
    destination_stop_id: str
    stop_ids: list[str]
    trip_count: int
    geometry: PatternGeometryOut
    stations: list[PatternStationOut]


class CatalogLineOut(BaseModel):
    line_id: str
    network_id: str | None
    operator: str
    route_ids: list[str]
    patterns: list[PatternOut]


class CoverageSummaryOut(BaseModel):
    total_patterns: int
    validated: int
    partial: int
    pending: int


class CatalogOut(GtfsValidityOut):
    """Catálogo cacheable con metadatos de vigencia GTFS. Se sirve con
    `ETag`/`304` y no incluye ningún dato operativo del colector."""

    schema_version: str = CATALOG_SCHEMA_VERSION
    catalog_version: str
    gtfs_version: str
    geometry_catalog_version: str
    gtfs_valid_from: str
    gtfs_valid_until: str
    mode: Literal["live", "replay"]
    operator: str
    lines: list[CatalogLineOut]
    stations: list[StationOut]
    geometries: list[CatalogGeometryOut]
    coverage: CoverageSummaryOut


class CatalogRefOut(BaseModel):
    catalog_version: str
    gtfs_version: str
    geometry_catalog_version: str


class RawPositionOut(BaseModel):
    """Lo que publicó la fuente, sin retoque. ``lat``/``lon`` ``None`` cuando la
    entidad no traía posición -- nunca ``(0, 0)``."""

    lat: float | None
    lon: float | None
    source: str
    gps_observed_at: datetime
    payload_hash: str


class MapMatchedOut(BaseModel):
    """Proyección real sobre el patrón verificado. Solo existe cuando
    ``resolution == "map_matched"``; si no, el bloque entero es ``null``."""

    resolution: Literal["map_matched"]
    lat: float
    lon: float
    progress_m: float
    distance_from_raw_m: float
    pattern_id: str
    geometry_version: str


class ProgressEnvelopeOut(BaseModel):
    """Plan de progreso compacto, válido para `reference_at <= t <= rendered.valid_until`:

    ```text
    t0 = dwell_until or reference_at
    progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0),
                      max_progress_m)
    ```

    `dwell_until` es una espera programada real: hasta ese instante el progreso
    se mantiene en el del ancla. `speed_mps == 0` es avance nulo declarado (el
    horario no autoriza avanzar en el horizonte), no dato ausente. El cliente
    convierte el progreso en coordenada sobre la longitud de arco del patrón
    que ya tiene del catálogo; nunca interpola lat/lon en línea recta entre
    estaciones. La fase es hold:<hold_reason> con velocidad cero o antes de
    t0, cap:<cap_kind> desde cap_reached_at y moving en otro caso.
    """

    reference_at: datetime
    progress_m_at_reference: float
    speed_mps: float
    max_progress_m: float
    horizon_s: float
    dwell_until: datetime | None


    hold_reason: str | None = None
    cap_stop_id: str | None = None
    cap_kind: Literal["stop", "horizon"] | None = None
    cap_reached_at: datetime | None = None
    envelope_id: str | None = None

    @field_serializer("reference_at", "dwell_until", "cap_reached_at", when_used="json")
    def milliseconds(self, value: datetime | None):
        return value.isoformat(timespec="milliseconds") if value is not None else None


class StopStateOut(BaseModel):
    source: str
    operator_status: str | None
    operator_stop_id: str | None
    observation_observed_at: datetime | None
    coherent: bool | None


class RenderedOut(BaseModel):
    stop_state: StopStateOut | None = None
    frozen_basis: Literal["authorized_envelope_end", "anchor_version_changed"] | None = None
    last_confirmed_progress_m: float | None = None
    dwell_basis: Literal["muestras", "ancla"] | None = None
    rendering_method: RenderingMethodLiteral
    coordinate_space: Literal["map_matched", "raw", "schedule"] | None
    lat: float | None
    lon: float | None
    progress_m: float | None
    pattern_id: str | None
    geometry_version: str | None
    """Solo con `coordinate_space == "map_matched"`."""
    geometry_candidate_version: str | None
    """Versión de la geometría candidata/contextual cuando **no** hubo
    proyección real (nota abierta por MP-018 para esta tarea)."""
    confidence_index: float | None
    """Índice heurístico **no calibrado** (anexo de Hito 3): no es una
    probabilidad. `None` cuando no hay base para estimarlo."""
    calculated_at: datetime
    display_at: datetime
    valid_until: datetime | None
    last_confirmed_at: datetime | None
    anchor_observed_at: datetime | None
    anchor_age_s: float | None
    anchor_distance_from_raw_m: float | None
    progress_envelope: ProgressEnvelopeOut | None
    reason: str | None


class VehicleTimestampsOut(BaseModel):
    """Los cinco instantes que el anexo exige no confundir entre sí."""

    gps_observed_at: datetime
    received_at: datetime
    feed_published_at: datetime | None
    snapshot_generated_at: datetime
    display_at: datetime


class SnapshotDelayOut(BaseModel):
    seconds: int | None
    coverage: Literal["reported", "missing"]
    observed_at: datetime | None
    age_s: float | None
    source: Literal["operator_trip_update"] | None
    expired: bool
    """`True` cuando existe un retraso de operador pero es demasiado antiguo
    para aplicarlo; se publica con su edad y no se usa para la ETA."""
    approximation: str | None
    """`trip_level_delay_applied_to_all_stops` cuando el retraso es de nivel
    viaje: se declara la aproximación, no se propaga en silencio."""


class SnapshotVehicleOut(BaseModel):
    vehicle_id: str
    trip_id: str
    service_date: str
    """Día de servicio GTFS resuelto **para esta circulación**, no la fecha
    civil: un viaje con horas `24:xx` sigue perteneciendo al día en que empezó
    después de la medianoche local. `circulation_status` y la posición se
    calculan contra este día."""
    route_id: str | None
    line: str | None
    pattern_id: str | None
    circulation_status: Literal["active", "expired", "unresolved"]
    schedule_relationship: str | None
    timestamps: VehicleTimestampsOut
    raw: RawPositionOut
    map_matched: MapMatchedOut | None
    rendered: RenderedOut
    position: PositionOut | None
    """Vista de compatibilidad de los cuatro estados de ADR-0004. En estimated y stale
    sin retraso de presentación, las coordenadas coinciden con rendered.
    `rendered` es la autoridad de presentación; ambos derivan del mismo ancla
    (`rendered.anchor_observed_at`)."""
    delay: SnapshotDelayOut
    quality: QualityOut


class SnapshotRevisionOut(BaseModel):
    """Revisión ordenable **solo dentro de `scope`** (ADR-0014).

    Regla de contrato para el cliente: si `scope` coincide, ordenar por
    `sequence` y descartar una respuesta con `sequence` menor; con `sequence`
    igual, desempatar por `generated_at` y después por `tiebreak`. Si `scope`
    difiere, **no** comparar secuencias: tratarlo como discontinuidad.
    `snapshot_id` jamás se ordena.
    """

    scope: str
    scope_source: Literal["database_system_identifier", "database_oid", "unavailable"]
    sequence: int | None
    generated_at: datetime
    tiebreak: str


class SnapshotDegradationOut(BaseModel):
    resource: str
    feed_name: str | None
    status: Literal["stale", "error", "unknown"]
    reason: str
    last_valid_source_timestamp: datetime | None
    data_age_s: float | None
    poll_age_s: float | None


class SnapshotCountsOut(BaseModel):
    """Dos particiones independientes y exactas de `vehicles_total`.

    `by_rendering_method` reparte cada circulación por **cómo** se obtuvo su
    coordenada publicada, y `by_coordinate_space` por **a qué espacio**
    pertenece. Son cortes distintos de lo mismo: una circulación congelada
    cuya coordenada vive en el corredor cuenta en `stale_frozen` y en
    `map_matched` a la vez. Cada diccionario suma exactamente
    `vehicles_total`; no se mezclan los dos criterios en un solo contador,
    para que ninguna cifra sea ambigua.

    Las claves ausentes son ausencia de casos, no se publican como `0`
    artificiales de categorías que no existen en este snapshot.
    """

    vehicles_total: int
    by_rendering_method: dict[RenderingMethodLiteral, int]
    by_coordinate_space: dict[Literal["map_matched", "raw", "schedule", "none"], int]
    with_operator_delay: int
    without_operator_delay: int


class SnapshotOut(GtfsValidityOut):
    schema_version: str = SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str
    snapshot_id_is_sortable: Literal[False] = False
    """Declarado en el propio payload: `snapshot_id` es identidad de contenido.
    Ordenar hashes o UUID como si fueran secuencias está prohibido; para eso
    está `revision`."""
    revision: SnapshotRevisionOut
    mode: Literal["live", "replay"]
    catalog_ref: CatalogRefOut
    generated_at: datetime
    display_at: datetime
    feeds: list[FeedHealthOut]
    degraded: list[SnapshotDegradationOut]
    vehicles: list[SnapshotVehicleOut]
    counts: SnapshotCountsOut


class EtaOut(BaseModel):
    """ETA con procedencia explícita. Nunca se fabrica un valor: cuando no hay
    base, `method` es `unavailable`, `eta_at` es `null` y `reason` dice por qué,
    conservando siempre el horario planificado si existe."""

    method: Literal["schedule", "operator_delay_on_schedule", "unavailable"]
    scheduled_at: datetime | None
    eta_at: datetime | None
    delay_seconds: int | None
    delay_observed_at: datetime | None
    delay_age_s: float | None
    approximation: str | None
    reason: str | None


class BoardEntryOut(BaseModel):
    trip_id: str
    service_date: str
    """Día de servicio GTFS **de esta llamada**, que tras medianoche puede ser
    el anterior al civil: un viaje con horas `24:xx` pertenece al día de
    servicio en que empezó. Puede diferir de `StationBoardOut.service_date`."""
    route_id: str
    line: str | None
    network_id: str | None
    operator: str
    headsign: str
    destination_stop_id: str
    stop_sequence: int
    scheduled_arrival_time: str | None
    """Hora GTFS tal cual, incluidas las `24:xx` del día de servicio."""
    scheduled_departure_time: str | None
    scheduled_arrival_at: datetime | None
    scheduled_departure_at: datetime | None
    arrival: EtaOut
    departure: EtaOut
    circulation_source: Literal["scheduled_only", "observed"]
    """`scheduled_only` = programado por GTFS sin observación de vehículo; nunca
    se presenta como Live confirmado."""
    vehicle_id: str | None
    position_available: bool
    schedule_relationship: str | None
    operator_next_stop_id: str | None
    relative_to_operator_next: Literal["before", "at", "after", "unknown"] | None
    """Posición de esta parada respecto a la próxima parada que declara el
    operador. No es evidencia de `SKIPPED` por parada: el modelo canónico no
    persiste `stop_time_update` (ver `limitations`)."""


class BoardCoverageOut(BaseModel):
    scheduled_calls: int
    returned: int
    observed_circulations: int
    with_operator_delay: int
    eta_from_operator: int
    eta_from_schedule: int
    eta_unavailable: int
    operator_delay_coverage_pct: float | None
    """`None` cuando el denominador es cero: un porcentaje sin muestra no es
    `0.0` (DEC-009, regla no negociable de `docs/DATA_CONTRACTS.md`)."""


class StationBoardOut(BaseModel):
    schema_version: str = BOARD_SCHEMA_VERSION
    station_id: str
    name: str
    service_date: str
    """Día de servicio principal (el civil de Europe/Madrid)."""
    service_dates_considered: list[str]
    """Días de servicio realmente cruzados para construir el tablero.

    Se derivan de la **ventana completa** (`lookback_s`/`lookahead_s`), no del
    instante de consulta: incluyen el día anterior mientras su horario
    extendido (`24:xx`) pueda caer dentro de la retrospectiva, y el día
    siguiente cuando sus primeras llamadas caigan dentro de la anticipación."""
    calculated_from: str = (
        "gtfs_calendar+calendar_dates+stop_times, cruzado con trip_update y "
        "observaciones de vehículo"
    )
    """El tablero se calcula con servicios y calendario; **no** con trenes
    cercanos por proximidad geográfica."""
    mode: Literal["live", "replay"]
    generated_at: datetime
    display_at: datetime
    revision: SnapshotRevisionOut
    catalog_ref: CatalogRefOut
    entries: list[BoardEntryOut]
    coverage: BoardCoverageOut
    limitations: list[str]


# --------------------------------------------------------------------------
# MP-021: histórico frío. Recursos NUEVOS -- el contrato de MP-019
# (`/api/v1/snapshot`, `/api/v1/catalog`) no se toca.
# --------------------------------------------------------------------------

HISTORY_SCHEMA_VERSION = "history-1.0"


class HistoryDayOut(BaseModel):
    service_date: str
    circulations_scheduled: int
    """Denominador del día: circulaciones que el GTFS programaba (con
    `calendar_dates.txt` aplicado, MP-021)."""
    circulations_observed: int
    circulations_unobserved: int
    """El hueco de cobertura **real**: programadas sin posición y sin ninguna
    actualización de viaje, es decir, de las que no llegó ni una señal. Se
    publica como recuento propio para que ninguna cobertura del día pueda
    presentarse sin él."""
    circulations_canceled: int
    """Programadas que el operador declaró `CANCELED`. **No** son un hueco de
    cobertura: el tren no circuló y el feed lo dijo, así que contarlas como
    fallo de captura culparía al colector de algo que no hizo."""
    circulations_operator_only: int
    """Programadas sin posición pero con actualización de viaje: el operador
    las conocía y nunca se localizaron. Hueco de posición, no de información."""
    circulations_unscheduled: int
    """Observadas cuyo `trip_id` no estaba en el calendario de ese día. No es
    un error de datos a ocultar: es un desajuste real entre el feed en vivo y
    el GTFS estático, y el histórico existe para dejarlo ver."""
    lines_present: int
    rows_total: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    """`None` cuando el día solo tiene servicios programados sin observar."""


class HistoryDaysOut(BaseModel):
    schema_version: str = HISTORY_SCHEMA_VERSION
    archive_root: str
    """Ruta del archivo frío leído, para que una vista vacía se pueda
    diagnosticar sin adivinar qué directorio se consultó."""
    days: list[HistoryDayOut]


class HistoryLineMetricOut(BaseModel):
    route_id: str
    line_short_name: str
    trips_scheduled: int
    """Denominador de `delay_coverage_pct`."""
    trips_with_delay_data: int
    """Denominador de `on_time_pct_of_covered`."""
    delay_coverage_pct: float | None
    on_time_pct_of_covered: float | None
    """`None` -- nunca `0.0` -- cuando ningún viaje de la ruta tuvo retraso
    reportado ese día (DEC-009)."""


class HistoryCirculationOut(BaseModel):
    service_date: str
    route_id: str
    line_short_name: str
    trip_id: str
    vehicle_id: str | None
    """`None` en una circulación programada que nunca se observó: no hay
    vehículo porque no se vio ninguno, no porque se desconozca su nombre."""
    scheduled: bool
    observed: bool
    """Cobertura de **posición**: al menos una `vehicle_position_observation`.
    No significa "sabemos algo del viaje" -- ver `coverage`."""
    canceled: bool | None
    """El operador declaró el viaje `CANCELED`. `None` cuando no hubo ninguna
    actualización de viaje: no es que no esté anulado, es que no se sabe."""
    coverage: Literal["observed", "canceled", "operator_only", "unobserved", "unscheduled"]
    """Clasificación única de la fila; evita que cada consumidor la rederive a
    partir de `scheduled`/`observed`/`canceled` y se equivoque al hacerlo."""
    headsign: str | None
    scheduled_first_stop_id: str | None
    scheduled_first_departure_time: str | None
    scheduled_last_stop_id: str | None
    scheduled_last_arrival_time: str | None
    positions_count: int | None
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    distinct_stops_observed: int | None
    last_current_status: str | None
    trip_updates_count: int | None
    delay_reported_count: int | None
    """Denominador de `on_time`. `None` cuando no hubo ninguna actualización de
    viaje; `0` con `trip_updates_count >= 1` es un **cero medido** (hubo
    actualización y no traía retraso), que es lo que ocurre con una
    cancelación. Las métricas de posición, en cambio, son `None` exactamente
    cuando `observed` es `false`."""
    latest_reported_delay_seconds: int | None
    on_time: bool | None


class HistoryCirculationsOut(BaseModel):
    schema_version: str = HISTORY_SCHEMA_VERSION
    service_date: str
    line: str | None
    only: Literal["all", "observed", "unobserved", "canceled", "operator_only", "unscheduled"]
    returned: int
    limit: int
    truncated: bool
    """`True` cuando la consulta alcanzó `limit`: la lista está recortada y los
    recuentos del día (`/history/days`) siguen siendo la referencia."""
    circulations: list[HistoryCirculationOut]


class HistoryPositionOut(BaseModel):
    observed_at: datetime
    received_at: datetime | None
    latitude: float | None
    longitude: float | None
    current_status: str | None
    current_stop_id: str | None
    speed_kmh: float | None
    bearing: float | None
    quality_flags: str | None
    """Tal como se archivó: son las banderas crudas de la observación, sin
    reinterpretar."""


class HistoryDelayOut(BaseModel):
    observed_at: datetime
    delay_seconds: int | None
    delay_coverage: str


class HistoryCirculationDetailOut(BaseModel):
    schema_version: str = HISTORY_SCHEMA_VERSION
    circulation: HistoryCirculationOut
    positions: list[HistoryPositionOut]
    """Observaciones crudas archivadas de esa circulación, en orden temporal.
    Vacía -- y coherente con `observed=false` -- cuando no se observó."""
    delays: list[HistoryDelayOut]
    """Actualizaciones de viaje del `trip_id`. El operador publica el retraso
    contra el VIAJE, no contra el vehículo, así que se devuelven del viaje y no
    se atribuyen a un tren concreto."""


class HistoryStationMetricOut(BaseModel):
    station_id: str
    observations_count: int


class HistoryStationsOut(BaseModel):
    schema_version: str = HISTORY_SCHEMA_VERSION
    service_date: str
    returned: int
    stations: list[HistoryStationMetricOut]


class HistoryLinesOut(BaseModel):
    schema_version: str = HISTORY_SCHEMA_VERSION
    service_date: str
    lines: list[HistoryLineMetricOut]
