# ADR-0015: Archivo frío idempotente e histórico consultable por circulación

- **Estado:** `Propuesto` — aplicado de forma provisional bajo [ADR-0007](0007-autonomy-model.md). No lo promueve el ejecutor ni el revisor: solo el propietario del repositorio (`AGENTS.md`, regla 8), normalmente en el cierre de Hito 3.
- **Fecha:** 2026-11-23
- **Decisores:** Claude Opus como ejecutor de MP-021 (escalado por la asignación fija del kit en `PLAN-Y-ACEPTACION.md`: continuidad analítica sobre identidad y temporalidad); revisión cruzada aprobada por OpenAI Codex el 2026-11-23; promoción pendiente del propietario (Pedro Matute).

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
**reemplaza el subárbol `date=<fecha>`**. El resultado no puede contener restos
de una ejecución anterior y ningún otro día se toca.

**A prueba de caídas, no atómico de un solo paso** (corregido tras la revisión
de Codex). La primera versión de MP-021 borraba el subárbol anterior con
`rmtree` y renombraba encima: dos pasos con un agujero real en medio, porque
una caída entre ambos dejaba el día **borrado sin reemplazo** -- justo lo que
esta decisión existe para impedir. `rename(2)` no puede sustituir de un solo
paso un directorio destino no vacío, así que la atomicidad total de un árbol de
particiones no está disponible de forma portable y **no se afirma**. Lo que sí
se garantiza es que en ningún instante se destruye lo archivado:

1. la versión anterior se **aparta** a `.quarantine/` con un `rename` atómico;
2. la preparada ocupa el nombre definitivo con otro `rename` atómico;
3. solo entonces se borra la cuarentena.

Toda exportación empieza por `recover_interrupted_swaps`, que distingue las dos
interrupciones posibles por la sola presencia de `date=<fecha>` --falta, se
restaura desde la cuarentena; está, la cuarentena es basura y se borra-- sin
necesidad de ningún registro aparte. Por eso relanzar
`infra/operate/daily-archive.sh` tras una caída es seguro sin intervención.

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
servicio**. `scheduled` dice si el GTFS programa el viaje ese día y `observed`
si hubo al menos una `vehicle_position_observation` --cobertura de
**posición**, no "sabemos algo del viaje"--.

Una circulación observada cuyo `trip_id` no está en el calendario de ese día no
se descarta: se marca `scheduled=false`. Un viaje sin `stop_times` (huérfano)
también es fila, con el horario explícitamente ausente, para que su denominador
coincida con el de `daily_line_metrics` (5 casos reales en el ZIP oficial del
`2026-11-20`).

**No todo lo que no se ve es un hueco** (corregido tras la revisión de Codex).
La primera versión clasificaba como hueco cualquier viaje sin posición y
afirmaba que todas sus métricas eran `NULL`. Las dos cosas eran falsas en el
Parquet real del `2026-11-20`: tres viajes (`1023V20865C5`, `1023V21340C10`,
`1023V21748C2`) salían como huecos con `trip_updates_count = 1` y
`delay_reported_count = 0`. Al mirar el origen, los tres tenían una
`trip_update_observation` real con `schedule_relationship = 'CANCELED'` y
ninguna posición: **Renfe había anulado ese servicio**. Contarlos como hueco de
cobertura culpaba a nuestro colector de trenes que nunca salieron, y
`apps/api/snapshot.py` ya trataba la cancelación como ciudadana de primera
(ETA `trip_canceled`, MP-019) mientras este mart la ignoraba.

La columna `coverage` clasifica cada fila en **una sola** categoría, por orden
de prioridad, y los recuentos del día se derivan de ella:

| `coverage` | Qué significa |
|---|---|
| `unscheduled` | Observada, pero fuera del calendario del día |
| `observed` | Programada y con al menos una posición real |
| `canceled` | Programada, sin posición, anulada por el operador: el tren no circuló |
| `operator_only` | Programada, sin posición, con parte del operador: nunca se localizó |
| `unobserved` | Programada y sin ninguna señal: el hueco de cobertura real |

`canceled` se publica además como columna booleana propia, porque una
circulación puede estar anulada *y* tener posiciones, y eso no debe quedar
escondido bajo una categoría.

**Qué es `NULL` y qué es un cero medido.** La regla correcta no es "todo `NULL`
si no se observó", sino **cada métrica junto al denominador que la sostiene**:
las de posición son `NULL` exactamente cuando `observed = false`; las de
actualización de viaje lo son cuando no hubo ninguna, y si la hubo,
`delay_reported_count = 0` es un **cero medido** --hubo parte y no traía
retraso--, que es justo lo que ocurre con una cancelación porque el feed real
no publica `delay` cuando `scheduleRelationship` es `CANCELED`
(`packages/contracts/raw.py`). `on_time` es `NULL` --nunca `false`-- mientras
`delay_reported_count` sea `NULL` o `0`.

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
| **Borrar `date=<fecha>` y escribir encima** | Más simple que preparar y sustituir, pero deja una ventana en la que el día está medio escrito; si el proceso muere ahí, el archivo queda corrupto y el agregado lo leería. Es, además, el fallo exacto que tenía la primera versión de esta tarea. |
| **Indirección por enlace simbólico** para lograr atomicidad de un solo paso | Es la única vía portable de un solo paso, pero `pathlib.Path.glob("**/...")` no desciende por enlaces simbólicos en Python 3.12 y el comportamiento del `glob` de DuckDB a través de enlaces no está garantizado: cambiaría el contrato de lectura de toda la capa gold para ganar una propiedad que la cuarentena ya cubre sin romper nada. |
| **`renameat2(RENAME_EXCHANGE)` / `renamex_np(RENAME_SWAP)`** | Intercambio atómico de directorios de verdad, pero son extensiones de Linux y de macOS respectivamente, sin equivalente portable. |
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
  día, y brevemente el triple durante la sustitución (preparada + cuarentena +
  definitiva). A las magnitudes medidas (decenas de KB por día) es irrelevante.
- La sustitución **no** es atómica de un solo paso, y se documenta como lo que
  es: a prueba de caídas con recuperación automática. Un lector que consulte el
  archivo exactamente entre los dos renombrados vería el día ausente durante
  unos milisegundos; se asume, porque la alternativa portable obligaba a
  cambiar el contrato de lectura de toda la capa gold.
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
