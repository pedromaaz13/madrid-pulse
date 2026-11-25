# ADR-0014 · Enmienda 1: modelo de estado de parada, horizonte por tramo y revisión coherente

- **Estado:** **Dirección aprobada por el propietario el 2026-11-25** (A con C como degradación R8; F1; perfil P-024 provisional; limitaciones aceptadas): ver [`0014-amendment-owner-decision.md`](0014-amendment-owner-decision.md). Hasta entonces fue `Propuesto`. **La decisión no convierte en APPROVED el dictamen histórico de Astra (CHANGES_REQUESTED parcial) ni valida los supuestos `UNVERIFIED`.** ADR-0014 base sigue `Propuesto` salvo lo que esta enmienda sustituye; su promoción completa no está decidida.
- **Fecha:** 2026-11-25. Ronda 2 el mismo día, tras el dictamen `CHANGES_REQUESTED` (7 B, 4 A) de Codex `gpt-6.2-astra` · high sobre `f0f8224`; la tabla de correcciones está en el Anexo. Cierre de la 2ª ronda ordinaria (B2, B5, B6 y A3 parciales) el mismo día; **no hay tercera ronda automática** (ORCHESTRATION_POLICY §3.3): las correcciones de ese cierre no las re-verifica Codex salvo decisión del propietario.
- **Tarea:** MP-024 (H4-00).
- **Ejecutor:** Claude `claude-opus-5-5` · high.
- **Revisor:** Codex `gpt-6.2-astra` · high, proveedor contrario.
- **Alcance:** enmienda a [ADR-0014](0014-snapshot-and-temporal-contract.md), que sigue `Propuesto`. **Sustituye** su §2 y **enmienda** su §3 y su §5; el resto queda intacto.
- **Por qué enmienda y no ADR-0016:** el defecto está en el contrato temporal que define ADR-0014, y ese ADR aún no está aceptado. Lo coherente es que el propietario promueva un único contrato corregido.
- **Fuera de alcance:** el grafo de segmentos OSM (MP-029). Ninguna regla de esta enmienda lo necesita.
- **Evidencia:** [`docs/evidence/mp-024/`](../evidence/mp-024/README.md). Arnés offline v2, salida `output.txt`, `results.json`, fixture AC-15 y `ts_equivalence.cjs`.

**Convención.** «Medido» = salida del arnés sobre producción `beb9434` o sobre el prototipo; las cifras son exactas, sin redondear el predicado. «`UNVERIFIED`» = no demostrable con los datos disponibles. Los prototipos del arnés **no** son MP-025a.

---

## 1. Contexto

Hallazgos de [`FINDINGS_REGISTER.md`](../audits/hito-03/FINDINGS_REGISTER.md), medidos de nuevo con producción `beb9434`:

| FR | Sev. | Hallazgo | Medido en `beb9434` |
|---|---|---|---|
| FR-01 (S1-a) | **P0** | La envolvente pone en marcha circulaciones que el operador declara `STOPPED_AT` | `speed_mps > 0` en 25/25 con GPS idéntico entre cortes; 17/17 pre-salida, 4/4 salidas retrasadas, 7/7 intermedias |
| FR-03 | P1 | La espera programada solo se expresa en una ventana de ~1 m (tolerancia de 1,0 m + guarda) | `19656`: 661,12 m a 30 s y 1 322,25 m a 60 s |
| FR-04 | P1 | El horizonte de 180 s atraviesa estaciones | 20/44 cruzan una parada a más de τ = 50 m; 29/44 con margen de 1 m |
| FR-05 | P1 | Retroceso al caducar; el aviso desaparece porque depende de `valid_until` | Camino stale real de producción: 25/25 retroceden, p50 2 357,87 m, máx 3 959,22 m |
| FR-07 | P1 | `build_snapshot()` mezcla lecturas de instantes distintos | Reproducido por AUD-06. **No se reejecuta aquí** |
| FR-26 | P2 | Mezcla de reloj de pared y segundos reales | Sintéticos: 2027-03-28 da 8 000,00 m frente a 3 000,00 m reales; 2027-10-31 da 0,00 m frente a 333,33 m |
| FR-27 | P2 | Dos coordenadas del mismo instante | 2 975 muestras (edades enteras 61–179 s, modo `estimated`): máx 429,52 m en progreso y 429,39 m entre lat/lon |
| FR-31 | P2 | §2 sin `dwell_until` y con «`speed_mps = 0` ⇔ espera» | Las otras superficies usan `t0 = dwell_until or reference_at` |
| FR-33 | P2 | `stop_time_update` por parada descartado | No medible |

Relacionados que se cubren: **FR-06** (`anchor` sin `coordinate_space`) y **FR-32** (`CANCELED` dibujada como en marcha).

**Causa raíz común de S1** (`FINDINGS_REGISTER.md` §2.3): la envolvente deduce el estado del tren respecto de las paradas **solo** por geometría e interpolación del horario.

## 2. Hechos medidos que condicionan el diseño

Corte `1533`: 44 circulaciones con cadena completa, más 44 pares `1532→1533` de 77 s cada uno.

1. **El estado del operador está y es coherente con el viaje.** `current_status` y `current_stop_id` aparecen en 44/44, y la parada pertenece al viaje en 44/44.
2. **`IN_TRANSIT_TO X` no significa «va hacia X».** En 4/8 casos X queda más de 1 km **por detrás** del ancla: 4 288,52; 2 416,28; 3 234,47 y 1 848,87 m. Por eso el tope por tramo sale del horario. La semántica en vivo es `UNVERIFIED` (MP-028).
3. **`19656` está `post_llegada`.** Está 141 s después de su última llegada programada. Su arco medio fue de **75,0 km/h en los 77 s previos** a `1533`. No es una velocidad instantánea, y tampoco prueba qué hizo en los 30 s siguientes (A1). **No existe retención por «hora de llegada pasada».**
4. **Coste de A:** 3/44 pares, 3 de los 27 `STOPPED_AT` en `1532`. Son `19671`, `20284` y `20836`: avanzaron 2 204,0, 2 424,5 y 1 860,2 m antes de `1533`, y A predice exactamente 0 m. El instante real de salida es desconocido. Que la latencia en vivo quede acotada por ~20 s de cadencia es `UNVERIFIED` si hay retraso o pérdida del feed.
5. **Estructura del GTFS en los 44 viajes:**
   - 0 `stop_id` repetidos;
   - 0 tramos con separación ≤ 2τ (100 m);
   - 0 tramos con duración real ≤ 0 (829 tramos).

   Los casos límite de §4.2 solo se ejercitan con sintéticos.
6. **Reproyección:** el ancla `rendered` frente a la proyección `map_matched` difiere como máximo 0,0016 m (n = 44).

## 3. Alternativas comparadas

Las comparaciones se hacen con el horizonte de producción: 180 s desde el ancla (`rendering.py:279,346`). El perfil de ensayo es P-024 (τ = 50 m, Dmin = 30 s; §6).

**Grupo M — hechos de movimiento sobre cortes reales.** Son los únicos criterios que discriminan entre alternativas. Se solapan: M1 ⊂ M2a ∪ M3 ∪ M4 = los 28 `STOPPED_AT`.

M2 se mide de dos formas (B6), porque responden a reglas distintas:
- **M2a mide R1:** que no se mueva un tren pre-salida que el operador declara `STOPPED_AT`, aunque su salida programada caiga dentro del horizonte. Es la que entra en el total.
- **M2b mide R2:** el avance acumulado hasta la salida programada, el único que R2 prohíbe a un tren no declarado parado.

En el corte, las 17 pre-salidas son `STOPPED_AT` (comprobado con `assert`). B2 y C pasan M2b, porque solo avanzan después de la salida programada, y fallan M2a en 2/17. R2 sin `STOPPED_AT` lo prueba el sintético S2b.

C se mide con la entrada en zona por muestras de §4.6 aplicada a los cortes: 31 anclas tienen dos muestras consecutivas en la zona y cambian 14 envolventes de C, la misma lista con Dmin = 30 y con Dmin = 180.

| Criterio (predicado exacto) | BASE | **A** | B1 ±600 s | B2 B1 + pre-salida | C (Dmin 30) | D tolerancia 50 |
|---|---|---|---|---|---|---|
| M1 `STOPPED_AT` con GPS idéntico y `speed_mps > 0` | 25/25 | **0/25** | 21/25 | 10/25 | 10/25 | 25/25 |
| M2a (R1) pre-salida, las 17 declaradas `STOPPED_AT`, con `speed_mps > 0` en el horizonte | 17/17 | **0/17** | 13/17 | 2/17 | 2/17 | 17/17 |
| M3 salida retrasada en origen con `speed_mps > 0` | 4/4 | **0/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| M4 `STOPPED_AT` intermedia con `speed_mps > 0` | 7/7 | **0/7** | 7/7 | 7/7 | 7/7 | 7/7 |
| M5 cruzan una parada a más de τ antes de `valid_until` | 20/44 | **0/44** | 22/44 | 20/44 | 0/44 | 20/44 |
| M6 `19656`: avance a 30 s `== 0` | 661,12 m | **0 m** | 661,12 m | 661,12 m | 0 m | 661,12 m |
| M7 guarda: `IN_TRANSIT_TO`/`INCOMING_AT` que avanzaron ≥ 100 m con predicción `== 0` | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| **Grupo M PASS** (con M2a) | **1/7** | **7/7** | 1/7 | 1/7 | 3/7 | 1/7 |
| M2b (R2), aparte: avance acumulado hasta min(salida programada, horizonte) `> 0` en las 17 | 17/17 | 0/17 | 13/17 | 0/17 | 0/17 | 17/17 |
| Grupo M si M2b sustituyera a M2a | 1/7 | 7/7 | 1/7 | 2/7 | 4/7 | 1/7 |
| Coste: `STOPPED_AT` en `1532` que salieron, con predicción `== 0` | 0/27 | **3/27** | 0/27 | 0/27 | 0/27 | 0/27 |
| Error a 77 s, p50 / p90 / máx (m) | 1 229,15 / 1 731,54 / 3 274,23 | 0,00 / 1 523,78 / 3 274,23 | 950,49 / 2 216,27 / 3 422,22 | 875,97 / 1 921,01 / 3 422,22 | 570,10 / 1 338,31 / 3 669,40 | = BASE |
| Sobreavance > 100 m a 77 s | 32/44 | **2/44** | 24/44 | 18/44 | 15/44 | 32/44 |

- **A — recomendada.** Es la única con 7/7. Coste: 3/27.
- **B — descartada.**
  - B1 apenas corrige y empeora el peor caso: 8 000 m de avance al caducar y 3 422,22 m de error.
  - B2 deja las 4 salidas retrasadas y las 7 intermedias.
- **C — descartada como modelo y conservada como degradación R8.** Sin el estado del operador no retiene las 4 + 7.
  - Con Dmin = 180 s y la entrada por muestras sigue publicando avance en 4/4 salidas retrasadas y en 4/7 intermedias, y además pierde 7/9 avances legítimos (grupo M 2/7).
  - La ronda 2 publicaba 0/4 y 0/7 porque, sin historia, la espera arrancaba en el ancla.
- **D — descartada.** Con tolerancia de 50 m es idéntica a BASE en todo: la guarda `rendering.py:192` descarta la espera.

**Grupo S (reglas, sintéticos) y grupo T (reglas transversales)** se informan aparte (§8). No discriminan: A y C incorporan R-CANCEL, R-DST y R-STALE por diseño; B y D conservan la aritmética de producción por definición, y podrían adoptarlas igual. Por eso **no** se suman al total del grupo M.

## 4. Decisión propuesta

**A** con C como degradación, el orden total de §4.2 y las reglas transversales. Vive en la traducción de MP-019 y en sus consumidores; `engine.py` sigue siendo la única autoridad sobre qué observación es utilizable.

### 4.1 Entradas y observación efectiva

- **Observación efectiva** (B3): la que el motor usó como ancla, es decir, la de `MovementPosition.observed_at`. El estado del operador (`current_status`, `current_stop_id`) se toma **de esa observación**, no de `latest`.
  - Si el motor rechaza `latest` y usa `previous` (`engine.py:109-128`), el estado es el de `previous`.
  - Medido (P1, motor real, `19664` con `latest` desplazado 0,27°): el motor usa `previous` (`IN_TRANSIT_TO`), que da R5 con avance. Usar el `STOPPED_AT` de `latest` daría R1 y retención. Resultados distintos.
  - El bloque `map_matched` sigue describiendo `latest` (`snapshot.py:335-356`).
- **Ocurrencia de la parada declarada** (A4): si `stop_id` aparece varias veces en el viaje, se toma la **ocurrencia de progreso más cercano** al ancla; en empate, la de menor `stop_sequence`. Sintético S14 PASS; en el corte no hay repeticiones.
- **Estado ausente frente a contradictorio** (A4), en `stop_state.coherent`:
  - `null`: estado ausente (`current_status` nulo o desconocido, o sin `current_stop_id`);
  - `false`: contradictorio;
  - `true`: coherente.
- **Zona de una parada:** |progreso(parada) − progreso(ancla)| ≤ τ, con τ = `stop_zone_radius_m`. Si varias paradas están en zona (zonas solapadas), cuenta la más cercana y, en empate, la de menor índice.

### 4.2 Orden total de precedencia (B1)

```text
1  R-CANCEL  trip_update base CANCELED (§4.4)                  → retención   hold_reason=trip_canceled
2  clasificar estado de la observación efectiva:
     AUSENTE        status ∉ {STOPPED_AT, INCOMING_AT, IN_TRANSIT_TO} o stop_id nulo
     INCOHERENTE    stop_id ajeno al viaje
                    | STOPPED_AT con ancla fuera de zona de X
                    | INCOMING_AT con X por detrás fuera de zona (gap < −τ)
     COHERENTE      resto (IN_TRANSIT_TO X: siempre coherente; X solo pista, §2.2)
3  AUSENTE     → R8                                    stop_state.coherent = null
4  INCOHERENTE → R7 → R8                               stop_state.coherent = false
5  R1   STOPPED_AT coherente                                    → retención   operator_stopped_at
6  R4   INCOMING_AT con ancla en zona de X                       → retención   operator_incoming_at
7  R6x  ancla < progreso(primera parada) − τ                     → retención   outside_schedule_extent
8  R6   ancla ≥ progreso(última parada) − τ                      → retención   terminal
9  R2   anchor_at < salida programada de la primera parada:
          salida ≥ valid_until → retención   before_first_departure
          si no                → dwell_until = salida; después, R5
10 R5   tramo

R8 (degradación = alternativa C) = pasos 7, 8 y 9, después «zona de parada» (§4.6) y luego R5.
R5: prev = última ocurrencia con progreso ≤ ancla + τ
    cap  = primera ocurrencia posterior con progreso > ancla + τ   (cap_stop_id)
    v    = (prog(k) − prog(prev)) / (llegada_real(k) − salida_real(prev)) para el primer k ≥ cap
           con duración real > 0 y distancia > 0 (fusión de tramos de duración 0, sintético S13);
           ninguno → retención schedule_incoherent; v ≤ max_estimated_speed_kmh
    max_progress_m = min(prog(cap), ancla + v · (valid_until − inicio))
```

- **Orden.** La incoherencia y el estado ausente se resuelven **antes** de pre-salida, terminal y tramo.
- **Contraejemplo del revisor (S5b).** `INCOMING_AT` apunta a la parada anterior y el ancla está en zona de otra.
  - Hoy: R7 → R8, idéntica a C campo a campo, con avance a 20 s `== 0,0` m.
  - Con la v1: 262,64 m.
- **Sintéticos (todos PASS):**

  | Caso | Comprueba |
  |---|---|
  | S7 | `stop_id` ajeno |
  | S10 | `INCOMING_AT` con la parada 1 182 m por detrás |
  | S11 | ancla antes de la primera parada |
  | S12 | zonas solapadas: tope Z2 |
  | S13 | tramo de duración 0: v = 3 000/180 m/s, no 160 km/h |
  | S14 | `stop_id` repetido |

### 4.3 Envolvente, fases y serialización (sustituye ADR-0014 §2; B4)

**(a) Envolvente.** Todos los campos son aditivos salvo los existentes.

```text
progress_envelope = { reference_at, progress_m_at_reference, speed_mps, max_progress_m, horizon_s,
                      dwell_until,      -- NULL | instante ≥ reference_at hasta el que no hay avance
                      hold_reason,      -- causa de la retención inicial (§4.2); NULL si no la hay
                      cap_stop_id,      -- parada que fija max_progress_m (NULL si no hay tope de parada)
                      cap_kind,         -- stop | horizon | NULL (sin avance)
                      cap_reached_at,   -- instante (redondeo HACIA ARRIBA a ms) en que se alcanza max_progress_m
                      envelope_id }     -- hash de las entradas de §4.4 (identidad de la envolvente)
t0 = dwell_until if dwell_until is not None else reference_at
progress(t) = min(progress_m_at_reference + speed_mps · max(0, t − t0), max_progress_m)
```

- `speed_mps = 0` significa ningún avance en todo el horizonte.
- `dwell_until` poblado con `speed_mps > 0` significa esperar y luego avanzar.

**(b) Semántica de los campos.**
- `hold_reason` describe la **envolvente**, no el fotograma: no cambia dentro del horizonte.
- `cap_kind = stop` solo si `max_progress_m` es **exactamente** el progreso de `cap_stop_id`. Entonces `progress(cap_reached_at) == max_progress_m` (medido en S2b).
- `horizon` significa que la autorización termina antes de llegar a la parada.

La fase del **fotograma** `t` es una función pura, idéntica en Python y TS:

```text
phase(t) = "hold:<hold_reason>"  si speed_mps == 0 o t < t0
         = "cap:<cap_kind>"      si cap_reached_at no es NULL y t ≥ cap_reached_at
         = "moving"              en otro caso
```

`before_first_departure` deja de aplicar en `t0`. Sintético S2b: `hold` → `moving` en la hora de salida → `cap:stop`.

**(c) Serialización.** Todos los instantes de la envolvente se construyen y se serializan **con precisión de milisegundo**: `isoformat(timespec="milliseconds")`.
- `Date.parse` (`movement.ts:16-23`) trunca los submilisegundos. Con microsegundos la discrepancia medida es 0,0117 m: 18 envolventes con un desfase de 0,7 ms.
- Con milisegundos, el `progressAt` de **producción** transpilado da |Δ| = **0 m** frente a Python en 367 muestras de 63 envolventes, y las fases coinciden en 367/367 (`ts_equivalence.cjs`).

### 4.4 Identidad de la envolvente y congelación (R-STALE F1; B2)

- **Tres relojes de una `trip_update`.**
  - `observed_at`: cuándo **ocurrió** según la fuente;
  - `received_at`: cuándo la **recibió** el colector (`0001_init.up.sql:109-110`);
  - visibilidad para una consulta: el commit de su ciclo (run).
- **Ejemplo del problema.** Una cancelación ocurrida a +20 s y visible por primera vez a +181 s era un retroceso F1 de **1 071,15 m** en `19667` con la política de la ronda 2, que recortaba en `observed_at` (`contraejemplo_19667.observed` en la salida). Recortar en `received_at` tampoco basta: si una fila se hace visible después de su `received_at`, vuelve a haber retroceso.
- **Política adoptada: envolvente inmutable por run** (B2). La envolvente de un ancla se calcula **una vez, con el estado disponible cuando el ancla lo estuvo**:
  - **Estado base:** la última `trip_update` del viaje, por (`ingestion_run_id`, `observed_at`), con `ingestion_run_id ≤` el del ancla. Es la misma regla en producción, en el arnés (`authorized_plan`, `run <= anchor_run`) y en replay.
  - **Predicado de edad:** un `CANCELED` base solo aplica si `anchor.observed_at − trip_update.observed_at ≤ cancel_max_age_s`. El valor del umbral se difiere a MP-028; el perfil P-024 usa 600 s.
  - **Ninguna fila posterior modifica** la envolvente vigente ni su congelación F1: ni un `CANCELED` ni una anulación, aunque haya ocurrido antes y llegue tarde. Se aplica a la **siguiente ancla**. Entretanto, el tren se rotula por `schedule_relationship` y el aviso de interfaz, sin mover la coordenada.
  - **Coste:** un tren cancelado puede seguir extrapolando hasta su siguiente observación o hasta `valid_until`, como máximo 180 s.
- **Reloj de vigencia y replay.**
  - `valid_until = reference_at + stale_after_s`, evaluado en `display_at`.
  - Una consulta en vivo solo ve las filas confirmadas y visibles en ese instante.
  - **Garantía de replay, acotada:** **dado el identificador del ancla (su observación y su `ingestion_run_id`)**, la envolvente se reconstruye exactamente, porque solo depende de filas con `run ≤ run(ancla)` y de las versiones registradas en `envelope_id`.
  - **Lo que no garantiza:** que un replay por **hora civil** (`?at=`, que selecciona runs con `started_at ≤ at`, MP-026a) elija la misma ancla que se publicó en vivo a esa hora.
    - El esquema guarda `started_at` y `finished_at` por run (`0001_init.up.sql:64-75`), pero no cuándo se hizo visible: el colector fija `finished_at` antes del commit (`collector.py:118-125,144-154`).
    - Con un solo escritor se conoce el **orden** de los commits, no su **hora**.
    - Por eso, un run iniciado antes de `at` y aún sin confirmar en vivo puede salir seleccionado en el replay. Contraejemplo del revisor: run 100 con `started_at` = 10 y commit a 13 o a 18; consultando a la hora 15, el ancla en vivo es la del run 100 o la del 99, y la reconstrucción por `started_at` da siempre el 100.
  - **Mantener la garantía por hora civil** exigiría una referencia histórica de publicación o visibilidad (p. ej. registrar `committed_at` por run, o el `revision.sequence` servido) y una prueba en el intervalo entre el inicio y el commit de un run. **Pendiente / `UNVERIFIED`**; la decisión se difiere a MP-026b (replay `?at=`) y MP-032 (operación).
- **Condición de la garantía** (declarada y verificable por configuración): las filas con `run ≤ run(ancla)` son visibles antes que el ancla. Se cumple con un único colector y un commit por ciclo (`collector.py:115-118`), porque los runs se confirman en orden de `id`. Si se viola (varios escritores, carga retroactiva), la garantía de no retroceso deja de valer:
  - escenario `CONDICION_VIOLADA_base_run99_visible+100` → retroceso F1 de **1 310,66 m**;
  - MP-025a debe excluir de la base del directo las filas de cargas retroactivas;
  - MP-032 debe operar un único colector.
- **Descartadas.**
  - **Recorte en `observed_at`** (ronda 2): produce el contraejemplo.
  - **Recorte en `received_at`:** su garantía depende de que visibilidad == `received_at`, y no es más robusta que la inmutabilidad, que es más simple.
- **Entradas de la envolvente** (`envelope_id`):
  - ancla (vehículo, viaje, `observed_at`, `ingestion_run_id`, progreso, estado efectivo);
  - estado base (`ingestion_run_id` de la `trip_update` usada o `null`);
  - `gtfs_version`, `geometry_version` y la versión de los umbrales.
- **Medido.** 25 en ventana, consultando cada 0,5 s de 0 a 400 s; **cada consulta ve solo las filas visibles en su instante**, así que la disponibilidad varía entre consultas:

  | Escenario (ocurrió · visible) | Base | Retroceso F1 máximo |
  |---|---|---|
  | Sin cambio | 25 sin cancelación | 0,0 m |
  | `CANCELED` posterior · ocurrió +20 s, visible +20 s | 25 sin cancelación (aplica en la siguiente ancla) | 0,0 m |
  | `CANCELED` posterior · ocurrió +20 s, visible +181 s (**contraejemplo**) | 25 sin cancelación | **0,0 m** (ronda 2: 1 071,15 m en `19667`) |
  | `CANCELED` +60 s y anulación +150 s | 25 sin cancelación | 0,0 m |
  | `CANCELED` base, ocurrido hace 300 s | 25 canceladas | 0,0 m |
  | `CANCELED` base de ayer (−86 400 s) | 25 caducadas (ignoradas por edad) | 0,0 m |
  | `CANCELED` base ocurrido hace 700 s y recibido hace 5 s | 25 caducadas (la edad se mide en `observed_at`) | 0,0 m |
  | Condición violada: fila base visible a +100 s | 25 canceladas | 1 310,66 m (fuera de la garantía) |

- **Congelación F1 (recomendada).** Si `display_at > valid_until`, `rendering_method = stale_frozen` y la coordenada es `progress(valid_until)` de la envolvente **reconstruida con las entradas admisibles hasta `valid_until`**. Es una función pura de datos persistidos: tras un reinicio o en una primera consulta ya caducada da el mismo valor (medido: 0 discrepancias en 8 × 25). Se publican `frozen_basis = authorized_envelope_end` y `last_confirmed_progress_m` = ancla.
  - **Sin envolvente posible**, o con `gtfs_version`/`geometry_version`/umbrales distintos de los del ancla: se congela **en el ancla** con `frozen_basis = anchor_version_changed` (medido).
  - El aviso de congelación de la interfaz no depende de `valid_until` (MP-030).
  - **AC-T1:** retroceso al expirar `== 0` m.
- **Si el propietario elige F2,** esta viñeta y AC-T1 se sustituyen por: «`stale_frozen` en el ancla, con `frozen_basis = anchor`, `rewound_from_progress_m = progress(valid_until)` y `rewind_m` = diferencia». **AC-T1′:** |salto publicado − `rewind_m`| ≤ 1e-9 m y aviso visible. Medido: 0,0 m sobre las 25 en ventana, 7/25 con `rewind_m > 0`; el máximo con A sobre las 44 circulaciones es 2 371,04 m (M8).

### 4.5 Ramas de presentación (B3)

Las ramas se aplican en este orden, sobre el instante `display_at`:

| # | Condición | `rendering_method` · `coordinate_space` | Envolvente | Notas |
|---|---|---|---|---|
| 1 | Sin GPS utilizable y sin horario resoluble, o `CANCELED` sin ancla utilizable | `unlocated` · `null` | no | `reason = trip_canceled` si aplica (P2: medido) |
| 2 | Patrón sin corredor validado | `anchor` (o `stale_frozen` con edad > `stale_after_s`) · `raw` | no | `CANCELED` solo rotula; congelación sin retroceso, porque no hubo avance (P3) |
| 3 | Corredor validado y motor `SCHEDULED` | `schedule_only` · `schedule` | sí: R8 sobre el punto de horario, con `coherent = null` | P2: medido |
| 4 | Hay ancla `A_prev` (última aceptada con `observed_at ≤ display_at`) y otra posterior `A_next` del mismo viaje con `A_next − A_prev ≤ stale_after_s` | `interpolated_between_known_anchors` · `map_matched` | no | Solo con `display_lag_s > 0` o en replay. Medido (P4, `19656` a −30 s): igual que producción, |Δ| = 0 m |
| 5 | `display_at − A_prev > stale_after_s` | `stale_frozen` · `map_matched` | no | §4.4 |
| 6 | Resto | `anchor` / `extrapolated_from_last_anchor` · `map_matched` | sí: §4.2 | — |

- **Todas las edades se evalúan en `display_at`.**
- **R-ONECOORD (FR-27).** Con `display_lag_s = 0` (valor por defecto, `config.py:61`), si `position.mode ∈ {estimated, stale}`, `position.lat/lon` **es** `rendered.lat/lon`.
  - **AC-T4:** distancia entre las coordenadas serializadas ≤ 0,01 m. Hoy: 429,39 m.
  - Con `mode = observed`, `position` es el ancla y la diferencia la declara `rendering_method`.
  - Con `display_lag_s > 0`, `position` describe `calculated_at` y `rendered` describe `display_at`. No son el mismo instante y no aplica.
- **R-SPACE (FR-06).** El consumidor distingue el par (`rendering_method`, `coordinate_space`). No se añaden valores al enum.

### 4.6 Zona de parada en la degradación R8 y DST (B5)

- **Duración real.** La espera programada en una parada es `instant(salida) − instant(llegada)` en segundos reales UTC, nunca la diferencia de reloj de pared. Sintético S15: W1 01:30→03:30 del 2027-10-31 dura **10 800 s reales** (7 200 de pared). `dwell_until` = entrada + 10 800 s; avance `== 0` a +90 s y 444,44 m a +180 s.
- **Retención:** `dwell_until = zone_entry_at + max(min_dwell_s, espera_real)`.
- **Se conserva solo el tiempo que prueban las muestras, no la espera completa** (B5).
  - **Qué es `zone_entry_at`:** el `observed_at` de la observación más antigua de la **racha consecutiva final** de observaciones del mismo viaje cuya zona es la de la misma parada, dentro de la historia que lee la API: hoy `latest` + `previous`, un máximo de 2 muestras.
  - **Es una cota superior de la entrada real**, nunca anterior a ella. La espera puede durar más de lo debido (el tren se retiene de más), nunca menos de lo probado.
  - **Base:** `dwell_basis = muestras` con al menos 2 muestras en la zona; `ancla` si solo está el ancla (reinicio, primera observación; S15b).
  - **Con 3 o más observaciones consecutivas** el par ya no contiene la entrada original. Sintético S16 (entrada real e0, muestras en e0, +20 s y +40 s, espera de 120 s): el par prueba e0+20 s y la retención dura hasta e0+140 s; con las 3 muestras, hasta e0+120 s. El par retiene 20 s **más**.
  - **Si MP-025a amplía la historia leída,** la entrada se acerca a la real sin cambiar la regla.
  - **Aplicado a los cortes reales:** 31/44 anclas tienen 2 muestras consecutivas en la zona, y cambian 14 envolventes de C (§3).
- **R-DST, regla general:** toda conversión horario↔instante usa `service_day_instant` por punto, y toda duración se mide entre instantes UTC. Afecta a la velocidad de tramo (S8, S9) y a la espera (S15).

### 4.7 Revisión coherente (sustituye ADR-0014 §5; B7; implementación en MP-026b)

- **Garantía intrarrespuesta.**
  - **Qué cubre:** cada respuesta que publique `revision`, es decir `/snapshot` **y** `/stations/{id}/board` (`snapshot.py:941-945,1008`).
  - **Cómo:** se construye en **una** transacción `REPEATABLE READ READ ONLY`, de modo que todas sus lecturas (vehículos, `trip_update`, salud y marcador) ven la **misma instantánea MVCC**.
  - **Requisito previo:** el colector confirma cada ciclo en una transacción (`collector.py:115-118`), así que un run es visible entero o no lo es.
  - **Cambio que exige:** `_revision_scope` (`db.py:311-318`) no puede hacer `rollback()` dentro de esa transacción: se lee antes o con `SAVEPOINT`.
- **`sequence` es una cota, no una identidad.**
  - Es el `max(source_ingestion_run.id)` visible en la instantánea, y toda fila de la respuesta tiene `ingestion_run_id ≤ sequence`.
  - `id` es `IDENTITY` (`0001_init.up.sql:65`): dos escritores pueden reservar n y n+1 y confirmar en orden inverso. Por eso **dos respuestas con la misma `sequence` pueden tener contenido distinto**.
  - La identidad es `snapshot_id`. El orden se da por (`scope`, `sequence`, `generated_at`, `tiebreak`).
- **Filtros explícitos.** El filtro `ingestion_run_id ≤ sequence`, y el de la salud por `run.id` (`db.py:178`), son defensivos: no son la garantía.
- **Base vacía:** `sequence = null` (`db.py:296-298`) y `vehicles = []`.

### 4.8 Otras reglas transversales

- **R-CANCEL:** vigencia según §4.4. `cancel_max_age_s` está pendiente (§6).
- **R-REPROJ:** ancla y paradas con la misma primitiva y la misma `geometry_version`. Un cambio de versión invalida la envolvente.
- **R-SKIP (FR-33, limitación declarada):** el modelo no afirma omisiones de parada. Un tren que no para en `cap_stop_id` queda retenido en ella hasta la siguiente observación.

## 5. Mapa FR → regla → criterio

| FR | Reglas | Criterios |
|---|---|---|
| FR-01 | R1, R2, R4, R6 | AC-M1…M4, S1–S3, S5, S2b |
| FR-03 | R1, R4 (zona + `stop_id`; deroga la tolerancia de ±1 m) | AC-M6, S4 |
| FR-04 | R5 (`cap_stop_id`) | AC-M5, S12 |
| FR-05 | R-STALE F1 (o F2) | AC-T1 (o AC-T1′) |
| FR-07 | §4.7 | AC-T6 (MP-026b) |
| FR-26 | R-DST | AC-T2: S8, S9, S15 |
| FR-27 | R-ONECOORD | AC-T4 |
| FR-31 | §4.3 | AC-T7 |
| FR-33 | R-SKIP | sin prueba automática |
| FR-32 | R-CANCEL | AC-T3 |
| FR-06 | R-SPACE | MP-030 |
| — (incoherencia operador↔GTFS) | R7 | AC-S2: S5b, S7, S10 |

## 6. Parámetros y perfil de ensayo (A4)

**Perfil de ensayo P-024:** τ = 50 m, `min_dwell_s` = 30 s y `cancel_max_age_s` = 600 s.
- Son los **valores por defecto provisionales** de MP-025a y los que usan sus pruebas (AC-M5 y AC-M6 dependen de τ).
- MP-028 los sustituye por valores calibrados. Al hacerlo se reejecutan este arnés y las AC con los valores nuevos y se registra el diff.
- No son valores de diseño.

| Parámetro | P-024 | Evidencia (barrido discreto: no demuestra invariancia en el continuo) |
|---|---|---|
| `stop_zone_radius_m` (τ) | 50 m | `19656` exige τ ≥ 5,5 (con 5,3 avanza 662,02 m). Grupo M 7/7 desde τ = 20,8 (con 5 degradaciones R7/R8). Ninguna degradación desde 38,1 (2 con 37,9). Cota superior: separación mínima entre paradas consecutivas; en estos 44 viajes ninguna ≤ 100 m. Si en MP-028 aparecen tramos ≤ 2τ, rige la regla de zonas solapadas de §4.1 |
| `min_dwell_s` | 30 s | Solo R8. Con la entrada por muestras, C con 180 s sigue avanzando en 4/4 salidas retrasadas y 4/7 intermedias, y pierde 7/9 avances legítimos |
| `stale_after_s` | 180 s (`model.py:40`) | Sin cambio (DEC-010) |
| `cancel_max_age_s` | 600 s (provisional) | Reloj y predicado fijados en §4.4 (`anchor.observed_at − trip_update.observed_at`); el valor se calibra en MP-028. Referencia: `operator_delay_max_age_s` = 600 s (`config.py:59`). No hay casos de Madrid en el kit |

## 7. Consecuencias

- **Contrato `/api/v1`:** cambios aditivos y nullables, sin `/api/v2`.
  - `ProgressEnvelopeOut` añade `hold_reason`, `cap_stop_id`, `cap_kind`, `cap_reached_at` y `envelope_id`.
  - `RenderedOut` añade `stop_state {source, operator_status, operator_stop_id, observation_observed_at, coherent}`, `frozen_basis`, `last_confirmed_progress_m` y `dwell_basis`.
  - Instantes en milisegundos.
  - Cambia la semántica documentada de `stale_frozen` y de `position` en `estimated`/`stale`.
  - Habrá más trenes quietos: 36/44 retenidos en el corte.
- **`packages/movement`:** ADR-0012 no cambia.
  - `TripSchedule.stops` aditivo, con ocurrencias.
  - La selección de §4.2 sustituye a `_envelope`.
  - `dwell_end_seconds` deja de usarse en presentación.
  - `schedule_relationship` y `zone_entry_at` entran como argumentos.
- **`apps/api/snapshot.py`:**
  - estado de la observación efectiva;
  - `trip_update` hasta `_render_vehicle` (`:321`);
  - R-ONECOORD en `_legacy_position` (`:245`);
  - §4.7 en `build_snapshot` (`:629`) y en `board`.
- **`apps/web`:**
  - `progressAt` no cambia;
  - se añade `phase` (§4.3 b);
  - aviso de congelación sin `valid_until`;
  - `METHOD_STYLES` indexado por par (método, espacio);
  - rótulos de `hold_reason`/`stop_state`/`CANCELED` (MP-030).
- **Riesgos.** Todos se validan en MP-025b (p50 ≤ 200 m, ≥ 500 pares):
  - semántica de Renfe en vivo (`UNVERIFIED`);
  - salidas retenidas (3/27);
  - paradas omitidas como tope (R-SKIP).

## 8. Criterios de aceptación de MP-025a

Las pruebas usan el perfil P-024 y predicados exactos. Para cortes reales, el cálculo parte del GPS bruto y pasa por el motor de producción.

Tipo:
- **R** = rojo medido en `beb9434`;
- **H** = rojo heredado de una auditoría;
- **G** = guarda (verde antes y después);
- **N** = prueba nueva, sin contraparte en `beb9434`.

| ID | Prueba (predicado) | `beb9434` | Tipo |
|---|---|---|---|
| AC-M1 | `STOPPED_AT` con GPS idéntico con `speed_mps > 0`: `== 0/25` | 25/25 | R |
| AC-M2 | (R1) Pre-salida declarada `STOPPED_AT` con `speed_mps > 0`: `== 0/17` | 17/17 | R |
| AC-M2b | (R2) Pre-salida con avance acumulado hasta min(salida programada, horizonte) `> 0`: `== 0/17`; R2 sin `STOPPED_AT`, en S2b | 17/17 | R |
| AC-M3 | Salidas retrasadas en origen con `speed_mps > 0`: `== 0/4` | 4/4 | R |
| AC-M4 | Intermedias `STOPPED_AT` con `speed_mps > 0`: `== 0/7` | 7/7 | R |
| AC-M5 | Cruzan una parada a más de τ: `== 0/44` | 20/44 | R |
| AC-M6 | `19656` desde su GPS bruto, avance a 30 s `== 0` | 661,12 m | R |
| AC-M7 | `IN_TRANSIT_TO`/`INCOMING_AT` que avanzaron ≥ 100 m con predicción `== 0`: `== 0/9` | 0/9 | G |
| AC-S1 | S1–S5 y S2b (pre-salida, salida retrasada, intermedias, R2 sin `STOPPED_AT`): avance `== 0` donde se exige y fases de §4.3 b | S1–S5 FAIL | R / N (S2b) |
| AC-S2 | S5b, S7, S10: R7 → R8 idéntica a C campo a campo y `coherent = false` | — | N |
| AC-S3 | S11–S14 (casos límite de §4.2) | — | N |
| AC-S4 | S15b y S16: base de la espera (`muestras`/`ancla`) y entrada probada como cota superior | — | N |
| AC-T1 | Retroceso al expirar `== 0` con disponibilidad que **varía entre consultas**, en los 7 escenarios dentro de la garantía de §4.4 (incluido el contraejemplo ocurrió +20 s · visible +181 s) × 25, con reinicio y cambio de versión; aviso visible (vitest) | 25/25 retroceden | R |
| AC-T2 | DST: S8 = 3 000 ± 1e-6 m, S9 = **1000/3 m** (333,333 333…) ± 1e-6 m; S15 (espera de 10 800 s reales) | 8 000 / 0 m | R (S8, S9) / N (S15) |
| AC-T3 | `CANCELED` base (`run ≤` el del ancla, edad ≤ `cancel_max_age_s`): avance `== 0` y `hold_reason = trip_canceled`; un `CANCELED` caducado no se aplica; uno posterior no modifica la envolvente vigente (§4.4) | 2 143,81 m | R |
| AC-T4 | Distancia lat/lon entre `position` y `rendered` serializadas ≤ 0,01 m (`estimated`/`stale`, `display_lag_s = 0`) | 429,39 m | R |
| AC-T5 | Fixture Python↔TS con instantes en ms: |Δ| ≤ 1e-6 m y fases iguales | — | N |
| AC-T6 | (MP-026b) Escrituras intercaladas tras leer el marcador, entre la lectura de vehículos y la de `trip_update`, y dos escritores n/n+1 confirmando en orden inverso. Toda fila con `run_id ≤ sequence`; la respuesta es igual a una lectura de referencia con la **misma** instantánea (`pg_export_snapshot`); se documenta que dos respuestas con igual `sequence` pueden diferir | mezcla reproducida por AUD-06 | H, **no reejecutado** |
| AC-T7 | La fórmula y la semántica de §4.3 son equivalentes en ADR, `DATA_CONTRACTS.md`, `schemas.py`, `rendering.py` y `movement.ts` | ADR-0014 §2 discrepa | revisión documental |
| AC-T8 | Ramas de §4.5: P1 (estado de la observación efectiva), P2, P3, P4 | P1 no existe hoy | N |

MP-025b (en vivo, sin cambios): salto al llegar el ancla p50 ≤ 200 m con ≥ 500 pares.

## 9. Decisión que debe tomar el propietario

1. **Aprobar A** (§4.2, orden total), con C como degradación R8, y las reglas R-CANCEL, R-STALE, R-DST, R-REPROJ, R-ONECOORD, R-SPACE y R-SKIP.
2. **Aprobar** §4.3 (sustituye ADR-0014 §2), §4.4–§4.6 y §4.7 (sustituye §5; se implementa en MP-026b).
3. **Elegir la congelación al caducar:**
   - **F1 (recomendada):** congelar en el final autorizado; criterio AC-T1, retroceso `== 0` con envolvente inmutable por run, bajo la condición de un único colector (§4.4).
   - **F2:** congelar en el ancla y declararlo; criterio AC-T1′, salto `== rewind_m`, hasta 2 371 m.
4. **Aceptar** el perfil P-024 (τ = 50 m, `min_dwell_s` = 30 s, `cancel_max_age_s` = 600 s) como valores provisionales de MP-025a.
5. **Diferido:** calibración (MP-028; incluye el valor de `cancel_max_age_s`), validación en vivo (MP-025b), persistencia de `stop_time_update` (R-SKIP), segmentos OSM (MP-029) e interfaz (MP-030).
6. **Abierto `UNVERIFIED`:** semántica real de `IN_TRANSIT_TO`/`INCOMING_AT` en vivo, y latencia de las salidas retenidas.

## 10. Reproducción

Ver [`docs/evidence/mp-024/README.md`](../evidence/mp-024/README.md): comandos, HEAD, SHA-256 y salida de dos ejecuciones deterministas. Sin base de datos.

## Anexo — Correcciones de la ronda 2

| Punto | Dónde |
|---|---|
| B1 precedencia y casos límite | §4.1, §4.2; arnés `make_plan_a`/`schedule_rules`/`leg`; sintéticos S5b, S7, S10–S14 |
| B2 identidad de la envolvente y F1/F2 | §4.4; arnés `authorized_plan`/`present`/`stale_tests` (camino stale real; 5 escenarios × 25; reinicio; cambio de versión) |
| B3 ramas de presentación | §4.1, §4.5; arnés `presentation_tests` P1–P4 con el motor real; R-ONECOORD medido en lat/lon |
| B4 `hold_reason`, fases y precisión | §4.3 b–c; arnés `phase`/`build_fixture`; `ts_equivalence.cjs` con el `progressAt` de producción |
| B5 DST en la espera y espera consumida | §4.6; sintéticos S15 y S15b |
| B6 honestidad del total | §3 (grupo M 7/7 frente a 3/7 y 1/7, coste 3/27), §8 (grupos M/S/T, tipos R/H/G/N, predicados exactos con `speed_mps > 0` y `== 0`); DEC-047 |
| B7 MVCC frente a cota y alcance | §4.7, AC-T6; `board` incluido |
| A1 inferencias acotadas | §2.3, §2.4; README |
| A2 integridad del arnés | igualdad completa 44/44, `assert` de denominadores, defaults de `ApiConfig` en ejecución, manifiesto con identidad y conjunto esperado |
| A3 cierre verificable y §9 compacto | §8 (tipos, AC-T7 por equivalencia), §5 (AC-S2 → R7), §9 |
| A4 perfil de ensayo | §6 (P-024, revalidación), §4.1 (ocurrencias, ausente frente a contradictorio, zonas solapadas) |

### Cierre de la 2ª ronda ordinaria (B2, B5, B6 y A3 parciales; sin tercera ronda automática)

| Punto | Dónde |
|---|---|
| B2 cancelación conocida tarde | §4.4: tres relojes, envolvente inmutable por run, predicado de edad, replay, condición de la garantía y alternativas descartadas. Arnés `Update`/`authorized_plan`/`present`/`stale_tests`: 8 escenarios con visibilidad variable entre consultas; contraejemplo `19667` 1 071,15 m → 0,0 m; condición violada medida (1 310,66 m). Alineación con la base por run |
| B5 espera conservada | §4.6: solo el tiempo probado por las muestras, como cota superior. Arnés `zone_entry_from_history` aplicado a `build_real` (31 anclas con 2 muestras, 14 envolventes de C cambian) y sintético S16 con tres observaciones. §3 y §6 reconciliados (C con Dmin 180: 4/4 y 4/7) |
| B6 M2 | §3: M2a (R1) en el total y M2b (R2) aparte, con denominadores y con el total si M2b sustituyera a M2a (B2 2/7, C 4/7). §8: AC-M2 y AC-M2b. DEC-047 |
| A3 AC-T2 | §8: S9 = 1000/3 m ± 1e-6 m; el arnés usa el mismo criterio |
| B2 replay por hora (verificación final, sin re-verificación posterior) | §4.4: garantía de replay acotada a la reconstrucción dado el identificador del ancla y su run; el replay por hora civil con `started_at ≤ at` puede seleccionar un ancla aún no confirmada en vivo; la referencia histórica de visibilidad queda pendiente (`UNVERIFIED`) para MP-026b/MP-032. Solo texto: el arnés y sus resultados no cambian |
