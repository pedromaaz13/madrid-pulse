"""Modelos de respuesta — conformes a docs/DATA_CONTRACTS.md."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
    poll_age_s: float
    unchanged_for_s: float | None
    entities: int | None
    rejected: int


class HealthOut(BaseModel):
    feeds: list[FeedHealthOut]
    mode: Literal["live", "replay"] | None = None
    gtfs_version: str | None = None
    gtfs_valid_from: str | None = None
    gtfs_valid_until: str | None = None


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

SNAPSHOT_SCHEMA_VERSION = "1.0"
CATALOG_SCHEMA_VERSION = "1.0"
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


class CatalogOut(BaseModel):
    """Catálogo cacheable: cambia solo con el GTFS o la geometría, nunca con un
    sondeo. Se sirve con `ETag`/`304` y no incluye ningún dato operativo."""

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
    estaciones.
    """

    reference_at: datetime
    progress_m_at_reference: float
    speed_mps: float
    max_progress_m: float
    horizon_s: float
    dwell_until: datetime | None


class RenderedOut(BaseModel):
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
    """Vista de compatibilidad de los cuatro estados de ADR-0004, sin cambios.
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
    vehicles_total: int
    rendered_map_matched: int
    rendered_raw: int
    rendered_schedule_only: int
    rendered_stale_frozen: int
    rendered_unlocated: int
    with_operator_delay: int
    without_operator_delay: int


class SnapshotOut(BaseModel):
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
