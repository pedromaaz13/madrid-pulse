"""API propia de Madrid Pulse (`/api/v1/*`) — ver docs/DATA_CONTRACTS.md.

Nunca hace de passthrough de las APIs de Renfe/CRTM; siempre lee de
PostgreSQL y de la topología/geometría ya resueltas en memoria. Nunca
inventa un dato ausente como cero -- ver `apps/api/service.py`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg
import logging
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response

from . import service, snapshot
from .config import ApiConfig
from .gtfs_source import LoadedNetwork, load_network
from .schemas import (
    CatalogOut,
    HealthOut,
    LineOut,
    SnapshotOut,
    StationBoardOut,
    StationOut,
    VehicleOut,
)

_STATE: dict[str, object] = {}
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = ApiConfig.from_env()
    _STATE["config"] = config
    network = load_network(config)
    _STATE["network"] = network
    logger.info(
        "API mode=%s GTFS=%s vigencia=%s..%s",
        network.mode, network.gtfs_version, network.gtfs_valid_from, network.gtfs_valid_until,
    )
    yield
    _STATE.clear()


app = FastAPI(
    title="Madrid Pulse API",
    version="1.0.0",
    description="API propia de Madrid Pulse. No es un passthrough de Renfe/CRTM.",
    lifespan=lifespan,
)


def get_config() -> ApiConfig:
    config = _STATE.get("config")
    if config is None:
        raise RuntimeError("ApiConfig no inicializada (lifespan no ejecutado)")
    return config  # type: ignore[return-value]


def get_network() -> LoadedNetwork:
    network = _STATE.get("network")
    if network is None:
        raise RuntimeError("LoadedNetwork no inicializada (lifespan no ejecutado)")
    return network  # type: ignore[return-value]


def get_connection(config: ApiConfig = Depends(get_config)) -> psycopg.Connection:
    with psycopg.connect(config.database_dsn) as conn:
        yield conn


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@app.get("/api/v1/health", response_model=HealthOut)
def health(
    config: ApiConfig = Depends(get_config),
    network: LoadedNetwork = Depends(get_network),
    conn: psycopg.Connection = Depends(get_connection),
) -> HealthOut:
    result = service.feed_health(conn, now_utc(), stale_after_s=config.feed_stale_after_s)
    return result.model_copy(update={
        "mode": network.mode,
        "gtfs_version": network.gtfs_version,
        "gtfs_valid_from": network.gtfs_valid_from.isoformat(),
        "gtfs_valid_until": network.gtfs_valid_until.isoformat(),
    })


@app.get("/api/v1/live/vehicles", response_model=list[VehicleOut])
def live_vehicles(
    network: LoadedNetwork = Depends(get_network),
    conn: psycopg.Connection = Depends(get_connection),
) -> list[VehicleOut]:
    return service.list_vehicles(conn, network, now_utc())


@app.get("/api/v1/live/vehicles/{vehicle_id}", response_model=VehicleOut)
def live_vehicle(
    vehicle_id: str,
    network: LoadedNetwork = Depends(get_network),
    conn: psycopg.Connection = Depends(get_connection),
) -> VehicleOut:
    result = service.get_vehicle(conn, network, vehicle_id, now_utc())
    if result is None:
        raise HTTPException(status_code=404, detail="vehicle_id no encontrado")
    return result


@app.get("/api/v1/lines", response_model=list[LineOut])
def lines(network: LoadedNetwork = Depends(get_network)) -> list[LineOut]:
    return service.list_lines(network)


@app.get("/api/v1/lines/{line_id}", response_model=LineOut)
def line_detail(line_id: str, network: LoadedNetwork = Depends(get_network)) -> LineOut:
    result = service.get_line(network, line_id)
    if result is None:
        raise HTTPException(status_code=404, detail="line_id no encontrado")
    return result


@app.get("/api/v1/stations", response_model=list[StationOut])
def stations(network: LoadedNetwork = Depends(get_network)) -> list[StationOut]:
    return service.list_stations(network)


@app.get("/api/v1/stations/{station_id}", response_model=StationOut)
def station_detail(station_id: str, network: LoadedNetwork = Depends(get_network)) -> StationOut:
    result = service.get_station(network, station_id)
    if result is None:
        raise HTTPException(status_code=404, detail="station_id no encontrado")
    return result


# --------------------------------------------------------------------------
# MP-019 (ADR-0014): catálogo cacheable, snapshot operativo y tablero.
# --------------------------------------------------------------------------


def _replay_clock(
    config: ApiConfig, network: LoadedNetwork, at: datetime | None
) -> datetime:
    try:
        return snapshot.resolve_clock(config, network, at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/catalog", response_model=CatalogOut)
def catalog(
    request: Request,
    response: Response,
    network: LoadedNetwork = Depends(get_network),
) -> CatalogOut | Response:
    """Catálogo cacheable, versionado por GTFS + geometría.

    Responde `304` cuando el cliente ya tiene la versión vigente: el catálogo
    solo cambia si cambia el GTFS o la geometría, nunca con un sondeo. Es
    deliberadamente el **único** recurso cacheable: `/snapshot` se sirve con
    `no-store` para que ningún dato viejo se rotule como nuevo.
    """
    etag = f'"{network.catalog_version}"'
    headers = {"ETag": etag, "Cache-Control": "no-cache"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    cached = network._catalog_json.get(network.catalog_version)
    if cached is None:
        cached = snapshot.build_catalog_payload(network).model_dump_json().encode()
        network._catalog_json[network.catalog_version] = cached
    # Devolver una `Response` ya serializada evita revalidar y reserializar el
    # mismo payload inmutable en cada petición (ver la medición en
    # docs/evidence/mp-019-explain-y-bench.md). `response_model` sigue
    # documentando el contrato en OpenAPI.
    return Response(content=cached, media_type="application/json", headers=headers)


@app.get("/api/v1/snapshot", response_model=SnapshotOut)
def live_snapshot(
    response: Response,
    at: datetime | None = Query(
        default=None,
        description=(
            "Reloj explícito, solo admitido en modo replay. En live se rechaza con 400: "
            "un instante arbitrario permitiría falsificar edades."
        ),
    ),
    display_lag_s: float | None = Query(
        default=None,
        ge=0,
        description=(
            "Retraso de presentación declarado. Con un valor > 0 y dos anclas reales, "
            "`rendered.rendering_method` puede ser `interpolated_between_known_anchors`."
        ),
    ),
    config: ApiConfig = Depends(get_config),
    network: LoadedNetwork = Depends(get_network),
    conn: psycopg.Connection = Depends(get_connection),
) -> SnapshotOut:
    response.headers["Cache-Control"] = "no-store"
    now = _replay_clock(config, network, at)
    return snapshot.build_snapshot(conn, network, config, now, display_lag_s=display_lag_s)


@app.get("/api/v1/stations/{station_id}/board", response_model=StationBoardOut)
def station_board(
    station_id: str,
    response: Response,
    at: datetime | None = Query(default=None, description="Reloj explícito, solo en replay."),
    lookback_s: float = Query(default=600.0, ge=0, le=7200),
    lookahead_s: float = Query(default=7200.0, ge=0, le=86400),
    limit: int = Query(default=20, ge=1, le=200),
    config: ApiConfig = Depends(get_config),
    network: LoadedNetwork = Depends(get_network),
    conn: psycopg.Connection = Depends(get_connection),
) -> StationBoardOut:
    """Tablero calculado con servicios + calendario + actualizaciones.

    Nunca con "trenes cercanos": parte de la enumeración real de servicios
    programados del día de servicio (`scheduled_trip_instances_for_date`).
    """
    response.headers["Cache-Control"] = "no-store"
    now = _replay_clock(config, network, at)
    result = snapshot.build_station_board(
        conn,
        network,
        config,
        station_id,
        now,
        lookback_s=lookback_s,
        lookahead_s=lookahead_s,
        limit=limit,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="station_id no encontrado")
    return result
