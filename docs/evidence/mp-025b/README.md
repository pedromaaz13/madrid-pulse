# MP-025b · Validación provisional del motor sobre captura MP-028

**Smoke insuficiente. FR-01 sigue abierto.** El 26 de noviembre de 2026, entre las 00:11:13 y las 00:16:13 de Madrid, el colector obtuvo 212 posiciones de 24 vehículos. Solo 80 pares permiten contrastar una predicción con la siguiente observación. En 19 de esos 80 la corrección supera 200 m. El máximo supera 3 km. La guarda M7 también presenta un resultado adverso: en 9/10 pares iniciados en tránsito o aproximación con avance observado ≥ 100 m, la predicción fue de 0 m. La decisión sobre FR-01 corresponde al propietario tras las jornadas y los demás gates.

| Muestra | Duración | Vehículos / viajes con corredor | Pares medibles / candidatos | p50 / p90 / p95 / máximo descriptivos (m) | Criterio N ≥ 500 y mediana ≤ 200 m |
|---|---:|---:|---:|---|---|
| Smoke | 300,090699 s | 11/24 vehículos y 11/24 viajes | 80/188 | 0 / 1605,043752 / 2417,157027 / 3045,815884 | Insuficiente |
| Jornada 1 | Pendiente del manifiesto del coordinador | — | — | — | NO EJECUTADO |
| Jornadas 2 y 3 | Pendientes de captura | — | — | — | NO EJECUTADO |

## Qué se midió y qué quedó fuera

Cada vehículo aporta sus filas consecutivas en el orden de observación (desempate por ID). Se conserva el vínculo a la fila seleccionada por el replay mediante el hash bruto y el reloj GPS. Para cada par se exige la misma circulación (vehículo, viaje y día de servicio), intervalo positivo ≤ 180 s, corredor validado, proyecciones a ≤ 200 m de la vía y envolvente atribuible a la primera ancla. Se calcula el valor absoluto de la diferencia entre el progreso dirigido de la segunda proyección y la envolvente de producción evaluada al **instante GPS de la segunda observación**. La proyección bruta de destino se incluye aunque el motor conserve una ancla anterior. Por eso esta medida de error de predicción puede diferir del movimiento mostrado al refrescar. Cuantiles con interpolación lineal, decisiones sobre valores sin redondear.

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

## Retenciones y semántica del operador

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

## Casos adversos

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

## Caducidad, recuperación y procedencia

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

## Reproducción y custodia de las entradas

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

## Verificaciones ejecutadas

| Comprobación | Resultado real |
|---|---|
| Dos procesos independientes de replay sobre la copia restaurada | PASS. HEAD ce3ee3a2fef2cb60ff0ff6d6d62ec5b5b3861714, cmp con salida 0. final-1.json y final-2.json en analysis, ambos con SHA-256 263f9612496ee78873411d9b70df4a6527efe6b321cdca1cfb3c1ea84230e4ba |
| unittest de métricas y recuperación sintética | PASS. Ran 4 tests, OK. Salto sintético 311.371489 m |
| ruff check y compileall | PASS. All checks passed! y compilación con salida 0 tras corregir 11 diagnósticos de estilo de la ejecución inicial |
| Aislamiento | PASS. Las cuatro migraciones up se aplicaron desde cero. Verificados mp025b / public / mp_test / madrid-pulse:disposable. docker rm -fv mp025b-smoke eliminó el contenedor y su volumen anónimo. La consulta posterior por nombre exacto no devolvió contenedores |
| Revisión independiente y jornadas 1–3 | Pendientes. Sin dictamen ni autorización de cierre de FR-01 |

Ejecutor Codex, modelo/esfuerzo solicitados gpt-6.2-astra · high según despacho. La identidad efectiva del backend no se verificó de forma independiente. La revisión corresponde a Claude Opus · high. El propietario conserva la decisión de cierre.
