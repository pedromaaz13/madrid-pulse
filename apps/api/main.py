"""API propia de Madrid Pulse (`/api/v1/*`) — ver docs/DATA_CONTRACTS.md.

Nunca hace de passthrough de las APIs de Renfe/CRTM; siempre lee de
PostgreSQL y de la topología/geometría ya resueltas en memoria. Nunca
inventa un dato ausente como cero -- ver `apps/api/service.py`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg
from fastapi import Depends, FastAPI, HTTPException

from . import service
from .config import ApiConfig
from .gtfs_source import LoadedNetwork, load_network
from .schemas import HealthOut, LineOut, StationOut, VehicleOut

_STATE: dict[str, object] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = ApiConfig.from_env()
    _STATE["config"] = config
    _STATE["network"] = load_network(config)
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
    config: ApiConfig = Depends(get_config), conn: psycopg.Connection = Depends(get_connection)
) -> HealthOut:
    return service.feed_health(conn, now_utc(), stale_after_s=config.feed_stale_after_s)


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
