# ADR-0014: Contrato temporal de presentación y snapshot coherente

- **Estado:** `Propuesto` — aplicado de forma provisional bajo [ADR-0007](0007-autonomy-model.md). No lo promueve el ejecutor ni el revisor: solo el propietario del repositorio (`AGENTS.md`, regla 8), normalmente en el cierre de Hito 3.
- **Fecha:** 2026-11-22
- **Decisores:** Claude Opus como ejecutor de MP-019 (escalado por política de modelo de Hito 2: decisión arquitectónica de alto impacto); revisión cruzada completada y aprobada por OpenAI Codex el 2026-11-22; promoción pendiente del propietario (Pedro Matute).

## Contexto

`docs/hitos/hito-03/MEJORAS-PRODUCTO-VALIDADAS.md` (sección MP-019) exige
registrar un ADR **antes** de implementar, comparando tres formas posibles del
contrato temporal entre backend y cliente, y elegir "la alternativa más simple
que preserve reglas, consistencia y presupuesto medido".

El punto de partida real, no hipotético:

- `packages/movement` (MP-012, [ADR-0012](0012-movement-package-boundary.md))
  produce `MovementPosition` con cuatro estados (`observed / estimated / stale /
  scheduled`), confianza, edad, fuente y anomalías. Mantiene **fija** la
  coordenada de la última observación mientras `age_s <= observed_max_age_s`
  (60 s por defecto, DEC-010). Con la cadencia real del feed (~20–22 s, MP-003),
  eso significa que un cliente que consulte la API cada 20 s recibe tres veces
  la misma coordenada antes de que el motor empiece a estimar: el tren se ve
  quieto y luego salta.
- `packages/geo` (MP-018) ya separa `raw` de `map_matched` por patrón/sentido
  (`PositionMatch`), con `progress_m`, `distance_from_raw_m` y
  `geometry_version`, y declara honestamente que 72 de 103 patrones siguen
  `pending` (sin geometría descargada).
- `docs/hitos/hito-03/ANEXO-CRITICO-POSICION-Y-RELOJ.md` exige una tercera
  coordenada, `rendered`, con `rendering_method` de seis valores
  (`anchor`, `interpolated_between_known_anchors`,
  `extrapolated_from_last_anchor`, `schedule_only`, `stale_frozen`,
  `unlocated`), `display_at`, `valid_until`, `last_confirmed_at` y
  `calculated_at`, y prohíbe expresamente escribir un frame de cliente como
  observación de origen o llamar `interpolated` a una extrapolación sin ancla
  futura.
- El mismo anexo y `MEJORAS-PRODUCTO-VALIDADAS.md` prohíben tres cosas
  concretas: imponer un array de puntos futuros, abrir un endpoint por tren, y
  mantener una segunda implementación divergente del motor.

La decisión no es "cómo animar en MP-020": es **qué publica el backend para que
el cliente pueda presentar movimiento continuo sin que nadie fabrique una
observación**.

## Decisión

Se adopta la **alternativa 1** del encargo —progreso temporal compacto
calculado por el backend— materializada como una **envolvente de progreso**
(`ProgressEnvelope`) por circulación, y se **extiende** `packages/movement` de
forma aditiva en vez de sustituirlo o duplicarlo.

### 1. Una sola regla de movimiento, en un solo lenguaje

`packages/movement/rendering.py` (nuevo, dentro del paquete existente) traduce
el `MovementPosition` que ya calcula el motor en una `RenderedPosition`. Reutiliza
`TripSchedule`, `service_seconds` y `MovementThresholds` de MP-012; no
reimplementa map-matching, resolución de `route_id`, horario ni límites
físicos. El motor sigue siendo la única autoridad sobre qué observación es
utilizable y cuál es el ancla.

### 2. La envolvente, no una trayectoria

Por circulación con corredor validado el backend publica:

```text
progress_envelope = {
  reference_at,              -- instante del ancla realmente usada
  progress_m_at_reference,   -- progreso dirigido del ancla sobre el patrón
  speed_mps,                 -- avance permitido, derivado del horario y acotado
  max_progress_m,            -- tope dentro del horizonte (fin de horario/corredor)
  horizon_s,                 -- cuánto tiempo es lícito avanzar
  dwell_until                -- NULL salvo espera en parada realmente programada
}
```

El cliente evalúa una única expresión monótona y acotada:

```text
progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - reference_at),
                  max_progress_m)      para reference_at <= t <= valid_until
```

y la convierte a coordenada **sobre la longitud de arco del patrón** usando la
geometría que ya recibió del catálogo cacheable. No hay array de puntos
futuros, no hay endpoint por tren, y la expresión no es un motor: no decide
anclas, no filtra saltos, no resuelve horarios. `speed_mps = 0` con
`dwell_until` poblado es una espera declarada, no un dato ausente.

### 3. Seis métodos de presentación, cada uno con su procedencia

`rendering_method` describe cómo se obtuvo la coordenada publicada en
`display_at`, no el estado del feed:

| Método | Cuándo |
|---|---|
| `anchor` | La coordenada publicada **es** el ancla (sin avance aplicado: `display_at == reference_at`, o la envolvente da avance cero porque el horario no lo permite todavía). |
| `interpolated_between_known_anchors` | `display_at` cae entre dos anclas reales (replay/búfer con retraso de presentación declarado). Jamás en directo. |
| `extrapolated_from_last_anchor` | Hay ancla pasada y no hay ancla futura: avance acotado por horario + topología + límites físicos. Es el caso normal del directo. |
| `schedule_only` | No hay observación utilizable: posición derivada solo del horario (equivale a `PositionMode.SCHEDULED`). |
| `stale_frozen` | El ancla superó `stale_after_s`: se congela en el ancla, sin avance, con confianza decaída. |
| `unlocated` | No se puede publicar ninguna coordenada defendible (sin `raw` y sin horario resoluble, o patrón sin geometría y sin `raw`). |

`position.mode` (`observed/estimated/stale/scheduled`) **se conserva sin
cambios** por compatibilidad, como exige el anexo; `rendered` es aditivo. Ambos
derivan del mismo ancla y lo publican (`rendered.anchor_observed_at`), de modo
que un consumidor puede comprobar que no se contradicen.

### 4. `raw`, `map_matched` y `rendered` son tres bloques distintos

`map_matched` se publica **solo** cuando
`PositionMatch.resolution == map_matched` y existe `projection` real. El
`geometry_version` que `packages.geo.catalog.match_position` devuelve también en
los fallbacks `RAW`/`UNLOCATED` (nota no bloqueante que MP-018 dejó abierta
para esta tarea) se publica en esos casos como
`geometry_candidate_version`, un campo distinto: versión de la geometría
candidata/contextual, nunca la versión de una proyección que no ocurrió.

### 5. Identidad de snapshot vs revisión ordenable

`snapshot_id` es un hash de contenido: **identidad, no secuencia**, y así se
documenta. La ordenación usa un bloque explícito:

```text
revision = { scope, scope_source, sequence, generated_at, tiebreak }
```

`sequence` es `max(source_ingestion_run.id)` considerado — monótona de verdad
(secuencia de PostgreSQL), sobrevive a reinicios del proceso de API y **no
rejuvenece** cuando el colector se detiene. `scope` es el
`system_identifier` del clúster PostgreSQL (`pg_control_system()`), con
degradación declarada a `pgdb:<datname>:<oid>` si el rol no puede leerlo.
Comparar `sequence` entre scopes distintos está prohibido por contrato: ante
scope distinto el cliente compara `generated_at` y desempata con `tiebreak`,
tratando el cambio como discontinuidad, no como rebobinado.

### 6. Catálogo cacheable separado del snapshot operativo

`GET /api/v1/catalog` publica líneas, patrones, estaciones y cobertura
geométrica, versionado por `gtfs_version` + `geometry_catalog_version`, con
`ETag` y `304`. `GET /api/v1/snapshot` publica solo el estado operativo, con
`Cache-Control: no-store` para que nada viejo se rotule como nuevo. El snapshot
referencia el catálogo por versión (`catalog_ref`), no lo reenvía.

### 7. ETA con procedencia, nunca fabricada

`eta_method` distingue `schedule` (horario planificado, sin dato de operador),
`operator_delay_on_schedule` (horario + `delay` del `trip_update`, con su
`observed_at` y su edad) y `unavailable` (con causa explícita:
`trip_canceled`, `already_passed`, `passed_or_skipped_per_operator_next_stop`,
`schedule_time_missing`). No se introduce ningún modelo predictivo propio. La
aplicación de un `delay` de nivel viaje a todas las paradas se publica marcada
como aproximación (`trip_level_delay_applied_to_all_stops`), nunca en silencio.

### 8. El tablero se calcula con servicios y calendario

`GET /api/v1/stations/{station_id}/board` parte de
`packages.gtfs.catalog.scheduled_trip_instances_for_date` (calendario +
excepciones + `stop_times`, incluidas horas `24:xx`) y cruza con observaciones y
`trip_update`. **No** se construye con "trenes cercanos" por proximidad
geográfica.

## Alternativas consideradas

### Alternativa 2 — Horario y anclas normalizados con cálculo puro compartido o equivalencia verificada por replay

El backend publicaría horario normalizado y anclas, y el cliente recalcularía
la posición con "el mismo cálculo puro".

**Descartada.** El cliente de este proyecto es TypeScript y el motor es Python.
"Cálculo puro compartido" exigiría o compilar Python a WASM (dependencia y
presupuesto nuevos, no autorizados en este hito) o escribir una segunda
implementación en TypeScript y demostrar su equivalencia por replay. Eso es
exactamente la "segunda implementación divergente" que el encargo prohíbe: la
equivalencia habría que mantenerla viva en cada cambio de umbral, de
`TripSchedule` o de límite físico, y el replay solo prueba las secuencias
incluidas en él. Además duplicaría en el cliente reglas que no son de
presentación (qué observación es utilizable, cómo se filtra un salto de 787 km/h
del feed real documentado en DEC-010), que es el núcleo de MP-012. La ganancia
—un payload algo menor— no compensa.

### Alternativa 3 — Interpolación con búfer entre anclas conocidas, declarando retraso de presentación

El cliente mantendría un búfer de dos anclas y dibujaría siempre entre ellas,
declarando el retraso de presentación.

**Descartada como contrato principal, conservada como caso explícito.** Es la
única forma honesta de decir `interpolated_between_known_anchors`, y el
contrato la soporta (método 2 de la tabla) para replay y para un cliente que
elija retrasar la presentación. Pero no puede ser *el* contrato del directo:
exige un ancla futura que en vivo no existe, así que impondría un retraso de
presentación de al menos un intervalo de sondeo (~20 s reales medidos en
MP-003) a todos los usuarios, y en cuanto el feed se detiene el búfer se queda
sin segunda ancla y hay que caer a extrapolación de todas formas — es decir, el
caso difícil no desaparece, solo se posterga. El anexo es explícito: "En directo
sin ancla futura, el avance es estimación; no denominarlo interpolación
observada".

### Alternativa 4 (no planteada en el encargo, evaluada y descartada) — Subir los umbrales del motor

Bastaría con bajar `observed_max_age_s` a 0 para que el motor estimara siempre.

**Descartada.** Cambia la semántica de `position.mode` publicada y ya
consumida: nada quedaría nunca `observed`, rompiendo DEC-010/ADR-0004 y el
contrato v1 sin necesidad. La envolvente consigue presentación continua
*conservando* el significado de los cuatro estados, que es lo que pide el anexo
("campos aditivos de procedencia/rendering para quitar ambigüedad").

### Alternativa 5 (evaluada y descartada) — Un segundo motor de presentación independiente

Escribir en `apps/api/` una capa de movimiento propia, desacoplada de MP-012.

**Descartada** por el mismo motivo que la alternativa 2, y porque violaría
[ADR-0012](0012-movement-package-boundary.md): la lógica de movimiento no vive
en la capa HTTP.

## Consecuencias

- `packages/movement` crece de forma **aditiva** (`rendering.py`, y una caché de
  `TripSchedule` opcional e inyectable en `MovementEngine` por coste medido).
  `engine.py` y `model.py` conservan su contrato; ningún estado ni valor
  existente cambia de significado.
- El contrato `/api/v1` **no rompe compatibilidad**: `VehicleOut` conserva todos
  sus campos y añade bloques nullable; los endpoints nuevos son nuevos. No hace
  falta `/api/v2` (ADR-0005).
- El cliente de MP-020 necesita la geometría del patrón para convertir progreso
  en coordenada: el catálogo cacheable deja de ser una comodidad y pasa a ser
  parte del contrato de movimiento. Un patrón sin geometría validada **no**
  obtiene envolvente: se publica `raw` etiquetado o `unlocated`, nunca un avance
  sobre un corredor ajeno.
- La envolvente es monótona y acotada por construcción, así que un cliente no
  puede hacer retroceder ni acelerar ficticiamente un tren evaluándola; el
  horizonte (`valid_until`) obliga a congelar en vez de seguir inventando.
- La coordenada `rendered` **nunca** se archiva como observación Renfe: el
  snapshot es de solo lectura y el histórico (MP-021) sigue leyendo
  `vehicle_position_observation`, no el snapshot.
- Queda explícitamente fuera de alcance, documentado y no silenciado: el
  `stop_time_update` por parada (y por tanto la evidencia directa de `SKIPPED`
  por parada) **no** está persistido en el modelo canónico — solo
  `next_stop_id`, el primer no-`SKIPPED`. El tablero declara esa limitación y
  expone `operator_next_stop_id` con la posición relativa de cada parada, sin
  afirmar que una parada concreta fue omitida.
