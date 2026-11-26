# MP-038 · Evaluación comparable de MP-036 sobre la jornada 1

**FR-01 sigue abierto.** Sobre los **11 206 pares H1 evaluables en ambas revisiones**, la discrepancia respecto del siguiente GPS fue idéntica par a par. En los **35 383 pares de fotogramas comparables**, las discontinuidades de presentación >200 m bajaron de **2 935 a 2 771**. La corrección cambió la identidad del ancla confirmada en **974/35 594** fotogramas con ancla confirmada en alguna revisión. En 907 de esos fotogramas conservó un ancla más antigua.

## Entradas y método

Se comparó `4bc86128d44a9b83f8f9747df5cf83ce593f0194` con `0c518fa9fab3e1185a95480877474742c70585b6` (HEAD de producto al iniciar MP-038, con el delta de MP-036). Ambos procesos usaron la misma restauración, las dos ventanas de [MP-025b](../mp-025b/README.md#jornada-1-de-3--26-de-noviembre-de-2026), el catálogo completo, el mismo perfil y los **516 instantes** del arnés, con `display_lag_s=0`. Se comprobaron las vistas temporales, los relojes, la identidad de las filas brutas y las proyecciones par a par. Entraron **29 507/29 642** filas de GPS y **347** vehículos, de los cuales **135** tenían corredor. El corte del reinicio excluyó 135 filas y eliminó los 65 enlaces GPS potenciales entre segmentos. El tiempo se expresa en UTC.

1. **Discrepancia ante el GPS bruto (H1).** Valor absoluto de la envolvente propia de A evaluada a la hora GPS de B menos la proyección dirigida del GPS bruto B. El GPS B rechazado como ancla sigue en H1 si tiene proyección válida. Se aplica [la función de exclusión de MP-025b](../../../infra/operate/validation/metrics.py#L45) a cada revisión. Se publican los resultados de la población que cada revisión hace elegible y los de su intersección.
2. **Ancla confirmada.** Por vehículo e instante, se compara `rendered.last_confirmed_at` si hay progreso confirmado, resolviendo esa hora a una huella de GPS única del mismo vehículo y viaje dentro del segmento. Se registra cada diferencia de identidad, incluidas las apariciones o pérdidas de confirmación. Un **reanclaje** es un evento `anchor_reacquired` del motor, deduplicado por revisión, segmento, vehículo, GPS bruto y ancla confirmada. Los tres eventos tuvieron cambio de ancla en el fotograma correspondiente.
3. **Discontinuidad de presentación.** Diferencia firmada de `rendered.progress_m` entre dos instantes consecutivos del arnés en el mismo segmento, para la misma circulación y geometría map-matched. Incluye correcciones y avance ordinario entre los dos instantes. Se conserva el signo para los casos y se agregan las magnitudes. Los pares con ausencia, cambio de circulación, falta de progreso en vía o geometría distinta se excluyen. Se publican ambos denominadores propios y su intersección.

Los estratos siguen el estado del GPS bruto A y la velocidad aparente **absoluta** `|arco(B) − arco(A)| / (tB − tA)`, con tope inclusivo de **160 km/h**. Una racha al inicio significa que A repite exactamente la coordenada bruta de su predecesor consecutivo de la misma circulación en el segmento. En H1, A y B son las filas GPS del par. En fotogramas, A y B son los GPS publicados por los dos snapshots y el primero visible se atribuye a su propio estado si A falta. Sin avance de la hora GPS, intervalo fuera de (0, 180 s] o falta de una proyección comparable, la velocidad queda sin determinar. Los **180 s**, el descarte de GPS a más de **200 m** de la vía y el tope de **160 km/h** salen de [los umbrales de producción](../../../packages/movement/model.py#L42). La corrección usa profundidad **256** y **K=2**. [Configuración del historial](../../../apps/api/db.py#L17) · [Configuración del reanclaje](../../../packages/movement/engine.py#L24).

## H1 y presentación

Los cuantiles y máximos están en metros. Los recuentos de las dos últimas columnas usan el denominador `n` de cada fila.

| Medición y población | Revisión | n | p50 | p90 | p95 | Máx. | >200 m | >5 km |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H1 elegible | Base | 11 425 | 0 | 1 143,0 | 1 916,0 | 23 634,0 | 2 298 | 32 |
| H1 elegible | Corrección | 11 233 | 0 | 1 038,6 | 1 876,0 | 23 634,0 | 2 125 | 26 |
| H1 común | Ambas | 11 206 | 0 | 1 039,7 | 1 880,2 | 23 634,0 | 2 117 | 26 |
| H1 con B sustituido por ancla previa | Base | 310 | 2 255,6 | 3 709,3 | 6 678,6 | 23 634,0 | 310 | 23 |
| H1 con B sustituido por ancla previa | Corrección | 309 | 2 254,0 | 3 709,3 | 6 544,1 | 23 634,0 | 309 | 22 |
| Presentación elegible | Base | 35 383 | 0 | 136,0 | 462,2 | 23 634,0 | 2 935 | 50 |
| Presentación elegible | Corrección | 35 436 | 0 | 121,3 | 391,7 | 13 016,0 | 2 788 | 13 |
| Presentación común | Base | 35 383 | 0 | 136,0 | 462,2 | 23 634,0 | 2 935 | 50 |
| Presentación común | Corrección | 35 383 | 0 | 120,7 | 389,3 | 13 016,0 | 2 771 | 13 |

De **29 095** pares GPS candidatos, ambas revisiones excluyeron 17 199 sin corredor, 92 sin proyección válida, 44 por intervalo largo y uno por cambio de circulación. La falta de plan inicial excluyó **334** en la base y **526** en la corrección. De esos pares, 307 carecieron de plan en ambas, 219 solo en la corrección y 27 solo en la base. Así se explica la caída aparente de la cola H1 al comparar las dos poblaciones propias. El baseline reprodujo los **33 campos de replay compartidos** con `jornada1-delta1.json`. `jump_tail` es el campo adicional de la versión del arnés usada aquí.

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
| Sin racha | 927 / 927 (2 452) | 505 / 8 178 | 1 413 / 1 316 (8 130) | 0 / 3 |
| Racha indeterminada | — (0) | 3 / 502 | 36 / 36 (340) | 0 / 0 |

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

En la corrección, **104/107** rachas terminan con un GPS aceptado más cerca del ancla retenida que del último GPS repetido. **3/107** llegan al borde del prefijo sin otra aceptación. Estos recuentos describen el comportamiento con coordenadas repetidas. El grupo de fotogramas con racha de la tabla anterior incluye todas las repeticiones elegibles, también las aceptadas.

## Criterio histórico y límites

Se mantiene el criterio de H1 **p50 ≤200 m con ≥500 pares**. Las dos ejecuciones cubren ese umbral provisional y la mediana cero oculta colas de kilómetros. M7 sigue siendo retrospectivo. En los conjuntos propios se observaron **135/1 441 → 120/1 349** retenciones con avance GPS de al menos 100 m en tránsito o aproximación. Cambia el número de oportunidades evaluables y esta comparación carece de una medida de salida física. Los estratos de referencia se consultaron con `git show pedromaaz13/mp-037-estudio-m7-r4:docs/evidence/mp-037/README.md`. [Criterio vigente en ADR-0014 §8](../../adr/0014-amendment-stop-state.md#8-criterios-de-aceptación-de-mp-025a).

La evaluación cubre una sola jornada, dos tramos de hora punta y los corredores con geometría validada. Quedan **UNVERIFIED** la posición y la puntualidad físicas, la discontinuidad perceptible en el cliente con interpolación y latencia reales, la generalización a otras jornadas, horarios, corredores o cortes, y el cumplimiento integral de FR-01. Las jornadas 2 y 3 siguen pendientes. La evaluación queda para revisión independiente.

## Reproducción y custodia

Los datos y el resultado JSON se guardan fuera de Git, en el directorio original `data/capture/2026-11-26/analysis/`. El modelo y esfuerzo del despacho fueron Codex `gpt-6.2-sol` · medium. Identidad efectiva del backend **UNVERIFIED**. Revisor asignado Claude `claude-opus-5-5` · high.

| Archivo | SHA-256 |
|---|---|
| `analysis/session-1-20261126T090138Z.dump` | `95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1` |
| `session-1/manifest.json` | `5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e` |
| `fomento_transit.zip` | `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e` |
| `analysis/mp038-jornada1.json` | `1450a64fc58ea97bdda36a631fb1192298288a2173a6360250910f345a7ac5fe` |

Con dependencias Python instaladas localmente, ejecutar [`run.sh`](run.sh) con un identificador nuevo. La salida registra el HEAD de cada checkout. Si solo cambia el commit del informe, se pueden comparar las magnitudes y casos eliminando `inputs.heads` de ambos JSON.

```bash
repo_original=/Users/matu/Documents/DATA/madrid-pulse
capture="$repo_original/data/capture/2026-11-26"
gtfs="$repo_original/data/gtfs_static/fomento_transit.zip"
MP038_PYTHON="$repo_original/.venv/bin/python" docs/evidence/mp-038/run.sh "$capture" "$gtfs" revision
(cd "$capture/analysis" && shasum -a 256 -c mp038-revision.json.sha256)
```

El script comprueba los hashes de entrada, copia el dump y aplica las cuatro migraciones antes de restaurar sus tablas de datos. Usa PostGIS local `postgis/postgis:17-3.5`, `--pull=never`, y el DSN `postgresql://mp_test:mp_local@127.0.0.1:5470/mp038` (credenciales desechables). La consulta de control devolvió `mp038|public|mp_test|madrid-pulse:disposable`. El replay trabaja en modo de solo lectura, con escritura habilitada únicamente para crear o reemplazar las vistas temporales por segmento. Las dos revisiones usan un caché local de proyecciones puras y ejecutan el constructor de snapshots y el motor de producción de su checkout. Las pruebas CI con PostgreSQL usaron `mp038_ci` marcada, dentro del primer contenedor desechable, con el mismo puerto y rol.

| Comando ejecutado | Salida o resultado |
|---|---|
| Replays completos en `4bc8612` y `0c518fa`, dos restauraciones independientes mediante los comandos de `run.sh` | **PASS**. Ambas ejecuciones produjeron un resultado idéntico con `cmp`. El arnés comparó las 29 507 filas y los 516 instantes. |
| `shasum -a 256 -c "$dump.sha256"`, `cmp` de la copia, y SHA-256 antes y después de 25 archivos originales, incluidos volcado, manifiesto y resultados históricos | **PASS**. Todos los ficheros devolvieron `OK`; `cmp` terminó con código 0. El JSON nuevo y su `.sha256` llevan nombre propio. |
| `python -m unittest -v $(awk '/^            (apps\|packages\|services\|tests)\./ {print $1}' .github/workflows/ci.yml) infra.operate.validation.test_metrics tests.governance.test_governance` con `MADRID_PULSE_ENV=test`, `MADRID_PULSE_REQUIRE_DB=1` y enlaces temporales al ZIP local | **PASS**. `Ran 385 tests`, `OK (skipped=5)`. Los cinco casos de soak MP-007 quedaron **NO EJECUTADOS** por ausencia de esa población en la base limpia. |
| `python -m unittest -v infra.operate.validation.test_mp038` | **PASS**. `Ran 7 tests`, `OK`. |
| `npm ci --offline --no-audit --no-fund`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` en `apps/web` con Node 22.13.1 | **PASS**. 11 archivos y 110 pruebas. El build verificó el worker MapLibre de 550 754 bytes y emitió un aviso de tamaño de chunk. |
| `ruff check infra/operate/validation`, `python -m compileall -q infra/operate/validation`, `python scripts/governance/check_docs.py`, `bash -n docs/evidence/mp-038/run.sh`, `git diff --check` | **PASS**. `All checks passed!`, `Documentación de gobernanza correcta.` y salidas 0. |
| `infra.operate.validation.test_segments` | **NO EJECUTADO**. Está fijado al endpoint histórico de MP-025b. El replay invocó `check_segment` antes de analizar cada una de las dos ventanas en ambas revisiones. |
| `docker rm -fv` y comprobación de nombre, volumen y `lsof -nP -iTCP:5470 -sTCP:LISTEN`; `git worktree remove` del baseline temporal | **PASS**. Ambos contenedores, sus volúmenes, la escucha y los checkouts temporales fueron retirados. |
