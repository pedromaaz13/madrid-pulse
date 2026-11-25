# MVP_WEB_ARCHITECTURE.md — Dos objetivos de publicación

Fecha: 2026-11-24. Base: `SERVICE_INVENTORY.md` (código real). **Propuesta**: no contrata ni despliega nada.

> **Nota de vigencia (2026-11-25):** la sección **MVP 0** de este documento (exportar el replay de la API, captura de 30–60 min) queda **SUPERADA** por [`MVP0_IMPLEMENTATION_PLAN.md`](MVP0_IMPLEMENTATION_PLAN.md): contrato de demo propio con observaciones, independiente del motor y de `build_snapshot` (que tienen FR-01/FR-02), captura de 90 min. La sección MVP 1 sigue vigente como propuesta.

## MVP 0 — Demo web reproducible (sin procesos persistentes) — SUPERADA

**Qué es.** El frontend actual, publicado como sitio estático, mostrando una **reproducción congelada de una captura real** (Renfe, 2026-11-20) con el reloj de replay que ya existe (`?at=`). Mapa, líneas, estaciones, fichas, tablero y histórico funcionan con ficheros JSON precalculados por la propia API. Nada se presenta como actual: el panel ya muestra `REPLAY` y la hora del snapshot, y se añade un aviso permanente con fecha de la captura y limitaciones.

**Por qué es viable sin servidor.** En replay la respuesta de `/api/v1/snapshot?at=…` es determinista (`snapshot.py:resolve_clock`), el catálogo es cacheable (`ETag`) y el frontend solo hace GET a `/api/v1/*` con un único punto de entrada (`src/api/client.ts`).

```text
 [Local, una vez]                                   [Publicación]
 captura real  ──► PostGIS desechable ──► API (replay) ──► exportador ──► /data/*.json ┐
 (data/hito-03)                             (código actual)   (nuevo)                    ├─► Pages (estático)
 build frontend (VITE_DATA_MODE=static, VITE_TILE_URL) ───────────────────────────────┘        │
                                                              navegador ──► tiles (proveedor) ◄─┘
```

Piezas nuevas mínimas (todas pequeñas, ninguna reescribe la arquitectura):
1. **Exportador estático** (`scripts/export_static_demo.py`): arranca la API en modo replay contra una base desechable cargada con la captura y escribe `catalog.json`, `health.json`, `snapshot/<epoch>.json` (rejilla de 10 s, la cadencia de sondeo del frontend), tableros por estación y fichero(s) de histórico.
2. **Adaptador en el cliente** (`VITE_DATA_MODE=static`): `requestJson` traduce `/snapshot?at=T` al fichero de la rejilla más cercano y reinicia el reloj al agotar la ventana (el reloj ya es repetible). Salud con estado `archivo`, nunca `live`.
3. **Teselas configurables** (`VITE_TILE_URL`) y atribución.
4. **Aviso visible** (limitaciones y FR-01/FR-02) y publicación con `base` correcto.

Límites a decir en voz alta:
- La captura actual cubre **dos minutos** (15:32–15:33). Un demo con recorrido digno exige **una captura local de 30–60 min** (colector + base desechable; coste cero) antes de exportar.
- La reproducción hereda FR-01 (movimiento fantasma antes de salida/tras llegada) y FR-02: es una demo de producto con defectos conocidos y rotulados, no una prueba de calidad. **Decisión del propietario** si se publica así o se espera a H4-04.
- Tamaño estimado: ~140 KB por snapshot (`src/__fixtures__/snapshot-map-matched.json`); 30 min a 10 s = 180 ficheros ≈ 25 MB sin comprimir (≈ unos pocos MB servidos comprimidos). Sin problema para GitHub Pages (≤1 GB) ni Cloudflare Pages (20 000 ficheros, 25 MiB/fichero).

**Dónde.** GitHub Pages (recomendado): coste 0, mismo repositorio, despliegue por Actions propio, sin cuenta nueva. Cloudflare Pages es equivalente y añade cabeceras y dominio; se justifica en MVP 1. Ver `DEPLOYMENT_OPTIONS.md`.

## MVP 1 — Live ferroviario

**Qué es.** Frontend + API + colector + PostGIS conectados, datos GTFS-RT reales de Renfe cada 30 s, con edades y estados. **No se autoriza públicamente** mientras FR-01/FR-02 u otro bloqueante estén abiertos.

```text
 Internet ──HTTPS──► Caddy (único puerto público 443)
                        ├── /            → ficheros estáticos del frontend
                        └── /api/v1/*    → API FastAPI (uvicorn) ──► PostgreSQL/PostGIS (red interna, sin puerto público)
 Colector ──HTTPS──► gtfsrt.renfe.com (3 feeds / 30 s) ──► PostgreSQL
 Cron diario: archivo Parquet (snapshotter) ──► volumen / copia externa;  pg_dump nocturno ──► copia externa
```

Diseño coherente con el código: frontend y API **bajo el mismo origen** (comentado en `vite.config.ts`), así que no hace falta CORS ni exponer la API con otro dominio. La base solo es alcanzable por la red interna. Sin credenciales en variables `VITE_*`.

## Variables de entorno (nombres, sin valores)

| Variable | Componente | Público | Nota |
|---|---|---|---|
| `VITE_API_ROOT` | frontend (build) | sí | por defecto `/api/v1` |
| `VITE_DATA_MODE` | frontend (build) | sí | `static` (MVP 0) — **por crear** |
| `VITE_TILE_URL` | frontend (build) | sí | URL de teselas; claves de proveedor restringidas por dominio — **por crear** |
| `MADRID_PULSE_DATABASE_DSN` / `MADRID_PULSE_DATABASE_URL` | API / colector | **no** | secreto del entorno; sin default tras MP-023 |
| `MADRID_PULSE_MODE` | API | no | `replay` o `live` |
| `MADRID_PULSE_GTFS_SOURCE` | API / colector | no | ruta al ZIP GTFS completo |
| `MADRID_PULSE_NETWORK_ID`, `MADRID_PULSE_SHORT_NAME` | API | no | configuración de red |
| `MADRID_PULSE_FEED_STALE_AFTER_S`, `MADRID_PULSE_OPERATOR_DELAY_MAX_AGE_S`, `MADRID_PULSE_DISPLAY_LAG_S` | API | no | umbrales |
| `COLLECTOR_POLL_INTERVAL_SECONDS`, `COLLECTOR_REQUEST_TIMEOUT_SECONDS`, `COLLECTOR_MAX_RETRIES`, `COLLECTOR_BACKOFF_BASE_SECONDS` | colector | no | 30 s por defecto |
| `SNAPSHOTTER_OUTPUT_DIR` | API / archivo | no | volumen del Parquet |
| `POSTGRES_PASSWORD` | base | **no** | generado en el host, no versionado |

## Seguridad, datos y veracidad
- **Atribuciones obligatorias** en la interfaz: © OpenStreetMap contributors (ODbL) y "Origen de los datos: Renfe Operadora, CC BY 4.0, datos modificados por Madrid Pulse; Renfe no respalda este servicio" (`docs/legal/ATTRIBUTION.md`). Hoy el mapa muestra la de OSM; **falta el pie de Renfe como requisito de publicación** (comprobar en la tarea D-05).
- **Teselas:** la política de uso de OpenStreetMap restringe el uso intensivo de `tile.openstreetmap.org` sin aprobación, exige Referer/User-Agent válidos y caché; para un demo de bajo tráfico con atribución es defendible, **no para un lanzamiento**. Alternativa: proveedor con clave restringida por dominio o PMTiles propio. Elegir proveedor y coste es decisión del propietario.
- **Estados de dato:** la UI ya distingue observada/proyectada y `REPLAY`; en MVP 1 deben mostrarse además `estimada` y `caducada` con edad real (contrato existente; FR-01/FR-02 impiden confiar en la posición proyectada).
- **Datos de usuarios:** la aplicación no recoge ninguno; no hay cuentas.
- **Exposición:** la API es de solo lectura; aun así, limitar tasa en el borde y no exponer `/docs` si no se desea. Base sin puerto público. Claves solo en el entorno del servidor.
