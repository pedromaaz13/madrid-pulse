# MP-037 · Contradicciones entre estado de parada y GPS

**Estudio offline de una jornada, para revisión independiente.** FR-01 sigue abierto y el NO-GO público sigue vigente.

## Diseño de la comparación

M7 en [ADR-0014, enmienda 1 §3 y §8](../../adr/0014-amendment-stop-state.md) pregunta, con la **siguiente** observación ya disponible, si la primera envolvente predijo exactamente cero avance ante ≥100 m de avance del GPS entre muestras. R4 decide en el **primer** instante si retiene un `INCOMING_AT` cuyo GPS efectivo ya está en zona de su parada declarada. Ejecutar «R4 antes de M7» equivale al control. Convertir M7 en una excepción en tiempo real requeriría una señal causal especificada aparte. Las variantes usan el GPS y el horario ya disponibles para cada ancla.

| Política | Regla de ensayo |
|---|---|
| `control` | Renderizador de producción. R-CANCEL, clasificación, R1, R4, R6x, R6, R2 y R5, con R7→R8 para estados incoherentes. |
| `sin_r4` | Suprime R4 en todas sus activaciones. Pasa a R6x, R6, R2 y R5 sin espera de zona. Es una referencia para medir el coste de quitar la guarda. |
| `r4_r8` | Sustituye las activaciones de R4 por R8, incluida la espera programada de zona cuando corresponde. |
| `r4_dos_gps` | Deriva a R8 solo cuando hay muestra previa de zona utilizable, anterior a la efectiva y con edad ≤ horizonte vigente, y esa proyección queda fuera de la zona de la ocurrencia declarada. Con muestra previa dentro de zona o sin evidencia previa utilizable, se conserva R4. |
| `parada_previa` | En `STOPPED_AT` incoherente con plan positivo, exige un `stop_id` que resuelva una sola ocurrencia y una muestra previa de zona utilizable y reciente dentro de τ de ella. Retiene en el progreso del **GPS efectivo** durante su horizonte, con `coherent=false`. |
| `gps_previo` | Usa el mismo disparador que `parada_previa` y retiene a la altura de la proyección del **GPS previo** admitido para esa zona. La coordenada proviene solo de esa muestra. La selección de casos sigue condicionada por el estado del operador y su parada declarada. |

**Invariante de R4.** El GPS efectivo y aceptado debe quedar dentro de τ de la ocurrencia declarada. El arnés comprueba la condición en cada activación de R4.

Las variantes de R4 invocan el constructor de producción con el contexto de tránsito o degradación correspondiente. Esa sustitución interna sirve para obtener una curva hipotética. El arnés conserva la etiqueta del operador de la observación original en sus registros. Resuelve la ocurrencia según §4.1 y reutiliza `zone_sample` calculado por la API. La muestra aporta una proyección de la coordenada anterior, cuya aceptación previa como ancla y cuyo estado por parte del operador son señales independientes. Un identificador ausente, ajeno al viaje o con ocurrencias repetidas queda sujeto a la política vigente. [Constructor de producción](../../../packages/movement/rendering.py#L180) y [selección de muestra previa](../../../apps/api/snapshot.py#L446).

Se contrastó P-024 con el manifiesto. Horizonte de 180 s, distancia a vía de hasta 200 m, tope de velocidad estimada de 160 km/h, zona de 50 m, espera mínima de 30 s y edad máxima de cancelación de 600 s. Los 100 m de M7 y los 200 m de salto son criterios de auditoría heredados. [Parámetros de producción](../../../packages/movement/model.py#L39), [decisión del propietario](../../adr/0014-amendment-owner-decision.md) y [métricas de MP-025b](../mp-025b/README.md).

### Población y unidades de medida

Se reutilizan el replay y las vistas temporales de [MP-025b](../mp-025b/README.md). Dos segmentos de 9 340 y 20 167 filas, con reinicio de historial tras la suspensión. Se aplican los filtros de MP-025b a los 29 095 pares consecutivos de los 347 vehículos, con 11 425 pares H1 evaluables y 516 instantes de replay. El control comprueba contra MP-025b las exclusiones, la distribución H1, los recuentos de casos, las salidas retenidas y su distribución de latencia. Las políticas reciben la misma selección de observaciones, servicio y geometría. El proceso instrumenta el constructor de envolventes en memoria. La selección del ancla, las anomalías, la cancelación y las respuestas originales quedan a cargo de producción. Las variantes se proyectan en progreso dirigido sobre el mismo corredor.

- **Avance en `STOPPED_AT`.** La proporción de planes con velocidad positiva mide autorización de avance. En la cohorte de contradicciones se mide también cuánto se habría presentado al primer fotograma y antes del recambio del ancla, incluido el tiempo en fase de avance. Los casos con GPS idéntico entre observaciones dan una medida adicional de sobreavance potencial. La identidad de coordenadas puede deberse a cuantización.
- **Retención y latencia.** `STOPPED_AT` cuenta pares con desplazamiento GPS proyectado hacia delante >0 m. `INCOMING_AT` e `IN_TRANSIT_TO` cuentan M7 (≥100 m). Hay retención cuando la curva de A predice avance cero desde su referencia a la hora GPS de B. La latencia va desde esa hora hasta el primer fotograma de replay del mismo viaje/día en el que el ancla efectiva, al menos tan reciente como B, y la curva presentada están por delante del ancla efectiva de A. Un retorno del ancla efectiva a la posición inicial o el fin de la ventana puede dejar la latencia sin resolver. La comparación de cuantiles incluye solo los retenidos con latencia evaluable para cada política.
- **Error H1 con GPS de destino.** Distancia absoluta en metros de progreso dirigido entre el pronóstico de A y la proyección del GPS B, a la hora GPS de B. Incluye GPS B proyectables que el motor rechaza como ancla.
- **Discontinuidad al presentar B.** Diferencia firmada de progreso en el instante de visibilidad de B entre el fotograma hipotético de B y la continuación del plan de A. Los dos anclajes deben ser efectivos en fotogramas consecutivos del vehículo, del mismo viaje, día y versión de geometría. La continuación de A se congela al llegar a su horizonte F1. Un valor negativo es un retroceso. Si B se rechaza, falta la transición A→B y ese par queda fuera del denominador de discontinuidad. La unidad es arco dirigido, y la percepción del salto en el navegador permanece UNVERIFIED.
- **Plausibilidad y racha GPS.** La velocidad aparente es el desplazamiento absoluto de arco dividido por el intervalo GPS. Se contrasta con el tope de **160 km/h** de la estimación. Es un filtro descriptivo y no cambia la selección del motor. La racha de A mide el tiempo desde la primera coordenada bruta idéntica consecutiva del mismo vehículo y viaje dentro del segmento. Un valor >0 s requiere al menos dos observaciones. Los GPS ausentes, el cambio de viaje y los cortes de segmento rompen la racha. Una coordenada se considera compartida si figura exactamente igual en tres o más vehículos distintos del ámbito indicado.

## Resultados

### Los 19 planes positivos con `STOPPED_AT`

Fueron **19/18 242** declaraciones y **19/7 001** con envolvente propia, en 17 vehículos. Hubo 20 planes con GPS fuera de la zona declarada, uno con velocidad cero, y 6 981 planes coherentes, todos con velocidad cero. Las otras 11 241 declaraciones carecían de envolvente propia. En los 19 casos el GPS efectivo se proyectó **709,5–7 110,2 m hacia delante** de la parada que declaraba el operador. Los 19 GPS iniciales se aceptaron como ancla. R7 marcó la contradicción y R8 generó 16 curvas con espera de zona de horario y tres curvas de avance por horario sin espera, a **8,44–14,35 m/s**.

Los 19 GPS brutos de A se concentran en seis puntos fijos, uno por `stop_id` declarado. La menor distancia geodésica de cada punto a las coordenadas de parada del catálogo GTFS cae en **otra** estación, a **7,6–38,3 m**. Esto concuerda con el patrón de GPS fantasma de MP-025b. El último punto publicado ya aproxima una estación distinta de la declarada. Su proximidad al GTFS no verifica la posición real del vehículo.

| `stop_id` en A | Planes positivos | Otra estación GTFS más cercana a A | Qué publicó el siguiente GPS del mismo segmento |
|---|---:|---|---|
| 35605 | 8 | 35610 · Las Retamas · 21,5 m | Siete conservaron `STOPPED_AT/35605`, a −2,5 m de su parada. Los siete GPS fueron sustituidos por el ancla anterior. Uno quedó al final del segmento. |
| 35600 | 5 | 35601 · Maestra Justa Freire · 7,6 m | Cinco conservaron `STOPPED_AT/35600`, a −16,9 m. Se marcaron por retroceso y los cinco se aceptaron como ancla. |
| 17003 | 3 | 17009 · Universidad-Cantoblanco · 19,4 m | Tres conservaron `STOPPED_AT/17003`, a +2,9 m. Los tres GPS fueron sustituidos por el ancla anterior. |
| 17001 | 1 | 17000 · Madrid-Chamartín · 34,3 m | `20428` cambió a `STOPPED_AT/17000` en la misma coordenada bruta. |
| 60100 | 1 | 18000 · Madrid-Atocha Cercanías · 10,7 m | `20437` cambió a `STOPPED_AT/18000` en la misma coordenada bruta. |
| 18003 | 1 | 18000 · Madrid-Atocha Cercanías · 38,3 m | `20721` quedó al final del primer segmento. |

En **15/19** la siguiente fila apoya la parada declarada, con regreso a ≤17 m y el mismo `stop_id`. **10/15** de esos GPS se rechazaron para presentación (`backward_jump`). Los dos cambios de `stop_id` con GPS intacto y los dos cortes sin sucesor dejan especialmente ambiguo dónde estaba el tren. En los 19 planes, el avance máximo autorizado hasta caducar tuvo p50 **2 232,27 m** y máximo **2 468,83 m**. La distancia desde el ancla hasta el recambio o el fin del segmento fue positiva en **16/19**, p50 **660,63 m** y máximo **1 024,27 m** sobre los 19. Al contar solo desde el primer fotograma, la curva avanzó hasta **885,91 m** y permaneció en fase de avance hasta **61,78 s** (p50 **50,31 s**). El tiempo visible del ancla, incluida cualquier espera, tuvo p50 **61,46 s**, máximo **64,98 s** y dos casos censurados.

El peor avance antes del recambio fue `20434`, GPS de **08:33:30 UTC**, `STOPPED_AT/17003`: la proyección saltó a **17 765,91 m**, frente a **15 435,09 m** de la parada, y se rechazó el siguiente GPS (**15 438,00 m**). La envolvente efectiva siguió avanzando hasta **1 024,27 m** adicionales antes de salir de presentación. El caso `19595` a **08:20:52 UTC** ilustra el alcance de `parada_previa`: mantiene la proyección efectiva de **32 677,18 m**, a **709,47 m** de `35600`. Suprime **31,31 m** de extrapolación y conserva la corrección posterior al GPS aceptado de **31 950,77 m**. Esa corrección sigue siendo de **−726,42 m** en el arco.

En **13/19** el GPS inmediatamente anterior del volcado tiene la misma coordenada fantasma. **12/19** están dentro de los segmentos admitidos para el replay. El decimotercero es `20741` a las 07:34:52 UTC. Su muestra previa, a las 07:34:30 UTC, quedó fuera por el inicio del segundo segmento a las 07:34:33,343268 UTC. La observación excluida aporta contexto sobre el feed y quedó fuera de las políticas y sus métricas. [Corte del segmento en MP-025b](../mp-025b/README.md).

**Efecto medido de las dos variantes.** Ambas cambian **6/19** planes. Solo cinco, todos para `35600`, alcanzaban avance efectivo con el control. El sexto es `20437`, cuya espera ya duraba hasta el siguiente GPS. La suma de avance desde el ancla hasta su recambio o corte baja de **9 894,3 a 9 509,5 m** en la cohorte, una reducción de **384,8 m** (3,9 %). Con `parada_previa`, los cinco retrocesos de `35600` se reducen de 758–830 m a **726,41 m** cada uno. El número de saltos >200 m en pares que empiezan en `STOPPED_AT` sigue en **490/6 903**.

| Casos | Salto de entrada hacia A, control / `parada_previa` / `gps_previo` | Salto al siguiente GPS, control / `parada_previa` / `gps_previo` |
|---|---|---|
| Cinco `35600` | +726,41 / +726,41 / 0 m, cada uno | −830,09 a −757,72 / −726,41 / 0 m |
| `20437`, `60100→18000` | +7 110,17 / +7 110,17 / 0 m | 0 / 0 / +7 110,17 m |

En los cinco `35600`, la proyección del GPS previo (31 950,77 m) y la del siguiente GPS aceptado coinciden, a **−16,94 m** de `35600`. Mantener ese punto elimina ambos saltos del episodio en el arnés. En `20437` difiere del siguiente GPS y traslada el salto a la transición posterior. En conjunto, `gps_previo` pasó de **490 a 486** saltos >200 m en los **6 903** pares que empiezan en `STOPPED_AT`. Los otros **seis** saltos >200 m que elimina entran por `INCOMING_AT` y eran oportunidades M7. Ninguna de las seis anclas intervenidas inicia una oportunidad de salida `STOPPED_AT`.

La variante conserva la selección de ancla del motor y muestra la proyección previa como posición derivada. En esas seis entradas M7, B es efectivo y la posición mostrada coincide con el ancla inicial de la oportunidad. El predicado del estudio termina esos episodios sin resolver su latencia. Resultaron evaluables **129/135** con `gps_previo`, frente a **135/135** con el control. Los saltos >200 m bajan de 45 a **40/45** en el grupo ≤160 km/h y de 90 a **89/90** en el grupo >160 km/h. La salida física sigue UNVERIFIED.

### Las 135 retenciones M7

**135/1 441** oportunidades M7, en **73 vehículos**, empezaron por `INCOMING_AT` en la zona de la parada declarada. La distancia inicial a la parada tuvo p50 **2,91 m** y máximo **21,84 m**. Las 135 retenciones tuvieron avance presentado de cero antes de B. El intervalo GPS A→B tuvo p50 **40 s**, p90 **42 s** y máximo **60 s**. Desde el primer fotograma ya visible de A al que mostró B, p50 **30,82 s** y máximo **61,57 s**. El avance bruto proyectado tuvo p50 **1 916,02 m**, p90 **3 046,34 m** y máximo **7 110,17 m**.

En **90/135** la velocidad aparente supera 160 km/h. Sobre las 135, la mediana es **58,6 m/s** y el máximo **740,5 km/h**. En **114/135**, A ya cerraba una racha de la misma coordenada, con p50 **60 s** y máximo **400 s** entre la primera muestra idéntica de la racha y A. **135/135** puntos A y **134/135** puntos B fueron compartidos por al menos tres vehículos. En todo el volcado, incluidas las filas del smoke fuera de la sesión, **28 488/29 817** filas GPS con coordenada (**95,5 %**) ocupan puntos compartidos, sobre **1 392** coordenadas distintas. Solo en la ventana de sesión, son **28 311/29 605** (**95,6 %**), en **1 364** coordenadas distintas, con la misma cobertura compartida de A y B. Esta densidad y las rachas hacen compatible la magnitud de los desplazamientos con un cambio entre puntos discretos del feed, aun cuando el motor acepte ambas muestras.

| Estado GPS de B | Mismo `stop_id` | Otro `stop_id` | B publicado como ancla efectiva |
|---|---:|---:|---:|
| `INCOMING_AT` | 2 | 112 | 114/114 |
| `STOPPED_AT` | 6 | 9 | 15/15 |
| `IN_TRANSIT_TO` | 5 | 1 | 6/6 |
| Total | 13 | 122 | 135/135 |

La mayor discontinuidad del control en este grupo fue `20233`, de `INCOMING_AT/60100` a `INCOMING_AT/18000` a **07:49:30 UTC**. Las coordenadas brutas cambiaron de latitud 40,352676 y longitud −3,684073 a latitud 40,406540 y longitud −3,689511 en **40 s**. Ambos GPS fueron aceptados. El control corrigió **+7 110,17 m**, frente a **+6 653,30 m** al sustituir R4 por R8 y **+6 587,78 m** al omitir R4. El peor H1 del estrato completo de `INCOMING_AT` fue `20213` a **06:11:10 UTC**, con desplazamiento proyectado de **−23 633,99 m**, `backward_jump/implausible_speed` y reutilización del ancla efectiva. El signo lo excluye de M7 y el rechazo excluye la transición A→B de la discontinuidad. Se conserva como caso adverso en el H1 de todas las políticas.

### Comparación por política y estado de A

Las tablas dan p50 / p90 / máximo en segundos para la latencia y en metros para los errores y saltos. `GPS idéntico` cuenta pares con avance derivado positivo frente a coordenadas brutas repetidas. `Salto >200` cuenta el valor absoluto de la discontinuidad.

| Política y estado | Planes positivos | Retenciones / oportunidades | Latencia, n | Avance con GPS idéntico |
|---|---:|---:|---|---:|
| Control, `STOPPED_AT` | 19/7 001 | 402/402 | 8,32 / 17,27 / 49,04 (402) | 0/6 499 |
| `parada_previa` y `gps_previo`, `STOPPED_AT` | 13/7 001 | 402/402 | 8,32 / 17,27 / 49,04 (402) | 0/6 499 |
| Control, `INCOMING_AT` | 18/2 335 | 135/136 | 9,10 / 17,91 / 21,88 (135) | 5/2 053 |
| `gps_previo`, `INCOMING_AT` | 18/2 335 | 135/136 | 9,10 / 18,51 / 21,88 (129) | 5/2 053 |
| `r4_dos_gps`, `INCOMING_AT` | 759/2 335 | 127/136 | 9,41 / 18,75 / 21,88 (127) | 259/2 053 |
| `r4_r8`, `INCOMING_AT` | 2 153/2 335 | 11/136 | 15,83 / 19,50 / 20,98 (11) | 1 327/2 053 |
| `sin_r4`, `INCOMING_AT` | 2 153/2 335 | 0/136 | — (0) | 1 908/2 053 |
| Todas, `IN_TRANSIT_TO` | 2 289/2 291 | 0/1 305 | — (0) | 452/452 |

Cada variante cambia únicamente planes del estado al que se dirige. El salto presentado depende también del plan de B y puede cambiar en pares que empiezan en otro estado. Las 402 oportunidades de `STOPPED_AT` pertenecen a los **6 918** pares H1 del estrato. Los 402 desplazamientos alcanzan 100 m. Tres B se rechazaron inicialmente y el máximo de **49,04 s** corresponde a `20793`, con el GPS B proyectado **+21 511,83 m**, rechazado por `implausible_speed`. Solo `gps_previo` deja casos retenidos con latencia sin resolver en esta captura.

| Política y estado | Error H1 p50 / p90 / máx. | Salto presentado p50 / p90 / máx. | Salto >200 m | Retrocesos |
|---|---:|---:|---:|---:|
| Control, `parada_previa` y `r4_dos_gps`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 23,59 / 7 842,46 (6 903) | 490/6 903 | 5/6 903 |
| `gps_previo`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 14,77 / 7 842,46 (6 903) | 486/6 903 | 0/6 903 |
| `r4_r8`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 28,31 / 7 842,46 (6 903) | 491/6 903 | 5/6 903 |
| `sin_r4`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 28,31 / 7 842,46 (6 903) | 493/6 903 | 5/6 903 |
| Control y `parada_previa`, `INCOMING_AT` | 0 / 0 / 23 633,99 (2 267) | 0 / 110,55 / 7 110,17 (2 216) | 179/2 216 | 35/2 216 |
| `gps_previo`, `INCOMING_AT` | 0 / 0 / 23 633,99 (2 267) | 0 / 104,21 / 7 110,17 (2 216) | 173/2 216 | 35/2 216 |
| `r4_dos_gps`, `INCOMING_AT` | 0 / 162,12 / 23 633,99 (2 267) | 0 / 246,90 / 7 110,17 (2 216) | 300/2 216 | 654/2 216 |
| `r4_r8`, `INCOMING_AT` | 181,41 / 578,97 / 23 633,99 (2 267) | 260,34 / 586,54 / 6 659,34 (2 216) | 1 216/2 216 | 1 473/2 216 |
| `sin_r4`, `INCOMING_AT` | 350,16 / 750,58 / 23 633,99 (2 267) | 382,91 / 771,96 / 6 587,78 (2 216) | 1 850/2 216 | 1 937/2 216 |
| Todas salvo `sin_r4`, `IN_TRANSIT_TO` | 499,77 / 2 188,64 / 18 620,72 (2 240) | 372,43 / 1 660,64 / 6 588,29 (1 996) | 1 400/1 996 | 939/1 996 |
| `sin_r4`, `IN_TRANSIT_TO` | 499,77 / 2 188,64 / 18 620,72 (2 240) | 382,99 / 1 715,38 / 6 588,29 (1 996) | 1 436/1 996 | 871/1 996 |

Dentro de los 135 casos originales de M7, los saltos >200 m siguieron en **135/135** con todas las políticas salvo `gps_previo` (**129/135**). El máximo absoluto de `r4_r8` en `INCOMING_AT` se dio en `20237`, con `60100→18000` en el GPS de **08:07:30 UTC**. En `sin_r4` el máximo fue el mismo caso `20233` que en el control, con **+6 587,78 m**. En `STOPPED_AT` el máximo observado al presentar B fue `20430` a **08:52:10 UTC** y en `IN_TRANSIT_TO` fue `19588` a **07:56:10 UTC**. Las **310** segundas proyecciones sustituidas por un ancla anterior siguieron disponibles para H1, con el estado y las banderas de producción conservados.

### M7 por velocidad aparente y racha previa

Se cruzan velocidad y racha sobre **todos los 4 507 pares H1** cuyo A era `INCOMING_AT` o `IN_TRANSIT_TO`, y sobre su subconjunto de **1 441 oportunidades M7**. Cada celda de cuatro valores sigue el orden **control / sin R4 / R4→R8 / R4 con dos GPS**. Los cuantiles restantes, los recuentos de `parada_previa` y `gps_previo`, y los estratos marginales completos están en `m7_strata` del JSON. Los cuatro cruces son disjuntos.

| Cruce en todos los pares H1 | N H1 | H1 p50, m | N salto | Salto p50, m | Saltos >200 m |
|---|---:|---|---:|---|---|
| ≤160 km/h · sin racha | 1 876 | 10,8 / 273,2 / 88,9 / 85,1 | 1 843 | 5,4 / 279,7 / 85,5 / 122,6 | 560 / 1 239 / 605 / 681 |
| ≤160 km/h · con racha | 1 888 | 0 / 368,0 / 293,3 / 0 | 1 848 | 0 / 396,5 / 367,9 / 0 | 499 / 1 526 / 1 491 / 499 |
| >160 km/h · sin racha | 293 | 1 865,5 / 1 752,6 / 1 801,0 / 1 801,0 | 165 | 1 234,8 / 1 287,1 / 1 233,3 / 1 233,3 | 164 / 165 / 164 / 164 |
| >160 km/h · con racha | 450 | 2 076,3 / 1 959,8 / 2 013,3 / 2 076,3 | 356 | 1 837,9 / 1 819,0 / 1 802,4 / 1 837,9 | 356 / 356 / 356 / 356 |

| Cruce en oportunidades M7 | N oportunidades y H1 | Retenciones | H1 p50, m | N salto | Salto p50, m | Saltos >200 m |
|---|---:|---|---|---:|---|---|
| ≤160 km/h · sin racha | 663 | 4 / 0 / 3 / 3 | 106,4 / 106,4 / 106,4 / 106,4 | 663 | 56,6 / 136,7 / 56,6 / 56,6 | 245 / 277 / 245 / 245 |
| ≤160 km/h · con racha | 262 | 41 / 0 / 0 / 41 | 622,5 / 580,9 / 580,9 / 622,5 | 262 | 642,8 / 582,7 / 583,0 / 642,8 | 222 / 223 / 222 / 222 |
| >160 km/h · sin racha | 157 | 17 / 0 / 8 / 10 | 1 426,6 / 1 373,5 / 1 426,6 / 1 426,6 | 155 | 1 290,3 / 1 345,9 / 1 287,1 / 1 287,1 | 154 / 155 / 154 / 154 |
| >160 km/h · con racha | 359 | 73 / 0 / 0 / 73 | 1 880,7 / 1 837,9 / 1 854,2 / 1 880,7 | 356 | 1 837,9 / 1 819,0 / 1 802,4 / 1 837,9 | 356 / 356 / 356 / 356 |

Sobre **las 135 retenciones del control**, las cuatro políticas conservaron 45/45 saltos >200 m en el estrato ≤160 km/h y 90/90 en el estrato >160 km/h. Sí cambió su magnitud. En las 45 del primer estrato, la mediana del salto fue **1 290,3 / 852,4 / 894,5 / 1 290,3 m**. La latencia p50 de los casos aún retenidos fue **6,2 / — / 15,9 / 6,1 s** (n = 45 / 0 / 3 / 44). En el estrato >160 km/h, la latencia p50 fue **11,9 / — / 15,7 / 12,3 s** (n = 90 / 0 / 8 / 83). Esta mejora de magnitud en las retenciones originales coexiste con más saltos al quitar R4 entre el resto de pares de velocidad aparente ≤160 km/h.

## Recomendación

**En esta jornada, R4 produjo menos discontinuidades de presentación frente al feed discretizado.** El control tiene 179/2 216 saltos >200 m en `INCOMING_AT`, frente a 1 850/2 216 sin R4 y 1 216/2 216 con R8. De las 135 retenciones originales, 45 quedaron dentro del tope de 160 km/h. En esas 45, el control retuvo 45 con latencia p50 **6,2 s**, `sin_r4` retuvo 0 y `r4_r8` retuvo 3. Los saltos >200 m permanecieron en **45/45** en las tres variantes. Recomendamos conservar R4 como criterio de presentación mientras se repite la comparación y seguir informando M7 como guarda retrospectiva. La exactitud respecto al movimiento físico permanece UNVERIFIED.

**Mantener `parada_previa` y `gps_previo` como candidatas pendientes de las jornadas 2 y 3.** `parada_previa` elimina 384,8 m de avance derivado sobre los 9 894,3 m acumulados por los 19 casos y conserva la coordenada fantasma del GPS efectivo. `gps_previo` coloca la posición derivada en una observación anterior e intercambia discontinuidades de llegada y salida. Ambos ensayos conservan el dato bruto y registran el origen de la curva. La igualdad de 402/402 retenciones y de su latencia carece de sensibilidad a esta intervención: **0/6** anclas modificadas abre una oportunidad de salida según el criterio del estudio.

### Texto candidato para decisión del propietario, pendiente de jornadas 2 y 3

Esta propuesta afecta al paso **R7→R8 de §4.2**. R4 conserva su lugar y la nueva regla tiene prioridad posterior a la comprobación de versiones y a R-CANCEL. Texto para insertar en el caso **INCOHERENTE**, antes de aplicar R8.

> Si la observación efectiva declara `STOPPED_AT`, el ancla está fuera de τ de la parada declarada, `stop_id` identifica una única ocurrencia del itinerario y R8 autorizaría una velocidad positiva, se consultará la muestra previa de zona de §4.6. Si esa muestra es proyectable con el criterio vigente, pertenece al mismo viaje, su edad respecto del ancla es estrictamente positiva y no supera el horizonte vigente, y queda dentro de τ de la ocurrencia declarada, se retendrá el progreso del GPS efectivo hasta reemplazo o caducidad. La causa será `incoherent_stop_prior_gps`, con `stop_state.coherent=false`. En los demás casos se aplicará R8. La parada declarada seguirá disponible para explicar la discrepancia. La coordenada derivada conservará el ancla efectiva.

- **§4.3–§4.5.** Registrar la causa y la muestra previa que condiciona la envolvente conforme a la identidad inmutable por ancla/run. Conservar el GPS bruto, `map_matched`, la parada declarada y el progreso confirmado. La degradación conserva la procedencia que declara `stop_state`; el consumidor expone la contradicción y la causa de la retención. Al caducar, F1 congela la curva autorizada en su extremo.
- **Contrato y consumidores.** Ampliar el `Literal` cerrado de `hold_reason` en [`apps/api/schemas.py:296`](../../../apps/api/schemas.py#L296), regenerar el enum en [`apps/api/openapi.json:2080`](../../../apps/api/openapi.json#L2080) y documentarlo en [`docs/DATA_CONTRACTS.md:258`](../../DATA_CONTRACTS.md#L258). Hoy el valor se rechazaría al validar el modelo API y queda fuera del contrato de los clientes generados. El tipo TS de `hold_reason` admite cadenas, y AC-T7 debe verificar en las fixtures la misma evaluación de progreso y fase `hold:incoherent_stop_prior_gps` en Python y TypeScript. También debe verificarse cómo se presenta ese motivo en los consumidores. [Contrato TS](../../../apps/web/src/domain/contract.ts#L146) y [fase TS](../../../apps/web/src/domain/movement.ts#L25).
- **§4.6 y §8.** Fijar que se usa la muestra previa admitida por el replay, incluida la validación del mismo viaje, la geometría y la edad. Incorporar pruebas de ocurrencias múltiples, identificadores ausentes, desconocidos o que cambian, zona en el límite, muestra caducada o rechazada, cancelación, cambio de perfil y nuevo anclaje tras quedarse sin GPS. Mantener AC-M7 con el mismo predicado y añadir al informe su desglose por estado, aceptación del destino y efecto de presentación.
- **Riesgos.** Una muestra anterior dentro de la zona puede coexistir con una salida real. Una parada repetida necesita otra señal de ocurrencia y sigue la degradación existente. El GPS cuantizado puede retener un punto erróneo. La evidencia de esta jornada no estima la frecuencia de esos riesgos fuera de su población.
- **Validación antes de decidir.** Aplicar este mismo diseño con P-024 en las jornadas 2 y 3, con SHA-256, GTFS y catálogo por sesión. Revisar para cada política y jornada los pares con GPS aceptado y rechazado, los cambios de parada con GPS idéntico, las salidas retenidas, la latencia y las colas de discontinuidad. Comparar los saltos de llegada y salida en `parada_previa` y `gps_previo` e inspeccionar todos los casos que cambian. Buscar evidencia operativa independiente para corroborar esas salidas cuando esté disponible. Verificar F1, R-CANCEL y la procedencia en el cliente con casos dirigidos antes de promover una propuesta. Presentar los deltas por jornada y los casos adversos al propietario para su decisión. Los resultados históricos de MP-025b conservan el criterio original.

### Límites

**UNVERIFIED:** momento físico de detención o salida, posición física exacta de un tren, semántica general de `current_stop_id`, si la cuantización proviene del dispositivo o de otro paso del feed, visibilidad histórica por hora civil, salto percibido en navegador, efecto de una implementación de producción de las variantes y extrapolación a otras jornadas, líneas, horas o cobertura de corredor. Las anclas y pares del mismo vehículo no son observaciones independientes. El estudio cubre una jornada, dos ventanas y la fracción con corredor y GPS evaluables. La ausencia de retroceso al caducar para las variantes es una propiedad del cálculo acotado del arnés en estas métricas. Queda pendiente la validación completa del contrato F1 de una implementación futura.

## Reproducción y custodia

Los archivos privados se leen en su ubicación original. Solo se restaura una copia en el contenedor `mp037-study` con volumen anónimo. Destino `postgresql://mp_test:mp_local@127.0.0.1:5468/mp037`, esquema `public`, rol local propietario `mp_test`, marca `madrid-pulse:disposable`. Desde el repositorio, con Python 3.12 y las dependencias ya disponibles, Docker con la imagen local y las rutas privadas de la jornada.

El puerto y el nombre de la base se leen del DSN explícito. El arnés exige loopback, entorno y modo `replay`, núcleo completo y la marca desechable antes de cualquier escritura temporal. Rechaza los destinos reservados y las opciones de conexión en la URL.

| Entrada | SHA-256 o identificador |
|---|---|
| Dump `analysis/session-1-20261126T090138Z.dump` | `95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1` |
| `session-1/manifest.json` | `5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e` |
| GTFS `fomento_transit.zip` | `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e` |
| Catálogo compuesto verificado por el arnés | `sha256:f071ad8d6e217331bc3cdcc2304b7a300ee8306f346acc52b9276e3e6aa4702d` |
| Fixture sintética incluida en `test_contradictions.py` | `993f0146f7c53369bbeea9a0b7b7fafd5ed6be318e0fd79e7fe4705f62be917f` |
| Base de producción `origin/main` | `d0dd0bca62b18200b082a30504dca4d75f73171d` |
| HEAD del arnés durante las dos ejecuciones del delta | `2b5fe89e6a1561fb34db8c334f247fc4ac233e67` |
| Evidencia de primera pasada `analysis/mp037-r1-{1,2}.json` | `9a489bee276d9a6f1b76a35d1d1c73f71f84fb32def015e6de00ad8a0cc9a502` en cada archivo |
| Evidencia de este delta `analysis/mp037-r2-{1,2}.json` | `286ed314108b69b48e40bdad9cdac4b3f43c50c1bffbf6fceca1af22c42ab660` en cada archivo |

```bash
set -eu
umask 077
data=/Users/matu/Documents/DATA/madrid-pulse/data
capture="$data/capture/2026-11-26"
dump="$capture/analysis/session-1-20261126T090138Z.dump"
manifest="$capture/session-1/manifest.json"
export MADRID_PULSE_GTFS_SOURCE="$data/gtfs_static/fomento_transit.zip"
shasum -a 256 -c "$dump.sha256"
shasum -a 256 "$manifest" "$MADRID_PULSE_GTFS_SOURCE"
docker run --pull=never --name mp037-study --label madrid-pulse.disposable=mp037 \
  -d -p 127.0.0.1:5468:5432 -e POSTGRES_DB=mp037 -e POSTGRES_USER=mp_test \
  -e POSTGRES_PASSWORD=mp_local postgis/postgis:17-3.5
trap 'docker rm -fv mp037-study' EXIT
until docker exec mp037-study pg_isready -h 127.0.0.1 -U mp_test -d mp037; do sleep 1; done
for migration in infra/migrations/*.up.sql; do
  docker exec -i mp037-study psql -X -v ON_ERROR_STOP=1 -U mp_test -d mp037 < "$migration"
done
export MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME=''
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5468/mp037
python -m infra.operate.mark_disposable_db
docker cp "$dump" mp037-study:/tmp/copy.dump
docker exec mp037-study sh -ec 'pg_restore -l /tmp/copy.dump | awk "/TABLE DATA public/ && !/spatial_ref_sys/" > /tmp/data.toc
pg_restore -L /tmp/data.toc --single-transaction --disable-triggers -U mp_test -d mp037 /tmp/copy.dump'
results=$(mktemp -d)
for n in 1 2; do
  python -m infra.operate.validation.contradictions "$manifest" "$dump" > "$results/run-$n.json"
done
cmp "$results/run-1.json" "$results/run-2.json"
shasum -a 256 "$results"/run-*.json
```

Los resultados y sus ficheros `.sha256` están en el directorio privado `data/capture/2026-11-26/analysis/` de la captura original, excluido de Git. El JSON conserva las filas de los casos, los estratos de M7, la cuantización, la estación GTFS más cercana y las transiciones alrededor de las seis anclas que cambian. El hash incorpora el HEAD. Con otro HEAD se comparan los datos tras omitir `inputs.head`.

La prueba del GPS anterior excluido para `20741` se hizo sobre el volcado completo restaurado. Este comando reproduce el punto bruto previo en contexto, por fuera del replay segmentado.

```sql
SELECT observed_at, source_trip_id, latitude, longitude, ingestion_run_id
FROM public.vehicle_position_observation
WHERE source_vehicle_id = '20741'
  AND observed_at < '2026-11-26 07:34:52+00'
  AND ingestion_run_id <= (
    SELECT max(ingestion_run_id)
    FROM public.vehicle_position_observation
    WHERE source_vehicle_id = '20741'
      AND observed_at = '2026-11-26 07:34:52+00'
  )
ORDER BY observed_at DESC, id DESC
LIMIT 1;
```

## Comprobaciones ejecutadas

| Comando o comprobación | Resultado observado |
|---|---|
| `shasum -a 256 -c "$dump.sha256"`, cuatro migraciones, `mark_disposable_db` y `pg_restore --single-transaction` | **PASS**. El volcado dio `OK`. Puerto publicado `127.0.0.1:5468`. La comprobación SQL devolvió `mp037\|public\|mp_test\|madrid-pulse:disposable`. |
| Dos procesos independientes de `python -m infra.operate.validation.contradictions "$manifest" "$dump"`, `cmp` y `shasum -a 256 -c` sobre ambos resultados | **PASS**. `cmp` con salida cero y ambos `.sha256` devolvieron `OK`. |
| `python -m unittest -v infra.operate.validation.test_contradictions` | **RED esperado**, 10 tests, 1 fallo y 13 errores al aplicar las pruebas al arnés de primera pasada. **GREEN**, `Ran 10 tests`, `OK` con el delta. Cubre el puerto y base explícitos, rachas, borde del tope de velocidad, `gps_previo` y el borde positivo de `parada_previa` a τ. |
| Todos los módulos Python enumerados en `.github/workflows/ci.yml`, más `infra.operate.validation.test_metrics`, `infra.operate.validation.test_contradictions` y `tests.governance.test_governance` | **PASS**, `Ran 379 tests`, `OK (skipped=5)`. Se usó la base limpia y marcada `mp037_ci` del mismo contenedor con `MADRID_PULSE_ENV=test` y `MADRID_PULSE_REQUIRE_DB=1`. Los 13 casos GTFS se ejecutaron usando un enlace temporal al ZIP local validado. Soak MP-007 **NO EJECUTADO**, por ausencia de esa población en la base limpia. |
| `npm ci --offline --no-audit --no-fund`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` en `apps/web`, Node 22.13.1 | **PASS**. 11 archivos y 110 tests en Vitest. Build con aviso de tamaño y validación del worker MapLibre de 550 754 bytes. |
| `ruff check infra/operate/validation`, `python -m compileall -q infra/operate/validation`, `python scripts/governance/check_docs.py`, `git diff --check` | **PASS**. `All checks passed!`, compilación sin errores, `Documentación de gobernanza correcta.` y salida cero de Git. |
| `infra.operate.validation.test_segments` en el puerto histórico que exige esa prueba | **NO EJECUTADO**. La prueba valida el endpoint específico de MP-025b. El propio replay de MP-037 llama a `check_segment` contra las tablas restauradas y exige coincidencia de exclusiones y población. |
| `docker rm -fv mp037-study`, consulta de nombre exacto, `docker volume inspect` sobre el volumen registrado y `lsof -nP -iTCP:5468 -sTCP:LISTEN` | **PASS**. Contenedor, volumen y escucha ausentes tras la retirada. |

Para repetir la suite Python de CI en una base limpia del mismo contenedor, crear `mp037_ci`, aplicar las cuatro migraciones y marcarla como desechable con el DSN de esa base. El comando se ejecutó con ese DSN, `MADRID_PULSE_ENV=test` y `MADRID_PULSE_REQUIRE_DB=1`.

```bash
python -m unittest -v $(awk '/^            (apps|packages|services|tests)\./ {print $1}' .github/workflows/ci.yml) \
  infra.operate.validation.test_metrics infra.operate.validation.test_contradictions \
  tests.governance.test_governance
```

Ejecutor según despacho inicial: Codex `gpt-6.2-sol` · medium, sesión reutilizada para el delta. Identidad efectiva del backend UNVERIFIED. Queda pendiente la única reverificación del delta por Claude `claude-opus-5-5` · high.
