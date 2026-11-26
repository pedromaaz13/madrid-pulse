# MP-025b · Validación provisional del motor sobre captura MP-028

**PROVISIONAL · 1 de 3 jornadas. FR-01 sigue abierto.** La mediana del salto cumple el criterio de MP-025b, pero en 19 anclas el motor autorizó velocidad positiva mientras Renfe declaraba STOPPED_AT. También retuvo 135 de 1441 avances de al menos 100 m iniciados en tránsito o aproximación. En dos secuencias el snapshot recuperó un ancla antes descartada cuando el GPS bruto ya había vuelto al punto inicial. Los casos proceden de dos segmentos de una sola mañana. El propietario conserva la decisión sobre FR-01.

| Criterio del plan | Veredicto de la jornada | Evidencia |
|---|---|---|
| H1 · N ≥ 500 y p50 ≤ 200 m | **Cumple** | 11425 pares medidos, p50 0 m. En 2298/11425 el salto supera 200 m; p95 1916,041857 m y máximo 23633,987753 m |
| STOPPED_AT · cero planes con velocidad positiva | **No cumple** sobre todas las declaraciones; cumple en las coherentes con zona | 19/18242 anclas STOPPED_AT, 19/7001 con plan, 0/6981 con parada declarada coherente. En 11241 anclas falta un plan evaluable |
| M7 · conservar avance cuando IN_TRANSIT_TO o INCOMING_AT se desplazó ≥ 100 m | **No cumple** la guarda de cero retenciones | 135/1441 pares retenidos. Los 135 empezaron en INCOMING_AT dentro de la zona de la parada declarada |
| F1 · retroceso al caducar = 0 | **Cumple** en los cruces medibles | 0/65 retrocesos, máximo 0 m. Hubo 8 recuperaciones ordinarias, 5 con salto > 200 m |
| Cancelación conocida señalizada | **Cumple en las entradas observables** | 12/12 filas con vehículo visible señalizadas; 171/171 llamadas visibles señalizadas. Hubo 7 filas sin vehículo y 1 sin llamada visible en los tableros consultados |
| Salidas retenidas y latencia | **Coste observado**; sin umbral de aceptación aprobado | 402/6918 pares iniciados en STOPPED_AT tuvieron avance observado y predicción de avance cero. Detalle de latencia y casos rechazados más abajo |
| Procedencia | **Observable** en este replay | 51 entradas unlocated, 38 schedule_only y 24299 stale_frozen. La base declarada al congelar GPS bruto tiene la limitación descrita más abajo |
| Representatividad · tres jornadas | **Insuficiente** | Solo jornada 1. El smoke fue una prueba de cinco minutos del arnés y se conserva por separado |


## Jornada 1 de 3 · 26 de noviembre de 2026

La ventana civil abarca **3 h 00 min 01,583943 s** (07:00:23–10:00:24 de Madrid). La cobertura temporal efectiva es **2 h 00 min 29,082465 s** tras descontar **59 min 32,501478 s** entre dos ciclos GPS correctos. Los tres feeds devolvieron 235/235 respuestas correctas durante las rondas que llegaron a ejecutarse. Durante la suspensión faltaron rondas completas. La sesión terminó por duración, con código 0 y el bloqueo del colector liberado. Las jornadas 2 y 3 siguen pendientes.

| Segmento independiente (UTC) | Rondas GPS con datos en captura | Filas de posición para análisis | Cobertura de identidad |
|---|---:|---:|---|
| Inicio 06:00:23.004291 hasta el último run a las 06:35:00.841790 | 68/68 | 9340 | 188 vehículos y 188 viajes |
| Reinicio 07:34:33.343268 hasta fin 09:00:24.588234 | 167/167 | 20167 de 20302 | 224 vehículos y 225 viajes |
| Total | 235/235 | 29507 de 29642 | Los vehículos y viajes que reaparecen solo cuentan una vez en la cobertura conjunta |

Tras aplicar el corte, quedaron posiciones analizables en 234/235 rondas: 68/68 antes y 166/167 después. Hubo datos de captura en las 235. El fin del hueco se fijó en el reloj de ingesta del primer run GPS tras la suspensión. Sus **135** observaciones llevaban la hora GPS **07:34:30**, dentro del intervalo excluido. La segunda serie empieza con el siguiente GPS, a las **07:34:52**. En la primera serie se admiten los GPS de 06:00:10 del primer run porque preceden al arranque de la sesión y no atraviesan la suspensión. La segunda serie también excluye actualizaciones de viaje con reloj de origen dentro del hueco.

**Reanudación tras suspensión.** 65 vehículos reaparecieron en el segundo segmento con el mismo viaje que en su última muestra del primero. Esos 65 enlaces se descartaron antes de calcular distribuciones. Las vistas temporales de PostgreSQL limitan tanto los runs como las observaciones y actualizaciones visibles a producción. Al reanudar no se arrastran ancla, estado del operador, envolvente, progreso congelado ni reloj de latencia del segmento anterior. No se midió un salto a través de la suspensión. Las recuperaciones ordinarias que se indican abajo empiezan y terminan dentro de un solo segmento.

### Pares y cobertura del corredor

De 347 vehículos únicos, 135 tuvieron al menos un ancla en corredor validado. Por viaje, la cobertura fue 135/348. La proyección de un GPS se evalúa sobre su propia geometría y el cálculo usa el progreso dirigido del viaje.

| Tramo | Pares consecutivos | Salto medible | Sin corredor | Sin proyección | Sin plan inicial | Otras exclusiones | p50 / p90 / p95 / máximo (m) |
|---|---:|---:|---:|---:|---:|---|---|
| Antes | 9152 | 3444 | 5555 | 26 | 111 | intervalo_largo 16 | 0.000000 / 1077.736586 / 1916.023158 / 23633.987753 |
| Después | 19943 | 7981 | 11644 | 66 | 223 | intervalo_largo 28, otra_circulacion 1 | 0.000000 / 1156.298485 / 1919.390287 / 23539.789354 |
| Jornada | 29095 | 11425 | 17199 | 92 | 334 | intervalo_largo 44, otra_circulacion 1 | 0.000000 / 1142.973740 / 1916.041857 / 23633.987753 |

De los 11759 pares con dos proyecciones admisibles, 334 no tenían envolvente propia de la primera ancla. Se midieron 11425/11759. El JSON privado identifica cada primera ancla excluida por esta causa. Las exclusiones son disjuntas. Los motivos ausentes de la tabla tienen recuento cero. Los cuantiles conjuntos se calcularon con todos los pares individuales. No se promediaron medianas de los segmentos. Intervalos observados por vehículo dentro de los segmentos (p50 / p90 / p95 / máximo en segundos): 38.000000 / 42.000000 / 42.000000 / 4320.000000.

### Estado de parada y coherencia

| Estado | Posición de la parada declarada | Coherencia | Anclas | Sin plan | Planes a 0 m/s | Planes a > 0 m/s | Pares con salto | p50 / p90 / p95 / máximo (m) |
|---|---|---|---:|---:|---:|---:|---:|---|
| INCOMING_AT | en_zona | True | 2317 | 0 | 2317 | 0 | 2249 | 0.000000 / 0.000000 / 1570.681207 / 23633.987753 |
| INCOMING_AT | pasada_mas_1km | False | 17 | 0 | 0 | 17 | 17 | 0.000000 / 1565.919635 / 3177.560127 / 3702.431034 |
| INCOMING_AT | siguiente | True | 1 | 0 | 0 | 1 | 1 | 7448.074725 / 7448.074725 / 7448.074725 / 7448.074725 |
| INCOMING_AT | sin_clasificar | None | 2969 | 2969 | 0 | 0 | 0 | — |
| IN_TRANSIT_TO | en_zona | True | 720 | 0 | 0 | 720 | 703 | 798.163177 / 2420.558655 / 3145.451251 / 18620.717658 |
| IN_TRANSIT_TO | pasada | True | 183 | 0 | 0 | 183 | 176 | 470.924342 / 1411.114944 / 1874.249249 / 10587.242544 |
| IN_TRANSIT_TO | pasada_mas_1km | True | 1388 | 0 | 2 | 1386 | 1361 | 362.096691 / 2170.451250 / 2960.999599 / 16174.766569 |
| IN_TRANSIT_TO | sin_clasificar | None | 3670 | 3670 | 0 | 0 | 0 | — |
| STOPPED_AT | fuera_zona_declarada | False | 20 | 0 | 1 | 19 | 18 | 1461.041919 / 2758.523809 / 2758.523809 / 2758.523809 |
| STOPPED_AT | intermedia | True | 2129 | 0 | 2129 | 0 | 2100 | 0.000000 / 1703.059965 / 2505.020943 / 21511.828502 |
| STOPPED_AT | origen_tras_salida_programada | True | 696 | 0 | 696 | 0 | 687 | 0.000000 / 0.000000 / 0.000000 / 12692.804927 |
| STOPPED_AT | pre_salida | True | 4124 | 0 | 4124 | 0 | 4082 | 0.000000 / 0.000000 / 0.000000 / 10259.281272 |
| STOPPED_AT | sin_clasificar | None | 11241 | 11241 | 0 | 0 | 0 | — |
| STOPPED_AT | terminal | True | 32 | 0 | 32 | 0 | 31 | 0.000000 / 0.000000 / 0.000000 / 0.000000 |

### Correcciones mayores de 200 m

Esta tabla incluye cada par adverso una vez. El desglose separa avance y retroceso del segundo GPS proyectado. Las causas nombran la decisión del motor en el primer fotograma. El JSON privado conserva el vehículo, la hora, el desplazamiento firmado, el avance previsto, el salto exacto y la aceptación del segundo GPS para cada caso.

| Estado inicial | Causa del plan inicial | Casos | Proyección posterior / igual / anterior | Sin plan propio en el segundo GPS | Máximo (m) | Vehículo y hora UTC de ese máximo |
|---|---|---:|---:|---:|---:|---|
| INCOMING_AT | avance por horario | 1 | 1 / 0 / 0 | 1 | 7448.074725 | 20235, 08:23:10 |
| INCOMING_AT | operator_incoming_at | 197 | 135 / 0 / 62 | 48 | 23633.987753 | 20213, 06:11:10 |
| INCOMING_AT | schedule_stop_zone | 6 | 0 / 4 / 2 | 2 | 3702.431034 | 19608, 08:41:10 |
| IN_TRANSIT_TO | avance por horario | 1680 | 882 / 364 / 434 | 243 | 18620.717658 | 19596, 08:25:51 |
| IN_TRANSIT_TO | terminal | 1 | 0 / 0 / 1 | 1 | 1556.038188 | 20710, 06:19:10 |
| STOPPED_AT | avance por horario | 2 | 0 / 0 / 2 | 2 | 1526.696988 | 19535, 06:18:10 |
| STOPPED_AT | operator_stopped_at | 398 | 396 / 0 / 2 | 5 | 21511.828502 | 20793, 08:46:51 |
| STOPPED_AT | schedule_stop_zone | 13 | 0 / 0 / 13 | 8 | 2758.523809 | 20414, 06:06:30 |

### Caducidad y procedencia de los fotogramas

| Método | Espacio | Base de congelación | Fotogramas de vehículo |
|---|---|---|---:|
| anchor | map_matched | None | 21285 |
| anchor | raw | None | 40211 |
| extrapolated_from_last_anchor | map_matched | None | 6006 |
| schedule_only | schedule | None | 38 |
| stale_frozen | map_matched | authorized_envelope_end | 8265 |
| stale_frozen | raw | anchor_version_changed | 16034 |
| unlocated | None | None | 51 |

Total de 91890 entradas de vehículo en 516 instantes de replay. Una ancla puede aparecer en muchos fotogramas.


### Lectura de los casos adversos

**Correcciones.** En el smoke hubo 19/80 saltos > 200 m (23,75 %); en la jornada, 2298/11425 (20,11 %), repartidos entre 114 vehículos. El patrón persiste con una muestra mayor. En 1680 casos el primer estado era IN_TRANSIT_TO y el motor avanzó por horario; en 364 de ellos la segunda proyección quedó en el mismo punto y en 434 quedó por detrás. También hubo grandes avances de GPS tras retenciones por estado del operador. En 310/2298 casos el segundo GPS careció de plan propio. El máximo, vehículo 20213 a las 06:11:10 UTC, fue un retroceso proyectado de 23633,987753 m tras INCOMING_AT retenido en zona. La nueva fila llevaba implausible_speed y el motor descartó ese GPS como ancla de movimiento. El error GPS–predicción se conserva en el resultado; la fuente no permite afirmar que el tren recorriera esa distancia ni que el usuario viera tal salto.

**STOPPED_AT.** El smoke no reveló planes positivos. En la jornada aparecieron 19, en 17 vehículos. En los 19 la proyección estaba fuera de los 50 m de la parada declarada, R7 marcó incoherencia y R8 recurrió al horario. En 16 se publicó schedule_stop_zone con velocidad positiva disponible después de la espera y en tres se permitió avance por horario sin espera. El rango fue de 8,440056 a 14,353688 m/s. El resultado adverso también llegó a la presentación: 46 entradas extrapolated_from_last_anchor con estado efectivo STOPPED_AT, 32 con schedule_stop_zone y 14 sin causa de retención. Son fotogramas repetibles de anclas, no 46 trenes. Las 4124 pre-salidas, 696 paradas en origen pasada la hora programada, 2129 paradas intermedias y 32 terminales coherentes sí quedaron a 0 m/s.

| Parada declarada | Decisión de R8 | Vehículo y hora GPS UTC de cada excepción |
|---|---|---|
| 17001 | schedule_stop_zone | 20428 08:47:52 |
| 17003 | schedule_stop_zone | 20414 06:05:52, 20428 08:27:51, 20434 08:33:30 |
| 18003 | schedule_stop_zone | 20721 06:34:52 |
| 35600 | schedule_stop_zone | 19595 08:20:52, 19601 08:34:10, 19607 08:48:30, 20767 08:11:30, 20789 08:58:50 |
| 35605 | avance por horario | 19535 06:17:52, 20717 06:32:52, 19607 08:59:51 |
| 35605 | schedule_stop_zone | 20709 06:03:52, 20741 07:34:52, 20749 08:00:30, 20755 08:09:50, 20775 08:42:52 |
| 60100 | schedule_stop_zone | 20437 08:03:52 |

**Aproximación y tránsito.** En IN_TRANSIT_TO, 1571/2291 anclas interpretables apuntaban a una parada pasada, 1388 de ellas a más de 1 km, frente a 4/8 en el corte 1533. Otras 720 estaban en zona y ninguna apuntaba a la siguiente. La política admite como coherente IN_TRANSIT_TO con parada pasada. En INCOMING_AT, 2317/2335 estaban en zona, una apuntaba a la siguiente y 17 estaban a más de 1 km por detrás. En esas 17, R7→R8 permitió el plan de horario; la mediana del salto fue 0 m y el máximo 3702,431034 m. La frecuencia observada depende del corredor, los vehículos y la franja disponibles. La interpretación general del campo del operador permanece UNVERIFIED.

**Salidas retenidas.** En 402/6918 pares iniciados en STOPPED_AT (107 vehículos) el siguiente GPS avanzó en el sentido del viaje y la predicción fue exactamente cero. Los 402 desplazamientos alcanzaron también los 100 m de la definición histórica, frente a 3/27 en 1532 y 3/43 en el smoke. Esta clasificación observa la primera proyección desplazada. Un desplazamiento aislado puede ser ruido del feed.

Desde el instante GPS de esa primera proyección, el primer fotograma de replay con un ancla efectiva desplazada tardó **p50 8,323758 s, p90 17,266597 s, p95 19,986589 s y máximo 49,042598 s** (402/402). En 399 casos ya pudo mostrar el desplazamiento el primer run elegible. En tres el motor descartó inicialmente ese GPS; asignarles su retardo de ingesta habría subestimado el máximo. Se siguió la presentación hasta la siguiente ancla efectiva dentro del mismo segmento. Estos tiempos miden disponibilidad por replay, no el momento de salida del tren, el commit real ni el repintado del navegador.

| Vehículo | GPS desplazado UTC | Primer fotograma que mostró avance UTC | Latencia (s) |
|---|---|---|---:|
| 20231 | 06:21:52 | 06:22:35.444589 | 43,444589 |
| 20721 | 06:11:30 | 06:12:18.591167 | 48,591167 |
| 20793 | 08:46:51 | 08:47:40.042598 | 49,042598 |

**Hallazgo de presentación en dos de esos tres casos.** A las 06:22:35.444589, el GPS de 20231 había vuelto exactamente a su coordenada de las 06:21:30 y seguía declarando STOPPED_AT. Sin embargo, el snapshot eligió como ancla efectiva el GPS de las 06:21:52, que había descartado en el fotograma anterior. El progreso mostrado pasó de 68,387400 a 10327,668672 m. A las 08:47:40.042598, 20793 también volvió a la coordenada previa, pero el snapshot eligió el GPS de las 08:46:51 y extrapoló: progreso confirmado 33687,171049 m y mostrado 34547,078447 m, frente a 12175,342547 m antes. Se reprodujeron ambos casos con build_snapshot sobre las vistas del segmento. La selección latest/previous usa las dos últimas muestras (packages/movement/engine.py:106–125); en estas secuencias reaparece una muestra que la respuesta anterior había rechazado. Se reporta al revisor sin modificar el motor. En cambio, para 20721 sí fue el GPS nuevo de las 06:12:10 el que finalmente se presentó. Esta distinción impide interpretar las 402 latencias como confirmaciones de salidas físicas.

**Guarda M7.** La fracción adversa bajó de 9/10 del smoke al 9,37 % (135/1441) en jornada 1. Los 135 casos diurnos proceden de una sola regla: operator_incoming_at congela el avance dentro de la zona de parada y el siguiente GPS ya estaba al menos 100 m más adelante. Ninguno se debió a before_first_departure, que sí explicó cuatro de los nueve del smoke. El corte histórico 1532→1533 daba 0/9. Los tres resultados tienen poblaciones y cadencias distintas.

**F1 y reaparición ordinaria.** Al pasar de valid_until a +1 ms sobre la misma ancla y geometría, el retroceso máximo fue 0 m en 65 comparaciones. Los 8 saltos al recuperar tras caducidad tuvieron p50/p90/p95/máximo de **2571,203214 / 5478,116637 / 6660,286683 / 7842,456728 m**. En los ocho casos se pasó del final congelado autorizado a una nueva ancla sobre corredor. La tabla recoge los ocho, independientemente de su magnitud. Los 65 enlaces de reanudación tras suspensión están fuera de esta población. El salto de **311,371489 m** se reprodujo en el test sintético de recuperación a +95 s, antes de caducar. Su referencia es otra y no entra en estos cuantiles.

| Vehículo | Primer fotograma recuperado UTC | Salto (m) |
|---|---|---:|
| 20410 | 2026-11-26T06:14:21.798549+00:00 | 0.0 |
| 20232 | 2026-11-26T07:53:10.670496+00:00 | 37.983479201859154 |
| 20422 | 2026-11-26T07:59:21.008772+00:00 | 677.5784008517803 |
| 20234 | 2026-11-26T08:05:00.091786+00:00 | 4464.828027064388 |
| 20236 | 2026-11-26T08:10:39.173680+00:00 | 4464.828027064388 |
| 20424 | 2026-11-26T08:14:45.447155+00:00 | 4464.828027064388 |
| 20243 | 2026-11-26T08:19:53.407324+00:00 | 0.8743919868902594 |
| 20238 | 2026-11-26T08:26:33.576234+00:00 | 7842.456728365687 |

**Cancelaciones y procedencia.** De 23 trip_updates CANCELED capturados, cuatro llegaron en el primer ciclo reanudado con hora de observación dentro del hueco. Se examinaron los 19 restantes al primer instante elegible. De ellos, 12 tenían vehículo en snapshot y 12 mostraron la relación CANCELED. Los demás siete carecían de vehículo. En los tableros por defecto de sus paradas, 18 de las 19 filas tenían al menos una llamada visible y todas las 171 entradas correspondientes llevaban la relación. La señal de la relación se examina por separado de la autorización de movimiento de la envolvente. Las 8265 congelaciones sobre corredor declaran authorized_envelope_end; las 16034 congelaciones de GPS bruto declaran anchor_version_changed según el fallback de producción. Esta última etiqueta también aparece sin corredor, de modo que por sí sola no demuestra un cambio real de versión. Ningún unlocated publicó espacio de coordenadas y cada schedule_only declaró schedule. Se verificó el contrato en el replay; la visibilidad histórica, la percepción en el navegador, las salidas físicas, el significado universal de current_stop_id y la existencia de una parada omitida siguen UNVERIFIED.

### Reproducción de la jornada

Se ejecutaron las cuatro migraciones desde cero sobre la imagen local postgis/postgis:17-3.5 en mp025b-j1. Se verificaron el puerto publicado 127.0.0.1:5456, la base mp025b, el esquema public, el propietario mp_test y la marca madrid-pulse:disposable. La única operación en mp028-capture (base mp028_capture, puerto publicado 5466) fue un pg_dump consistente de solo lectura:

```bash
docker exec -e PGOPTIONS='-c default_transaction_read_only=on' mp028-capture \
  pg_dump -U mp028_capture -d mp028_capture -Fc > "$dump"
shasum -a 256 "$dump"
```

En el bloque de reproducción del smoke se sustituyen el nombre del contenedor por mp025b-j1 y las entradas por estas rutas relativas al directorio privado de captura 2026-11-26. La comparación de cada ejecución registra también el HEAD, por lo que debe usarse el indicado para reproducir el hash exacto.

| Entrada | SHA-256 |
|---|---|
| analysis/session-1-20261126T090138Z.dump | 95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1 |
| session-1/manifest.json | 5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e |
| session-1/metadata.json | df116024ee1041f5743998826974c65920426a033a2b2b3e8448a01ff98dfc38 |
| session-1/session.json | aa3bc3a5798c5d8c915b51942bf7b7192a2f1d71e01df617f514dae446857e63 |

El manifiesto identifica el HEAD de captura 1e60839d408e6668da8e1711937ed21b31c09615. Los 705 runs llevaban la huella esperada de P-024 y ninguno se clasificó retroactivo. Se contrastaron GTFS y catálogo completos. El manifiesto registra 1970 incidencias implausible_speed para la jornada completa. La medida de salto compara la predicción con la segunda proyección del GPS, incluso si el motor descarta ese segundo GPS al dibujar. El detalle por caso permite distinguir ambas situaciones.

**PASS.** Se ejecutaron ruff check infra/operate/validation, compileall y seis pruebas con unittest (cinco pruebas del arnés y la recuperación sintética de referencia). La prueba SQL adicional por segmento verificó que cada posición pertenecía a un run visible y que ningún GPS anterior al reinicio entraba en el segundo segmento. Se ejecutó el replay sin red dos veces:

```bash
export MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME=''
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5456/mp025b
export MADRID_PULSE_GTFS_SOURCE=/Users/matu/Documents/DATA/madrid-pulse/data/gtfs_static/fomento_transit.zip
d=/Users/matu/Documents/DATA/madrid-pulse/data/capture/2026-11-26
for n in 1 2; do
  python -m infra.operate.validation.replay "$d/session-1/manifest.json" \
    "$d/analysis/session-1-20261126T090138Z.dump" > "$d/analysis/jornada1-segmentos$n.json"
done
cmp "$d"/analysis/jornada1-segmentos{1,2}.json
```

**PASS.** Los dos procesos independientes sobre HEAD 39bab4f5413702d7f7186f63fc682d7f06a23290 produjeron JSON idéntico byte a byte (cmp con salida 0), SHA-256 **18e3eb9153e5bb42459fffa4ca740591ac1368c3f11d75f09ed8faa5beeb782c**. El JSON incluye adverse, stopped_adverse, recovery_cases y departure_events para auditar cada caso con el instante exacto sin publicar las capturas. El replay del smoke sobre esta restauración conservó todos los campos numéricos y resultados del informe histórico (se compararon todos sus campos salvo HEAD y SHA del dump). Se verificó la retirada del contenedor y volumen propios con docker rm -fv mp025b-j1 y consulta posterior por nombre exacto.

La jornada queda entregada para revisión cruzada de Claude Opus · high. Despacho ejecutor Codex gpt-6.2-astra · high; identidad efectiva del backend UNVERIFIED. Jornadas 2 y 3 y cierre por el propietario pendientes.

## Smoke previo · prueba de cinco minutos del arnés

**Smoke insuficiente. FR-01 sigue abierto.** El 26 de noviembre de 2026, entre las 00:11:13 y las 00:16:13 de Madrid, el colector obtuvo 212 posiciones de 24 vehículos. Solo 80 pares permiten contrastar una predicción con la siguiente observación. En 19 de esos 80 la corrección supera 200 m. El máximo supera 3 km. La guarda M7 también presenta un resultado adverso: en 9/10 pares iniciados en tránsito o aproximación con avance observado ≥ 100 m, la predicción fue de 0 m. La decisión sobre FR-01 corresponde al propietario tras las jornadas y los demás gates.

| Muestra | Duración | Vehículos / viajes con corredor | Pares medibles / candidatos | p50 / p90 / p95 / máximo descriptivos (m) | Criterio N ≥ 500 y mediana ≤ 200 m |
|---|---:|---:|---:|---|---|
| Smoke | 300,090699 s | 11/24 vehículos y 11/24 viajes | 80/188 | 0 / 1605,043752 / 2417,157027 / 3045,815884 | Insuficiente |

### Qué se midió y qué quedó fuera

Cada vehículo aporta sus filas consecutivas en el orden de observación (desempate por ID). Se conserva el vínculo a la fila seleccionada por el replay mediante el hash bruto y el reloj GPS. Para cada par se exige la misma circulación (vehículo, viaje y día de servicio), intervalo positivo ≤ 180 s, corredor validado, proyecciones a ≤ 200 m de la vía y envolvente atribuible a la primera ancla. Se calcula el valor absoluto de la diferencia entre el progreso dirigido de la segunda proyección y la envolvente de producción evaluada al **instante GPS de la segunda observación**. La proyección bruta de destino se incluye aunque el motor conserve un ancla anterior. Por eso esta medida de error de predicción puede diferir del movimiento mostrado al refrescar. Cuantiles con interpolación lineal, decisiones sobre valores sin redondear.

| Balance del smoke | Recuento |
|---|---:|
| Filas / primeras observaciones sin predecesor | 212 / 24 |
| Pares consecutivos | 188 |
| Cambio de circulación / empate / intervalo largo / fila no seleccionada | 0 / 0 / 0 / 0 |
| Sin corredor en algún extremo | 103 |
| Sin proyección admisible adicional | 0 |
| Ambos extremos proyectables | 85 |
| Proyección inicial sin envolvente propia | 5 |
| Pares con salto medido | 80 |

Las cinco exclusiones por falta de plan corresponden a las siguientes primeras anclas UTC del 25 de noviembre. Todas son IN_TRANSIT_TO tras retrocesos en el GPS proyectado. El motor puede usar la observación previa. Atribuir su envolvente al nuevo GPS falsearía el origen de la predicción.

| Vehículo | Horas UTC |
|---|---|
| 19788 | 23:11:50 |
| 19793 | 23:14:10 |
| 20533 | 23:12:10 y 23:15:10 |
| 20941 | 23:15:10 |

Los 10/10 ciclos de posiciones contenían filas. Posiciones, actualizaciones de viaje y alertas registraron 10/10 intentos correctos cada uno y cero huecos de más de 60 s entre ciclos correctos según el manifiesto. Los **188 intervalos por vehículo** tienen p50/p90/p95 de 40 s y máximo de 120 s. Que el feed responda en todos los ciclos no garantiza una actualización por tren. El manifiesto registra 27 incidencias de velocidad inverosímil. Los desplazamientos siguientes describen observaciones del feed, sin verificación independiente del movimiento físico.

### Retenciones y semántica del operador

| Anclas STOPPED_AT | Velocidad positiva / planes | Anclas |
|---|---:|---:|
| En origen, antes de la salida programada | 0/20 | 20 |
| En origen, después de la hora programada | 0/9 | 9 |
| Parada intermedia | 0/17 | 17 |
| Sin plan en corredor | — | 34 |
| Total | 0/46 | 80 |

Ninguna de las 80 produjo una predicción positiva. La comprobación numérica cubre 46/80, y las 34 restantes carecen de velocidad publicada. Las tres categorías con plan se basan en la parada declarada, la zona proyectada y el día de servicio que resuelve producción. «Tras la hora programada» describe un tren observado detenido en el origen, sin medir su retraso al partir.

**Salidas retenidas.** En 3/43 pares elegibles iniciados en STOPPED_AT aumentó el progreso observado. En los tres el plan autorizó exactamente 0 m y el incremento superó 100 m. Son tres vehículos. Con la definición del corte 1532, el coste es 3/43 frente a 3/27. La primera respuesta identificable con posición desplazada es la del instante de visibilidad del segundo GPS en replay. Desde el reloj GPS de ese ancla, las latencias fueron 1,296956 s (20941), 2,597174 s (20533) y 3,310967 s (20520). Distribución p50/p90/p95/máx de 2,597174 / 3,1682084 / 3,2395877 / 3,310967 s. El tren pudo partir en cualquier momento entre anclas. La disponibilidad para un cliente real y el instante de salida física siguen UNVERIFIED.

| Estado | Clasificación de la parada declarada entre anclas interpretables | Sin clasificación / total | Coherencia publicada |
|---|---|---:|---|
| IN_TRANSIT_TO | 10 en zona, 10 pasadas (7 a más de 1 km), 0 siguientes, 0 posteriores | 53/73 | 20/20 coherentes |
| INCOMING_AT | 24 en zona, 1 pasada a más de 1 km, 0 siguientes, 0 posteriores | 34/59 | 24/25 coherentes |

El corte 1533 tenía 4/8 IN_TRANSIT_TO con parada a más de 1 km por detrás. Aquí son 7/20 interpretables. El motor admite una parada pasada en IN_TRANSIT_TO. Entre los 5 pares medibles iniciados con esa distancia, el salto mediano fue 1444,804797 m y el máximo 2417,157027 m. En el único par INCOMING_AT incoherente, R7 descartó la declaración y R8 retuvo por horario (before_first_departure), con salto 0 m. Entre los otros 21 pares INCOMING_AT, la mediana también fue 0 m pero el máximo llegó a 3045,815884 m. Estas proporciones describen anclas repetidas de pocos viajes a medianoche. La semántica general de Renfe, la entrada real en zona y una parada efectivamente omitida siguen sin verificar.

**Guarda M7.** El corte 1532→1533 registró 0/9 retenciones ante avance ≥ 100 m en IN_TRANSIT_TO o INCOMING_AT. El smoke registra 9/10. Los nueve casos se individualizan en la tabla siguiente: cinco retenciones por operator_incoming_at en zona y cuatro por before_first_departure. El décimo (20941, 23:11:50) sí predijo avance, aunque quedó 1616,961 m por debajo del observado. Queda pendiente verificar la frecuencia en horario diurno.

### Casos adversos

Cada fila recoge la corrección > 200 m y su explicación inmediata. La hora es la del segundo GPS (UTC del 25 de noviembre). El avance observado lleva signo. «Plan nuevo» indica si el segundo GPS recibió envolvente propia. La medida utiliza la proyección aun cuando el motor rechace ese GPS para presentación.

| Vehículo | Hora UTC | Estado inicial | Causa del plan | Avance previsto (m) | Avance observado (m) | Salto (m) | Plan nuevo |
|---|---|---|---|---:|---:|---:|---|
| 19788 | 23:11:50 | IN_TRANSIT_TO | before_first_departure | 0.000 | -1206.897 | 1206.897 | no |
| 19788 | 23:12:50 | INCOMING_AT | operator_incoming_at | 0.000 | 1916.047 | 1916.047 | sí |
| 19788 | 23:15:10 | INCOMING_AT | operator_incoming_at | 0.000 | 1603.720 | 1603.720 | sí |
| 19791 | 23:13:50 | IN_TRANSIT_TO | before_first_departure | 0.000 | 1655.663 | 1655.663 | sí |
| 19791 | 23:14:10 | IN_TRANSIT_TO | before_first_departure | 0.000 | -929.249 | 929.249 | sí |
| 19791 | 23:14:50 | IN_TRANSIT_TO | before_first_departure | 0.000 | 929.249 | 929.249 | sí |
| 19791 | 23:15:50 | IN_TRANSIT_TO | before_first_departure | 0.000 | 891.486 | 891.486 | sí |
| 19793 | 23:13:10 | INCOMING_AT | operator_incoming_at | 0.000 | 1528.432 | 1528.432 | sí |
| 19793 | 23:14:10 | IN_TRANSIT_TO | before_first_departure | 0.000 | -1451.470 | 1451.470 | no |
| 20520 | 23:13:10 | INCOMING_AT | operator_incoming_at | 0.000 | 1570.681 | 1570.681 | sí |
| 20520 | 23:15:50 | STOPPED_AT | operator_stopped_at | 0.000 | 1469.492 | 1469.492 | sí |
| 20533 | 23:12:10 | IN_TRANSIT_TO | before_first_departure | 0.000 | -2417.157 | 2417.157 | no |
| 20533 | 23:13:10 | IN_TRANSIT_TO | before_first_departure | 0.000 | 2417.157 | 2417.157 | sí |
| 20533 | 23:14:50 | STOPPED_AT | operator_stopped_at | 0.000 | 1444.805 | 1444.805 | sí |
| 20533 | 23:15:10 | IN_TRANSIT_TO | before_first_departure | 0.000 | -1444.805 | 1444.805 | no |
| 20941 | 23:11:50 | IN_TRANSIT_TO | avance por horario | 459.656 | 2076.616 | 1616.961 | sí |
| 20941 | 23:12:50 | STOPPED_AT | operator_stopped_at | 0.000 | 2505.021 | 2505.021 | sí |
| 20941 | 23:13:50 | INCOMING_AT | operator_incoming_at | 0.000 | 3045.816 | 3045.816 | sí |
| 20941 | 23:15:10 | INCOMING_AT | operator_incoming_at | 0.000 | -3045.816 | 3045.816 | no |

Las inversiones de signo en 19791, 20533 y 20941 muestran por qué importa conservar el signo del desplazamiento y la identidad del ancla. Una diferencia de kilómetros entre GPS sucesivos no demuestra que un tren haya recorrido esa distancia en sentido contrario. Las retenciones por horario antes de la salida aparecen incluso en viajes con GPS desplazado durante este corte nocturno. La correspondencia entre ese GPS y la salida real del día de servicio queda UNVERIFIED.

### Caducidad, recuperación y procedencia

Se consultaron 18 instantes distintos, que dieron 432 entradas de vehículo. Se incluyeron la primera visibilidad por replay de las observaciones, la de la cancelación, el fin del periodo y dos lados del límite de vigencia (exactamente valid_until y +1 ms) cuando entre ellos no llegaba otra ancla. La huella y el GTFS son los de captura.

| Método y espacio | Fotogramas de vehículo | Señal y procedencia |
|---|---:|---|
| anchor / map_matched | 176 | 80 con operator_stopped_at, 56 con operator_incoming_at y 40 con before_first_departure (39 IN_TRANSIT_TO y 1 INCOMING_AT) |
| extrapolated_from_last_anchor / map_matched | 10 | IN_TRANSIT_TO, sin causa de retención |
| anchor / raw | 228 | Sin envolvente ni estado de parada derivado |
| stale_frozen / map_matched | 12 | INCOMING_AT, frozen_basis=authorized_envelope_end |
| stale_frozen / raw | 6 | Sin progreso métrico. Producción declara frozen_basis=anchor_version_changed en el fallback bruto (packages/movement/rendering.py:557), incluso cuando la causa original es ausencia de corredor |
| unlocated / schedule_only / interpolated_between_known_anchors | 0 / 0 / 0 | No observados en estos fotogramas con display_lag_s=0 |

**F1.** Dos cruces medibles sobre corredor. Retroceso 0/2, máximo 0 m. Los 12 fotogramas congelados sobre corredor incluyen repeticiones de ancla. No hubo recuperación medible con nueva ancla tras congelación en ese corredor durante el smoke. N=0, por tanto los cuantiles de recuperación están ausentes. El test de referencia MP-022 produjo **311,371489 m** al recuperar a +95 s respecto de una estimación anterior. Es sintético y ocurre antes del horizonte de 180 s. No se suma al denominador de recuperaciones tras caducidad.

**CANCELED.** Una fila de trip_update declaró cancelado el viaje 1029J19790C5. No hubo ninguna posición para ese viaje en la copia. Al consultar su primer instante elegible (23:11:20.341296 UTC), el snapshot carecía de ese vehículo y los tableros de sus paradas con los parámetros públicos por defecto devolvieron cero llamadas de ese viaje. Señalización observable 0/0 en las entradas aplicables. El dato de cancelación existe, pero esta captura no demuestra la señalización de un vehículo visible cancelado.

### Reproducción y custodia de las entradas

La API, las métricas y el reloj se ejecutan localmente. El modo replay selecciona filas por started_at del run y observed_at de la fuente. Cada entrada del arnés usa at = max(started_at, observed_at); la lectura SQL de producción acota además la secuencia de la respuesta. La confirmación de la transacción y la publicación histórica por hora civil permanecen UNVERIFIED. Los instantes de replay no son capturas de navegador.

| Entrada o constante | Evidencia |
|---|---|
| Motor | origin/main 4bc86128d44a9b83f8f9747df5cf83ce593f0194 |
| Captura | Smoke en la rama MP-028, HEAD de69a40e0d2ed20e92bd1f67026c99ca1a61f172 |
| Manifiesto SHA-256 | bee3ced933fbfe944842be6388b0e4f434b6325bbd52e7ebec9065b15342ed20 |
| Copia privada en analysis/smoke-20261125T231945Z.dump | d4c736f18422ef701acddd6f8efee56aa9d137e767fdba44b278cb97859020f5 |
| GTFS 2026-11-19..2026-12-18 | 58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e |
| Catálogo compuesto | f071ad8d6e217331bc3cdcc2304b7a300ee8306f346acc52b9276e3e6aa4702d |
| Fixture sintética MP-022, tests/fixtures/mp022_synthetic/sequence.json | ca949627348434118eb07beb5f2ad1dbb21ec758e6a8bdb9c5faf5f856e2deeb |
| P-024 | packages/movement/model.py:39–51. Edad observada 60 s, horizonte 180 s, distancia a vía 200 m, velocidad máxima estimada 160 km/h, zona 50 m, espera 30 s, cancelación 600 s. Perfil completo contrastado con el manifiesto mediante packages/movement/profile.py:49 |
| Producción | apps/api/snapshot.py:765 (snapshot consistente), :349 (render), :1044 (tablero), packages/movement/rendering.py:121 (avance) y :215–227 (coherencia) |
| Umbrales de auditoría | docs/adr/0014-amendment-stop-state.md:391 (500 pares, mediana ≤ 200 m), :42 (parada pasada por > 1 km), :75–79 y docs/evidence/mp-024/stop_state_comparison.py:91 (guarda de avance ≥ 100 m). El +1 ms es una sonda de la primera unidad posterior al límite serializado |

La copia se obtuvo con pg_dump en una transacción de solo lectura dentro del contenedor de captura cuyo puerto publicado es 127.0.0.1:5466. Destino recién creado en 127.0.0.1:5456, base mp025b, esquema public, rol propietario local mp_test. La restauración de tablas de aplicación conserva las filas clasificadas en captura. Las migraciones crean de nuevo el esquema y PostGIS aporta sus propias tablas de extensión. Todos los resultados y la copia están fuera de Git.

Para reproducir desde la copia conservada (bash, desde la raíz, con las dependencias Python de requirements.txt y la imagen ya presentes):

```bash
set -eu
capture=/Users/matu/Documents/DATA/madrid-pulse/data/capture/2026-11-26
dump="$capture/analysis/smoke-20261125T231945Z.dump"
manifest="$capture/smoke/manifest.json"
shasum -a 256 -c "$dump.sha256"
docker run --pull=never --name mp025b-smoke -d -p 127.0.0.1:5456:5432 \
  -e POSTGRES_DB=mp025b -e POSTGRES_USER=mp_test -e POSTGRES_PASSWORD=mp_local postgis/postgis:17-3.5
trap 'docker rm -fv mp025b-smoke' EXIT
until docker exec mp025b-smoke pg_isready -h 127.0.0.1 -U mp_test -d mp025b; do sleep 1; done
export MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME=''
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5456/mp025b
export MADRID_PULSE_GTFS_SOURCE=/Users/matu/Documents/DATA/madrid-pulse/data/gtfs_static/fomento_transit.zip
for sql in infra/migrations/*.up.sql; do
  docker exec -i mp025b-smoke psql -X -v ON_ERROR_STOP=1 -U mp_test -d mp025b < "$sql"
done
python -m infra.operate.mark_disposable_db
docker cp "$dump" mp025b-smoke:/tmp/copy.dump
docker exec mp025b-smoke sh -ec "pg_restore -l /tmp/copy.dump | awk '/TABLE DATA public/ && !/spatial_ref_sys/' > /tmp/data.toc
 pg_restore -L /tmp/data.toc --single-transaction --disable-triggers -U mp_test -d mp025b /tmp/copy.dump"
python -m unittest -v infra.operate.validation.test_metrics tests.e2e.test_stop_state.RecoveryMeasurement
ruff check infra/operate/validation
python -m compileall -q infra/operate/validation
for n in 1 2; do
  python -m infra.operate.validation.replay "$manifest" "$dump" > "$capture/analysis/reproduccion-$n.json"
done
cmp "$capture"/analysis/reproduccion-{1,2}.json
shasum -a 256 "$capture"/analysis/reproduccion-{1,2}.json
```

Para cada jornada se toma otra copia consistente tras finalizar la sesión, se registra su SHA-256 y se sustituyen únicamente las rutas de dump y manifiesto. Cada par pertenece a una sesión. Los resultados JSON externos contienen el detalle y el HEAD de ejecución, por lo que repetir con otro HEAD cambia el hash del informe aunque las métricas coincidan.

### Verificaciones ejecutadas

| Comprobación | Resultado real |
|---|---|
| Dos procesos independientes de replay sobre la copia restaurada | PASS. HEAD ce3ee3a2fef2cb60ff0ff6d6d62ec5b5b3861714, cmp con salida 0. final-1.json y final-2.json en analysis, ambos con SHA-256 263f9612496ee78873411d9b70df4a6527efe6b321cdca1cfb3c1ea84230e4ba |
| unittest de métricas y recuperación sintética | PASS. Ran 4 tests, OK. Salto sintético 311.371489 m |
| ruff check y compileall | PASS. All checks passed! y compilación con salida 0 tras corregir 11 diagnósticos de estilo de la ejecución inicial |
| Aislamiento | PASS. Las cuatro migraciones up se aplicaron desde cero. Verificados mp025b / public / mp_test / madrid-pulse:disposable. docker rm -fv mp025b-smoke eliminó el contenedor y su volumen anónimo. La consulta posterior por nombre exacto no devolvió contenedores |
| Revisión independiente y jornadas 2 y 3 | Pendientes. Sin dictamen ni autorización de cierre de FR-01 |

Ejecutor Codex, modelo/esfuerzo solicitados gpt-6.2-astra · high según despacho. La identidad efectiva del backend no se verificó de forma independiente. La revisión corresponde a Claude Opus · high. El propietario conserva la decisión de cierre.
