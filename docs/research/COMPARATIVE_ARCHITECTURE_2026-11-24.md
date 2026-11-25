<!-- FUENTE IMPORTADA ÍNTEGRA — no editar el cuerpo. Solo esta cabecera es de gobernanza. -->
> **Nota de incorporación (2026-11-25).** Documento fuente recibido del propietario e incorporado sin alterar su contenido (todo lo que sigue a la primera línea `---` es el original byte a byte).
> - **Estatus:** INVESTIGACIÓN (2026-11-24): hechos de repositorios ajenos verificados a los commits citados; el resto son hipótesis o propuestas
> - **Fuente:** `COMPARATIVE_ARCHITECTURE_2026-11-24.md` (paquete `MADRID_PULSE_ORCA_GOBERNANZA_MVP_LIVE_DESIGN`)
> - **SHA-256 del original:** `adb830489832626e7cea7ff5b2d4c1076093b2c18cf2ae729825bb52794fbfaf`
> - **Alcance:** comparativa Madrid Pulse @ 7583ca5 / Vía Península @ 66d468a (AGPL-3.0) / Electricity Maps @ 3a17f6c (AGPL-3.0); solo estudio conceptual, sin copia de código
> - **Regla:** importar este documento **no** convierte sus recomendaciones en decisiones aprobadas. Las decisiones viven en `docs/DECISIONS.md` y `docs/adr/`; el estado vigente, en `docs/STATUS.md` y `docs/governance/PROJECT_STATE.json` (si el cuerpo menciona PROJECT_STATE.yaml, el fichero real es el .json).
> - **Privacidad:** el cuerpo conserva por integridad la formulación original, incluida alguna ruta absoluta local; excepción **aceptada por el propietario (2026-11-25)**: el original se conserva sin modificar y la ruta no es operativa (ver el override).

---
# **Madrid Pulse — Deep Research: arquitectura end-to-end, ingeniería de datos y estrategia de producto**

**Auditoría comparativa · 24 de noviembre de 2026**

En esta segunda investigación quiero ir bastante más allá de comparar frameworks. Vamos a analizar cómo se transforma un dato publicado por Renfe en un tren que se mueve sobre un mapa, cómo se conserva ese dato, cómo se convierte en información analítica y cómo se mantiene toda esa infraestructura funcionando en producción.

La pregunta central es si estamos construyendo correctamente un producto de movilidad o si estamos acumulando componentes técnicos que no terminan de traducirse en una buena experiencia de usuario.

No tengo acceso a un modo independiente de Deep Research desde esta sesión, pero sí puedo realizar una investigación técnica ampliada utilizando el conector de GitHub, inspección de código fuente, documentación arquitectónica y fuentes técnicas externas.

## **1. Alcance y metodología**

He recuperado los árboles completos de archivos de los tres repositorios principales, fijando las referencias de código para evitar comparar versiones distintas durante el análisis.

| Proyecto                                                                                                                                            | Commit de referencia | Archivos en el árbol |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | -------------------- |
| [Madrid Pulse](https://github.com/pedromaaz13/madrid-pulse/tree/7583ca5f4450aa70e5b6b05b7394aef4cc28f3a4?utm_source=chatgpt.com)                    | `7583ca5`            | 399                  |
| [Vía Península](https://github.com/gariasf/viapeninsula/tree/66d468a4f170a3245ea637956fefa1b216afaf32?utm_source=chatgpt.com)                       | `66d468a`            | 373                  |
| [Electricity Maps](https://github.com/electricitymaps/electricitymaps-contrib/tree/3a17f6c468bff85c7909bd17e42bf5521886547f?utm_source=chatgpt.com) | `3a17f6c`            | 1.730                |

Los recuentos incluyen documentación, código, configuraciones, pruebas y fixtures. No son una medida de complejidad ni de calidad del software.

El análisis abarcará las siguientes capas:

01

**Data sources**

GTFS, GTFS-Realtime, OpenStreetMap y contratos externos

02

**Data ingestion**

Polling, adaptadores, resiliencia e idempotencia

03

**Data platform**

Persistencia, modelado, calidad e histórico

04

**Geospatial processing**

Grafo ferroviario, rutas, estaciones y map-matching

05

**Real-time movement engine**

Tiempo, posiciones, paradas e interpolación

06

**Data serving & API**

Snapshots, REST, caché, distribución y escalabilidad

07

**Frontend & rendering**

MapLibre, React, WebGL, fotogramas y experiencia visual

08

**Analytics**

History, Explore, métricas y explotación histórica

09

**Platform engineering**

Infraestructura, despliegue, CI/CD y observabilidad

10

**Product architecture**

Decisiones, costes, roadmap y estrategia de implementación

Un principio importante: distinguiré los hechos observados directamente en código, los resultados reportados por la auditoría de H3 y las recomendaciones arquitectónicas que todavía requieren validación experimental.

## **2. Data sources: qué información tenemos realmente**

El primer error conceptual que debemos evitar es pensar que Renfe proporciona un flujo continuo de coordenadas GPS. La fuente entrega observaciones discretas y, en algunos casos, incompletas.

### **2.1. GTFS estático frente a GTFS-Realtime**

**GTFS Static**

Lo que debería ocurrir

`routes.txt` — Líneas

`trips.txt` — Viajes

`stops.txt` — Estaciones

`stop_times.txt` — Horarios

`calendar.txt` — Servicios

`calendar_dates.txt` — Excepciones

`shapes.txt` — Geometrías

**GTFS-Realtime**

Lo que reporta el operador

`VehiclePositions` — Posiciones

`TripUpdates` — Actualizaciones del viaje

`Alerts` — Incidencias

`timestamp` — Tiempo de observación

`current_status` — Estado

`current_stop_id` — Parada asociada

La tercera fuente necesaria es OpenStreetMap, que permite construir una representación geográfica de las vías cuando las geometrías GTFS no son suficientemente detalladas.

Estas fuentes desempeñan responsabilidades diferentes:

| Fuente  | Responsabilidad            | Limitación                                                 |
| ------- | -------------------------- | ---------------------------------------------------------- |
| GTFS    | Servicio planificado       | No confirma que un tren esté circulando                    |
| GTFS-RT | Observaciones del operador | Puede tener retrasos, errores y discontinuidades           |
| OSM     | Infraestructura física     | No determina por sí sola qué itinerario utiliza cada viaje |

### **2.2. Madrid Pulse**

He inspeccionado directamente `services/collector/config.py`. Estos son los tres feeds configurados:

- [vehicle_positions.json](https://gtfsrt.renfe.com/vehicle_positions.json?utm_source=chatgpt.com)
- [trip_updates.json](https://gtfsrt.renfe.com/trip_updates.json?utm_source=chatgpt.com)
- [alerts.json](https://gtfsrt.renfe.com/alerts.json?utm_source=chatgpt.com)

La configuración actual establece:

| Parámetro          | Valor por defecto    |
| ------------------ | -------------------- |
| Polling            | 30 segundos          |
| Timeout            | 10 segundos          |
| Reintentos         | 3                    |
| Base del backoff   | 1 segundo            |
| Núcleo ferroviario | Madrid, prefijo `10` |

El propio código documenta que durante MP-003 se observaron actualizaciones de aproximadamente 20–22 segundos y una cabecera `Cache-Control: max-age=30`.

Por tanto, sondear Renfe cada segundo no tendría sentido en estas condiciones. El navegador puede animar a 60 FPS, pero eso no convierte la frecuencia de adquisición en 60 observaciones por segundo.

Fuente: [CollectorConfig](https://github.com/pedromaaz13/madrid-pulse/blob/main/services/collector/config.py?utm_source=chatgpt.com).

### **2.3. Qué diferencia a Vía Península**

Vía Península trabaja también con datos oficiales, pero plantea desde el principio una arquitectura multioperador. Cada fuente tiene características particulares: formatos, cadencias, información disponible y reglas de interpretación.

Esta capacidad es esencial porque el mismo modelo de movimiento no puede asumir que todos los operadores publican posiciones GPS, predicciones y estados con idéntico significado.

### **2.4. Qué diferencia a Electricity Maps**

Electricity Maps lleva este planteamiento todavía más lejos: adapta fuentes heterogéneas a contratos normalizados de producción, consumo, intercambios y precios energéticos.

Es el equivalente a tener una interfaz de ingesta común y adaptadores especializados para cada operador de transporte.

**Decisión para Madrid Pulse:** mantener Renfe como única fuente ferroviaria operativa del alcance actual, pero evitar que los contratos internos dependan innecesariamente de peculiaridades de Renfe.

No necesitamos implementar Metro, EMT o BiciMAD todavía. Necesitamos que añadirlos en el futuro no obligue a modificar todo el sistema.

## **3. Data ingestion: del feed original a nuestra plataforma**

### **3.1. El pipeline actual de Madrid Pulse**

El collector no es un simple script que descarga un JSON. Ya contiene una cadena de procesamiento bastante sólida.

He inspeccionado:

[collector.py](https://github.com/pedromaaz13/madrid-pulse/blob/main/services/collector/collector.py?utm_source=chatgpt.com) · [db.py](https://github.com/pedromaaz13/madrid-pulse/blob/main/services/collector/db.py?utm_source=chatgpt.com) · [normalize.py](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/contracts/normalize.py?utm_source=chatgpt.com) · [quality/engine.py](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/quality/engine.py?utm_source=chatgpt.com).

**Fetch**

Descarga HTTP del feed con timeout y reintentos

**Parse**

Validación de la estructura raw

**Normalize**

Conversión a entidades canónicas y fechas UTC

**Scope filter**

Selección de entidades del núcleo de Madrid

**Deduplicate**

Comparación del hash con la última entidad persistida

**Quality checks**

Detección de anomalías y problemas de calidad

**Persist**

Escritura transaccional en PostgreSQL

Una característica positiva es que las funciones de normalización son independientes de HTTP y PostgreSQL. Reciben modelos raw y devuelven modelos canónicos.

Eso facilita las pruebas unitarias, la incorporación de nuevas fuentes y el reprocesamiento de observaciones.

### **3.2. Deduplicación: una decisión correcta con limitaciones**

El collector compara el hash canónico de una entidad con el último hash almacenado para esa misma identidad. Si no ha cambiado, evita insertar otra observación idéntica.

Imagina que Renfe publica la misma posición de un tren en tres sondeos consecutivos:

| 10:00:00 | Tren A · Posición X | INSERT    |
| -------- | ------------------- | --------- |
| 10:00:30 | Tren A · Posición X | Duplicado |
| 10:01:00 | Tren A · Posición X | Duplicado |
| 10:01:30 | Tren A · Posición Y | INSERT    |

Ejemplo simplificado: presupone que el contenido canónico completo es idéntico, no solamente las coordenadas.

Esto reduce almacenamiento, pero hay que conservar la diferencia entre:

- El momento en que cambió una observación.
- El momento en que volvimos a recibirla.
- El momento en que comprobamos que la fuente seguía funcionando.

Un feed puede estar operativo mientras mantiene un vehículo inmóvil. Si solamente utilizamos la última observación deduplicada para medir frescura, podríamos confundir una posición repetida con una caída del servicio.

Madrid Pulse ya registra ejecuciones de ingesta separadamente. Mantendría esa decisión y evaluaría si necesitamos también metadatos por entidad, como `last_seen_at`, para los casos donde la recepción repetida sea operacionalmente relevante.

### **3.3. Transacciones e idempotencia**

El código de acceso a PostgreSQL documenta un fallo anterior especialmente instructivo: algunas operaciones utilizaban transacciones anidadas que se convertían en savepoints, dejando observaciones sin confirmar.

La solución fue centralizar el límite transaccional de cada ciclo de ingesta.

Esto demuestra que existe trabajo real de ingeniería detrás del proyecto. Sin embargo, todavía debemos comprobar escenarios de:

- Dos collectors ejecutándose accidentalmente.
- Reinicio durante la escritura.
- Reintentos después de una pérdida de conexión.
- Recepción de observaciones desordenadas.
- Cambios de identidad entre viajes.

La deduplicación por comparación de hash no sustituye por sí sola un mecanismo completo de exclusión mutua o idempotencia concurrente.

### **3.4. Quality Engine**

Los umbrales por defecto encontrados en el código son:

| Regla                 | Umbral inicial        |
| --------------------- | --------------------- |
| Observación obsoleta  | 180 s                 |
| Velocidad implausible | 200 km/h              |
| Snapshot repetido     | 180 s                 |
| Desviación temporal   | 300 s                 |
| Identificador ausente | Validación específica |

El propio código especifica que estos valores son calibrables.

Esto está bien diseñado como capa técnica, pero no debemos confundir calidad de observación con calidad del producto. Un GPS puede pasar todas estas validaciones y aun así producir una animación incorrecta si el motor interpreta mal una parada.

**Mantendría el Quality Engine, ampliándolo con reglas específicas del dominio ferroviario y métricas de comportamiento por fuente.**

### **3.5. Vía Península: un modelo de adaptadores más maduro**

He revisado directamente sus archivos [`src/fetcher/step.ts`](https://github.com/gariasf/viapeninsula/blob/main/src/fetcher/step.ts?utm_source=chatgpt.com) y [`src/fetcher/worker.ts`](https://github.com/gariasf/viapeninsula/blob/main/src/fetcher/worker.ts?utm_source=chatgpt.com).

Son especialmente interesantes porque separan tres responsabilidades:

| Componente    | Responsabilidad                                             |
| ------------- | ----------------------------------------------------------- |
| `worker.ts`   | Ejecución periódica, persistencia del estado y publicación  |
| `step.ts`     | Procesamiento, adaptadores, estado de fuentes y snapshots   |
| `networks.ts` | Configuración de operadores y comportamiento de sus fuentes |

`step.ts` contiene adaptadores para Renfe, FGC, TRAM, Metro y fuentes genéricas GTFS-RT, incluyendo formatos JSON y Protocol Buffers.

El worker es relativamente pequeño, mientras que la lógica de interpretación de datos permanece separada y puede probarse utilizando respuestas grabadas.

Hay mecanismos particularmente interesantes:

- Conservación del último dato válido cuando falla una fuente.
- Detección de redes que desaparecen temporalmente de un feed que sigue operativo.
- Cadencias independientes por fuente.
- Seguimiento de credenciales y cuotas cuando corresponda.
- Tratamiento específico de estaciones omitidas y viajes cancelados.
- Persistencia del estado entre ejecuciones del Durable Object.

Madrid Pulse ya dispone de una parte importante de estos fundamentos, pero todavía orientada a un solo operador.

### **3.6. Decisión: ¿deberíamos migrar el collector a Cloudflare Workers?**

No lo haría.

Vía Península utiliza Cloudflare Workers porque su collector tiene como objetivo principal producir snapshots compactos para el navegador. Madrid Pulse necesita persistencia histórica, PostgreSQL, procesos Python y explotación analítica.

La arquitectura de ejecución de Vía Península encaja con su producto. No demuestra que nuestro collector deba adoptar el mismo runtime.

Lo que sí adoptaría son sus **patrones de resiliencia, configuración de fuentes y separación de responsabilidades**.

## **4. Data platform: PostgreSQL, PostGIS y arquitectura histórica**

Esta es probablemente la capa donde Madrid Pulse tiene una ambición mayor que Vía Península.

### **4.1. Modelo relacional existente**

He revisado la migración [`0001_init.up.sql`](https://github.com/pedromaaz13/madrid-pulse/blob/main/infra/migrations/0001_init.up.sql?utm_source=chatgpt.com). El esquema define catorce tablas, además de índices temporales, de identidad y espaciales.

### **Modelo lógico simplificado de Madrid Pulse**

Representación conceptual de entidades y asociaciones. No es un DER físico completo ni implica que todos los vínculos dibujados sean claves foráneas declaradas.

Las entidades físicas adicionales incluyen alertas de servicio y agregados diarios por línea y estación.

Este modelo permite hacer preguntas que un simple snapshot de trenes no puede responder eficientemente:

- ¿Cuántos viajes programados observamos realmente?
- ¿Cuánto tiempo permaneció detenido un tren?
- ¿Qué estaciones acumulan mayores retrasos?
- ¿Qué porcentaje de la red tiene posiciones válidas?
- ¿En qué momentos del día empeora la calidad de la fuente?

Aquí empieza la diferencia entre un **mapa de movilidad** y una **plataforma de datos de movilidad**.

### **4.2. ¿PostGIS está justificado?**

Sí, aunque debemos distinguir lo que permite la tecnología de lo que actualmente se está ejecutando dentro de ella.

La migración confirma columnas geográficas e índices GiST. Sin embargo, una parte significativa de la geometría y del motor ferroviario se procesa en Python, utilizando las estructuras cargadas por la aplicación.

No debemos afirmar que todo el motor espacial funciona mediante consultas SQL PostGIS.

| Operación                                        | Tecnología apropiada    |
| ------------------------------------------------ | ----------------------- |
| Consultar estaciones próximas                    | PostGIS                 |
| Cruces con áreas municipales                     | PostGIS                 |
| Persistir puntos y geometrías                    | PostGIS                 |
| Reconstruir una trayectoria ferroviaria compleja | Python + grafo          |
| Calcular un fotograma del tren                   | TypeScript en navegador |
| Analizar millones de observaciones históricas    | DuckDB + Parquet        |

Esta distribución tiene sentido. No hay razón para obligar a una única tecnología a resolver todos los problemas.

### **4.3. Arquitectura hot/cold**

La separación del almacenamiento es una de las decisiones más acertadas del proyecto.

**Ingesta continua**

Observaciones originales normalizadas

**Hot storage — PostgreSQL**

Estado operativo y observaciones recientes

**Cold storage — Parquet**

Histórico particionado, comprimido con ZSTD

**Analytical layer — DuckDB**

Transformaciones, agregados y consultas históricas

He comprobado en [`services/snapshotter/export.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/services/snapshotter/export.py?utm_source=chatgpt.com) que:

- DuckDB lee directamente PostgreSQL mediante su extensión correspondiente.
- Escribe Parquet con compresión ZSTD.
- Utiliza particiones temporales por fecha y hora.
- Contempla recuperación de sustituciones de particiones interrumpidas.
- Convierte timestamps a `Europe/Madrid` para delimitar las particiones diarias.

Hay un matiz que deberíamos revisar en futuras pruebas: el día civil local y el día de servicio GTFS no son necesariamente equivalentes, especialmente para viajes que continúan después de medianoche.

### **4.4. Bronze, Silver y Gold**

Madrid Pulse está evolucionando hacia una arquitectura medallion, aunque no debe confundirse el diseño conceptual con tres plataformas físicas independientes.

| Capa lógica  | Datos                                                                   |
| ------------ | ----------------------------------------------------------------------- |
| Bronze / raw | Observaciones de origen, ejecuciones de ingesta, alertas y trazabilidad |
| Silver       | Identidades resueltas, circulaciones, fechas de servicio y calidad      |
| Gold         | Métricas diarias, agregaciones por línea, estación y núcleo             |

Hay una mejora importante pendiente de evaluar: conservar también los payloads originales completos cuando exista una necesidad de auditoría o reprocesamiento. Un hash del feed permite verificar identidad, pero no reconstruir un documento que no se ha guardado.

### **4.5. ¿Necesitamos dbt?**

Por ahora, no necesariamente.

El repositorio calcula agregaciones con Python y SQL de DuckDB. En [`gold.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/services/snapshotter/gold.py?utm_source=chatgpt.com) ya existen procesos de agregación por núcleo, línea y estación.

Además, se han corregido dos problemas reales:

- Aplicación de las excepciones de `calendar_dates.txt` al denominador de servicios programados.
- Orden explícito de resultados para obtener exportaciones reproducibles.

Yo introduciría dbt cuando haya suficientes modelos, dependencias, métricas compartidas y necesidades de lineage como para justificar su mantenimiento.

No añadiría dbt simplemente para que el proyecto tenga un stack más atractivo en LinkedIn.

## **5. Geospatial engineering: el mayor diferencial técnico de Vía Península**

Esta es una de las conclusiones más importantes de toda la investigación. **Madrid Pulse y Vía Península no construyen actualmente la geometría ferroviaria siguiendo el mismo procedimiento.**

### **5.1. Madrid Pulse: reconstrucción basada en relaciones OSM**

En [`packages/geo/corridor.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/geo/corridor.py?utm_source=chatgpt.com), nuestro algoritmo encadena los segmentos de vía contenidos en una relación OSM utilizando los nodos que comparten sus extremos.

Cuando dos segmentos no encajan, registra un `ChainGap`. No inventa una conexión entre ambos.

En [`packages/geo/madrid.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/geo/madrid.py?utm_source=chatgpt.com), se declaran explícitamente las fuentes geográficas verificadas, sus hashes, las fechas de captura y los identificadores de ruta que pueden utilizarlas.

El resultado es un enfoque conservador y bastante seguro:

El enfoque actual evita fabricar vías inexistentes, pero depende de disponer de relaciones adecuadas y suficientemente completas.

Es una solución válida para comenzar con C5 y ampliar posteriormente a algunos corredores. Pero al intentar cubrir una red completa aparecen limitaciones importantes.

### **5.2. Vía Península: reconstrucción mediante grafos ferroviarios**

He inspeccionado [`src/build/track.ts`](https://github.com/gariasf/viapeninsula/blob/main/src/build/track.ts?utm_source=chatgpt.com), que contiene unas 1.300 líneas dedicadas al trazado ferroviario.

Su planteamiento es diferente: construye grafos a partir de las vías de OSM y determina los recorridos que pueden utilizar los viajes, teniendo en cuenta estaciones, sentidos, características de las vías y configuraciones de red.

Entre las funciones encontradas:

| Función         | Responsabilidad                       |
| --------------- | ------------------------------------- |
| `railGraphs()`  | Construcción de grafos ferroviarios   |
| `traceShapes()` | Trazado a partir de geometrías GTFS   |
| `traceRuns()`   | Resolución de recorridos              |
| `traceRun()`    | Reconstrucción de un itinerario       |
| `walk()`        | Recorrido del grafo entre estaciones  |
| `paths()`       | Búsqueda de caminos candidatos        |
| `railGraph()`   | Construcción de nodos y aristas       |
| `wrongTracks()` | Identificación de vías inadecuadas    |
| `nearest()`     | Proyección sobre la geometría         |
| `turnsBack()`   | Detección de inversiones de recorrido |

El algoritmo incluye costes de paso, restricciones y lógica para seleccionar vías compatibles. Es bastante más sofisticado que concatenar los elementos de una relación OSM.

Esquema conceptual del trazado mediante grafos. Las conexiones grises representan caminos candidatos; la verde, el recorrido compatible con la secuencia de estaciones.

Esto explica en buena medida por qué Vía Península puede ampliar su cobertura a numerosos operadores y redes sin depender exclusivamente de una relación OSM por cada variante de viaje.

### **5.3. Comparación técnica**

| Característica                  | Madrid Pulse                                    | Vía Península                              |
| ------------------------------- | ----------------------------------------------- | ------------------------------------------ |
| Unidad geográfica inicial       | Relación OSM                                    | Grafo de vías                              |
| Resolución de recorridos        | Corredores configurados                         | Trazado sobre caminos candidatos           |
| Ramales                         | Requieren validación y configuración específica | Resueltos mediante trazado y reglas de red |
| Tratamiento de discontinuidades | Conservador, registra gaps                      | Búsqueda de recorridos compatibles         |
| Fuentes geográficas             | Fixtures Overpass                               | Extractos Geofabrik y osmium               |
| Vías compartidas                | Geometrías por corredor/patrón                  | Segmentos físicos y representación lateral |
| Actualización                   | Catálogo basado en fuentes verificadas          | Build automatizado y versionado            |
| Escalabilidad geográfica        | Limitada por trabajo manual actual              | Más industrializada                        |

### **5.4. Mi propuesta: cambiar progresivamente el procedimiento geoespacial**

No eliminaría el código actual de corredores, porque es útil como referencia, fallback y mecanismo de validación.

Pero sí desarrollaría una alternativa basada en grafo ferroviario.

La arquitectura propuesta sería:

```
Geofabrik .osm.pbf
       │
       ▼
Filtrado de infraestructura ferroviaria
       │
       ▼
Grafo físico de nodos y aristas
       │
       ├── GTFS stops
       ├── GTFS shapes
       └── Secuencias de paradas
       │
       ▼
Resolución del recorrido por patrón
       │
       ▼
Validación geométrica
       │
       ▼
Catálogo ferroviario versionado
```

[Geofabrik](https://download.geofabrik.de/europe/spain.html?utm_source=chatgpt.com) distribuye extractos OSM compatibles con herramientas como Osmium, lo que ofrece una alternativa al uso repetitivo de consultas Overpass.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://download.geofabrik.de\&sz=32)

Geofabrik Download Server



### **Tecnologías candidatas**

| Tecnología | Utilización                                     |
| ---------- | ----------------------------------------------- |
| Osmium     | Extracción y filtrado OSM                       |
| Pyosmium   | Procesamiento de datos OSM desde Python         |
| Shapely    | Operaciones geométricas                         |
| PyProj     | Transformaciones de coordenadas                 |
| NetworkX   | Prototipado y validación de grafos              |
| PostGIS    | Persistencia y consultas espaciales             |
| SciPy      | Índices y búsquedas espaciales, si se necesitan |
| pgRouting  | Alternativa a evaluar, no requisito inicial     |

No instalaría todas estas dependencias inmediatamente. Primero realizaría una prueba comparativa sobre tres tipos de recorrido: C5, una línea con ramales y una línea que comparte vías con otras.

El objetivo es comprobar que el enfoque de grafo reduce el trabajo manual y mejora la cobertura sin degradar la precisión.

## **6. Motor de movimiento: cómo conseguimos un tiempo real realmente fluido**

Esta es la capa decisiva del producto.

### **6.1. El algoritmo actual de Madrid Pulse**

He inspeccionado directamente cuatro niveles del código:

| Archivo                                                                                                                                           | Función                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| [`packages/movement/engine.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/movement/engine.py?utm_source=chatgpt.com)         | Estimación y resolución ferroviaria    |
| [`packages/movement/schedule.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/movement/schedule.py?utm_source=chatgpt.com)     | Modelo de horarios                     |
| [`packages/movement/rendering.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/packages/movement/rendering.py?utm_source=chatgpt.com)   | Contrato de movimiento para el cliente |
| [`apps/web/src/domain/movement.ts`](https://github.com/pedromaaz13/madrid-pulse/blob/main/apps/web/src/domain/movement.ts?utm_source=chatgpt.com) | Evaluación visual de la posición       |

Nuestro sistema establece tres coordenadas diferenciadas.

Raw

Dato original del operador

Matched

Proyección sobre vía

Rendered

Posición visual calculada

**Esta separación debe conservarse.** Es una característica valiosa para la integridad de los datos y el análisis histórico.

El problema no es la separación de responsabilidades, sino cómo calculamos la tercera coordenada.

### **6.2. El contrato ProgressEnvelope**

Actualmente, el backend publica una envolvente temporal compacta que contiene:

```
interface ProgressEnvelope {
  reference_at: string;
  progress_m_at_reference: number;
  speed_mps: number;
  max_progress_m: number;
  horizon_s: number;
  dwell_until: string | null;
}
```

En el navegador se aplica una fórmula equivalente a:

\\[ p(t)=\min(p_0+v\max(0,t-t_0),p\_{\max}) \\]

Donde:

- \\(p_0\\) es el progreso inicial sobre la vía.
- \\(v\\) es la velocidad autorizada por el backend.
- \\(t_0\\) es el instante de referencia o fin de espera.
- \\(p\_{\max}\\) es el límite máximo del progreso.

Esto permite animar al tren sin volver a consultar el backend para cada fotograma.

**El defecto estructural es que una envolvente lineal única representa mal un movimiento ferroviario con varios tramos y paradas dentro de su horizonte de validez.**

### **6.3. El fallo de las paradas explicado visualmente**

Ejemplo ilustrativo: una proyección lineal atraviesa una estación durante el periodo en que debería respetar una parada.

Una solución superficial consistiría en reducir el horizonte de 180 segundos o modificar un umbral. No creo que eso resuelva el problema completo.

Necesitamos un modelo que represente explícitamente el estado del tren y las transiciones entre estados.

### **6.4. Vía Península: el horario como fuente del movimiento**

He revisado el archivo [`src/engine.ts`](https://github.com/gariasf/viapeninsula/blob/main/src/engine.ts?utm_source=chatgpt.com). Contiene aproximadamente 1.964 líneas y concentra buena parte de la lógica ferroviaria utilizada por el navegador y por sus pruebas.

Funciones relevantes:

| Función           | Responsabilidad                                     |
| ----------------- | --------------------------------------------------- |
| `trainsAt()`      | Determinar los trenes representables en un instante |
| `trainAt()`       | Calcular la posición de un tren concreto            |
| `boardAt()`       | Construir próximas salidas de una estación          |
| `reportsByTrip()` | Asociar observaciones a viajes                      |
| `delayOf()`       | Estimar desviaciones temporales                     |
| `replay()`        | Aplicar la secuencia de observaciones               |
| `eased()`         | Suavizar correcciones de progreso                   |
| `unheld()`        | Movimiento sin retención                            |
| `place()`         | Calcular posición a partir del horario              |
| `cutTrip()`       | Adaptar recorridos con estaciones omitidas          |
| `nearbyAt()`      | Detectar servicios próximos                         |

El horario define la función base de progreso:

\\[ s(t)=F\_{\text{horario}}(t-\Delta) \\]

Donde \\(\Delta\\) representa una corrección temporal derivada de los datos en directo.

Si existe una observación GPS válida, puede utilizarse para ajustar el desfase temporal del viaje. El modelo sabe que una circulación no avanza necesariamente a velocidad constante durante todo su recorrido.

### **6.5. ¿Debemos copiar su filosofía completa?**

No exactamente.

| Enfoque                          | Ventaja                              | Riesgo                                  |
| -------------------------------- | ------------------------------------ | --------------------------------------- |
| GPS directo                      | Máxima fidelidad al dato publicado   | Movimiento discontinuo                  |
| Extrapolación lineal             | Simple y económica                   | Puede atravesar paradas incorrectamente |
| Horario como autoridad principal | Gran fluidez y cobertura programada  | Puede aparentar actividad no confirmada |
| Modelo híbrido por estados       | Equilibrio entre veracidad y fluidez | Mayor complejidad de diseño             |

Recomiendo el cuarto enfoque para Madrid Pulse.

La razón es que nuestro proyecto tiene una aspiración analítica. No podemos convertir una hipótesis de circulación en una observación real y posteriormente utilizarla para calcular puntualidad o calidad del servicio.

### **6.6. Arquitectura propuesta del motor ferroviario**

La autoridad de movimiento continuaría en Python, mientras que TypeScript se limitaría a evaluar la representación autorizada.

Máquina de estados propuesta y simplificada. La obsolescencia se modelaría preferentemente como un estado de calidad independiente del estado operativo.

Cada estado determinaría qué movimiento puede autorizarse.

| Estado        | Política propuesta                                        |
| ------------- | --------------------------------------------------------- |
| Programado    | No presentar como circulación observada                   |
| En origen     | No salir antes de la ventana autorizada                   |
| En movimiento | Avance acotado según observaciones y horario              |
| En estación   | Respetar permanencia y evidencia de parada                |
| Cancelado     | Excluir de circulación activa                             |
| Obsoleto      | Congelar o pasar a estimación explícitamente diferenciada |
| Finalizado    | Retirar del conjunto activo                               |

En vez de una única velocidad para todo el horizonte, podríamos probar un contrato por segmentos:

```
{
  "movement_version": "2",
  "operational_state": "AT_STATION",
  "position_provenance": "operator_observation",
  "segments": [
    {
      "kind": "hold",
      "from": "10:00:00Z",
      "until": "10:00:40Z",
      "progress_m": 1800
    },
    {
      "kind": "travel",
      "from": "10:00:40Z",
      "until": "10:01:30Z",
      "start_progress_m": 1800,
      "end_progress_m": 2300
    }
  ]
}
```

Es un contrato conceptual, no código ya implementado. El segmento de movimiento solo debería publicarse cuando las reglas ferroviarias y la evidencia permitan autorizarlo; una parada declarada no debe convertirse automáticamente en una salida confirmada.

Este diseño tendría que contrastarse con alternativas menos complejas dentro de H4-00.

### **6.7. Frescura y reconciliación**

No debemos utilizar una única fecha para todos los aspectos de la observación.

| Timestamp               | Significado                           |
| ----------------------- | ------------------------------------- |
| `gps_observed_at`       | Momento de observación de la posición |
| `feed_published_at`     | Publicación del feed                  |
| `received_at`           | Recepción por Madrid Pulse            |
| `snapshot_generated_at` | Generación de la respuesta            |
| `display_at`            | Instante representado                 |
| `valid_until`           | Límite de validez de la estimación    |

El contrato actual ya contiene esta separación. Debemos mantenerla y utilizarla correctamente.

La guía de GTFS-Realtime recomienda refrescos de feed de al menos cada 30 segundos y una antigüedad máxima recomendada de 90 segundos para posiciones y actualizaciones de viajes. También distingue la frescura del feed de la de sus entidades.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://gtfs.org\&sz=32)

General Transit Feed Specification+1



Por tanto, que un snapshot se haya generado hace cinco segundos no significa que sus observaciones GPS tengan cinco segundos.

## **7. API y Data Serving: cómo llega la información hasta el usuario**

Esta es la segunda gran oportunidad de mejora arquitectónica, después del procesamiento geoespacial.

### **7.1. Madrid Pulse ya dispone de una API considerablemente desarrollada**

He contrastado [`apps/api/main.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/apps/api/main.py?utm_source=chatgpt.com), [`snapshot.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/apps/api/snapshot.py?utm_source=chatgpt.com), [`history.py`](https://github.com/pedromaaz13/madrid-pulse/blob/main/apps/api/history.py?utm_source=chatgpt.com) y los resultados de la auditoría AUD-06.

La auditoría reporta 15 endpoints y coherencia entre la especificación OpenAPI almacenada y la generada por FastAPI.

| Familia de endpoints                  | Función                              |
| ------------------------------------- | ------------------------------------ |
| `/api/v1/health`                      | Estado y frescura de las fuentes     |
| `/api/v1/live/vehicles`               | Vehículos en directo                 |
| `/api/v1/live/vehicles/{vehicle_id}`  | Detalle de vehículo                  |
| `/api/v1/lines`                       | Líneas                               |
| `/api/v1/lines/{line_id}`             | Detalle de línea                     |
| `/api/v1/stations`                    | Estaciones                           |
| `/api/v1/stations/{station_id}`       | Detalle de estación                  |
| `/api/v1/catalog`                     | Catálogo completo versionado         |
| `/api/v1/snapshot`                    | Estado operativo                     |
| `/api/v1/stations/{station_id}/board` | Tablero de próximas circulaciones    |
| `/api/v1/history/*`                   | Cinco recursos de consulta histórica |

Esto es una base interesante para desarrollar otros clientes en el futuro: una aplicación móvil, un dashboard especializado o integraciones de terceros.

### **7.2. Cómo se genera actualmente un snapshot**

El procedimiento encontrado en `build_snapshot()` es aproximadamente el siguiente:

**GET /api/v1/snapshot**

Petición del frontend

**Resolver reloj operativo**

Live o replay; instante de presentación

**Leer últimas observaciones**

Historial reciente de vehículos desde PostgreSQL

**Consultar TripUpdates**

Retrasos y actualizaciones de viajes

**Consultar salud y revisión**

Estado de fuentes y marcador de ingesta

**Construir cada vehículo**

Identidad, map-matching, movimiento y calidad

**Serializar SnapshotOut**

Contrato completo con catálogo de referencia

El endpoint se sirve con `Cache-Control: no-store`. Esto evita reutilizar inadvertidamente datos antiguos, pero también implica que las solicitudes individuales no se benefician de una caché HTTP compartida bajo su configuración actual.

### **7.3. Problema de consistencia transaccional**

AUD-06 ha documentado una carrera real entre el collector y la API.

Secuencia conceptual basada en la carrera reproducida y documentada por AUD-06.

El resultado reportado fue un snapshot etiquetado con revisión 74 que omitía el vehículo insertado en esa revisión.

Este defecto es especialmente importante antes de implementar una caché compartida. Si publicamos snapshots inconsistentes en CDN, amplificamos el problema a todos los usuarios.

La solución que evaluaría primero es construir el snapshot dentro de una vista transaccional coherente mediante `REPEATABLE READ`, complementada con un marcador de revisión explícito cuando sea necesario.

Fuente: [BACKEND_OPERATIONS_AUDIT.md](https://github.com/pedromaaz13/madrid-pulse/blob/main/docs/audits/hito-03/BACKEND_OPERATIONS_AUDIT.md?utm_source=chatgpt.com).

### **7.4. Arquitectura alternativa: generar una vez, servir muchas veces**

Vía Península no necesita reconstruir un estado completo de la red ferroviaria por cada persona que abre el mapa.

Para Madrid Pulse propongo tres niveles de distribución:

| Recurso              | Generación                            | Distribución              |
| -------------------- | ------------------------------------- | ------------------------- |
| Catálogo             | Cuando cambia GTFS o geometría        | R2/CDN, versión inmutable |
| Snapshot live        | Periódicamente, según cadencia medida | R2/CDN, caché corta       |
| Datos personalizados | Bajo demanda                          | FastAPI                   |

Por ejemplo:

```
data.madridpulse.example/
├── manifest.json
├── madrid/
│   ├── catalog-a83f2.json
│   ├── tracks-b718c.json
│   ├── trips-2026-11-24-d39c8.json
│   └── live/
│       ├── latest.json
│       └── snapshot-000482.json
└── health.json
```

El patrón sería:

1. Generar el snapshot de forma transaccional.
2. Validar su esquema.
3. Publicar primero los recursos versionados que necesita.
4. Publicar el snapshot.
5. Actualizar el puntero o manifest de último estado válido.
6. Conservar la versión anterior si la nueva generación falla.

El navegador debe comprobar las versiones, la revisión y los timestamps antes de aceptar nuevos datos.

Cloudflare documenta que un bucket R2 debe conectarse a un dominio personalizado para utilizar su CDN de caché de esta manera. No basta con crear un bucket y asumir que todas las respuestas quedan cacheadas.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developers.cloudflare.com\&sz=32)

Cloudflare Cache (CDN) docs



### **7.5. ¿REST, WebSockets o Server-Sent Events?**

| Tecnología     | Cuándo utilizarla                                     |
| -------------- | ----------------------------------------------------- |
| REST + polling | Snapshots pequeños y cadencias de segundos            |
| REST + ETag    | Catálogo, recursos versionados y detección de cambios |
| SSE            | Notificaciones unidireccionales de cambios            |
| WebSockets     | Interacción bidireccional persistente                 |
| CDN            | Distribución masiva de estados compartidos            |

Madrid Pulse no necesita WebSockets para conseguir animación fluida. El movimiento ocurre en el navegador.

Un canal WebSocket podría reducir el tiempo entre publicación y recepción, pero también introduce conexiones persistentes, reconexiones, estado y mayores exigencias operativas.

**Mi decisión para la beta sería polling HTTP sobre snapshots compartidos y mantener FastAPI.** Solo evaluaría SSE posteriormente si existe una necesidad de latencia que el modelo actual no pueda satisfacer.

## **8. Frontend engineering: por qué una aplicación parece fluida y otra no**

La fluidez de un mapa depende de varias capas, no únicamente del framework frontend.

### **8.1. Madrid Pulse ya está razonablemente modularizado**

El árbol de `apps/web/src` contiene una separación clara:

```
apps/web/src/
├── api/
│   ├── client.ts
│   └── resources.ts
├── domain/
│   ├── contract.ts
│   ├── geometry.ts
│   ├── movement.ts
│   ├── identity.ts
│   ├── catalogIndex.ts
│   └── revision.ts
├── hooks/
│   ├── useSnapshot.ts
│   ├── useCatalog.ts
│   ├── useClock.ts
│   ├── useHistory.ts
│   └── useStationBoard.ts
├── map/
│   ├── MapView.tsx
│   ├── features.ts
│   └── layers.ts
└── ui/
    ├── TrainPanel.tsx
    ├── StationPanel.tsx
    ├── NetworkPanel.tsx
    ├── HistoryView.tsx
    ├── ExploreView.tsx
    └── SearchBox.tsx
```

Esta arquitectura es correcta como punto de partida. No recomendaría una reescritura.

### **8.2. Tres relojes diferentes**

Ejemplo de funcionamiento durante 60 segundosAdquisición cada 30 s, polling del cliente cada 10 s y representación continua. La frecuencia del render no implica nuevas observaciones físicas.

En Madrid Pulse existen estos tres niveles. El `requestAnimationFrame` se ejecuta en el componente del mapa y actualiza la fuente de vehículos sin provocar necesariamente un nuevo render completo de React.

Eso es una decisión acertada.

### **8.3. El posible cuello de botella de MapLibre**

En el código actual, `vehicleFrames()` construye una colección GeoJSON con las posiciones correspondientes al instante de presentación. Después, `MapView.tsx` actualiza la fuente con `setData()`.

Este mecanismo puede ser suficiente para decenas o centenares de trenes. Pero debemos medir cuánto cuesta:

- Construir los objetos GeoJSON.
- Serializarlos o transferirlos al worker.
- Actualizar los datos de la fuente.
- Ejecutar el renderizado WebGL.
- Actualizar etiquetas y cámara.

MapLibre dispone también de `updateData()`, que permite actualizaciones incrementales sobre entidades identificadas de forma única. Su documentación recomienda distintas optimizaciones cuando crece el tamaño de los conjuntos GeoJSON.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://maplibre.org\&sz=32)

MapLibre GL JS+2



Madrid Pulse ya asigna identificadores estables a los vehículos. Esto facilita evaluar actualizaciones incrementales sin cambiar de framework.

### **Propuesta de benchmark**

| Variante                     | Implementación                               |
| ---------------------------- | -------------------------------------------- |
| A — Baseline                 | `setData()` en cada frame                    |
| B — Cadencia limitada        | Actualizar geometrías a 30 Hz                |
| C — Incremental              | `updateData()` para entidades modificadas    |
| D — Optimización espacial    | Actualizar principalmente vehículos visibles |
| E — Capa WebGL especializada | Solo si las anteriores no cumplen objetivos  |

Mediría las cinco variantes con 100, 500, 1.000 y 5.000 vehículos sintéticos, además de cortes reales de Madrid.

La decisión debe basarse en frame time, CPU, memoria y experiencia visual. No basta con comprobar que existe un `requestAnimationFrame`.

### **8.4. El hallazgo más interesante del frontend de Vía Península**

He encontrado un archivo que considero especialmente valioso:

[`src/page/budget.json`](https://github.com/gariasf/viapeninsula/blob/main/src/page/budget.json?utm_source=chatgpt.com).

Contiene presupuestos cuantitativos de rendimiento diferenciados para escritorio y teléfono.

| Métrica                                               | Escritorio | Teléfono |
| ----------------------------------------------------- | ---------- | -------- |
| Carga inicial de líneas                               | 600 ms     | 1.500 ms |
| Carga inicial de trenes                               | 1.000 ms   | 2.500 ms |
| Pausa máxima al incorporar una región                 | 100 ms     | 300 ms   |
| Pausa máxima durante ciertos desplazamientos del mapa | 34 ms      | 100 ms   |
| CPU del hilo principal en reposo                      | 100 ms/s   | 400 ms/s |
| FPS siguiendo un tren                                 | ≥110       | ≥55      |

Son presupuestos de sus escenarios de pruebas, **no resultados que haya confirmado que se cumplen siempre en producción**.

Pero aquí está una diferencia de metodología que adoptaría inmediatamente: Vía Península define explícitamente cuánto rendimiento está dispuesto a consumir al incorporar una funcionalidad.

Madrid Pulse debería tener un archivo equivalente, por ejemplo:

```
apps/web/performance/budget.json
```

Y un runner Playwright que genere resultados comparables entre commits.

No debemos perseguir exactamente sus cifras de FPS, porque dependen del hardware, pantalla, navegador y metodología de prueba. Debemos establecer presupuestos propios reproducibles.

### **8.5. Las auditorías visuales actuales no son suficientes para garantizar una buena UX**

La auditoría de frontend de Madrid Pulse documenta pruebas de navegador, selección, búsqueda, movimiento reducido, solapamiento y funcionamiento de History/Explore.

Sin embargo, el propio documento indica que su segunda versión todavía estaba pendiente de reverificación independiente.

Fuente: [FRONTEND_UX_AUDIT.md](https://github.com/pedromaaz13/madrid-pulse/blob/main/docs/audits/hito-03/FRONTEND_UX_AUDIT.md?utm_source=chatgpt.com).

Yo separaría dos dimensiones que ahora parecen mezclarse:

- **Functional correctness:** los botones, filtros, consultas y estados funcionan correctamente.
- **Product quality:** la aplicación es clara, agradable, rápida y comprensible sin conocer su arquitectura.

El segundo objetivo requiere diseño visual, pruebas de interacción y comparación directa con productos de referencia.

## **9. Electricity Maps: análisis profundo de su arquitectura de producto**

A diferencia de Vía Península, Electricity Maps es una referencia para aprender cómo convertir datos de múltiples fuentes en una experiencia analítica geoespacial.

### **9.1. Qué código tenemos disponible realmente**

He confirmado la existencia de dos repositorios diferentes:

| Repositorio                                                                                                                                  | Contenido                                            | Estado    |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | --------- |
| [electricitymaps-contrib](https://github.com/electricitymaps/electricitymaps-contrib?utm_source=chatgpt.com)                                 | Parsers, modelos, configuraciones, calidad y pruebas | Activo    |
| [electricitymaps-contrib-rewrite](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/tree/master/web?utm_source=chatgpt.com) | Frontend histórico completo                          | Archivado |

La rama del repositorio archivado es `master`. He conseguido recuperar su árbol de archivos frontend.

Esto permite estudiar su arquitectura anterior con bastante profundidad, aunque no la implementación exacta de la aplicación comercial actual.

### **9.2. Arquitectura basada en configuración**

He inspeccionado [`config/zones/ES.yaml`](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/config/zones/ES.yaml?utm_source=chatgpt.com).

Cada zona energética contiene información geográfica y atributos de dominio, con valores fechados, fuentes y configuraciones específicas.

Este patrón es extremadamente útil para Madrid Pulse.

En lugar de repartir particularidades de cada red por todo el código, podríamos evolucionar hacia configuraciones declarativas:

```
network_id: renfe-cercanias-madrid
operator: renfe
timezone: Europe/Madrid

sources:
  static:
    format: gtfs
    refresh_policy: daily

  realtime:
    format: gtfs-rt-json
    poll_interval_seconds: 30

geospatial:
  source: openstreetmap
  build_strategy: railway_graph

capabilities:
  vehicle_positions: true
  trip_updates: true
  service_alerts: true

quality:
  freshness_policy: renfe_cercanias_v1
```

Esto es una propuesta de diseño. Los intervalos y capacidades definitivos deben verificarse para cada fuente.

El objetivo no es abstraer todo desde el principio, sino evitar que la integración de otra red obligue a duplicar el collector, la API y el frontend.

### **9.3. Contratos y semántica de los datos**

En [`electricitymap/contrib/lib/models/events.py`](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/electricitymap/contrib/lib/models/events.py?utm_source=chatgpt.com) encontramos modelos Pydantic que representan entidades energéticas con reglas propias de validación.

Por ejemplo, el modelo `ProductionMix` establece categorías conocidas de producción energética, contempla valores ausentes y trata valores negativos mediante reglas explícitas.

Hay una similitud importante con nuestros paquetes:

| Electricity Maps      | Madrid Pulse                     |
| --------------------- | -------------------------------- |
| Parser por fuente     | Adaptador por operador           |
| ZoneKey               | Network ID                       |
| Production event      | Vehicle observation              |
| ProductionMix         | Contrato de datos ferroviarios   |
| Exchange              | Conexión o flujo entre entidades |
| Source                | Procedencia de la observación    |
| Validación de eventos | Quality Engine                   |

No son equivalencias semánticas exactas, pero sí patrones de arquitectura comparables.

### **9.4. Arquitectura frontend histórica**

El árbol recuperado confirma una organización por funcionalidades:

```
web/src/
├── api/
│   ├── getState.ts
│   ├── getZone.ts
│   └── getWeatherData.ts
├── features/
│   ├── map/
│   │   ├── Map.tsx
│   │   ├── MapWrapper.tsx
│   │   └── map-utils/
│   ├── map-controls/
│   ├── charts/
│   │   ├── CarbonChart.tsx
│   │   ├── BreakdownChart.tsx
│   │   ├── EmissionChart.tsx
│   │   └── hooks/
│   └── time/
│       ├── TimeAxis.tsx
│       ├── TimeController.tsx
│       └── TimeHeader.tsx
└── components/
    ├── TimeSlider.tsx
    └── TimeDisplay.tsx
```

Fíjate en una cosa: el tiempo es una funcionalidad de producto independiente. No es simplemente una variable que se pasa al mapa.

Electricity Maps combina un contexto geográfico, un contexto temporal y un contexto analítico.

Esta es la dirección que considero adecuada para Madrid Pulse.

La experiencia de producto conecta entidades geográficas, evolución temporal y métricas sobre un modelo de datos común.

### **9.5. Cómo trasladarlo a nuestra aplicación**

Imagínate seleccionar Atocha en el mapa y poder cambiar entre:

- Estado actual de la estación.
- Trenes que llegarán en los próximos minutos.
- Histórico de retrasos.
- Evolución de circulaciones observadas.
- Líneas que atraviesan la estación.
- Incidencias activas o históricas.
- Cobertura y calidad de las observaciones disponibles.

No deberíamos obligar al usuario a buscar la misma estación tres veces en Live, History y Explore.

El contexto de selección debería mantenerse entre las vistas.

Este es un objetivo mucho más interesante que añadir gráficos independientes al frontend.

He inspeccionado también los componentes históricos de Electricity Maps que coordinan esos tres contextos.

| Archivo                                                                                                                                                                | Patrón de arquitectura encontrado                                       |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [`getState.ts`](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/blob/master/web/src/api/getState.ts?utm_source=chatgpt.com)                         | Consulta del estado global, con actualización periódica                 |
| [`getZone.ts`](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/blob/master/web/src/api/getZone.ts?utm_source=chatgpt.com)                           | Consulta contextual de una entidad seleccionada                         |
| [`Map.tsx`](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/blob/master/web/src/features/map/Map.tsx?utm_source=chatgpt.com)                        | Capas geográficas, selección, estado visual y estilos                   |
| [`TimeController.tsx`](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/blob/master/web/src/features/time/TimeController.tsx?utm_source=chatgpt.com) | Selección temporal compartida mediante estado global                    |
| [`App.tsx`](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/blob/master/web/src/App.tsx?utm_source=chatgpt.com)                                     | Composición de producto, carga diferida, gestión de errores y versiones |

Una técnica concreta que me interesa es la utilización de `feature-state` de MapLibre para cambiar colores y estados de selección sin tener que reconstruir necesariamente todas las geometrías.

También utiliza TanStack Query para separar la consulta global de las consultas particulares y Jotai para compartir estados de selección y tiempo.

No trasladaría automáticamente estas librerías a Madrid Pulse, pero sí su organización conceptual.

## **10. Propuesta de diseño del producto Madrid Pulse**

Después de estudiar ambos proyectos, creo que deberíamos definir una identidad propia que combine la facilidad de exploración de Vía Península y la profundidad analítica de Electricity Maps.

### **10.1. Sistema visual map-first**

Wireframe conceptual de producto. Geometrías y cifras ilustrativas, no datos ferroviarios reales ni captura del frontend actual.

El mapa debe ser el elemento principal. Los paneles deben enriquecerlo, no competir con él.

### **10.2. Tres modos, un mismo modelo de entidades**

**Live**

Qué está ocurriendo ahora.

Trenes, líneas, estaciones, próximas llegadas e incidencias.

**History**

Qué ha ocurrido anteriormente.

Reproducción temporal, circulaciones y observaciones históricas.

**Explore**

Qué patrones podemos descubrir.

Puntualidad, cobertura, tendencias y análisis por entidades.

La navegación debería conservar la entidad seleccionada y, cuando proceda, el intervalo temporal.

### **10.3. Capa semántica y ontología**

Aquí existe una oportunidad especialmente interesante para tus objetivos profesionales.

Madrid Pulse puede evolucionar hacia un modelo de objetos operacionales, sin necesidad de introducir una plataforma de ontologías independiente.

Modelo semántico conceptual. Las relaciones físicas definitivas deben resolverse mediante identidades y contratos de dominio.

Este planteamiento conecta con los conceptos de inteligencia operacional que te interesan de Palantir Foundry.

Pero antes de incorporar agentes de IA que consulten esta ontología, necesitamos entidades fiables, relaciones verificadas y métricas correctamente definidas.

## **11. Analytics: convertir el histórico en un producto de datos**

Esta es la capa que justificaría mantener nuestra arquitectura más allá de un mapa visual.

### **11.1. Métricas que construiría**

| Métrica                  | Numerador / definición                 | Denominador o condición          |
| ------------------------ | -------------------------------------- | -------------------------------- |
| Cobertura de circulación | Viajes observados                      | Viajes programados               |
| Cobertura geográfica     | Circulaciones con corredor validado    | Circulaciones elegibles          |
| Puntualidad observada    | Viajes evaluados dentro del umbral     | Viajes con evidencia suficiente  |
| Retraso medio            | Suma de retrasos válidos               | Observaciones de retraso válidas |
| Disponibilidad de fuente | Tiempo con fuente saludable            | Tiempo monitorizado              |
| Cancelaciones reportadas | Viajes declarados cancelados           | Viajes programados               |
| Fiabilidad de posición   | Observaciones que superan validaciones | Observaciones evaluadas          |
| Cobertura temporal       | Intervalos con datos disponibles       | Intervalos esperados             |

El denominador es tan importante como el resultado.

No podemos decir que una línea tiene un 98 % de puntualidad si solamente disponemos de información suficiente sobre un pequeño porcentaje de sus circulaciones.

Tampoco podemos equiparar un servicio no observado con un servicio cancelado.

### **11.2. Qué producto analítico puede resultar**

**Explore — Rendimiento ferroviario**

Ejemplo de dashboard analítico

Datos simulados

Puntualidad evaluada

# **87,4 %**

Cobertura

# **72,1 %**

Retraso medio

# **3,8 min**

**Retraso medio por franja horaria**

0 min2 min4 min6 min8 min06:0007:0008:0009:0010:0012:0014:0016:0018:0020:0022:00

**Cobertura de observación por línea**

0%25%50%75%100%C1C2C3C4C5C7C8C10

Datos completamente ficticios utilizados para ilustrar la experiencia de producto y la presentación de métricas con cobertura explícita.

### **11.3. Arquitectura analítica futura**

Una vez que el producto tenga suficiente histórico, podemos plantear:

- Modelos dimensionales de circulaciones, estaciones, líneas y observaciones.
- Métricas definidas mediante una capa semántica.
- Comparaciones entre semanas y periodos.
- Detección de anomalías en retrasos.
- Análisis espacial de interrupciones.
- SQL Lab de solo lectura sobre conjuntos de datos controlados.
- Consultas mediante agentes de IA.

Pero hay una condición: los modelos predictivos y agentes deben trabajar sobre observaciones y estimaciones correctamente diferenciadas.

No introduciría inteligencia artificial en el cálculo de posiciones simplemente por incorporar IA al producto.

## **12. Platform engineering: arquitectura real de producción**

La arquitectura local y la de producción no tienen por qué ser completamente diferentes. Pero actualmente hay una distancia importante entre ejecutar componentes en un ordenador y disponer de una plataforma pública mantenible.

### **12.1. Qué existe en Madrid Pulse**

El árbol del repositorio contiene:

| Componente                  | Situación observada          |
| --------------------------- | ---------------------------- |
| Docker Compose              | PostgreSQL/PostGIS local     |
| GitHub Actions              | CI Python y frontend         |
| Migraciones SQL             | Implementadas                |
| Scripts de operación        | Implementados                |
| Servicios systemd           | Plantillas                   |
| Servicios launchd           | Plantillas                   |
| Exportación diaria          | Scripts y lógica disponibles |
| Infraestructura Cloudflare  | Documentación                |
| Despliegue público completo | No verificado                |
| Operación 24/7              | No demostrada                |

Hay más trabajo de operación implementado del que parecía inicialmente, pero todavía no constituye una infraestructura pública completamente desplegada.

### **12.2. Arquitectura de producción recomendada**

**Usuarios de Madrid Pulse**

Escritorio · Móvil · Clientes API

**Cloudflare Edge**

DNS · HTTPS · CDN · Protección

**Frontend hosting**

Vite static build

**R2 público**

Snapshots · Catálogo

**VPS Linux · Docker Compose**

24/7

**Collector**

Adquisición Renfe

**FastAPI**

Consultas REST

**Publisher**

Snapshots para CDN

**Snapshotter**

Exportación y marts

**PostgreSQL / PostGIS**

Red privada y volumen persistente

**R2 privado**

Histórico Parquet

**Backups**

Recuperación independiente

GitHub Actions · CI/CD · Builds · Observabilidad

Es una arquitectura relativamente económica y sencilla de comprender.

No necesita Kubernetes, un clúster Spark, Kafka ni una docena de microservicios.

### **12.3. Configuración inicial de servicios**

| Servicio                | Tecnología propuesta                     | Responsabilidad                    |
| ----------------------- | ---------------------------------------- | ---------------------------------- |
| DNS y HTTPS             | Cloudflare                               | Dominio y seguridad perimetral     |
| Frontend                | Cloudflare Workers Static Assets o Pages | Aplicación React compilada         |
| Compute                 | VPS Linux                                | Ejecutar procesos persistentes     |
| Orquestación            | Docker Compose                           | Gestionar servicios                |
| Base operativa          | PostgreSQL/PostGIS                       | Datos relacionales y espaciales    |
| API                     | FastAPI + Uvicorn                        | Consultas de producto              |
| Object storage          | Cloudflare R2                            | Histórico y distribución           |
| Analítica               | DuckDB                                   | Procesamiento de Parquet           |
| Scheduling              | systemd timers / GitHub Actions          | Procesos periódicos                |
| CI/CD                   | GitHub Actions                           | Construcción, pruebas y despliegue |
| Monitorización inicial  | Health checks y logs estructurados       | Estado operativo                   |
| Monitorización avanzada | Prometheus/Grafana, si se justifica      | Métricas y alertas                 |

El VPS es una opción inicial, no una obligación definitiva. Si aumenta el tráfico o el mantenimiento de PostgreSQL empieza a consumir demasiado tiempo, podemos externalizar la base de datos sin cambiar la arquitectura conceptual.

### **12.4. Entornos separados**

Esto es particularmente importante después del incidente de PostgreSQL documentado durante AUD-06.

**Development**

Tu equipo

Base desechable

Fixtures

Cambios frecuentes

**Staging**

Infraestructura de prueba

Datos controlados

Pruebas E2E

Captura continua

**Production**

Aplicación pública

Datos persistentes

Backups

Release aprobada

Cada entorno debe tener credenciales independientes y configuraciones explícitas. Si falta una variable crítica de base de datos, el proceso debe fallar al iniciar en vez de conectarse a una instancia por defecto.

## **13. CI/CD: cómo debería evolucionar nuestro proceso**

Vía Península ya ha resuelto una cuestión que Madrid Pulse todavía debe consolidar: coordinar la publicación de código y datos.

En nuestro caso propondría dos pipelines distintos.

### **Pipeline de software**

Pull Request

Lint + Typecheck

Unit tests + PostgreSQL integration

Regresiones ferroviarias

Build frontend + contenedores

Playwright + performance budgets

Deploy staging

Smoke tests + aceptación

Release y despliegue autorizado

### **Pipeline de datos**

Descarga GTFS y actualización OSM según política

Verificación de versiones y licencias

Construcción topológica y geográfica

Validación de patrones y estaciones

Generación de bundles inmutables

Publicación de objetos en R2

Actualización del manifest

Informe de calidad y alertas

El pipeline de datos no debería obligarnos a desplegar de nuevo todo el frontend cada vez que cambian unos horarios.

Y un cambio visual no debería obligarnos a regenerar toda la red ferroviaria.

Esta independencia reduce costes, riesgos y tiempos de desarrollo.

## **14. Observabilidad: cómo saber si Madrid Pulse funciona realmente**

Un mapa que sigue mostrando trenes no demuestra que la plataforma esté saludable. Podría estar mostrando estimaciones o datos antiguos.

Necesitamos observabilidad técnica y observabilidad del dominio.

| Categoría  | Indicadores                                  |
| ---------- | -------------------------------------------- |
| Ingesta    | Éxitos, errores, latencia, tamaño, entidades |
| Frescura   | Edad del feed y de cada observación          |
| Calidad    | Duplicados, anomalías, campos ausentes       |
| Geometría  | Cobertura, gaps, distancia al trazado        |
| Movimiento | Avances falsos, saltos, correcciones         |
| API        | Latencia p50/p95/p99, errores, peticiones    |
| PostgreSQL | Conexiones, consultas lentas, tamaño         |
| CDN        | Cache hit ratio, lecturas de origen          |
| Frontend   | FPS, frame time, memoria, errores JS         |
| Histórico  | Particiones disponibles, tamaño, integridad  |
| Operación  | Uptime, reinicios, recuperación              |
| Coste      | Almacenamiento, compute y operaciones        |

Un buen producto de datos debe poder responder no solo qué está ocurriendo en la red ferroviaria, sino también qué calidad tiene la información que estamos mostrando.

## **15. Estudio de escalabilidad y costes**

### **15.1. Escalabilidad del directo**

He preparado un modelo interactivo para evaluar la arquitectura actual frente a una basada en snapshots compartidos.

## **Modelo de carga y distribución**

Usuarios simultáneos

## **300**

Horas diarias con esa concurrencia

**8 h**

Polling del cliente y del publisher

10 s20 s30 s

Tamaño comprimido del snapshot

**80 KB**

Cache hit ratio estimado

**95 %**

Peticiones mensuales de clientes

# **12.960.000**

Pico de peticiones / segundo

# **15**

Generaciones mensuales del publisher 24/7

# **129.600**

Lecturas mensuales de origen con CDN

# **648.000**

Transferencia mensual a usuarios

# **1036,8 GB**

Reducción estimada de lecturas de origen

# **95 %**

Simulación teórica de 30 días. No incorpora peticiones adicionales de catálogo, histórico, teselas o fallos. Los tamaños y el porcentaje de caché deben medirse.

La principal ventaja del snapshot compartido no es eliminar todas las peticiones. Es evitar que cada petición obligue a ejecutar otra vez la lógica de movimiento, consultar PostgreSQL y serializar el estado ferroviario completo.

### **15.2. Almacenamiento histórico**

## **Estimación de histórico de posiciones**

Vehículos activos de media**120**

Frecuencia de captura

10 s20 s30 s60 s

Horas de servicio por día**18 h**

Bytes estimados por fila almacenada**250 B**

Reducción mediante deduplicación**30 %**

Filas por día

# **181.440**

Filas por año

# **66.2 M**

Almacenamiento anual estimado

# **16.6 GB**

Almacenamiento a cinco años

# **82.8 GB**

Solo posiciones de vehículos. Excluye TripUpdates, alertas, índices PostgreSQL, backups, metadatos y archivos GTFS/OSM. Los bytes por fila son una hipótesis ajustable.

A esta escala no parece existir una justificación inmediata para un data warehouse distribuido.

PostgreSQL para los datos operacionales y Parquet/DuckDB para el archivo histórico siguen siendo decisiones razonables.

R2 factura almacenamiento y operaciones, aunque no cobra directamente el egress de los objetos. Por ello debemos medir el número de lecturas, escrituras y el porcentaje de caché, y no solamente los gigabytes almacenados.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developers.cloudflare.com\&sz=32)

Cloudflare R2 docs



### **15.3. Presupuesto de arquitectura**

Como escenario de planificación, no como cotización verificada de proveedores:

| Escenario                      | Infraestructura                                  | Presupuesto orientativo mensual |
| ------------------------------ | ------------------------------------------------ | ------------------------------- |
| Desarrollo local               | Equipo propio                                    | 0 € adicionales de hosting      |
| Beta económica                 | VPS + CDN + R2 + backups                         | 12–45 €                         |
| Beta con servicios gestionados | Compute + PostgreSQL gestionado + object storage | 35–100 €                        |
| Producto con crecimiento       | Separación de servicios y capacidad ampliada     | 80–250 € o más                  |

Yo comenzaría con el escenario económico y definiría métricas que activen el cambio al siguiente nivel.

No contrataría capacidad por anticipado sin tráfico real o pruebas que demuestren su necesidad.

## **16. Evaluación comparativa definitiva**

Comparación cualitativa basada en las implementaciones públicas inspeccionadas

|              | Madrid Pulse      | Vía Península      | Electricity Maps     |
| ------------ | ----------------- | ------------------ | -------------------- |
| Ingesta      | Implementada      | Multioperador      | Multifuente          |
| Contratos    | Canónicos         | Bundles tipados    | Eventos de dominio   |
| Persistencia | PostGIS           | R2 / DO            | Parcialmente privada |
| Geometría    | Cobertura parcial | Grafo ferroviario  | Geometrías de zonas  |
| Movimiento   | P0 pendientes     | Motor cliente      | No aplica            |
| Distribución | REST dinámica     | CDN                | API propia           |
| Frontend     | React / GL        | TS / GL            | React / GL histórico |
| Histórico    | Parquet / DuckDB  | Snapshots y delays | Producto de datos    |
| CI/CD        | CI verificada     | CI/CD en código    | Proceso interno      |
| Producción   | NO-GO             | Publicada          | Publicada            |

### **Qué podemos aprender de cada uno**

**De Vía Península:**

El trazado ferroviario mediante grafos, las reglas específicas por operador, la animación consciente de horarios, los builds anticipados, la separación de geometrías y datos dinámicos, la distribución mediante CDN y los presupuestos de rendimiento.

**De Electricity Maps:**

Los adaptadores de fuentes, los contratos semánticos, las configuraciones declarativas, la separación de estado global y detalle contextual, la navegación temporal compartida y la explotación del histórico como producto.

**De Madrid Pulse:**

La separación entre observaciones, posiciones proyectadas y estimaciones, la persistencia propia, el potencial analítico, la API versionada, la arquitectura modular y el control explícito de calidad.

No elegiría uno de los tres modelos íntegramente. Construiría una síntesis coherente con nuestros objetivos.

## **17. Decisiones técnicas definitivas propuestas**

| Componente                   | Decisión | Justificación                                                              |
| ---------------------------- | -------- | -------------------------------------------------------------------------- |
| Python                       | KEEP     | Ecosistema de datos y geoprocesamiento                                     |
| FastAPI                      | KEEP     | Contratos tipados y consultas de producto                                  |
| PostgreSQL/PostGIS           | KEEP     | Persistencia propia y dominio geoespacial                                  |
| Parquet/DuckDB               | KEEP     | Histórico eficiente                                                        |
| React/TypeScript             | KEEP     | Aplicación compleja y modular                                              |
| MapLibre GL                  | KEEP     | Motor cartográfico adecuado                                                |
| Deduplicación                | MODIFY   | Revisar concurrencia y frescura por entidad                                |
| Motor temporal               | MODIFY   | Introducir estados y movimiento por tramos                                 |
| Geometrías OSM               | MODIFY   | Reducir dependencia de relaciones manuales                                 |
| Snapshot API                 | MODIFY   | Coherencia transaccional y distribución compartida                         |
| Renderizado                  | MODIFY   | Optimización basada en benchmarks                                          |
| Grafo ferroviario            | ADOPT    | Mayor cobertura y automatización                                           |
| Geofabrik/osmium             | ADOPT    | Procesamiento reproducible                                                 |
| CDN/R2                       | ADOPT    | Escalabilidad del plano de distribución                                    |
| Performance budgets          | ADOPT    | Control de calidad visual                                                  |
| Basemap vectorial            | ADOPT    | Control cartográfico                                                       |
| Staging y CD                 | ADOPT    | Operación real y releases reproducibles                                    |
| Configuración por red        | ADOPT    | Extensibilidad                                                             |
| Kafka/Flink/Spark            | DEFER    | Volumen insuficiente para justificarlo                                     |
| dbt                          | DEFER    | Introducir cuando crezca la capa analítica                                 |
| WebSockets                   | DEFER    | No necesarios para fluidez visual                                          |
| Kubernetes                   | REJECT   | Complejidad operativa innecesaria                                          |
| Reescritura a TypeScript     | REJECT   | No existe beneficio demostrado                                             |
| Copia directa de código AGPL | REJECT   | Preservar estrategia de licencia MIT mediante implementación independiente |

Los dos repositorios de referencia tienen código bajo AGPL. Estudiar sus patrones arquitectónicos es distinto de incorporar código derivado a nuestra aplicación. Debemos conservar esta distinción y revisar también las licencias de datos y cartografía.

## **18. Roadmap técnico integrado con el Hito 4**

No crearía otro backlog independiente de las tareas existentes. Incorporaría las conclusiones de esta investigación en el H4 y añadiría únicamente las actividades que actualmente no están cubiertas suficientemente.

| ID propuesto | Trabajo                                  | Dependencia         | Prioridad        |
| ------------ | ---------------------------------------- | ------------------- | ---------------- |
| ARC-01       | ADR de movimiento temporal               | H4-00               | P0               |
| DAT-01       | Aislamiento y seguridad de PostgreSQL    | H4-11               | P0 operativa     |
| DAT-02       | Captura y calibración con datos reales   | DAT-01              | P1               |
| MOV-01       | Modelo de estados y paradas              | ARC-01              | P0               |
| API-01       | Snapshot transaccional coherente         | H4-01               | P0/P1            |
| API-02       | Corrección del reloj replay              | H4-01               | P0               |
| GEO-01       | Completar corredores disponibles         | H4-03               | P1               |
| GEO-02       | PoC de grafo ferroviario                 | GEO-01 parcial      | P1               |
| GEO-03       | Build geográfico reproducible            | GEO-02              | P1               |
| UX-01        | Procedencia visual y estados             | MOV-01              | P1               |
| UX-02        | Basemap vectorial y design system        | Independiente       | P1               |
| UX-03        | Vías compartidas y símbolos ferroviarios | GEO-02              | P1               |
| UX-04        | Benchmarks Playwright/MapLibre           | UX-02               | P1               |
| SRV-01       | PoC de snapshot publisher                | API-01              | P1               |
| SRV-02       | Manifest y catálogo versionado           | GEO-03              | P1               |
| ANA-01       | Métricas y denominadores auditados       | DAT-02              | P1               |
| OPS-01       | Docker Compose de producción             | DAT-01              | P1               |
| OPS-02       | Staging, CI/CD y backups                 | OPS-01              | P1               |
| OPS-03       | Soak test 72 h y carga                   | Componentes previos | P1               |
| REL-01       | Release-readiness y beta                 | Gates aprobados     | P0 para publicar |

Estos identificadores son propuestas de agrupación, no tareas autorizadas ni creadas en GitHub.

### **Orden de ejecución recomendado**

Dos líneas de trabajo paralelas, con dependencias explícitas

**Data & Railway**

Seguridad de datos

Captura real

Contrato temporal

Corrección del motor

Grafo ferroviario

Snapshot publisher

**Product & Platform**

Design system

Basemap vectorial

Staging inicial

Performance baseline

Integración frontend

CI/CD y observabilidad

**Integración y validación**

Regresiones · Calidad · Rendimiento · 72 h de operación

**Beta pública de Madrid Pulse**

Tras aprobación de los gates de publicación

Esto permite avanzar en la experiencia de producto sin esperar a que estén corregidas todas las cuestiones ferroviarias, siempre que los desarrollos visuales utilicen contratos controlados y fixtures.

## **19. Organización de agentes y control de costes de desarrollo**

La investigación también revela una cuestión de metodología: Vía Península presenta decisiones técnicas concretas, pruebas específicas y presupuestos medibles. Nosotros corremos el riesgo de invertir demasiados recursos de IA en auditorías extensas y documentación repetitiva.

Para evitarlo establecería una política de ejecución por complejidad.

| Complejidad          | Modelo recomendado                          | Tipo de tarea                                            |
| -------------------- | ------------------------------------------- | -------------------------------------------------------- |
| Baja                 | Haiku o modelo ligero disponible            | Inventarios, documentación, tareas mecánicas             |
| Media                | Sonnet o Codex de esfuerzo medio            | React, API, SQL, tests, infraestructura                  |
| Alta                 | Codex de razonamiento alto                  | Algoritmos, integración y defectos complejos             |
| Crítica              | Opus o modelo de razonamiento avanzado      | Arquitectura temporal, grafos y decisiones irreversibles |
| Revisión adversarial | Proveedor contrario, contexto independiente | ADR críticos y gates de publicación                      |

Los identificadores exactos deben verificarse en Orca, sin asumir disponibilidad por el nombre comercial del modelo.

El protocolo de Elephant-Goldfish que habíamos estudiado lo aplicaría a tres decisiones:

1. Modelo ferroviario temporal.
2. Arquitectura de construcción geoespacial.
3. Arquitectura de producción y distribución.

No lo utilizaría para cada cambio de código, cada componente React o cada prueba unitaria.

Además, exigiría que cada agente entregue una implementación, pruebas, evidencia y riesgos pendientes, sin generar por defecto informes de cientos de líneas.

## **20. Mi conclusión profesional**

Después de esta investigación, no considero que Madrid Pulse tenga un problema fundamental de selección tecnológica.

El proyecto tiene cuatro problemas diferentes:

**1. Veracidad ferroviaria**

El motor actual no representa correctamente determinadas paradas y transiciones temporales. Es el problema más urgente.

**2. Automatización geoespacial insuficiente**

Dependemos demasiado de corredores configurados y relaciones OSM específicas. Vía Península demuestra un camino más industrializado mediante grafos.

**3. Distribución y operación**

Tenemos los componentes de una plataforma de datos, pero no una estrategia de publicación y funcionamiento continuo suficientemente demostrada.

**4. Desarrollo de producto**

Necesitamos dedicar una línea de trabajo explícita a diseño, cartografía, interacción, rendimiento y coherencia entre las vistas analíticas.

No cambiaría todo el stack. Cambiaría la forma de construir las geometrías, el contrato temporal del movimiento y la arquitectura de distribución del directo.

### **La arquitectura definitiva hacia la que dirigiría Madrid Pulse**

**DATA ACQUISITION**

Python · Adaptadores · GTFS/GTFS-RT

**DATA ENGINEERING**

Contratos · Calidad · PostGIS · Parquet

**RAILWAY INTELLIGENCE**

Grafo ferroviario · Identidad · Estado · Movimiento

**DATA SERVING**

FastAPI · Snapshot publisher · R2 · CDN

**GEOSPATIAL EXPERIENCE**

React · TypeScript · MapLibre · WebGL

LIVE

HISTORY

EXPLORE

Futuras extensiones: movilidad multimodal, capa semántica, SQL Lab e inteligencia operacional.

## **21. Fuentes principales y límites de la investigación**

| Área                       | Fuente primaria                                                                                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Collector y persistencia   | [Madrid Pulse — services/collector](https://github.com/pedromaaz13/madrid-pulse/tree/main/services/collector?utm_source=chatgpt.com)                       |
| Geometrías                 | [Madrid Pulse — packages/geo](https://github.com/pedromaaz13/madrid-pulse/tree/main/packages/geo?utm_source=chatgpt.com)                                   |
| Movimiento                 | [Madrid Pulse — packages/movement](https://github.com/pedromaaz13/madrid-pulse/tree/main/packages/movement?utm_source=chatgpt.com)                         |
| API                        | [Madrid Pulse — apps/api](https://github.com/pedromaaz13/madrid-pulse/tree/main/apps/api?utm_source=chatgpt.com)                                           |
| Frontend                   | [Madrid Pulse — apps/web](https://github.com/pedromaaz13/madrid-pulse/tree/main/apps/web?utm_source=chatgpt.com)                                           |
| Auditoría H3               | [Madrid Pulse — auditorías](https://github.com/pedromaaz13/madrid-pulse/tree/main/docs/audits/hito-03?utm_source=chatgpt.com)                              |
| Grafo ferroviario          | [Vía Península — track.ts](https://github.com/gariasf/viapeninsula/blob/main/src/build/track.ts?utm_source=chatgpt.com)                                    |
| Motor temporal             | [Vía Península — engine.ts](https://github.com/gariasf/viapeninsula/blob/main/src/engine.ts?utm_source=chatgpt.com)                                        |
| Ingesta                    | [Vía Península — step.ts](https://github.com/gariasf/viapeninsula/blob/main/src/fetcher/step.ts?utm_source=chatgpt.com)                                    |
| Decisiones arquitectónicas | [Vía Península — ADRs](https://github.com/gariasf/viapeninsula/tree/main/docs/adr?utm_source=chatgpt.com)                                                  |
| Rendimiento                | [Vía Península — budget.json](https://github.com/gariasf/viapeninsula/blob/main/src/page/budget.json?utm_source=chatgpt.com)                               |
| Adaptadores                | [Electricity Maps — parsers](https://github.com/electricitymaps/electricitymaps-contrib/tree/master/electricitymap/contrib/parsers?utm_source=chatgpt.com) |
| Frontend histórico         | [Electricity Maps — rewrite](https://github.com/electricitymaps/electricitymaps-contrib-rewrite/tree/master/web?utm_source=chatgpt.com)                    |
| Estándares                 | [GTFS-Realtime Best Practices](https://gtfs.org/documentation/realtime/realtime-best-practices/?utm_source=chatgpt.com)                                    |
| Rendimiento cartográfico   | [MapLibre Performance Guide](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/?utm_source=chatgpt.com)                                           |
| Distribución cloud         | [Cloudflare R2 Cache](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/?utm_source=chatgpt.com)                                  |

Esta investigación ha incluido inspección directa de código fuente, árboles de repositorios, contratos, configuraciones y documentación técnica. No ha incluido ejecución independiente de las aplicaciones, benchmarks reales ni reproducción propia de los defectos encontrados por los auditores de H3.

Las decisiones propuestas son, por tanto, recomendaciones arquitectónicas fundamentadas que deben validarse mediante pruebas antes de autorizar cambios importantes.

**Mi recomendación es incorporar esta investigación al Hito 4, sin reiniciar Madrid Pulse.** Construir primero una plataforma ferroviaria excelente y publicarla. Después podremos utilizar esa infraestructura como base para un producto de inteligencia de movilidad mucho más ambicioso.

El objetivo ya no debería ser simplemente desarrollar más código. Debería ser conseguir una aplicación que esté funcionando en Internet, que conserve datos cada día y que podamos enseñar como un proyecto completo de Data Engineering, Software Architecture, Geospatial Engineering y Product Development.