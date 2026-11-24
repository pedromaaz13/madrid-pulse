# MP-021 — Inspección real en navegador de History y Explore

Mismo estándar que [MP-020](mp-020-inspeccion-navegador.md): no se da por
funcionando nada que no se haya visto funcionar en un navegador real, con datos
reales, y los defectos encontrados mirando se corrigen y se documentan.

## Entorno

**Montado para esta tarea, no reutilizado del de MP-020.** El entorno de MP-020
(API `8010`, Vite `5181`) seguía vivo, pero sirve desde el worktree
`mp-020-mapa-y-tablero` y no tiene el código de MP-021; se dejó intacto.

| Pieza | Dónde |
|---|---|
| API | `127.0.0.1:8011`, `uvicorn apps.api.main:app` desde **este** worktree, `MADRID_PULSE_MODE=replay`, `MADRID_PULSE_SHORT_NAME=` (núcleo completo), GTFS = ZIP oficial del kit |
| Frontend | `127.0.0.1:5182`, Vite con `MADRID_PULSE_API_TARGET=http://127.0.0.1:8011`, Node **22.13.1** |
| PostgreSQL | `mp020-replay-db` en `127.0.0.1:5434` (**reutilizado**, solo lectura desde la API; recuentos `240/199/4/7/2` comprobados intactos al terminar) |
| Archivo frío | Dos días reales archivados con `python -m services.snapshotter`: `2026-11-19` (soak real de MP-007, 668 posiciones, desde la base de desarrollo `5433` en **solo lectura**) y `2026-11-20` (cortes `1532`/`1533` del kit, 240 posiciones) |
| Navegador | Chrome vía Chrome DevTools MCP |

Los dos días archivados son deliberadamente distintos entre sí, y eso es lo que
hace útil la inspección:

- **`2026-11-20`** tiene calendario GTFS y observaciones: 1 304 circulaciones
  programadas, 122 observadas, **1 182 huecos de cobertura**.
- **`2026-11-19`** tiene 668 observaciones reales y **cero** servicios
  programados, porque el `calendar.txt` del ZIP oficial empieza el día 20. Sus
  24 circulaciones son el caso "observada fuera de programación" en datos
  reales, no inventado.

## Qué se comprobó, y con qué se vio

| Captura | Qué demuestra |
|---|---|
| `01-history-c5-observadas.png` | Lista de circulaciones archivadas de la C5 del `2026-11-20`, con su identidad (`vehículo · hora prevista`), el `trip_id` real y la puntualidad **siempre con su número de reportes** |
| `02-history-huecos-cobertura.png` | El filtro «Huecos de cobertura»: cada fila dice `Programada sin observar · sin dato posición(es)` y `Sin dato de retraso`. Ningún `0` disfrazando una ausencia |
| `03-history-detalle-19656-ver-en-live.png` | Detalle de la circulación **19656** (la misma que sirvió de evidencia en MP-020): horario previsto con estaciones resueltas (Móstoles-El Soto 14:30 → Humanes 15:31), 2 posiciones archivadas, puntualidad `En hora (+5 min) · 2 reporte(s)`, las dos observaciones crudas con coordenada, y el botón **Ver en Live** |
| `04-live-tras-volver-desde-historico.png` | El resultado de pulsarlo: Live con el mapa completo de Cercanías Madrid y la **misma** circulación seleccionada (`CIRCULACIÓN 19656 · 2026-11-20`), sin traducir ninguna clave |
| `05-explore-puntualidad-con-cobertura.png` | Explore del `2026-11-20`: todo porcentaje con su fracción (`5.6 % (4/72)`, `75.0 % (3/4)`), denominador del día explícito (1 304) y la advertencia de que la cobertura mide al colector, no a la red |
| `06-explore-dia-sin-calendario-gtfs.png` | El día sin calendario: `sin muestra` en vez de `0 %`, y la explicación de que es ausencia de calendario (el GTFS de Renfe no es retroactivo), no puntualidad cero |
| `07-explore-movil-390px.png` | Explore a 390×844 real (emulación móvil con `devicePixelRatio` 3): sin desbordamiento horizontal del documento, tabla ancha desplazándose dentro de su propio contenedor |
| `08-history-movil-390px-huecos.png` | Los huecos de cobertura a 390 px, legibles y sin recortes |

### Ida y vuelta Live ↔ History, con la misma identidad

Comprobado de verdad, no deducido:

1. `?view=history&hd=2026-11-20&train=19656&trip=1023V19656C5&sd=2026-11-20`
   restaura la ficha histórica desde la URL.
2. Con el reloj de replay situado en el corte (`at=2026-11-20T14:33:21Z`), el
   snapshot vigente contiene esa misma identidad y aparece **Ver en Live**.
3. Pulsarlo navega a Live conservando los tres parámetros de identidad; el
   panel muestra `CIRCULACIÓN 19656 · 2026-11-20`.
4. **Sin** ese reloj, el snapshot vigente resuelve `service_date = 2026-11-23`
   y la misma circulación **ya no es la misma**: la interfaz dice *"Esta
   circulación no está en el snapshot vigente: no se puede abrir en Live"* en
   vez de ofrecer un salto que llevaría a una ficha vacía. Es el comportamiento
   correcto de la identidad vehículo+viaje+**día de servicio**.

### Medidas tomadas en el navegador

```text
390 px:  innerWidth=390  documentElement.scrollWidth=390  → sin desbordamiento horizontal
         .table-scroll: clientWidth=362  scrollWidth=662   → la tabla se desplaza dentro de su caja
teclado: primer tabulador → botón «Live», outline "solid 3px rgb(238,137,86)" (foco visible)
consola: 0 errores de aplicación (el único 404 de la sesión es /favicon.ico del servidor de desarrollo)
```

## Defectos reales encontrados mirando, que ningún test detectó

### 1. El rótulo del tren seleccionado se quedaba en «Sin línea» para siempre

**Síntoma:** al volver a Live desde el histórico (o al abrir cualquier enlace
con circulación ya seleccionada), el rótulo sobre el mapa decía `Sin línea ·
19656` aunque el panel mostrase correctamente la C5 y el snapshot publicase
`line: "C5"`.

**Causa real:** `MapView` leía el vehículo de `vehicleIndexRef`, un índice que
puebla el efecto de la fuente «última lectura» — y ese efecto **retorna antes
de poblarlo** mientras el estilo del mapa no está listo. Con el snapshot
llegando antes que el mapa, el rótulo se construía con el índice vacío; y como
sus dependencias (`selectedVehicleKey`, `vehicles`) no volvían a cambiar de
identidad si el siguiente sondeo traía la misma revisión, el efecto no se
repetía **nunca**.

**Corrección:** buscar el vehículo en el array `vehicles` que ya es dependencia
del efecto, no en el índice diferido. Verificado recargando: el rótulo pasa a
`C5 · 19656` (captura `04`).

### 2. Más de media pantalla en blanco en móvil en las vistas de archivo

**Síntoma:** a 390 px, History y Explore dejaban un bloque vacío de ~1 000 px
sobre el contenido.

**Causa real:** la consulta móvil de MP-020 reparte la pantalla entre mapa y
panel (`.side-panel { flex: 0 0 46% }`, `column-reverse`). En las vistas de
archivo no hay mapa, pero el panel seguía limitado al 46 %.

**Corrección:** `.app--archive` en móvil pasa el panel a `flex: 1 1 auto` y
vuelve al orden normal. Verificado (captura `07`).

### 3. El mismo día tenía dos denominadores distintos

**Síntoma:** Explore mostraba «Viajes programados (denominador) **1304**» y,
tres filas más abajo, «122 de **1299** programadas». Dos cifras con la misma
etiqueta y distinto valor en la misma pantalla.

**Causa real:** `daily_line_metrics` cuenta todos los viajes que el calendario
programa, y el mart por circulación omitía los que no tienen `stop_times`.
Verificado: son **5 viajes huérfanos reales** del ZIP oficial del `2026-11-20`
(`1023V17120C8b`, `1023V17128C8b`, `1023V17130C8b`, `1023V17134C8b`,
`1023V17707C5`).

**Corrección:** el mart por circulación los conserva como filas con el horario
**explícitamente ausente**, en vez de descartarlos. Ambas cifras valen ahora
1 304, y la interfaz dice `sin horario publicado` en esas filas con una nota que
lo explica. Fijado como regresión en
`services/snapshotter/tests/test_history.py` (el denominador del mart debe
coincidir con el de `daily_line_metrics`) y en la suite del cliente sobre la
grabación real.

### 4. Una nota de cobertura afirmaba algo falso para el otro día

**Síntoma:** en el día `2026-11-19` la interfaz decía «con dos sondeos
archivados la cobertura es baja por construcción». Ese día tuvo **120**
ejecuciones de ingesta, no dos: el texto estaba escrito a mano pensando en el
otro día.

**Corrección:** la nota se deriva ahora de los datos del propio día (la ventana
real de observación archivada), o declara que no hay ninguna observación.

---

## Segunda ronda — correcciones tras la revisión de Codex

Codex encontró **dos hallazgos bloqueantes reales** sobre la primera entrega
(`b0a1d2f`/`db3dd1a`). Los dos eran ciertos. Esto es la evidencia de su
corrección, pensada para que la re-verificación sea rápida.

### Hallazgo 1 — la sustitución no era atómica

**Lo que dijo Codex:** `services/snapshotter/export.py` hacía
`shutil.rmtree(final_partition)` **antes** de `replace()`. No es una sustitución
atómica: una caída entre ambos borra el día ya archivado sin reemplazo, que es
exactamente lo que ADR-0015/DEC-040 dicen prevenir. **Correcto.**

**Qué se cambió.** La versión anterior ya no se borra: se **aparta** a
`.quarantine/` con un `rename` atómico, la preparada ocupa el nombre definitivo
con un segundo `rename` atómico, y solo entonces se borra la cuarentena. Toda
exportación empieza por `recover_interrupted_swaps`, que resuelve una
interrupción anterior distinguiendo los dos casos por la sola presencia de
`date=<fecha>`.

**Qué se dejó de afirmar.** Ya no se dice "sustitución atómica": `rename(2)` no
puede reemplazar de un solo paso un directorio destino no vacío, y las dos vías
que sí lo lograrían se descartan con su razón en ADR-0015 (enlace simbólico:
`pathlib.Path.glob("**/...")` no desciende por enlaces en Python 3.12 y el
`glob` de DuckDB a través de enlaces no está garantizado, así que cambiaría el
contrato de lectura de toda la capa gold; `renameat2`/`renamex_np`: extensiones
de Linux y macOS sin equivalente portable). Lo que se afirma ahora, y es lo que
protege el histórico, es **a prueba de caídas con recuperación automática**.

**Prueba de inyección de fallo**, en la costura exacta — `Path.replace`
instrumentado para caer justo antes del segundo renombrado:

```text
$ python -m unittest services.snapshotter.tests.test_idempotency -v
test_a_crash_between_the_two_renames_never_destroys_the_archived_day ... ok
test_rerunning_after_a_crash_completes_the_pending_replacement ... ok
test_a_crash_after_installing_the_new_day_keeps_the_new_content ... ok
Ran 8 tests -- OK
```

El primero compara el inventario completo (ruta + SHA-256 de cada Parquet)
antes de la caída y después de la recuperación: el día archivado sobrevive
**byte a byte**, no solo "existe algo".

**Verificado también contra el mecanismo anterior**, restaurando el
`rmtree`+`replace` de la primera entrega y ejecutando los mismos tests:

```text
FAIL: test_a_crash_between_the_two_renames_never_destroys_the_archived_day
AssertionError: False is not true : la versión anterior no está en cuarentena: se ha perdido
```

Es decir: el test falla con el síntoma exacto del hallazgo cuando el defecto
está presente, y pasa cuando está corregido. (El segundo test pasa con ambos
mecanismos, porque comprueba que un reintento deja el día completo --y
reexportar desde el origen también lo consigue--; el que fija la destrucción de
datos es el primero.)

### Hallazgo 2 — huecos con métricas no nulas

**Lo que dijo Codex:** en el Parquet real del `2026-11-20` había 3 huecos
`scheduled=true/observed=false` con `trip_updates_count=1` y
`delay_reported_count=0` (no `NULL`) para `1023V21340C10`, `1023V21748C2` y
`1023V20865C5`, contradiciendo el criterio "huecos con métricas NULL, nunca 0"
que la propia entrega daba por cumplido. **Correcto.**

**Origen exacto, rastreado hasta el dato crudo.** No era un defecto de
agregación que calculase `0` en vez de `NULL`: los tres viajes tienen una
`trip_update_observation` **real** y ninguna posición.

```text
source_trip_id   observed_at   delay_seconds  delay_coverage  schedule_relationship
1023V20865C5     14:32:04Z     None           missing         CANCELED
1023V21340C10    14:32:04Z     None           missing         CANCELED
1023V21748C2     14:32:04Z     None           missing         CANCELED
  posiciones de los tres viajes: 0, 0, 0
```

**Renfe había anulado esos tres servicios.** El tren no circuló, y el operador
nos lo dijo. Clasificarlos como hueco de cobertura culpaba a nuestro colector
de trenes que nunca salieron -- y `apps/api/snapshot.py` ya trataba la
cancelación como ciudadana de primera desde MP-019 (ETA `trip_canceled`),
mientras este mart la ignoraba. El `delay_coverage='missing'` tampoco es
casual: `packages/contracts/raw.py` ya documenta que el feed real no publica
`delay` cuando `scheduleRelationship` es `CANCELED`.

**Semántica corregida y documentada.** El mart publica `canceled` y una columna
`coverage` que clasifica cada fila en **una sola** categoría:

| `coverage` | Qué significa |
|---|---|
| `unscheduled` | Observada, fuera del calendario del día |
| `observed` | Programada y con al menos una posición real |
| `canceled` | Programada, sin posición, anulada por el operador: el tren no circuló |
| `operator_only` | Programada, sin posición, con parte del operador: nunca se localizó |
| `unobserved` | Programada y sin ninguna señal: el hueco de cobertura real |

Y la regla de nulos se corrige a lo que de verdad se cumple -- **cada métrica
con el denominador que la sostiene**, no "todo `NULL` si no se observó":

- métricas de **posición** -> `NULL` exactamente cuando `observed = false`;
- métricas de **parte del operador** -> `NULL` cuando no hubo ninguna; si la
  hubo, `delay_reported_count = 0` es un **cero medido** (hubo parte y no traía
  retraso), que es justo el caso de una cancelación;
- `on_time` -> `NULL`, nunca `false`, mientras `delay_reported_count` sea
  `NULL` o `0`.

**Parquet regenerado** para los dos días archivados, y comprobado sobre él:

```text
$ /api/v1/history/days
2026-11-20: scheduled 1304 · observed 122 · unobserved 1179 · canceled 3 · operator_only 0 · unscheduled 0
2026-11-19: scheduled    0 · observed  24 · unobserved    0 · canceled 0 · operator_only 0 · unscheduled 24
  -> las cinco categorías particionan el día: 122 + 1179 + 3 = 1304

$ SELECT count(*) ... WHERE coverage='unobserved'
    AND (trip_updates_count IS NOT NULL OR delay_reported_count IS NOT NULL
         OR positions_count IS NOT NULL OR on_time IS NOT NULL)
0
```

Y sobre los **1 179 huecos completos** que devuelve la API (no una muestra),
comprobado desde el navegador: `anuladasEnElFiltroDeHuecos: 0`,
`huecosConMetricasNoNulas: 0`.

**Caso `operator_only` cubierto aunque no aparezca en estos dos días.** El
archivo actual no contiene ninguna circulación con parte del operador sin
cancelar y sin posición (`circulations_operator_only: 0`), así que se cubre con
un test sintético explícito
(`test_a_trip_update_without_position_and_without_cancellation_is_operator_only`):
no se declara verificado sobre datos que no existen.

### Defecto adicional encontrado al re-verificar en navegador

Al abrir `?view=history&hf=canceled` la vista mostraba «Todas» y 120 filas en
vez de las 3 anuladas: la lista blanca en tiempo de ejecución de
`hooks/useUrlState.ts` se quedó con las cuatro categorías antiguas y el enlace
caía en silencio a `all`. Corregido y fijado con regresión
(`acepta las cinco categorías reales de cobertura del mart`).

### Capturas de esta ronda

| Captura | Qué demuestra |
|---|---|
| `09-history-anuladas-no-son-huecos.png` | El día con las cinco categorías separadas (1 179 huecos reales / 3 anuladas), el aviso que explica por qué una anulación no es un fallo de captura, y el filtro «Anuladas» devolviendo exactamente 3 filas |
| `10-history-detalle-circulacion-anulada.png` | Detalle de `1023V20865C5`: «Anulada por el operador», «el tren no circuló. No es un hueco de captura», posiciones `sin dato`/`—` y «Actualizaciones del viaje: 1 · 0 con retraso reportado» (el cero medido, con su contexto) |
