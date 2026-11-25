# MP-024 · Evidencia del modelo de estado de parada (cierre de la 2ª ronda)

Evidencia offline y reproducible de la enmienda [`docs/adr/0014-amendment-stop-state.md`](../../adr/0014-amendment-stop-state.md), en estado `Propuesto`.

Historia de revisión:
- **Ronda 2:** respondió al dictamen `CHANGES_REQUESTED` de Codex `gpt-6.2-astra` · high sobre `f0f8224` (B1–B7, A1–A4).
- **Cierre de la 2ª ronda ordinaria:** corrige los cuatro puntos que Codex dejó parciales sobre `559a5c2`: B2, B5, B6 y A3. La tabla de correcciones está en el anexo del ADR.

> **Sin tercera ronda automática** (ORCHESTRATION_POLICY §3.3). Las correcciones de este cierre **no las re-verifica Codex** salvo que el propietario lo decida. Lo que aquí se afirma está respaldado por `output.txt` y por las comprobaciones del propio arnés, no por una revisión independiente posterior.

**Qué es y qué no es:**
- Las alternativas del guion son **prototipos de diseño**. No son MP-025a.
- El guion importa `packages/` y `apps/` en solo lectura y no los modifica.
- τ = 50 m, `min_dwell_s` = 30 s y `cancel_max_age_s` = 600 s forman el **perfil de ensayo P-024**: valores provisionales, no de diseño. Los calibra MP-028.

## Ficheros

| Fichero | Contenido |
|---|---|
| `stop_state_comparison.py` | Arnés v2. Secciones 0–6: validación, hechos, grupo M, sensibilidad, grupo S, camino stale (grupo T) y ramas de presentación. Opción `--fixture-out` para AC-15 |
| `ts_equivalence.cjs` | Evalúa el `progressAt` **de producción** (`apps/web/src/domain/movement.ts` transpilado sin cambios) sobre el fixture, más un prototipo JS de `phase` |
| `output.txt`, `results.json` | Salida de la ejecución registrada |
| `ac15_fixture.json`, `ts_equivalence.txt` | Fixture AC-15 y resultado de Node |

## Cómo reproducir

```sh
R=/Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay
E=docs/evidence/mp-024
python3 $E/stop_state_comparison.py --replay $R --json $E/results.json \
  --fixture-out $E/ac15_fixture.json > $E/output.txt
# Transpilado del TS de producción a un directorio temporal. El tsc 6.0.3 se toma, solo como herramienta,
# del node_modules del worktree h4-planning; el código que se transpila es el de este worktree.
TSC=/Users/matu/orca/workspaces/madrid-pulse/h4-planning/apps/web/node_modules/.bin/tsc
$TSC --outDir /tmp/mp024-ts --module commonjs --target es2022 --skipLibCheck --ignoreDeprecations 6.0 \
  apps/web/src/domain/movement.ts
node $E/ts_equivalence.cjs /tmp/mp024-ts/movement.js $E/ac15_fixture.json > $E/ts_equivalence.txt
(cd $R && python3 -I comprobar.py)   # integridad del kit, solo stdlib
```

**Entorno de la ejecución registrada (2026-11-25):**
- `python3` 3.12.3, pydantic 2.13.4, Node v20.20.0, tsc 6.0.3.
- **Sin base de datos:** no se abrió ninguna conexión. Para validar los valores por defecto de `ApiConfig.from_env()`, que por defecto apunta a 5433, se sustituye la DSN por `postgresql://mp024-no-connect.invalid:1/none` y no se conecta.
- **HEAD de ejecución:** `559a5c2e98a3be088713ccdcd0d1bcbd8ea17c4f` (ronda 2), con los cambios del cierre aún sin commitear. El guion comprueba que `packages/`, `apps/`, `services/` e `infra/` son idénticos a `beb9434`.

**Determinismo:** dos ejecuciones en directorios independientes producen `output.txt`, `results.json` y `ac15_fixture.json` idénticos byte a byte (`cmp`).

| Fichero | SHA-256 |
|---|---|
| `output.txt` | `2ba8713743472ed88be562e5b588308db9fecebef30a1a97962bb466d32ed75a` |
| `results.json` | `6073b942e86021ee4498ebb9b895bc170f2c0b13e58e15ca0f829d5023b9f860` |
| `ac15_fixture.json` | `dda61ba411b418ffa0c8c01cea8d146df401ba2f23981e7463ace2bac83a7869` |

Las salidas de los comandos registrados:

| Comando | Resultado |
|---|---|
| Arnés | exit 0 |
| `tsc` | exit 0 |
| `node ts_equivalence.cjs` | exit 0 |

## Entradas

Fuera de Git y citadas por hash: `/Users/matu/orca/workspaces/madrid-pulse/h4-planning/data/hito-03/replay/`. El guion separa la **identidad del manifiesto** de su **validación interna**:
- Identidad: `sha256(manifest.json)` = `40e0b99af024f67e7e4015c6830f8ee5fad7e062f48d874e962e6e1eba81f9b1`.
- Validación interna: comprueba que el conjunto de entradas es **exactamente** el esperado (7 ficheros) y verifica cada SHA-256 contra el manifiesto.

| Fichero | SHA-256 |
|---|---|
| `1532/vehicle_positions.json` | `c50da3eecdd34ab7b85f3e039e759cf4740788cd4725310276d69b7ab1c13a5f` |
| `1532/trip_updates.json` | `6d8e63bca6cfdbf5496cebe78b318ec72d831f5ebad1fe22b5c8a02d49589407` |
| `1532/alerts.json` | `88c7eefec6a6bb23139cf5b65994c3378da9373094dd2ab650ddf6e86afde43a` |
| `1533/vehicle_positions.json` | `77f8faa14ccd183fc16f81702dc8af0ac0c98dc5558582a684bb96f3e59ca9e9` |
| `1533/trip_updates.json` | `60e2680fb548b79576144ddf3e0578d29f797390e8e4638d689403a780a04c7f` |
| `1533/alerts.json` | `fa7d28bb85e7f7c36883c112ac63417fc4ef9009ad26623df428469b513cf4f9` |
| `fomento_transit.zip` | `c5b40823c5cacbec6d9a21d88ec0530d9604a6d4331df98c330e608f0bacb11e` |

## 0. Validación del arnés (ORCHESTRATION_POLICY §3.4; A2)

- **Constantes:** cada una se localiza con `archivo:línea` (patrón único) y, si tiene valor en ejecución, se compara con él.

  | Constante | Dónde | Valor | Comprobado |
  |---|---|---|---|
  | `observed_max_age_s` | `model.py:39` | 60 | texto + ejecución |
  | `stale_after_s` | `model.py:40` | 180 | texto + ejecución |
  | `max_estimated_speed_kmh` | `model.py:45` | 160 | texto + ejecución |
  | `max_estimated_acceleration_mps2` | `model.py:46` | 1,2 | texto + ejecución |
  | `tolerance_m` | `schedule.py:120` | 1,0 | texto + ejecución |
  | horizonte = `valid_until` | `rendering.py:279`, `:346` | — | texto |
  | guarda de espera | `rendering.py:192` | — | texto |
  | `operator_delay_max_age_s` | `config.py:59` | 600 | texto + ejecución (`ApiConfig.from_env()` sin overrides `MADRID_PULSE_*`) |
  | `display_lag_s` | `config.py:61` | 0 | texto + ejecución (ídem) |

- **Equivalencia de la línea base:** igualdad **completa de campos** (`==` del dataclass) entre la envolvente publicada por `render_from_movement`, `_envelope(valid_until)` y la variante B(±∞). Resultado: **44/44**, con denominador 44 comprobado mediante `assert`.
- **Denominadores comprobados con `assert`:**
  - 44 circulaciones y 28 `STOPPED_AT`;
  - 25 con GPS idéntico, 17 pre-salida, 4 salidas retrasadas y 7 intermedias;
  - 44 pares, todos de 77,0 s;
  - 9 `IN_TRANSIT_TO`/`INCOMING_AT` que avanzaron y 27 `STOPPED_AT` en `1532`;
  - 25 en ventana para el camino stale.
- **Reproyección:** n = 44, distancia máxima entre el ancla `rendered` y `map_matched` de **0,0016 m** (antes se informaba redondeada como 0,0 m).
- **Línea base de producción:**
  - FR-05: camino stale **real** (`render_from_movement` a 179 s y 181 s, comprobado `STALE_FROZEN`) → 25/25 retroceden, p50 2 357,87 m, máx 3 959,22 m.
  - FR-27: 2 975 muestras → 429,52 m en progreso y **429,39 m entre lat/lon**.

## 1. Hechos del corte (A1: acotados al intervalo observado)

- **`IN_TRANSIT_TO` con la parada más de 1 km por detrás:** 4/8 casos:

  | Viaje | Parada | Distancia por detrás |
  |---|---|---|
  | `20277` | `60100` | 4 288,52 m |
  | `20281` | `37011` | 2 416,28 m |
  | `20845` | `35609` | 3 234,47 m |
  | `20846` | `35606` | 1 848,87 m |

- **Estructura GTFS de los 44 viajes (829 tramos):**
  - 0 `stop_id` repetidos;
  - 0 tramos con separación ≤ τ;
  - 0 tramos con separación ≤ 2τ;
  - 0 tramos con duración real ≤ 0.

  Esos casos límite solo se prueban con sintéticos.
- **Entrada en zona por muestras (B5):**
  - 31/44 anclas tienen 2 observaciones consecutivas (`1532`, `1533`) en la zona de la misma parada.
  - Aplicar esa entrada cambia **14** envolventes de C, la misma lista con Dmin = 30 y con Dmin = 180 (`output.txt` §1).
- **`19656`:** 75,0 km/h es la **media del arco en los 77 s previos** a `1533` (`scratch/aud04_cohorte_19656.py`). No es una velocidad instantánea ni dice qué hizo después.
- **Cruces residuales de A con margen de 1 m:** `19667` (a +2,47 m de `35605`) y `20281` (a +6,91 m de `37002`; el operador declara `37011`). Lo **probado** es que hay cero cruces *fuera de zona*. Atribuirlos a ruido de proyección es `UNVERIFIED`.

## 2. Grupo M: hechos de movimiento sobre cortes reales (discriminantes; predicados exactos)

| Criterio | BASE | D tol 50 | B1 | B2 | C | **A** |
|---|---|---|---|---|---|---|
| M1 `STOPPED_AT` con GPS idéntico y `speed_mps > 0` | 25/25 | 25/25 | 21/25 | 10/25 | 10/25 | **0/25** |
| M2a (R1) pre-salida, las 17 declaradas `STOPPED_AT`, con `speed_mps > 0` | 17/17 | 17/17 | 13/17 | 2/17 | 2/17 | **0/17** |
| M3 salida retrasada con `speed_mps > 0` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **0/4** |
| M4 intermedias con `speed_mps > 0` | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 | **0/7** |
| M5 cruces a más de τ | 20/44 | 20/44 | 22/44 | 20/44 | 0/44 | **0/44** |
| M6 `19656` a 30 s `== 0` | 661,12 m | 661,12 m | 661,12 m | 661,12 m | 0 | **0** |
| M7 guarda (predicción `== 0` con ≥ 100 m observados) | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| **PASS** (con M2a) | **1/7** | 1/7 | 1/7 | 1/7 | 3/7 | **7/7** |
| M2b (R2), aparte: avance hasta min(salida programada, horizonte) `> 0` | 17/17 | 17/17 | 13/17 | 0/17 | 0/17 | 0/17 |
| PASS si M2b sustituyera a M2a | 1/7 | 1/7 | 1/7 | 2/7 | 4/7 | 7/7 |
| Coste: `STOPPED_AT` en `1532` que salieron, predicción `== 0` | 0/27 | 0/27 | 0/27 | 0/27 | 0/27 | **3/27** |
| Error a 77 s, p50 / p90 / máx (m) | 1 229,15 / 1 731,54 / 3 274,23 | = BASE | 950,49 / 2 216,27 / 3 422,22 | 875,97 / 1 921,01 / 3 422,22 | 570,10 / 1 338,31 / 3 669,40 | 0,00 / 1 523,78 / 3 274,23 |

- Los criterios M1–M4 se solapan.
- **M2a frente a M2b (B6).** M2a mide R1: no debe moverse un tren pre-salida declarado `STOPPED_AT` aunque su salida programada caiga dentro del horizonte. M2b mide R2: el avance antes de la salida programada. B2 y C solo avanzan después de la salida, así que pasan M2b y fallan M2a en 2/17. Las 17 son `STOPPED_AT` (comprobado con `assert`). R2 sin `STOPPED_AT` lo prueba S2b.
- **C con la entrada por muestras:** la tabla de grupo M de C no cambia con Dmin = 30. El máximo de M8 pasa de 3 310,99 a 3 973,18 m.
- El coste de A son `19671` (2 204,0 m), `20284` (2 424,5 m) y `20836` (1 860,2 m). El instante real de salida es desconocido.

## 3. Sensibilidad (barrido discreto: no prueba invariancia en el continuo)

| τ (A) | Grupo M | M1 | `19656` a 30 s | Degradaciones R7/R8 |
|---|---|---|---|---|
| 5 / 5,3 | 4/7 | 1/25 | 662,02 m | 17 |
| 5,5 / 10 | 5/7 | 1/25 | 0 | 13 / 7 |
| 20,8 / 30 | 7/7 | 0/25 | 0 | 5 |
| 37,9 | 7/7 | 0/25 | 0 | 2 |
| 38,1 … 150 | 7/7 | 0/25 | 0 | 0 |

| Variante de C | M3 | M4 | Guarda |
|---|---|---|---|
| Dmin = 0 / 30 / 60 | 4/4 | 7/7 | 0/9 |
| Dmin = 180 | **4/4** | **4/7** | **7/9 perdidos** |

Las cifras se calculan con la entrada en zona por muestras aplicada a los cortes. La ronda 2 publicaba 0/4 y 0/7 con Dmin = 180 porque omitía la historia y la espera empezaba en el ancla: es la discrepancia que señaló el revisor (B5), ya reconciliada.

## 4. Grupo S: pruebas sintéticas de reglas (predicados exactos)

Sobre el horario real de `1023V19656C5`, salvo S8, S9 y S12–S16, que usan horarios sintéticos de geometría controlada.

| Caso | Criterio | BASE | A | Otros |
|---|---|---|---|---|
| S1 pre-salida −300 s, `STOPPED_AT` | avance `== 0` | FAIL 2 811,25 m | PASS (R1) | B2 PASS, C PASS |
| S2 pre-salida −60 s | `== 0` 1 ms antes de la salida | FAIL 937,07 m | PASS | B2 y C PASS |
| S2b R2 con `IN_TRANSIT_TO` | 0 antes de la salida, > 0 después, fases `hold → moving → cap:stop`, `progress(cap_reached_at) == max` | — | PASS (506,07 m a +30 s) | — |
| S3 salida retrasada +120 s | `== 0` | FAIL | PASS | C FAIL 2 019,90 m |
| S4 intermedia con espera, +5,38 m | `== 0` a 30 s | FAIL 417,19 m | PASS | C PASS |
| S5 intermedia sin espera programada | `== 0` | FAIL 2 364,45 m | PASS | C FAIL 1 969,82 m |
| **S5b contraejemplo del revisor** | R7 → R8 == C campo a campo, `== 0` a 20 s | — | **PASS** (v1: 262,64 m) | — |
| S6 `CANCELED` | `== 0` y `hold_reason = trip_canceled` | FAIL 2 143,81 m | PASS | C PASS |
| S6b control en marcha | avance > 0 | PASS | PASS | todos PASS |
| S7 `stop_id` ajeno | R7 → R8 == C, `coherent = false` | — | PASS | C: N/A |
| S10 `INCOMING_AT` con la parada 1 182 m por detrás | ídem | — | PASS | C: N/A |
| S11 ancla 500 m antes de la primera parada | retención `outside_schedule_extent` | — | PASS | — |
| S12 zonas solapadas (paradas a 0 y 60 m) | tope = Z2 | — | PASS | — |
| S13 tramo de duración real 0 | v = 3 000/180 m/s, tope T1 | — | PASS | — |
| S14 `stop_id` repetido | ocurrencia más cercana, R1 | — | PASS | — |
| S8 DST 2027-03-28 | 3 000 ± 1e-6 m | FAIL 8 000,00 m | PASS | B1/B2/D FAIL, C PASS |
| S9 DST 2027-10-31 | **1000/3 m** ± 1e-6 m (medido: 333,33333333333394 m) | FAIL 0,00 m | PASS | ídem |
| S15 espera DST de R8 (01:30→03:30, 2027-10-31) | 10 800 s reales; `== 0` a +90 s; > 0 a +180 s; base `muestras` (entrada calculada desde 2 observaciones) | — | PASS | C PASS |
| S15b sin muestra previa en la zona | retención declarada con base `ancla` | — | PASS | C PASS |
| S16 tres observaciones consecutivas en zona (e0, +20, +40 s), espera de 120 s | el par prueba la entrada e0+20 s (`dwell_until` e0+140 s); con 3 muestras, e0 (e0+120 s); el par retiene **más**, nunca menos | — | PASS | C PASS |

## 5. Grupo T: camino stale real con disponibilidad variable (B2)

Prototipo A sobre las 25 en ventana, consultando cada 0,5 s de 0 a 400 s. **Cada consulta solo ve las filas visibles en su instante** (`visible_at ≤ display_at`), así que la disponibilidad varía entre consultas. Política: envolvente inmutable por run (ADR §4.4).

| Escenario (ocurrió · visible) | Base | Retroceso F1 máx | F2: \|salto − `rewind_m`\| | F2 con `rewind_m > 0` | Discrepancias tras reinicio |
|---|---|---|---|---|---|
| Sin cambio | 25 sin cancelación | 0,0 m | 0,0 | 7 | 0 |
| `CANCELED` posterior · +20 s · +20 s | 25 sin cancelación | 0,0 | 0,0 | 7 | 0 |
| `CANCELED` posterior · +20 s · **+181 s** (contraejemplo) | 25 sin cancelación | **0,0** | 0,0 | 7 | 0 |
| `CANCELED` +60 s y anulación +150 s | 25 sin cancelación | 0,0 | 0,0 | 7 | 0 |
| `CANCELED` base −300 s | 25 canceladas | 0,0 | 0,0 | 0 | 0 |
| `CANCELED` base de ayer (−86 400 s) | 25 caducadas por edad | 0,0 | 0,0 | 7 | 0 |
| `CANCELED` base ocurrido −700 s, recibido −5 s | 25 caducadas por edad | 0,0 | 0,0 | 7 | 0 |
| **Condición violada:** fila del run base visible a +100 s | 25 canceladas | **1 310,66 m** | 0,0 | 0 | 0 |

- **Contraejemplo del revisor en `19667`**, con la cancelación no visible a +179 s y visible a +181 s:

  | Política | +179 s | +181 s | Retroceso |
  |---|---|---|---|
  | Ronda 2 (recorte por `observed_at`) | 1 284,89 m | 213,74 m | **1 071,15 m** (reproduce el dictamen) |
  | Envolvente inmutable | 1 284,89 m | 1 284,89 m | **0,0 m** |

- **Condición violada.** El retroceso se produce si una fila de un run anterior o igual al del ancla se hace visible después del ancla (varios escritores o carga retroactiva). Queda **fuera de la garantía**: el ADR la condiciona a un único colector con un commit por ciclo.
- **Cambio de versión:** congela en el ancla con `frozen_basis = anchor_version_changed`.
- **Línea base de producción:** 25/25 retroceden (§0).

## 6. Ramas de presentación (motor real) y AC-15

- **P1:** con `latest` de `19664` desplazado 0,27°, el motor usa `previous`.
  - Con el estado de la observación efectiva (`IN_TRANSIT_TO`): R5, con avance.
  - Con el de `latest` (`STOPPED_AT`, el uso erróneo): R1, retención.
  - Los resultados son distintos.
- **P2:** sin ancla utilizable, `schedule_only` sigue R8 (`R8(ausente):R5`, `coherent = null`). Si está `CANCELED`, publica `unlocated` sin coordenada.
- **P3:** solo `raw`, sin envolvente. `CANCELED` solo rotula.
- **P4:** interpolación con `display_at` 30 s antes de `1533` → `interpolated_between_known_anchors`, |prototipo − producción| = 0 m, tramo entre anclas de 77 s.
- **AC-15 (`ts_equivalence.txt`):**
  - 64 envolventes y 377 muestras con instantes en ms → |Δ| máx **0 m**, 0 fases distintas.
  - 19 envolventes con un desfase de 0,7 ms en µs → |Δ| máx **0,0117 m** (`Date.parse` trunca).
  - De ahí la regla de serializar en ms (§4.3 c).

## Límites y no verificado

- **`UNVERIFIED`:**
  - la semántica en vivo de `IN_TRANSIT_TO`/`INCOMING_AT`;
  - el instante real de salida de los 3 trenes retenidos;
  - la latencia en vivo si hay retraso o pérdida del feed;
  - la causa de los dos cruces dentro de la zona;
  - que en producción se cumpla la condición de la garantía de §4.4 (un único colector, runs visibles en orden de `id`, sin cargas retroactivas en la base del directo); el arnés solo mide qué pasa si se viola;
  - el valor calibrado de `cancel_max_age_s` (600 s es provisional);
  - cuánto se acerca a la entrada real la entrada en zona por muestras con la cadencia en vivo.

  Requieren MP-028 y MP-025b.
- **AC-T6 / FR-07: NO EJECUTADO.** Requiere PostgreSQL con dos conexiones y es trabajo de MP-026b.
- **Prototipos:** la función `phase` y el comparador JS son prototipos de la especificación. Del TS de producción solo se ejecuta `progressAt`, sin cambios.
- **`CANCELED`:** sin casos de Madrid en el kit; solo se prueba con sintéticos.
- **DST:** solo con horarios sintéticos, porque el `calendar.txt` del kit no tiene viajes esas fechas.
- **Muestra:** un único par de cortes (15:32–15:33 locales). No representa el día.
- **Revisión:** ver el aviso del principio: sin tercera ronda automática.
