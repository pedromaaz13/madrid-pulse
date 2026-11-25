"""Lecturas de PostgreSQL para la API — nunca escribe (colector aparte)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import psycopg
from psycopg.rows import dict_row

from packages.contracts.canonical import TripUpdateObservation, VehiclePositionObservation


@dataclass(frozen=True)
class ObservedRow:
    """Observación canónica más los dos timestamps que el modelo Pydantic no
    conserva: ``received_at`` (cuándo lo recibió el colector) y
    ``feed_published_at`` (cabecera publicada del feed que lo trajo).

    El anexo de Hito 3 exige distinguirlos de ``gps_observed_at``
    (``position.observed_at``): la hora de un sondeo exitoso no es la edad de
    un dato de origen antiguo. ``feed_published_at`` es ``None`` cuando la
    ejecución de ingesta no registró cabecera, nunca ``received_at`` en su
    lugar.
    """

    position: VehiclePositionObservation
    received_at: datetime
    feed_published_at: datetime | None = None


@dataclass(frozen=True)
class VehicleHistory:
    source_vehicle_id: str
    latest: ObservedRow
    previous: ObservedRow | None


def _row_to_observed(row: dict) -> ObservedRow:
    position = VehiclePositionObservation(
        source_vehicle_id=row["source_vehicle_id"],
        source_trip_id=row["source_trip_id"],
        observed_at=row["observed_at"].astimezone(timezone.utc),
        latitude=row["latitude"],
        longitude=row["longitude"],
        current_status=row["current_status"],
        current_stop_id=row["current_stop_id"],
        speed_kmh=row["speed_kmh"],
        bearing=row["bearing"],
        raw_vehicle_label=row["raw_vehicle_label"],
        payload_hash=row["payload_hash"],
    )
    published = row.get("feed_published_at")
    return ObservedRow(
        position=position,
        received_at=row["received_at"].astimezone(timezone.utc),
        feed_published_at=published.astimezone(timezone.utc) if published is not None else None,
    )


def latest_vehicle_histories(
    conn: psycopg.Connection, *, as_of: datetime | None = None
) -> list[VehicleHistory]:
    """Las dos observaciones más recientes de cada vehículo distinto visto.

    Sin corte de edad: un vehículo con último dato muy antiguo se devuelve
    igualmente -- es responsabilidad del motor de movimiento (MP-012)
    clasificarlo como `stale`/`scheduled`, no de esta capa ocultarlo.
    Con `as_of` solo se consideran observaciones e ingestas hasta ese instante.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            WITH ranked AS (
                SELECT v.source_vehicle_id, v.source_trip_id, v.observed_at, v.received_at,
                       v.latitude, v.longitude, v.current_status, v.current_stop_id,
                       v.speed_kmh, v.bearing, v.raw_vehicle_label, v.payload_hash,
                       r.source_timestamp AS feed_published_at,
                       row_number() OVER (
                           PARTITION BY v.source_vehicle_id
                           ORDER BY v.observed_at DESC, v.id DESC
                       ) AS rank
                FROM vehicle_position_observation v
                JOIN source_ingestion_run r ON r.id = v.ingestion_run_id
                WHERE %(as_of)s::timestamptz IS NULL
                   OR (r.started_at <= %(as_of)s AND v.observed_at <= %(as_of)s)
            )
            SELECT * FROM ranked WHERE rank <= 2
            ORDER BY source_vehicle_id, rank
            """,
            {"as_of": as_of},
        )
        by_vehicle: dict[str, list[dict]] = {}
        for row in cur.fetchall():
            by_vehicle.setdefault(row["source_vehicle_id"], []).append(row)

    histories: list[VehicleHistory] = []
    for vehicle_id, rows in by_vehicle.items():
        rows.sort(key=lambda item: item["rank"])
        latest = _row_to_observed(rows[0])
        previous = _row_to_observed(rows[1]) if len(rows) > 1 else None
        histories.append(
            VehicleHistory(source_vehicle_id=vehicle_id, latest=latest, previous=previous)
        )
    return histories


def vehicle_history(conn: psycopg.Connection, source_vehicle_id: str) -> VehicleHistory | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT v.source_vehicle_id, v.source_trip_id, v.observed_at, v.received_at,
                   v.latitude, v.longitude, v.current_status, v.current_stop_id,
                   v.speed_kmh, v.bearing, v.raw_vehicle_label, v.payload_hash,
                   r.source_timestamp AS feed_published_at
            FROM vehicle_position_observation v
            JOIN source_ingestion_run r ON r.id = v.ingestion_run_id
            WHERE v.source_vehicle_id = %s
            ORDER BY v.observed_at DESC, v.id DESC
            LIMIT 2
            """,
            (source_vehicle_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return None
    latest = _row_to_observed(rows[0])
    previous = _row_to_observed(rows[1]) if len(rows) > 1 else None
    return VehicleHistory(source_vehicle_id=source_vehicle_id, latest=latest, previous=previous)


def latest_trip_update(
    conn: psycopg.Connection, source_trip_id: str, *, observed_after: datetime
) -> TripUpdateObservation | None:
    """Última actualización de viaje, acotada a ``observed_after``.

    Hallazgo real de MP-017 (kit Hito 3): un `trip_id` GTFS recurre cada día
    que su `service_id` está activo -- el mismo `source_trip_id` identifica la
    circulación de hoy y la de ayer. Sin cota temporal, un retraso de ayer
    seguía siendo "la última actualización" hasta que llegara una fila nueva
    de hoy, completando el viaje de hoy con un dato de otra fecha de servicio.
    `observed_after` exige que la fila realmente pertenezca a la ventana
    reciente del llamante (ver `apps/api/service.py`, que la calcula a partir
    de la fecha de servicio vigente), no a cualquier histórico del mismo id.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT source_trip_id, observed_at, schedule_relationship, delay_seconds,
                   delay_coverage, next_stop_id, payload_hash
            FROM trip_update_observation
            WHERE source_trip_id = %s AND observed_at >= %s
            ORDER BY observed_at DESC, id DESC
            LIMIT 1
            """,
            (source_trip_id, observed_after),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return TripUpdateObservation(
        source_trip_id=row["source_trip_id"],
        observed_at=row["observed_at"].astimezone(timezone.utc),
        schedule_relationship=row["schedule_relationship"],
        delay_seconds=row["delay_seconds"],
        delay_coverage=row["delay_coverage"],
        next_stop_id=row["next_stop_id"],
        payload_hash=row["payload_hash"],
    )


@dataclass(frozen=True)
class FeedRunSample:
    feed_name: str
    source_timestamp: datetime | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    entity_count: int | None
    payload_hash: str


def recent_ingestion_runs(
    conn: psycopg.Connection, *, as_of: datetime, per_feed_limit: int = 50
) -> list[FeedRunSample]:
    """Ejecuciones por feed hasta el reloj de la petición, inclusive.

    Corrección de MP-019: la versión anterior rankeaba **toda** la tabla con una
    ventana y descartaba el exceso en Python, así que el coste crecía con el
    histórico completo de ingesta aunque solo se usaran 50 filas por feed. El
    `LATERAL` acotado usa el índice
    `source_ingestion_run_feed_started_at_idx` (migración 0002) y devuelve
    como máximo `per_feed_limit` filas de cada feed.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            WITH feeds AS (SELECT DISTINCT feed_name FROM source_ingestion_run)
            SELECT recent.*
            FROM feeds
            CROSS JOIN LATERAL (
                SELECT run.feed_name, run.source_timestamp, run.started_at, run.finished_at,
                       run.status, run.entity_count, run.payload_hash
                FROM source_ingestion_run run
                WHERE run.feed_name = feeds.feed_name AND run.started_at <= %s
                ORDER BY run.started_at DESC, run.id DESC
                LIMIT %s
            ) AS recent
            """,
            (as_of, per_feed_limit),
        )
        rows = cur.fetchall()
    return [
        FeedRunSample(
            feed_name=row["feed_name"],
            source_timestamp=(
                row["source_timestamp"].astimezone(timezone.utc)
                if row["source_timestamp"] is not None else None
            ),
            started_at=row["started_at"].astimezone(timezone.utc),
            finished_at=(
                row["finished_at"].astimezone(timezone.utc)
                if row["finished_at"] is not None else None
            ),
            status=row["status"],
            entity_count=row["entity_count"],
            payload_hash=row["payload_hash"],
        )
        for row in rows
    ]


def latest_trip_updates(
    conn: psycopg.Connection,
    source_trip_ids: Sequence[str],
    *,
    observed_after: datetime,
    as_of: datetime | None = None,
) -> dict[str, TripUpdateObservation]:
    """Igual que ``latest_trip_update`` pero para muchos viajes en **una** consulta.

    Elimina el N+1 real que tenía ``service.list_vehicles`` (una consulta por
    vehículo). ``DISTINCT ON`` con el mismo orden que la versión unitaria
    (``observed_at DESC, id DESC``) garantiza que cada viaje devuelva
    exactamente la misma fila que devolvería la consulta individual, incluido
    el desempate ``id DESC`` de ADR-0010.

    Un viaje sin fila dentro de la ventana simplemente no aparece en el
    diccionario: ausencia, no un retraso de cero.
    Con `as_of` se exige que la observación y su ingesta ya hayan ocurrido.
    """
    if not source_trip_ids:
        return {}
    unique_ids = sorted(set(source_trip_ids))
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (source_trip_id)
                   source_trip_id, observed_at, schedule_relationship, delay_seconds,
                   delay_coverage, next_stop_id, payload_hash
            FROM trip_update_observation u
            WHERE source_trip_id = ANY(%(trip_ids)s) AND observed_at >= %(observed_after)s
              AND (%(as_of)s::timestamptz IS NULL OR (
                  observed_at <= %(as_of)s AND EXISTS (
                      SELECT 1 FROM source_ingestion_run r
                      WHERE r.id = u.ingestion_run_id AND r.started_at <= %(as_of)s
                  )
              ))
            ORDER BY source_trip_id, observed_at DESC, id DESC
            """,
            {"trip_ids": unique_ids, "observed_after": observed_after, "as_of": as_of},
        )
        rows = cur.fetchall()
    return {
        row["source_trip_id"]: TripUpdateObservation(
            source_trip_id=row["source_trip_id"],
            observed_at=row["observed_at"].astimezone(timezone.utc),
            schedule_relationship=row["schedule_relationship"],
            delay_seconds=row["delay_seconds"],
            delay_coverage=row["delay_coverage"],
            next_stop_id=row["next_stop_id"],
            payload_hash=row["payload_hash"],
        )
        for row in rows
    }


@dataclass(frozen=True)
class RevisionMarker:
    """Revisión monotónica **dentro de un ámbito explícito** (ADR-0014).

    `sequence` es el mayor `source_ingestion_run.id` considerado: una secuencia
    real de PostgreSQL, monotónica, que sobrevive a reinicios del proceso de
    API y que **no** avanza cuando el colector se detiene (no rejuvenece nada).
    `scope` acota dónde esa comparación es lícita: el `system_identifier` del
    clúster. Tras una restauración en otro clúster el `scope` cambia y comparar
    secuencias entre ámbitos distintos queda prohibido por contrato.

    `sequence` es `None` cuando no hay ninguna ejecución de ingesta registrada:
    ausencia de revisión, no revisión cero.
    """

    scope: str
    scope_source: str
    sequence: int | None


def revision_marker(conn: psycopg.Connection, *, as_of: datetime) -> RevisionMarker:
    scope, scope_source = _revision_scope(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT max(id) FROM source_ingestion_run WHERE started_at <= %s", (as_of,))
        row = cur.fetchone()
    sequence = row[0] if row is not None else None
    return RevisionMarker(scope=scope, scope_source=scope_source, sequence=sequence)


def _revision_scope(conn: psycopg.Connection) -> tuple[str, str]:
    """`system_identifier` del clúster, con degradación declarada.

    `pg_control_system()` exige privilegios que un rol de solo lectura puede no
    tener. En ese caso se degrada a la identidad de la base de datos y se
    **declara** en `scope_source`, para que un cliente sepa que el ámbito es
    más débil (no distingue una restauración en un clúster distinto con el
    mismo OID) en vez de confiar de más en una secuencia.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT system_identifier FROM pg_control_system()")
            row = cur.fetchone()
        if row is not None and row[0] is not None:
            return f"pg:{row[0]}", "database_system_identifier"
    except psycopg.Error:
        conn.rollback()
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), oid FROM pg_database WHERE datname = current_database()")
        row = cur.fetchone()
    if row is None:
        return "unknown", "unavailable"
    return f"pgdb:{row[0]}:{row[1]}", "database_oid"


def vehicles_for_trips(
    conn: psycopg.Connection, source_trip_ids: Sequence[str], *, as_of: datetime
) -> dict[str, VehiclePositionObservation]:
    """Última observación de vehículo de cada viaje, en **una** consulta.

    El tablero necesita saber si un servicio programado tiene además una
    circulación observada (y si esa observación trae posición). Sin esto haría
    una consulta por fila de tablero: el mismo N+1 que ya tenía
    ``list_vehicles``. Un viaje sin observación no aparece en el diccionario:
    `scheduled_only` se deduce de la ausencia, no de un valor fabricado.
    """
    if not source_trip_ids:
        return {}
    unique_ids = sorted(set(source_trip_ids))
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (v.source_trip_id)
                   v.source_vehicle_id, v.source_trip_id, v.observed_at, v.latitude, v.longitude,
                   v.current_status, v.current_stop_id, v.speed_kmh, v.bearing,
                   v.raw_vehicle_label, v.payload_hash
            FROM vehicle_position_observation v
            JOIN source_ingestion_run r ON r.id = v.ingestion_run_id
            WHERE v.source_trip_id = ANY(%s) AND r.started_at <= %s AND v.observed_at <= %s
            ORDER BY v.source_trip_id, v.observed_at DESC, v.id DESC
            """,
            (unique_ids, as_of, as_of),
        )
        rows = cur.fetchall()
    return {
        row["source_trip_id"]: VehiclePositionObservation(
            source_vehicle_id=row["source_vehicle_id"],
            source_trip_id=row["source_trip_id"],
            observed_at=row["observed_at"].astimezone(timezone.utc),
            latitude=row["latitude"],
            longitude=row["longitude"],
            current_status=row["current_status"],
            current_stop_id=row["current_stop_id"],
            speed_kmh=row["speed_kmh"],
            bearing=row["bearing"],
            raw_vehicle_label=row["raw_vehicle_label"],
            payload_hash=row["payload_hash"],
        )
        for row in rows
    }
