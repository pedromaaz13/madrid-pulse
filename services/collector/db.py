"""Capa de acceso a PostgreSQL/PostGIS (esquema de MP-006).

Cada función recibe una conexión `psycopg` ya abierta y ejecuta su propia
instrucción SQL sin abrir una transacción propia -- el límite de commit es
responsabilidad exclusiva de quien orquesta el ciclo completo
(`collector.run_cycle`, con un único `with conn.transaction():` por ciclo).

Hallazgo durante la verificación de MP-007: una versión anterior envolvía
cada `INSERT` individual en su propio `with conn.transaction()`. Con una
conexión de larga duración (`autocommit=False`), solo la PRIMERA instrucción
ejecutada tras un commit abre una transacción real que se compromete al
salir del bloque; cualquier instrucción posterior que ya encuentre una
transacción ambiente abierta (por ejemplo, un `SELECT` suelto de
`latest_payload_hash`) convierte ese `with conn.transaction()` en un
SAVEPOINT anidado, que libera pero NO compromete la transacción exterior.
El resultado observado al ejecutar un ciclo completo de verdad: las filas de
`source_ingestion_run` quedaban comprometidas pero las de
`vehicle_position_observation` quedaban indefinidamente sin comprometer
hasta que algo llamara a `conn.commit()` -- cosa que nunca ocurría en el
bucle principal. Corregido centralizando el límite de transacción en
`run_cycle`.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import psycopg

from packages.contracts.canonical import ServiceAlert, TripUpdateObservation, VehiclePositionObservation


def insert_ingestion_run(
    conn: psycopg.Connection,
    *,
    feed_name: str,
    source_timestamp: Optional[datetime],
    started_at: datetime,
    finished_at: Optional[datetime],
    status: str,
    entity_count: Optional[int],
    payload_hash: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO source_ingestion_run
                (feed_name, source_timestamp, started_at, finished_at, status, entity_count, payload_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (feed_name, source_timestamp, started_at, finished_at, status, entity_count, payload_hash),
        )
        row = cur.fetchone()
        assert row is not None
        return row[0]


# Las tres tablas de observación comparten la misma forma de dedup: la fila
# más reciente para la misma clave de entidad de origen.
#
# Hallazgo real de la revisión de Codex en MP-007 (reproducido de forma
# independiente, no solo reportado): `ORDER BY observed_at DESC` por sí solo
# NO es determinista cuando dos filas comparten el mismo `observed_at` --
# ese timestamp es el que reporta la propia fuente (el tren/el feed), no el
# instante de nuestro poll, así que dos polls consecutivos con cambios reales
# pueden perfectamente compartir el mismo `observed_at`. Sin un desempate,
# Postgres puede devolver cualquiera de las filas empatadas, y un tercer poll
# que repite el payload cambiado puede compararse contra la fila VIEJA en vez
# de la nueva, insertando una fila duplicada en vez de deduplicar. `id DESC`
# como desempate secundario es monotónico con el orden real de inserción y
# resuelve el empate de forma determinista.
_LATEST_HASH_QUERIES = {
    "vehicle_position_observation": (
        "SELECT payload_hash FROM vehicle_position_observation "
        "WHERE source_vehicle_id = %s ORDER BY observed_at DESC, id DESC LIMIT 1"
    ),
    "trip_update_observation": (
        "SELECT payload_hash FROM trip_update_observation "
        "WHERE source_trip_id = %s ORDER BY observed_at DESC, id DESC LIMIT 1"
    ),
    "service_alert": (
        "SELECT payload_hash FROM service_alert "
        "WHERE source_alert_id = %s ORDER BY active_period_start DESC, id DESC LIMIT 1"
    ),
}


def latest_payload_hash(conn: psycopg.Connection, table: str, entity_key: str) -> Optional[str]:
    """Hash de la última fila almacenada para esta clave de entidad, si existe.

    `table` es siempre una de las claves fijas de `_LATEST_HASH_QUERIES`
    (nunca una cadena proveniente del feed), por lo que no hay riesgo de
    inyección SQL al seleccionar la consulta correspondiente.
    """
    query = _LATEST_HASH_QUERIES[table]
    with conn.cursor() as cur:
        cur.execute(query, (entity_key,))
        row = cur.fetchone()
        return row[0] if row else None


def insert_vehicle_position_observation(
    conn: psycopg.Connection,
    obs: VehiclePositionObservation,
    *,
    received_at: datetime,
    ingestion_run_id: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vehicle_position_observation
                (observed_at, received_at, source_vehicle_id, source_trip_id, latitude, longitude,
                 current_status, current_stop_id, raw_vehicle_label, nucleo_prefix, nucleo_name,
                 payload_hash, ingestion_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                obs.observed_at,
                received_at,
                obs.source_vehicle_id,
                obs.source_trip_id,
                obs.latitude,
                obs.longitude,
                obs.current_status,
                obs.current_stop_id,
                obs.raw_vehicle_label,
                obs.nucleo_prefix,
                obs.nucleo_name,
                obs.payload_hash,
                ingestion_run_id,
            ),
        )


def insert_trip_update_observation(
    conn: psycopg.Connection,
    obs: TripUpdateObservation,
    *,
    received_at: datetime,
    ingestion_run_id: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trip_update_observation
                (observed_at, received_at, source_trip_id, schedule_relationship, delay_seconds,
                 delay_coverage, next_stop_id, nucleo_prefix, payload_hash, ingestion_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                obs.observed_at,
                received_at,
                obs.source_trip_id,
                obs.schedule_relationship,
                obs.delay_seconds,
                obs.delay_coverage,
                obs.next_stop_id,
                obs.nucleo_prefix,
                obs.payload_hash,
                ingestion_run_id,
            ),
        )


def insert_service_alert(
    conn: psycopg.Connection,
    alert: ServiceAlert,
    *,
    ingestion_run_id: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO service_alert
                (source_alert_id, description_text, description_language, active_period_start,
                 active_period_end, affected_route_ids, nucleo_prefixes, payload_hash, ingestion_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                alert.source_alert_id,
                alert.description_text,
                alert.description_language,
                alert.active_period_start,
                alert.active_period_end,
                json.dumps(alert.affected_route_ids),
                json.dumps(sorted(alert.nucleo_prefixes)),
                alert.payload_hash,
                ingestion_run_id,
            ),
        )
