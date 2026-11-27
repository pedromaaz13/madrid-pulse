# MP-038 · Jornada 2 · baseline frente a MP-036

Comparación de `4bc8612` con MP-036 (`0c518fa`) sobre **705 runs** de la segunda jornada, con el reloj y los filtros de la [jornada 1](README.md), **K=2**, historial de **256** y umbrales de producción congelados.

1. **Recuperación tras rechazos.** Se recuperaron **306/341 → 317/325** episodios observados. El p90 subió de **30,9 a 61,7 s**. Las reapariciones de B tras rechazo bajaron de **5 a 0** en **373** tríadas A→B→A. La corrección registró **6** reanclajes señalados y **0** promociones sin señal.
2. **Antigüedad.** La corrección usó un ancla más antigua en **1 932/40 117** fotogramas con alguna confirmación. El incremento tuvo mediana **78 s** y máximo **220 s**.
3. **Retenciones prolongadas.** Las observadas durante >180 s pasaron de **3 a 12**. Siete de las doce quedaron censuradas al cierre. La mayor recuperación con GPS que siguió llegando tardó **215,5 s**.
4. **Discontinuidades.** En **39 973** pares comunes, los saltos >200 m bajaron de **2 587 a 2 461**. Hubo **22** cruces al alza y **148** a la baja, y **13/44** pares exclusivos de la corrección superaron 200 m.

La **discrepancia frente al GPS bruto** H1 fue idéntica en **9 916** pares comunes (p50 **0 m**). Entre **135** pares con ancla retenida, subió en **76** y bajó en **59**. Subió en los **52** donde el GPS siguiente repitió coordenada. **FR-01 sigue abierto**. La posición física permanece **UNVERIFIED**.

## Recuperación tras rechazos

Se evalúa cada llegada de GPS seleccionada por la API para la misma fila bruta y con motor aplicable. Una retención comienza en la primera llegada rechazada que publica un ancla anterior confirmada, salvo cuando el motor señala un reanclaje en esa llegada. La recuperación es el primer recambio a un GPS propio aceptado o un reanclaje señalado. Se cuentan aparte las promociones de una muestra previamente rechazada sin señal de reanclaje, las pérdidas de confirmación y los episodios censurados. Un reanclaje deliberado con K=2 puede elegir una muestra antes rechazada. Queda identificado por la bandera `anchor_reacquired` de producción.

| Medida | Base | Corrección |
|---|---|---|
| Llegadas GPS seleccionadas con motor | 10 567 | 10 567 |
| GPS aceptados al llegar | 10 210 | 10 087 |
| GPS distintos del ancla al llegar | 357 | 480 |
| De ellos, sin confirmación | 16 | 0 |
| De ellos, con ancla anterior y sin reanclaje | 341 | 474 |
| De ellos, con reanclaje señalado | 0 | 6 |
| Episodios de retención observados | 341 | 325 |
| GPS nuevo aceptado | 306 | 311 |
| Reanclaje señalado | 0 | 6 |
| Pérdida de confirmación | 16 | 0 |
| Promoción previa sin señal | 16 | 0 |
| Censura al final del segmento | 3 | 8 |

Entre los episodios con recuperación, los tiempos p50 / p90 / máximo fueron **30,8 / 30,9 / 35,9 s** (n=306) y **30,8 / 61,7 / 215,5 s** (n=317). De 26 154 filas GPS, quedaron fuera del denominador de llegadas con motor 15 587 en la base y 15 587 en la corrección. La exclusión reúne observaciones fuera de cobertura y filas que no se publicaron como GPS propio en su instante de llegada.

Se considera racha cuando la coordenada se repite respecto al GPS bruto precedente de la misma circulación. La velocidad aparente es el desplazamiento absoluto proyectado en vía dividido por el tiempo entre los GPS comparados, con intervalo válido de (0, 180 s]. Los recuentos de recuperación usan poblaciones de episodios propias de cada revisión.

| Estrato inicial | Recuperaciones / episodios base | Recuperaciones / episodios corrección |
|---|---|---|
| Global | 306/341 | 317/325 |
| `STOPPED_AT` | 20/30 | 26/26 |
| `INCOMING_AT` | 23/28 | 24/26 |
| `IN_TRANSIT_TO` | 263/283 | 267/273 |
| ≤160 km/h | 73/76 | 73/75 |
| >160 km/h | 208/224 | 205/210 |
| Velocidad indeterminada | 25/41 | 39/40 |
| Con racha | 0/0 | 0/0 |
| Sin racha | 294/329 | 307/314 |
| Racha indeterminada | 12/12 | 10/11 |

### Tríadas A→B→A y promociones de GPS rechazado

Se reproduce la clasificación de [MP-036](../mp-036/README.md#clasificación-de-las-416-tríadas). Se buscan tres GPS consecutivos del mismo vehículo y viaje, con coordenadas de A y C idénticas y distintas de B. Se usa la respuesta de producción al hacerse visibles B y C (`max(observed_at, started_at)`), comprobando fecha y huella de la fila bruta. Se exige que las horas GPS de B y C identifiquen muestras únicas en la serie. El barrido de promociones fuera de la tríada comprueba si un GPS rechazado que se observó al llegar reaparece como ancla confirmada en un fotograma posterior del mismo vehículo y circulación.

| Resultado en C | Jornada 1 base → corrección | Jornada 2 base → corrección |
|---|---|---|
| B vuelve tras rechazo | 6 → 0 | 5 → 0 |
| B se conserva tras aceptarse al llegar | 44 → 44 | 60 → 60 |
| C se acepta al retornar | 104 → 115 | 115 → 127 |
| Sin ancla confirmada | 5 → 0 | 7 → 0 |
| Sin motor en B o C | 257 → 257 | 186 → 186 |
| Otra ancla anterior | 0 → 0 | 0 → 0 |
| Fila de B o C sustituida | 0 → 0 | 0 → 0 |
| Total | 416 → 416 | 373 → 373 |

El barrido de todas las llegadas detectó las siguientes promociones de un GPS previamente rechazado. Las tríadas están incluidas en ese barrido.

| Promoción al confirmar un GPS antes rechazado | Base | Corrección |
|---|---|---|
| Sin bandera de reanclaje | 16 | 0 |
| Con `anchor_reacquired` | 0 | 6 |

Los cinco casos A→B→A de la base fueron `19621` (09:07:51 → 09:08:10 UTC), `20258` (09:31:30 → 09:31:50 UTC), `20441` (08:55:30 → 08:55:51 UTC), `20442` (08:45:30 → 08:46:10 UTC) y `20789` (08:24:30 → 08:24:52 UTC). Las horas corresponden a B y C.

Los seis reanclajes señalados ocurrieron en `20235` (08:05:08), `20237` (08:10:16 y 08:15:55), `20781` (08:12:51), `20241` (08:36:58) y `20790` (08:48:51 UTC). En los **10 567** GPS visibles con motor, la corrección no mostró ninguna promoción de un rechazado sin bandera. La base mostró **16**, cinco de ellas en A→B→A.

En la comprobación complementaria de prefijos de MP-036, restringida a los runs de esta jornada, las rachas de ≥2 rechazos en vía pasaron de **12 a 91**. En la corrección **78/91** tenían coordenada idéntica y en **0/78** apareció un reanclaje. Las **206** filas de esas rachas tuvieron **128** aceptaciones como ancla propia en la base y **0** en la corrección. En **74/78** el siguiente GPS aceptado estaba más cerca del ancla retenida y **4/78** quedaron sin GPS posterior aceptado. El filtro usa esa misma ancla para aceptar muestras, de modo que la proximidad tiene una dependencia con el criterio del propio motor.

## Antigüedad del ancla y retenciones prolongadas

La antigüedad es el tiempo entre el reloj del fotograma y el GPS del ancla confirmada en vía. Se mide en todos los fotogramas con progreso confirmado, incluidos los de posición congelada. La duración de una retención se mide desde su primera llegada rechazada hasta el recambio o el último fotograma observado cuando hay censura por fin de segmento, ausencia del vehículo o cambio de circulación. Los casos censurados aportan límites inferiores y se publican aparte de los tiempos hasta una recuperación. **>180 s** usa el horizonte de vigencia de producción como corte descriptivo. Se guarda la duración de cada episodio en `operational.*.hold_cases`, con el primer y último GPS rechazados, su número de llegadas y el desenlace. Así se distingue un ancla mantenida sin nuevas muestras de una racha de rechazos que sigue llegando.

En **97 694** fotogramas de vehículo, se excluyen por falta de progreso confirmado **57 605 / 57 577** (base / corrección). Los estratos de antigüedad usan el estado del GPS visible y su cambio respecto al GPS bruto precedente de la misma circulación. Los de retenciones usan la llegada que inicia el episodio. Las familias marginales se solapan y el JSON también conserva sus cruces. Las celdas dan n · p50 / p90 / máximo, en segundos.

| Estrato | Edad base | Edad corrección | Retención base | Retención corrección |
|---|---|---|---|---|
| Global | 40 089 · 39,0 / 3 780,7 / 7 241,1 | 40 117 · 39,0 / 3 798,0 / 7 241,1 | 341 · 30,8 / 30,9 / 4 918,9 | 325 · 30,8 / 92,3 / 6 428,4 |
| `STOPPED_AT` | 14 800 · 20,0 / 108,3 / 6 839,1 | 14 817 · 20,0 / 108,6 / 6 839,1 | 30 · 30,8 / 30,8 / 35,8 | 26 · 30,8 / 123,2 / 184,8 |
| `INCOMING_AT` | 15 316 · 1 161,0 / 4 619,3 / 7 241,1 | 15 317 · 1 161,0 / 4 619,3 / 7 241,1 | 28 · 30,8 / 30,9 / 4 918,9 | 26 · 30,8 / 62,4 / 4 918,9 |
| `IN_TRANSIT_TO` | 9 973 · 61,0 / 4 120,2 / 6 719,1 | 9 983 · 100,0 / 4 142,0 / 6 719,1 | 283 · 30,8 / 30,9 / 1 054,3 | 273 · 30,8 / 65,7 / 6 428,4 |
| ≤160 km/h | 35 294 · 38,0 / 3 680,0 / 7 019,1 | 35 294 · 38,0 / 3 690,2 / 7 019,1 | 76 · 30,8 / 30,9 / 1 054,3 | 75 · 35,9 / 92,4 / 1 054,3 |
| >160 km/h | 3 530 · 39,0 / 3 658,7 / 6 719,1 | 3 530 · 39,0 / 3 658,7 / 6 719,1 | 224 · 30,8 / 30,9 / 4 918,9 | 210 · 30,8 / 92,3 / 6 428,4 |
| Velocidad indeterminada | 1 265 · 1 752,5 / 5 372,9 / 7 241,1 | 1 293 · 1 706,4 / 5 348,0 / 7 241,1 | 41 · 30,8 / 30,9 / 35,8 | 40 · 30,8 / 38,4 / 5 134,4 |
| Con racha | 30 753 · 39,0 / 3 700,0 / 7 019,1 | 30 753 · 39,0 / 3 721,0 / 7 019,1 | 0 · — / — / — | 0 · — / — / — |
| Sin racha | 8 186 · 22,0 / 3 520,0 / 6 719,1 | 8 214 · 22,0 / 3 516,0 / 6 719,1 | 329 · 30,8 / 30,9 / 4 918,9 | 314 · 30,8 / 92,3 / 6 428,4 |
| Racha indeterminada | 1 150 · 2 146,2 / 5 620,0 / 7 241,1 | 1 150 · 2 174,1 / 5 620,0 / 7 241,1 | 12 · 30,8 / 30,8 / 30,8 | 11 · 30,8 / 61,7 / 5 134,4 |

La corrección cambió la identidad del ancla en **1 984/40 117** fotogramas con al menos una confirmación. En **1 932** pasó a un ancla más antigua, en **24** a una más reciente y en **28** ganó confirmación. La diferencia en las anclas más antiguas tuvo p50 **78 s**, p90 **120 s** y máximo **220 s** (`20441`, fotograma **08:32:21,408341**, de ancla **08:32:10** a **08:28:30**). El máximo absoluto de antigüedad en ambas revisiones, **7 241,1 s**, corresponde a `19566` con último GPS de **07:54:10** y persistencia hasta el cierre.

| Retenciones >180 s | Base | Corrección |
|---|---|---|
| n y p50 / p90 / máximo (s) | 3 · 1 054,3 / 4 146,0 / 4 918,9 | 12 · 1 023,4 / 5 901,4 / 6 428,4 |
| Con llegadas rechazadas que abarcan >180 s | 0 | 1 |

| Revisión | Vehículo | Inicio UTC | Retención (s) | GPS rechazados | Lapso entre rechazos (s) | Desenlace |
|---|---|---|---|---|---|---|
| Base | `20238` | 08:32:52 | 4 918,9 | 1 | 0,0 | Censura al final del segmento |
| Base | `20790` | 09:37:16 | 1 054,3 | 1 | 0,0 | Censura al final del segmento |
| Base | `19619` | 09:38:18 | 992,6 | 1 | 0,0 | Censura al final del segmento |
| Corrección | `20242` | 08:07:42 | 6 428,4 | 2 | 30,8 | Censura al final del segmento |
| Corrección | `20768` | 08:15:25 | 5 966,1 | 3 | 61,6 | Censura al final del segmento |
| Corrección | `20246` | 08:26:12 | 5 319,1 | 4 | 92,2 | Censura al final del segmento |
| Corrección | `20774` | 08:29:16 | 5 134,4 | 2 | 30,8 | Censura al final del segmento |
| Corrección | `20238` | 08:32:52 | 4 918,9 | 1 | 0,0 | Censura al final del segmento |
| Corrección | `20790` | 09:37:16 | 1 054,3 | 1 | 0,0 | Censura al final del segmento |
| Corrección | `19619` | 09:38:18 | 992,6 | 1 | 0,0 | Censura al final del segmento |
| Corrección | `20441` | 08:29:16 | 215,5 | 7 | 184,7 | Nuevo GPS aceptado |
| Corrección | `20430` | 08:37:29 | 184,9 | 6 | 154,1 | Nuevo GPS aceptado |
| Corrección | `20775` | 08:41:35 | 184,8 | 6 | 153,9 | Nuevo GPS aceptado |
| Corrección | `19607` | 09:00:14 | 184,7 | 6 | 153,8 | Nuevo GPS aceptado |
| Corrección | `19621` | 09:38:18 | 184,7 | 6 | 153,9 | Nuevo GPS aceptado |

Los tres episodios largos de la base y siete de la corrección quedaron censurados al cierre. Los cinco episodios largos restantes de la corrección recuperaron un ancla. El peor con GPS que siguió llegando fue `20441`: **215,5 s** hasta que volvió a aceptar un GPS, con **siete** muestras rechazadas repartidas en **184,7 s**. El máximo global de `20242`, **6 428,4 s**, incluye la persistencia hasta el cierre después de solo dos rechazos separados por **30,8 s**.

## Discontinuidades presentadas

Se mide el salto firmado de progreso en vía entre instantes consecutivos de replay, con la misma circulación y geometría. La tabla de población común compara ambos motores sobre las mismas transiciones. Las poblaciones elegibles propias incluyen los saltos que solo se pueden medir en una revisión. El corte de 200 m se aplica a la magnitud del salto. Los flujos conservan ambos sentidos de cruce.

| Población | n | p50 / p90 / máximo (m) | >200 m | >5 km |
|---|---|---|---|---|
| Base elegible | 39 973 | 0,0 / 58,7 / 51 363,5 | 2 587 | 32 |
| Corrección elegible | 40 017 | 0,0 / 31,7 / 28 884,4 | 2 474 | 10 |
| Base común | 39 973 | 0,0 / 58,7 / 51 363,5 | 2 587 | 32 |
| Corrección común | 39 973 | 0,0 / 29,8 / 28 884,4 | 2 461 | 10 |

| Estrato | Suben | Bajan | Iguales | ≤200 → >200 m | >200 → ≤200 m |
|---|---|---|---|---|---|
| Global | 75 | 396 | 39 502 | 22 | 148 |
| `STOPPED_AT` | 7 | 24 | 14 735 | 3 | 15 |
| `INCOMING_AT` | 5 | 10 | 15 251 | 2 | 6 |
| `IN_TRANSIT_TO` | 63 | 362 | 9 516 | 17 | 127 |
| ≤160 km/h | 30 | 161 | 9 121 | 11 | 88 |
| >160 km/h | 6 | 57 | 979 | 3 | 25 |
| Velocidad indeterminada | 39 | 178 | 29 402 | 8 | 35 |
| Con racha | 51 | 251 | 30 370 | 15 | 69 |
| Sin racha | 24 | 123 | 8 006 | 7 | 73 |
| Racha indeterminada | 0 | 22 | 1 126 | 0 | 6 |

De **97 694** transiciones candidatas, se excluyeron en base / corrección **249 / 249** por falta del vehículo en uno de los ticks y **57 472 / 57 428** por falta de progreso en vía. Las **22** subidas y **148** bajadas a través del corte de 200 m figuran en `paired_presentation_threshold_cases`, con el salto firmado y ambos extremos.

Hubo **0** pares exclusivos de la base y **44** de la corrección. En estos 44, la base publicó `schedule_only` en **56** extremos, todos con `off_track`. En el mayor (**+2 844,2 m** en `20775`, 08:13:21 UTC), la corrección aún mantenía el ancla de **08:11:30 UTC** al fallar el GPS de **08:12:30**, y ambas revisiones confirmaron el de **08:13:10**. Los **13** saltos exclusivos >200 m explican el paso de **2 461/39 973** en la población común a **2 474/40 017** en la población elegible completa de la corrección.

- **`20442`, peor discontinuidad común de la base.** A las **08:46:12,836749**, la base recuperó el GPS de **08:45:30** que había rechazado y presentó **+51 363,5 m**. La corrección aceptó el GPS de retorno de **08:46:10** y presentó **0 m**.
- **`20426`, peor discontinuidad de la corrección y mayor aumento de magnitud.** A las **08:04:37,806771**, el salto fue de **−123,0 → +28 884,4 m**. Después del GPS de **08:03:52**, la base ya extrapolaba desde ese GPS. La corrección aún mostraba **32,5 m** desde el ancla de **08:02:30**. Ambas confirmaron el GPS de **08:04:30** y presentaron **28 916,9 m**.

Cuatro vehículos tuvieron más saltos >200 m en pares comunes.

| Vehículo | Saltos >200 m base → corrección | Cambio de suma de magnitudes (m) |
|---|---|---|
| `20790` | 46 → 50 | -9 158,7 |
| `20236` | 29 → 30 | -1 418,2 |
| `20248` | 55 → 56 | -1 676,7 |
| `20249` | 16 → 17 | -2 648,6 |

## Discrepancia frente al GPS bruto

H1 se evalúa como en MP-025b y conserva el criterio **p50 ≤200 m con ≥500 pares**. Si la envolvente del GPS A existe en ambas revisiones, H1 común mide los pares con A aceptada como su propia ancla. B sigue siendo GPS bruto aunque se rechace. Para evaluar el efecto de retener un ancla se compara, aparte, la envolvente retenida al llegar A frente al GPS B a su hora de observación. Si el snapshot ya publica progreso congelado en vía, se usa ese valor. Se estratifica según si B repite o cambia la coordenada de A y se distinguen los reanclajes.

| Población H1 | n | p50 / p90 / máximo (m) | >200 m | >5 km |
|---|---|---|---|---|
| Base elegible | 10 057 | 0,0 / 1 181,2 / 51 363,5 | 2 043 | 27 |
| Corrección elegible | 9 940 | 0,0 / 1 062,8 / 51 363,5 | 1 930 | 26 |
| Base común | 9 916 | 0,0 / 1 063,0 / 51 363,5 | 1 922 | 25 |
| Corrección común | 9 916 | 0,0 / 1 063,0 / 51 363,5 | 1 922 | 25 |

El mayor H1 común fue **51 363,5 m**, en `20442` con GPS B de las 08:45:30 UTC. B fue sustituido por el ancla previa.

De **25 905** pares candidatos, **288** pierden la envolvente propia de A en ambas revisiones, **141** solo en la corrección y **24** solo en la base. El H1 común coincide par a par y, por construcción, carece de los casos con A rechazada por la corrección. Las exclusiones de H1 son disjuntas.

| Motivo de exclusión H1 | Base | Corrección |
|---|---|---|
| `intervalo_largo` | 46 | 46 |
| `sin_corredor` | 15 407 | 15 407 |
| `sin_plan_del_ancla` | 312 | 429 |
| `sin_proyeccion_valida` | 83 | 83 |

| Estrato H1 común | n | >200 m base → corrección |
|---|---|---|
| Global | 9 916 | 1 922 → 1 922 |
| `STOPPED_AT` | 6 002 | 372 → 372 |
| `INCOMING_AT` | 2 081 | 180 → 180 |
| `IN_TRANSIT_TO` | 1 833 | 1 370 → 1 370 |
| ≤160 km/h | 9 089 | 1 095 → 1 095 |
| >160 km/h | 827 | 827 → 827 |
| Velocidad indeterminada | 0 | 0 → 0 |
| Con racha | 7 725 | 1 085 → 1 085 |
| Sin racha | 2 084 | 825 → 825 |
| Racha indeterminada | 107 | 12 → 12 |

Dentro de `IN_TRANSIT_TO`, el H1 común superó 200 m en **578/641** pares con racha y **783/1 182** sin racha. Los **10** pares de racha indeterminada aportaron **9** casos >200 m.

En **141** pares H1 de la base, A pierde su propia envolvente con la corrección. Todos pudieron compararse con un ancla anterior, **6** de ellos en un reanclaje señalado. El contraste contiene **5** valores de progreso congelado. «B cambia» y «B repite» describen el movimiento que registra el GPS bruto entre A y B.

| Población del contraste adicional | n | p50 base → corrección (m) | >200 m base → corrección | >5 km base → corrección | Suben / bajan |
|---|---|---|---|---|---|
| Ancla retenida | 135 | 862,8 → 1 290,3 | 119 → 103 | 2 → 11 | 76 / 59 |
| B cambia de coordenada | 83 | 1 471,8 → 703,3 | 81 → 51 | 2 → 6 | 24 / 59 |
| B repite coordenada | 52 | 257,8 → 2 472,1 | 38 → 52 | 0 → 5 | 52 / 0 |
| Reanclaje al llegar A | 6 | 6,9 → 111,9 | 2 → 2 | 0 → 0 | 4 / 2 |

En los 135 pares con ancla retenida, **16** cruzaron hacia >200 m y **32** bajaron a ≤200 m. Con B repetido hubo **14 subidas y 0 bajadas** por ese corte. Con B cambiado hubo **2 subidas y 32 bajadas**. Dentro de `IN_TRANSIT_TO` aumentó la magnitud en **44/44** con B repetido, y subió en **23/76** y bajó en **53/76** con B cambiado.

El mayor aumento fue en `20426`, A de 08:03:52 y B de 08:04:30 UTC, **218,4 → 28 789,0 m**. El mayor descenso fue en `20250`, A de 09:10:10 y B de 09:10:50 UTC, **6 984,2 → 719,5 m**.

**GPS cuantizado.** Hubo **1 458** coordenadas distintas en **26 116/26 154** filas con coordenada. **24 338/26 116** filas con coordenada ocuparon puntos usados por al menos tres vehículos. **20 643/25 829** pares GPS consecutivos comparables repitieron exactamente la coordenada. Por ello, reducir un salto mostrado y alejarse de un GPS repetido pueden ocurrir en la misma transición.

## Comparación con la jornada 1

Cada celda presenta base → corrección. El suplemento operativo de la jornada 1 usa sus dos segmentos originales. Los campos de resultados que comparte con `mp038-delta-r2-verificado.json` coinciden.

| Medida | Jornada 1 · 26 nov | Jornada 2 · 27 nov |
|---|---|---|
| GPS con motor al llegar | 12 014 en ambas | 10 567 en ambas |
| Recuperaciones / episodios | 334/370 → 347/352 | 306/341 → 317/325 |
| Tiempo hasta recuperación, p50 / p90 / máximo (s) | 30,8 / 30,9 / 61,8 → 30,9 / 92,5 / 431,1 | 30,8 / 30,9 / 35,9 → 30,8 / 61,7 / 215,5 |
| Reapariciones A→B→A tras rechazo | 6/416 → 0/416 | 5/373 → 0/373 |
| Promociones sin señal / reanclajes señalados | 17 / 0 → 0 / 3 | 16 / 0 → 0 / 6 |
| Fotogramas con ancla más antigua en la corrección y aumento p50 / p90 / máximo | 907/35 594 · 60 / 140 / 438 s | 1 932/40 117 · 78 / 120 / 220 s |
| Retenciones >180 s / episodios | 1/370 → 11/352 | 3/341 → 12/325 |
| Retenciones >180 s censuradas | 1/1 → 2/11 | 3/3 → 7/12 |
| Saltos >200 m en pares comunes | 2 935/35 383 → 2 771/35 383 | 2 587/39 973 → 2 461/39 973 |
| Cruces de 200 m ↑ / ↓ en pares comunes | 24 / 188 | 22 / 148 |
| Saltos >200 m en pares exclusivos de la corrección | 17/53 | 13/44 |
| H1 común, p50 y pares | 0 m en 11 206, en ambas | 0 m en 9 916, en ambas |
| Retención frente a GPS bruto, discrepancia ↑ / ↓ | 127 / 89 en 216 | 76 / 59 en 135 |
| GPS siguiente repetido, discrepancia ↑ / ↓ | 113 / 0 en 113 | 52 / 0 en 52 |
| GPS siguiente cambiado, discrepancia ↑ / ↓ | 14 / 89 en 103 | 24 / 59 en 83 |

En ambas jornadas la corrección redujo los saltos grandes en pares comunes y aumentó las retenciones >180 s. En la jornada 2 aumentó el máximo de discontinuidad residual (**13 016 → 28 884 m** entre jornadas) y hubo más retenciones prolongadas censuradas (**2 → 7** con la corrección).

## Entradas, aislamiento y reproducción

El dump de la jornada 2 es **acumulativo**. El arnés selecciona runs cuya hora `started_at` pertenece al intervalo semiabierto **[2026-11-27 07:54:13,087033, 09:54:51,084788) UTC**. Las vistas temporales restringen los runs y, por sus claves, los GPS y las actualizaciones de viaje visibles al API. El modelo de prefijos de MP-036 para la jornada 2 aplica el mismo intervalo en SQL. Los GPS generados justo antes del inicio pueden pertenecer al primer run de la sesión. La unidad de pertenencia es el run y el replay usa tanto la hora GPS como la de ingesta. Se incluyeron **705 runs de IDs 769–1473**, 235 por feed, todos `ok`. Se excluyeron los **768** runs anteriores. `session_audit.feeds` conserva los IDs exactos por feed. La captura duró 7 238 s civiles, con **7 230,097 s** de cobertura efectiva, sin huecos en los tres feeds y con **249** vehículos distintos. El colector era `7300003` y el GTFS `58ac5543…`. El arnés procesó **26 154** filas GPS y **509** instantes. Hubo cobertura de corredor en **100/249** vehículos.

| Feed | Runs | Primer y último ID |
|---|---:|---:|
| Posiciones | 235 | 769 y 1471 |
| Actualizaciones de viaje | 235 | 770 y 1472 |
| Alertas | 235 | 771 y 1473 |

Como parte de la custodia se verificó el SHA-256 de ambos dumps y se ejecutó `cmp` contra el original en `data/capture/2026-11-27/session-1/capture.dump`. Se hizo una copia temporal para restaurar. PostGIS `postgis/postgis:17-3.5` se levantó con `--pull=never`, en **127.0.0.1:5470**, DSN local `postgresql://mp_test:mp_local@127.0.0.1:5470/mp038`. La consulta de aislamiento devolvió `mp038|public|mp_test|madrid-pulse:disposable`. La suite usó su propio contenedor marcado, con base `mp038_ci`, en el mismo puerto. Los procesos ejecutaron el arnés compartido y el producto de sus propios checkouts, con sus procedencias registradas en `inputs.module_origins`. El replay usó `display_lag_s=0`.

Las dos ejecuciones definitivas fijaron `plan_cache_mode=force_custom_plan` en su conexión de replay. La primera tentativa se detuvo antes de publicar JSON porque el plan genérico de PostgreSQL degradaba el rendimiento con el volcado acumulativo. Una consulta local de historial devolvió las mismas 497 filas en 4,37 s con plan genérico y en 0,06 s con plan específico. El cambio de planificación se aplica a la conexión desechable y conserva las consultas, las vistas de filtrado y la configuración de movimiento.

```bash
repo_original=/Users/matu/Documents/DATA/madrid-pulse
captura="$repo_original/data/capture/2026-11-26"
sesion="$repo_original/data/capture/2026-11-27/session-1"
gtfs="$repo_original/data/gtfs_static/fomento_transit.zip"
export MP038_PYTHON="$repo_original/.venv/bin/python" MP038_PORT=5470
(
    cd "$repo_original"
    shasum -a 256 -c "data/capture/2026-11-26/analysis/mp038-jornada2-custodia.sha256"
)
cmp "$captura/analysis/session-2-20261127T095451Z.dump" "$sesion/capture.dump"
for id in jornada2-revision jornada2-revision-replica; do
    docs/evidence/mp-038/run.sh "$captura" "$gtfs" "$id" --jornada2 "$sesion"
done
(
    cd "$captura/analysis"
    cmp mp038-jornada2-revision.json mp038-jornada2-revision-replica.json
    shasum -a 256 -c mp038-jornada2-revision.json.sha256 mp038-jornada2-revision-replica.json.sha256
)
docs/evidence/mp-038/run.sh "$captura" "$gtfs" jornada1-operativa-revision --operativa-j1
(
    cd "$repo_original"
    shasum -a 256 -c "data/capture/2026-11-26/analysis/mp038-jornada2-custodia.sha256"
)
```

`--operativa-j1` repite la instrumentación de recuperación, duración y antigüedad sobre el volcado y manifiesto originales de la jornada 1 para obtener columnas directamente comparables. Genera un resultado nuevo. Para reproducir el SHA exacto de los resultados, la traza identifica el checkout de la corrección como `39166da`. El producto coincide con `0c518fa`; el arnés del presente informe se aplicó sobre ese checkout. `inputs.heads` refleja el commit desde el que se ejecute una réplica posterior.

| Archivo | SHA-256 |
|---|---|
| `analysis/session-2-20261127T095451Z.dump` y `2026-11-27/session-1/capture.dump` | `6a325074c48c021428084af9741772187204f8abc8862cd22376e7ff922ca75f` |
| `2026-11-27/session-1/manifest.json` | `60cabc28a997d8bc0b28c6c2ac11890214932c6091bcc06ebf1923fddab18cbe` |
| `fomento_transit.zip` | `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e` |
| `analysis/mp038-jornada2.json` y `analysis/mp038-jornada2-replica.json` | `55b5e285208ede33f0dd2169fe15985cf504a3f69b45d0ae89a9daf9c0df485f` |
| `analysis/mp038-jornada1-operativa.json` | `821a5b91cf438fd9ec492488c140be7bb6253ef8c7550de027800446d2613b1e` |
| `analysis/mp038-jornada2-custodia.sha256` | `87f4ffadb5c0778515982b5ac57837cdff9bcdc81f729d7200cf104f30497065` |

Los JSON y sus hashes están en el directorio original de capturas, fuera de Git. El inventario de custodia conserva los hashes previos al primer replay con rutas relativas al repositorio original. Incluye los archivos preexistentes bajo `data/capture/2026-11-26/` y los originales de la sesión del 27.

## Verificación y límites

| Comando o comprobación | Resultado |
|---|---|
| `run.sh … jornada2 --jornada2 "$sesion"` y `run.sh … jornada2-replica --jornada2 "$sesion"` y `cmp` y ambos `.sha256` | **PASS**. Dos restauraciones independientes y JSON idénticos byte a byte. |
| `run.sh … jornada1-operativa --operativa-j1` | **PASS**. Suplemento comparativo sobre el dump original. |
| `shasum -a 256 -c` antes y después sobre el inventario de la jornada 1 y los originales de la jornada 2 y `cmp` del dump contra el original y la copia temporal | **PASS**. Los 129 ficheros preexistentes del inventario conservan sus hashes. |
| `python -m unittest -v $(awk '/^            (apps\|packages\|services\|tests)\./ {print $1}' .github/workflows/ci.yml) infra.operate.validation.test_metrics tests.governance.test_governance` | **PASS**, `Ran 385 tests`, `OK (skipped=5)`. Se usó `MADRID_PULSE_REQUIRE_DB=1` y el [ZIP enlazado en las dos rutas de la suite](README.md#reproducción-y-custodia). Las cinco pruebas del soak MP-007 quedaron **NO EJECUTADAS** por falta de su población específica. |
| `python -m unittest -v infra.operate.validation.test_mp038 infra.operate.validation.test_mp038_session` | **PASS**, `Ran 17 tests`, `OK`. Incluye la detección de reapariciones, el caso censurado, la recuperación, la exclusión del GPS bruto al medir edad y la cuantización. |
| `npm ci --offline --no-audit --no-fund`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` con Node 22.13.1 | **PASS**, 11 archivos y 110 pruebas. El build validó el worker MapLibre (550 754 bytes) y emitió un aviso de tamaño de chunk. |
| `ruff check infra/operate/validation`, `python -m compileall -q infra/operate/validation`, `python scripts/governance/check_docs.py`, `bash -n docs/evidence/mp-038/run.sh`, `git diff --check` | **PASS**, `All checks passed!`, `Documentación de gobernanza correcta.` y códigos 0. |
| `test_segments` en el puerto histórico de MP-025b | **NO EJECUTADO**. Ambos replays invocaron `check_segment` contra las vistas temporales. |
| `docker rm -fv`, inspección de contenedores y volúmenes, `lsof -nP -iTCP:5470 -sTCP:LISTEN` y retirada de worktrees | **PASS**. Contenedores, volúmenes, escucha y checkouts temporales ausentes. |

El GPS publicado por el feed permite medir discrepancias. La posición y la puntualidad físicas quedan **UNVERIFIED**, al igual que el efecto en el navegador con latencia e interpolación reales, la generalización a otros horarios, corredores y jornadas, y el cumplimiento integral de FR-01. Se mantienen el criterio de MP-025b y los parámetros prerregistrados. La entrega queda pendiente de la única verificación de Claude `claude-opus-5-5` · high. Orca registró Codex `gpt-6.2-sol` · medium para la ejecución.
