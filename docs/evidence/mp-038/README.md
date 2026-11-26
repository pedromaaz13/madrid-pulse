# MP-038 · Evaluación comparable de MP-036 sobre la jornada 1

**FR-01 sigue abierto.** Donde MP-036 retiene un ancla tras rechazar el GPS A, la discrepancia mediana frente al GPS bruto B sube de **674,5 a 1 845,6 m** (216 pares con ancla retenida). En los **35 383** pares de fotogramas comunes, los saltos >200 m bajan de **2 935 a 2 771**, con **24 saltos nuevos** y **188** que bajan al umbral o por debajo. La corrección cambia el ancla confirmada en **974/35 594** fotogramas. El GPS bruto es una referencia del feed y la posición física permanece **UNVERIFIED**.

## Entradas y método

Se comparó el producto de `4bc86128d44a9b83f8f9747df5cf83ce593f0194` con el de `0c518fa9fab3e1185a95480877474742c70585b6` (incluye el delta de MP-036). Ambos procesos usaron la misma restauración, las dos ventanas de [MP-025b](../mp-025b/README.md#jornada-1-de-3--26-de-noviembre-de-2026), el catálogo completo, el mismo perfil y los **516 instantes** del arnés, con `display_lag_s=0`. Se comprobaron las vistas temporales, los relojes, la identidad de las filas brutas y las proyecciones par a par. Entraron **29 507/29 642** filas de GPS y **347** vehículos, de los cuales **135** tenían corredor. El corte del reinicio excluyó 135 filas y eliminó los 65 enlaces GPS potenciales entre segmentos. El tiempo se expresa en UTC.

1. **Discrepancia ante el GPS bruto (H1).** Valor absoluto de la envolvente propia de A evaluada a la hora GPS de B menos la proyección dirigida del GPS bruto B. El GPS B rechazado como ancla sigue en H1 si tiene proyección válida. Se aplica [la función de exclusión de MP-025b](../../../infra/operate/validation/metrics.py#L45) a cada revisión. Se publican los resultados de la población que cada revisión hace elegible y los de su intersección. H1 común exige por construcción que A sea su propia ancla en ambas revisiones. La función `identify` guarda `a.plan` solo si el snapshot confirma el propio GPS A y lo presenta en vía. Así, H1 común excluye los casos donde MP-036 retiene un ancla previa. [Código del arnés](../../../infra/operate/validation/replay.py#L54).
2. **Ancla confirmada.** Por vehículo e instante, se compara `rendered.last_confirmed_at` si hay progreso confirmado, resolviendo esa hora a una huella de GPS única del mismo vehículo y viaje dentro del segmento. Se registra cada diferencia de identidad, incluidas las apariciones o pérdidas de confirmación. Un **reanclaje** es un evento `anchor_reacquired` del motor, deduplicado por revisión, segmento, vehículo, GPS bruto y ancla confirmada. Los tres eventos tuvieron cambio de ancla en el fotograma correspondiente.
3. **Discontinuidad de presentación.** Diferencia firmada de `rendered.progress_m` entre dos instantes consecutivos del arnés en el mismo segmento, para la misma circulación y geometría map-matched. Incluye correcciones y avance ordinario entre los dos instantes. Se conserva el signo para los casos y se agregan las magnitudes. Los pares con ausencia, cambio de circulación, falta de progreso en vía o geometría distinta se excluyen. Se publican ambos denominadores propios y su intersección.

Los estratos siguen el estado del GPS bruto A y la velocidad aparente **absoluta** `|arco(B) − arco(A)| / (tB − tA)`, con tope inclusivo de **160 km/h**. Una racha al inicio significa que A repite exactamente la coordenada bruta de su predecesor consecutivo de la misma circulación en el segmento. Sin un predecesor comparable con coordenadas de ambos puntos, la racha queda indeterminada. En H1, A y B son las filas GPS del par. En fotogramas, A y B son los GPS publicados por los dos snapshots y el primero visible se atribuye a su propio estado si A falta. Sin avance de la hora GPS, intervalo fuera de (0, 180 s] o falta de una proyección comparable, la velocidad queda sin determinar. Los **180 s**, el descarte de GPS a más de **200 m** de la vía y el tope de **160 km/h** salen de [los umbrales de producción](../../../packages/movement/model.py#L42). La corrección usa profundidad **256** y **K=2**. [Configuración del historial](../../../apps/api/db.py#L17) · [Configuración del reanclaje](../../../packages/movement/engine.py#L24).

## H1 y presentación

Los cuantiles y máximos están en metros. Los recuentos de las dos últimas columnas usan el denominador `n` de cada fila.

| Medición y población | Revisión | n | p50 | p90 | p95 | Máx. | >200 m | >5 km |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H1 elegible | Base | 11 425 | 0 | 1 143,0 | 1 916,0 | 23 634,0 | 2 298 | 32 |
| H1 elegible | Corrección | 11 233 | 0 | 1 038,6 | 1 876,0 | 23 634,0 | 2 125 | 26 |
| H1 común, A aceptada por ambas revisiones | Ambas | 11 206 | 0 | 1 039,7 | 1 880,2 | 23 634,0 | 2 117 | 26 |
| H1 con B sustituido por ancla previa | Base | 310 | 2 255,6 | 3 709,3 | 6 678,6 | 23 634,0 | 310 | 23 |
| H1 con B sustituido por ancla previa | Corrección | 309 | 2 254,0 | 3 709,3 | 6 544,1 | 23 634,0 | 309 | 22 |
| Presentación elegible | Base | 35 383 | 0 | 136,0 | 462,2 | 23 634,0 | 2 935 | 50 |
| Presentación elegible | Corrección | 35 436 | 0 | 121,3 | 391,7 | 13 016,0 | 2 788 | 13 |
| Presentación común | Base | 35 383 | 0 | 136,0 | 462,2 | 23 634,0 | 2 935 | 50 |
| Presentación común | Corrección | 35 383 | 0 | 120,7 | 389,3 | 13 016,0 | 2 771 | 13 |

De **29 095** pares GPS candidatos, ambas revisiones excluyeron 17 199 sin corredor, 92 sin proyección válida, 44 por intervalo largo y uno por cambio de circulación. La falta de plan inicial excluyó **334** en la base y **526** en la corrección. De esos pares, 307 carecieron de plan en ambas, 219 solo en la corrección y 27 solo en la base. El cambio de elegibilidad explica la caída de la cola H1 en las poblaciones propias. Los 11 206 pares comunes tienen el mismo resultado H1 par a par. Los 11 254 pares consecutivos con envolvente propia de A en ambas revisiones, incluidos los que quedan fuera de H1 por otro criterio, tienen envolventes iguales. El baseline reprodujo los **33 campos de replay compartidos** con `jornada1-delta1.json`. `jump_tail` es el campo adicional de la versión del arnés usada aquí.

Hubo **91 890** pares vehículo-instante de ancla en ambas revisiones. Para la presentación, a partir de **91 890** candidatos por revisión se excluyeron **412** sin el vehículo en los dos instantes, **1** por cambio de circulación y **56 094 / 56 041** por falta de progreso map-matched. No hubo descartes por geometría distinta. En los pares de presentación comunes, **481** magnitudes bajaron, **98** subieron y **34 804** fueron iguales. Los retrocesos bajaron de **754 a 630**.

### Estratos sobre poblaciones comunes

Los denominadores de H1 y de presentación son los del cruce entre base y corrección. La columna de ancla cuenta los cambios de identidad base→corrección entre los fotogramas con una confirmación en al menos una revisión. Las tres familias marginales se solapan. El JSON contiene también los cruces estado × velocidad × racha, los cuantiles por estrato y las transiciones internas por revisión.

| Estrato | H1 >200 m base / corrección (n) | Ancla distinta / n | Presentación >200 m base / corrección (n) | Reanclajes base / corrección |
|---|---:|---:|---:|---:|
| Global | 2 117 / 2 117 (11 206) | 974 / 35 594 | 2 935 / 2 771 (35 383) | 0 / 3 |
| `STOPPED_AT` | 408 / 408 (6 894) | 184 / 16 172 | 524 / 521 (16 041) | 0 / 0 |
| `INCOMING_AT` | 189 / 189 (2 239) | 69 / 11 697 | 213 / 188 (11 668) | 0 / 0 |
| `IN_TRANSIT_TO` | 1 520 / 1 520 (2 073) | 721 / 7 725 | 2 198 / 2 062 (7 674) | 0 / 3 |
| ≤160 km/h | 1 202 / 1 202 (10 291) | 221 / 10 613 | 1 394 / 1 293 (10 602) | 0 / 3 |
| >160 km/h | 915 / 915 (915) | 16 / 1 146 | 934 / 887 (1 143) | 0 / 0 |
| Velocidad indeterminada | — (0) | 737 / 23 835 | 607 / 591 (23 638) | 0 / 0 |
| Con racha | 1 190 / 1 190 (8 754) | 466 / 26 914 | 1 486 / 1 419 (26 913) | 0 / 0 |
| Sin racha | 904 / 904 (2 281) | 505 / 8 178 | 1 413 / 1 316 (8 130) | 0 / 3 |
| Racha indeterminada | 23 / 23 (171) | 3 / 502 | 36 / 36 (340) | 0 / 0 |

La velocidad aparente quedó indeterminada en **23 835/35 594** comparaciones de ancla y en **23 638/35 383** pares comunes de presentación. En **23 580** y **23 559**, respectivamente, ambos fotogramas compartían la hora GPS (Δt=0). Los demás tenían GPS previo ausente (158 en ancla), intervalo fuera de rango (5 en cada población) o proyecciones incomparables (92 y 74). Los cortes ≤/>160 km/h cubren aproximadamente un tercio de esos totales.

### Discrepancia del ancla retenida frente al GPS B

En **219** pares que entran en H1 con la base, el GPS A de la corrección carece de envolvente propia. En **216** de esos pares la corrección conserva un ancla que ya estaba confirmada. Coinciden con los casos en los que el GPS A repite la coordenada de su predecesor. Los **3** restantes son los reanclajes de `20414`, `20418` y `19588`. Ahí la corrección confirma al llegar A una muestra anterior que había rechazado.

Para cada par se toma el snapshot del instante en que llega A. Se evalúa la envolvente propia de la base a la hora GPS de B y se contrasta con la proyección del GPS bruto B, incluidos los B rechazados. En la corrección, **189/216** tienen una envolvente del ancla retenida y **27/216** ya publican progreso congelado en vía (`stale_frozen`). Para estos 27 se usa el progreso congelado que publicó la API, constante al evaluar B. Los tres reanclajes tienen envolvente activa y se informan aparte. Esta medida adicional conserva el criterio histórico de H1.

| Población | n | p50 base → corrección (m) | >200 m base → corrección | >5 km base → corrección | Aumenta / disminuye |
|---|---:|---:|---:|---:|---:|
| Ancla retenida tras rechazar A | 216 | 674,5 → 1 845,6 | 179 → 163 | 6 → 24 | 127 / 89 |
| De ellos, B cambia de coordenada | 103 | 2 079,4 → 110,7 | 103 → 50 | 6 → 0 | 14 / 89 |
| De ellos, B repite la coordenada de A | 113 | 263,4 → 3 141,4 | 76 → 113 | 0 → 24 | 113 / 0 |
| Reanclajes al llegar A | 3 | 257,5 → 11,9 | 2 → 0 | 0 → 0 | 1 / 2 |
| Total con A sin envolvente propia | 219 | 672,4 → 1 721,0 | 181 → 163 | 6 → 24 | 128 / 91 |

El cruce se puede reproducir en `gps.retained_anchor_discrepancy.cases`. Los casos de retención llevan `streak/frozen` y, según B cambie o repita la coordenada de A, `next_gps/changed` o `next_gps/frozen` en `strata`. Para identificar los tres reanclajes, se cruza por segmento, vehículo, hora GPS de A y hora del ancla anterior con `reanchors`. La distinción separa una coordenada que cambia en el feed de una observación del movimiento físico.

En `20428`, el GPS repitió **40,644844 / −3,7762609**, a **32,47 m** de progreso, mientras la corrección mostraba un ancla de las **08:11:52** a **10 803,32 m**. En **12** pares consecutivos con A desde **08:13:10** y B hasta **08:19:10**, la discrepancia de la corrección fue **10 770,85 m**. La base alternó entre **600,06** y **1 200,12 m** en esos pares. Cuando el GPS cambió a **10 812,11 m** a las **08:19:51**, la discrepancia del par bajó de **9 549,51 a 8,79 m**.

### Aumentos, reducciones y cruces de 200 m en presentación

Los cruces usan la magnitud del salto. Un salto de 200 m exactos pertenece al lado ≤200 m. Las columnas de cruces son subconjuntos de las columnas de cambio de magnitud. Los recuentos por estado, velocidad y racha usan los mismos pares comunes de la tabla anterior. El JSON conserva todos los cruces con signo, vehículo, hora y estrato, y los agregados del cruce estado × velocidad × racha.

| Estrato | Aumentan | Disminuyen | Iguales | ≤200 → >200 m | >200 → ≤200 m |
|---|---:|---:|---:|---:|---:|
| Global | 98 | 481 | 34 804 | 24 | 188 |
| `STOPPED_AT` | 32 | 23 | 15 986 | 9 | 12 |
| `INCOMING_AT` | 8 | 41 | 11 619 | 2 | 27 |
| `IN_TRANSIT_TO` | 58 | 417 | 7 199 | 13 | 149 |
| ≤160 km/h | 32 | 215 | 10 355 | 15 | 116 |
| >160 km/h | 2 | 89 | 1 052 | 0 | 47 |
| Velocidad indeterminada | 64 | 177 | 23 397 | 9 | 25 |
| Con racha | 91 | 319 | 26 503 | 24 | 91 |
| Sin racha | 7 | 160 | 7 963 | 0 | 97 |
| Racha indeterminada | 0 | 2 | 338 | 0 | 0 |

`STOPPED_AT` es el único estado con más magnitudes que suben que bajan (32 frente a 23). Entre los 24 saltos nuevos figuran `20217` (06:33:52, de 0 a +408,8 m), `20741` (07:37:44, de +116,5 a +405,8 m) y `19571` (07:41:20, de −98,3 a +404,4 m).

<details>
<summary>Los 24 cruces de ≤200 a >200 m</summary>

| Fotograma UTC | Vehículo | Estado inicial | Salto base → corrección (m) |
|---|---|---|---:|
| 06:05:30 | `20709` | `STOPPED_AT` | 0 → +301,8 |
| 06:07:30 | `20414` | `STOPPED_AT` | 0 → +281,6 |
| 06:33:52 | `20217` | `INCOMING_AT` | 0 → +408,8 |
| 06:35:00.841790 | `20416` | `INCOMING_AT` | 0 → +366,6 |
| 07:36:43.172404 | `20741` | `STOPPED_AT` | +140,8 → +405,2 |
| 07:37:13.997817 | `20741` | `IN_TRANSIT_TO` | -98,0 → +404,8 |
| 07:37:44.898184 | `20741` | `IN_TRANSIT_TO` | +116,5 → +405,8 |
| 07:41:20.811493 | `19571` | `IN_TRANSIT_TO` | -98,3 → +404,4 |
| 07:53:41.465243 | `20239` | `IN_TRANSIT_TO` | -97,0 → +400,8 |
| 08:12:11.503116 | `20755` | `IN_TRANSIT_TO` | -26,7 → +256,1 |
| 08:12:30 | `20755` | `IN_TRANSIT_TO` | +197,7 → +242,9 |
| 08:18:51.881163 | `20761` | `IN_TRANSIT_TO` | +20,1 → +287,3 |
| 08:24:30.415029 | `20767` | `IN_TRANSIT_TO` | +25,8 → +268,1 |
| 08:29:30 | `20428` | `STOPPED_AT` | 0 → +322,2 |
| 08:30:14.261149 | `20428` | `STOPPED_AT` | 0 → +319,5 |
| 08:30:30 | `20428` | `STOPPED_AT` | 0 → +225,9 |
| 08:35:10 | `20434` | `STOPPED_AT` | 0 → +267,6 |
| 08:35:52.826443 | `20434` | `STOPPED_AT` | 0 → +327,6 |
| 08:36:10 | `20434` | `STOPPED_AT` | 0 → +246,5 |
| 08:44:35.537182 | `20775` | `IN_TRANSIT_TO` | -143,9 → +335,3 |
| 08:44:51 | `20775` | `IN_TRANSIT_TO` | +165,2 → +203,0 |
| 08:45:06.295392 | `20775` | `IN_TRANSIT_TO` | -61,0 → +200,8 |
| 08:45:37.044307 | `20775` | `IN_TRANSIT_TO` | -88,2 → +403,8 |
| 08:52:16.668839 | `20247` | `IN_TRANSIT_TO` | -124,5 → +400,3 |

</details>

| Vehículo con más saltos >200 m en pares comunes | Base → corrección |
|---|---:|
| `20741` | 6 → 8 |
| `20775` | 42 → 45 |
| `20434` | 38 → 41 |
| `20709` | 7 → 8 |
| `20416` | 27 → 28 |
| `20239` | 54 → 55 |
| `20247` | 14 → 15 |
| `20217` | 30 → 31 |

En `20741`, la suma de magnitudes en sus 514 pares comunes también aumenta **37,3 m**. En los otros siete vehículos baja la suma, aunque aumente el recuento de saltos >200 m.

**Pares medibles solo en la corrección.** En los **53** pares, la base produjo `schedule_only` en uno o ambos extremos (31 y 22 pares, respectivamente), con posición derivada del horario y sin ancla confirmada. En cada extremo afectado constaba `off_track`, a veces junto con `backward_jump` o `implausible_speed`. El historial de la corrección le permite publicar progreso en vía en esos extremos, a partir del ancla retenida o de una nueva confirmación. El máximo de **2 245,5 m** fue `20788` a las **08:49:43,030124**, al confirmar su GPS de **08:49:30**. En ese instante la base conservó solo la posición derivada del horario. Otros casos fueron `20767` (2 204,0 m) y `19589` (2 071,2 m). Los **17/53** por encima de 200 m explican el paso de **2 771/35 383** saltos en los pares comunes a **2 788/35 436** en toda la población medible de la corrección. Para la base, la magnitud en esos 53 pares queda indeterminada.

## Identidad del ancla y episodios adversos

De los **35 594** fotogramas con al menos un ancla confirmada, **34 620** conservaron la identidad, **907** pasaron a un ancla más antigua, **29** a una más reciente y **38** ganaron una confirmación. En otros **56 296** fotogramas, ambas revisiones carecían de confirmación. En los 907 con ancla más antigua, la diferencia de hora tuvo mediana **60 s**, p90 **140 s** y máximo **438 s** (`20428`, fotograma de las 08:19:22,588404). Entre los **91 477** pasos dentro de una misma circulación visible en ambos instantes, la base y la corrección adelantaron el ancla **11 471 / 11 279** veces. Hubo **16 / 0** pérdidas y **15 / 0** recuperaciones desde ausencia de ancla entre dos fotogramas consecutivos. Los **38** de la comparación entre revisiones se refieren a pares simultáneos y tienen otro denominador.

| Caso | Fotograma UTC | Ancla GPS base → corrección | Discontinuidad base → corrección |
|---|---|---|---:|
| `20231`, retorno A→B→A | 06:22:35,444589 | 06:21:52 → 06:22:30 | +10 259,28 → 0 m |
| `20793`, retorno A→B→A | 08:47:40,042598 | 08:46:51 → 08:47:30 | +22 371,74 → +169,89 m |
| `20414`, confirma la primera de dos muestras coherentes entre sí | 06:17:57,714944 | 06:17:52 → 06:17:10 (25 214,90 m) | −1 719,43 → −1 417,00 m |
| `20418`, confirma la primera de dos muestras coherentes entre sí | 06:32:57,378956 | 06:32:52 → 06:32:10 (16 187,25 m) | −1 875,80 → −1 664,91 m |
| `20752`, sigue retenido tras las muestras incompatibles | 07:45:27,265986 | 07:44:52 → 07:44:10 (41 198,73 m) | −23 104,05 → 0 m |

En `20231` desaparece también el retroceso de −10 259,28 m del fotograma siguiente. En `20793` el siguiente retroceso pasa de −22 371,74 a −169,89 m y más tarde ambas revisiones todavía presentan un salto de **+3 045,82 m**. En `20752`, los GPS de 07:44:52 y 07:45:10 se proyectan a unos **17 659 m** y **39 595 m** (≈4 387 km/h en 18 s), por encima del límite de plausibilidad. El tercer reanclaje, `19588`, confirma el GPS de **07:56:30** al publicar el de **07:57:10** (fotograma 07:57:17,465813, progreso confirmado **15 189,71 m**).

- **Peor H1 en ambas revisiones.** `20213`, GPS B de las **06:11:10**. La discrepancia de **23 633,99 m** entra en H1 pese al rechazo (`backward_jump` y `implausible_speed`).
- **Peor discontinuidad base y mayor descenso de magnitud.** El siguiente GPS de `20213`, de **06:11:30**, entra a las **06:11:47,750826**. El salto de **−23 633,99 m** pasa a **0 m** porque la corrección conserva el ancla de las **06:10:30**.
- **Peor discontinuidad residual.** `20721` presenta **+13 016,02 m** en la corrección a las **06:12:18,591167**, al confirmar el GPS de **06:12:10**. La mayor ampliación de magnitud fue **+914,59 m** en `20741` a las **07:39:17,318703** (de **+958,96** a **−1 873,55 m**, ambos con GPS de **07:39:10** al final del par).

### Las 107 rachas de MP-036

Se reprodujo [la población de prefijos del volcado completo de MP-036](../mp-036/README.md) sobre la misma restauración (12 160 filas con corredor, 12 146 proyectables). Incluye filas fuera de la jornada segmentada. La racha descriptiva agrupa rechazos consecutivos en vía con ancla anterior y al menos dos GPS idénticos, saltando filas sin proyección admisible como en MP-036. El extracto conserva los IDs y las decisiones de ambas revisiones para las mismas filas.

| Medida de prefijos | Base | Corrección |
|---|---:|---:|
| Rachas de ≥2 rechazos en vía | 15 | 111 |
| Rachas de GPS idéntico con esa definición | 0 | 107 |
| Rachas del conjunto fijo de 107 con reanclaje | 0/107 | 0/107 |
| Filas aceptadas como ancla propia en esas mismas 107 rachas | 220/327 | 0/327 |

En la corrección, **104/107** rachas terminan con un GPS aceptado más cerca del ancla retenida que del último GPS repetido. **3/107** llegan al borde del prefijo sin otra aceptación. Estos recuentos describen el comportamiento con coordenadas repetidas. El filtro de la corrección selecciona el siguiente GPS aceptado en relación con el ancla que retuvo. Por ello, el 104/107 es parcialmente circular y carece de independencia como evidencia de que el ancla corresponda a la posición física. El grupo de fotogramas con racha de la tabla anterior incluye todas las repeticiones elegibles, también las aceptadas.

## Criterio histórico y límites

Se mantiene el criterio de H1 **p50 ≤200 m con ≥500 pares**. Las dos ejecuciones cubren ese umbral provisional y la mediana cero oculta colas de kilómetros. En las poblaciones propias de MP-025b también cambian estos recuentos.

| Métrica histórica | Base → corrección |
|---|---:|
| Salidas `STOPPED_AT` retenidas | 402/6 918 → 398/6 902 |
| Salidas retenidas con latencia indeterminada | 0/402 → 2/398 |
| Latencia calculable, n y p50 | 402 a 8,32 s → 396 a 8,17 s |
| Oportunidades M7 con avance GPS ≥100 m | 1 441 → 1 349 |
| Retenciones M7 | 135/1 441 → 120/1 349 |
| Transiciones desde el límite de vigencia a congelación con ancla estable, `frozen_rewind_m.n` | 65 → 72, con retroceso máximo de 0 m en ambas |

M7 sigue siendo retrospectivo y cambia su población elegible. El JSON lista los **17 campos de salida** que difieren en el objeto interno de replay, incluidos campos derivados de la misma selección. Los cambios de elegibilidad, H1 y M7 quedan en las tablas (`excluded`, `unavailable`, `jumps`, `jump_tail`, `jumps_by_state`, `h1_strata`, `departures`, `latency_s`, `m7_retenciones`, `frozen_rewind_m`). El desglose histórico de `adverse`, `departure_events`, `recovery_cases`, `recovery_m`, `provenance`, `states` y `separacion` queda fuera del análisis adicional de MP-038. La salida física permanece UNVERIFIED. Los estratos de referencia se consultaron con `git show pedromaaz13/mp-037-estudio-m7-r4:docs/evidence/mp-037/README.md`. [Criterio vigente en ADR-0014 §8](../../adr/0014-amendment-stop-state.md#8-criterios-de-aceptación-de-mp-025a).

La evaluación cubre una sola jornada, dos tramos de hora punta y los corredores con geometría validada. Quedan **UNVERIFIED** la posición y la puntualidad físicas, la discontinuidad perceptible en el cliente con interpolación y latencia reales, la generalización a otras jornadas, horarios, corredores o cortes, y el cumplimiento integral de FR-01. Las jornadas 2 y 3 siguen pendientes. La evaluación queda para revisión independiente.

## Reproducción y custodia

Los datos y el resultado JSON se guardan fuera de Git, en el directorio original `data/capture/2026-11-26/analysis/`. El modelo y esfuerzo del despacho fueron Codex `gpt-6.2-sol` · medium. Identidad efectiva del backend **UNVERIFIED**. Revisor asignado Claude `claude-opus-5-5` · high.

| Archivo | SHA-256 |
|---|---|
| `analysis/session-1-20261126T090138Z.dump` | `95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1` |
| `session-1/manifest.json` | `5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e` |
| `fomento_transit.zip` | `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e` |
| Primera ronda, `analysis/mp038-jornada1.json` | `1450a64fc58ea97bdda36a631fb1192298288a2173a6360250910f345a7ac5fe` |
| Preliminar, solo envolventes activas, `analysis/mp038-delta-r2.json` | `0bfbcc5e0383532ca0b8885222aacc7c13dd47219c62f9ec7164858ee3153694` |
| Delta final, `analysis/mp038-delta-r2-replica.json` y `analysis/mp038-delta-r2-verificado.json` | `c72629a8f7dfbe913509ddd0abf09717de2ed77f89c4fc8beb42eb2b24e1bfae` |

El resultado preliminar solo pudo evaluar 192 envolventes activas. El primer `cmp` con el delta dio distinto al incorporar los 27 progresos congelados. La reproducción independiente compara las dos salidas del arnés corregido.

El delta se ejecutó con el checkout de corrección en `29033f6`, cuyo código de producto coincide con `0c518fa`. Con dependencias Python instaladas localmente, ejecutar [`run.sh`](run.sh) con un identificador nuevo. La salida registra el HEAD de cada checkout. Si solo cambia el commit del informe, se pueden comparar las magnitudes y casos eliminando `inputs.heads` de ambos JSON.

```bash
repo_original=/Users/matu/Documents/DATA/madrid-pulse
capture="$repo_original/data/capture/2026-11-26"
gtfs="$repo_original/data/gtfs_static/fomento_transit.zip"
export MP038_PYTHON="$repo_original/.venv/bin/python" MP038_PORT=5470
for id in revision replica; do
    docs/evidence/mp-038/run.sh "$capture" "$gtfs" "$id"
done
(
    cd "$capture/analysis"
    cmp mp038-revision.json mp038-replica.json
    shasum -a 256 -c mp038-revision.json.sha256 mp038-replica.json.sha256
)
```

El checkout temporal sigue PEP 420. Como `4bc8612` carece de `infra/operate/validation`, el baseline obtiene `replay.py`, `metrics.py`, `segments.py` y los módulos MP-038 del worktree que aporta `PYTHONPATH`. `apps.api.snapshot` y `packages.movement.engine` se resuelven en el checkout desde el que se ejecuta cada proceso. La traza valida el origen con `__file__`, imprime las rutas absolutas al log y guarda las rutas relativas a cada raíz en `inputs.module_origins` para permitir `cmp`.

El script comprueba los hashes de entrada, copia el dump y aplica las cuatro migraciones antes de restaurar sus tablas de datos. Usa PostGIS local `postgis/postgis:17-3.5`, `--pull=never`, y el DSN `postgresql://mp_test:mp_local@127.0.0.1:5470/mp038` (credenciales desechables). La lista blanca de `MP038_PORT` admite **5470** y **5471**. El valor predeterminado es 5470 y el guard exige host `127.0.0.1`, el puerto elegido, base `mp038`, modo replay, núcleo completo, DSN sin opciones ni fragmento y marca desechable. La consulta de control devolvió `mp038|public|mp_test|madrid-pulse:disposable`. El replay trabaja en modo de solo lectura, con escritura habilitada únicamente para crear o reemplazar las vistas temporales por segmento. Las dos revisiones usan un caché local de proyecciones puras y ejecutan el constructor de snapshots y el motor de producción de su checkout. Las pruebas de CI con PostgreSQL usaron su propio contenedor desechable en el mismo puerto y rol, con base marcada `mp038_ci`. Para ejecutar los casos del GTFS oficial en esa suite se crearon los dos enlaces temporales desde la raíz del worktree.

```bash
mkdir -p data/gtfs_static data/hito-03/replay
ln -s "$gtfs" data/gtfs_static/fomento_transit.zip
ln -s "$gtfs" data/hito-03/replay/fomento_transit.zip
```

| Comando ejecutado | Salida o resultado |
|---|---|
| Replays completos en `4bc8612` y `0c518fa`, dos restauraciones independientes con `run.sh ... delta-r2-replica` y `run.sh ... delta-r2-verificado` | **PASS**. Ambas ejecuciones produjeron un resultado idéntico con `cmp`. El arnés comparó las 29 507 filas y los 516 instantes. |
| `shasum -a 256 -c "$dump.sha256"`, `cmp` de la copia, y SHA-256 antes y después de 116 archivos de la captura y el ZIP, en conjunto, incluidos volcado, manifiesto, resultados históricos y primera ronda de MP-038 | **PASS**. Todos los ficheros devolvieron `OK`; `cmp` terminó con código 0. El JSON nuevo y su `.sha256` llevan nombre propio. |
| `python -m unittest -v $(awk '/^            (apps\|packages\|services\|tests)\./ {print $1}' .github/workflows/ci.yml) infra.operate.validation.test_metrics tests.governance.test_governance` con `MADRID_PULSE_ENV=test`, `MADRID_PULSE_REQUIRE_DB=1` y enlaces temporales al ZIP local | **PASS**. `Ran 385 tests`, `OK (skipped=5)`. Los cinco casos de soak MP-007 quedaron **NO EJECUTADOS** por ausencia de esa población en la base limpia. |
| `python -m unittest -v infra.operate.validation.test_mp038` | **RED** contra el arnés anterior, `Ran 10 tests`, 1 fallo y 2 errores. Una prueba adicional de progreso congelado dio **RED** por caso ausente. **GREEN** tras el delta, `Ran 11 tests`, `OK`. |
| `npm ci --offline --no-audit --no-fund`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` en `apps/web` con Node 22.13.1 | **PASS**. 11 archivos y 110 pruebas. El build verificó el worker MapLibre de 550 754 bytes y emitió un aviso de tamaño de chunk. |
| `ruff check infra/operate/validation`, `python -m compileall -q infra/operate/validation`, `python scripts/governance/check_docs.py`, `bash -n docs/evidence/mp-038/run.sh`, `git diff --check` | **PASS**. `All checks passed!`, `Documentación de gobernanza correcta.` y salidas 0. |
| `infra.operate.validation.test_segments` | **NO EJECUTADO**. Está fijado al endpoint histórico de MP-025b. El replay invocó `check_segment` antes de analizar cada una de las dos ventanas en ambas revisiones. |
| `docker rm -fv` y comprobación de nombre, volumen y `lsof -nP -iTCP:5470 -sTCP:LISTEN`; `git worktree remove` del baseline temporal | **PASS**. Los tres contenedores sucesivos de replay y el de CI, sus volúmenes, la escucha y los checkouts temporales fueron retirados. |
