# Madrid Pulse — replanteamiento completo, validación técnica y plan de implantación

## Plan visible corregido y decisión ejecutiva

La definición correcta del equipo de trabajo queda fijada así y sustituye cualquier formulación anterior contradictoria: **Orca es exclusivamente el IDE/entorno de trabajo. Los dos agentes ejecutores y revisores son Anthropic Claude Code y OpenAI Codex.** En consecuencia, el paso que anteriormente aparecía como “Preparar tareas para agentes (Claude Code y Orca) y verificación” debe considerarse reemplazado por:

> **Preparar tareas y revisión cruzada para agentes Claude Code y Codex en Orca IDE.**

El plan visible de investigación y ejecución queda, por tanto, así:

1. Auditar directamente Via Península —web, repositorio, ADRs, contratos y arquitectura—, Valfiguer —web, blog, API y datos históricos— y compararlos con la propuesta original de Madrid Pulse.
2. Verificar fuentes, accesos y permisos de Renfe GTFS/GTFS-RT, CRTM/Comunidad de Madrid, OpenStreetMap y las licencias de todos los proyectos utilizados como referencia.
3. Auditar algoritmos de movimiento, map-matching, cálculo de retrasos, JSON, contratos de entrada/salida y calidad de datos, separando explícitamente lo comprobado de lo inferido.
4. Validar arquitectura, costes, seguridad, almacenamiento histórico, modelos de datos, API propia y viabilidad tecnológica/profesional.
5. Diseñar roadmap por fases y tareas dependientes, con ejecución y revisión cruzada **Claude Code ↔ Codex**, trabajando ambos dentro de **Orca IDE**, y preparar el arranque del repositorio.

La conclusión principal es **GO**, pero con una condición importante: Madrid Pulse no debería plantearse como una copia de Via Península ni de Valfiguer. Técnicamente el proyecto es viable y, de hecho, los feeds que necesitamos existen actualmente: Renfe Data publica GTFS estático y tres conjuntos GTFS-RT para Cercanías —posiciones, trip updates e incidencias—, mientras que el endpoint actualmente utilizado por Valfiguer confirma acceso operativo a `vehicle_positions.json`, `trip_updates.json` y `alerts.json`. citeturn650461search2turn568214view0

Tampoco debemos partir de la premisa de que “ya tenemos TODO”. Tenemos suficientes piezas para construir el producto, pero aún debemos validar nosotros mismos la cobertura real de la C5, estabilidad temporal de IDs, timestamps, correspondencia `trip_id ↔ GTFS static`, frecuencia efectiva de actualización, anomalías y comportamiento durante cambios de día. Valfiguer demuestra precisamente que existen problemas reales de calidad —incluidas correcciones de reloj y de cambio de día— y publica `flags` para hacerlos explícitos. citeturn568214view0turn568214view1

La propuesta original de **Madrid Pulse** sigue teniendo sentido porque su objetivo es distinto: no solo visualizar el tren actual, sino construir un producto de datos propio con **Live / History / Explore**, un pipeline histórico analizable y una arquitectura preparada para ampliar Madrid → España. Via Península ha optimizado brillantemente la visualización y el movimiento; Valfiguer ha optimizado normalización, transparencia de fuente y explotación de históricos; Madrid Pulse debería tomar esas ideas como referencia, pero conservar una arquitectura analítica propia.

## Qué hacen realmente Via Península y Valfiguer, y qué debe ser Madrid Pulse

### Via Península

Via Península es actualmente el referente técnico más útil para estudiar el problema de **movimiento visual convincente sobre infraestructura ferroviaria real**. Su README explica que el tren no se dibuja simplemente en el último punto GPS: el horario mueve el tren continuamente a lo largo de su recorrido y la información live corrige temporalmente ese movimiento. Entre actualizaciones, el tren sigue desplazándose frame a frame por geometría ferroviaria derivada de OpenStreetMap. citeturn835009view0turn103999view1

Su arquitectura pública es particularmente interesante. El proceso diario construye las geometrías y viajes, un fetcher basado en Cloudflare obtiene los feeds periódicamente, los resultados se publican en R2 y el navegador consume snapshots estáticos mediante CDN. El propio proyecto enfatiza que esto evita ejecutar código de backend por cada petición del usuario, desacoplando el coste del número de espectadores. citeturn835009view0turn103999view0

Via Península también resuelve un problema que tendremos nosotros: las geometrías GTFS no necesariamente coinciden exactamente con las vías visibles. Su ADR de trazado explica que toma las estaciones en orden y calcula caminos ferroviarios sobre la red de OpenStreetMap, teniendo en cuenta sentido, ancho de vía, vía doble, cambios de ancho y casos anómalos. No debemos copiar esa implementación, pero el principio arquitectónico es muy valioso: **posición del tren y geometría visual son dos problemas distintos**. citeturn566786view0

También ofrece una lección importante sobre escalado de datos: acabaron dividiendo los bundles por región porque una única carga para toda España crecía demasiado y una avería en una red podía romper toda la compilación. El ADR correspondiente muestra un diseño con `track` por región y `trips` por región/día. citeturn566786view1

El código de Via Península está publicado bajo **AGPL-3.0**. Esa licencia está diseñada expresamente para que modificaciones de software accesibles a usuarios mediante red ofrezcan también el código fuente correspondiente. Por tanto, estudiar el proyecto, sus ADRs, patrones y decisiones es perfectamente legítimo; **copiar o derivar directamente su implementación dentro de Madrid Pulse puede imponer obligaciones AGPL sobre la obra derivada**. citeturn168389view0turn597929search0

Mi recomendación es clara: **clean-room conceptual**. Podemos leer el proyecto para entender problemas, interfaces, edge cases y arquitectura; después escribimos nuestra implementación desde cero basándonos en GTFS, GTFS-RT, OSM y nuestras especificaciones. Si en algún momento queremos incorporar código de Via Península literalmente, se abre una decisión de licencia que debe registrarse en un ADR antes de hacerlo.

### Valfiguer

Valfiguer está más cerca de Madrid Pulse en la capa de **datos y analítica** que Via Península. Su servicio expone una API pública en GeoJSON, datos de trenes, estaciones, líneas, avisos, cancelaciones, puntualidad, informes y un histórico descargable. citeturn568214view1

Su endpoint live actualmente devuelve, además del `FeatureCollection`, metadatos de salud por feed: `ok`, `stale`, `data_age_s`, `unchanged_for_s`, `source_timestamp`, `entities`, `rejected`, errores y umbral de staleness. Es una idea excelente y deberíamos incorporarla conceptualmente a Madrid Pulse mediante un modelo propio de observabilidad de fuente. citeturn568214view0

Su histórico es especialmente útil como referencia de dimensionamiento. Valfiguer guarda **cada cambio de posición, estado o retraso**, no necesariamente cada polling idéntico, en CSV comprimido por día, con campos como `received_at`, `reported_at`, `train_id`, `source`, `trip_id`, coordenadas, estado, parada, retraso, velocidad y flags; conserva 90 días. Los ficheros visibles de noviembre de 2026 oscilan aproximadamente entre 11 y 21 MB/día para el conjunto de fuentes que maneja el proyecto. citeturn568214view1

Esto confirma algo muy importante para nuestra arquitectura: **no necesitamos almacenar cada lectura completa cada 20 segundos si nada cambia**. Podemos deduplicar observaciones idénticas y archivar solo cambios significativos, reduciendo drásticamente coste y volumen.

El artículo de Valfiguer también describe problemas empíricos que deberíamos convertir en pruebas de calidad: posiciones que implicaban velocidades absurdas, necesidad de descartar incoherencias, trenes saliéndose de la vía y necesidad de adherirlos a geometría ferroviaria. También explica que utilizaron agentes Claude Code en paralelo, pero esa experiencia de desarrollo no implica ninguna especificación técnica para Madrid Pulse. citeturn650461search8

### Madrid Pulse

La diferenciación debería ser ésta:

| Producto | Fortaleza principal | Persistencia | Movimiento | Analítica | Arquitectura pública |
|---|---|---:|---|---|---|
| Via Península | Visualización ferroviaria y motor de movimiento | Snapshots/bundles operativos | Muy desarrollado | Secundaria | Sí, AGPL |
| Valfiguer | Datos normalizados, transparencia, histórico, puntualidad | Histórico 90 días | Más orientado a posición observada | Fuerte | API pública; implementación no verificada como repo público |
| **Madrid Pulse** | **Producto de datos Madrid-first con Live + History + Explore** | **Hot DB + histórico columnar + agregados** | **Suave pero explícitamente estimado** | **Primera clase** | **Nuestra arquitectura y contratos** |

Madrid Pulse no necesita competir copiando todo lo que hacen. El MVP correcto es **C5 Madrid**, con una base de datos y contratos diseñados desde el primer día para crecer a todo Cercanías Madrid y posteriormente a España.

## Datos, algoritmos, licencias y límites que debemos respetar

Renfe Data permite reutilización comercial y no comercial, incluida copia, transformación, extracción y combinación, pero exige citar la fuente, conservar la información relevante sobre actualización y no insinuar respaldo o patrocinio de Renfe. El propio portal declara actualmente los datasets bajo Creative Commons Attribution 4.0. citeturn950736search0turn950736search2

Para el MVP, las fuentes primarias deben ser directamente Renfe, no la API de Valfiguer. Los endpoints observados y usados actualmente son:

```text
Cercanías vehicle positions:
gtfsrt.renfe.com/vehicle_positions.json

Cercanías trip updates:
gtfsrt.renfe.com/trip_updates.json

Cercanías service alerts:
gtfsrt.renfe.com/alerts.json

GTFS static Cercanías:
Renfe Data / Fichero_CER
```

Valfiguer documenta esas mismas fuentes y actualmente consulta posiciones Cercanías aproximadamente cada 20 segundos, trip updates cada 30 segundos y avisos cada 60 segundos. Eso es evidencia útil sobre el comportamiento actual, pero Madrid Pulse debe medirlo directamente y no asumir esos intervalos contractualmente. citeturn568214view1

CRTM publica además datos de Cercanías Madrid y GTFS estático. Su licencia permite uso comercial y no comercial y permite crear obras de valor añadido, aunque establece requisitos propios de reutilización y atribución. El NAP del Ministerio también identifica actualmente un dataset GTFS de “Cercanías Madrid” cuyo responsable es CRTM. citeturn950736search3turn950736search4turn950736search5

Para geometría ferroviaria podemos utilizar OpenStreetMap, pero OSM está bajo **ODbL** y exige atribución; si generamos una base de datos derivada de OSM y la distribuimos, debemos revisar las obligaciones de share-alike de la base derivada. La UI debe incluir claramente `© OpenStreetMap contributors`. citeturn950736search7

Los datos CC BY 4.0 permiten adaptación y reutilización comercial siempre que exista atribución adecuada y se indiquen cambios cuando corresponda. citeturn597929search5turn597929search6

Por tanto, establecería desde el principio:

```text
docs/legal/DATA_SOURCES.md
docs/legal/ATTRIBUTION.md
docs/legal/LICENSE_MATRIX.md
```

y cada dataset deberá registrar al menos:

```text
source_id
publisher
dataset_name
source_url
license
attribution_text
fetched_at
source_updated_at
checksum
schema_version
```

En calidad de datos, el proyecto `Niltra/cercanias`, publicado con MIT, aporta otra referencia útil: diferencia **cobertura del retraso** de **puntualidad**, detecta snapshots repetidos y correcciones abruptas del retraso, precisamente para evitar publicar métricas como si representaran todo el servicio cuando solo representan la muestra que informa. citeturn168389view4turn103999view3

Eso debe convertirse en una regla de Madrid Pulse:

```text
NO publicar:
"87 % de puntualidad de C5"

si realmente solo podemos afirmar:
"87 % de los viajes observados con delay disponible estuvieron dentro del umbral;
cobertura del feed: 78 %."
```

### Movimiento del tren

No copiaría el motor de Via Península, pero sí adoptaría su principio: **schedule-driven, live-corrected**. El propio proyecto documenta que los feeds en vivo pueden ser demasiado discontinuos para animar directamente y que incluso algunos puntos de Renfe pueden generar velocidades implausibles. citeturn103999view1

Nuestro motor debería trabajar con cuatro estados:

```text
OBSERVED
ESTIMATED
STALE
SCHEDULED
```

y devolver además:

```json
{
  "position_mode": "ESTIMATED",
  "confidence": 0.78,
  "last_observation_at": "...",
  "age_s": 23,
  "source": "renfe_gtfs_rt"
}
```

Así evitamos representar una interpolación como GPS real.

La lógica inicial podría ser:

```text
GPS reciente y plausible
        ↓
map-match al track
        ↓
localizar distancia acumulada sobre shape
        ↓
estimar progreso esperado por horario
        ↓
calcular offset temporal
        ↓
interpolar hasta siguiente observación
        ↓
limitar aceleración / velocidad / retrocesos imposibles
```

Cuando el dato sea viejo:

```text
0–60 s       Live / confidence alta
60–180 s     Estimated / confidence decreciente
>180 s       Stale
sin datos    Scheduled
```

Los umbrales exactos deben parametrizarse y calibrarse con datos reales, no fijarse como verdad desde el diseño.

## Arquitectura objetivo, histórico y coste mínimo

La arquitectura original de Madrid Pulse es sólida y profesional, pero para el MVP conviene evitar una proliferación prematura de microservicios. Recomiendo **monorepo + modular monolith**, con procesos independientes solo donde realmente aportan aislamiento:

```text
Renfe GTFS / GTFS-RT
        │
        ▼
Python Collector
        │
        ├── raw immutable payload metadata
        │
        ▼
Normalizer + Quality Layer
        │
        ├── PostgreSQL / PostGIS  ← estado operativo + hot history
        │
        └── R2 Parquet            ← histórico frío
                        │
                        ▼
                  DuckDB + dbt
                        │
             métricas / agregados
                        │
               FastAPI propia
                 │           │
                 ▼           ▼
            React App    snapshots CDN
```

La razón para mantener PostgreSQL/PostGIS es buena: tendremos entidades relacionales, consultas temporales y geometría espacial. Supabase soporta actualmente PostGIS y su plan gratuito incluye 500 MB; Pro parte de 25 USD/mes y añade 8 GB de disco y backups diarios. citeturn471992search1turn471992search3

R2 encaja extraordinariamente bien con nuestro histórico. Cloudflare cobra actualmente 0,015 USD por GB-mes en Standard, incluye 10 GB-mes y 1 millón de operaciones Class A + 10 millones Class B mensuales gratuitos, y no cobra egress de R2 a Internet. citeturn471992search0

Si utilizamos el volumen de Valfiguer como referencia conservadora —aproximadamente 11–21 MB comprimidos diarios para mucho más que la C5—, incluso 90 días completos representarían del orden de 1–2 GB comprimidos, por debajo de los 10 GB del free tier de R2. Esa extrapolación es solo una referencia y debe medirse con nuestro colector real. citeturn568214view1turn471992search0

Para FastAPI, durante desarrollo no activaría hosting. En producción inicial Render dispone actualmente de servicios Python y una instancia de 512 MB en torno a 7 USD/mes; existen alternativas, pero no hay ninguna necesidad de decidir proveedor antes de tener benchmarks. citeturn275103search1

### Política de almacenamiento recomendada

No guardaría posiciones detalladas indefinidamente en Postgres.

**PostgreSQL hot:**

```text
current_vehicle_state     → último estado por tren
vehicle_observation       → 7 días
trip_delay_observation    → 30 días
feed_run                   → 90 días
data_quality_event        → 180 días
daily_line_metrics        → permanente
station_daily_metrics     → permanente
```

**R2 / Parquet:**

```text
raw/renfe/vehicle_positions/date=YYYY-MM-DD/hour=HH/
raw/renfe/trip_updates/date=YYYY-MM-DD/hour=HH/

silver/vehicle_observations/date=YYYY-MM-DD/
silver/trip_updates/date=YYYY-MM-DD/

gold/line_daily_metrics/date=YYYY-MM-DD/
gold/station_daily_metrics/date=YYYY-MM-DD/
```

La granularidad recomendada es **Parquet diario particionado por fecha**, no semanal. Un día es la unidad natural de replay, debugging y análisis ferroviario; los ficheros pueden compactarse al terminar el día.

La deduplicación debe basarse en hash canónico de los campos relevantes. Si Renfe devuelve exactamente la misma observación en cinco polls consecutivos, almacenamos una sola observación y aumentamos, si queremos, `seen_count`.

### Modelo relacional inicial

```text
network
  id PK
  code UNIQUE
  name

route
  id PK
  network_id FK
  source_route_id
  short_name
  color
  UNIQUE(network_id, source_route_id)

station
  id PK
  source_stop_id
  name
  geom geography(Point,4326)

service_date
  date PK
  gtfs_version_id FK

trip
  id PK
  service_date
  source_trip_id
  route_id
  direction_id
  start_time
  UNIQUE(service_date, source_trip_id)

trip_stop
  trip_id FK
  stop_sequence
  station_id FK
  scheduled_arrival
  scheduled_departure
  PRIMARY KEY(trip_id, stop_sequence)

vehicle_observation
  id bigint PK
  observed_at timestamptz
  received_at timestamptz
  source_vehicle_id
  source_trip_id
  trip_id FK nullable
  geom geography(Point,4326)
  current_status
  current_stop_sequence
  speed_kmh
  bearing
  quality_flags jsonb
  payload_hash
```

Índices:

```sql
(vehicle_observation observed_at DESC)
(vehicle_observation trip_id, observed_at DESC)
(vehicle_observation source_vehicle_id, observed_at DESC)
GIST(vehicle_observation.geom)
UNIQUE(source_id, payload_hash) -- según contrato de ingestión
```

Todas las timestamps internas deben almacenarse en **UTC con `timestamptz`**. `Europe/Madrid` se aplica en presentación y al interpretar calendarios GTFS. Esto evita errores DST, especialmente en históricos.

### Contratos API propios

No reutilizaría la estructura de Valfiguer ni de Via Península como contrato interno. Creamos nuestros propios contratos versionados:

```text
GET /api/v1/live/vehicles
GET /api/v1/live/vehicles/{vehicle_id}
GET /api/v1/lines
GET /api/v1/lines/{line_id}
GET /api/v1/stations/{station_id}
GET /api/v1/history/lines/{line_id}
GET /api/v1/history/trips/{trip_id}
GET /api/v1/quality/feeds
GET /api/v1/metrics/lines/{line_id}
GET /api/v1/metrics/stations/{station_id}
```

Ejemplo Madrid Pulse:

```json
{
  "vehicle_id": "renfe:cercanias-madrid:...",
  "trip_id": "...",
  "line": "C5",
  "position": {
    "lat": 40.3501,
    "lon": -3.8312,
    "mode": "observed",
    "confidence": 1.0
  },
  "delay": {
    "seconds": 184,
    "coverage": "reported"
  },
  "observation": {
    "reported_at": "...",
    "received_at": "...",
    "age_s": 12
  },
  "quality": {
    "stale": false,
    "flags": []
  }
}
```

## Repositorio, fases y tareas conectadas para Claude Code ↔ Codex

El repositorio sugerido continúa siendo:

```text
madrid-pulse
```

No lo creamos todavía. Cuando apruebes el plan, **MP-001 será literalmente la primera tarea**.

La estructura objetivo:

```text
madrid-pulse/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── package.json
├── docker-compose.yml
├── .env.example
│
├── docs/
│   ├── PLAN.md
│   ├── TASKS.md
│   ├── CHANGELOG.md
│   ├── DECISIONS.md
│   ├── STATUS.md
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACTS.md
│   ├── DATA_QUALITY.md
│   ├── legal/
│   │   ├── DATA_SOURCES.md
│   │   ├── LICENSE_MATRIX.md
│   │   └── ATTRIBUTION.md
│   └── adr/
│       ├── 0001-project-scope-c5.md
│       ├── 0002-data-sources.md
│       ├── 0003-storage-strategy.md
│       ├── 0004-position-model.md
│       ├── 0005-api-contract.md
│       └── 0006-licensing-policy.md
│
├── apps/
│   ├── web/
│   └── api/
│
├── services/
│   ├── collector/
│   ├── normalizer/
│   └── snapshotter/
│
├── packages/
│   ├── contracts/
│   ├── gtfs/
│   ├── geo/
│   └── quality/
│
├── analytics/
│   ├── dbt/
│   └── duckdb/
│
├── infra/
│   ├── docker/
│   ├── cloudflare/
│   └── migrations/
│
├── tests/
│   ├── fixtures/
│   ├── integration/
│   └── e2e/
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

Las primeras tareas deben formar una cadena; ninguna tarea puede declararse completa sin producir una evidencia verificable.

| ID | Depende | Ejecuta | Revisa | Entregable / DoD | Prioridad |
|---|---|---|---|---|---|
| **MP-001** Bootstrap documental del repo | — | **Claude Code** | **Codex** | repo, `PLAN`, `TASKS`, `CHANGELOG`, `DECISIONS`, `STATUS`, ADR dir, AGENTS | P0 |
| **MP-002** Matriz de fuentes/licencias | MP-001 | **Codex** | **Claude Code** | Renfe/CRTM/OSM documentados con atribución y restricciones | P0 |
| **MP-003** Probe real C5 | MP-002 | **Claude Code** | **Codex** | captura controlada GTFS + VP + TU + alerts; esquema real documentado | P0 |
| **MP-004** Fixtures reproducibles | MP-003 | **Codex** | **Claude Code** | fixtures anonimizados/congelados + hashes + tests de parseo | P0 |
| **MP-005** Contrato canónico interno | MP-004 | **Claude Code** | **Codex** | Pydantic/JSON Schema para vehicle/trip/feed health | P0 |
| **MP-006** Postgres/PostGIS schema v1 | MP-005 | **Codex** | **Claude Code** | migraciones, constraints, índices, rollback | P0 |
| **MP-007** Collector idempotente | MP-005,006 | **Claude Code** | **Codex** | polling, retries, timeout, hashing, dedupe, metrics | P0 |
| **MP-008** Quality engine | MP-007 | **Codex** | **Claude Code** | stale, speed anomalies, missing IDs, duplicate snapshot, clock anomalies | P0 |
| **MP-009** Historical exporter | MP-007,008 | **Claude Code** | **Codex** | Parquet diario particionado + replay test | P1 |
| **MP-010** GTFS topology C5 | MP-004 | **Codex** | **Claude Code** | estaciones, trips, shapes y validación de recorrido | P0 |
| **MP-011** OSM rail geometry prototype | MP-010 | **Claude Code** | **Codex** | geometría C5 + atribución + casos ambiguos | P1 |
| **MP-012** Motion engine v1 | MP-008,010,011 | **Codex** | **Claude Code** | observed/estimated/stale/scheduled + tests deterministas | P1 |
| **MP-013** FastAPI v1 | MP-005,007,012 | **Claude Code** | **Codex** | OpenAPI, live vehicles, feed health, line/station endpoints | P1 |
| **MP-014** React/MapLibre C5 | MP-013 | **Codex** | **Claude Code** | mapa funcional, movimiento + visualización de incertidumbre | P1 |
| **MP-015** E2E + readiness MVP | MP-009,012,013,014 | **Claude Code** | **Codex** | replay completo, CI verde, checklist MVP y ADRs actualizados | P1 |

El patrón de trabajo será siempre:

```text
Issue
  ↓
agente ejecutor
  ↓
tests locales
  ↓
PR
  ↓
agente contrario revisa
  ↓
correcciones
  ↓
CI
  ↓
evidencia en TASKS + STATUS
  ↓
merge
```

**Nunca Claude Code revisa su propio cierre final y nunca Codex revisa el suyo.**

Via Península demuestra además el valor de ejecutar build, typecheck, tests, smoke tests y comparaciones reproducibles antes de publicar cambios; ese enfoque merece adoptarse como disciplina aunque implementemos herramientas diferentes. citeturn103999view2

GitHub Actions es gratuito actualmente para runners estándar en repositorios públicos; para repos privados existe una cuota mensual incluida según plan. citeturn471992search5turn471992search6

Las fases quedan:

```text
Fase 0   Gobierno y documentación
          ↓
Fase 1   Validación real de datos C5
          ↓
Fase 2   Contratos + DB + collector
          ↓
Fase 3   Calidad + histórico
          ↓
Fase 4   Geometría + movimiento
          ↓
Fase 5   FastAPI
          ↓
Fase 6   Frontend Live
          ↓
Fase 7   History / Explore
          ↓
Fase 8   Hardening + producción
          ↓
Fase 9   Madrid completo
          ↓
Fase 10  España
```

El **MVP no debe empezar por React**. La aplicación visual solo se desarrolla cuando podamos demostrar que el colector, contratos y replay funcionan con datos reales.

## Operación en Orca, servicios, prompts maestros y decisiones abiertas

### Servicios que NO activaría todavía

En este momento no hace falta pagar nada. Podemos desarrollar MP-001 a MP-006 completamente en local.

Cuando aprobemos y empecemos:

```text
AHORA
GitHub
Orca IDE
Claude Code
Codex
Docker Desktop / Docker Engine
Python
Node
PostgreSQL + PostGIS local
DuckDB

DESPUÉS DE VALIDAR COLLECTOR
Cloudflare account
R2 bucket

ANTES DE PRODUCCIÓN
Supabase Pro o PostgreSQL equivalente
Render / Railway / Fly / equivalente para FastAPI/collector
dominio
monitorización
```

Con los precios actuales, un MVP público razonable puede mantenerse aproximadamente en el rango **25–40 USD/mes** una vez se decida operar producción 24/7: unos 25 USD de Postgres gestionado, aproximadamente 7 USD de un pequeño servicio Python y potencialmente 0 USD de R2 mientras permanezca dentro del free tier. Es una estimación, no un presupuesto garantizado. citeturn471992search3turn471992search0turn275103search1

### Prompt maestro para Claude Code en Orca

```text
PROJECT: Madrid Pulse

ROLE:
You are the implementation agent Claude Code working inside Orca IDE.

IMPORTANT:
Orca is the IDE, not an agent.
The two development agents are:
- Anthropic Claude Code
- OpenAI Codex

WORKFLOW:
1. Read:
   docs/PLAN.md
   docs/TASKS.md
   docs/STATUS.md
   docs/DECISIONS.md
   docs/adr/*
2. Work ONLY on the assigned task ID.
3. Inspect existing code before modifying anything.
4. Do not change architecture without proposing an ADR.
5. Never invent Renfe fields or API behaviour.
6. Preserve source attribution and licensing metadata.
7. Add tests for every parsing or transformation rule.
8. Run lint, typecheck, unit and integration tests.
9. Update TASKS.md and STATUS.md with evidence.
10. Create a concise review handoff for Codex.

REVIEW:
Codex is the independent reviewer.
Do not mark the task DONE until Codex review is resolved.

DATA PRINCIPLES:
- UTC internally.
- Europe/Madrid only at presentation/service-calendar boundaries.
- ingestion must be idempotent.
- raw source != normalized data.
- observed position != estimated position.
- missing data must never be represented as zero.
- punctuality metrics must expose coverage.

LICENSE:
Do not copy AGPL implementation from Via Península.
Concepts and public standards may be reimplemented independently.
```

### Prompt maestro para Codex en Orca

```text
PROJECT: Madrid Pulse

ROLE:
You are OpenAI Codex working inside Orca IDE as implementation
agent or independent reviewer depending on the task assignment.

IMPORTANT:
Orca is the IDE, not an agent.
The two development agents are:
- Anthropic Claude Code
- OpenAI Codex

WHEN IMPLEMENTING:
Follow docs/PLAN.md and the assigned MP task exactly.
Produce tests and evidence before requesting review.

WHEN REVIEWING CLAUDE CODE:
Do not rewrite blindly.
Audit:
- correctness
- data contract compliance
- idempotency
- timestamps
- edge cases
- licence constraints
- migrations
- test coverage
- performance
- security
- documentation consistency

Attempt to break the implementation using fixtures and boundary cases.

A task is APPROVED only when:
- acceptance criteria pass,
- tests pass,
- documentation matches implementation,
- no unresolved licence or data-quality issue exists.

Record the review result in the task evidence.
```

### Política Git/PR

```text
main
 └── protected

feature branches:
mp-007-collector
mp-008-quality-engine
...

PR title:
[MP-007] Build idempotent Renfe collector

required:
✓ tests
✓ lint
✓ typecheck
✓ migration validation
✓ licence/data-source check where relevant
✓ reviewer agent approval
```

Los commits deberían referenciar siempre la tarea:

```text
feat(collector): add Renfe vehicle polling [MP-007]
test(collector): add duplicate snapshot fixture [MP-007]
docs(status): record collector validation [MP-007]
```

### Go / no-go antes de comenzar

**GO confirmado** para arquitectura, fuentes abiertas, C5 como piloto, almacenamiento híbrido y frontend MapLibre.

**GO condicionado** para el motor de movimiento: el patrón es viable, pero nuestra implementación deberá probarse contra observaciones reales antes de decidir smoothing y thresholds.

**GO condicionado** para histórico de retrasos: debe incluir métrica de cobertura y calidad.

**NO-GO** para ocupación en tiempo real inferida. Solo se mostrará si aparece una fuente legítima o una futura capa colaborativa explícitamente diferenciada.

**NO-GO** para copiar código AGPL de Via Península dentro de un producto que queramos licenciar de forma incompatible. Via Península puede utilizarse como material de estudio; su implementación solo puede reutilizarse respetando AGPL. citeturn168389view0turn597929search0

**NO-GO** para almacenar indefinidamente cada polling de posición en PostgreSQL. El modelo hot + Parquet diario + agregados permanentes es más sostenible.

Las únicas preguntas que quedan abiertas y **no bloquean MP-001** son la licencia que quieres para nuestro código original —MIT, Apache-2.0 u otra—; si Madrid Pulse será inicialmente público o privado en GitHub; y si quieres que el histórico detallado sea permanente en R2 o tenga una retención inicial de 12/24 meses. Esas decisiones pueden registrarse posteriormente mediante ADR sin impedir que creemos primero la estructura documental y el repositorio.

La primera acción cuando demos comienzo en Orca será, por tanto, exactamente ésta:

```text
MP-001
Crear madrid-pulse y, antes de escribir código de producto, generar:

docs/PLAN.md
docs/TASKS.md
docs/CHANGELOG.md
docs/DECISIONS.md
docs/STATUS.md
docs/adr/
AGENTS.md
README.md

Ejecutor: Claude Code
Revisor: Codex
Entorno: Orca IDE
```

Ese es el punto correcto desde el que empezar Madrid Pulse.