# AUD-08 — reproducción y reconciliación

**Ejecutor:** OpenAI Codex · worker `task_e0212d2fd3fe`
**Fecha:** 2026-11-23
**Rama/worktree:** `audit/hito-03-adversarial` / `audit-hito-03`
**Decisión de ubicación:** se crea este documento separado y no se alarga
`BACKEND_OPERATIONS_AUDIT.md`, que ya contiene la auditoría de operación
específica de AUD-06.

## Veredicto

La lista de cierre actualmente definida por CI contiene 283 casos Python. En
este worktree, que incluye `data/`, se reproduce como **OK, 5 `skip`**; en un
checkout limpio como el que verá GitHub Actions, donde el ZIP oficial bajo
`data/` no está versionado, es **OK, 18 `skip`**. Por tanto, **283/5 no es el
resultado que reportaría CI**: son 265 casos ejecutados allí. El frontend sí
reproduce **89/89**, lint, typecheck y build correctos con Node **22.13.1**.
Esto confirma el conteo final de MP-022, pero no demuestra que todos los
defectos de las auditorías anteriores hayan desaparecido: por ejemplo, AUD-05
encontró un P0 de semántica de replay que la batería verde no ejerce.

La única sonda nueva que abrió un hallazgo es una carrera controlada entre el
colector y el archivador: una exportación puede mezclar generaciones de tablas
si una ingesta confirma entre el `COPY` de una tabla y el de la siguiente. Un
reproceso idempotente reconcilia el día, pero la primera versión del archivo no
es un corte atómico multi-tabla. No se afirma 24/7: ni esta ráfaga ni los 823,2
s de MP-021 lo prueban.

## Entorno y método reproducido

- Contenedor propio y desechable `aud08-postgis`, imagen
  `postgis/postgis:17-3.5`, en `127.0.0.1:5548`; nunca se usó el PostgreSQL
  compartido de `5433`.
- Las migraciones `infra/migrations/0001_init.up.sql` y
  `0002_api_batch_indexes.up.sql` se aplicaron desde una base vacía. Resultado:
  PostgreSQL `17.5`, PostGIS `3.5.2`, **15 tablas base y 2 vistas PostGIS**
  (`geometry_columns` y `geography_columns`), no 17 tablas.
- La lista de módulos invocada fue exactamente la de
  `.github/workflows/ci.yml`. El cargador de `unittest` contó 283 casos en esa
  lista. Se reprodujeron tres resultados de `skip`, según entorno:
  (1) **5** en esta base aislada con `data/` presente: cuatro
  `ApiContractTests` que requieren las 24 filas del soak y
  `test_real_soak_postgres`, que exige exactamente 668; (2) **1** cuando la
  API recibe `MADRID_PULSE_DATABASE_DSN` de la base compartida con los 24
  vehículos, mientras colector/snapshotter usan otro
  `MADRID_PULSE_DATABASE_URL`: los cuatro primeros dejan de saltar y queda el
  test de 668; (3) **18** en un checkout limpio sin el ZIP GTFS oficial de
  `data/`, incluidos 13 `skip` adicionales de catálogo/geo real. CI fija
  explícitamente **ambas** variables de conexión, por lo que (2) es una
  configuración divergente que explica el «1 skip» histórico, no un resultado
  CI válido.
- Para frontend se ejecutó `fnm exec --using 22.13.1 npm ci`, seguido de
  `npm run lint`, `npm run typecheck`, `npm test` y `npm run build`. La primera
  corrida accidental con el Node por defecto `20.20.0` también pasó pero emitió
  `EBADENGINE`; no se usa como evidencia de cierre.

| Comprobación realmente ejecutada | Resultado | Evidencia |
|---|---|---|
| Migrar PostgreSQL vacío | **PASS** | `0001` + `0002`, PostgreSQL 17.5 / PostGIS 3.5.2 / 15 tablas base + 2 vistas |
| Suite Python, worktree con `data/` | **PASS** | 283 casos: 278 pasan y 5 `skip` explícitos; salida 0 contra `:5548` |
| Suite Python, CI de checkout limpio | **PASS** | 283 casos: 265 pasan y 18 `skip`; el ZIP GTFS oficial no viaja en Git, así que este es el resultado representativo de CI |
| Suite Python, DSN/API y URL/colector en BDs distintas | **PASS, no representativo de CI** | 283 casos, 1 `skip`; la API lee su DSN y los otros procesos su URL, mecanismo que explica el conteo histórico |
| Frontend Node 22.13.1 | **PASS** | lint y typecheck limpios; Vitest 10 archivos, **89/89**; build y worker MapLibre `550754` bytes |
| Feed caído + hora civil ambigua | **PASS** | error persistido a `2026-10-25T00:30:00Z`; la hora local ambigua `02:30` se resuelve a su primera ocurrencia, `2026-10-25T00:30:00Z`, sin fecha inventada |
| Ingesta efímera fuera de 1532/1533 | **PASS** | payload sintético válido de 2030, `AUD08-2030` / `1023V19656C5`: ciclo `ok`, 1 fila persistida |
| Carrera colector–archivador | **FAIL** para atomicidad multi-tabla; **PASS** para recuperación por reproceso | primera exportación: 1 posición y 2 `source_ingestion_run`; reproceso: 2 y 2 |
| Operación continua 24/72 h, red real y navegador prolongado | **NOT RUN** | requiere host persistente/autorización y no se sustituye con pruebas locales |

## Escenarios adversariales nuevos

### Caída de feed durante el instante ambiguo de DST

Con dos llamadas reales a las funciones de producción y PostgreSQL aislado se
forzó una `URLError` del feed `vehicle_positions` con reloj fijo
`2026-10-25T00:30:00Z` (la primera `02:30` de Europe/Madrid). `run_cycle()`
persistió una ejecución `('error', NULL, 2026-10-25T00:30:00Z, NULL)` y no
insertó observación; en el mismo escenario `service_day_instant(2026-10-25,
02:30)` devolvió exactamente `2026-10-25T00:30:00Z`, la primera ocurrencia que
declara el contrato temporal. La combinación no mezcló una observación fallida
con una fecha de servicio inventada.

### Dato efímero no perteneciente al replay

Se generó en memoria un payload GTFS-RT válido de una única entidad, con marca
`2030-01-01T00:00:00Z`, identificador `AUD08-2030` y viaje
`1023V19656C5`. No se leyó ninguno de los cortes 1532/1533 como dato de la
sonda. `run_cycle()` devolvió `ok`, `inserted_count=1`, y PostgreSQL almacenó
el vehículo, viaje y `observed_at` esperados. Esto verifica el camino de
normalización/persistencia para una marca temporal nueva; no pretende validar
la vigencia futura del GTFS ni la operación real de Renfe en 2030.

### Carrera entre ingesta y archivo

Se insertó una posición `AUD08-RACE-before` de `2098-01-02`; durante
`export_service_date()` se instrumentó únicamente el límite de sincronización
del experimento, después del `COPY` de
`vehicle_position_observation` y antes de reemplazar su partición. Una segunda
conexión PostgreSQL confirmó `AUD08-RACE-during` en ese punto. El primer
archivo quedó así:

```text
vehicle_position_observation: 1 fila
source_ingestion_run:          2 filas
```

El mismo `export_service_date()` relanzado sin modificar datos dejó `2/2`.
Por tanto la sustitución por partición protege de una caída y el reproceso
converge, pero no existe una vista transaccional única que alinee las cinco
tablas de una primera exportación concurrente.

## Reconciliación AUD-02 a AUD-06

| Tema | Resolución |
|---|---|
| Cobertura geométrica | No hay contradicción: AUD-02 reconstruye **103** patrones; AUD-03 y AUD-04 usan los mismos **28** validados. Los **75** no validados son 72 sin prueba geométrica más 3 parciales; dentro de los 72 hay 67 accionables por adquisición, 1 patrón truncado del feed y 4 C4b con alternativa de coste cero aún no incorporada. |
| `67`, `72` y `75` de AUD-03 | Son universos distintos, no conteos rivales: 75 es todo patrón no `validated`; 72 excluye los 3 `partial`; 67 es el subconjunto de esos 72 para el que falta adquirir/probar una fuente, no los C4b ya contrastables ni el feed truncado. |
| El residuo `68` | Quedó sin explicar en la primera versión de AUD-08. En AUD-01, 68 equivale a los **67** patrones accionables sin fuente/intento más el **1** patrón C8b truncado por el feed: es un conjunto de «sin explicación geométrica suficiente», no 68 trabajos de adquisición. Esta distinción consta en `RAILWAY_GEOMETRY_AUDIT.md:1244-1264`; AUD-08 debe conservarla para no volver a convertirlo en una cifra rival de 67. |
| `72` frente a `75` en AUD-04 | `POSITION_MOVEMENT_AUDIT.md:141` y `:543` llaman «72 de 103 sin corredor validado» a una categoría que, por el catálogo de AUD-03, son **75** no validados (72 `pending` + 3 `partial`). Se registra como discrepancia editorial abierta para sus autores o AUD-09: AUD-08 no modifica un informe ya aprobado. El «75–78 anchor» de ese informe es además un rango de circulaciones, no el recuento de patrones. |
| Horizonte `180` frente a `190` segundos | `POSITION_MOVEMENT_AUDIT.md:455` aún dice «hasta 180 s después del ancla», mientras `:598-663` y los demás informes distinguen 180 s configurados de **190 s efectivos**. Es una discrepancia abierta de redacción: debe decir cuál de las dos magnitudes está midiendo, sin reescribir el informe aprobado en esta tarea. |
| Movimiento frente a geometría | AUD-04 no afirma que los 28 corredores estén completos: examina únicamente los map-matcheables que AUD-03 permite. Sus fallos de reloj/renderizado no contradicen que la geometría de esos 28 sea utilizable. |
| P0 de replay de AUD-05 frente a backend verde de AUD-06 | No hay contradicción: AUD-05 demuestra que un `?at=` anterior a un `started_at` existente produce edades negativas y `unknown`; AUD-06 valida contratos, índices y recuperación, pero no afirma que esa combinación temporal esté cubierta. La suite integral de 283 también pasó: es una brecha de cobertura, no una refutación del P0. |
| 233 / 276 / 283 Python; 49 / 88 / 89 frontend | Son cortes de alcance e historia, no resultados simultáneos del mismo árbol. 233/49 corresponde al cierre MP-020; 276/88 a MP-021 antes de los dos módulos MP-022 incorporados a CI; la lista CI actual cuenta 283 y el frontend actual ejecuta 89. Con `data/` disponible Python da 5 `skip`; el checkout real de CI da 18, distinción que faltaba en el primer informe. |
| Línea base `5433` e informe AUD-06 | El registro de despacho documenta un incidente de AUD-06: dos ciclos reales del colector tocaron `5433`. La línea base registrada cambió de `668/484/3/120/0` a **`895/646/8/126/8`** (posiciones / actualizaciones / alertas / ejecuciones / eventos), diferencia `+227/+162/+5/+6/+8`. Esto contradice `BACKEND_OPERATIONS_AUDIT.md:25` («usé exclusivamente» su contenedor) y `:281` («la base compartida … no se tocó»); ambas afirmaciones requieren corrección por su autor o consideración de AUD-09. AUD-08 no tocó `5433`; lo declara como antecedente ajeno, no como una acción propia. |
| «Sin skips contra desarrollo» | Ya no es reproducible como línea base: `test_real_soak_postgres` exige el conteo exacto 668, no los 895 datos actuales. No se volvió a abrir `5433` para esta auditoría, por lo que no se reclaman cifras nuevas de ejecución; se registra que la evidencia histórica de «0 skip» dejó de ser reutilizable. |
| Operación 24/7 | AUD-01, AUD-04 y AUD-06 coinciden: las capturas 1532/1533 y la ráfaga de 823,2 s/21 ciclos aportan regresiones y recuperación puntual, no una demostración de 24/7. AUD-08 no eleva esa evidencia. |

## Hallazgos

### AUD08-P2-001 — La primera exportación concurrente no es un corte atómico entre tablas

- **Identificador:** `AUD08-P2-001`.
- **Componente:** `services/snapshotter/export.py::export_service_date` /
  `export_raw_table`; relación con `services/collector/collector.py::run_cycle`.
- **Severidad:** **P2**.
- **Evidencia reproducible:** carrera real descrita arriba, contra Postgres
  aislado: al confirmar una nueva posición después del `COPY` de posiciones y
  antes de los `COPY` posteriores, el archivo inicial contiene 1 posición y 2
  ejecuciones de ingesta. El reproceso inmediato del mismo día produce 2/2.
- **Archivo/símbolo/dato afectado:** los cinco `TableSource` se exportan
  secuencialmente desde una conexión DuckDB; no hay watermark común ni una
  transacción repetible que ate todas las lecturas a una misma generación.
- **Riesgo:** quien archive explícitamente un día mientras el colector todavía
  confirma datos de ese día puede leer un histórico provisional con relaciones
  intertabla incompletas. El script normal archiva «ayer», lo cual reduce el
  riesgo operativo, pero no lo elimina para reexportaciones manuales,
  confirmaciones tardías o una planificación incorrecta.
- **Causa raíz:** aislamiento por tabla, no por exportación completa.
- **Alternativas:** (A) documentar que el archivo solo se ejecuta sobre un día
  cerrado y que cualquier reproceso tras ingesta tardía es obligatorio; (B)
  capturar un límite `source_ingestion_run.id` al comienzo y filtrar las cinco
  fuentes por él; (C) exportar bajo una instantánea PostgreSQL repetible común.
- **Recomendación:** A de inmediato y B cuando se permita archivar/reprocesar
  días con el colector activo. B mantiene el modelo actual y ofrece un límite
  auditable sin presentar una primera corrida como atómica.
- **Prueba de cierre:** repetir esta carrera y exigir que la primera exportación
  contenga o bien ambos `run` y ambas posiciones, o bien solo los elementos
  anteriores al watermark, nunca 2 `run` con 1 posición.

### AUD08-DESCARTADO-001 — Una caída de feed durante DST fabrica una fecha de servicio

- **Identificador:** `AUD08-DESCARTADO-001`.
- **Componente:** colector y `packages.movement.service_day_instant`.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** la sonda combinada registró el error sin
  observación y conservó la primera ocurrencia declarada de `02:30` local.
- **Riesgo auditado:** confundir una falla de ingesta con un dato del segundo
  pliegue de hora o con una fecha de servicio creada por inferencia.
- **Causa raíz:** no aplica; no se reprodujo.
- **Alternativas/recomendación:** conservar el tratamiento actual y añadir una
  regresión integrada si se cambia el resolvedor temporal o el supervisor.
- **Prueba de cierre:** satisfecha para la sonda aislada de AUD-08; no equivale
  a una observación de la transición DST en el feed real.

### AUD08-NO-VERIFICADO-001 — Disponibilidad continua 24/7

- **Identificador:** `AUD08-NO-VERIFICADO-001`.
- **Componente:** colector supervisado, red, PostgreSQL, disco y archivado.
- **Severidad:** **NO VERIFICADO**.
- **Evidencia disponible:** los 823,2 s/21 ciclos de MP-021 y la recuperación
  puntual de AUD-06 son útiles pero no cubren días, rotación de DNS/TLS,
  agotamiento de recursos, reinicios repetidos ni cambios de feed.
- **Qué falta:** host persistente autorizado, métricas de uptime/RSS/FD/lag/
  disco, y una ventana de al menos 24 h (preferiblemente 72 h) con fallos de
  red y base ensayados.

## Límites y limpieza

No se hicieron llamadas a Renfe/CRTM/OSM en vivo. Todas las filas adversariales
fueron sintéticas y vivieron exclusivamente en el contenedor `aud08-postgis`;
la carrera usó un directorio temporal eliminado al terminar y, antes del
recuento final, el contenedor se recreó desde cero. El contenedor se elimina al
cierre de esta tarea; no se modificó código de producto, datos persistentes ni
la base compartida.
