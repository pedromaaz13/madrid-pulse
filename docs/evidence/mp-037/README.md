# MP-037 · Contradicciones entre estado de parada y GPS

**Estudio offline de una jornada, para revisión independiente.** FR-01 sigue abierto y el NO-GO público sigue vigente.

## Diseño de la comparación

M7 en [ADR-0014, enmienda 1 §3 y §8](../../adr/0014-amendment-stop-state.md) pregunta, con la **siguiente** observación ya disponible, si la primera envolvente predijo exactamente cero avance ante ≥100 m de avance del GPS entre muestras. R4 decide en el **primer** instante si retiene un `INCOMING_AT` cuyo GPS efectivo ya está en zona de su parada declarada. Ejecutar «R4 antes de M7» equivale al control. Convertir M7 en una excepción en tiempo real requeriría una señal causal especificada aparte. Las variantes usan el GPS y el horario ya disponibles para cada ancla.

| Política | Regla de ensayo |
|---|---|
| `control` | Renderizador de producción. R-CANCEL, clasificación, R1, R4, R6x, R6, R2 y R5, con R7→R8 para estados incoherentes. |
| `gps_en_zona` | Conserva R4 solo si la proyección del GPS **efectivo y aceptado** está a ≤ τ de la ocurrencia declarada. Es el predicado que ya exige R4. El arnés comprueba esa implicación en cada llamada a R4. |
| `sin_r4` | Suprime R4 en todas sus activaciones. Pasa a R6x, R6, R2 y R5 sin espera de zona. Es una referencia para medir el coste de quitar la guarda. |
| `r4_r8` | Sustituye las activaciones de R4 por R8, incluida la espera programada de zona cuando corresponde. |
| `r4_dos_gps` | Deriva a R8 solo cuando hay muestra previa de zona utilizable, anterior a la efectiva y con edad ≤ horizonte vigente, y esa proyección queda fuera de la zona de la ocurrencia declarada. Con muestra previa dentro de zona o sin evidencia previa utilizable, se conserva R4. |
| `parada_previa` | En `STOPPED_AT` incoherente con plan positivo, exige un `stop_id` que resuelva una sola ocurrencia y una muestra previa de zona utilizable y reciente dentro de τ de ella. Retiene en el progreso del **GPS efectivo** durante su horizonte, con `coherent=false`; el estado contradictorio sigue registrado. |

Las variantes de R4 invocan el constructor de producción con el contexto de tránsito o degradación correspondiente. Esa sustitución interna sirve para obtener una curva hipotética. El arnés conserva la etiqueta del operador de la observación original en sus registros. Resuelve la ocurrencia según §4.1 y reutiliza `zone_sample` calculado por la API. En `parada_previa`, esa muestra respalda espacialmente la parada declarada, aunque por sí sola no acredita el estado previo del operador. Un identificador ausente, ajeno al viaje o con ocurrencias repetidas queda sujeto a la política vigente. [Constructor de producción](../../../packages/movement/rendering.py#L180) y [selección de muestra previa](../../../apps/api/snapshot.py#L446).

Se contrastó P-024 con el manifiesto. Horizonte de 180 s, distancia a vía de hasta 200 m, tope de velocidad estimada de 160 km/h, zona de 50 m, espera mínima de 30 s y edad máxima de cancelación de 600 s. Los 100 m de M7 y los 200 m de salto son criterios de auditoría heredados. [Parámetros de producción](../../../packages/movement/model.py#L39), [decisión del propietario](../../adr/0014-amendment-owner-decision.md) y [métricas de MP-025b](../mp-025b/README.md).

### Población y unidades de medida

Se reutilizan el replay y las vistas temporales de [MP-025b](../mp-025b/README.md). Dos segmentos de 9 340 y 20 167 filas, con reinicio de historial tras la suspensión. Se aplican los filtros de MP-025b a los 29 095 pares consecutivos de los 347 vehículos, con 11 425 pares H1 evaluables y 516 instantes de replay. El control comprueba contra MP-025b las exclusiones, la distribución H1, los recuentos de casos, las salidas retenidas y su distribución de latencia. Las políticas reciben la misma selección de observaciones, servicio y geometría. El proceso instrumenta el constructor de envolventes en memoria. La selección del ancla, las anomalías, la cancelación y las respuestas originales quedan a cargo de producción. Las variantes se proyectan en progreso dirigido sobre el mismo corredor.

- **Avance en `STOPPED_AT`.** La proporción de planes con velocidad positiva mide autorización de avance. En la cohorte de contradicciones se mide también cuánto se habría presentado al primer fotograma y antes del recambio del ancla, incluido el tiempo en fase de avance. Los casos con GPS idéntico entre observaciones dan una medida adicional de sobreavance potencial. La identidad de coordenadas puede deberse a cuantización.
- **Retención y latencia.** `STOPPED_AT` cuenta pares con desplazamiento GPS proyectado hacia delante >0 m. `INCOMING_AT` e `IN_TRANSIT_TO` cuentan M7 (≥100 m). Hay retención cuando el progreso previsto en la hora GPS de B sigue en el ancla de A. La latencia va desde la hora GPS de B hasta el primer fotograma de replay del mismo viaje/día en el que el ancla efectiva, al menos tan reciente como B, y la curva presentada están por delante de A. Un retorno del ancla efectiva a la posición inicial o el fin de la ventana puede dejar la latencia sin resolver. La comparación de cuantiles de latencia entre políticas incluye solo los casos retenidos con latencia evaluable para cada una.
- **Error H1 con GPS de destino.** Distancia absoluta en metros de progreso dirigido entre el pronóstico de A y la proyección del GPS B, a la hora GPS de B. Incluye GPS B proyectables que el motor rechaza como ancla.
- **Discontinuidad al presentar B.** Diferencia firmada de progreso en el instante de visibilidad de B entre el fotograma hipotético de B y la continuación del plan de A. Los dos anclajes deben ser efectivos en fotogramas consecutivos del vehículo, del mismo viaje, día y versión de geometría. La continuación de A se congela al llegar a su horizonte F1. Un valor negativo es un retroceso. Si B se rechaza, falta la transición A→B y ese par queda fuera del denominador de discontinuidad. La unidad es arco dirigido, y la percepción del salto en el navegador permanece UNVERIFIED.

## Resultados

### Los 19 planes positivos con `STOPPED_AT`

Fueron **19/18 242** declaraciones y **19/7 001** con envolvente propia, en 17 vehículos. Hubo 20 planes con GPS fuera de la zona declarada, uno con velocidad cero, y 6 981 planes coherentes, todos con velocidad cero. Las otras 11 241 declaraciones carecían de envolvente propia. En los 19 casos el GPS efectivo se proyectó **709,5–7 110,2 m hacia delante** de la parada que declaraba el operador. Los 19 GPS iniciales se aceptaron como ancla. R7 marcó la contradicción y R8 generó 16 curvas con espera de zona de horario y tres curvas de avance por horario sin espera, a **8,44–14,35 m/s**.

| `stop_id` en A | Planes positivos | Qué publicó el siguiente GPS del mismo segmento |
|---|---:|---|
| 35605 | 8 | Siete conservaron `STOPPED_AT/35605`, a −2,5 m de su parada. Los siete GPS fueron sustituidos por el ancla anterior. Uno quedó al final del segmento. |
| 35600 | 5 | Cinco conservaron `STOPPED_AT/35600`, a −16,9 m. Se marcaron por retroceso y los cinco se aceptaron como ancla. |
| 17003 | 3 | Tres conservaron `STOPPED_AT/17003`, a +2,9 m. Los tres GPS fueron sustituidos por el ancla anterior. |
| 17001 | 1 | `20428` cambió a `STOPPED_AT/17000` en la misma coordenada bruta. |
| 60100 | 1 | `20437` cambió a `STOPPED_AT/18000` en la misma coordenada bruta. |
| 18003 | 1 | `20721` quedó al final del primer segmento. |

En **15/19** la siguiente fila apoya la parada declarada, con regreso a ≤17 m y el mismo `stop_id`. **10/15** de esos GPS se rechazaron para presentación (`backward_jump`). Los dos cambios de `stop_id` con GPS intacto y los dos cortes sin sucesor dejan especialmente ambiguo dónde estaba el tren. En los 19 planes, el avance máximo autorizado hasta caducar tuvo p50 **2 232,27 m** y máximo **2 468,83 m**. La distancia desde el ancla hasta el recambio o el fin del segmento fue positiva en **16/19**, p50 **660,63 m** y máximo **1 024,27 m** sobre los 19. Al contar solo desde el primer fotograma, la curva avanzó hasta **885,91 m** y permaneció en fase de avance hasta **61,78 s** (p50 **50,31 s**). El tiempo visible del ancla, incluida cualquier espera, tuvo p50 **61,46 s**, máximo **64,98 s** y dos casos censurados.

El peor avance antes del recambio fue `20434`, GPS de **08:33:30 UTC**, `STOPPED_AT/17003`: la proyección saltó a **17 765,91 m**, frente a **15 435,09 m** de la parada, y se rechazó el siguiente GPS (**15 438,00 m**). La envolvente efectiva siguió avanzando hasta **1 024,27 m** adicionales antes de salir de presentación. El caso `19595` a **08:20:52 UTC** ilustra el alcance de `parada_previa`: mantiene la proyección efectiva de **32 677,18 m**, a **709,47 m** de `35600`. Suprime **31,31 m** de extrapolación y conserva la corrección posterior al GPS aceptado de **31 950,77 m**. Esa corrección sigue siendo de **−726,42 m** en el arco.

### Las 135 retenciones M7

**135/1 441** oportunidades M7, en **73 vehículos**, empezaron por `INCOMING_AT` en la zona de la parada declarada. La distancia inicial a la parada tuvo p50 **2,91 m** y máximo **21,84 m**. Las 135 retenciones tuvieron avance presentado de cero antes de B. El intervalo GPS A→B tuvo p50 **40 s**, p90 **42 s** y máximo **60 s**. Desde el primer fotograma ya visible de A al que mostró B, p50 **30,82 s** y máximo **61,57 s**. El avance bruto proyectado tuvo p50 **1 916,02 m**, p90 **3 046,34 m** y máximo **7 110,17 m**.

| Estado GPS de B | Mismo `stop_id` | Otro `stop_id` | B publicado como ancla efectiva |
|---|---:|---:|---:|
| `INCOMING_AT` | 2 | 112 | 114/114 |
| `STOPPED_AT` | 6 | 9 | 15/15 |
| `IN_TRANSIT_TO` | 5 | 1 | 6/6 |
| Total | 13 | 122 | 135/135 |

La mayor discontinuidad del control en este grupo fue `20233`, de `INCOMING_AT/60100` a `INCOMING_AT/18000` a **07:49:30 UTC**. Las coordenadas brutas cambiaron de latitud 40,352676 y longitud −3,684073 a latitud 40,406540 y longitud −3,689511 en **40 s**. Ambos GPS fueron aceptados. El control corrigió **+7 110,17 m**, frente a **+6 653,30 m** al sustituir R4 por R8 y **+6 587,78 m** al omitir R4. El peor H1 del estrato completo de `INCOMING_AT` fue `20213` a **06:11:10 UTC**, con desplazamiento proyectado de **−23 633,99 m**, `backward_jump/implausible_speed` y reutilización del ancla efectiva. El signo lo excluye de M7 y el rechazo excluye la transición A→B de la discontinuidad. Se conserva como caso adverso en el H1 de todas las políticas.

### Comparación por política y estado de A

Las tablas dan p50 / p90 / máximo en segundos para la latencia y en metros para los errores y saltos. `GPS idéntico` cuenta pares con avance derivado positivo frente a coordenadas brutas repetidas. `Salto >200` cuenta el valor absoluto de la discontinuidad. R4 antes de M7 y `gps_en_zona` tienen el mismo resultado que el control.

| Política y estado | Planes positivos | Retenciones / oportunidades | Latencia, n | Avance con GPS idéntico |
|---|---:|---:|---|---:|
| Control, `STOPPED_AT` | 19/7 001 | 402/402 | 8,32 / 17,27 / 49,04 (402) | 0/6 499 |
| `parada_previa`, `STOPPED_AT` | 13/7 001 | 402/402 | 8,32 / 17,27 / 49,04 (402) | 0/6 499 |
| Control, `INCOMING_AT` | 18/2 335 | 135/136 | 9,10 / 17,91 / 21,88 (135) | 5/2 053 |
| `r4_dos_gps`, `INCOMING_AT` | 759/2 335 | 127/136 | 9,41 / 18,75 / 21,88 (127) | 259/2 053 |
| `r4_r8`, `INCOMING_AT` | 2 153/2 335 | 11/136 | 15,83 / 19,50 / 20,98 (11) | 1 327/2 053 |
| `sin_r4`, `INCOMING_AT` | 2 153/2 335 | 0/136 | — (0) | 1 908/2 053 |
| Todas, `IN_TRANSIT_TO` | 2 289/2 291 | 0/1 305 | — (0) | 452/452 |

Cada variante cambia únicamente planes del estado al que se dirige. El salto presentado depende también del plan de B y puede cambiar en pares que empiezan en otro estado. Las 402 oportunidades de `STOPPED_AT` pertenecen a los **6 918** pares H1 del estrato. Los 402 desplazamientos alcanzan 100 m. Tres B se rechazaron inicialmente y el máximo de **49,04 s** corresponde a `20793`, con el GPS B proyectado **+21 511,83 m**, rechazado por `implausible_speed`. Todas las latencias de las retenciones fueron evaluables en esta captura.

| Política y estado | Error H1 p50 / p90 / máx. | Salto presentado p50 / p90 / máx. | Salto >200 m | Retrocesos |
|---|---:|---:|---:|---:|
| Control, `parada_previa` y `r4_dos_gps`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 23,59 / 7 842,46 (6 903) | 490/6 903 | 5/6 903 |
| `r4_r8`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 28,31 / 7 842,46 (6 903) | 491/6 903 | 5/6 903 |
| `sin_r4`, `STOPPED_AT` | 0 / 0 / 21 511,83 (6 918) | 0 / 28,31 / 7 842,46 (6 903) | 493/6 903 | 5/6 903 |
| Control y `parada_previa`, `INCOMING_AT` | 0 / 0 / 23 633,99 (2 267) | 0 / 110,55 / 7 110,17 (2 216) | 179/2 216 | 35/2 216 |
| `r4_dos_gps`, `INCOMING_AT` | 0 / 162,12 / 23 633,99 (2 267) | 0 / 246,90 / 7 110,17 (2 216) | 300/2 216 | 654/2 216 |
| `r4_r8`, `INCOMING_AT` | 181,41 / 578,97 / 23 633,99 (2 267) | 260,34 / 586,54 / 6 659,34 (2 216) | 1 216/2 216 | 1 473/2 216 |
| `sin_r4`, `INCOMING_AT` | 350,16 / 750,58 / 23 633,99 (2 267) | 382,91 / 771,96 / 6 587,78 (2 216) | 1 850/2 216 | 1 937/2 216 |
| Todas salvo `sin_r4`, `IN_TRANSIT_TO` | 499,77 / 2 188,64 / 18 620,72 (2 240) | 372,43 / 1 660,64 / 6 588,29 (1 996) | 1 400/1 996 | 939/1 996 |
| `sin_r4`, `IN_TRANSIT_TO` | 499,77 / 2 188,64 / 18 620,72 (2 240) | 382,99 / 1 715,38 / 6 588,29 (1 996) | 1 436/1 996 | 871/1 996 |

Dentro de los 135 casos originales de M7, los saltos >200 m siguieron en **135/135** con cada política. El máximo absoluto de `r4_r8` en `INCOMING_AT` se dio en `20237`, con `60100→18000` en el GPS de **08:07:30 UTC**. En `sin_r4` el máximo fue el mismo caso `20233` que en el control, con **+6 587,78 m**. En `STOPPED_AT` el máximo observado al presentar B fue `20430` a **08:52:10 UTC** y en `IN_TRANSIT_TO` fue `19588` a **07:56:10 UTC**. Las **310** segundas proyecciones sustituidas por un ancla anterior siguieron disponibles para H1, con el estado y las banderas de producción conservados.

## Recomendación

**Conservar R4 y mantener M7 como guarda retrospectiva.** Suprimir R4 llevó la guarda a 0/1 441, con avance derivado añadido en **1 903** pares `INCOMING_AT` de GPS idéntico y **1 671** discontinuidades adicionales >200 m sobre 2 216. Derivar todos los casos a R8 dio una mejora intermedia en M7 y añadió **1 037** discontinuidades >200 m. La opción de dos GPS evitó solo **8/135** retenciones y añadió **121** discontinuidades de esa magnitud. El resultado literal de M7 puede mejorar mientras la presentación empeora en otros pares. Reportar ambos resultados permite cuantificar ese coste.

**Validar `parada_previa` como candidata para `STOPPED_AT` incoherente.** Pasó de 19 a 13 planes positivos y de 16 a 11 con avance antes del recambio en esa cohorte. En esta jornada conservó 402/402 retenciones con la misma latencia y 490/6 903 saltos presentados >200 m. Mantener el GPS como ancla preserva la procedencia y evita un traslado artificial a la estación, a cambio de que la posición mostrada pueda seguir lejos de ella. El vehículo 20437 demuestra que la parada declarada puede cambiar con el GPS intacto. La muestra previa respalda una zona y el significado físico del cambio sigue abierto.

### Texto propuesto para decisión del propietario, condicionado a jornadas 2 y 3

Esta propuesta afecta al paso **R7→R8 de §4.2**. R4 conserva su lugar y la nueva regla tiene prioridad posterior a la comprobación de versiones y a R-CANCEL. Texto para insertar en el caso **INCOHERENTE**, antes de aplicar R8.

> Si la observación efectiva declara `STOPPED_AT`, el ancla está fuera de τ de la parada declarada, `stop_id` identifica una única ocurrencia del itinerario y R8 autorizaría una velocidad positiva, se consultará la muestra previa de zona de §4.6. Si esa muestra es proyectable con el criterio vigente, pertenece al mismo viaje, su edad respecto del ancla es estrictamente positiva y no supera el horizonte vigente, y queda dentro de τ de la ocurrencia declarada, se retendrá el progreso del GPS efectivo hasta reemplazo o caducidad. La causa será `incoherent_stop_prior_gps`, con `stop_state.coherent=false`. En los demás casos se aplicará R8. La parada declarada seguirá disponible para explicar la discrepancia. La coordenada derivada conservará el ancla efectiva.

- **§4.3–§4.5.** Registrar la causa y la muestra previa que condiciona la envolvente conforme a la identidad inmutable por ancla/run. Conservar el GPS bruto, `map_matched`, la parada declarada y el progreso confirmado. La degradación conserva la procedencia que declara `stop_state`; el consumidor expone la contradicción y la causa de la retención. Al caducar, F1 congela la curva autorizada en su extremo.
- **§4.6 y §8.** Fijar que se usa la muestra previa admitida por el replay, incluida la validación del mismo viaje, la geometría y la edad. Incorporar pruebas de ocurrencias múltiples, identificadores ausentes, desconocidos o que cambian, zona en el límite, muestra caducada o rechazada, cancelación, cambio de perfil y nuevo anclaje tras quedarse sin GPS. Mantener AC-M7 con el mismo predicado y añadir al informe su desglose por estado, aceptación del destino y efecto de presentación.
- **Riesgos.** Una muestra anterior dentro de la zona puede coexistir con una salida real. Una parada repetida necesita otra señal de ocurrencia y sigue la degradación existente. El GPS cuantizado puede retener un punto erróneo. La evidencia de esta jornada no estima la frecuencia de esos riesgos fuera de su población.
- **Validación antes de decidir.** Congelar esta definición y P-024. Repetir control y variantes por separado sobre las jornadas 2 y 3, con SHA-256, GTFS y catálogo por sesión. Revisar para cada política y jornada los pares con GPS aceptado y rechazado, los cambios de parada con GPS idéntico, las salidas retenidas, la latencia y las colas de discontinuidad. Inspeccionar todos los cambios de decisión de `parada_previa` y comprobar si la evidencia operativa disponible corrobora alguna salida real. Verificar F1, R-CANCEL y el cliente con casos dirigidos antes de promover la propuesta. Presentar los deltas por jornada y los casos adversos al propietario para que decida si acepta el coste de retención. Los resultados históricos de MP-025b conservan el criterio original.

### Límites

**UNVERIFIED:** momento físico de detención o salida, posición física exacta de un tren, semántica general de `current_stop_id`, si la cuantización proviene del dispositivo o de otro paso del feed, visibilidad histórica por hora civil, salto percibido en navegador, efecto de una implementación de producción de las variantes y extrapolación a otras jornadas, líneas, horas o cobertura de corredor. Las anclas y pares del mismo vehículo no son observaciones independientes. El estudio cubre una jornada, dos ventanas y la fracción con corredor y GPS evaluables. La ausencia de retroceso al caducar para las variantes es una propiedad del cálculo acotado del arnés en estas métricas. Queda pendiente la validación completa del contrato F1 de una implementación futura.

## Reproducción y custodia

Los archivos privados se leen en su ubicación original. Solo se restaura una copia en el contenedor `mp037-study` con volumen anónimo. Destino `postgresql://mp_test:mp_local@127.0.0.1:5468/mp037`, esquema `public`, rol local propietario `mp_test`, marca `madrid-pulse:disposable`. Desde el repositorio, con Python 3.12 y las dependencias ya disponibles, Docker con la imagen local y las rutas privadas de la jornada.

| Entrada | SHA-256 o identificador |
|---|---|
| Dump `analysis/session-1-20261126T090138Z.dump` | `95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1` |
| `session-1/manifest.json` | `5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e` |
| GTFS `fomento_transit.zip` | `58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e` |
| Catálogo compuesto verificado por el arnés | `sha256:f071ad8d6e217331bc3cdcc2304b7a300ee8306f346acc52b9276e3e6aa4702d` |
| Fixture sintética incluida en `test_contradictions.py` | `54bdb40ad60896637724e9c5324c0687d23b7a4dc9f8b5f7e791d56f1070134b` |
| Base de producción `origin/main` | `d0dd0bca62b18200b082a30504dca4d75f73171d` |
| HEAD del arnés durante las dos ejecuciones | `1054ec8901529da2996f97e5731de3028943249d` |

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

El JSON privado incluye `stopped_cases`, `m7_cases`, `summary` y `worst`, con entrada, estado y parada efectivos, proyección, reloj GPS y reloj del replay. También identifica si se retuvo una observación anterior. El hash del JSON incorpora el HEAD. Con otro HEAD se comparan los datos tras omitir `inputs.head`.

## Comprobaciones ejecutadas

| Comando o comprobación | Resultado observado |
|---|---|
| `shasum -a 256 -c "$dump.sha256"`, cuatro migraciones, `mark_disposable_db` y `pg_restore --single-transaction` | **PASS**. El volcado dio `OK`. Puerto publicado `127.0.0.1:5468`. La comprobación SQL devolvió `mp037\|public\|mp_test\|madrid-pulse:disposable`. |
| Dos procesos independientes de `python -m infra.operate.validation.contradictions "$manifest" "$dump"` y `cmp` | **PASS**. Salida idéntica byte a byte. SHA-256 de ambos JSON: `9a489bee276d9a6f1b76a35d1d1c73f71f84fb32def015e6de00ad8a0cc9a502`. Resultados privados en `/tmp/mp037-evidence/run-1.json` y `run-2.json`. |
| `python -m unittest -v infra.operate.validation.test_contradictions` | **PASS**, `Ran 6 tests`, `OK`. R4 y zona en el límite, precedencia sobre terminal/pre-salida, R-CANCEL, perfil distinto, muestra previa ausente o caducada, IDs ausentes/ajenos/repetidos, censura de latencia y denominador de transición efectiva. |
| Todos los módulos Python enumerados en `.github/workflows/ci.yml`, más `infra.operate.validation.test_metrics`, `infra.operate.validation.test_contradictions` y `tests.governance.test_governance` | **PASS**, `Ran 375 tests`, `OK (skipped=18)`. Se usó la base limpia y marcada `mp037_ci` del mismo contenedor con `MADRID_PULSE_ENV=test` y `MADRID_PULSE_REQUIRE_DB=1`. Los 18 skips iniciales correspondieron a 13 casos del GTFS oficial completo y cinco del soak MP-007. |
| `python -m unittest -v packages.geo.tests.test_catalog.MadridCorridorCatalogRealTests packages.gtfs.tests.test_catalog.FullMadridCatalogRealFeedTests` | **PASS**, `Ran 13 tests`, `OK`. Se expuso temporalmente el ZIP local validado en la ruta de fixture `data/hito-03/replay/fomento_transit.zip`. Soak MP-007 **NO EJECUTADO**, por ausencia de esa población en la base limpia. |
| `npm ci --offline --no-audit --no-fund`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` en `apps/web`, Node 22.13.1 | **PASS**. 11 archivos y 110 tests en Vitest. Build con aviso de tamaño y validación del worker MapLibre de 550 754 bytes. |
| `ruff check infra/operate/validation`, `python -m compileall -q infra/operate/validation`, `python scripts/governance/check_docs.py`, `git diff --check` | **PASS**. `All checks passed!`, compilación sin errores, `Documentación de gobernanza correcta.` y salida cero de Git. |
| `infra.operate.validation.test_segments` en el puerto histórico que exige esa prueba | **NO EJECUTADO**. La prueba valida el endpoint específico de MP-025b. El propio replay de MP-037 llama a `check_segment` contra las tablas restauradas y exige coincidencia de exclusiones y población. |
| `docker rm -fv mp037-study`, consulta de nombre exacto y `lsof -nP -iTCP:5468 -sTCP:LISTEN` | **PASS**. Docker devolvió `mp037-study` al retirarlo. Después, la consulta de contenedores y la de puerto no devolvieron entradas. |

Para repetir la suite Python de CI en una base limpia del mismo contenedor, crear `mp037_ci`, aplicar las cuatro migraciones y marcarla como desechable con el DSN de esa base. El comando se ejecutó con ese DSN, `MADRID_PULSE_ENV=test` y `MADRID_PULSE_REQUIRE_DB=1`.

```bash
python -m unittest -v $(awk '/^            (apps|packages|services|tests)\./ {print $1}' .github/workflows/ci.yml) \
  infra.operate.validation.test_metrics infra.operate.validation.test_contradictions \
  tests.governance.test_governance
```

Ejecutor según despacho: Codex `gpt-6.2-sol` · medium. Identidad efectiva del backend UNVERIFIED. La revisión corresponde a Claude `claude-opus-5-5` · high sobre el HEAD entregado.
