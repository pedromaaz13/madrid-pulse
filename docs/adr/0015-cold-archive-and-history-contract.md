# ADR-0015: Archivo frío idempotente e histórico consultable por circulación

- **Estado:** `Propuesto` — aplicado de forma provisional bajo [ADR-0007](0007-autonomy-model.md). No lo promueve el ejecutor ni el revisor: solo el propietario del repositorio (`AGENTS.md`, regla 8), normalmente en el cierre de Hito 3.
- **Fecha:** 2026-11-23
- **Decisores:** Claude Opus como ejecutor de MP-021 (escalado por la asignación fija del kit en `PLAN-Y-ACEPTACION.md`: continuidad analítica sobre identidad y temporalidad); revisión cruzada de OpenAI Codex pendiente; promoción pendiente del propietario (Pedro Matute).

## Contexto

El kit de Hito 3 resume MP-021 en una frase vinculante
(`MEJORAS-PRODUCTO-VALIDADAS.md`): *"Abrir histórico con identidad/fecha de Live
y volver al contexto. Idempotencia, huecos y denominadores visibles."* Y acota
lo que **no** se construye: ni SQL Lab, ni dbt obligatorio, ni cuentas, ni
infraestructura distribuida.

El punto de partida real, verificado antes de tocar nada:

- `services/snapshotter/export.py` (MP-009) exportaba a Parquet particionado con
  `OVERWRITE_OR_IGNORE`, y su docstring lo describía como idempotente. **No lo
  era.** Medido en este hito con DuckDB 2.0: tras escribir `hour=10` (3 filas) +
  `hour=11` (2 filas) y reprocesar con una sola fila en `hour=10`, el glob del
  archivo seguía devolviendo **3 filas**; las de `hour=11` sobrevivían como
  particiones fantasma.
- `OVERWRITE` tampoco servía: medido en el mismo banco, exportar `2026-11-20`
  con `OVERWRITE` sobre `raw/<tabla>/` **borró** el `date=2026-11-19` ya
  archivado. Es destructivo a nivel de raíz.
- Los agregados de `gold.py` (MP-015) tenían el mismo conjunto de filas al
  recalcularlos pero no el mismo **orden**: sobre el catálogo completo de Madrid
  del `2026-11-20` (35 filas de línea, 69 de estación) dos corridas
  consecutivas con la misma entrada daban ficheros con SHA-256 distintos. El
  `GROUP BY` paralelo de DuckDB no garantiza orden de salida.
- `gold.py` reimplementaba el calendario GTFS a mano y solo leía `calendar.txt`
  (límite (a) de DEC-033), mientras `packages.gtfs.scheduled_service_ids_for_date`
  (MP-017) ya aplicaba las excepciones de `calendar_dates.txt`. El afectado era
  el **denominador** de toda métrica de puntualidad.
- `SnapshotterConfig` fijaba `short_name="C5"`, de modo que el mart no podía
  cubrir las 12 líneas / 42 rutas del catálogo Madrid.
- Ningún agregado existente respondía la pregunta que abre el histórico desde
  Live: *qué hizo esta circulación concreta* — vehículo + viaje + día de
  servicio, la identidad fijada por MP-017/019/020.

## Decisión

### 1. Idempotencia por preparación y sustitución, no por modo de escritura

Cada tabla se exporta a un directorio de preparación (`.staging/`, fuera del
árbol que lee la capa gold) y, solo cuando la escritura ha terminado, se
**reemplaza el subárbol `date=<fecha>`** con un `rename` del sistema de
ficheros. El resultado no puede contener restos de una ejecución anterior y
ningún otro día se toca.

Corolario explícito: **un origen vacío no borra el archivo**. Si el día no tiene
filas en la tabla hot pero sí existe archivo previo, se conserva y el resultado
lo declara (`action="preserved_existing"`). El Parquet es el almacén permanente
y la tabla hot se purga por diseño (DEC-011/NOGO-003): la ausencia de filas
calientes no es prueba de que el día no tuviera observaciones.

### 2. Los agregados se escriben con orden explícito

Los cuatro marts llevan `ORDER BY` por su clave. Un mart que no es byte-estable
no se puede verificar por hash ni comparar entre dos reprocesos, que es
exactamente lo que el criterio de aceptación exige poder hacer.

### 3. Una sola implementación del calendario

`gold.py` resuelve el calendario con `packages.gtfs.scheduled_service_ids_for_date`,
la misma función que usa el tablero de estación. El denominario del mart y el del
tablero no pueden discrepar. Cierra el límite (a) de DEC-033.

### 4. Mart nuevo por circulación, con los huecos como filas

`gold/circulation_daily_history` tiene grano **vehículo + viaje + día de
servicio** y es la unión completa de dos conjuntos, con dos banderas que dicen a
cuál pertenece cada fila:

- `scheduled`: el viaje figura en el GTFS para ese día de servicio.
- `observed`: existe al menos una `vehicle_position_observation` real.

Un servicio programado nunca observado **es una fila**, con todas sus métricas
de observación en `NULL` — nunca en `0`. Una circulación observada cuyo
`trip_id` no está en el calendario de ese día tampoco se descarta: se marca
`scheduled=false`. Un viaje sin `stop_times` (huérfano) también es fila, con el
horario explícitamente ausente, para que su denominador coincida con el de
`daily_line_metrics` (5 casos reales en el ZIP oficial del `2026-11-20`).

`on_time` es `NULL` —nunca `false`— mientras no haya ni un retraso reportado, y
`delay_reported_count`, su denominador, viaja siempre con ella.

### 5. El histórico son recursos NUEVOS, no una extensión del contrato de MP-019

`/api/v1/history/*` se sirve desde el Parquet con DuckDB en solo lectura, sin
tocar PostgreSQL ni la topología operativa. `/api/v1/snapshot` y
`/api/v1/catalog` (ADR-0014) quedan exactamente como están. Un día que no está
archivado responde `404` con el comando que lo archivaría — **nunca** un día
vacío con métricas a cero.

La identidad de la ruta de detalle es la de Live
(`/history/circulations/{vehicle_id}/{trip_id}?service_date=`), la misma que
lleva la URL del frontend (`?train=&trip=&sd=`), para que abrir el histórico
desde Live y volver no requiera traducir ninguna clave.

### 6. Operación continua **supervisada y local**, nunca "24/7 verificado"

`infra/operate/` entrega supervisor portable, agentes `launchd`, unidades
`systemd` y un medidor real. Se declara explícitamente qué no está desplegado.
Ningún servicio de pago se contrata: ADR-0007 reserva esa decisión al
propietario.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| **Dejar `OVERWRITE_OR_IGNORE` y documentar el límite** | Es justamente el criterio de aceptación de la tarea. Y el fallo no es teórico: con la tabla hot purgada o corregida, el agregado heredaba filas que ya no existen en el origen. |
| **Usar `OVERWRITE` a secas** | Medido: borra la raíz entera. Reprocesar un día se llevaría por delante todo el histórico. |
| **Borrar `date=<fecha>` y escribir encima** | Más simple que preparar y sustituir, pero deja una ventana en la que el día está medio escrito; si el proceso muere ahí, el archivo queda corrupto y el agregado lo leería. |
| **Materializar el histórico en PostgreSQL** | Contradice DEC-011/NOGO-003 (no almacenar indefinidamente cada poll en PostgreSQL) y ADR-0003 (Parquet consumido vía DuckDB). |
| **Extender `/api/v1/snapshot` con un parámetro de fecha histórica** | Mezclaría un recurso `no-store` con datos inmutables y rompería el contrato de MP-019, que el encargo prohíbe tocar. |
| **Un SQL Lab o un explorador de consultas libre** | Prohibido explícitamente por el kit para este cierre. |
| **Añadir `pytz` para materializar `TIMESTAMPTZ` de DuckDB** | Dependencia nueva evitable: la conversión explícita a UTC en SQL deja el valor en el único formato que el contrato admite. |

## Consecuencias

**A favor**

- Reprocesar un día es seguro, repetible y verificable por hash. El archivo
  diario se puede reintentar tras un fallo sin pensarlo.
- El denominador del día es uno solo y coincide entre los dos marts.
- Los huecos de cobertura son consultables (`only=unobserved`) y contados
  (`/history/days`), no una ausencia que haya que inferir.
- El mart cubre el catálogo Madrid completo por configuración, sin literales de
  línea en el código (ADR-0011).

**En contra, y asumido**

- El archivo frío ocupa el doble transitoriamente durante la preparación de un
  día. A las magnitudes medidas (decenas de KB por día) es irrelevante.
- `/api/v1/history/*` abre una conexión DuckDB por petición. Es el mismo criterio
  que DEC-038 para PostgreSQL: se mide y se documenta, no se resuelve
  introduciendo una capa de caché que podría servir un día reprocesado como si
  no lo estuviera.
- El umbral de puntualidad (`GoldThresholds.on_time_threshold_seconds = 300`)
  sigue sin calibrar: límite (b) de DEC-033, que este hito **no** cierra. Con
  dos días archivados y minutos de cobertura no hay base para calibrarlo, y
  fijarlo con esta muestra sería fabricar una calibración.
- `station_daily_metrics` sigue sin `data_quality_events_count`: límite (c) de
  DEC-033, intacto por la razón original (`entity_ref` nunca referencia una
  parada).
