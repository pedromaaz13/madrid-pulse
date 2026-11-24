# Madrid Pulse · Auditoría del directo
20 de noviembre de 2026. Base de revisión: [main, 990c95d](https://github.com/pedromaaz13/madrid-pulse/tree/990c95dfa58cabcf664b905318a4a84fe1cecf19). El código incluye MP-015 y el PR #2 fusionado. El párrafo «Estado actual» del README raíz todavía describe MP-001. El Hito 3 figura como propuesta en docs/HITO_3_BACKLOG.md.

## Dos capturas de Renfe y un cruce reproducible

Descargué los tres JSON oficiales y el ZIP de horarios empleado por el propio repositorio. Las horas de esta tabla son de Madrid, según la cabecera del productor. Los contadores nacionales son entidades del JSON, antes del filtro por núcleo.

| Feed | Primera captura | Segunda captura | Resultado en el parser de main |
|---|---:|---:|---|
| Posiciones | 15:32:04 · 463 | 15:33:21 · 468 | Leídas |
| Actualizaciones de viaje | 15:32:04 · 469 | 15:33:21 · 474 | Cada documento falla entero con 49 errores de validación |
| Avisos | 15:32:09 · 72 | 15:33:26 · 73 | Leídos. El filtro de Madrid pierde avisos por estación |

Las seis respuestas fueron HTTP 200. Entre las dos muestras había 118 identificadores de vehículo madrileños en común. Cambiaron las coordenadas de 35. Un tren parado también puede enviar observaciones recientes. Dos capturas demuestran actividad en esa ventana, no disponibilidad durante el día completo.

En la primera captura había 119 identificadores distintos de vehículo del núcleo 10. Los 119 traían coordenadas y un timestamp 10 segundos anterior a la fecha HTTP de la respuesta. Crucé su tripId con trips.txt y luego su route_id con routes.txt. Resultado: 119 coincidencias con el ZIP oficial, **cero** con la fixture de 15 viajes. La configuración actual de la API con el ZIP completo sigue filtrando por C5. Pasando la captura por la capa real de servicio y su geometría OSM, devolvió 28 posiciones observadas C5 y 91 vehículos sin posición calculada. La cobertura del 100 % es específica de estas muestras. Los 119 tenían también una actualización de viaje con delay en el JSON crudo, aunque el parser actual rechaza ese JSON.

| Línea según el GTFS completo | C1 | C2 | C3 | C4 | C4a | C4b | C5 | C7 | C8a | C8b | C9 | C10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vehículos del corte | 8 | 17 | 13 | 0 | 10 | 11 | 28 | 10 | 5 | 5 | 1 | 11 |

El catálogo estático incluía 42 route_id repartidos entre esos 12 nombres y 36.097 trip_id madrileños distintos a lo largo de su calendario. Una fila C9 en el feed identifica un servicio publicado bajo esa línea. El tipo de prestación o una sustitución por autobús requieren consultar sus avisos. El reparto anterior mide coincidencia con catálogo, no cuántos trenes programados operaban ni cuántos iban en hora.

El paquete de reproducción contiene las seis respuestas tal como llegaron, el horario usado, sus SHA-256, el parche y una sonda ejecutable sin conexión. Origen de los datos: Renfe Operadora, [Renfe Data](https://data.renfe.com/), [posiciones de Cercanías](https://data.renfe.com/dataset/ubicacion-vehiculos). Para el criterio GTFS, véanse [referencia de tiempo real](https://gtfs.org/documentation/realtime/reference/) y [recomendaciones de frescura](https://gtfs.org/documentation/realtime/realtime-best-practices/).

## Fallos y correcciones

| Prioridad | Evidencia en main | Efecto y acción |
|---|---|---|
| P0 · Ingesta de retrasos | packages/contracts/raw.py, RawStopTimeUpdate.arrival obligatorio. Renfe envió 7 paradas SKIPPED en 5123V77736R4 y 21 en cada uno de 1023V20842C5 y 1023V20849C5, todas sin arrival | El parseo nacional falla antes de filtrar Madrid. La validación además quedaba fuera del bloque que registra fallos en source_ingestion_run. El parche admite la parada omitida, evita seleccionarla como siguiente parada comercial y registra fallo de descarga o validación con el hash disponible. |
| P0 · Edad de la fuente | apps/api/service.py, feed_health, usa latest.started_at tanto para source_timestamp como para data_age_s. El colector ya guarda la cabecera verdadera | Una descarga reciente de un fichero viejo puede indicar ok. El parche lee source_timestamp y comprueba también la edad del sondeo. App.tsx cambia el rótulo de la hora del navegador a «Consulta». La frescura por vehículo sigue dependiendo de observed_at. |
| P0 · Modo local y catálogo | apps/api/config.py y gtfs_source.py cargan una fixture y una única línea/corredor por defecto. Vite solo redirige /api a localhost:8000 | Separar modos live y replay. En live fallar al inicio con un diagnóstico útil si se seleccionó una fixture o un GTFS vencido. Publicar versión y vigencia del ZIP. Descargarlo sin cambiar MADRID_PULSE_GTFS_SOURCE deja activa la fixture. |
| P1 · Trenes históricos en Live | apps/api/db.py, latest_vehicle_histories, recupera toda la tabla y obtiene los dos últimos registros de cada vehículo en Python. latest_trip_update busca por trip_id sin fecha ni límite de antigüedad; service.list_vehicles añade una consulta por vehículo | Una corrida anterior puede contar como activa o prestar su retraso a otra jornada. Materializar estado de la última instantánea válida, con última recepción de cada entidad y periodo de gracia. Preservar ausencias como dato de calidad. Unir retrasos por viaje, día de servicio, versión y vigencia. Mantener histórico aparte. |
| P1 · Cambio de viaje | La anterior se selecciona por vehículo. MovementEngine.position lanza ValueError si previous pertenece a otro viaje y _movement_position devuelve None | Al cambiar de servicio, la primera lectura válida puede perder posición. Seleccionar la observación anterior por instancia de viaje o pasar previous=None en el cambio. Añadir caso de regresión con el mismo vehículo en dos viajes. |
| P1 · Avisos de estación | RawInformedEntity solo conserva routeId. _persist_alerts requiere prefijo de ruta de Madrid. En la primera muestra solo sobreviven 4 avisos por ese criterio nacional | Renfe publicó AVISO_527127 para stopId 60104 (Valdemoro) e INFO_527405 para 60103 (Pinto). Conservar todos los selectores y resolver stopId con un índice de estaciones del núcleo. Mantener el aviso una vez aunque afecte a varias líneas. |
| P1 · Cobertura y trayectoria | El cargador construye un MovementEngine con un Corridor. El motor exige un segmento continuo. La API proyecta todas las estaciones de la topología sobre ese único corredor | Quitar el filtro C5 sin sustituir esa estructura dibujaría recorridos incorrectos. Indexar por patrón ordenado de paradas, sentido, variante, versión de red y, cuando exista, shape_id. Validar distancias, huecos y tramos compartidos antes de habilitar movimiento. |
| P1 · Reloj del mapa | App.tsx consulta cada 20 s; fetchDashboard espera líneas, salud y vehículos juntos. MapView.tsx elimina y crea todos los marcadores DOM; el botón del marcador solo tiene título. La cámara puede volver a encuadrar tras «Centrar» al recibir un nuevo objeto line | Separar geometría versionada de posiciones. Conservar selección y cámara, actualizar símbolos por ID y dar al mapa información de avance sobre vía. Actualizar la antigüedad en el cliente incluso si falla el siguiente poll. |
| P2 · Qué significa «programado» | El motor ofrece scheduled, pero list_vehicles parte de vehículos ya observados. _service_date usa la fecha civil actual de Madrid | Para mostrar salidas sin GPS, partir del horario activo. Resolver el día anterior para servicios 24:xx y probar medianoche, cambios de hora y cancelaciones. Separar horario, estimación y observación en API y UI. |

También reproduje un problema de zona horaria. Con PostgreSQL en Europe/Madrid, psycopg devuelve el mismo instante con offset +01:00 en noviembre. El lector de main lo pasa al modelo canónico, que exige offset cero, y la petición de vehículos falla con ValidationError. El parche convierte los timestamps de PostgreSQL a UTC en el límite de lectura de API y calidad. Para diagnosticar el entorno local, ejecutar `SHOW TIME ZONE` en una sesión con la misma configuración del proceso. Este fallo da error de lectura; la presencia de un listado antiguo por sí sola no lo demuestra.

El tipo observed actual es una observación reciente proyectada sobre vía. Guardar el punto bruto y el proyectado permite explicar correcciones. Si el motor cae sobre una muestra anterior plausible, devolver el timestamp de la posición mostrada además del de la observación más reciente. El contrato actual de posición solo devuelve latitud, longitud, modo y confianza.

## Cómo aislar un localhost antiguo

Desde la raíz, con Python 3.12 y Node compatibles con el repositorio. Los comandos de servicio usan la configuración local del proyecto. Para una instalación existente, conservar su volumen y su DSN.

1. Arrancar la base y comprobar el esquema. En una base nueva, aplicar la migración inicial una vez según infra/migrations/README.md.
2. Preparar el entorno una vez con los siguientes comandos.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
.venv/bin/python -m apps.api.tools.fetch_gtfs_static
```

3. Ejecutar en **terminales independientes** desde la raíz.

| Terminal | Comando |
|---|---|
| Colector continuo | `.venv/bin/python -m services.collector` |
| API con catálogo completo C5 | `MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" .venv/bin/uvicorn apps.api.main:app --port 8000` |
| Web | `cd apps/web && npm ci && npm run dev` |

Si personalizas la conexión, el proceso del colector lee MADRID_PULSE_DATABASE_URL. La API lee MADRID_PULSE_DATABASE_DSN. Ambos deben apuntar a la misma base. Reiniciar la API tras cambiar el catálogo, que se carga una vez al inicio. El Compose actual solo levanta PostgreSQL/PostGIS. El snapshotter exporta un día y termina. La ingesta funciona aunque no haya un navegador abierto.

4. Dentro de la base ejecutar esta consulta dos veces con más de un ciclo de separación. El intervalo por defecto del colector es una pausa de 30 s **después** de consultar secuencialmente los tres feeds. Un timeout con reintentos lo alarga.

```sql
SELECT DISTINCT ON (feed_name)
       feed_name, status, entity_count, started_at, source_timestamp,
       now() - started_at AS desde_sondeo,
       now() - source_timestamp AS edad_cabecera
FROM source_ingestion_run
ORDER BY feed_name, started_at DESC, id DESC;
```

5. Comparar la cabecera con la última observación de vehículo y la recepción. Para verificar que Vite llega a la misma API, consultar /api/v1/health tanto en el puerto 8000 como a través del puerto que imprima Vite.

```sql
SELECT observed_at, received_at, source_vehicle_id, source_trip_id,
       now() - observed_at AS edad_posicion
FROM vehicle_position_observation
ORDER BY observed_at DESC, id DESC
LIMIT 5;
```

Si no avanza started_at en ningún feed, mirar el proceso, las dos variables de conexión y sus logs. Si avanza started_at pero no source_timestamp, comparar el JSON de Renfe y el hash de respuesta. Si avanzan posiciones pero faltan ciclos de trip_updates, buscar el fallo de validación. Si las horas son actuales y faltan líneas, revisar el catálogo y los corredores. Si solo una pestaña envejece, mirar el proxy, el último error HTTP y el reloj del cliente. Consultar el estado de una base local existente es una prueba distinta de reproducir estos fallos sobre main.

## Reproducción completa con base de datos

Monté dos bases nuevas con PostgreSQL 17.11 y PostGIS 3.6.0, apliqué la migración inicial e inyecté los bytes originales en el colector usando el reloj del corte. Consulté los endpoints FastAPI a través del cliente HTTP de pruebas. Se usó el ZIP completo con filtro C5. En la comparación, main se ejecutó con sesión UTC, después de reproducir por separado el error de zona horaria; el parche también funcionó con sesión Europe/Madrid. El Compose del repo especifica PostGIS 3.5. Las pruebas no accedieron al localhost del propietario.

| Resultado en el primer corte | main | Con el parche |
|---|---:|---:|
| Vehículos de Madrid ofrecidos por la API | 119 | 119 |
| Posiciones observadas en el corredor C5 | 28 | 28 |
| Vehículos con retraso reportado | 0 | 119 |
| Feeds enumerados por health en esta base limpia | 2 | 3 |
| Edad indicada para posiciones a las 15:32:14 | 0 s | 10 s |
| Edad indicada para avisos a las 15:32:14 | 0 s | 5 s |

El colector corregido insertó 122 actualizaciones distintas de Madrid en el primer corte. En el segundo insertó 77 y deduplicó 47. Coincidieron con el GTFS los 121 vehículos madrileños del segundo corte. Los números del soak antiguo (24 vehículos, 4 de C5) pertenecen a la documentación previa del repo y no sirven como expectativa de tráfico en vivo.

## Alcance del parche

Aplicar en un worktree basado en el commit auditado con `git apply --check /ruta/madrid-pulse-live.patch` y luego `git apply /ruta/madrid-pulse-live.patch`. Reiniciar el colector y la API. El parche conserva los endpoints actuales. Las tareas P1/P2 de la tabla y la flota de toda la red quedan en el plan de implementación.

Validación inicial: 53 tests de contratos/geometría/movimiento y fixtures en main. En el frontend de main pasaron 5 tests, lint, typecheck y build con verificación del worker de MapLibre. Sobre el parche se ejecutaron los 118 casos del listado de módulos de CI: 113 pasaron y 5 se omitieron por depender de la base histórica exacta del soak de MP-007. Los seis JSON completos atravesaron parser y normalización. Las capturas contienen 469 y 474 actualizaciones que ahora se leen. La sonda incluida se ejecuta con `python replay/comprobar.py` tras descomprimir el paquete. Verifica primero el checksum de cada fichero y repite los cruces sobre los datos congelados.
