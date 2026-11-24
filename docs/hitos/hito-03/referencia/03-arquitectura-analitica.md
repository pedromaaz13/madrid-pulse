# Plataforma analítica de Cercanías Madrid

## Inventario y decisión para el siguiente hito

| Pieza | Implementación en main | Siguiente entrega |
|---|---|---|
| Captura | Colector Python con polling, reintentos, validación, normalización, filtro por núcleo y deduplicación en PostgreSQL | Ejecutarlo 24/7 en un host independiente de Orca. Propietario único del polling, reinicio supervisado, comprobación de última recepción por feed y archivo de la respuesta original. |
| Almacenamiento operativo | PostgreSQL/PostGIS y migración SQL. FastAPI lee la base; carga GTFS y un corredor OSM en memoria | Estado activo indexado, GTFS e índices espaciales versionados, aislamiento entre Live, histórico y reprocesamientos. |
| Distribución del directo | Cada navegador sondea FastAPI cada 20 s. La API recalcula por petición y consulta retrasos uno a uno | Tras cada ingesta correcta, producir snapshot compartido, validarlo y publicar puntero a la última versión completa. Clientes con polling condicional y ETag. |
| Histórico | Snapshotter de PostgreSQL a Parquet ZSTD, con consultas DuckDB y agregados Python/SQL por núcleo, ruta y estación | Archivo inmutable, manifiesto de captura y publicación por partición. Automatizar exportación y reproceso. Cuantificar periodos sin observaciones. |
| Analítica y usuarios | analytics/dbt documenta la intención. ADR-0013 aceptado difiere dbt-core. API v1 implementa Live, líneas, estaciones y salud; History/Explore, autenticación y SQL Lab son evolución | Modelo semántico probado contra la capa gold. Accesos diferenciados. Consultas públicas parametrizadas y, más adelante, SQL Lab en una réplica de lectura. |

**Para este volumen elegiría un servicio de ingesta siempre encendido y snapshots publicados por HTTP.** En local se puede desarrollar y reproducir con PostgreSQL, colector, API y Vite. En un host económico se ejecutan los mismos tres procesos de backend, se sirve el frontend estático y se conserva el histórico en almacenamiento de objetos. Al cerrar el portátil, el host continúa. Una segunda instancia de la API puede crecer independientemente del único escritor activo del colector.

Kafka tendría un caso de uso cuando varios consumidores independientes necesiten retener y reproducir eventos con sus propios offsets, o cuando medir el retraso de procesamiento demuestre un cuello que la solución simple no absorbe. Un WebSocket o SSE puede reducir peticiones desde clientes, pero no mejora la antigüedad que entrega Renfe. Medir antes API p95, ingesta p95, edad del snapshot publicado, número de clientes, transferencia y retraso de los consumidores. No contratar infraestructura para esta propuesta.

## Contrato del directo

Mantener API v1 mientras se introduce de forma aditiva el contrato de snapshot. Identificar el snapshot y sus fuentes por separado. Ejemplo conceptual:

| Campo | Interpretación |
|---|---|
| snapshot_id, generated_at, gtfs_version, geometry_version | Reproducir qué vio el cliente. Rechazar una actualización más antigua que la ya mostrada. |
| feed_published_at, received_at, last_success_at, last_attempt_at, last_error | Publicación en origen, recepción y estado de transporte o parseo. Un feed fallido puede conservar última respuesta buena con su edad original. |
| service_date, trip_id, start_time cuando haga falta, route_id, vehicle_id | Identidad del servicio y de la observación. Mantener source IDs como texto y la evidencia de resolución. Tratar refuerzos y ambigüedades explícitamente. |
| gps_observed_at, raw_coordinates, matched_coordinates, pattern_id, progress_m, calculated_at | Evidencia para reproducir el movimiento y distinguir observación, ajuste a vía y cálculo visual. |
| delay_seconds, delay_observed_at, next_stop_id, expected_arrival_at, time_source | Llegada prevista, procedencia y antigüedad propias. Leer las predicciones por parada y conservar las cancelaciones y SKIPPED. Null significa desconocido. |
| matched, reason, freshness, active | Poder explicar un tren sin ruta, una línea sin corredor o una observación retirada de la flota. Registrar por separado salud de fuente y de geometría. |

Distinguir el último **snapshot válido** con cero entidades de una descarga fallida. Una caída parcial de alertas no debe vaciar posiciones o tablero. Mantener una ventana de gracia configurable para intermitencias, excluir activos finalizados y conservarlos en History. El TTL para mostrar trenes, el umbral para dibujarlos atenuados y el umbral de puntualidad son parámetros diferentes.

## Modelo de datos para BI y SQL

| Tabla propuesta | Grano / clave lógica | Uso |
|---|---|---|
| dim_service_day, dim_line, dim_stop, dim_pattern | Día operativo local; línea por núcleo; estación física y códigos fuente; secuencia de paradas versionada | Filtrar por ramal y estación sin duplicar viajes en intercambiadores. Conservar fecha, versión y validez. |
| fct_trip_service | Una circulación por núcleo, día de servicio e instancia GTFS. Admitir un origen ADDED y una resolución pendiente | Denominador programado, añadido o cancelado por separado. Fecha de calendario y de servicio pueden diferir. |
| fct_vehicle_observation | Observación de vehículo fuente por hora observada y revisión/hash | Replay, edad GPS, cambios de vehículo/viaje. Una consulta de mapa o un frame jamás crean una fila aquí. |
| fct_stop_prediction | Predicción emitida en una captura para una instancia de viaje y secuencia de parada | Comparar horario y ETA y cuantificar cambios. Una predicción, incluso la última, debe conservar esa etiqueta. |
| fct_feed_run y fct_alert_period | Intento de captura por feed; aviso versionado por periodo con puente a afectados | Identificar huecos, medir retraso de ingestión y saber qué aviso se conocía a qué hora. |
| mart_line_day y mart_station_hour | Línea-día y estación-franja; numeradores y denominadores almacenados | API, Explore y Power BI sobre las mismas definiciones. Publicar nivel de cobertura y número de viajes. |

**Definición inicial de puntualidad.** El gold existente usa el último delay reportado del viaje y considera puntual `abs(delay_seconds) <= 300`. Su denominador cubierto se limita a viajes programados con dato. Rotularlo como «puntualidad según último retraso publicado»; no asegurar que es la llegada final. El agregado actual opera por route_id. Para una línea comercial, sumar numeradores y denominadores de sus variantes tras garantizar una asignación única de cada viaje.

- Cobertura del retraso = viajes programados con retraso válido / viajes programados elegibles.
- Puntualidad entre cubiertos = viajes cubiertos dentro del umbral / viajes cubiertos.
- Cobertura del cruce estático = observaciones madrileñas con trip resuelto / observaciones madrileñas recibidas en el corte. Mostrar también por línea cuando se conozca de forma independiente; declarar el grupo de línea desconocida.
- Si el denominador vale cero, devolver null y mostrar «sin muestra». Ejemplo: 80 programados, 60 cubiertos, 45 puntuales → 75 % de cobertura y 75 % de puntualidad entre cubiertos. Los 20 restantes quedan como desconocidos.
- En Power BI las medidas agregadas dividen `SUM(numerador)` entre `SUM(denominador)`. En SQL publicar columnas de conteo y la misma convención de porcentajes. Evitar promediar los porcentajes diarios.
- Si se añaden viajeros oficiales, usar otra tabla de hechos con su fuente, unidad y periodo. Contar posiciones o circulaciones no permite inferir viajeros.

## Orquestación y acceso

1. **Captura continua.** Un supervisor mantiene el colector. Registrar fuente, instante recibido, HTTP, bytes y SHA-256. Conservar bytes crudos comprimidos en objetos inmutables y un manifiesto por sondeo, incluso si el contenido ya se había visto. Activar la lectura de una nueva versión estática solo después de validar catálogo y geometría.
2. **Cierre diario y llegadas tardías.** Programar un trabajo después del cierre del día de servicio. Exportar a un prefijo temporal por ejecución, comprobar filas, hashes y relaciones, y publicar el manifiesto de esa versión. Aceptar un parámetro service_date para backfill. Exclusión mutua por partición y reintento idempotente. Reabrir días con correcciones y dejar trazabilidad.
3. **dbt.** Proponer un ADR que sustituya el alcance de ADR-0013 cuando la red completa multiplique los marts. Una primera migración pequeña: Python mantiene la resolución ferroviaria; exporta trips resueltos y calendarios. dbt-duckdb lee Parquet, modela stg → int → mart y ejecuta `dbt build`. Comparar diariamente conteos, cobertura y retraso con el gold vigente antes del cambio de consumidor. Preservar el resultado, logs y manifiesto de cada ejecución. Un cron supervisado basta de entrada; introducir Dagster si se necesitan dependencias, backfills y observabilidad que ya cueste operar manualmente.
4. **SQL común y semántica.** Una vista versionada por caso de uso, nombres y tipos estables, timestamps UTC, fecha de servicio explícita, unidades en el nombre y consultas parametrizadas. Tests de unicidad, relaciones y conteos. La ficha de cada métrica identifica grano, fuente, ventana, exclusiones, numerador, denominador y versión de regla. API y Power BI comparten el mart publicado.
5. **Roles.** process_collector escribe ingesta; process_transform lee origen y escribe marts; api_reader consulta vistas publicables; analyst_reader lee marts documentados. Cuenta de migraciones separada. Aplicar grants mínimos en Postgres y acceso por prefijo en objetos. Mantener Live público. Usar identidad OIDC para favoritos sincronizados o consultas guardadas cuando esas funciones existan; ligar los registros privados al usuario autenticado. Aislar el SQL Lab con permisos de solo lectura, límite de coste/tiempo y separación respecto a la base que sirve el mapa.
6. **Retención y coste.** Conservar indefinidamente snapshots lógicos, estáticos versionados y agregados. Deduplicar contenido por hash y compactar particiones pequeñas en frío. Como referencia de dimensionado, a 30 s son hasta 2.880 ciclos diarios y 8.640 respuestas entre tres feeds; la cadencia real incluye tiempos de descarga. Medir durante una semana bytes originales/comprimidos, objetos, lecturas, almacenamiento caliente y transferencia. Proyectar coste mensual con esas medidas y el precio de la región elegida antes de tocar retención. Probar restauración de un día desde el manifiesto.

**Primera demo analítica:** elegir una C5, reconstruir los puntos publicados y las predicciones conocidas en cada instante, mostrar cuándo cambió el retraso y reproducir la cifra de puntualidad de ese día desde una consulta documentada. Esa demo verifica el archivo, los contratos, la capa semántica y el frontend sobre la misma circulación.
