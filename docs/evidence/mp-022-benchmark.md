# MP-022 — Benchmark reproducible de cierre

## Entorno medido

| Dimensión | Valor |
|---|---|
| Equipo | MacBook Air (Apple M1, 8 núcleos, 8 GB RAM) |
| Sistema | macOS 26.6.2 arm64 |
| Python | 3.12.3, entorno `.venv` de este worktree |
| Node | 22.13.1 mediante `fnm` |
| PostgreSQL | `postgis/postgis:17-3.5`, contenedor desechable `mp022-validation-db`, puerto 5437 |
| Dataset | replay congelado `1532/1533`, GTFS `sha256:c5b40823…`, 240 posiciones / 199 updates / 4 alertas / 7 ingestas / 2 eventos de calidad |
| Reloj | `2026-11-20T14:33:31Z`, diez segundos después del corte `1533` |
| Catálogo | 12 líneas, 42 rutas, 103 patrones, 95 estaciones |

No son umbrales universales ni una medición de producción. El benchmark de
API se ejecutó en proceso con `TestClient`: incluye el código de aplicación y
PostgreSQL, pero excluye red y servidor ASGI.

## API — 30 iteraciones por ruta

Comando:

```bash
PYTHONPATH="$PWD" \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/hito-03/replay/fomento_transit.zip" \
MADRID_PULSE_SHORT_NAME= MADRID_PULSE_MODE=replay \
MADRID_PULSE_DATABASE_DSN=postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5437/madrid_pulse \
  .venv/bin/python -m apps.api.tools.bench_snapshot \
  --iterations 30 --station-id 18000 --at 2026-11-20T14:33:31Z
```

| Ruta | Estado | p50 ms | p95 ms | Máx ms | Bytes |
|---|---:|---:|---:|---:|---:|
| `/api/v1/catalog` | 200 | 0.52 | 1.51 | 1.66 | 361 362 |
| `/api/v1/snapshot` | 200 | 254.73 | 418.23 | 2 501.02 | 220 356 |
| `/api/v1/stations/18000/board` | 200 | 103.14 | 179.75 | 212.59 | 23 429 |
| `/api/v1/live/vehicles` (legado) | 200 | 1 621.14 | 2 110.15 | 2 345.80 | 43 313 |
| `/api/v1/health` | 200 | 75.23 | 83.14 | 111.25 | 727 |
| `/api/v1/catalog` condicionado (304) | 304 | 0.41 | 0.58 | 0.74 | 0 |

Observación registrada: el endpoint legado `/api/v1/live/vehicles` es mucho
más costoso que el snapshot batch y queda explícitamente fuera del camino del
frontend MP-020. DEC-038 (pool de conexiones) sigue abierta; no se oculta la
latencia ni se introduce una dependencia durante una auditoría de cierre.

Una primera corrida exploratoria de 60 iteraciones usó por error la estación
inexistente `70110` y devolvió 404; no se presenta como benchmark de tablero.
La tabla anterior es la corrida válida de Atocha (`18000`), todas las rutas con
el estado esperado.

## Edad y cobertura del dato

En el corte exacto `1533` hay 121 observaciones, todas con edad 10 s al
construir el snapshot. La p50/p95 por línea es `10/10 s` salvo C4, que tiene
denominador cero y publica `null`, nunca `0 s`. La cobertura ponderada de
resolución de ruta de **este corte congelado** es `121/121`; no significa que
Renfe publique GPS de todos los 1 299 viajes programados ni que exista
geometría validada para todos los patrones. Véase
[`mp-022-coverage.md`](mp-022-coverage.md).

## Fotogramas y memoria

La evidencia heredada de MP-020 (frontend integrado, Chrome) midió 60 s y 13
fotogramas intermedios de la circulación 19656: 1 316,7 m a 22,0 m/s, pasos
de 110,1–110,5 m cada 5 s, sin teletransporte; también validó movimiento
reducido y el fallback sin WebGL. Esa evidencia sigue en
[`mp-020-inspeccion-navegador.md`](mp-020-inspeccion-navegador.md), pero **no
se atribuye a una nueva corrida MP-022**.

En esta ejecución se midió RSS de los procesos servidor ya calentados: API
13,1 MiB y Vite 3,6 MiB. Esto no es memoria del navegador ni del recorrido de
usuario. Orca no expuso ningún navegador controlable en la sesión del
ejecutor; por tanto duración de frames, heap del navegador y memoria del
recorrido completo quedan **sin re-medición MP-022**. Esta carencia mantiene
la puerta 9 en `PARTIAL` y prohíbe afirmar fluidez final nueva.
