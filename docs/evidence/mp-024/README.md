# MP-024 · Evidencia comparativa del modelo de estado de parada

Evidencia offline y reproducible de la enmienda propuesta [`docs/adr/0014-amendment-stop-state.md`](../../adr/0014-amendment-stop-state.md).
Compara la envolvente de producción (`beb9434`) con tres alternativas de diseño y con la alternativa descartada «subir la tolerancia». Lo hace sobre los cortes reales congelados del 2026-11-20 y sobre casos sintéticos, y evalúa los criterios de aceptación propuestos para MP-025a.

**Qué es y qué no es.** Las alternativas del guion son **prototipos de diseño** que sirven para medir criterios. **No** son la implementación de MP-025a ni la sustituyen. El guion no modifica `packages/`, `apps/` ni `services/`: los importa en solo lectura. Las constantes de las alternativas (`TAU_STOP_M`, `D_MIN_S`, `OFFSET_SYM_S`) son **valores de arnés** con barrido de sensibilidad, no valores de diseño; su calibración corresponde a MP-028.

## Ficheros

| Fichero | Contenido |
|---|---|
| `stop_state_comparison.py` | Arnés: validación (§3.4), cortes reales, sensibilidad, casos sintéticos y criterios de aceptación |
| `output.txt` | Salida completa de la ejecución registrada (texto) |
| `results.json` | La misma ejecución en JSON (`--json`) |

## Cómo reproducir

```sh
# Desde la raíz del worktree. Python 3.12 con requirements.txt (pydantic). Sin red ni base de datos.
python3 docs/evidence/mp-024/stop_state_comparison.py \
  --replay /Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay \
  --json docs/evidence/mp-024/results.json > docs/evidence/mp-024/output.txt
# Comprobación de integridad de los cortes (guion del propio kit, solo stdlib):
(cd /Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay && python3 -I comprobar.py)
```

**Entorno de la ejecución registrada:** 2026-11-25, `python3` 3.12.3 (pyenv), pydantic 2.13.4. La ejecución tardó unos 42 s. No usó base de datos: no se abrió **ningún** DSN, ni `127.0.0.1:5433` ni contenedores. **HEAD de ejecución:** `aee334ebecb722b00bbd516be6ec900cdfa024e7`, con el arnés aún sin commitear. El guion comprueba que `packages/`, `apps/`, `services/` e `infra/` son idénticos a `beb9434` (`git diff --quiet beb9434 -- …` → `True`). Por tanto, la línea base medida **es** `beb9434`.

**Determinismo:** dos ejecuciones consecutivas producen un `results.json` idéntico byte a byte (`cmp`).

## Entradas (fuera de Git por decisión; citadas por hash)

Directorio: `/Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay/`. El guion verifica cada SHA-256 contra `manifest.json` y aborta si alguno no coincide. `comprobar.py` del kit también pasa (119/121 vehículos de Madrid, 121 matches en `1533`).

| Fichero | SHA-256 |
|---|---|
| `1532/vehicle_positions.json` | `c50da3eecdd34ab7b85f3e039e759cf4740788cd4725310276d69b7ab1c13a5f` |
| `1532/trip_updates.json` | `6d8e63bca6cfdbf5496cebe78b318ec72d831f5ebad1fe22b5c8a02d49589407` |
| `1532/alerts.json` | `88c7eefec6a6bb23139cf5b65994c3378da9373094dd2ab650ddf6e86afde43a` |
| `1533/vehicle_positions.json` | `77f8faa14ccd183fc16f81702dc8af0ac0c98dc5558582a684bb96f3e59ca9e9` |
| `1533/trip_updates.json` | `60e2680fb548b79576144ddf3e0578d29f797390e8e4638d689403a780a04c7f` |
| `1533/alerts.json` | `fa7d28bb85e7f7c36883c112ac63417fc4ef9009ad26623df428469b513cf4f9` |
| `fomento_transit.zip` | `c5b40823c5cacbec6d9a21d88ec0530d9604a6d4331df98c330e608f0bacb11e` |
| `manifest.json` | `40e0b99af024f67e7e4015c6830f8ee5fad7e062f48d874e962e6e1eba81f9b1` |

Las geometrías de corredor se leen de `tests/fixtures/` del propio repositorio, igual que en los arneses de AUD-09.

## Validación del arnés (ORCHESTRATION_POLICY §3.4)

El guion localiza cada constante con una expresión regular que debe aparecer **una sola vez** y comprueba su valor en tiempo de ejecución. Si algo no cuadra, aborta con `ARNÉS INVÁLIDO`.

| Constante | Dónde | Valor |
|---|---|---|
| `observed_max_age_s` | `packages/movement/model.py:39` | 60,0 |
| `stale_after_s` | `packages/movement/model.py:40` | 180,0 |
| `max_estimated_speed_kmh` | `packages/movement/model.py:45` | 160,0 |
| `max_estimated_acceleration_mps2` | `packages/movement/model.py:46` | 1,2 |
| `dwell_end_seconds(tolerance_m=1.0)` | `packages/movement/schedule.py:120` | 1,0 |
| horizonte del ancla observada = `valid_until` = ancla + `stale_after_s` | `packages/movement/rendering.py:279` y `:346` | 180 s **desde el ancla** (no los 190 s de los arneses de AUD-01/04) |
| guarda `anchor_at < candidate < horizon_end` | `packages/movement/rendering.py:192` | — |
| `operator_delay_max_age_s` | `apps/api/config.py:59` | 600 |
| `display_lag_s` | `apps/api/config.py:61` | 0 |

- **La línea base llama a producción:** `MovementEngine.position` → `render_from_movement`. Sobre las 44 circulaciones, la envolvente publicada es idéntica a `_envelope(…, horizon_end=valid_until)`. También es idéntica a la variante de B con acotación ±∞, que es la reimplementación usada para B. Resultado: **44/44**.
- **La línea base reproduce las cifras auditadas:**

  | Cifra | Auditoría | Este arnés |
  |---|---|---|
  | `STOPPED_AT` con avance | 28/28 | 28/28 |
  | `STOPPED_AT` con GPS idéntico y avance | 25/25 | 25/25 |
  | Pre-salida con avance | 17/17 | 17/17 |
  | Salidas retrasadas en origen | 4 | 4 |
  | `STOPPED_AT` intermedias | 7 | 7 |
  | Envolventes que atraviesan una estación | 29/44 | 29/44 |
  | `19656` a 30 s / 60 s | 661,1 / 1 322,2 m | 661,1 / 1 322,2 m |
  | Salto al llegar el ancla siguiente | p50 1 229,15 / máx 3 274,23 m | p50 1 229,1 / máx 3 274,2 m |
  | FR-05: retroceso 179→181 s | 25/25, p50 2 357,9 / máx 3 959,2 m | 25/25, p50 2 357,9 / máx 3 959,2 m |
  | FR-27: discrepancia `position`/`rendered` | 429,5 m | 429,5 m |

- **Las alternativas reutilizan primitivas de producción:** `TripSchedule`, `Corridor.project_station`, `parse_gtfs_time`, `service_day_instant` y `ProgressEnvelope`, con sus invariantes y su `progress_at`. El guion comprueba que las paradas que reconstruye coinciden con los puntos de `TripSchedule`.

## Hechos del corte `1533` que condicionan el diseño (44 circulaciones con cadena completa)

- **Cobertura del estado del operador:** `current_status` está presente en **44/44**, y `current_stop_id` pertenece al viaje en **44/44**.
- **`IN_TRANSIT_TO` no apunta a la parada siguiente.** En **4 de 8** casos `current_stop_id` queda **más de 1 km por detrás** del ancla. Los cuatro casos son `20277`, que está 4 288,5 m pasado su `60100`, y `20281`, `20845` y `20846`, entre 1 848,9 y 3 234,5 m (`in_transit_behind_detail`). El sondeo exploratorio previo situó a los otros 4 a ≤ 5,4 m de su parada; ese dato no lo imprime el arnés. En este feed, `IN_TRANSIT_TO X` se comporta como «salió de X», no como «va hacia X» (que es la semántica de la especificación GTFS-RT). Esto está medido en un solo corte; la semántica en vivo es `UNVERIFIED` (MP-028).
- **Hueco entre la parada declarada y el ancla en los 28 `STOPPED_AT`** (progreso de la parada − progreso del ancla):
  - **21 en origen:** de −38,0 a +8,2 m. El extremo corresponde a las cocheras de origen `37012`/`17005`.
  - **7 intermedias:** de −3,6 a +2,5 m.

  Con τ ≥ 40 m las 28 son coherentes; con τ = 20,8 m, 5 caen en degradación (sección «Sensibilidad»).
- **`19656` está `post_llegada` y en marcha.** Está +141 s pasada su última llegada programada, va `INCOMING_AT 35002` a −5,38 m de la parada y se movió a 75,0 km/h entre cortes (reproducido con `scratch/aud04_cohorte_19656.py`). **Retener por ventana temporal tras la llegada sería falso.**
- **Reproyección:** la coordenada `rendered` del ancla coincide con la proyección `map_matched` (p50 0,0 m, máx 0,0 m sobre 44).

## Resultados sobre los cortes reales

Definiciones de las columnas:
- **«Con avance»:** más de 1 m sobre el ancla dentro del horizonte de producción (`valid_until`).
- **M5:** la parada se supera **estrictamente** antes de `valid_until` con margen de 1 m (definición de `aud09_stop_crossing.py` v2).
- **M5b:** igual que M5, pero excluye la parada en cuya zona τ ya está el tren.
- **M7:** usa el ancla de `1532` y compara con la verdad de `1533` (77 s; 44 pares).
- **H2b:** circulaciones `IN_TRANSIT_TO`/`INCOMING_AT` en `1532` que avanzaron ≥ 100 m y a las que la alternativa no da avance.

| Métrica | BASE `beb9434` | D: tolerancia 50 m (descartada) | B1: offset ±600 s | B2: B1 + pre-salida | C: segmentos (τ 50, Dmin 30) | **A: operador (τ 50)** |
|---|---|---|---|---|---|---|
| M1 `STOPPED_AT` con GPS idéntico y avance | 25/25 | 25/25 | 21/25 | 10/25 | 10/25 | **0/25** |
| M2 pre-salida con avance | 17/17 | 17/17 | 13/17 | 2/17 | 2/17 | **0/17** |
| M3 salida retrasada en origen con avance | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **0/4** |
| M4 `STOPPED_AT` intermedia con avance | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 | **0/7** |
| M5 atraviesan ≥ 1 parada (1 m) | 29/44 | 29/44 | 26/44 | 23/44 | 13/44 | 2/44 (\*) |
| M5b atraviesan ≥ 1 parada (> τ) | 20/44 | 20/44 | 22/44 | 20/44 | 0/44 | **0/44** |
| M6 `19656`: avance a 30 s / 60 s | 661,1 / 1 322,2 m | 661,1 / 1 322,2 m | 661,1 / 1 322,2 m | 661,1 / 1 322,2 m | 0 / 0 m | **0 / 0 m** |
| M7 error a 77 s: p50 / p90 / máx | 1 229,1 / 1 731,5 / 3 274,2 m | ídem | 950,5 / 2 216,3 / 3 422,2 m | 876,0 / 1 921,0 / 3 422,2 m | 570,1 / 1 338,3 / 3 669,4 m | 0,0 / 1 523,8 / 3 274,2 m |
| M7 sobreavance > 100 m | 32 | 32 | 24 | 18 | 15 | **2** |
| M7 avance legítimo perdido (cualquier estado) | 0 | 0 | 0 | 0 | 0 | **3** (†) |
| H2b avance perdido (`IN_TRANSIT_TO`/`INCOMING_AT`) | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| M8 retroceso al caducar si se congela en el ancla (F2): p50 / máx | 2 816,7 / 5 400,6 m | ídem | 2 558,3 / 8 000,0 m | 2 221,9 / 8 000,0 m | 1 588,1 / 3 311,0 m | 0,0 / 2 371,0 m |

(\*) Las dos son la parada en la que el tren **ya está** y de la que sale: `19667` está a +2,5 m de `35605` y `20281` a +6,9 m de `37002`. Son ruido de proyección dentro de la zona τ, no cruces reales.

(†) Las tres circulaciones son `19671`, `20284` y `20836`. Estaban `STOPPED_AT` en `1532` y salieron antes de `1533`: 2 204,0 m, 2 424,5 m y 1 860,2 m en 77 s (`M7_lost_detail` en `output.txt`). A las retiene hasta la siguiente observación. Es el coste explícito de A, acotado por la cadencia del feed: 77 s entre los cortes del kit, ~20 s en vivo según MP-003. El error en vivo es `UNVERIFIED` (MP-025b/MP-028).

**Lectura:**
- **D** (solo subir la tolerancia) es idéntica a la línea base en todas las métricas. Con 50 m la espera se detecta, pero la guarda la descarta (`19656` sigue en 661,1 m), lo que confirma el contrafactual B de AUD-04.
- **B1** apenas corrige y **empeora** el peor caso: la acotación desplaza el horario y satura los 160 km/h (8 000 m al caducar; 3 422,2 m de error máximo).
- **B2** cubre la pre-salida, pero deja intactas las 4 salidas retrasadas y las 7 intermedias. Son las 11/28 que predijo la auditoría.
- **C** resuelve `19656` y los cruces de parada, pero sin el estado del operador no distingue un tren parado de uno que pasa por la zona de parada. La sensibilidad lo confirma: solo con Dmin = 180 s retiene las 4 + 7, y entonces pierde 7 de 9 avances legítimos.

## Sensibilidad (cortes reales)

| Variante | M1 | M5 | `19656` 30/60 s | M7 p50/p90/máx | H2b perdidos | Degradados |
|---|---|---|---|---|---|---|
| A τ = 5 m | 4/25 | 4/44 | 662,0 / 1 324,0 m | 0,0 / 1 730,3 / 3 274,2 | 0/9 | 17 |
| A τ = 20,8 m (p95 de proyección) | 0/25 | 2/44 | 0 / 0 | 0,0 / 1 523,8 / 3 274,2 | 0/9 | 5 |
| A τ = 40 / 50 / 100 m | 0/25 | 2/44 | 0 / 0 | 0,0 / 1 523,8 / 3 274,2 | 0/9 | 0 |

| Variante | M1 | M3 | M4 | M7 p50/p90/máx | H2b perdidos |
|---|---|---|---|---|---|
| C Dmin = 0 s | 10/25 | 4/4 | 7/7 | 754,9 / 1 571,0 / 3 274,2 | 0/9 |
| C Dmin = 30 s | 10/25 | 4/4 | 7/7 | 570,1 / 1 338,3 / 3 669,4 | 0/9 |
| C Dmin = 60 s | 10/25 | 4/4 | 7/7 | 206,2 / 1 672,4 / 4 064,6 | 0/9 |
| C Dmin = 180 s | 2/25 | 0/4 | 0/7 | 0,0 / 1 899,3 / 4 288,5 | **7/9** |

**Conclusión para la calibración (MP-028):**
- τ debe ser ≥ 5,38 m para `19656`.
- τ debe ser ≥ 38 m para que las 28 `STOPPED_AT` de este corte sean coherentes sin degradar. Entre 40 y 100 m no cambia nada en este corte.
- La cota superior razonable la fija la distancia mínima entre paradas consecutivas. Queda sin medir aquí: `UNVERIFIED`.

## Casos sintéticos

Sobre el horario **real** de `1023V19656C5` (paradas con espera de 60 s) y sobre dos horarios sintéticos de 20 000 m en las fechas de cambio de hora de 2027.

| Caso (criterio) | BASE | D | B1 | B2 | C | A |
|---|---|---|---|---|---|---|
| S1 pre-salida −300 s, `STOPPED_AT` (0 m en el horizonte) | FAIL 2 811,3 m | FAIL | FAIL | PASS | PASS | PASS |
| S2 pre-salida −60 s (0 m antes de la salida) | FAIL 921,5 m | FAIL | FAIL | PASS | PASS | PASS |
| S3 salida retrasada +120 s, `STOPPED_AT` (0 m) | FAIL 2 811,3 m | FAIL | FAIL | FAIL | FAIL 2 019,9 m | PASS |
| S4 intermedia con espera 60 s, ancla +5,38 m (0 m a 30 s) | FAIL 417,2 m | FAIL 417,2 m | FAIL | FAIL | PASS | PASS |
| S5 intermedia sin espera programada, `STOPPED_AT` (0 m) | FAIL 2 364,5 m | FAIL | FAIL | FAIL | FAIL 1 969,8 m | PASS |
| S6 `CANCELED` a mitad de tramo (0 m, R-CANCEL) | FAIL 2 143,8 m | FAIL | FAIL | FAIL | PASS | PASS |
| S6b control en marcha (> 1 m) | PASS 2 143,8 m | PASS | PASS | PASS | PASS 1 181,9 m | PASS 1 181,9 m |
| S7 `STOPPED_AT` con `stop_id` ajeno al viaje (degrada y lo declara) | N/A | N/A | N/A | N/A | N/A | PASS |
| S10 `INCOMING_AT` con la parada 1 182 m por detrás (no retiene y lo declara) | N/A | N/A | N/A | N/A | N/A | PASS |
| S8 DST 2027-03-28, 01:50→02:10 (3 000,0 ± 1 m en 180 s reales) | FAIL 8 000,0 m | FAIL | FAIL | FAIL | PASS | PASS |
| S9 DST 2027-10-31, 01:30→03:30 (333,3 ± 1 m) | FAIL 0,0 m | FAIL | FAIL | FAIL | PASS | PASS |

**Advertencia de equidad.** S6, S8, S9 y AC-6 dependen de reglas **transversales**: R-CANCEL, R-DST y R-STALE. Los prototipos A y C las incorporan; B y D conservan la aritmética de producción por definición. Cualquier alternativa podría adoptarlas. Lo que **discrimina** entre alternativas son M1–M5b, M6, M7, S3, S4 y S5.

## Criterios de aceptación propuestos para MP-025a (sección 5 de `output.txt`)

| Criterio | BASE `beb9434` | D | B1 | B2 | C | A |
|---|---|---|---|---|---|---|
| Total PASS | **1/11** | 2/11 | 2/11 | 2/11 | 7/11 | **11/11** |

- La línea base solo pasa **AC-4**. Es la prueba de no regresión: no perder el avance legítimo. Es correcto que sea verde en `beb9434`.
- Las otras **10** son **ROJO en `beb9434`**.
- **AC-10** (FR-27, una coordenada por instante) **no se mide en el prototipo**: depende de la regla R-ONECOORD en `apps/api`. De ella solo se mide la línea base, con 429,5 m de discrepancia.

## Límites y no verificado

- **`UNVERIFIED`:**
  - la semántica de `IN_TRANSIT_TO`/`INCOMING_AT` en vivo;
  - la presencia de `current_status` fuera de este corte;
  - el error de A en vivo (cadencia ~20 s) y la frecuencia de las salidas inmediatamente posteriores a un `STOPPED_AT`.

  Todo ello requiere la captura de MP-028 y la validación de MP-025b (salto p50 ≤ 200 m con ≥ 500 pares).
- **Cancelaciones:** no hay ningún caso de Madrid en los cortes. Los 7 `CANCELED` con posición son del núcleo 51 (AUD04-P2-007). R-CANCEL solo se prueba con casos sintéticos.
- **DST:** el `calendar.txt` del kit no tiene viajes en las fechas de cambio de hora (AUD-04). Se prueba con horarios sintéticos y la reachability real sigue siendo la que midió AUD-04.
- **FR-07 (revisión coherente, §5 de la enmienda):** **NO EJECUTADO.** Exige una prueba con dos conexiones PostgreSQL reales y corresponde a MP-026b. Este arnés no usa base de datos.
- **FR-33 (`stop_time_update` por parada):** no se mide. La enmienda lo declara como limitación.
- **Alcance del corte:** un solo par de cortes a las 15:32–15:33 locales y 44 circulaciones con cadena completa. **No** es una muestra del día.
