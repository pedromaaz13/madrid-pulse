# MVP_READINESS.md — Checklist de preparación de Hito 2 ("Live Railway MVP")

Documento de cierre de Hito 2 (`MP-010`→`MP-015`), redactado en MP-015 para la
aceptación del propietario. Resume el estado real, con evidencia verificable,
no una declaración de intenciones — cada punto enlaza a su prueba real. No
reemplaza `docs/STATUS.md` (tablero vivo, detalle por tarea) ni
`docs/CHANGELOG.md` (historial); es el resumen ejecutivo para la decisión de
aceptación.

## 1. Objetivo de Hito 2 — cumplido

> "Primera app local funcional mostrando la C5 en vivo — topología GTFS real,
> geometría OSM, motor de movimiento con cuatro estados, API `/api/v1` propia,
> frontend React/MapLibre, E2E + CI." (`docs/STATUS.md`, autorización del
> propietario del 2026-11-19)

| Componente | Tarea | Estado | Evidencia |
|---|---|---|---|
| Topología GTFS real | MP-010 | `DONE` | `packages/gtfs/`, fixture real congelada (`tests/fixtures/gtfs_c5_real/`, checksums en `MANIFEST.md`) |
| Geometría OSM real | MP-011 | `DONE` | `packages/geo/`, fixture real congelada (`tests/fixtures/osm_c5_real/`, 4 relaciones reales, licencia ODbL — DEC-024) |
| Motor de movimiento (4 estados) | MP-012 | `DONE` | `packages/movement/`, ADR-0004/ADR-0012, calibrado contra el soak real de MP-007 (666,4 km/h máximo map-matched real) |
| API `/api/v1` propia | MP-013 | `DONE` | `apps/api/`, 7 endpoints reales, OpenAPI congelado (`apps/api/openapi.json`) |
| Frontend React/MapLibre | MP-014 | `DONE` | `apps/web/`, 4 rondas de revisión visual real en navegador (ver `docs/STATUS.md` → tareas cerradas) |
| E2E + CI | MP-015 | En curso (este documento) | `.github/workflows/ci.yml`, `tests/e2e/test_replay.py` |

## 2. Demo local real — instrucciones reproducibles

```sh
# 1. Base de datos
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d

# 2. GTFS oficial completo (necesario para resolver vehículos C5 reales en vivo;
#    la fixture reducida de MP-010 basta para los tests, no para la demo en vivo)
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python -m apps.api.tools.fetch_gtfs_static
export MADRID_PULSE_GTFS_SOURCE=data/gtfs_static/fomento_transit.zip

# 3. Colector real (feeds en vivo de Renfe)
python -m services.collector

# 4. API real
uvicorn apps.api.main:app --reload --port 8000

# 5. Frontend real
cd apps/web && npm ci && npm run dev
```

Verificado realmente en esta tarea y en MP-010→MP-014 (ver `docs/STATUS.md`
por tarea): el colector ingiere datos reales de Renfe, el motor de movimiento
map-matchea posiciones reales contra el corredor OSM real, la API resuelve
`route_id`/posición contra la topología GTFS real, y el frontend dibuja el
corredor y los cuatro estados de posición sobre un mapa real en navegador.

## 3. Suite de tests — estado real, verificado dos veces

**Contra la base de desarrollo local** (histórico real de MP-007 presente):
114/114 tests Python en verde, sin ningún `skip`. Frontend: lint/typecheck/5
tests/build en verde.

**Contra un PostgreSQL recién creado** (simulando exactamente lo que hace
CI — migraciones aplicadas desde cero, sin ningún dato preexistente): 109 en
verde + 5 `skip` explícitos y documentados (DEC-035). Esos 5 dependen del
soak real irrepetible de MP-007 (668 filas/24 vehículos capturados en vivo
una sola vez) — no son reproducibles por diseño fuera de la base que los
capturó, y se saltan explícitamente en vez de fallar o declararse superados
sin ejecutarse.

CI (`.github/workflows/ci.yml`) ejecuta ambos jobs (Python + frontend) en
cada push/PR contra un PostgreSQL de servicio recién creado — nunca toca
Renfe/CRTM/OSM en vivo.

## 4. Principios de datos — verificados, no solo declarados

De `AGENTS.md`: UTC interno, idempotencia, raw ≠ normalizado, observado ≠
estimado, dato ausente ≠ cero, puntualidad siempre con cobertura.

- **UTC interno:** `require_utc`/`require_utc_or_none` en `packages/contracts/canonical.py`; conversión a Europe/Madrid solo en presentación/calendario de servicio (tests de frontera de huso horario en `services/snapshotter/tests/test_export.py`).
- **Idempotencia:** deduplicación por hash canónico de payload completo (ADR-0010/DEC-013), probada contra PostgreSQL real en `services/collector/tests/test_collector_cycle.py`.
- **Raw ≠ normalizado:** `packages/contracts/raw.py` (passthrough fiel al feed) vs. `canonical.py` (modelo interno); ningún campo no observado se inventa (ADR-0009, ~800 entidades reales auditadas en MP-005/MP-007).
- **Observado ≠ estimado:** cuatro estados explícitos (`observed`/`estimated`/`stale`/`scheduled`, ADR-0004), nunca con la misma semántica visual en el frontend (4 rondas de revisión visual real de MP-014).
- **Dato ausente ≠ cero:** `delay.coverage: "missing"` nunca se interpreta como retraso cero (probado en `apps/api/tests/test_api_contract.py` y `apps/web/src/format.test.ts`); `on_time_pct_of_covered`/`delay_coverage_pct` son `NULL`, no `0`, cuando el denominador es cero (`services/snapshotter/tests/test_gold.py`).
- **Puntualidad con cobertura:** `delay_coverage_pct` y `on_time_pct_of_covered` siempre se calculan y exponen juntos, nunca uno sin el otro (`docs/DATA_QUALITY.md`, DEC-033).

## 5. Hallazgos reales que moldearon la implementación (no exhaustivo — ver `docs/DECISIONS.md` para las 35 entradas completas)

- "C5" no es un identificador único en el feed nacional de Renfe (Madrid/Asturias/Andalucía) — resuelto con `route_id` completo, nunca el código de línea (ADR-0008, MP-003).
- El colector filtra por núcleo (Madrid), no por línea — de 24 vehículos reales del soak, solo 4 son C5; 19 son otras líneas del núcleo y 1 es un refuerzo sin resolver (DEC-029, confirmado contra el GTFS completo).
- Huecos reales de geometría OSM que un polyline único puentearía silenciosamente — corregido a segmentos explícitos sin interpolar a través de un hueco (MP-011, hallazgo bloqueante de la revisión de Codex).
- El worker de MapLibre se rompía en dos puntos distintos del pipeline de Vite (prebundle de dev con `504`, build de producción sin emitir el asset) — ninguno de los dos lo detectaba un test automatizado; solo la inspección real en navegador (MP-014, 4 rondas).
- `daily_line_metrics`/`station_daily_metrics` llevaban diferidas desde MP-009 (DEC-021) porque la resolución `route_id`/`station_id` no existía todavía — resueltas de verdad en MP-015 (DEC-033) en cuanto esa resolución estuvo disponible.

## 6. Límites conocidos y documentados (no deuda oculta)

| Límite | Dónde se documenta | Por qué no se resolvió ahora |
|---|---|---|
| `trips_scheduled` no usa `calendar_dates.txt` (excepciones de calendario) | DEC-033 | `packages.gtfs` no lo parsea todavía; extenderlo es alcance propio |
| Umbral de puntualidad (300s) sin calibrar con histórico real | DEC-033 | No existe todavía suficiente histórico real de puntualidad para calibrarlo con evidencia |
| `station_daily_metrics` sin `data_quality_events_count` | DEC-033 | `data_quality_event.entity_ref` nunca referencia una parada; atribuirlo exigiría un cruce no verificado |
| `history`/`metrics` endpoints de la API no implementados | DEC-027/ADR-0005 | Dependían de las métricas gold anteriores (ahora resueltas en MP-015) — quedan como alcance de Hito 3 si el propietario lo prioriza |
| CRTM verificado por licencia pero nunca integrado como fuente | ADR-0002 (corregido en MP-015) | Renfe solo bastó para todo el piloto C5; CRTM queda disponible como fuente complementaria futura |
| `analytics/dbt/` sin dbt-core literal | DEC-034 | La disciplina dbt se aplica directamente en `services/snapshotter/gold.py`; introducir el motor sería redundante en este hito |
| Retención de datos (`docs/DATA_MODEL.md`) sigue siendo propuesta, no medida | ADR-0003/DEC-004 | Requiere volumen real sostenido en producción, no alcanzable en un piloto de desarrollo local |

## 7. Gobernanza — pendiente exclusivo del propietario (no se decide aquí)

- **Promoción de ADRs `Propuesto` → `Aceptado`:** ADR-0005, 0008, 0009, 0010, 0011, 0012. Ningún agente puede hacer esta promoción (ADR-0007); MP-015 corrigió únicamente contenido desactualizado (ver `docs/STATUS.md` → "Auditoría de contenido de los 12 ADRs"), nunca el campo `Estado`.
- **DEC-002** (licencia del código propio) y **DEC-004** (retención de datos) siguen `PENDING` — gates de licencia/coste reservados al propietario (ADR-0007).
- **Integración a `main`:** las ramas `mp-010-gtfs-topology` → `mp-015-e2e-readiness` están encadenadas y cada tarea quedó `DONE` tras revisión cruzada real; el propietario decide cuándo y cómo fusionar (en lote al cierre de Hito 2 u otro momento).
- **Hito 3:** propuesta de planificación completa en `docs/HITO_3_BACKLOG.md` (9 áreas, sin implementación), pendiente de que el propietario la revise, recorte o reordene antes de autorizar.

## 8. Recomendación

Hito 2 cumple su objetivo declarado: una app local funcional, real, auditada
en cada tarea por el agente contrario, con evidencia verificable en cada
afirmación de este documento. No hay deuda oculta — cada límite conocido
está documentado con su motivo. Se recomienda al propietario proceder con la
auditoría de integración final (mismo rigor que el cierre de Hito 1,
`docs/STATUS.md` → "Auditoría independiente de preparación para
integración") antes de fusionar a `main`.
