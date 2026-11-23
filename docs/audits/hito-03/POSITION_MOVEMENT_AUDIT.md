# AUD-04 — Raw / matched / rendered y contratos temporales

**Ejecuta:** Claude Opus · High (worker Orca, contexto nuevo)
**Revisa:** Codex Sol · High (pendiente, contexto nuevo)
**Fecha:** 2026-11-23
**Rama de auditoría:** `audit/hito-03-adversarial` @ `c07fc75`
**Worktree:** `/Users/matu/orca/workspaces/madrid-pulse/audit-hito-03`
**Alcance:** `packages/movement/{engine.py,model.py,schedule.py,rendering.py}`,
`docs/adr/0014-snapshot-and-temporal-contract.md`, `apps/api/snapshot.py`,
`apps/web/src/{domain/movement.ts,domain/format.ts,map/features.ts,map/layers.ts,ui/*}`.

No se ha modificado código de producto, migraciones ni datos persistentes. No se ha
creado ningún contenedor PostgreSQL: todas las mediciones se hacen reproduciendo en
proceso la misma cadena que ejecuta `apps/api/snapshot.py` sobre los cortes reales del
kit, con reloj controlado. Los arneses viven en `scratch/aud04_*.py` y
`scratch/aud04_web/`, siguiendo la convención de AUD-01/02/03.

**La pregunta de esta auditoría no es «se mueve bonito» sino «se mueve por donde el tren
se movió de verdad, y cuando no se sabe, lo dice».**

---

## 0. Base de medida y entorno

### 0.1 Datos

| Elemento | Valor verificado |
|---|---|
| GTFS estático | `data/hito-03/replay/fomento_transit.zip`, SHA-256 del manifiesto verificado por `comprobar.py` |
| Cortes GTFS-RT | `1532` (`header.timestamp` → `2026-11-20T14:32:04Z`) y `1533` (`2026-11-20T14:33:21Z`), **77 s** de separación |
| Entidades `vehicle_positions` | 463 (corte 1532) y 468 (corte 1533); 1 por corte sin bloque `position` |
| Vehículos Madrid (`network_id="10"`) tras resolver `trip_id` | 467 en el corte 1533 |
| Patrones con corredor validado | **28 de 103** (`CorridorCoverage.can_map_match`) |
| Circulaciones del corte 1533 con cadena completa `raw → matched → rendered` | **44** |
| Sentido de los 28 corredores validados | `forward=True` en **28 de 28** |

Reproducción: `.venv/bin/python scratch/aud04_chain.py`, `scratch/aud04_identity.py`.

### 0.2 Cohortes (para no confundir hallazgos con AUD01-P0-001)

AUD-01 ya documentó que el contrato publica movimiento para trenes que todavía no han
salido. Para que los hallazgos de AUD-04 **no** dependan de ese defecto, las 44
circulaciones se separan por la posición del instante del ancla respecto a la ventana
programada del viaje (`scratch/aud04_sweep.py`):

| Cohorte | n | Definición |
|---|---|---|
| `en_ventana` | **25** | `first_departure ≤ anchor_s ≤ last_arrival`: el tren está de verdad en ruta |
| `pre_salida` | 17 | `anchor_s < first_departure` — **es exactamente el conjunto de AUD01-P0-001** |
| `post_llegada` | 2 | `anchor_s > last_arrival` |

Los hallazgos **agregados** de este documento (`AUD04-P1-001`, `AUD04-P2-002`) se dan
sobre la cohorte `en_ventana`. `AUD04-P0-001` es la excepción y se declara como tal: su
caso cae en `post_llegada`, por 141 s (ver el hallazgo). Esa excepción **no** lo acerca a
`AUD01-P0-001`, cuyo conjunto es exactamente `pre_salida`: son cohortes disjuntas y
mecanismos distintos.

### 0.3 Medidas base de la cadena

```
== distancia GPS bruto -> geometria (engine.map_match.distance_from_track_m) ==
  n=44  min=0.4  p50=2.6  p95=20.8  max=106.8 m
  por encima de off_track_distance_m=200 m: 0

== reparto de modos y metodos (ancla + 10 s, el mismo reloj de la evidencia MP-019) ==
  position_mode:    {'observed': 44}
  rendering_method: {'extrapolated_from_last_anchor': 44}
  dwell_until poblado: 0 de 44
  speed_mps envolvente: min=6.78 p50=15.65 max=30.00 (108.0 km/h)
  anomalias: {'station_skip_anomaly': 1, 'backward_jump': 1}
```

```
== velocidad implícita entre las dos observaciones reales (arco dirigido) ==
  p50 = 0.0 km/h        max = 200.5 km/h
  delta de progreso: min=-509.5 m  max=+4288.5 m
  observaciones declaradas inutilizables por el motor: 0 de 44
```

La mediana de 0,0 km/h entre los dos cortes (31 de 44 no cambiaron de posición en 77 s
reales) es coherente con lo que AUD-01 midió y es el dato que hay que tener presente al
leer el resto: **mientras los trenes reales estaban casi todos quietos, la envolvente los
conducía a 6,8–30,0 m/s.**

---

## 1. Tabla exigida: las cinco categorías de posición y cómo las comunica la interfaz

Las cinco categorías que el encargo pide distinguir, mapeadas contra lo que el producto
publica y lo que el usuario ve. Evidencia del mapeo visual:
`cd apps/web && npx vitest run --dir ../../scratch/aud04_web --silent=false`

```
┌─────────┬──────────────────────────────────────┬──────────┬───────┬────────────────┐
│ (index) │ method                               │ shape    │ glyph │ label          │
├─────────┼──────────────────────────────────────┼──────────┼───────┼────────────────┤
│ 0       │ 'anchor'                             │ 'solid'  │ '●'   │ 'Observada'    │
│ 1       │ 'interpolated_between_known_anchors' │ 'ring'   │ '◆'   │ 'Interpolada'  │
│ 2       │ 'extrapolated_from_last_anchor'      │ 'dashed' │ '▸'   │ 'Proyectada'   │
│ 3       │ 'schedule_only'                      │ 'hollow' │ '○'   │ 'Solo horario' │
│ 4       │ 'stale_frozen'                       │ 'ring'   │ '◼'   │ 'Congelada'    │
│ 5       │ 'unlocated'                          │ 'absent' │ '—'   │ 'Sin ubicar'   │
└─────────┴──────────────────────────────────────┴──────────┴───────┴────────────────┘
formas compartidas por >1 metodo: [["ring",["interpolated_between_known_anchors","stale_frozen"]]]
```

Hecho previo imprescindible para leer la tabla: **las capas de MapLibre no llevan texto.**
`apps/web/src/map/layers.ts:24-28` lo declara, y las tres expresiones de estilo
(`STROKE_COLOR:29`, `STROKE_WIDTH:43`, `CORE_RADIUS:68`) son todas
`["match", ["get", "shape"], …]`. El glifo que `features.ts:109` calcula
(`label: "${línea} ${glifo}"`) **no se consume en ninguna parte**: el único rótulo DOM
es el del vehículo seleccionado y contiene `línea · vehicle_id`
(`MapView.tsx:449`), sin procedencia. Así que sobre el mapa la procedencia viaja por
**dos** canales: `shape` y la opacidad `faded` (`layers.ts:168`, `0.55` cuando
`quality.stale`, que `snapshot.py:457` activa para `stale_frozen`/`schedule_only`/`unlocated`).

| # | Categoría del encargo | Qué la representa en el contrato | Canal visual en el mapa | Texto que ve el usuario | ¿Sin ambigüedad? |
|---|---|---|---|---|---|
| **1** | **Observación real** (GPS tal cual lo publicó Renfe) | `rendering_method="anchor"` **+** `coordinate_space="raw"` (`render_raw_anchor`, patrón sin corredor validado) | `solid` · opaco | «Observada — Coordenada de la última observación publicada por la fuente» | **NO.** Comparte método, forma, glifo y etiqueta con la categoría 2 |
| **2** | **Proyección sobre vía** (map-matched) | `rendering_method="anchor"` **+** `coordinate_space="map_matched"` | `solid` · opaco — **idéntico a la categoría 1** | El mismo texto que la 1, que aquí es **falso**: la coordenada publicada es la proyección, hasta 106,8 m medidos del GPS bruto | **NO.** Ver `AUD04-P1-002` |
| **3** | **Estimación basada en observaciones** | `extrapolated_from_last_anchor` (directo) y `interpolated_between_known_anchors` (replay/búfer) | `dashed` · opaco / `ring` · opaco | «Proyectada — Avance estimado desde la última observación; no es una lectura GPS» / «Interpolada» | **Sí para `extrapolated`.** `interpolated` es inalcanzable en el producto desplegado y su forma coincide con la de la categoría 5 (`AUD04-P2-003`) |
| **4** | **Estimación basada en horario** | `schedule_only` (`coordinate_space="schedule"`) | `hollow` · atenuado | «Solo horario — Derivada del horario, sin observación utilizable» | **Sí.** Es la única categoría con forma, opacidad y texto propios y exclusivos |
| **5** | **Información caducada o insuficiente** | `stale_frozen` y `unlocated` | `ring` · atenuado / sin coordenada | «Congelada — Última posición confirmada; la fuente dejó de actualizar» / «Sin ubicar» | **Parcialmente.** `unlocated` sí (no se dibuja). `stale_frozen` comparte `shape` con `interpolated` y solo se separa por opacidad, no por forma ni contorno — contra el principio declarado en `format.ts:11-13` («la **forma, el contorno y el texto** identifican cómo se obtuvo la posición, para que el símbolo siga siendo legible en escala de grises») |

**Veredicto de la tabla:** de las cinco categorías, **una** (la 4) se comunica sin
ambigüedad por los tres canales declarados; **dos** (1 y 2) son visual y textualmente
indistinguibles entre sí, con el agravante de que la etiqueta compartida afirma algo falso
para la categoría 2; y la 3 y la 5 colisionan en `shape`, separándose solo por opacidad.

El campo que **sí** distingue 1 de 2 existe y se publica —`rendered.coordinate_space`,
más `counts.by_coordinate_space`— y no llega a ninguna superficie que un usuario mire:
`coordinate_space` aparece una sola vez, como cadena inglesa sin traducir
(`map_matched`/`raw`/`schedule`), dentro de un `<details>` plegado rotulado «Detalle
técnico de la posición» (`TrainPanel.tsx:183-187`); `counts.by_coordinate_space` está
tipado en `contract.ts:243` y **no se renderiza en ningún componente** (comprobado por
búsqueda en todo `apps/web/src`).

Contexto que agrava la 1 contra la 2, no lo atenúa: en el snapshot real de la evidencia
de MP-019 (`docs/evidence/mp-019-tres-snapshots-replay.md:41,64,108`) los únicos métodos
presentes son `anchor` (75–78 circulaciones) y `extrapolated_from_last_anchor` (44). Los
75–78 `anchor` son precisamente los patrones **sin** corredor validado (72 de 103 siguen
`pending`): es decir, **las posiciones con menos validación geométrica de todo el sistema
reciben el símbolo más autoritativo del vocabulario** (`solid`, opaco, «Observada»),
mientras las 44 que sí tienen trazado verificado se dibujan con el símbolo discontinuo.

---

## 2. Hallazgos

### AUD04-P0-001 — La espera programada en parada solo se expresa en una ventana de ~1 m de progreso: fuera de ella la posición dibujada atraviesa la parada sin detenerse, y en este corte no se activó ni una vez

- **Identificador:** `AUD04-P0-001`
- **Componente:** `packages/movement/schedule.py` (`TripSchedule.dwell_end_seconds`) +
  `packages/movement/rendering.py` (`_envelope`). Consumido por `apps/api/snapshot.py` y
  evaluado por `apps/web/src/domain/movement.ts`.
- **Severidad:** **P0 abierto a P1** — la rama «espera programada en parada» del contrato
  **existe y es alcanzable, pero solo en una ventana de ~1 m de progreso** alrededor del
  tramo plano (medida exacta en «Ventana real de alcanzabilidad»); fuera de ella la posición
  publicada atraviesa la parada sin retener el progreso, y `rendering.py:185-187` —que
  afirma que la envolvente «la respeta de verdad (retiene el progreso)»— solo se cumple
  dentro de ese ~1 m. En este corte **no se activó ni una vez**: `dwell_until` queda a
  `None` en las 44 circulaciones, pero el denominador que importa es **0 de 1**, la única
  cuyo ancla estaba cerca de una parada con espera declarada (a 5,38 m, cinco veces la
  anchura de la ventana). **Es independiente de `AUD01-P0-001` y ninguna de las dos
  correcciones que AUD-01 recomienda lo resuelve** (ver «Relación con AUD-01»).

  **Dos correcciones de alcance aplicadas tras las revisiones de Codex Sol, que conviene
  leer antes de fijar la severidad:**
  1. La versión anterior decía «estructuralmente inalcanzable para cualquier ancla real».
     **Era una sobreafirmación.** El propio contrafactual A de este hallazgo ya demostraba
     lo contrario, y el revisor lo reprodujo con prueba propia: la rama se activa, en una
     ventana estrecha. Lo correcto es «rama extremadamente estrecha, no activada en este
     corte», no «inalcanzable».
  2. Lo que el dato observado sostiene es que el horario declara la espera y que el
     contrato no la expresó en esta ancla; **no** que exista una observación del tren
     detenido (ver «Qué sostiene el dato observado y qué no»).

  **La severidad queda deliberadamente abierta para AUD-09 / el propietario.** P0 es
  defendible como riesgo contractual —afecta a la veracidad de lo que el mapa afirma sobre
  el comportamiento ferroviario—, y es la lectura que yo mantengo; pero la evidencia
  empírica disponible (envolvente 75,2 km/h frente a 75,0 km/h realmente observados, sin
  ninguna observación de parada contradicha) sostiene con más firmeza **P1**, y el revisor
  coincide en ese análisis. Con un solo corte y una sola ancla cercana no hay base para
  cerrarlo en un sentido u otro: no lo decido yo.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud04_dwell.py
  ```
  ```
  observacion real: vehicle_id=19656 trip=1023V19656C5
    GPS bruto publicado por Renfe: lat=40.283237 lon=-3.7991464
    observed_at=2026-11-20T14:33:21+00:00  current_stop_id='35002'  current_status='INCOMING_AT'
    map-match: distancia GPS->geometria = 4.23 m; progreso dirigido del ancla = 41198.73 m

  paradas con espera declarada (arrival != departure) y su progreso proyectado:
    progreso  20428.27 m  espera   60 s (15.00h)  hueco al ancla  -20770.46 m
    progreso  41193.35 m  espera   60 s (15.45h)  hueco al ancla      -5.38 m  <== la mas cercana al ancla

  parada mas cercana al ancla: Fuenlabrada (35002); hueco ancla->tramo plano = 5.38 m
  tolerancia fijada en dwell_end_seconds: 1,0 m
    dwell_end_seconds(tolerance_m=  1.0) -> None
    dwell_end_seconds(tolerance_m=  5.0) -> None
    dwell_end_seconds(tolerance_m=  6.0) -> 55680.0

  envolvente publicada con la tolerancia real (1,0 m):
    speed_mps=20.88 (75.2 km/h)  dwell_until=None  max_progress_m=45165.5
    avance dibujado en 60 s: 1252.7 m
    avance dibujado en 190 s: 3966.7 m
    rendering_method=extrapolated_from_last_anchor
    reason='sin ancla futura: avance estimado desde la última ancla'
  ```
  El tren es el **único** de las 44 circulaciones del corte que llega a estar a menos de
  2,8 km de una parada con espera declarada: sobre las 44, el hueco al tramo plano más
  cercano tiene mínimo **5,38 m** (este caso) y segundo mínimo **2 824,6 m**
  (`scratch/aud04_sweep.py`, cohorte `en_ventana`). Es decir, el caso se midió sobre el
  único tren donde el contrato tenía que funcionar, y no funcionó.

  **Cohorte real del caso (corregida tras la revisión de Codex Sol):** este ancla **no**
  está `en_ventana` sino **`post_llegada` por 141 s** — lo verifica
  `.venv/bin/python scratch/aud04_cohorte_19656.py`:
  ```
  primera salida programada :    52200 s (14.50 h)
  ultima llegada programada :    55860 s (15.52 h)
  ancla (observed_at 1533)  :    56001 s (15.56 h)
  -> cohorte = post_llegada;  ancla - ultima_llegada = +141 s
  progreso del ancla 41198.73 m de 45165.47 m -> faltan 3966.7 m
  ```
  Esto explica de dónde sale el `speed_mps = 20,88` publicado y hay que decirlo: al estar
  141 s pasada su última llegada programada, el horario desplazado sitúa al tren ya en el
  término, así que `span_m` es **todo** el trayecto restante (3 966,7 m) y la envolvente lo
  reparte en los 190 s del horizonte → 20,87 m/s. La velocidad no es arbitraria ni
  implausible; lo que falla es que **nada la interrumpe en la parada**.

  **Dos causas, no una.** El contrafactual del mismo arnés las separa:
  ```
  --- contrafactual A: ancla exactamente en el tramo plano (41193.35 m) ---
    dwell_end_seconds(41193.35, tol=1.0) -> 55680.0
    envolvente: speed=22.07 m/s dwell_until=2026-11-20 14:34:21+00:00
    avance a 30 s: 0.0 m          <-- el mecanismo SÍ retiene cuando se activa
    avance a 90 s: 662.0 m

  --- contrafactual B: el ancla real (41198.73 m) con la espera SI detectada (tol=6 m) ---
    dwell_end_seconds(tol=6.0) = 55680; temporal_offset_s = +321
    candidate = 2026-11-20T14:33:20.756218+00:00 ; anchor_at = 2026-11-20T14:33:21+00:00
    anchor_at < candidate ? False  ->  dwell_until DESCARTADO igualmente
  ```
- **Ventana real de alcanzabilidad (añadido tras la segunda revisión de Codex Sol):**
  el revisor corrigió mi afirmación de que la rama era «estructuralmente inalcanzable para
  cualquier ancla real» —el contrafactual A de arriba ya la refutaba— y la reproduje
  barriendo el progreso del ancla alrededor del tramo plano real de Fuenlabrada:
  ```sh
  .venv/bin/python scratch/aud04_dwell_window.py
  ```
  ```
  tramo plano en 41193.35 m; ancla real del corte en 41198.73 m (+5.38 m)

   offset vs plano  dwell_end_seconds  dwell_until publicado  avance a 30 s
          -1.010 m               None                     no        452.7 m
          -1.000 m               None                     no        452.7 m
          -0.999 m              55680                     SI          0.0 m
          -0.500 m              55680                     SI          0.0 m
          +0.000 m              55680                     SI          0.0 m
          +0.010 m              55680                     no        627.2 m
          +1.000 m              55680                     no        627.0 m
          +1.010 m               None                     no        627.0 m
          +5.380 m               None                     no        626.3 m

  ventana en la que `dwell_until` SE PUEBLA: offset en [-0.999, +0.000] m  (anchura ~1 m)
    condicion 1 (dwell_end_seconds, tolerancia +-1,0 m): offset en [-1,00, +1,00]
    condicion 2 (guarda anchor_at < candidate de _envelope): recorta el lado positivo
  ```
  Las dos causas se leen aquí por separado y confirman el mecanismo ya aprobado: la
  tolerancia abre una ventana de **2 m** (`[-1, +1]`) y la guarda de `_envelope` **recorta
  todo el lado positivo**, dejando una ventana efectiva de **~1 m** (`[-0,999, 0,000]`)
  sobre un recorrido de 45 165 m. Dentro de ella la espera se honra de verdad (0,0 m de
  avance a los 30 s); fuera, el símbolo avanza 452–627 m en esos mismos 30 s.
  **Qué cambia y qué no:** la rama **no** es inalcanzable —es extremadamente estrecha— y la
  afirmación defendible es que **no se activó en este corte**, con denominador **0 de 1**
  anclas cercanas, no «0 de 44». El mecanismo del fallo, los números del caso y la
  separación frente a `AUD01-P0-001` quedan intactos: el ancla real cayó a +5,38 m,
  cinco veces fuera de la ventana.
- **Qué sostiene el dato observado y qué no (añadido tras la revisión de Codex Sol):**
  la versión anterior de este hallazgo afirmaba que el tren estaba «realmente parado
  durante 60 s». **El dato no lo sostiene y la frase estaba de más.** Lo que las dos
  observaciones reales dicen (`scratch/aud04_cohorte_19656.py`):
  ```
  corte 1532: observed_at=14:32:04Z current_status='IN_TRANSIT_TO' current_stop_id='35011'
           progreso dirigido=39595.01 m  dist_via=2.07 m
  corte 1533: observed_at=14:33:21Z current_status='INCOMING_AT'   current_stop_id='35002'
           progreso dirigido=41198.73 m  dist_via=4.23 m
  entre los dos cortes: 77 s, arco dirigido +1603.72 m, cuerda 1603.38 m -> 75.0 km/h
  ```
  - **Sostenido:** el horario programa 60 s de espera en esta parada (tramo plano a
    41 193,35 m, de 55 620 s a 55 680 s); el operador sitúa al tren **aproximándose** a esa
    misma parada (`INCOMING_AT`, `stop_id=35002`, Fuenlabrada); y el contrato publica
    `dwell_until = None`, es decir, no puede expresar esa espera.
  - **No sostenido:** que el tren estuviera detenido. Ninguna de las dos observaciones
    tiene `current_status='STOPPED_AT'`, y la anterior lo sitúa **1 603,72 m** antes, 77 s
    atrás. No se dispone de ninguna observación que confirme la parada en sí: los dos
    cortes del kit están a 77 s y la espera dura 60 s, así que puede caer entera entre
    ellos sin dejar rastro (`AUD04-NO-VERIFICADO-002`).
  - **Dato que conviene no ocultar:** la velocidad observada entre los dos cortes
    (**75,0 km/h** sobre el arco) coincide casi exactamente con la que publica la
    envolvente (**75,2 km/h**). En este caso la envolvente **no** está inventando una
    velocidad implausible; el defecto es que atraviesa una parada programada a esa
    velocidad en vez de retener el progreso, y el contrafactual A lo cuantifica: con la
    espera honrada el símbolo avanza **0 m** a los 30 s, frente a los **626,4 m** que
    avanza hoy.
- **Archivo/símbolo/dato afectado:**
  `packages/movement/schedule.py:120-133` (`dwell_end_seconds`, `tolerance_m: float = 1.0`)
  y `:106-118` (`seconds_at_progress`); `packages/movement/rendering.py:188-194`
  (detección de espera y guarda `anchor_at < candidate < horizon_end`).
  Dato: corte `data/hito-03/replay/1533`, entidad `VP_C5-19656`.
- **Riesgo de producto:** la parada en estación es el momento en que un usuario de
  Cercanías mira el mapa (está en el andén, o espera a alguien que llega). Durante los 60 s
  que el horario programa de espera en Fuenlabrada, el símbolo recorre **1 252,7 m** —se
  sale de la estación— en vez de retener el progreso, y después vuelve atrás de golpe
  cuando llega la siguiente observación. Y lo hace rotulado «Proyectada — Avance estimado
  desde la última observación», que es cierto como procedencia pero no advierte de que el
  avance contradice una espera que el propio horario declara. El efecto no es particular de
  este tren: como la ventana de activación mide ~1 m de progreso, una parada programada solo
  detiene el símbolo si el ancla cae justo en ese ~1 m, de modo que **lo esperable es que la
  mayoría de las paradas programadas no lo detengan**. Lo que este corte demuestra es el
  caso concreto (la única ancla cercana, a 5,38 m, no activó la espera); **cuantificar esa
  proporción sobre la red exige una ventana en vivo** que esta auditoría no tuvo
  (`AUD04-NO-VERIFICADO-002`).
- **Causa raíz (confirmada en código):**
  1. **Tolerancia mal calibrada por un orden de magnitud.** `dwell_end_seconds` exige que
     el progreso del ancla caiga a ≤ 1,0 m del progreso del tramo plano. El error real de
     map-matching medido en este mismo corte es p50 **2,6 m**, p95 **20,8 m**, máx
     **106,8 m** (§0.3): la condición es más estricta que la precisión del dato con el que
     se evalúa. Además, el hueco de 5,38 m de este caso no es ruido GPS sino la diferencia
     entre dos proyecciones distintas —la de la estación (`build_trip_schedule` proyecta
     `stops.txt`) y la del tren—, así que ni un GPS perfecto garantizaría < 1 m.
  2. **La guarda se autocancela.** `_envelope` sitúa el horario con
     `temporal_offset_s = anchor_s − seconds_at_progress(anchor_progress)`. Para cualquier
     ancla **posterior** al punto plano, `seconds_at_progress` devuelve el segundo de
     **salida** de la espera, de modo que el final de la espera desplazado cae en el
     instante del ancla o antes, y `anchor_at < candidate` falla. Solo sobrevive el ancla a
     la que `seconds_at_progress` devuelve la hora de **llegada** (contrafactual A), es
     decir la que cae en `[inicio_plano − 1 m, inicio_plano]`: la guarda recorta todo el
     lado positivo de la tolerancia y deja la ventana efectiva en **~1 m de los 45 165 m**
     del recorrido, medida en «Ventana real de alcanzabilidad». Es una ventana muy
     estrecha, no una imposibilidad.
- **Por qué el test de regresión no puede fallar aquí:**
  `packages/movement/tests/test_rendering.py:145`
  (`test_scheduled_dwell_holds_the_train_at_the_anchor`) construye la observación con
  `self.observation(progress_m=point.progress_m)` (`:66-77`), que genera lat/lon con
  `point_at_arc_length` **exactamente** sobre el progreso del punto de horario. El ancla
  del test tiene error de map-matching **cero** por construcción, que es justo la única
  condición bajo la cual la tolerancia de 1,0 m pasa. El test verifica que el mecanismo
  funciona cuando se le entrega un ancla imposible en la realidad.
- **Alternativas:**
  (A) Subir `tolerance_m` a un valor derivado del error medido (p. ej. p95 = 20,8 m, o el
  `off_track_distance_m` ya existente). **Insuficiente por sí sola:** el contrafactual B
  demuestra que con 6 m la espera se detecta y la guarda la descarta igualmente.
  (B) Anclar la espera por **parada**, no por progreso: el feed ya publica
  `current_stop_id` (`35002`, Fuenlabrada) y `current_status` (`INCOMING_AT`/`STOPPED_AT`),
  ambos presentes en `VehiclePositionObservation` y hoy usados solo para
  `station_skip_anomaly`. Con `stop_id` + `stop_sequence` la espera se resuelve sin
  tolerancia geométrica alguna.
  (C) Corregir la guarda: comparar el final de la espera con el instante del ancla usando
  el segundo de **llegada** del tramo plano como referencia del offset cuando el ancla cae
  dentro de la ventana de la parada, en vez del de salida.
  (D) Publicar `dwell_until` siempre que el ancla esté en la ventana de parada y dejar que
  el cliente decida. Descartable: traslada la regla al cliente, que es lo que ADR-0014 §1
  prohíbe.
- **Recomendación razonada:** **(B) como corrección principal, (C) como cierre del caso
  simétrico.** (B) es la única que no depende de un umbral geométrico: usa el dato que el
  operador ya publica sobre su propia parada, es la lectura más honesta («Renfe dice que
  este tren está llegando a Fuenlabrada y el horario declara 60 s de espera allí») y
  reutiliza campos que ya están en el contrato canónico. (A) sola no basta y además
  relajaría la tolerancia en una función que también se usa para decidir qué es un tramo
  plano. Nada de esto toca `engine.py` ni el contrato publicado: solo la traducción de
  MP-019, así que cabe dentro de ADR-0014 sin enmendarlo.
- **Relación con AUD-01 (por qué es un hallazgo separado y no el mismo):** AUD01-P0-001
  recomienda (A) acotar `temporal_offset_s` a un rango defendible y (B) detectar la ventana
  de viaje para emitir `speed_mps = 0` con `dwell_until = primera_salida` **cuando el ancla
  es anterior a la primera salida programada**. Este caso **no** lo cubre ninguna de las
  dos, y la corrección de cohorte lo deja más claro, no menos:
  - (B) no aplica: su conjunto es `pre_salida` (17 circulaciones) y `1023V19656C5` es
    `post_llegada` (+141 s). Son cohortes **disjuntas**; la comprobación de ventana que
    AUD-01 propone se dispara antes de la primera salida y no dice nada de una parada
    intermedia con espera declarada.
  - (A) no aplica: `temporal_offset_s = +321 s` (5,35 min de retraso) es físicamente
    plausible y quedaría dentro de cualquier acotación razonable —por ejemplo los 600 s de
    `operator_delay_max_age_s` que AUD-01 cita como referencia—, así que acotar el offset
    deja este caso exactamente igual.
  El mecanismo es distinto: no es un offset absurdo ni un tren sin salir, es una espera
  declarada en el horario que el contrato no puede expresar.
- **Prueba necesaria para cerrar el hallazgo:** regresión que, partiendo del **GPS bruto
  real** del corte `1533` para `19656` (`40.283237, -3.7991464`, no de un punto generado
  sobre la geometría), exija `progress_envelope.dwell_until` poblado hasta el final del
  tramo plano (`55 680 s` de día de servicio) y, con él, progreso **retenido** en el ancla
  mientras `display_at < dwell_until` (0 m de avance a los 30 s, frente a los 626,4 m
  actuales). Falla contra el código actual con `dwell_until is None`. Nótese que la
  condición correcta es «retiene», no `speed_mps == 0`: la implementación publica
  `dwell_until` **junto con** la velocidad posterior a la espera, y es ADR-0014 §2 el que
  dice lo contrario (ver `AUD04-P2-006`). Más la comprobación del caso simétrico: un ancla
  20 m **pasada** la parada debe seguir publicando la espera si la parada sigue siendo la
  actual según el operador.

---

### AUD04-P1-001 — Al caer el feed, el símbolo retrocede de golpe 2 357,9 m de mediana (hasta 3 959,2 m), y el único aviso que explicaba la congelación desaparece justo en ese instante

- **Identificador:** `AUD04-P1-001`
- **Componente:** `packages/movement/rendering.py` (`render_from_movement`, rama
  `STALE_FROZEN`) + `apps/web/src/domain/movement.ts` (`frameFor`) +
  `apps/web/src/ui/TrainPanel.tsx` (aviso `expired`).
- **Severidad:** **P1** — no se inventa una posición nueva (la congelación en el ancla es
  la decisión correcta), pero la transición es un teletransporte de kilómetros sin
  declararlo, y ocurre exactamente en el escenario que el encargo pide auditar
  («recuperación tras caída de feed»).
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud04_sweep.py
  ```
  ```
  === cohorte en_ventana: 25 circulaciones ===
    A) retroceso al cruzar stale_after_s: n>1m=25  min=1213.8 p50=2357.9 max=3959.2 m
    detalle (peores por retroceso):
      19677 1023V19677C5 ancla=98 m de 45217 m   v=22.12 m/s  179s=4058 m -> 181s=98 m (+3959 m)
      19681 1023V19681C5 ancla=98 m de 45217 m   v=22.12 m/s  179s=4058 m -> 181s=98 m (+3959 m)
      20849 1023V20849C5 ancla=4074 m de 45217 m v=19.57 m/s  179s=7578 m -> 181s=4074 m (+3503 m)
      20472 1023V20472C4b ancla=10812 m de 59276 m v=19.30 m/s 179s=14267 m -> 181s=10812 m (+3455 m)
      20280 1023V20280C4a ancla=40505 m de 48386 m v=18.76 m/s 179s=43864 m -> 181s=40505 m (+3359 m)
  ```
  **25 de 25** circulaciones en ruta retroceden más de 1 m; ninguna avanza. El barrido usa
  reloj controlado: la misma observación real como ancla, `calculated_at` a edad 179 s y a
  edad 181 s, nada más cambia.
- **Archivo/símbolo/dato afectado:**
  `packages/movement/rendering.py:284-305` (rama `STALE_FROZEN`: `progress_m` vuelve a
  `anchor_progress_m` y `valid_until=None`);
  `apps/web/src/domain/movement.ts:74-97` (`frameFor` cae a la rama `published` cuando
  `progress_envelope === null`);
  `apps/web/src/ui/TrainPanel.tsx:82-83,118-123` (el aviso `expired` depende de
  `rendered.valid_until !== null`).
- **Riesgo de producto:** la secuencia que ve el usuario cuando el feed se detiene es:
  (1) el símbolo avanza con la envolvente hasta 180 s después del ancla; (2) al pasar
  `valid_until` el cliente lo congela en su última posición dibujada y muestra el aviso
  «La vigencia de esta posición expiró […]. El símbolo queda congelado en su última
  posición autorizada»; (3) llega el siguiente snapshot, ya `stale_frozen` con
  `valid_until = null`, el aviso **desaparece** (porque su condición exige
  `valid_until !== null`) y el símbolo **salta 2,4 km hacia atrás**, rotulado «Congelada —
  Última posición confirmada; la fuente dejó de actualizar». El texto del paso (2) además
  es inexacto: la posición en la que queda congelado no es «su última posición
  autorizada», es el ancla, que puede estar kilómetros por detrás.
- **Causa raíz (confirmada en código):** `rendered` tiene dos verdades distintas sin
  transición declarada. Mientras hay envolvente, el progreso publicado es
  `anchor_progress + speed·Δt`; en cuanto el motor marca `stale`, `rendering.py:291`
  publica `progress_m = anchor_progress_m`. La consecuencia que ADR-0014 enuncia —«la
  envolvente es monótona y acotada por construcción, así que un cliente no puede hacer
  retroceder […] un tren evaluándola» (`0014:230`)— es cierta **dentro de una
  envolvente** y falsa **entre dos snapshots consecutivos**, que es donde vive el usuario.
  El contrato no publica ningún campo que marque esa discontinuidad (no hay
  `rewound_from_m`, ni un `reason` que la nombre).
- **Alternativas:**
  (A) Publicar la discontinuidad: un campo aditivo en `rendered` (p. ej.
  `previous_display_progress_m` o un `reason` específico, «posición retrocedida al
  caducar la estimación: X m») y que el cliente lo anime/declare en vez de saltar. No
  cambia ninguna decisión de posición, solo deja de ocultar un salto.
  (B) Congelar en la última posición **dibujada** en vez de en el ancla. **Descartable:**
  convierte una extrapolación en hecho, exactamente lo que
  `ANEXO-CRITICO-POSICION-Y-RELOJ.md` prohíbe y lo que `rendering.py:282-283` documenta
  haber evitado a propósito.
  (C) Que el cliente interpole el retroceso en el tiempo (deslizar en vez de saltar).
  Mitiga la sensación pero sigue dibujando un recorrido que no ocurrió, ahora hacia atrás.
  (D) Reducir el horizonte para que el retroceso máximo sea pequeño. Es la palanca que
  AUD01-P1-005 ya discute (180 s sin recalibrar); con 60 s el retroceso p50 bajaría a
  ~790 m, sigue siendo visible.
  (E) Corregir solo el aviso: hacer que la condición de `expired` no dependa de
  `valid_until` y añadir un aviso propio para `stale_frozen` que diga que la posición
  mostrada es anterior a la que se estaba dibujando.
- **Recomendación razonada:** **(E) de inmediato y (A) como corrección del contrato.**
  (E) es un cambio de interfaz de tres líneas que elimina el peor efecto —que el aviso
  explicativo desaparezca justo cuando más falta hace— sin tocar backend. (A) es la
  corrección honesta: el sistema **sabe** que ha retrocedido (tiene el ancla y tiene la
  envolvente anterior) y hoy no lo dice. (B) está descartada por principio y (D) es una
  decisión de calibración que pertenece a AUD01-P1-005, no a este hallazgo.
- **Prueba necesaria para cerrar el hallazgo:** regresión de dos pasos sobre el ancla real
  de `1023V20849C5` (corte `1533`): a edad 179 s el `rendered.progress_m` debe ser
  ≈ 7 578 m y a edad 181 s ≈ 4 074 m; el contrato debe publicar en el segundo caso un
  campo o `reason` que nombre el retroceso de 3 503 m. Más una prueba de cliente que
  compruebe que el aviso de congelación sigue visible con `valid_until === null`.

---

### AUD04-P1-002 — El mapa no distingue «observación real» de «proyección sobre vía», y la etiqueta compartida afirma que la proyección es «la coordenada que publicó la fuente»

- **Identificador:** `AUD04-P1-002`
- **Componente:** `apps/web/src/domain/format.ts` (`METHOD_STYLES`),
  `apps/web/src/map/{features.ts,layers.ts}`, `apps/web/src/ui/{Legend.tsx,TrainPanel.tsx}`.
  El contrato de backend **no** es la causa: publica lo necesario y no se usa.
- **Severidad:** **P1** — es la distinción que el anexo crítico del hito convierte en
  requisito de primer orden (`raw ≠ map_matched ≠ rendered`), y la que separa «esto es lo
  que Renfe dijo» de «esto es donde hemos decidido que cae sobre una geometría de OSM».
- **Evidencia reproducible:**
  ```sh
  cd apps/web && npx vitest run --dir ../../scratch/aud04_web --silent=false
  ```
  Salida completa en §1. Lo relevante:
  - `METHOD_STYLES` tiene **seis** entradas, una por `rendering_method`. No hay ninguna
    entrada ni modificador por `coordinate_space`.
  - `rendering_method = "anchor"` lo emiten **dos** funciones distintas con espacios de
    coordenada distintos: `render_from_movement` (`rendering.py:351-365`,
    `coordinate_space=MAP_MATCHED`) y `render_raw_anchor` (`rendering.py:405-409`,
    `coordinate_space=RAW`). Ambas caen en la misma entrada `anchor`: `solid`, `●`,
    «Observada».
  - El `detail` de esa entrada es literalmente
    `"Coordenada de la última observación publicada por la fuente"`
    (`format.ts:27`), que es cierto para `RAW` y falso para `MAP_MATCHED`: ahí la
    coordenada publicada es `_coordinate(corridor, schedule, anchor_progress)`, es decir la
    proyección, a una distancia del GPS bruto que en este corte llega a **106,8 m** (§0.3).
  - Búsqueda sobre todo `apps/web/src`: `coordinate_space` se renderiza en **un** sitio,
    `TrainPanel.tsx:186`, como cadena inglesa sin traducir dentro de un `<details>`
    plegado; `counts.by_coordinate_space` está tipado (`contract.ts:243`) y no se renderiza
    en ningún componente.
  - El canal que podría haber salvado la distinción está muerto: `features.ts:109` calcula
    `label` con el glifo y **nada lo consume** (`layers.ts:24-28` declara que las capas no
    llevan texto; el único rótulo DOM, `MapView.tsx:449`, es `línea · vehicle_id`).
- **Archivo/símbolo/dato afectado:** `apps/web/src/domain/format.ts:25-30`;
  `apps/web/src/map/features.ts:95,109`; `apps/web/src/map/layers.ts:29-80`;
  `apps/web/src/ui/Legend.tsx:30`; `apps/web/src/ui/TrainPanel.tsx:183-187`;
  `packages/movement/rendering.py:351-365` y `:405-409`.
- **Riesgo de producto:** en el snapshot real de MP-019 los dos métodos presentes son
  `anchor` (75–78) y `extrapolated_from_last_anchor` (44). Los 75–78 `anchor` son los
  patrones **sin corredor validado** —los 72 de 103 `pending`—, que se dibujan en GPS
  bruto sin ninguna verificación geométrica, y reciben el símbolo más autoritativo del
  vocabulario (`solid`, opaco, «Observada»). Un usuario no tiene forma de saber, mirando
  el mapa, si el símbolo que ve está donde Renfe dijo o donde el sistema ha decidido
  proyectarlo; y cuando sí hay proyección, el texto le dice explícitamente que es la
  coordenada de la fuente.
- **Causa raíz (confirmada):** `METHOD_STYLES` se indexa por `rendering_method`, que
  describe **cómo se obtuvo el avance** (ancla, extrapolación, horario, congelado), no
  **en qué espacio vive la coordenada**. Son dos ejes ortogonales del contrato
  —ADR-0014 §4 los separa explícitamente— y la presentación colapsó el segundo.
- **Alternativas:**
  (A) Separar los dos ejes en la presentación: un modificador visual por
  `coordinate_space` (p. ej. relleno a rayas para `raw`, relleno pleno para
  `map_matched`) y un `detail` por par (método × espacio). Mantiene los seis métodos del
  anexo y añade el eje que falta.
  (B) Mínimo viable: corregir el `detail` de `anchor` para que no afirme procedencia de
  fuente, y mostrar `coordinate_space` traducido en la ficha **fuera** del `<details>`.
  No distingue en el mapa, pero deja de mentir.
  (C) Dividir `anchor` en dos métodos de contrato (`anchor_raw` / `anchor_map_matched`).
  Descartable: el anexo fija seis valores y romper esa lista es un cambio de contrato
  innecesario cuando `coordinate_space` ya existe.
  (D) Rotular el mapa con el glifo que ya se calcula. Exigiría un servidor de glifos
  externo, que `layers.ts:24-26` descarta por una razón real (no depender de ningún
  servicio fuera de las teselas).
- **Recomendación razonada:** **(B) ya, (A) como corrección completa.** (B) elimina la
  afirmación falsa y cuesta dos líneas. (A) es la que cierra el hallazgo: el eje
  `coordinate_space` es parte del contrato porque el propio hito decidió que `raw` y
  `map_matched` no son lo mismo, y publicarlo sin mostrarlo deja la decisión arquitectónica
  sin efecto en el producto. (C) y (D) introducen coste (contrato / dependencia externa)
  para un problema que (A) resuelve con un canal visual.
- **Prueba necesaria para cerrar el hallazgo:** prueba de cliente que, dadas dos
  circulaciones con el mismo `rendering_method = "anchor"` y `coordinate_space` distinto,
  exija propiedades de estilo distintas en la `FeatureCollection` que devuelve
  `vehicleFrames`, y un texto de ficha distinto. Hoy esa prueba falla por construcción:
  ambas comparten la misma entrada de `METHOD_STYLES`.

---

### AUD04-P2-001 — `_envelope` mezcla reloj de pared con segundos reales: en los dos días de cambio de hora publica 8 444 m de avance fabricado o congela la red entera durante una hora

- **Identificador:** `AUD04-P2-001`
- **Componente:** `packages/movement/rendering.py` (`_envelope`), frente a
  `packages/movement/schedule.py` (`service_seconds` / `service_day_instant`, DEC-039).
- **Severidad:** **P2** — el defecto es real y medido, pero **hoy inalcanzable** en
  Cercanías Madrid por un margen de 60 minutos de horario que nadie declaró como guarda.
  Se clasifica como latente, no como activo.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud04_dst.py
  ```
  ```
  == 2) escala de pared vs escala real dentro de _envelope ==
    viaje usado: 1023V20202C4; horario real de 5.38h a 5.83h; 48386 m de recorrido

    dia normal           ancla UTC 2026-11-20T14:33:21+00:00 (local 15:33:21 CET)
      segundos reales entre ancla y fin de horizonte: 190
      segundos de PARED que mide service_seconds:     190
      envolvente: speed=16.93 m/s (60.9 km/h)  max_progress=+3216.5 m sobre el ancla

    atraso 2026-10-25    ancla UTC 2026-10-25T00:59:00+00:00 (local 02:59:00 CEST)
      segundos reales entre ancla y fin de horizonte: 190
      segundos de PARED que mide service_seconds:     -3410
      envolvente: speed=0.00 m/s (0.0 km/h)  max_progress=+0.0 m sobre el ancla

    adelanto 2026-03-29  ancla UTC 2026-03-29T00:59:00+00:00 (local 01:59:00 CET)
      segundos reales entre ancla y fin de horizonte: 190
      segundos de PARED que mide service_seconds:     3790
      envolvente: speed=44.44 m/s (160.0 km/h)  max_progress=+8444.4 m sobre el ancla
  ```
  En el adelanto, la envolvente satura el techo físico (`max_estimated_speed_kmh = 160`) y
  autoriza **8 444,4 m** en 190 s reales. En el atraso publica `speed_mps = 0.00` con
  `reason = "el horario no autoriza avance todavía"`, que es falso: el horario sí autoriza,
  es la aritmética la que ha retrocedido 3 410 s.
- **Alcance real (reachability), medido y no supuesto:**
  ```
  == histograma de horas de stop_times (Madrid, nucleo 10) — 1 075 798 valores ==
    00:xx 1830   01:xx 30   04:xx 170   05:xx 19181 … 23:xx 37247   24:xx 8912
  ```
  No existe **ningún** valor en `02:xx`, `03:xx`, `25:xx` ni `26:xx`. La última hora
  programada antes del salto de las 02:00 locales es `01:00` (30 valores) y el servicio
  más tardío termina en `24:53`. Para que un ancla se vea afectada su horizonte de 190 s
  tendría que cruzar las 02:00, es decir el ancla debería caer entre 01:56:50 y 02:00
  locales: **a 56 minutos del último tren**. Además, el `calendar.txt` de este ZIP tiene
  ventanas de un solo día (`start_date = end_date = 20261120`), así que
  `scheduled_trip_instances_for_date` devuelve **0 viajes** en las dos fechas de cambio de
  hora con este corte (`scratch/aud04_dst_reach.py`): el escenario no es reproducible con
  los datos del kit, solo el cálculo que lo produciría.
- **Archivo/símbolo/dato afectado:** `packages/movement/rendering.py:182`
  (`horizon_schedule_s = service_seconds(horizon_end, service_date) - temporal_offset_s`,
  con `moving_s`/`horizon_s` en segundos reales) y `:191`
  (`candidate = anchor_at + timedelta(seconds=dwell_end_s + temporal_offset_s - anchor_s)`,
  que suma una diferencia de reloj de pared como si fuera tiempo real).
- **Riesgo de producto:** acotado por el alcance anterior. Si el servicio se prolongara
  hasta las 02:00 (refuerzos de Nochevieja, eventos, o un cambio de horario comercial), la
  noche del adelanto dibujaría trenes a 160 km/h recorriendo 8,4 km en tres minutos, y la
  del atraso congelaría toda la red durante una hora con un `reason` que culpa al horario.
- **Causa raíz (confirmada):** es exactamente la familia de defecto que **DEC-039 cerró en
  otra función**. `service_day_instant` existe precisamente para convertir segundos de día
  de servicio en instantes reales respetando el desplazamiento de cada fecha, y su
  docstring documenta los dos casos límite. `_envelope` **no la usa**: hace la aritmética
  inline con `timedelta`, que es la forma ingenua que DEC-039 declara incorrecta.
  La ida y vuelta de DEC-039 sigue intacta (ver `AUD04-DESCARTADO-003`); el agujero está
  en el consumidor.
- **Alternativas:**
  (A) Usar `service_day_instant(service_date, dwell_end_s + temporal_offset_s)` para
  `candidate`, y derivar `horizon_schedule_s` convirtiendo `horizon_end` con la misma
  pareja de funciones en vez de restar segundos de pared a segundos reales. Reutiliza lo
  que ya existe y está probado.
  (B) Acotar `horizon_schedule_s − anchor_s` a `[0, horizon_s·k]` con un `k` declarado, de
  modo que cualquier discontinuidad de reloj degrade a «sin avance declarado» en vez de a
  160 km/h. Defensa en profundidad, no corrección.
  (C) Declarar la limitación y no corregirla, apoyándose en el margen de 56 minutos.
  Barato pero frágil: el margen es una propiedad del horario comercial de Renfe, no una
  guarda del sistema, y nadie la vigila.
- **Recomendación razonada:** **(A), con (B) como red.** (A) no introduce dependencias ni
  cambia el contrato y elimina la clase entera de error; (B) convierte el peor caso en una
  degradación honesta. (C) por sí sola deja un defecto de reloj dependiendo de que Renfe
  no amplíe su horario nocturno, lo que no es una garantía que este sistema controle.
- **Prueba necesaria para cerrar el hallazgo:** prueba sobre un `TripSchedule` sintético
  con paradas a `01:50`/`02:10` en `service_date = 2026-03-29` que exija
  `speed_mps ≤ max_estimated_speed_kmh/3.6` **y** `max_progress_m − anchor ≤ 190 · speed`
  coherente con 190 s reales; y la simétrica en `2026-10-25` que exija que el avance no
  sea 0 cuando el horario sí autoriza. Ambas deben fallar contra el código actual.

---

### AUD04-P2-002 — El mismo payload publica dos coordenadas distintas del mismo tren para el mismo instante: `position` y la envolvente de `rendered` discrepan hasta 429,5 m con el ancla ya estimada

- **Identificador:** `AUD04-P2-002`
- **Componente:** `packages/movement/engine.py` (`_limit_estimate`) frente a
  `packages/movement/rendering.py` (`_envelope`); publicado junto en
  `apps/api/snapshot.py` (`_legacy_position` + `_rendered_out`).
- **Severidad:** **P2** — ambas posiciones son defendibles por separado y el contrato
  declara `rendered` como aditivo; el problema es que ADR-0014 §3 afirma que un consumidor
  puede comprobar que **no se contradicen**, y sí lo hacen.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud04_sweep.py
  ```
  ```
  === cohorte en_ventana ===
    B) |envolvente - motor| con edad 61-179 s: max=429.5 p50=0.4 m
      20849 1023V20849C5: a los 61 s el cliente dibuja 5268 m, el motor publica 5698 m (-430 m)
  ```
  Con edad ≤ 60 s la discrepancia llega a **1 800,2 m** (el motor mantiene fija la
  observación en modo `observed` mientras la envolvente avanza): eso **es** el diseño de
  ADR-0014 y está declarado, así que no se cuenta como hallazgo. El hallazgo es el tramo
  61–179 s, donde **los dos están estimando a la vez con reglas distintas**: el motor con
  `_limit_estimate` (velocidad observada entre las dos últimas anclas, acotada por
  `max_estimated_speed_kmh` **y** por `max_estimated_acceleration_mps2 = 1,2`), la
  envolvente con una tasa media derivada del **horario** y **sin ningún límite de
  aceleración**.
- **Archivo/símbolo/dato afectado:** `packages/movement/engine.py:334-361`
  (`_limit_estimate`, límite de aceleración) frente a
  `packages/movement/rendering.py:196` (`speed_mps = min(span_m / moving_s, max_speed_mps)`,
  sin término de aceleración); `apps/api/snapshot.py:245-253` (`_legacy_position`) y
  `:269-292` (`_rendered_out`).
- **Riesgo de producto:** dos consumidores del mismo snapshot (p. ej. el cliente web, que
  usa `rendered`, y cualquier integración que use el bloque `position` de compatibilidad)
  dibujan el mismo tren en dos sitios separados hasta 430 m. Además, la envolvente no
  respeta el límite de aceleración del motor: en `dwell_until` el progreso pasa de retener
  a `speed_mps` de golpe (aceleración infinita en `t0`), lo que es físicamente imposible
  aunque el desplazamiento resultante quede acotado.
- **Causa raíz (confirmada):** ADR-0014 §1 establece que `rendering.py` «no reimplementa
  […] límites físicos» y reutiliza `MovementThresholds`. Reutiliza dos de los tres
  (`stale_after_s`, `max_estimated_speed_kmh`) y **no** el tercero
  (`max_estimated_acceleration_mps2`), que solo aparece en `engine.py`. La envolvente no
  es una reimplementación del motor —eso se evitó bien— pero sí es una segunda regla de
  avance con un conjunto de límites distinto.
- **Alternativas:**
  (A) Derivar `speed_mps` de modo que el progreso de la envolvente nunca exceda el que
  `_limit_estimate` autorizaría en el mismo instante (tomar el mínimo de ambas cotas).
  Hace que `rendered` sea, por construcción, consistente con `position`.
  (B) Aplicar el límite de aceleración a la envolvente añadiendo un término cuadrático.
  Rompe la forma «una sola expresión» que ADR-0014 §2 fija como requisito del contrato;
  descartable por eso.
  (C) Declarar la divergencia en el contrato (documentar que `position` y `rendered` pueden
  diferir y cuál manda). Honesto y barato, pero deja a dos consumidores dibujando distinto.
- **Recomendación razonada:** **(A), y (C) como mínimo si (A) se considera fuera de
  alcance.** (A) no cambia la forma de la envolvente (sigue siendo una recta acotada), solo
  la elección de `speed_mps`, y convierte en cierta la afirmación de ADR-0014 §3. (B) está
  descartada por el propio contrato. (C) sola deja el defecto en pie pero al menos deja de
  prometer coherencia.
- **Prueba necesaria para cerrar el hallazgo:** regresión que, para el ancla real de
  `1023V20849C5` y edades de 61 a 179 s, exija
  `|envelope.progress_at(t) − engine.position(t).progress_m| ≤ 1 m`, y que falle hoy con
  429,5 m.

---

### AUD04-P2-003 — `interpolated_between_known_anchors` es inalcanzable en el producto desplegado, y su forma visual coincide con la de `stale_frozen`

- **Identificador:** `AUD04-P2-003`
- **Componente:** `apps/api/config.py` (`display_lag_s`), `apps/api/snapshot.py`
  (`build_snapshot`), `apps/web/src/api/resources.ts` (`fetchSnapshot`),
  `apps/web/src/domain/format.ts` (`METHOD_STYLES`), `apps/web/src/ui/Legend.tsx`.
- **Severidad:** **P2** — ninguna posición se dibuja mal por esto; lo que falla es que el
  único método que puede decir honestamente «interpolada entre dos observaciones reales»
  no se emite nunca, y la leyenda lo anuncia como si pudiera aparecer.
- **Evidencia reproducible (lectura de código, sin ambigüedad):**
  - `apps/api/config.py:61`: `display_lag_s = float(os.environ.get("MADRID_PULSE_DISPLAY_LAG_S", "0"))`.
  - `apps/api/snapshot.py:638`: `display_at = now - timedelta(seconds=lag)`; con `lag = 0`,
    `display_at == now`, que siempre es posterior a `latest.observed_at`.
  - `packages/movement/rendering.py:309-313`: la rama `INTERPOLATED` exige
    `previous_anchor.observed_at < display_at < anchor_at`. Con `display_at ≥ anchor_at` es
    inalcanzable.
  - `apps/api/snapshot.py:362-364`: incluso la construcción de `previous_anchor` está
    guardada por `display_at < latest.observed_at`.
  - `apps/web/src/api/resources.ts:30-32`: `fetchSnapshot` solo envía `at`; **nunca**
    `display_lag_s`. El cliente desplegado no puede activarlo.
  - `docs/evidence/mp-019-tres-snapshots-replay.md:41,64,108`: los tres snapshots de la
    evidencia de MP-019 contienen únicamente `anchor` y `extrapolated_from_last_anchor`.
  - `scratch/aud04_web/shapes.test.ts`:
    `METHOD_STYLES.interpolated_between_known_anchors.shape === METHOD_STYLES.stale_frozen.shape`
    (`"ring"`), y `layers.ts:29-80` solo estiliza por `shape`.
- **Archivo/símbolo/dato afectado:** `apps/api/config.py:61`;
  `apps/web/src/api/resources.ts:30`; `apps/web/src/domain/format.ts:31-41,49-54`;
  `apps/web/src/ui/Legend.tsx:4-11`.
- **Riesgo de producto:** doble. (1) La `Legend` solo lista los métodos presentes
  (`Legend.tsx:22`), así que en la práctica el usuario nunca verá «Interpolada» — correcto
  por diseño, pero significa que la categoría 3-interpolada del encargo no existe en el
  producto. (2) Si alguien la habilitara (`MADRID_PULSE_DISPLAY_LAG_S > 0`, que es una
  opción documentada en `main.py:203-209`), aparecería con la **misma forma** que
  `stale_frozen`, es decir la categoría de mayor confianza (interpolación entre dos
  lecturas reales) se dibujaría igual que la de menor (dato caducado), separadas solo por
  la opacidad.
- **Causa raíz (confirmada):** la alternativa 3 de ADR-0014 se conservó «como caso
  explícito» y se implementó correctamente en backend, pero el despliegue la deja con
  `display_lag_s = 0` y el cliente no expone el parámetro. La colisión de `shape` es
  independiente: `ring` se asignó a dos métodos sin que nada lo impida.
- **Alternativas:**
  (A) Asignar a `interpolated_between_known_anchors` una `shape` propia (quinta forma) y
  añadir el caso correspondiente a las tres expresiones de `layers.ts`. Cierra la colisión
  con cuatro líneas.
  (B) Exponer `display_lag_s` en el cliente (p. ej. un ajuste «presentación suave con
  retraso declarado de 20 s»), que es la forma de hacer útil la alternativa 3 de ADR-0014
  y la única que elimina el salto del ancla sin extrapolar.
  (C) Retirar el método del vocabulario de presentación del cliente mientras sea
  inalcanzable, documentándolo. Mantiene los seis valores del contrato y evita anunciar una
  categoría muerta.
- **Recomendación razonada:** **(A) ya, y (C) o (B) según lo que el propietario quiera del
  producto.** (A) es una corrección de un defecto objetivo (dos categorías, una forma) y no
  depende de ninguna decisión de producto. Entre (B) y (C): (B) es la que daría valor real
  —el retraso de presentación declarado es la única forma honesta de movimiento continuo
  sin extrapolar, y resolvería de raíz buena parte de `AUD04-P1-001`—, pero es una decisión
  de producto (introduce 20 s de retraso para todos los usuarios) que corresponde al
  propietario, no al auditor.
- **Prueba necesaria para cerrar el hallazgo:** prueba de cliente que exija `shape`
  distinta para los seis métodos (hoy falla: dos comparten `ring`), y una prueba de
  contrato que, con `display_lag_s = 25` y dos anclas reales de los cortes `1532`/`1533`,
  exija `rendering_method == "interpolated_between_known_anchors"` para al menos una
  circulación.

---

### AUD04-P2-004 — `observed_at` no es la hora del fijo GPS sino un sello de lote del feed, y la interfaz lo rotula «GPS observado» y «última lectura confirmada»

- **Identificador:** `AUD04-P2-004`
- **Componente:** `packages/contracts/normalize.py` (`vehicle_positions_to_canonical`),
  `packages/contracts/canonical.py` (`VehiclePositionObservation.observed_at`), todo el
  contrato temporal que se apoya en él (`engine.age_s`, `rendered.anchor_age_s`,
  `last_confirmed_at`, `_envelope.temporal_offset_s`),
  `apps/web/src/ui/TrainPanel.tsx`.
- **Severidad:** **P2** — la granularidad medida (≤ 7 s) es pequeña frente a los umbrales
  de 60/180 s, así que **no reclasifica estados hoy**; lo que falla es que el producto
  presenta como instante de observación un sello que no lo es, y no acota en ninguna parte
  la latencia real entre el fijo GPS y su publicación.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python - <<'PY'
  import json; from collections import Counter; from pathlib import Path
  for cut in ("1532","1533"):
      b = json.loads(Path(f"data/hito-03/replay/{cut}/vehicle_positions.json").read_text())
      h = int(b["header"]["timestamp"])
      ts = Counter(int(e["vehicle"]["timestamp"]) for e in b["entity"])
      print(cut, "header", h, "| valores distintos:", len(ts),
            "|", {v-h: n for v, n in sorted(ts.items())})
  PY
  ```
  ```
  1532 header 1795185124 | valores distintos: 5 | {-7: 217, -6: 114, -5: 6, -2: 7, 0: 119}
  1533 header 1795185201 | valores distintos: 4 | {-4: 216, -3: 116, -2: 8, 0: 128}
  ```
  **463 entidades comparten 5 valores de `vehicle.timestamp`**, todos dentro de 7 s del
  `header.timestamp`; 217 de ellas comparten exactamente el mismo segundo y 119 llevan el
  segundo del propio encabezado. Eso no es un instante de observación por vehículo: es un
  sello asignado por lotes al ensamblar el mensaje.
- **Archivo/símbolo/dato afectado:**
  `packages/contracts/normalize.py:43` (`observed_at=epoch_to_utc(vehicle.timestamp)`);
  `packages/contracts/canonical.py:69` (comentario «UTC, del timestamp de la entidad
  vehicle»); `packages/movement/engine.py:101` (`age_s`);
  `packages/movement/rendering.py:170-171` (`anchor_s`, `temporal_offset_s`);
  `apps/web/src/ui/TrainPanel.tsx:115` («Última lectura confirmada […]») y `:223`
  («GPS observado»).
- **Riesgo de producto:** cada edad que la interfaz muestra («hace 12 s») es en realidad
  una **cota inferior** de holgura desconocida, presentada como cifra exacta. La evidencia
  cruzada de que el sello y la posición no son consistentes al segundo está en §0.3: la
  circulación `1023V20277C4a` implica **200,5 km/h** de media sobre el arco entre las dos
  observaciones reales (184,2 km/h sobre la cuerda), imposible para el material de C-4a —
  o el fijo es más antiguo que su sello, o se perdieron posiciones intermedias; el sello no
  permite distinguirlo. `docs/DATA_QUALITY.md:70` tiene un flag `clock_anomaly`, pero
  compara el sello de la fuente con el `received_at` propio, no la latencia
  fijo→publicación, que ningún campo del feed expone.
- **Causa raíz (confirmada):** `MP-003` documentó el esquema real de `vehicle_positions`
  (`docs/research/MP-003-probe-findings.md:80-96`) incluyendo el campo `timestamp`, pero
  **no** caracterizó su distribución; se asumió que era el instante de observación por
  entidad y todo el contrato temporal se construyó sobre esa lectura.
- **Alternativas:**
  (A) Renombrar la semántica en el contrato y en la interfaz: `observed_at` →
  «publicado por la fuente» / «sello de la fuente», reservando «GPS observado» para cuando
  haya un dato que lo acredite. Cambio de rótulos y de documentación, cero cambio de
  cálculo.
  (B) Publicar la granularidad medida junto a la edad (p. ej.
  `anchor_age_s` con un `anchor_age_lower_bound: true`), para que el consumidor sepa que es
  una cota.
  (C) Caracterizar la latencia con una ventana de monitorización real (varias horas) y
  documentarla en `docs/DATA_QUALITY.md` como propiedad conocida del feed, con un flag si
  se desvía.
  (D) No hacer nada: el error es ≤ 7 s y los umbrales son de 60/180 s.
- **Recomendación razonada:** **(A) y (C).** (A) es gratis y elimina una afirmación que el
  dato no sostiene, en un producto cuyo principio declarado es «observado ≠ estimado».
  (C) es el único camino para saber si la holgura real es de segundos o de minutos, y es
  exactamente el tipo de medida que `MP-003` dejó `PENDING` para otras propiedades del
  feed. (D) es defendible por magnitud pero incompatible con el estándar de honestidad que
  el proyecto se ha fijado. (B) solo si (C) confirma que la holgura es material.
- **Prueba necesaria para cerrar el hallazgo:** no es una regresión de código sino una
  medida: ventana de monitorización ≥ 2 h registrando, por ciclo,
  `header.timestamp`, el histograma de `vehicle.timestamp` y `received_at`, y una
  afirmación documentada sobre la cota de latencia. Más una prueba de cliente que exija que
  el rótulo de la ficha no diga «GPS observado» mientras esa cota no esté establecida.

---

### AUD04-P2-005 — El `implausible_speed` que publica el snapshot usa 900 km/h; el evento de calidad de 200 km/h se registra en la base y nunca llega al directo

- **Identificador:** `AUD04-P2-005`
- **Componente:** `apps/api/snapshot.py` (`quality=QualityOut(...)`),
  `packages/movement/engine.py` (`_anomalies`), frente a `packages/quality/engine.py`.
- **Severidad:** **P2** — ninguna posición se calcula mal; lo que falla es que el único
  canal de calidad que el cliente recibe usa un umbral 4,5× más alto que el que el sistema
  aplica para registrar el evento.
- **Evidencia reproducible:**
  - `apps/api/snapshot.py:462`:
    `flags = [anomaly.flag for anomaly in movement.anomalies] if movement is not None else []`,
    y `:495` `quality=QualityOut(stale=stale, flags=flags)`. Es decir, `quality.flags` del
    snapshot **son** las anomalías de `packages/movement`, nada más.
  - `packages/movement/model.py:44`: `unusable_jump_speed_kmh: float = 900.0`, usado tanto
    por `_anomalies` (`engine.py:278`) como por `_is_unusable` (`engine.py:331`).
  - `packages/quality/engine.py:27`: `implausible_speed_kmh = 200.0` (umbral que
    `AUD01-P2-015` audita por otra razón —cuerda vs arco—). Sus `data_quality_event`
    aparecen **solo** en el histórico (`apps/api/history.py:315`, campo `quality_flags`);
    búsqueda sobre `apps/api/`: ninguna referencia a `data_quality_event` en el snapshot.
  - Medida: `.venv/bin/python scratch/aud04_unusable.py` →
    `observaciones declaradas inutilizables por el motor: 0 de 44`, con una velocidad
    implícita máxima de **200,5 km/h**. Ni el flag de 900 ni la ruta de 200 (cuerda 184,2)
    producen señal alguna para ese tren en vivo.
- **Archivo/símbolo/dato afectado:** `apps/api/snapshot.py:462,495`;
  `packages/movement/model.py:44`; `packages/movement/engine.py:276-287,329-332`;
  `packages/quality/engine.py:27`; `apps/api/history.py:315`.
- **Riesgo de producto:** el sistema **sabe** —y guarda en `data_quality_event`— que una
  posición es implausible, y el usuario que mira el mapa en directo no recibe esa
  información; solo la recibiría consultando el histórico del día siguiente. Con el umbral
  del canal publicado en 900 km/h, los saltos reales que el propio proyecto documenta
  (246–787 km/h crudos en MP-008, 666,4 km/h map-matched en MP-012) pasan sin flag.
- **Causa raíz (confirmada):** el umbral de 900 km/h **es una decisión deliberada y bien
  documentada** (ADR-0004:36, DEC-010, `STATUS.md:1383`): separa el filtro de
  discontinuidad del feed del límite físico de interpolación, con el argumento correcto de
  que descartar esas observaciones eliminaría datos reales. Lo que no se decidió en ninguna
  parte es que el snapshot publicara **solo** ese canal: la separación entre «no la
  descarto» y «no te lo cuento» se produjo por omisión al construir `QualityOut`.
- **Alternativas:**
  (A) Añadir a `quality.flags` del snapshot los `data_quality_event` vigentes de la
  circulación (los del umbral de 200 km/h), manteniendo las anomalías del motor. Usa datos
  que ya están en la base.
  (B) Añadir una anomalía propia del motor con un umbral ferroviario (velocidad comercial
  máxima + margen) **sin** cambiar `unusable_jump_speed_kmh`, de modo que marcar y
  descartar sigan siendo decisiones separadas, como ADR-0004 quiere.
  (C) Documentar que el snapshot no publica los eventos de calidad y que el canal de
  directo usa 900 km/h. Barato, no mejora el producto.
- **Recomendación razonada:** **(B), con (A) si el coste de consulta es aceptable.** (B)
  respeta la decisión arquitectónica de ADR-0004 (no descartar) y recupera lo que esa
  decisión no pretendía perder (avisar), sin acoplar el snapshot a la tabla de eventos.
  (A) es más completa pero añade una consulta por circulación al camino caliente, y
  `AUD-06` ya examina el coste del snapshot. Nótese que el umbral ferroviario de (B)
  depende del histórico que `AUD01-P2-015` y DEC-033 b declaran todavía inexistente: hasta
  entonces, un valor declarado como provisional y documentado es preferible a 900.
- **Prueba necesaria para cerrar el hallazgo:** regresión que, sobre el par
  `1532`/`1533` del vehículo `20277`, exija un flag de velocidad implausible en
  `vehicles[].quality.flags` del snapshot, y que falle hoy con `flags == []`.

---

### AUD04-P2-006 — ADR-0014 §2 publica la fórmula del cliente **sin** `dwell_until` y declara `speed_mps = 0` con espera, al contrario de las tres superficies vivas

- **Identificador:** `AUD04-P2-006`
- **Componente:** `docs/adr/0014-snapshot-and-temporal-contract.md` §2.
- **Severidad:** **P2** — documentación, no código; las tres superficies vivas coinciden
  entre sí. Pero ADR-0014 es lo que lee quien implemente un cliente o quien revise el
  contrato, y seguirlo al pie de la letra produce sobrepaso durante una espera.
- **Evidencia reproducible (cuatro textos, dos versiones de la fórmula):**
  - `docs/adr/0014-snapshot-and-temporal-contract.md:78-79`:
    `progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - reference_at), max_progress_m)`
    — **`reference_at`, sin `dwell_until`**.
  - `docs/DATA_CONTRACTS.md:191-192`: `t0 = dwell_until or reference_at`. Correcto.
  - `apps/api/schemas.py:258-261` (docstring de `ProgressEnvelopeOut`):
    `t0 = dwell_until or reference_at`. Correcto.
  - `apps/web/src/domain/movement.ts:9-10,17`: `t0 = dwell_until or reference_at`, y
    `const movingFromMs = Date.parse(envelope.dwell_until ?? envelope.reference_at)`.
    Correcto.
  - `packages/movement/rendering.py:106-114` (`moving_from` / `progress_at`). Correcto.
  - Segunda incoherencia, en el mismo §2: `0014:86` afirma que
    «`speed_mps = 0` con `dwell_until` poblado es una espera declarada», mientras
    `rendering.py:196-204` publica `dwell_until` **junto con** un `speed_mps > 0` (la tasa
    con la que avanzará **después** de la espera). El contrafactual A de
    `AUD04-P0-001` lo muestra con números: `speed=22.07 m/s` y
    `dwell_until=14:34:21` en la misma envolvente.
- **Archivo/símbolo/dato afectado:** `docs/adr/0014-snapshot-and-temporal-contract.md:75-86`.
- **Riesgo de producto:** un cliente escrito contra ADR-0014 §2 avanzaría durante toda la
  espera programada (hasta 60 s × `speed_mps`, ≈ 1 324 m con los 22,07 m/s del
  contrafactual) antes de topar con `max_progress_m`. Y un revisor que compruebe
  «`dwell_until` ⇒ `speed_mps == 0`» contra la implementación concluirá, erróneamente, que
  la implementación está mal.
- **Causa raíz:** ADR-0014 se escribió antes de que la espera se materializara como
  `moving_from`; al añadir `dwell_until` se actualizaron `DATA_CONTRACTS.md`, `schemas.py`
  y el cliente, y no el ADR. El propio `rendering.py:70-74` documenta la forma correcta en
  su docstring (`hold = dwell_until or reference_at; t0 = max(reference_at, hold)`).
- **Alternativas:** (A) corregir §2 para que coincida con las otras tres superficies y
  sustituir la frase sobre `speed_mps = 0`. (B) dejarlo y apoyarse en que
  `DATA_CONTRACTS.md` es el contrato publicado. (C) Marcar §2 como superado por
  `DATA_CONTRACTS.md`.
- **Recomendación razonada:** **(A).** Es una corrección de dos líneas en un ADR que
  todavía está en estado `Propuesto` y que el propietario promocionará al cerrar el hito:
  es el momento exacto para que el texto que se promueve sea el correcto. (B) deja una
  contradicción en el documento de decisión, que es precisamente lo que un ADR existe para
  evitar.
- **Prueba necesaria para cerrar el hallazgo:** ninguna automatizable; revisión de que las
  cuatro superficies (`0014:78`, `DATA_CONTRACTS.md:192`, `schemas.py:259`,
  `movement.ts:9`) enuncian literalmente la misma fórmula.

---

### AUD04-P2-007 — Una circulación que el operador declara `CANCELED` se dibuja igual que una en marcha: el dato se publica y la interfaz no lo lee

- **Identificador:** `AUD04-P2-007`
- **Componente:** `apps/api/snapshot.py` (`_render_vehicle`, que no consulta
  `schedule_relationship`), `apps/web/src/domain/contract.ts`,
  `apps/web/src/ui/{TrainPanel.tsx,NetworkPanel.tsx}`, `apps/web/src/map/features.ts`.
- **Severidad:** **P2** — la posición en sí es una observación real (el tren existe y
  publica GPS); lo que falta es decir que su **circulación** fue anulada. **Latente en
  Madrid** con los datos del kit.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud04_canceled.py
  ```
  ```
  === corte 1533: 474 trip_updates, 468 vehicle_positions ===
    schedule_relationship: {'SCHEDULED': 465, 'CANCELED': 9}
    CANCELED **con** vehicle_position en el mismo corte: 3
      5123V77744R4 vehicle=77744 lat=41.56993 lon=2.0143688
      5123V77634R4 vehicle=77634 lat=41.47872 lon=1.9255537
      5123V28526R2 vehicle=28526 lat=41.30321 lon=2.0106592
        (sin stop_times en el GTFS cargado)
  ```
  El fenómeno —una circulación anulada que **sigue publicando posición**— es real y
  reproducible: 3 casos en el corte `1533` y 4 en el `1532`. Los siete son del núcleo `51`
  (Cataluña), así que el filtro `MADRID_PREFIX` de `services/collector/collector.py:169`
  los descarta antes de persistirlos y no llegan al snapshot de este producto. **No hay
  ningún caso de Madrid en los dos cortes.**
- **Archivo/símbolo/dato afectado:** `apps/api/snapshot.py:321-424` (`_render_vehicle`, que
  recibe `history`/`coverage`/`movement` y **no** el `trip_update`) y `:474-476` (se publica
  `schedule_relationship` en `SnapshotVehicleOut`);
  `apps/api/snapshot.py:800-831` (`build_eta`, el **único** lugar donde `CANCELED` tiene
  efecto); `apps/web/src/domain/contract.ts:201` (campo tipado) — búsqueda sobre todo
  `apps/web/src`: ningún componente lo lee.
- **Riesgo de producto:** si Renfe anula un servicio de Madrid cuyo tren sigue emitiendo
  (maniobra a cocheras, retirada de servicio con la unidad en vía), el mapa lo dibuja con
  símbolo normal, el `TrainPanel` no dice nada y la única pista es la ETA de la ficha de
  estación, donde `ETA_REASON_LABELS` traduce `trip_canceled` como «Circulación cancelada»
  (`format.ts:136`). DEC-042 estableció que la anulación es «ciudadana de primera» en el
  mart histórico; en la capa de posición en vivo no lo es.
- **Causa raíz (confirmada):** `_render_vehicle` se diseñó con la firma
  `(network, history, coverage, movement, …)`: nunca ve el `trip_update`, así que no puede
  considerar la anulación aunque quisiera. La anulación entró al contrato por la vía de la
  ETA (ADR-0014 §7) y no por la de la posición.
- **Alternativas:**
  (A) Que el cliente use `schedule_relationship`, que ya recibe: un modificador visual y un
  aviso en la ficha. Cero cambios de backend.
  (B) Que el backend lo refleje en `rendered.reason` (p. ej. «el operador declaró esta
  circulación CANCELED; la posición es real pero el servicio no circula») sin cambiar el
  método ni la coordenada.
  (C) No dibujar las anuladas. **Descartable:** el tren existe y publica posición;
  ocultarlo sería inventar una ausencia, simétrico del error que el proyecto prohíbe.
- **Recomendación razonada:** **(A), y (B) si se quiere que la causa viaje con el dato.**
  (A) es lo correcto y lo más barato: el campo ya está en el payload y en los tipos del
  cliente. (B) tiene valor para cualquier otro consumidor de la API, pero obliga a pasar el
  `trip_update` a `_render_vehicle`, un cambio de firma que conviene valorar junto con lo
  que `AUD-06` diga del camino caliente del snapshot. (C) contradice un principio del
  proyecto.
- **Prueba necesaria para cerrar el hallazgo:** prueba de cliente con una fixture de
  snapshot que tenga `schedule_relationship: "CANCELED"` y exija un aviso visible en la
  ficha y un estilo distinto en el mapa; hoy no existe ninguna fixture así
  (`apps/web/src/__fixtures__/`).

---

### AUD04-P2-008 — El `anchor_observed_at` de una posición `schedule_only` es la observación que el motor **rechazó**, y la ficha la rotula «última lectura confirmada»

- **Identificador:** `AUD04-P2-008`
- **Componente:** `packages/movement/engine.py` (`_scheduled`, parámetro
  `unusable_observed_at`), `packages/movement/rendering.py` (rama `SCHEDULE_ONLY`),
  `apps/web/src/ui/TrainPanel.tsx`.
- **Severidad:** **P2** — **latente**: 0 casos en los dos cortes. Es un rótulo incorrecto
  en una ruta real del código, no un error de posición.
- **Evidencia reproducible (lectura de código; la ruta no se activa con los datos del kit):**
  - `packages/movement/engine.py:125-134`: cuando la observación es inutilizable y no hay
    `previous` del mismo viaje, se llama a `_scheduled(..., unusable_age_s=age_s,
    unusable_observed_at=latest.observed_at)`.
  - `packages/movement/engine.py:222-235`: ese `observed_at` se publica en el
    `MovementPosition` con `position_mode = SCHEDULED`.
  - `packages/movement/rendering.py:271-272`: la rama `SCHEDULE_ONLY` publica
    `anchor_observed_at = movement.observed_at` y `anchor_age_s = movement.age_s`, con
    `last_confirmed_at = None` (correcto).
  - `apps/web/src/ui/TrainPanel.tsx:115`:
    `Última lectura confirmada {formatIsoClock(rendered.last_confirmed_at ?? rendered.anchor_observed_at)}`
    — al ser `last_confirmed_at` nulo, **cae al `anchor_observed_at` de la muestra
    rechazada** y lo rotula «última lectura confirmada».
  - Alcance medido: `scratch/aud04_unusable.py` →
    `observaciones declaradas inutilizables por el motor: 0 de 44`;
    `docs/evidence/mp-019-tres-snapshots-replay.md` no contiene ningún `schedule_only`.
- **Archivo/símbolo/dato afectado:** `packages/movement/rendering.py:271-272`;
  `apps/web/src/ui/TrainPanel.tsx:115`.
- **Riesgo de producto:** cuando la ruta se active (observación a > 200 m de la vía, o
  salto > 900 km/h, sin observación previa del mismo viaje), la ficha afirmará que la
  última lectura confirmada es precisamente la que el sistema declaró inservible, junto a
  una coordenada derivada solo del horario.
- **Causa raíz (confirmada):** el contrato distingue bien los dos conceptos
  (`last_confirmed_at` nulo = no hay lectura confirmada; `anchor_observed_at` = la
  observación relacionada, utilizable o no), y el cliente los colapsa con un `??` para
  tener siempre algo que mostrar.
- **Alternativas:** (A) en el cliente, no usar el `??`: si `last_confirmed_at` es nulo,
  mostrar «sin lectura confirmada» y, aparte, «última observación recibida (descartada):
  …». (B) en el backend, no publicar `anchor_observed_at` en `SCHEDULE_ONLY`.
  **Descartable:** el dato es útil y su ausencia perdería información real.
  (C) renombrar el campo.
- **Recomendación razonada:** **(A).** El contrato ya es correcto; el defecto es del
  cliente y se corrige en una línea sin perder información. (B) destruiría un dato
  legítimo y (C) es un cambio de contrato innecesario.
- **Prueba necesaria para cerrar el hallazgo:** prueba de cliente con una fixture
  `rendering_method: "schedule_only"`, `last_confirmed_at: null` y `anchor_observed_at`
  poblado, que exija que el texto **no** contenga «última lectura confirmada» seguido de
  esa hora.

---

## 3. Hipótesis descartadas

### AUD04-DESCARTADO-001 — «La posición GPS original se altera en el camino»

**Descartada con medida exacta.** Comparación entidad a entidad entre el JSON del feed y
`VehiclePositionObservation`, sobre la **representación decimal** y no solo el valor:

```
corte 1532: 463 entidades; sin bloque position: 1; lat/lon alteradas: 0
corte 1533: 468 entidades; sin bloque position: 1; lat/lon alteradas: 0
```

`packages/contracts/normalize.py:44-45` pasa `vehicle.position.latitude/longitude` tal
cual, sin redondeo ni normalización, y `None` cuando el bloque `position` falta (1 entidad
por corte) — nunca `(0, 0)`, como `RawPositionOut` documenta (`schemas.py:231-233`).
`apps/api/snapshot.py:485-491` publica esos mismos valores en el bloque `raw` junto al
`payload_hash` de la entidad. **El `raw` del contrato es realmente el `raw` de Renfe.**

Un aparente contraejemplo inicial resultó ser un artefacto del arnés: indexar las
observaciones por `source_vehicle_id` colapsa el vehículo `71872`, que aparece **dos
veces** en el mismo mensaje (ver `AUD04-DESCARTADO-002`). Al comparar por entidad, las
diferencias desaparecen.

### AUD04-DESCARTADO-002 — «`vehicle_id` como única clave de partición puede fusionar dos circulaciones»

**Descartada para Madrid, con residuo documentado.** `apps/api/db.py:77-80` particiona por
`source_vehicle_id` (`row_number() OVER (PARTITION BY v.source_vehicle_id ORDER BY
v.observed_at DESC, v.id DESC)`), así que el snapshot publica como máximo **una**
circulación por vehículo. La colisión es real en el feed de Renfe:

```
corte 1532: 2 entidades con vehicle.id=71872
   entity_id=VP_C5-71872 trip=6023V71872C5 ts=1795185118 pos=(43.350883,-3.707188)
   entity_id=VP_C3-71872 trip=6223V71872C3 ts=1795185118 pos=(43.350925,-3.7071903)
```

Dos viajes distintos, dos líneas distintas, el mismo `vehicle.id`, el mismo sello y 5 m de
separación. Pero **ambos son de los núcleos `60`/`62`** y
`services/collector/collector.py:169` los descarta antes de persistir. Dentro de Madrid la
colisión no se da: de **3 079** números de vehículo del GTFS de Madrid, 3 041 reaparecen en
más de un `trip_id`, pero **0 de ellos están programados el mismo día de servicio** —el
prefijo de `trip_id` (`1023V`, `1024S`, …) codifica la fecha, así que un mismo número no
sirve dos circulaciones simultáneas (`scratch/aud04_identity.py` y el conteo sobre
`scheduled_trip_instances_for_date(2026-11-20)`).

Las guardas del código son además correctas si llegara a ocurrir:
`apps/api/snapshot.py:510-515` descarta el `previous` cuyo `source_trip_id` no coincide, y
`packages/movement/engine.py:97-100` lanza `ValueError` si el `latest` pertenece a otro
viaje. **Residuo que el propietario debería conocer:** si la colisión entrara en Madrid, la
consecuencia no sería una posición mezclada sino (a) la desaparición silenciosa de una de
las dos circulaciones del mapa y (b) `previous = None` permanente para ese vehículo, lo que
anula a la vez `initial_speed_mps` en `_limit_estimate`, los flags `backward_jump` e
`implausible_speed` y la rama de rechazo por salto de `_is_unusable` —todos requieren
`previous`—. La unicidad de `vehicle_id` dentro de Madrid es, hoy, una suposición no
declarada en ninguna parte, en un repositorio cuyo `packages/contracts/nucleo.py:1-8`
advierte precisamente de que los identificadores no son únicos entre núcleos.

### AUD04-DESCARTADO-003 — «DEC-039 se puede volver a romper por la vía de `service_seconds`»

**Descartada.** La ida y vuelta `service_seconds` ↔ `service_day_instant` se barrió cada
60 s sobre las 30 h de día de servicio en las tres fechas relevantes
(`scratch/aud04_dst.py`):

```
2026-03-29: segundos que no cierran la ida y vuelta: 60 de 1800
2026-10-25: segundos que no cierran la ida y vuelta:  0 de 1800
2026-11-20: segundos que no cierran la ida y vuelta:  0 de 1800
```

Los 60 que fallan el `2026-03-29` son **exactamente** los 60 minutos de la hora
inexistente (02:00–03:00 locales), que el docstring de `service_day_instant`
(`schedule.py:60-68`) declara como caso límite resuelto a propósito y que el feed real no
puebla (0 valores en `02:xx` sobre 1 075 798 horas de `stop_times`, §`AUD04-P2-001`). La
hora ambigua del atraso cierra sin error. **DEC-039 aguanta tal como está documentado**; el
defecto de reloj que sí encontré está en el consumidor (`_envelope`), no en estas dos
funciones.

### AUD04-DESCARTADO-004 — «Los dos `progress_m` del payload están en marcos distintos y se contradicen»

**Descartada hoy, con la condición que la sostiene medida y no supuesta.** El payload
publica dos campos homónimos en marcos conceptualmente distintos:
`map_matched.progress_m` viene de `CorridorCatalog.match_position`
(`packages/geo/catalog.py:187`), que devuelve la **longitud de arco física**, mientras
`rendered.progress_m` es el **progreso dirigido** del horario
(`TripSchedule.directed_progress`). Coinciden si y solo si `forward` es verdadero. Medida:

```
patrones validados: 28 de 103
forward: {True: 28}
circulaciones donde map_matched.progress_m != rendered anchor dirigido (>1 m): 0 de 44
```

Y coinciden **por construcción, no por casualidad**: cada patrón recibe su propio corredor
orientado en su propio sentido (de los 28 validados, 25 tienen un patrón inverso en el
catálogo, y cada uno con su geometría —longitudes 48 400 m vs 48 415 m, 45 186 m vs
45 284 m—), así que `build_trip_schedule` siempre encuentra las paradas en orden creciente.
Ninguna prueba ni comentario fija esa invariante, y ni `schemas.py:249` ni `:285` declaran
el marco de referencia de su `progress_m`; eso es deuda de documentación, no un defecto
activo. Nótese que **sí hay un caso real de alguien tropezando con ella**: el arnés de
AUD-01 (`scratch/aud01_envelope_predeparture.py:97`) pasa `match.progress_m` (físico) donde
`packages/movement/engine.py:136` usa `schedule.directed_progress(...)` (dirigido) — **sus cifras
son correctas precisamente porque `forward` es `True` en los 28**, y lo dejo registrado
como verificación de AUD-01, no como corrección.

---

## 4. No verificado

### AUD04-NO-VERIFICADO-001 — Las suites de `pytest` del proyecto no se reejecutaron

`pytest` **no está instalado** en el `.venv` de este worktree y **no está declarado** en
`requirements.txt` (que lista `psycopg`, `pydantic`, `duckdb`, `fastapi`, `uvicorn`,
`httpx`). El encargo de esta auditoría prohíbe instalar software sin autorización, así que
no ejecuté `packages/movement/tests/test_{engine,rendering}.py` ni
`apps/api/tests/test_snapshot_contract.py`. Lo que sí hice fue **leer** los tests
relevantes y documentar qué condición de entrada les impide detectar
`AUD04-P0-001` (ancla generada sobre la geometría, error de map-matching cero por
construcción). La suite del cliente sí se ejecutó: `npx vitest run src/domain/movement.test.ts`
→ **10/10**, y el arnés propio de §1 → 3/3.

### AUD04-NO-VERIFICADO-002 — Comportamiento con feed en vivo y cadencia real de ~20 s

Los dos cortes del kit están a **77 s**, no a los ~20–22 s de la cadencia real medida en
MP-003: entre ellos faltan ~3 sondeos. Eso significa que (a) las velocidades implícitas de
§0.3 son **medias sobre 77 s**, no saltos de un solo paso del feed, y (b) no he podido
observar la secuencia completa de una caída y recuperación real del feed, solo
reproducirla con reloj controlado sobre anclas reales. Las magnitudes de
`AUD04-P1-001` y `AUD04-P0-001` no dependen de la cadencia (se calculan desde un ancla
única), pero la **frecuencia** con la que un usuario real vería cada efecto sí, y no la he
medido. Requiere una ventana en vivo ≥ 2 h.

### AUD04-NO-VERIFICADO-003 — Render real en MapLibre no inspeccionado en navegador

Las conclusiones de §1 y de `AUD04-P1-002`/`AUD04-P2-003` se apoyan en el código de
estilos (`layers.ts`, `styles.css`, `format.ts`, `features.ts`, `Legend.tsx`) y en un
arnés que extrae el mapeo real de `METHOD_STYLES`, no en una captura del mapa renderizado.
No he comprobado visualmente cuánto se perciben las diferencias de opacidad
(0,55 vs 1,0) frente a las de forma, ni el comportamiento en escala de grises o con
daltonismo. `AUD-05` dispone de capturas en `docs/audits/hito-03/capturas/`; la validación
perceptual de la colisión `ring`/`ring` y de la indistinción `raw`/`map_matched` queda
pendiente de una inspección en navegador.

### AUD04-NO-VERIFICADO-004 — Reproducción en PostgreSQL del camino completo del snapshot

No levanté contenedor: reproduje la cadena en proceso llamando a las mismas funciones que
`apps/api/snapshot.py` (`coverage_for_trip` → `MovementEngine.position` →
`render_from_movement`), con las dos observaciones reales de cada vehículo como
`VehicleHistory`. Queda sin verificar por mí el comportamiento de
`db.latest_vehicle_histories` sobre datos reales y, con él, el efecto exacto de la
partición por `vehicle_id` (`AUD04-DESCARTADO-002`), que he razonado sobre el SQL y no
ejecutado. `AUD-06` cubre el camino de base de datos del snapshot.

---

## 5. Resumen

| ID | Severidad | Una línea |
|---|---|---|
| `AUD04-P0-001` | **P0 abierto a P1** | La espera programada en parada solo se expresa en una ventana de ~1 m de progreso (`[-0,999, 0,000]` m respecto al tramo plano): la tolerancia es de ±1,0 m frente a un error de map-matching de p95 20,8 m y la guarda de `_envelope` recorta además todo el lado positivo, así que fuera de ese ~1 m el símbolo atraviesa la estación a 75,2 km/h (1 252,7 m en los 60 s programados) en vez de retener el progreso. No activada ni una vez en este corte: 0 de 1 anclas cercanas (la única quedó a 5,38 m). Ninguna de las dos correcciones de AUD01-P0-001 lo cubre: cohortes disjuntas (`post_llegada` +141 s vs `pre_salida`) y offset plausible (+321 s). Severidad abierta para AUD-09/propietario |
| `AUD04-P1-001` | **P1** | Al caer el feed el símbolo retrocede 2 357,9 m de mediana (25 de 25 circulaciones en ruta) y el aviso que explicaba la congelación desaparece en ese mismo instante |
| `AUD04-P1-002` | **P1** | El mapa no distingue observación real de proyección sobre vía —una sola entrada de estilo para `anchor`— y su etiqueta afirma que la proyección es «la coordenada que publicó la fuente» |
| `AUD04-P2-001` | P2 | `_envelope` mezcla reloj de pared con segundos reales: 8 444 m fabricados el 2026-03-29 y congelación de una hora el 2026-10-25. Latente: el último tren pasa 56 min antes del salto |
| `AUD04-P2-002` | P2 | `position` y `rendered` publican dos coordenadas del mismo tren para el mismo instante, hasta 429,5 m aparte, con ambas estimando |
| `AUD04-P2-003` | P2 | `interpolated_between_known_anchors` es inalcanzable con `display_lag_s = 0` y su forma visual coincide con la de `stale_frozen` |
| `AUD04-P2-004` | P2 | `observed_at` es un sello de lote del feed (4–5 valores por mensaje, ±7 s del encabezado), rotulado «GPS observado» y «última lectura confirmada» |
| `AUD04-P2-005` | P2 | El flag de velocidad implausible que publica el snapshot usa 900 km/h; el evento de 200 km/h se guarda y nunca llega al directo |
| `AUD04-P2-006` | P2 | ADR-0014 §2 publica la fórmula sin `dwell_until` y declara `speed_mps = 0` con espera, contra las tres superficies vivas |
| `AUD04-P2-007` | P2 | Una circulación `CANCELED` se dibuja igual que una en marcha: el campo se publica y ningún componente lo lee. Latente en Madrid |
| `AUD04-P2-008` | P2 | El `anchor_observed_at` de un `schedule_only` es la observación rechazada, y la ficha la llama «última lectura confirmada». Latente |
| `AUD04-DESCARTADO-001` | — | El GPS bruto no se altera: 0 de 931 entidades, comparando representación decimal |
| `AUD04-DESCARTADO-002` | — | La partición por `vehicle_id` no fusiona circulaciones de Madrid (0 de 3 079 el mismo día), con residuo documentado y una colisión real en otro núcleo |
| `AUD04-DESCARTADO-003` | — | DEC-039 aguanta: la ida y vuelta solo falla en los 60 min declarados de la hora inexistente |
| `AUD04-DESCARTADO-004` | — | Los dos marcos de `progress_m` coinciden hoy por construcción (28/28 `forward=True`); las cifras de AUD-01 quedan verificadas |
| `AUD04-NO-VERIFICADO-001..004` | — | Suites de `pytest` no reejecutadas (no instaladas ni declaradas); sin ventana en vivo; sin inspección en navegador; sin PostgreSQL |

**Respuesta a la pregunta del encargo.** Para las 28 de 103 configuraciones con corredor
validado, un tren **sí** se desplaza sobre su recorrido ferroviario real: la proyección es
correcta (p50 2,6 m del trazado), el GPS bruto se conserva intacto, el progreso se mide
sobre la longitud de arco del patrón y nunca se interpola lat/lon en recta. Pero **el
cuándo no acompaña al dónde**: la velocidad con la que recorre ese trazado se deriva del
horario sin contrastarla con el movimiento observado (mediana real 0,0 km/h entre los dos
cortes), solo expresa las esperas en estación que el propio horario declara si el ancla
cae en una ventana de ~1 m (`AUD04-P0-001`), retrocede kilómetros sin avisar cuando el feed cae
(`AUD04-P1-001`), y la interfaz no distingue las dos categorías de posición que el anexo
crítico del hito convirtió en requisito (`AUD04-P1-002`). Los tres son defectos de la capa
de traducción de MP-019, no del motor de MP-012 ni de la geometría de MP-018, y los tres se
corrigen sin enmendar ADR-0014.
