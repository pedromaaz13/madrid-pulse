# ADR-0014 · Enmienda 1: modelo de estado de parada, horizonte por tramo y revisión coherente

- **Estado:** `Propuesto`. **No** lo promueven ni el ejecutor ni el revisor: lo decide el propietario del repositorio (`AGENTS.md`, regla 8). Además, es **gate humano antes de cualquier código de MP-025a** (`docs/H4_MP_MAPPING.md`).
- **Fecha:** 2026-11-25.
- **Tarea:** MP-024 (H4-00).
- **Ejecutor:** Claude `claude-opus-5-5` · high.
- **Revisor:** Codex `gpt-6.2-astra` · high, proveedor contrario. Revisión pendiente.
- **Enmienda a:** [ADR-0014](0014-snapshot-and-temporal-contract.md), que sigue `Propuesto`. **Sustituye** el texto de su §2 (fórmula y semántica de la envolvente) y **enmienda** §3 (métodos de presentación) y §5 (revisión). El resto de ADR-0014 (§1, §4, §6–§8, alternativas) queda intacto.
- **Evidencia:** [`docs/evidence/mp-024/`](../evidence/mp-024/README.md). Contiene el arnés offline `stop_state_comparison.py`, la salida completa `output.txt` y `results.json`, y se ejecutó sobre los cortes congelados con SHA-256 verificado.

**Por qué es una enmienda y no ADR-0016.** El defecto está en el contrato temporal que ADR-0014 define: la fórmula de §2, la semántica de `stale_frozen` de §3 y la promesa de §5. No hay una decisión de arquitectura nueva e independiente. ADR-0014 aún no está `Aceptado`, así que lo coherente es que el propietario promueva **un solo contrato corregido** (ADR-0014 + esta enmienda) en vez de un ADR aceptado con un texto que otro contradice (FR-31). La decisión sobre el grafo de segmentos OSM, que `NEXT_STEPS_PROPOSAL.md` sitúa «en H4-00 o ADR propio», **no** entra aquí: es de geometría (MP-029) y no la necesita ninguna regla de esta enmienda.

---

## 1. Contexto

Todas las referencias son al registro [`FINDINGS_REGISTER.md`](../audits/hito-03/FINDINGS_REGISTER.md); las cifras se recalculan en `docs/evidence/mp-024/output.txt` con producción `beb9434`.

| FR | Sev. | Hallazgo | Cifra en `beb9434` (este arnés) |
|---|---|---|---|
| FR-01 (S1-a) | **P0** | La envolvente pone en marcha circulaciones que el operador declara `STOPPED_AT` | 28/28 con avance: 17 pre-salida, 4 salidas retrasadas en origen, 7 intermedias. 25/25 con GPS idéntico entre cortes |
| FR-03 (S1) | P1 | La espera programada solo se expresa en una ventana de ~1 m (tolerancia de 1,0 m + guarda que recorta el lado positivo) | `19656` avanza 661,1 m a 30 s y 1 322,2 m a 60 s |
| FR-04 (S1) | P1 | Horizonte de 180 s heredado de DEC-010 sin recalibrar; la envolvente atraviesa estaciones | 29/44 cruzan ≥ 1 parada; 20/44 cruzan una parada a más de 50 m por delante |
| FR-05 (S1) | P1 | Al caducar, el símbolo retrocede de golpe y el aviso desaparece porque depende de `valid_until` | 25/25 en ventana, p50 2 357,9 m, máx 3 959,2 m |
| FR-07 | P1 | `build_snapshot()` puede publicar `revision.sequence` nueva sin su vehículo (contradice §5) | Reproducido por AUD-06 con PostgreSQL desechable; **no** se reejecuta aquí |
| FR-26 | P2 | `_envelope` mezcla reloj de pared y segundos reales | Sintético 2027-03-28: 8 000,0 m frente a 3 000,0 m reales. 2027-10-31: 0,0 m frente a 333,3 m |
| FR-27 | P2 | `position` y `rendered` publican dos coordenadas del mismo instante | Máx 429,5 m entre 61 y 179 s |
| FR-31 (S1) | P2 | §2 publica la fórmula sin `dwell_until` y afirma «`speed_mps = 0` con `dwell_until` = espera» | Las otras cuatro superficies (`rendering.py:71`, `schemas.py:259`, `DATA_CONTRACTS.md:193`, `movement.ts:9`) usan `t0 = dwell_until or reference_at` |
| FR-33 (S1) | P2 | `stop_time_update` por parada se descarta al normalizar | No medible con el modelo canónico actual |

Relacionados que la enmienda cubre porque comparten causa o superficie:
- **FR-06:** `anchor` sin separar por `coordinate_space`.
- **FR-32:** `CANCELED` dibujada como en marcha.

**Causa raíz común de S1** (`FINDINGS_REGISTER.md` §2.3): la envolvente deduce el estado del tren respecto de las paradas **solo** por progreso geométrico e interpolación del horario. Ignora el estado que publica el operador y la ventana temporal del viaje.

## 2. Hechos medidos que condicionan la decisión

La auditoría recomienda A. El encargo pide comprobar si de verdad lo es, y la comprobación sobre el corte `1533` (44 circulaciones con cadena completa) **matiza la formulación de la auditoría en dos puntos**:

1. **`current_status`/`current_stop_id` están en 44/44 y la parada pertenece al viaje en 44/44.** El dato existe y es utilizable.
2. **`IN_TRANSIT_TO X` no significa «va hacia X» en este feed.** En **4/8** casos `X` queda **más de 1 km por detrás** del ancla: `20277` a 4 288,5 m; `20281`, `20845` y `20846` entre 1 848,9 y 3 234,5 m. Si se usara `current_stop_id` como tope de avance, como en la lectura de la especificación GTFS-RT, se **retendría a trenes en marcha**. **Corrección 1:** el tope por tramo sale del horario (siguiente parada por delante del ancla) y `current_stop_id` solo se usa para las retenciones (`STOPPED_AT`, `INCOMING_AT` en zona). La semántica en vivo es `UNVERIFIED` (MP-028).
3. **`19656` está `post_llegada` (+141 s) y en marcha a 75,0 km/h** (`INCOMING_AT 35002`, −5,38 m). **Corrección 2:** la «ventana del viaje» sirve **antes de la salida** (por tiempo) y **en el terminal** (por posición), **nunca** después de la llegada programada por tiempo. Retener por tiempo tras la llegada congelaría trenes retrasados que siguen circulando.
4. **Coste de A:** 3 circulaciones (`19671`, `20284`, `20836`) estaban `STOPPED_AT` en `1532` y salieron antes de `1533`, entre 1 860,2 y 2 424,5 m en 77 s. A las retiene hasta la siguiente observación. El error está acotado por la cadencia del feed: 77 s en el kit, ~20 s en vivo (MP-003). En vivo es `UNVERIFIED`.

Con esas dos correcciones, **A sigue siendo la recomendada**, y es la única que cumple 11/11 criterios medibles.

## 3. Alternativas comparadas

Todas se aplican a las mismas 44 circulaciones y 44 pares `1532→1533`, con el horizonte real de producción (180 s desde el ancla, `rendering.py:279,346`) y la constante τ = 50 m del arnés. Detalle, definiciones y sensibilidad en `docs/evidence/mp-024/README.md`.

| Criterio (cortes reales) | BASE `beb9434` | **A** operador | B1 offset ±600 s | B2 B1 + pre-salida | C segmentos (Dmin 30 s) | D tolerancia 50 m |
|---|---|---|---|---|---|---|
| `STOPPED_AT` con GPS idéntico y avance | 25/25 | **0/25** | 21/25 | 10/25 | 10/25 | 25/25 |
| Pre-salida con avance | 17/17 | **0/17** | 13/17 | 2/17 | 2/17 | 17/17 |
| Salida retrasada en origen con avance | 4/4 | **0/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| `STOPPED_AT` intermedia con avance | 7/7 | **0/7** | 7/7 | 7/7 | 7/7 | 7/7 |
| Cruzan una parada > τ antes de `valid_until` | 20/44 | **0/44** | 22/44 | 20/44 | 0/44 | 20/44 |
| `19656`: avance a 30 s | 661,1 m | **0 m** | 661,1 m | 661,1 m | 0 m | 661,1 m |
| Error a 77 s (p50 / p90 / máx) | 1 229 / 1 732 / 3 274 m | 0 / 1 524 / 3 274 m | 951 / 2 216 / 3 422 m | 876 / 1 921 / 3 422 m | 570 / 1 338 / 3 669 m | = BASE |
| Sobreavance > 100 m a 77 s | 32 | **2** | 24 | 18 | 15 | 32 |
| Avance legítimo perdido: `IN_TRANSIT_TO`/`INCOMING_AT` | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Avance legítimo perdido: cualquier estado | 0 | **3** (salidas tras `STOPPED_AT`) | 0 | 0 | 0 | 0 |
| Criterios de aceptación (§8) PASS | 1/11 | **11/11** | 2/11 | 2/11 | 7/11 | 2/11 |

Casos sintéticos sobre el horario real de `1023V19656C5`:

| Caso | BASE | **A** | B1 | B2 | C | D |
|---|---|---|---|---|---|---|
| Salida retrasada | FAIL (2 811,3 m) | **PASS** | FAIL | FAIL | FAIL (2 019,9 m) | FAIL |
| Intermedia con espera (+5,38 m) | FAIL (417,2 m a 30 s) | **PASS** | FAIL | FAIL | PASS | FAIL (417,2 m) |
| Intermedia sin espera programada | FAIL (2 364,5 m) | **PASS** | FAIL | FAIL | FAIL (1 969,8 m) | FAIL |

El resto de sintéticos está en el README.

- **A — estado de parada del operador + ventana del viaje + tope por tramo.** **Recomendada.** Es la única que retiene las 28 `STOPPED_AT` sin perder ningún avance `IN_TRANSIT_TO`/`INCOMING_AT`. Solo necesita τ ≥ 5,38 m para `19656` y ≥ 38 m para que las 28 sean coherentes; entre 40 y 100 m el resultado no cambia (sensibilidad). Coste: retiene hasta la siguiente observación a un tren que sale justo después de declararse parado (3/44 en el kit).
- **B — acotar `temporal_offset_s`** (B1: ±`operator_delay_max_age_s`, `apps/api/config.py:59`; B2: B1 + retención hasta la primera salida). **Descartada.** B1 apenas corrige (21/25) y **empeora** el peor caso: al desplazar el horario satura los 160 km/h y deja 8 000 m de retroceso al caducar y 3 422 m de error. B2 cubre la pre-salida, pero deja las 4 salidas retrasadas y las 7 intermedias. Son las 11/28 que ya anticipó `AUDIT_EXECUTIVE_DECISION.md` §1.
- **C — segmentos hold/travel por tramo, derivados solo del horario.** **Descartada como modelo principal; se conserva como degradación** (R8) cuando falta el estado del operador o es incoherente. Resuelve `19656` y los cruces, pero sin el operador no distingue un tren parado de uno que pasa por la zona de parada. Con Dmin ≤ 60 s deja las 4 + 7 en marcha; con Dmin = 180 s las retiene, pero pierde **7/9** avances legítimos.
- **D — subir la tolerancia** (contrafactual B de AUD-04). **Descartada.** Con 50 m de tolerancia **todas** las métricas son idénticas a la línea base: la espera se detecta, pero la guarda `anchor_at < candidate` (`rendering.py:192`) la descarta (`19656` sigue en 661,1 m). Además no toca la pre-salida, las salidas retrasadas ni las intermedias sin espera programada (el 90,1 % de las paradas).

## 4. Decisión propuesta

Se adopta **A**, con C como degradación declarada, más las reglas transversales R-CANCEL, R-STALE, R-DST, R-REPROJ, R-ONECOORD y R-SPACE.

Todo vive en la traducción de MP-019 (`packages/movement/rendering.py`/`schedule.py`) y en su consumo (`apps/api/snapshot.py`, `apps/web/src/domain/movement.ts`). `engine.py` sigue siendo la única autoridad sobre qué observación es utilizable y cuál es el ancla.

### 4.1 Entradas de la regla

Para cada circulación con corredor validado:
- **Ancla:** `observed_at` y progreso dirigido, del motor.
- **Estado del operador de la misma observación:** `current_status`, `current_stop_id`. Ya están en `VehiclePositionObservation` (ADR-0009).
- **Paradas del viaje proyectadas con la misma primitiva que el horario:** `stop_id`, progreso, `arrival_s`, `departure_s`.
- **`schedule_relationship`** de la última `trip_update` del viaje.
- **Umbrales de §6.**

**Zona de parada de X** = |progreso(X) − progreso(ancla)| ≤ `stop_zone_radius_m`. La pertenencia a una parada se decide por **`stop_id` + zona**, nunca por la coincidencia ±1 m con un tramo plano del horario. Eso deroga el uso de `dwell_end_seconds(tolerance_m=1.0)` para presentación.

### 4.2 Reglas, en orden de precedencia

| Regla | Situación | Envolvente publicada | `hold_reason` |
|---|---|---|---|
| **R-CANCEL** | `schedule_relationship = CANCELED` en una `trip_update` vigente (edad ≤ `cancel_max_age_s`) | Retención abierta: `speed_mps = 0`, `max_progress_m` = ancla. Coordenada = ancla real, **nunca se oculta el tren** (AUD-04 (C) descartado) | `trip_canceled` |
| **R1** · `STOPPED_AT` coherente | `STOPPED_AT X`, X del viaje y ancla en zona de X | Retención abierta hasta nueva observación. **Prevalece** sobre la hora programada de salida | `operator_stopped_at` |
| **R2** · antes de salida | Ancla anterior a la primera salida programada (instante real con `service_day_instant`) y no aplica R1 | `dwell_until` = salida programada si cae antes de `valid_until`, con avance después según R5. Si no, retención abierta | `before_first_departure` |
| **R3** · salida retrasada | Ancla posterior a la salida programada y operador `STOPPED_AT` en origen | Es R1 (no hay regla temporal). Retención hasta que el operador deje de declararlo parado | `operator_stopped_at` |
| **R4** · llegada a parada (intermedia o terminal) | `INCOMING_AT X` con ancla en zona de X | Retención abierta: el tren está entrando en la parada. Con espera programada en X, `dwell_until` **no** se calcula por tramo plano ±1 m: la espera se retiene hasta la siguiente observación | `operator_incoming_at` |
| **R5** · en tramo (horizonte por tramo) | `IN_TRANSIT_TO` (cualquier X), `INCOMING_AT X` con X por delante fuera de zona, o tras R2 | Avance a la velocidad media programada del tramo actual (en segundos reales, ≤ `max_estimated_speed_kmh`), con `max_progress_m` ≤ progreso de la **siguiente parada fuera de la zona del ancla** (`cap_stop_id`). Al llegar se retiene. Nunca atraviesa una parada dentro de una envolvente | `null` hasta el tope; `leg_end_cap` al alcanzarlo |
| **R6** · terminal | Ancla en zona de la última parada | Retención abierta. **No** existe retención por «hora de llegada pasada»: `19656` circula 141 s después | `terminal` |
| **R7** · incoherencia operador↔GTFS | `current_stop_id` ajeno al viaje; `STOPPED_AT X` con ancla fuera de zona; `INCOMING_AT X` con X por detrás fuera de zona | No se aplica la retención del operador. Degrada a R8 y lo declara (`stop_state.coherent = false`) | según R8 |
| **R8** · sin estado del operador | `current_status` ausente o desconocido, o R7 | Segmentos solo con horario (alternativa C): R2/R6; en zona de parada, retención `max(min_dwell_s, espera programada)` y luego R5; fuera de zona, R5 | `schedule_stop_zone` / `null` |

**Reglas transversales:**

- **R-STALE (FR-05).** Ancla con edad > `stale_after_s`: `rendering_method = stale_frozen`, coordenada **congelada en el final autorizado de la última envolvente** (`progress_at(valid_until)`, recalculable de forma determinista desde la misma ancla). Se publica `frozen_basis = "authorized_envelope_end"` y `last_confirmed_progress_m` = ancla. No es un hecho nuevo: es la estimación ya publicada, sin avance y rotulada como tal. Con R5 esa estimación nunca pasa de la siguiente parada (opción F1). El aviso de congelación del cliente deja de depender de `valid_until !== null`. *Variante F2, a elección del propietario (§9):* congelar en el ancla y publicar `rewound_from_progress_m`. Retroceso medido con A: p50 0,0 m, máx 2 371,0 m.
- **R-DST (FR-26).** Toda conversión entre horario y tiempo usa `service_day_instant`/`service_seconds` por punto, y toda duración se mide en **segundos reales** entre instantes UTC. Queda prohibido restar segundos de reloj de pared a segundos reales (`rendering.py:182,191` hoy).
- **R-REPROJ.** Ancla y paradas se proyectan con la **misma** primitiva (`Corridor.project_station`) sobre el **mismo** `geometry_version`. La coordenada `rendered` de un `anchor` es la proyección `map_matched` (medido: 0,0 m en 44/44). Un cambio de `geometry_version` invalida la envolvente: el cliente no evalúa una envolvente sobre una geometría de otra versión y la sustituye por la coordenada publicada.
- **R-ONECOORD (FR-27).** Si `position.mode ∈ {estimated, stale}`, `position.lat/lon` se toma de `rendered` evaluado en `display_at`: una sola regla de estimación. Si `position.mode = observed`, `position` sigue siendo el ancla (ADR-0004/DEC-010 sin cambio de semántica), y la diferencia con `rendered` la declara `rendering_method` (`extrapolated_from_last_anchor`). Es la divergencia que AUD-04 ya consideraba «diseño declarado».
- **R-SPACE (FR-06).** Un consumidor distingue el **par** (`rendering_method`, `coordinate_space`): `anchor`+`raw` es «GPS de la fuente sin proyectar» y `anchor`+`map_matched` es «proyección sobre la vía de una observación». No se añaden valores al enum; el contrato documenta los pares válidos.
- **R-SKIP (FR-33, limitación declarada).** El modelo **no** afirma que una parada se omita. Las retenciones solo usan `current_stop_id` del operador. Si el tren pasa sin parar por la parada que hace de tope de R5, queda retenido en ella hasta la siguiente observación, un error acotado por la cadencia. La persistencia de `stop_time_update` por parada queda diferida a una tarea propia, fuera de MP-025a.

### 4.3 §2 corregida (sustituye el texto de ADR-0014 §2)

```text
progress_envelope = {
  reference_at,             -- instante del ancla
  progress_m_at_reference,  -- progreso dirigido del ancla
  speed_mps,                -- velocidad de avance DESPUÉS de cualquier espera (>= 0)
  max_progress_m,           -- tope: <= progreso de cap_stop_id (horizonte por tramo)
  horizon_s,                -- valid_until - reference_at
  dwell_until,              -- NULL o instante (>= reference_at) hasta el que no hay avance
  hold_reason,              -- NULL | trip_canceled | operator_stopped_at | operator_incoming_at |
                            --   before_first_departure | terminal | leg_end_cap | schedule_stop_zone
  cap_stop_id               -- NULL | stop_id de la parada que fija max_progress_m
}

t0          = dwell_until if dwell_until is not None else reference_at
progress(t) = min(progress_m_at_reference + speed_mps * max(0, t - t0), max_progress_m)
              para reference_at <= t <= valid_until; todas las diferencias, en segundos reales
```

Semántica:
- `speed_mps = 0` ⇒ **ningún avance en todo el horizonte**: retención abierta, con `hold_reason` poblado.
- `dwell_until` poblado y `speed_mps > 0` ⇒ espera y, después, avance a `speed_mps`. Son compatibles; se retira la frase de ADR-0014 §2 que decía lo contrario.

La fórmula es la que ya implementan `rendering.py:110-114` y `movement.ts:16-23`, así que no cambia la expresión del cliente.

### 4.4 §3 enmendada

- `stale_frozen` se dibuja en `progress_at(valid_until)` de la última envolvente (R-STALE F1) y publica `frozen_basis` y `last_confirmed_progress_m`.
- El método `anchor` se interpreta por par con `coordinate_space` (R-SPACE).
- Se añade a `rendered` un bloque aditivo `stop_state = { source: operator | schedule_fallback, operator_status, operator_stop_id, coherent }`, para que el cliente rotule por qué un tren está retenido sin deducirlo.

### 4.5 §5 enmendada: revisión coherente (para MP-026b)

`build_snapshot()` se ejecuta en **una sola transacción `REPEATABLE READ READ ONLY`**:
1. Primero lee el marcador de revisión (`max(source_ingestion_run.id)`).
2. Después hace todas las lecturas (historiales, `trip_update`, salud) **acotadas explícitamente por `ingestion_run_id <= marker.sequence`**.

Así el `revision.sequence` publicado describe exactamente las filas que contiene la respuesta. `snapshot_id` sigue siendo identidad de contenido, no orden. La acotación por secuencia se exige además de la transacción para que la propiedad no dependa del nivel de aislamiento por defecto del rol.

## 5. Mapa FR → regla → criterio

| FR | Reglas | Criterio de aceptación (§8) |
|---|---|---|
| FR-01 | R1, R2, R3 | AC-1, AC-2, AC-3, AC-12 |
| FR-03 | R4 (+ `stop_id` + zona; deroga la tolerancia de ±1 m) | AC-5 y S4 |
| FR-04 | R5 (horizonte por tramo, `cap_stop_id`) | AC-11 |
| FR-05 | R-STALE (F1 o F2) + aviso independiente de `valid_until` | AC-6 |
| FR-07 | §4.5 | AC-14 (MP-026b) |
| FR-26 | R-DST | AC-7, AC-8 |
| FR-27 | R-ONECOORD | AC-10 |
| FR-31 | §4.3 | AC-13 |
| FR-33 | R-SKIP (limitación declarada; persistencia diferida) | sin prueba automática; revisión de que ninguna superficie afirma una omisión |
| FR-06 / FR-32 (relacionados) | R-SPACE / R-CANCEL | AC-9, AC-16 y prueba de cliente en MP-030 |

## 6. Constantes: parámetros a calibrar por MP-028, no valores de diseño

Todas pasan a un `StopStateThresholds` inyectable, junto a `MovementThresholds`. Los valores del arnés solo sirven para medir.

| Parámetro | Papel | Valor en el arnés | Evidencia que acota su calibración |
|---|---|---|---|
| `stop_zone_radius_m` | Zona de parada (R1, R4, R5, R6, R7) | 50 m (barrido 5–100) | ≥ 5,38 m (`19656`); ≥ 38 m para las 28 `STOPPED_AT` del corte; p95 de proyección 20,8 m (AUD-04 §0.3). Cota superior: distancia mínima entre paradas consecutivas, `UNVERIFIED` |
| `min_dwell_s` | Retención mínima en zona de la degradación R8 | 30 s (barrido 0–180) | 180 s retiene pero pierde 7/9 avances legítimos. Calibrar con las esperas reales `STOPPED_AT` de MP-028 |
| `stale_after_s` (horizonte) | Límite superior de la envolvente | 180 s (`model.py:40`, sin cambio) | Con R5 el avance efectivo queda limitado por el tramo. DEC-010 no cambia de valor; MP-028 decide si se recalibra |
| `cancel_max_age_s` | Vigencia de un `CANCELED` | sin valor (propuesta: reutilizar `operator_delay_max_age_s` = 600 s, `config.py:59`) | Sin casos de Madrid en el kit (7 casos, todos del núcleo 51) |
| `max_estimated_speed_kmh` | Techo de la velocidad de tramo | 160 (`model.py:45`, sin cambio) | — |

## 7. Consecuencias

- **Contrato `/api/v1`, aditivo, sin `/api/v2`:**
  - `ProgressEnvelopeOut` añade `hold_reason` y `cap_stop_id`, ambos nullables.
  - `RenderedOut` añade `stop_state`, `frozen_basis` y `last_confirmed_progress_m`, todos nullables.
  - No cambia ningún valor de `rendering_method`. Cambia la **semántica documentada** de `stale_frozen` (coordenada) y de `position` cuando `mode ∈ {estimated, stale}` (R-ONECOORD): debe constar en `DATA_CONTRACTS.md` y en `schemas.py`.
  - Hay más trenes quietos en el mapa (28/44 del corte). Es el comportamiento correcto y hay que comunicarlo.
- **`packages/movement` (ADR-0012, frontera sin cambio):**
  - `TripSchedule` gana `stops` (aditivo), proyectadas con la misma primitiva.
  - `_envelope` se sustituye por la selección R-CANCEL…R8. `dwell_end_seconds` deja de usarse en presentación.
  - El estado del operador ya está en el contrato canónico, así que no hay dependencia nueva.
  - `schedule_relationship` entra como **dato** (argumento), no como lectura de base de datos.
  - Nada de HTTP entra en el paquete. **ADR-0012 no se modifica.**
- **`apps/api/snapshot.py`:**
  - `_render_vehicle` (`:321`) recibe la `trip_update` de la circulación (cambio de firma interno) para R-CANCEL y R-ONECOORD.
  - `_legacy_position` (`:245`) toma la coordenada de `rendered` en `estimated`/`stale`.
  - `build_snapshot` (`:629`) aplica §4.5.
- **`apps/web/src/domain/movement.ts`:**
  - `progressAt` (`:16-23`) **no cambia**: tope y retención ya caben en `max_progress_m` y `speed_mps = 0`.
  - `frameFor` (`:74-97`) deja de saltar al pasar a `stale_frozen` porque el backend publica el final autorizado (F1).
  - El aviso de `TrainPanel.tsx:82` no depende de `valid_until`.
  - `METHOD_STYLES` (`domain/format`) se indexa por (método, espacio).
  - Se rotulan `hold_reason`/`stop_state` y `schedule_relationship = CANCELED`. El detalle de interfaz es de MP-030.
- **Compatibilidad Python↔TypeScript:** una única expresión, ya idéntica en ambos lenguajes. MP-025a añade un **fixture dorado** compartido (envolventes con espera, tope, retención abierta y fechas DST), evaluado por `ProgressEnvelope.progress_at` y por `progressAt` en los mismos instantes, con tolerancia ≤ 1e-6 m. No se crea una segunda implementación del motor en TS (ADR-0014, alternativa 2, sigue descartada).
- **Riesgos:**
  - **Dependencia de la semántica de Renfe.** Medida en un solo corte. Si en vivo `IN_TRANSIT_TO` se comporta según la especificación, R5 podría usar `current_stop_id` como tope; mientras no se demuestre, no.
  - **Retención de salidas** hasta la siguiente observación (3/44 en el kit).
  - **Paradas omitidas** como tope (R-SKIP).
  - Todo ello lo valida en vivo **MP-025b**: salto al llegar el ancla p50 ≤ 200 m con ≥ 500 pares.

## 8. Criterios de aceptación de MP-025a (ROJO en `beb9434`, VERDE tras la corrección)

Las cifras «hoy» están medidas con el arnés sobre producción `beb9434` (`output.txt`), salvo donde se indica otra cosa. MP-025a las convierte en pruebas de `pytest`/`vitest` del repositorio. Las cifras sobre cortes reales se calculan **desde el GPS bruto**, pasando por el motor de producción, no desde puntos generados sobre la geometría.

| ID | Prueba | Umbral | Hoy (`beb9434`) |
|---|---|---|---|
| AC-1 | Corte `1533`: `STOPPED_AT` con GPS idéntico en `1532` y `1533` que publican `speed_mps > 0` | **0/25** | 25/25 — ROJO |
| AC-2 | Pre-salida con avance en el horizonte, y salidas retrasadas en origen `STOPPED_AT` con avance | **0/17** y **0/4** | 17/17 y 4/4 — ROJO |
| AC-3 | `STOPPED_AT` en parada intermedia con avance | **0/7** | 7/7 — ROJO |
| AC-4 | No regresión: `IN_TRANSIT_TO`/`INCOMING_AT` en `1532` que avanzaron ≥ 100 m y reciben 0 m a 77 s | **0/9** | 0/9 — VERDE (guarda) |
| AC-5 | `19656` desde su GPS bruto real (`40.283237, -3.7991464`), `INCOMING_AT 35002` | avance a 30 s **≤ 1 m** | 661,1 m — ROJO |
| AC-6 | Las 25 en ventana, edad 179 s → 181 s | retroceso **≤ 1 m**; aviso visible con `valid_until = null` (vitest) | 25/25 > 1 m, p50 2 357,9 m — ROJO |
| AC-7 | Horario sintético 01:50→02:10, 2027-03-28, ancla 01:58 local | avance en 180 s = **3 000,0 ± 1 m** | 8 000,0 m — ROJO |
| AC-8 | Horario sintético 01:30→03:30, 2027-10-31, ancla 02:59 CEST | avance = **333,3 ± 1 m** | 0,0 m — ROJO |
| AC-9 | Circulación `CANCELED` en marcha (sintética) | **0 m** y `hold_reason = trip_canceled` | 2 143,8 m — ROJO |
| AC-10 | Las 25 en ventana, edades 61–179 s con `position.mode = estimated`; peor caso de AUD-04: `20849` | \|`position` − `rendered`\| **≤ 1 m** | máx 429,5 m — ROJO |
| AC-11 | Envolventes que atraviesan una parada a más de `stop_zone_radius_m` antes de `valid_until` | **0/44** | 20/44 (29/44 con margen de 1 m) — ROJO |
| AC-12 | Sintéticos de salida retrasada (+120 s) y parada intermedia sin espera programada, `STOPPED_AT` | **0 m** | 2 811,3 m y 2 364,5 m — ROJO |
| AC-13 | Fórmula de §4.3 literal en ADR-0014, `DATA_CONTRACTS.md`, `schemas.py`, `rendering.py` y `movement.ts` | igualdad textual (revisión) | ADR-0014 §2 discrepa — ROJO |
| AC-14 | (MP-026b) Carrera con dos conexiones PostgreSQL reales entre la primera lectura y el marcador | respuesta toda anterior o toda posterior | mezcla reproducida por AUD-06 — ROJO. **No reejecutado en MP-024** |
| AC-15 | Fixture dorado Python↔TS | \|Δ\| ≤ 1e-6 m | el fixture no existe — prueba nueva |
| AC-16 | `STOPPED_AT` con `stop_id` ajeno, e `INCOMING_AT` con parada 1 182 m por detrás | sin retención del operador y `stop_state.coherent = false` | no existe el concepto — ROJO |

Validación en vivo (MP-025b, sin cambios respecto a H4-04): salto al llegar el ancla siguiente p50 ≤ 200 m con ≥ 500 pares. MP-025a puede cerrar sin ella y debe declararlo.

## 9. Decisión que debe tomar el propietario

**Recomendación:** aprobar la alternativa **A**, con las dos correcciones de §2 (tope por tramo desde el horario, no desde `current_stop_id`; sin retención por hora de llegada pasada), C como degradación y las reglas transversales.

**Qué se aprueba:**
1. Las reglas R-CANCEL, R1–R8, R-STALE, R-DST, R-REPROJ, R-ONECOORD y R-SPACE.
2. La fórmula de §4.3, que sustituye la de ADR-0014 §2.
3. §4.4 y §4.5.
4. Los criterios AC-1…AC-16 como cierre de MP-025a (AC-14 en MP-026b).

**Qué se difiere:**
- los **valores** de §6 (MP-028);
- la validación en vivo (MP-025b);
- la persistencia de `stop_time_update` (R-SKIP, tarea propia);
- el modelo de segmentos OSM (MP-029);
- el detalle de interfaz (MP-030).

**Elección explícita pendiente:** R-STALE **F1** (congelar en el final autorizado: retroceso 0 m, AC-6 tal como está) o **F2** (congelar en el ancla y declarar el retroceso: p50 0 m, máx 2 371 m con A; AC-6 pasaría a «retroceso declarado»). Recomendación: **F1**.

**Dudas abiertas:**
- (a) La semántica real de `IN_TRANSIT_TO`/`INCOMING_AT` de Renfe en vivo (MP-028).
- (b) Si `position` debe pasar a ser **siempre** `rendered` (cambia la semántica de `observed`, ADR-0004) o solo en `estimated`/`stale`, como se propone.
- (c) La vigencia de `CANCELED` (`cancel_max_age_s`).
- (d) La cota superior de `stop_zone_radius_m`.

## 10. Reproducción

```sh
python3 docs/evidence/mp-024/stop_state_comparison.py \
  --replay /Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay \
  --json docs/evidence/mp-024/results.json > docs/evidence/mp-024/output.txt
```

- **Entradas:** SHA-256 en `docs/evidence/mp-024/README.md`, verificados contra `manifest.json` por el propio guion.
- **Código de producto:** idéntico a `beb9434` (comprobado por el guion).
- **Base de datos:** ninguna.
