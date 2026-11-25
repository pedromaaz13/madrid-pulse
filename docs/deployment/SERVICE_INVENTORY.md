# SERVICE_INVENTORY.md — Inventario técnico de despliegue (código real, `integration/h3-audited` @ `d32c3da`)

Fecha: 2026-11-24. Estados: **READY** (se puede desplegar tal cual), **CONFIG** (solo configuración/infraestructura), **DEV** (falta desarrollo), **BLOCKED** (impedimento externo o de veracidad). Cada fila cita archivo y evidencia leída en el código; lo no comprobado se marca así.

## Frontend

| Componente | Estado | Evidencia |
|---|---|---|
| Entrada React/Vite | READY | `apps/web/index.html` → `src/main.tsx`; `npm run build` = `tsc -b && vite build && node scripts/verify-build.mjs` (`package.json`); build verde en CI |
| Rutas | READY | no hay router (`package.json` solo `react`, `react-dom`, `maplibre-gl`); vista y selección van en la query string (`src/hooks/useUrlState.ts`: `view`, `hd`, `hl`, `hf`, `replayAt`): no requiere reescritura SPA |
| Ruta base / subruta | CONFIG | `vite.config.ts` no define `base`; el worker de MapLibre usa `import.meta.env.BASE_URL` (`src/map/MapView.tsx:22-24`), así que bastará `base: "/madrid-pulse/"` para GitHub Pages |
| Worker MapLibre | READY | emitido como asset explícito (`vite.config.ts`, `emitMapLibreWorker`), comprobado por `verify-build.mjs` |
| Teselas | **BLOCKED** (producción) / CONFIG | `src/map/MapView.tsx:195` fija `https://tile.openstreetmap.org/{z}/{x}/{y}.png`; atribución ODbL visible (verificado en capturas). La política de OSM no admite uso intensivo sin aprobación (ver §Seguridad). La URL no es configurable: DEV mínimo (variable `VITE_TILE_URL`) |
| URL de API | CONFIG | `src/api/client.ts:1`: `VITE_API_ROOT ?? "/api/v1"` (mismo origen). `vite.config.ts` comenta que en despliegue frontend y `/api` van bajo el mismo origen mediante reverse proxy |
| Variables de entorno del frontend | READY | solo `VITE_API_ROOT` (público por naturaleza; no debe llevar secretos) y `MADRID_PULSE_API_TARGET` (solo proxy de desarrollo) |
| Datos congelados para demo estático | **DEV** | el frontend solo habla con `/api/v1/*` (`src/api/resources.ts`); no existe modo estático. `src/__fixtures__/*.json` son solo de tests |
| Etiquetado de procedencia | READY con límites | el panel muestra `REPLAY`/`SNAPSHOT`, observada/proyectada y cobertura "28 patrones verificados" (capturas auditadas); FR-01/FR-02 siguen abiertos |

## API (FastAPI)

| Componente | Estado | Evidencia |
|---|---|---|
| Entrada | READY | `apps/api/main.py`, `app`; arrancar con `uvicorn apps.api.main:app` (uvicorn en `requirements.txt`) |
| Endpoints | READY | `/api/v1/health, live/vehicles, lines, stations, catalog (ETag), snapshot, stations/{id}/board, history/*` (`apps/api/README.md`, `openapi.json`); todos GET |
| Healthcheck | CONFIG | `/api/v1/health` consulta PostgreSQL y feeds (`main.py:90-102`): sirve de readiness, no de liveness; añadir `/healthz` sin BD es DEV trivial |
| Modo | READY | `MADRID_PULSE_MODE` = `replay` (por defecto) o `live`; `at=` solo en replay, en live → 400 (`snapshot.py:resolve_clock`) |
| GTFS en arranque | CONFIG/DEV | el lifespan carga la red de `MADRID_PULSE_GTFS_SOURCE`, por defecto la fixture reducida `tests/fixtures/gtfs_c5_real` (`apps/api/config.py`); para el núcleo real hace falta el ZIP completo (15 MB, fuera de Git: `python -m apps.api.tools.fetch_gtfs_static`). Falta automatizar la descarga y el aviso de vigencia (FR-19) |
| Histórico | **DEV** (MVP 1) | `apps/api/history.py` lee Parquet local (`SNAPSHOTTER_OUTPUT_DIR`, por defecto `data/parquet`) con DuckDB: requiere volumen persistente o adaptación a almacenamiento de objetos |
| CORS | DEV si hay orígenes distintos | no hay `CORSMiddleware` en `main.py`. Innecesario con reverse proxy de mismo origen |
| Autenticación / rate limiting | **DEV** | ninguno en el código. API de solo lectura; limitación en el borde (proxy/CDN) o middleware |
| DSN por defecto | **DEV** (MP-023/H4-11) | `apps/api/config.py` y `services/collector/config.py` apuntan por defecto a `127.0.0.1:5433` con contraseña local: peligroso fuera de un portátil; H4-11 lo vuelve fallo seguro |
| Logs | CONFIG | `logging` a stdout, sin formato estructurado ni métricas |

## Collector y datos

| Componente | Estado | Evidencia |
|---|---|---|
| Colector | READY (operación) | `python -m services.collector` bucle infinito; sondea 3 feeds de `gtfsrt.renfe.com` cada 30 s (`services/collector/config.py`, `max-age=30` verificado en MP-003); RSS ≈ 19 MB (`docs/evidence/mp-021-coste-colector-continuo.md`) |
| Reinicios | READY | `infra/operate/supervise-collector.sh`, unidades systemd (`madrid-pulse-collector.service.template`, `Restart=always`) y launchd |
| PostgreSQL/PostGIS | CONFIG | imagen `postgis/postgis:17-3.5` (`ci.yml`, `infra/docker/docker-compose.yml`); la API y el colector necesitan acceso de red a esa base, que **no debe exponerse a internet** |
| Migraciones | CONFIG | `infra/migrations/0001_init`, `0002_api_batch_indexes` (+ down); no hay ejecutor de migraciones: CI las aplica con un bucle `psql` (`ci.yml`). DEV pequeño: script/entrypoint idempotente |
| Crecimiento de la base caliente | **DEV** (MVP 1) | ≈258 MB/día proyectados (extrapolación de 21 ciclos, marcada como tal en MP-021); sin purga el volumen de 5 GB de Railway Hobby duraría ~19 días. Retención = DEC-004 (propietario) + tarea |
| Archivo diario | READY | `infra/operate/daily-archive.sh`, `services/snapshotter` (idempotente); ≈19 MB/día de Parquet |
| Seeds | READY | no hay seeds: el GTFS se carga en memoria al arrancar |
| Rutas absolutas | READY | `REPO_ROOT` calculado relativo (`apps/api/config.py`); no hay rutas de usuario en el código (normalizadas en docs) |
| Backups | **DEV** | no existe procedimiento de `pg_dump`/restauración versionado (solo se hizo ad hoc en la incidencia 5433) |
| Datos congelados de replay | CONFIG | `data/hito-03/replay` (fuera de Git, 15,6 MB, solo **dos minutos** de captura 15:32–15:33 del 2026-11-20 + GTFS); un demo con recorrido útil exige una captura local más larga |

## Contenedores y CI/CD

| Componente | Estado | Evidencia |
|---|---|---|
| Dockerfiles | **DEV** | no hay ninguno para API, colector ni frontend; solo `docker-compose.yml` de PostgreSQL local |
| Compose de producción | **DEV** | no existe |
| Workflows | READY (CI) / DEV (CD) | solo `.github/workflows/ci.yml` (push a `main` y PR; jobs python y frontend); **no existe despliegue automático**, ni entornos, secretos ni webhooks en el repositorio (comprobado vía API de GitHub) |
| Estado de CI sobre H3 | READY | PR #3, run 45367091508 sobre `d32c3da`: python 283 tests OK, 18 skipped; frontend verde |

## Resumen
Reutilizable tal cual: frontend, API, colector, archivo, supervisión. Faltan, para publicar algo: modo de datos estáticos (MVP 0); Dockerfiles, compose, migraciones, purga, backups, proxy/rate limit, defaults seguros y automatización de GTFS (MVP 1).
