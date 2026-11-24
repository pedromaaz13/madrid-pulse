# Registro de despachos y revisiones — Auditoría adversarial Hito 3

Mantenido en vivo por el coordinador (Claude Sonnet) a medida que cada `AUD-ID` reporta. AUD-09 puede partir de este registro en vez de reconstruirlo desde cero.

**Run:** `run_3b3bfaf88f3d` · **Worktree:** `<WORKTREES>/audit-hito-03` (rama `audit/hito-03-adversarial`, base `mp-022-validacion-integrada@beb9434`)

| AUD-ID | Rol | Agente / modelo / esfuerzo (solicitado = efectivo) | Dispatch | Task | Commit | Veredicto |
|---|---|---|---|---|---|---|
| AUD-00 | Ejecutor | Claude Sonnet — hecho directamente por el coordinador (inventario mecánico, bajo riesgo) | — | `task_5e5d12f76982` | `0fbabe3` | — |
| AUD-00 | Revisor | Codex `gpt-5.6-terra` · medium | `ctx_34a13efbb75a` | `task_71d356947672` | — | **APPROVED** |
| AUD-02 | Ejecutor | Codex `gpt-5.6-sol` · high | `ctx_99b3f28c3b64` | `task_b03ab623492c` | `81b246c` | entregado |
| AUD-02 | Revisor | Claude `sonnet` · high | `ctx_10b070f167d5` | `task_d0968d994508` | — | **APPROVED (5/5)**, con reproducción propia de los 5 hallazgos citados |
| AUD-03 | Ejecutor | Codex `gpt-5.6-sol` · high | `ctx_8e6da472a2f5` | `task_cc9d4fbec491` | *(pausado — límite de uso de Codex, reset 16:49 CET)* | *(en curso)* |
| AUD-05 | Ejecutor | Claude `sonnet` · high | `ctx_f88f1e4cca5e` | `task_f3b4f5788326` | `861da95` | **completado** — hallazgo P0-1 confirmado |
| AUD-05 | Revisor | Codex `gpt-5.6-terra` · high | `ctx_41022ed63263` | `task_cb75c33efaca` | — | **CONFIRMADO** (reproducción independiente vía API pura, sin navegador) |
| AUD-01 | Ejecutor | Claude `opus` · high | `ctx_e69bfe336e92` | `task_8bf54c0799dd` | `9553be0` | **completado** — 2 P0 reales, mecanismo confirmado por el coordinador |
| AUD-01 | Revisor (1ª ronda) | Codex `gpt-5.6-sol` · high | `ctx_f31a48ded8a6` | `task_befe7c4069bd` | — | **CHANGES_REQUESTED** — ambos P0 confirmados, cifras a corregir |
| AUD-01 | Corrección | Claude `opus` · high (misma sesión, follow-up) | `ctx_82628c4e473d` | `task_e5569e13a76b` | *(pausado — límite de sesión Claude, reset 21:10 CET)* | *(en curso)* |
| AUD-03 | Ejecutor | Codex `gpt-5.6-sol` · high | `ctx_8e6da472a2f5` | `task_cc9d4fbec491` | `1c28163` | **completado** |
| AUD-03 | Revisor | Claude `opus` · high | `ctx_4db56fd6dd34` | `task_5f1319cdd3c0` | `2789ad2` | **CHANGES_REQUESTED** — 3/4 confirmados, 1 mal diagnosticado |
| AUD-03 | Corrección | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_352eb5227c6d` | `task_a86ea689f4b5` | *(en curso)* | *(en curso)* |
| AUD-01 | Corrección (rev.2) | Claude `opus` · high (follow-up) | `ctx_82628c4e473d` | `task_e5569e13a76b` | `f88d12f` | **aplicada**, enviada a reevaluación |
| AUD-01 | Revisor (2ª ronda) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_264f3fb407d7` | `task_4ac30104d092` | — | **CHANGES_REQUESTED** (4/6 puntos ya APROBADOS, quedan 2: dirección temporal `calculated_at` y criterios de refutación cuantificados en H1-H8) |
| AUD-01 | Corrección (ronda 3) | Claude `opus` · high (follow-up) | `ctx_349842fc8de0` | `task_5d4d3be6d4fe` | `574a620` | **aplicada**, enviada a veredicto final |
| AUD-01 | Revisor (3ª ronda, final) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_526284cf5474` | `task_4cba05ac92dd` | — | **APPROVED (definitivo)** — AUD-01 cerrado tras 3 rondas |
| AUD-03 | Corrección (ronda 2) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_352eb5227c6d` | `task_a86ea689f4b5` | `08ce3b8` | **aplicada**, enviada a veredicto final |
| AUD-03 | Revisor (2ª ronda, final) | Claude `opus` · high (follow-up) | `ctx_045f259f59a2` | `task_789f8d5e7a80` | `68e1e16` | **APPROVED (definitivo)** — AUD-03 cerrado tras 2 rondas, 2 mejoras no pedidas |
| AUD-06 | Revisor | Claude `sonnet` · high | `ctx_6afc827ab5e6` | `task_cb72e0e1c0c5` | `1a1dcbb`* | **APPROVED** — AUD-06 cerrado (*commiteado por el coordinador, el worker no lo hizo) |

## Incidente de alcance real — AUD-06 escribió en la base de desarrollo compartida

**2026-11-23, ~18:05 UTC.** El worker de AUD-06 (`ctx_cf7d40a866d7`) omitió el flag de entorno aislado en un comando de diagnóstico y el colector real ejecutó dos ciclos completos contra `127.0.0.1:5433` (`madrid-pulse-postgres-1`, la base de desarrollo compartida de TODO el proyecto) en vez de su propio contenedor desechable. Se detuvo él mismo al detectarlo (18:05:40Z) y lo reportó con transparencia.

**Verificado por el coordinador, comparando contra la línea base reconfirmada al cierre de cada tarea del proyecto (`668/484/3/120/0`):**

| Tabla | Antes | Ahora | Δ |
|---|---|---|---|
| `vehicle_position_observation` | 668 | 895 | +227 |
| `trip_update_observation` | 484 | 646 | +162 |
| `service_alert` | 3 | 8 | +5 |
| `source_ingestion_run` | 120 | 126 | +6 (runs 3090-3095) |
| `data_quality_event` | 0 | 8 | +8 |

El colector es solo-inserción por diseño (sin ruta de `UPDATE`/`DELETE`), así que esto es aditivo — nada previo debería haberse alterado o perdido, aunque no se ha hecho un diff fila a fila para confirmarlo al 100%. **No se ha tocado la base de desarrollo desde entonces. La decisión de conservar o limpiar estos registros queda exclusivamente para el propietario** — pendiente de respuesta.
| AUD-06 | Ejecutor | Codex `gpt-5.6-terra` · high | `ctx_cf7d40a866d7` | `task_7982bf79c176` | `75f97af` | **completado** — 103 tests reproducidos, 1 P1 real |
| AUD-06 | Revisor | Claude `sonnet` · high | `ctx_6afc827ab5e6` | `task_cb72e0e1c0c5` | — | *(en curso, advertido explícitamente sobre el incidente de 5433)* |
| AUD-07 | Ejecutor | Claude `sonnet` · medium | `ctx_7f0fde0b7e4f` | `task_a9deb9865cbc` | `44c98cb`, `ea49e6a` | **completado** — revisión independiente real de Codex (`ctx_db3c9aa62ac8`, settled/succeeded) incorporada: 2 P1→P2, 2 P1 confirmados, 1 hallazgo descartado |
| AUD-01 | — | Claude `opus` · high (pendiente de despachar) | — | `task_8bf54c0799dd` | — | en cola |
| AUD-04 | Ejecutor | Claude `opus` · high | `ctx_079d97438512` | `task_e6d1bf8a933e` | `c8263a0` | **completado** — 1 P0 nuevo independiente de AUD-01 |
| AUD-04 | Revisor | Codex `gpt-5.6-sol` · high | `ctx_4cc1f0959029` | `task_e3355549167a` | — | **CHANGES_REQUESTED** — mecanismo P0 confirmado, 2 imprecisiones a corregir |
| AUD-04 | Corrección | Claude `opus` · high (follow-up) | `ctx_df3d184f2548` | `task_28d2a39bb8db` | `6aff045` | **aplicada**, enviada a veredicto final + pregunta de severidad |
| AUD-04 | Revisor (ronda final) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_f6e4d425460c` | `task_e8ebd65626c3` | — | **CHANGES_REQUESTED** — mecanismo/cohorte/evidencia ya confirmados, 1 sobreafirmación a matizar |
| AUD-04 | Corrección (ronda 3) | Claude `opus` · high (follow-up) | `ctx_b3f6965ae197` | `task_675457d6a82d` | `90b0a3e` | **aplicada** — ventana de alcanzabilidad medida con precisión ([-0,999,0,000]m), enviada a veredicto final |
| AUD-04 | Revisor (ronda final, 2ª vez) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_e9d9a104948e` | `task_e36a368f56a5` | — | **CHANGES_REQUESTED** — ventana confirmada, 1 frase residual contradictoria a corregir |
| AUD-04 | Corrección (ronda 4) | Claude `opus` · high (follow-up) | `ctx_43c147440bf7` | `task_76fda7df01a6` | `312f05f` | **aplicada** — ancla del test medida con precisión (offset -0,000011m), enviada a veredicto final |
| AUD-04 | Revisor (ronda final, 3ª vez) | Codex `gpt-5.6-sol` · high (follow-up) | `ctx_e5a4ad50b816` | `task_4c932e94ae41` | — | **APPROVED (definitivo)** — AUD-04 cerrado tras 4 rondas |
| AUD-06 | — | Codex `gpt-5.6-terra` · high (pendiente de despachar) | — | `task_7982bf79c176` | — | en cola |
| AUD-08 | Ejecutor | Codex `gpt-5.6-terra` · high | `ctx_1d55182413e3` | `task_e0212d2fd3fe` | `a794c0e` | **completado** — 283 tests/5 skips, 89/89 frontend, 1 P2 (carrera colector-archivador) |
| AUD-08 | Revisor | Claude `sonnet` · high | `ctx_bfb72a618d4b` | `task_6d6e71ee602d` | — | **CHANGES_REQUESTED** (solo documental: skips 5/1/18, discrepancias 68/72-75/180-190s, línea base 5433, 17 tablas=15+2 vistas) *(histórico del encargo: se le pide aclarar 5 skips vs 1 skip de otros ejecutores y revisar cifras contradictorias)* |
| AUD-09 | — | Claude `opus` · high (pendiente, depende de AUD-07 revisión equivalente EGM (ya cerrada) + AUD-08) | — | `task_2e01f9d87b46` | — | pendiente de AUD-08 |

## Hallazgos reales reportados hasta ahora (resumen, no sustituye los documentos completos)

- **AUD-02** (reconstrucción GTFS, confirmado 5/5 por revisión independiente):
  - 12/42/103/95 coinciden con lo que afirmaba el cierre del Hito 3.
  - **121 trips huérfanos** (7 en `10T0035C5`, 114 en `10T0097C8b`).
  - Solo **40 de 103 `route_id`** tienen al menos un patrón asociado.
  - Solo **102 de 103 patrones** tienen ≥2 paradas; el patrón `10T0098C8b` tiene una sola parada (`12006`, Cercedilla).
  - **`calendar_dates.txt` ausente del ZIP real** — confirmado con `unzip -Z1` sobre el zip oficial (SHA-256 coincide), y `packages.gtfs.load_feed` sobre el feed real da `topology.calendar_dates == ()`. El manejo ADD/REMOVE que MP-017 dio por probado solo se verificó con fixtures sintéticas, nunca contra el ZIP real — **posible brecha real entre lo que el cierre de MP-017 afirmó y lo que el dato real permite verificar**.
  - **Bug real (sin impacto actual) en `ServiceDateResolver`**: `apps/api/service.py::service_dates_covering` resta un día fijo (`_service_date(start) - timedelta(days=1)`) sin escalar con `extended_horizon_s`; con un horizonte GTFS de 49:00+ (>48h) resolvería mal la fecha de servicio. El ZIP real de Madrid tiene un horizonte de solo 3180s, por lo que **hoy no se manifiesta**, pero el código no lo impide si el horizonte creciera.

- **AUD-05** (frontend/UX en navegador real, confirmado independientemente vía API):
  - **P0-1, confirmado tres veces (el coordinador leyendo código, el ejecutor en navegador, el revisor por API pura):** `/api/v1/snapshot?at=` reclasifica un feed con datos reales (`entities=468`, `source_timestamp` presente) como `status="unknown"` con `data_age_s`/`poll_age_s` **negativos**, cuando el reloj de replay precede a un `started_at` de ingesta ya persistida. Causa raíz: `apps/api/db.py:178-223` (`recent_ingestion_runs` no acota por `now`) + `apps/api/service.py:381` (cualquier edad negativa colapsa a `"unknown"`, el mismo estado que "nunca hubo ingesta"). Contradice el principio central del hito ("nunca vacía el recurso ni fabrica datos") en sentido inverso: aquí el sistema sí tiene el dato y lo oculta.
  - Impacto acotado a `/api/v1/snapshot` (Live) — el tablero de estación (`/stations/{id}/board`) no expone `degraded`/edades, así que no reproduce el mismo síntoma.
  - 3 hallazgos P2 cosméticos, sin impacto de producto.

- **AUD-01** (tesis de producto/arquitectura) — **la tarea más grave hasta ahora, 2 P0 reales**:
  - **P0-001, mecanismo confirmado por el coordinador leyendo código (cifras exactas pendientes de la revisión):** el motor de movimiento muestra trenes avanzando **antes de su salida real**. `packages/movement/schedule.py::dwell_end_seconds` solo detecta una espera programada cuando hay dos puntos de horario consecutivos con el mismo `progress_m` (llegada+salida en una parada intermedia) — el origen de un viaje nunca tiene un punto de "llegada" previo a su único punto de "salida", así que `dwell_end_seconds(0)` devuelve `None` **por construcción**, nunca por falta de dato real. Un vehículo observado en el origen antes de la hora de salida programada produce `temporal_offset_s` negativo en `_envelope` (interpretado como "el tren va adelantado de horario" en vez de "el tren todavía no ha salido"), `dwell_until` queda `None`, y el motor extrapola progreso sobre una circulación que físicamente sigue parada. El ejecutor midió, sobre el corte real `1533`: 17 de 121 circulaciones afectadas, hasta 38,6 min antes de la salida real, velocidades extrapoladas de 56-108 km/h, hasta 5701 m de avance falso; y un salto real al llegar el siguiente ancla con p50 1237 m / máximo 3274 m sobre 44 circulaciones, 26 de las cuales no se movieron en absoluto. **Esto contradice directamente la garantía de "sin teletransporte" verificada en MP-020/021/022** — pero sobre circulaciones YA en marcha, no sobre el caso pre-salida que esta auditoría descubre; no hay contradicción entre ambos hallazgos, son escenarios distintos que nadie había probado antes.
  - **P0-002:** 28/103 de geometría validada **estaba pre-autorizado por el propio criterio de cierre** (`docs/TASKS.md:443`, "mayoría pending honesto") en vez de ser un límite real descubierto durante el trabajo; 68 de los 72 patrones pendientes tienen como único motivo registrado "sin geometría descargada" — **nunca se intentó**, no es un límite de la fuente OSM.
  - **P1-003:** `route_coverage_pct` de la matriz vinculante (MP-022) es tautológico (121/121 = 100% por construcción) — exactamente la confusión que el propio kit advertía (`referencia/01-auditoria-live.md:22`). Cobertura real medida por el ejecutor: **65/73 = 89,0%**, con variación real por línea (C1 al 50%, C10 al 60%) — la instrumentación del feed **no es homogénea por línea**, justo lo que `HITO_3_BACKLOG.md:36` pedía confirmar y no se había confirmado.
  - **P1-005:** el horizonte de 180s (DEC-010, "calibrable") fue reutilizado por ADR-0014 sin recalibrar; el intervalo mediano real entre paradas de Madrid es exactamente 180s y el horario declara espera en solo el 9,9% de las paradas — la mitigación escrita en `rendering.py:84-85` es falsa en la práctica: los trenes se dibujan atravesando estaciones.
  - **P1-009:** ninguna puerta de aceptación del hito es falsable — documentar un hueco basta para dejar de bloquear el cierre (`AMPLIACION:40`, `MATRIZ-CIERRE:15`). Explica, sin suponer mala fe, cómo una cadena con 28/103 de geometría real pudo cerrar afirmando "las nueve puertas tienen evidencia".
  - Hipótesis H1-H4 con evidencia a favor medida sobre cortes congelados, necesitan confirmación con feed en vivo ≥2h y más días. H7 (escalado: 255ms p50 de snapshot/10s por espectador, sin pool ni CDN pese a ser principio declarado en `ARCHITECTURE.md:68-69`) derivada aritméticamente, no medida con red real. H5/H6/H8 (usuarios reales) quedan abiertas: los tres hitos no contienen ni una sola observación de una persona usando el producto.
  - **Revisión independiente (Codex Sol·High) reprodujo ambos P0 ejecutando los propios scripts del ejecutor, sin red ni PostgreSQL — CONFIRMA ambos P0 como hallazgo de producto, pero devuelve CHANGES_REQUESTED sobre la redacción:** el salto al llegar el ancla siguiente es real (p50 1237,09m/máx 3274,23m confirmados exactos), pero **solo 13/44 circulaciones se movieron, no 26** como afirmaba el documento (31/44 no cambiaron ni coordenada ni progreso); el horizonte usado es realmente **190s**, no los "180s" que rotulaba el script/documento. Para P0-002, matiza que de los 72 patrones pendientes, **68 no tienen fuente ni intento documentado**, pero **4 (C4b) sí tuvieron un intento real que falló con dos errores 502 de la relación OSM `9174512`** — un límite externo real, categóricamente distinto de "nunca se intentó". También exige precisión en el relato de "pre-autorización": `TASKS:443`/`STATUS:832` autorizaron "mayoría pending" y "mínimo C5+C4", nunca el número exacto 28/103. Corrección puntual en curso con el mismo ejecutor.

- **AUD-03** (75 patrones sin corredor validado) — revisión independiente (recomputada desde cero, catálogo+ZIP crudo) confirmó 3/4 y corrigió 1:
  - **Confirmado con evidencia más fuerte:** los 4 patrones C4b no solo los validaría la relación `9174512` (de un solo punto, marcada ahora `NO VERIFICADO` sin descarga) — **ya hay una alternativa de coste cero**: las 15 paradas de esos 4 patrones encajan a 48,3m sobre la relación `9174511` **ya congelada en el repo** (con monotonía inversa; 3/4 son inversos exactos de patrones ya validados). El bloqueo real es que `build_corridor_catalog` exige arcos crecientes — no hace falta descargar nada.
  - **Corregido: el "patrón degenerado de 1 parada" en realidad es un truncamiento del feed de origen** (`stop_sequence` 032/025 no empieza en 1; su ruta espejo `10T0097C8b` tiene 114 viajes con CERO `stop_times`) — marcarlo `non_traversable` habría consagrado un defecto del proveedor como estado de producto.
  - **Recuento corregido:** son **72** patrones sin ninguna prueba geométrica (ningún `GeometrySourceSpec` con ese `route_id`), no 67. Encaja exacto con AUD-01: 68 = 67 (sin fuente ni intento) + 1 (el patrón truncado de arriba, irreparable por descarga).
  - **Dato operativo importante para AUD-09:** el CSV canónico de cobertura asigna el **mismo** `reason` a los 72 pending — la distinción entre "límite externo real" y "sin intentar" **no es recuperable desde el artefacto canónico**, solo desde la prosa de `STATUS.md`.
  - 19/19 tests focales en ambas rondas.

- **AUD-06** (backend/operación): 103 tests reales reproducidos contra PostGIS aislado. **P1 principal:** `build_snapshot` puede publicar una `revision` nueva sin incluir el vehículo que la motivó — falta una vista transaccional consistente. **P2:** pérdida de `affected_stop_ids` en algún camino, FKs `trip_id` no pobladas, y confirma lo que AUD-04/AUD-08 deben vigilar: los 823s de operación medidos en MP-021 **no prueban 24/7**.

- **AUD-01 — CERRADO (APPROVED definitivo tras 3 rondas).** Resumen final: 2 P0 reales confirmados independientemente con cifras exactas (ver tabla de dispatch arriba), 8 hipótesis refutables con umbral numérico explícito, 4 hipótesis descartadas acotadas con razón sustantiva. El revisor de la ronda final dejó constancia de que el commit `574a620` también sincronizó la cifra 68→67+1 de P0-002 con la corrección de AUD-03 (fuera de su encargo explícito, no reevaluado por él) — es consistente con lo que AUD-03 estableció de forma independiente, no una afirmación nueva sin verificar.

- **AUD-03 — CERRADO (APPROVED definitivo tras 2 rondas).** El recuento final es 72 patrones sin prueba geométrica, 67 accionables por descarga, 1 irreparable (feed truncado), 4 con alternativa de coste cero ya en el repo. Nota advisory para quien corrija esto en producto (no bloquea el cierre de la auditoría): la celda "0: dato ausente" del CSV debería ser un guion, no un `0`, por el propio principio "dato ausente ≠ cero" de `AGENTS.md` — un pequeño recordatorio de que hasta los documentos de auditoría deben honrar las convenciones del proyecto que auditan.
- **AUD-06 — CERRADO (APPROVED).**

- **AUD-04** (raw/matched/rendered, movimiento) — **1 P0 nuevo, independiente del de AUD-01, confirmado en mecanismo por el coordinador leyendo código:**
  - **P0:** `packages/movement/schedule.py:120` usa `tolerance_m: float = 1.0` **hardcodeado** para decidir si una posición observada está "en" una parada con espera programada — un orden de magnitud más estricto que el error real de map-matching medido (p95≈20,8m). El ejecutor midió un caso real: el tren `1023V19656C5`, con 60s de espera programada en Fuenlabrada, se dibuja saliendo a **75,2 km/h** (1252,7m en 60s) porque su desvío real de 5,38m excede la tolerancia de 1,0m. **Esta cohorte (post-llegada, offset plausible +321s) está explícitamente separada de AUD01-P0-001 (pre-salida)** — el motor de movimiento tiene **al menos dos mecanismos de fallo independientes** alrededor de las paradas, no uno solo.
  - **P1 #1:** al cruzar `stale_after_s`, el símbolo retrocede una mediana de **2357,9m** (25/25 circulaciones en ruta, máximo 3959,2m) — y el aviso que explicaría la congelación **desaparece justo en ese instante**, porque depende de `valid_until`, que `stale_frozen` pone a `null`.
  - **P1 #2:** el mapa no distingue visualmente observación real de proyección sobre vía — una sola entrada de `METHOD_STYLES` para "anchor", con un texto de detalle que afirma (falsamente) que la proyección es la coordenada de la fuente.
  - **8 P2**, incluido un **segundo bug de DST** en `_envelope` (distinto del ya corregido en MP-019/DEC-039) y un umbral de velocidad implausible fijado en 900 km/h que deja pasar un evento real de 200 km/h sin que llegue al directo.
  - **4 NO-VERIFICADO declarados explícitamente** (sin `pytest` instalado y sin autorización para instalarlo; sin ventana de feed en vivo; sin navegador; sin contenedor PostgreSQL) — la suite del cliente (10/10) y su propio arnés vitest (3/3) sí se ejecutaron.

- **Nota de severidad abierta (AUD-04 P0), para que AUD-09/el propietario la resuelva, no decidida por ningún agente:** al corregir la cohorte, el ejecutor encontró que la velocidad calculada por la envolvente en este caso (75,2 km/h) **coincide casi exactamente con la velocidad real observada** entre los dos cortes (75,0 km/h) — a diferencia de AUD01-P0-001, aquí no hay una observación que contradiga directamente la cifra calculada. El defecto real es estructural: la rama de espera programada es inalcanzable (0 de 44 casos) pese a que `rendering.py:185-187` afirma lo contrario, y el contrafactual correcto sería 0m a los 30s (espera honrada) frente a los 626,4m que publica hoy. Queda abierto si esto cumple el listón de P0 ("afecta a la veracidad de los datos, la integridad ferroviaria...") o si, sin una observación directamente contradictoria, es más propiamente un P1.

*(Esta tabla se actualizará según reporte la revisión final de AUD-04 (dispatch `ctx_f6e4d425460c`) y después AUD-08/AUD-09.)*

| AUD-08 | Corrección | Codex `gpt-5.6-terra` · high (follow-up) | `ctx_eb57aa06e6d3` | `task_0312f23463c1` | *(en curso)* | *(en curso)* |
| AUD-06 | Corrección documental (afirmación falsa sobre 5433) | Codex `gpt-5.6-terra` · high (follow-up) | `ctx_5c1add5b519c` | `task_a05e3c7878cb` | *(en curso)* | *(en curso)* |
| AUD-08 | Revisor (ronda final) | Claude `sonnet` · high (follow-up) | `ctx_82199cab02ca` | `task_6f3985126a2a` | `aed1fc0` | **APPROVED** — AUD-08 cerrado; 2 observaciones no bloqueantes pasadas a AUD-09 |

## Corrección de registro (a petición de AUD-09, 2026-11-24)
- **AUD-05:** el único veredicto previo de Codex Terra (`ctx_41022ed63263`) fue "CHANGES_REQUESTED por P0-1": reprodujo el hallazgo P0-1, pero no evaluó formalmente el documento ni hubo re-revisión. **No estaba APPROVED.** Re-revisión formal despachada: Codex `gpt-5.6-terra` · high, `ctx_53f6eb860b17`, `task_55fbb3c5ce04` *(en curso)*.
- **AUD-07:** el revisor `ctx_db3c9aa62ac8` lo creó el propio ejecutor (profundidad 2), con modelo/esfuerzo no verificables, veredicto "verificado con matices" y correcciones `ea49e6a` sin re-verificar. **No conforme a la matriz.** Revisión formal despachada: Codex `gpt-5.6-terra` · medium, `ctx_1626c278cd8f`, `task_40fad4c8898e` *(en curso)*.
- Observación de Orca: el default actual de `~/.codex/config.toml` es `gpt-6.2-sol`, familia excluida por el encargo; todos los despachos de esta auditoría fijan `--model` explícitamente y el recibo confirma el modelo efectivo.

## Decisión del propietario sobre 5433 (2026-11-24)
CONSERVAR los datos. Sin DELETE/TRUNCATE/restauración. Dump fuera del repo. 5433 no sirve para pruebas reproducibles que dependan de su estado original. Tarea H4 de defaults peligrosos autorizada solo a planificación. Ver `INCIDENT_5433.md` §7.
- **AUD-07:** revisión formal conforme a matriz (Codex `gpt-5.6-terra` · medium, `ctx_1626c278cd8f` + follow-up `ctx_c95f2e3ad3ce`): CHANGES_REQUESTED (2 correcciones de redacción) -> correcciones `48dd53f` -> **APPROVED**.

---

## Consolidación verificada por AUD-09 (2026-11-23/24)

**Elabora:** AUD-09, Claude `opus` · high (`ctx_d10350eb24d0`). Las secciones anteriores de este registro son el histórico vivo del coordinador y **no se reescriben**; esta sección las reconcilia contra los recibos de Orca. Cuando hay diferencia, manda esta sección.

**Método (reproducible):**

```sh
orca orchestration worker-list --run run_3b3bfaf88f3d --limit 100 --json          # 33 dispatches + 3 posteriores
orca orchestration worker-show --dispatch <ctx_id> --json --full                   # startOptions.launch.{requested,effective}, dispatchedAt/completedAt, followUpOf, creatorDispatchId, depth
orca orchestration inbox --run run_3b3bfaf88f3d --limit 500 --full --json          # veredictos textuales (worker_done)
git log --format='%h %ad %s' --date=iso-strict beb9434..HEAD                        # commits de cada ronda
```

**Qué es «efectivo» aquí:** el campo `launch.effective` que Orca registra al crear el worker. Los *follow-up* (`followUpOf ≠ null`) reutilizan la misma sesión y Orca no registra un lanzamiento nuevo (`model = null`); su modelo efectivo es el de la sesión original de la cadena. **Orca no expone duración de razonamiento ni consumo de tokens: no se reporta ninguna cifra de consumo** (no se inventa). Las horas son UTC (`dispatchedAt` → `completedAt`).

### Tabla por AUD-ID

| AUD | Rol | Dispatch (task) | Modelo · esfuerzo solicitado = efectivo (recibo) | Matriz del encargo | Ventana UTC | Commit | Veredicto (mensaje) |
|---|---|---|---|---|---|---|---|
| 00 | Ejecutor | — (coordinador) | **no verificable por recibo** (el coordinador no es un worker; consta como Claude Sonnet) | Sonnet · medium | — | `0fbabe3` | — |
| 00 | Revisor | `ctx_34a13efbb75a` (`task_71d356947672`) | `gpt-5.6-terra` · medium | Terra · medium ✔ | 13:04:28→13:05:59 | — | **APPROVED** (`msg_0fad39dfd97e`) |
| 01 | Ejecutor | `ctx_e69bfe336e92` (`task_8bf54c0799dd`) | `opus` · high | Opus · high ✔ | 15:28:24→15:59:24 | `9553be0` | entregado |
| 01 | Revisor r1 | `ctx_f31a48ded8a6` | `gpt-5.6-sol` · high | Sol · high ✔ | 16:01:02→16:06:50 | — | CHANGES_REQUESTED (`msg_d25fe39c0caf`; ambos P0 confirmados) |
| 01 | Corrección r1 | `ctx_82628c4e473d` (fu `ctx_e69bfe336e92`) | heredado `opus` · high | — | 16:07:21→17:04:06 (pausa por límite de sesión Claude) | `f88d12f` | aplicada |
| 01 | Revisor r2 | `ctx_264f3fb407d7` (fu `ctx_f31a48ded8a6`) | heredado `gpt-5.6-sol` · high | — | 17:04:37→17:06:38 | — | CHANGES_REQUESTED (`msg_65b44df80992`) |
| 01 | Corrección r2 | `ctx_349842fc8de0` | heredado `opus` · high | — | 17:07:00→17:11:34 | `574a620` | aplicada |
| 01 | Revisor r3 | `ctx_526284cf5474` | heredado `gpt-5.6-sol` · high | — | 17:11:47→17:13:29 | — | **APPROVED** (`msg_9e1879a32878`; deja constancia de *hunks* de P0-002 no reevaluados) |
| 02 | Ejecutor | `ctx_99b3f28c3b64` (`task_b03ab623492c`) | `gpt-5.6-sol` · high | Sol · high ✔ | 13:04:37→13:27:51 | `81b246c` | entregado |
| 02 | Revisor | `ctx_10b070f167d5` | `sonnet` · high | Sonnet · high ✔ | 15:13:02→15:15:57 | — | **APPROVED 5/5** (`msg_6a9c33a1e7ec`) |
| 03 | Ejecutor | `ctx_8e6da472a2f5` (`task_cc9d4fbec491`) | `gpt-5.6-sol` · high | Sol · high ✔ | 15:12:57→16:02:24 (pausa por límite de uso Codex) | `1c28163` | entregado |
| 03 | Revisor r1 | `ctx_4db56fd6dd34` | `opus` · high | Opus · high ✔ | 16:02:47→17:03:50 (pausa por límite de sesión Claude) | `2789ad2` | CHANGES_REQUESTED (`msg_fb6aa3ea1a2a`; 3/4 confirmados) |
| 03 | Corrección | `ctx_352eb5227c6d` | heredado `gpt-5.6-sol` · high | — | 17:04:13→17:13:25 | `08ce3b8` | aplicada |
| 03 | Revisor r2 | `ctx_045f259f59a2` | heredado `opus` · high | — | 17:13:47→17:17:44 | `68e1e16` | **APPROVED** (`msg_925370d8e9a5`) |
| 04 | Ejecutor | `ctx_079d97438512` (`task_e6d1bf8a933e`) | `opus` · high | **Sonnet · high ✘ (desviación al alza, registrada)** | 17:18:38→17:52:38 | `c8263a0` | entregado |
| 04 | Revisor r1 | `ctx_4cc1f0959029` | `gpt-5.6-sol` · high | Sol · high ✔ | 17:53:31→17:56:58 | — | CHANGES_REQUESTED (`msg_854bd6103c7c`) |
| 04 | Corr. r1 / Rev. r2 | `ctx_df3d184f2548` / `ctx_f6e4d425460c` | heredados | — | 17:57:15→18:05:50 | `6aff045` | CHANGES_REQUESTED (`msg_8e45cec8ed75`) |
| 04 | Corr. r2 / Rev. r3 | `ctx_b3f6965ae197` / `ctx_e9d9a104948e` | heredados | — | 18:06:04→21:57:05 (pausa por límite de sesión Claude) | `90b0a3e` | CHANGES_REQUESTED (`msg_2fb8db32b926`) |
| 04 | Corr. r3 / Rev. r4 | `ctx_43c147440bf7` / `ctx_e5a4ad50b816` | heredados | — | 21:57:15→22:01:19 | `312f05f` | **APPROVED** (`msg_6cb1fbf48ac8`); severidad P0/P1 abierta → resuelta en `FINDINGS_REGISTER.md` §2 |
| 05 | Ejecutor | `ctx_f88f1e4cca5e` (`task_f3b4f5788326`) | `sonnet` · high | Sonnet · high ✔ | 13:04:40→15:27:00 (pausa por límite de sesión Claude) | `861da95` | entregado |
| 05 | Revisor r1 | `ctx_41022ed63263` | `gpt-5.6-terra` · high | Terra · high ✔ | 15:28:10→15:57:54 (pausa por límite Codex) | — | «CHANGES_REQUESTED por P0-1» (`msg_dd824ccd8ec2`); **no era APPROVED** |
| 05 | Revisor formal | `ctx_53f6eb860b17` (`task_55fbb3c5ce04`) | `gpt-5.6-terra` · high | Terra · high ✔ | 22:25:41→22:29:28 | — | CHANGES_REQUESTED **documental**, P0-1 confirmado (`msg_4a816dbcd13f`) |
| 05 | Corrección v2 | `ctx_3bc368ddffbd` (fu `ctx_f88f1e4cca5e`) | heredado `sonnet` · high | — | 22:29:36→22:40:35 | `39b3e06`, `28f696e` | aplicada (`msg_b0252f0c42d2`); entorno propio 5456, nunca 5433 |
| 05 | Re-verificación formal de la v2 | `ctx_7a5b7c7a3912` (fu `ctx_53f6eb860b17`) | heredado `gpt-5.6-terra` · high | Terra · high ✔ | 22:40:49→22:42:37 | `69a0708` (registro) | **APPROVED documental** (`msg_5100134ffbf0`); limitación: sin navegador, DevTools y zooms de 18/19 no repetidos |
| 06 | Ejecutor | `ctx_cf7d40a866d7` (`task_7982bf79c176`) | `gpt-5.6-terra` · high | Terra · high ✔ | 16:58:49→17:10:32 | `75f97af` | entregado; **incidente 5433** (`msg_08baf811cc62`, 17:05:56) |
| 06 | Revisor | `ctx_6afc827ab5e6` | `sonnet` · high | Sonnet · high ✔ | 17:10:55→17:17:34 | `1a1dcbb` (commit del coordinador) | **APPROVED** (`msg_59ca65b8b6b7`) |
| 06 | Corrección de divulgación | `ctx_5c1add5b519c` (fu `ctx_cf7d40a866d7`) | heredado `gpt-5.6-terra` · high | — | 22:20:06→22:21:02 | `2d02227` | aplicada; contrastada por el revisor final de AUD-08 (`msg_c82b2aa19e5a`) |
| 07 | Ejecutor | `ctx_7f0fde0b7e4f` (`task_a9deb9865cbc`) | `sonnet` · medium | Sonnet · medium ✔ | 13:04:47→15:18:04 (pausa por límite de sesión Claude) | `44c98cb`, `ea49e6a` | entregado |
| 07 | «Verificación» no conforme | `ctx_db3c9aa62ac8` (`task_31c89ba48f1f`) | **`null` / `null`** (sin modelo ni esfuerzo); `creatorDispatchId = ctx_7f0fde0b7e4f`, `depth = 2` | Terra · medium ✘ | 15:13:41→15:15:46 | — | «verificado con matices» (`msg_54257fc49b9f`): **no cuenta como revisión** |
| 07 | Revisor formal | `ctx_1626c278cd8f` (`task_40fad4c8898e`) | `gpt-5.6-terra` · medium | Terra · medium ✔ | 22:25:45→22:27:59 | — | CHANGES_REQUESTED (`msg_c0c0a380e4d1`) |
| 07 | Corrección | `ctx_03ed3179cb8c` (fu `ctx_7f0fde0b7e4f`) | `sonnet` · medium | — | →22:28:29 | `48dd53f` | aplicada (`msg_94588f8b26f9`) |
| 07 | Revisor formal r2 | `ctx_c95f2e3ad3ce` (fu `ctx_1626c278cd8f`) | heredado `gpt-5.6-terra` · medium | — | 22:28:38→22:28:59 | `26251cd` (registro) | **APPROVED** (`msg_cc461fada634`) |
| 08 | Ejecutor | `ctx_1d55182413e3` (`task_e0212d2fd3fe`) | `gpt-5.6-terra` · high | Terra · high ✔ | 22:01:40→22:12:14 | `a794c0e` | entregado |
| 08 | Revisor r1 | `ctx_bfb72a618d4b` | `sonnet` · high | Sonnet · high ✔ | 22:12:28→22:19:49 | `f290b76` (registro) | CHANGES_REQUESTED documental (`msg_50065e316974`) |
| 08 | Corrección | `ctx_eb57aa06e6d3` | heredado `gpt-5.6-terra` · high | — | 22:20:02→22:22:18 | `aed1fc0` | aplicada |
| 08 | Revisor r2 | `ctx_82199cab02ca` | heredado `sonnet` · high | — | 22:22:29→22:22:51 | — | **APPROVED** (`msg_c82b2aa19e5a`; 2 observaciones no bloqueantes absorbidas en `FINDINGS_REGISTER.md` §9) |
| 09 | Ejecutor | `ctx_d10350eb24d0` (`task_2e01f9d87b46`) | `opus` · high | Opus · high ✔ | 22:22:59→(en curso) | este commit | — |
| 09 | Revisor | *pendiente de despacho* | Codex `gpt-5.6-sol` · high (solicitado) | Sol · high | — | — | — |
| 09 | Revisor r1 (añadido en ronda 2, 2026-11-24) | `ctx_e51f26382ff4` (`task_a89f38cd833f`) | `gpt-5.6-sol` · high (recibo: solicitado = efectivo) | Sol · high ✔ | 22:43:50→22:49:01 | — | CHANGES_REQUESTED (`msg_ad9b81385016`): severidad P1 de `AUD04-P0-001` defendible y P1 de `AUD01-P0-002` coherente; FR-01 28/44 confirmado; NO-GO/CONDITIONAL GO respaldado; pide corregir cifras de horizonte (190 s → 180 s de producción), 30/44 → 29/44, 5/44 → 0/44, cota 221 m, separar servicio/repositorio, FR-29/FR-32, H4-11 y referencia de H4-09 |
| 09 | Corrección r1 | `ctx_607dbde2745f` (`task_537da6a757a0`, fu `ctx_d10350eb24d0`) | heredado `opus` · high | — | 22:49:10→ (pausa por límite de sesión Claude a las 22:49:18Z) | este commit | aplicada; reenvío al mismo revisor pendiente |

### HEAD auditado, comandos y resultados principales

| AUD | Código auditado | Comandos decisivos | Resultado reproducido |
|---|---|---|---|
| 00 | `beb9434`; cadena `990c95d→92c1b09→c28d5e4→728c667→7b87e6b→b616ae6→1ecbc8f→beb9434` | `git merge-base --is-ancestor`, `git ls-remote --heads origin`, `~/.codex/models_cache.json` | 7/7 ascendencias OK; ninguna rama en `origin`; EGM no instalado |
| 01 | `beb9434` + cortes `1532`/`1533` | `scratch/aud01_*.py` (7) | 17/121 pre-salida; salto p50 1 237,09 m / máx 3 274,23 m; 31/44 inmóviles; 65/73 = 89,0 % |
| 02 | ZIP `fomento_transit.zip` (SHA del manifiesto) | `scratch/aud02_rebuild.py`; 14 tests focales | 12/42/103/95 exactos; 121 huérfanos; 40/102 |
| 03 | 7 fixtures OSM (SHA-256 7/7) | `scratch/aud03_geometry.py summary|offline-c4b`; 19/19 tests focales | 28/3/72; 67+4+1; C4b ≤ 48,3 m sobre `9174511` |
| 04 | `beb9434` + cortes | `scratch/aud04_*.py` (11) + `scratch/aud04_web/` (vitest 3/3); `movement.test.ts` 10/10 | P0/P1 de movimiento; ventana `[-0,999, 0,000]` m |
| 05 | `d349465`→`28f696e` (docs) / `beb9434` (código); PostgreSQL desechable 5455 (v1) y 5456 (v2) | Chrome DevTools MCP con artefactos en `capturas/` (incl. `24-transcripciones-devtools.md`); `curl` de P0-1 | P0-1 reproducido 4 veces por 3 agentes; P2-1 medido (25 grupos con coordenada idéntica) |
| 06 | `beb9434`; PostgreSQL desechable 5546/5799 | 103 tests `unittest`; `EXPLAIN (ANALYZE, BUFFERS)`; `docker restart` | 103 OK; carrera de `build_snapshot` reproducida |
| 07 | `44c98cb`→`48dd53f` (documentos y código citados) | lectura con citas `archivo:línea` | sin P0; 2 P1 de proceso/riesgo |
| 08 | `beb9434`; PostgreSQL desechable 5548/5561 | lista exacta de `.github/workflows/ci.yml`; `npm` con Node 22.13.1 | 283 casos (5/1/18 skips según entorno); 89/89; carrera de exportación |
| 09 | `beb9434` + cortes; sin base de datos | `scratch/aud04_dwell*.py`, `aud04_cohorte_19656.py` (reproducidos) y **`scratch/aud09_stop_crossing.py` (nuevo)** | 28/44 `STOPPED_AT` con avance; 30/44 cruzan estación; espera declarada 1+5/44 |

### Desviaciones y observaciones de proceso (verificadas)

1. **Incidente 5433** (AUD-06, `ctx_cf7d40a866d7`): escritura aditiva en la base persistente compartida — 6 runs (3090–3095) / 227 / 162 / 5 / 8 filas, 17:04:46Z–17:05:18Z, sin dependencias entrantes, `n_tup_upd = 0`. Causa raíz de diseño: defaults de `services/collector/config.py:34` y `apps/api/config.py:34-35` a `127.0.0.1:5433`. **Decisión del propietario: CONSERVAR** (`INCIDENT_5433.md` §7). Efecto: la verificación histórica «sin skips contra desarrollo» deja de reproducirse; skips 5/1/18 según entorno. Ver `FINDINGS_REGISTER.md` FR-17, PR-01.
2. **AUD-07:** la verificación inicial la lanzó el ejecutor (profundidad 2, contra «profundidad 1» del encargo) sin modelo/esfuerzo; el default local de Codex al redactar es `gpt-6.2-sol` (familia excluida por el encargo) y `BASELINE.md` registraba `gpt-6-luna`: **no se puede saber qué modelo la ejecutó**. Sustituida por revisión formal conforme.
3. **AUD-05:** registrado como «CONFIRMADO» cuando el veredicto era CHANGES_REQUESTED sin re-revisión; corregido en `112a655`, re-revisado formalmente (CHANGES_REQUESTED documental), corregido en v2 y **APPROVED** (`ctx_7a5b7c7a3912`). Limitación: revisor sin navegador.
4. **AUD-04:** ejecutado por `opus` · high en lugar de `sonnet` · high (mejora de capacidad). Cuatro rondas de revisión: el límite del encargo («tras dos rondas fallidas **sin nueva evidencia**, BLOCKED») no se activó porque cada ronda aportó medida nueva (`aud04_cohorte_19656.py`, `aud04_dwell_window.py`, `aud04_test_anchor.py`).
5. **Pausas por límites del proveedor**, sin pérdida de contexto (las tareas conservaron historial): Claude a las 13:06Z (AUD-05, AUD-07), 16:12Z (AUD-01 corrección, AUD-03 revisión) y 18:06Z (AUD-04 r3, reanudado 21:55Z); Codex a las 15:21Z (AUD-03) y 15:28Z (AUD-05 revisión).
6. **Independencia proveedor contrario:** se cumple en todas las revisiones que cuentan (Claude↔Codex). Ningún agente revisó sus propias conclusiones como única validación, salvo la verificación no conforme de AUD-07, que no cuenta.
7. **Autoría:** `git log beb9434..HEAD` → 53 commits, todos `Pedro Matute <pedromaaz13@gmail.com>`, 0 `Co-authored-by` (comprobado antes de este commit). Ningún push, PR ni merge.
8. **Modelos para el H4:** `gpt-6.2-sol` está en `~/.codex/models_cache.json` (`visibility: list`) y es el default de `config.toml`, pero **no tiene recibo de Orca en esta ejecución**; la excepción del propietario lo limita a la tarea H4-11 y debe verificarse `effective.model` al despacharla.
- **AUD-05:** revisión formal (Codex `gpt-5.6-terra` · high, `ctx_53f6eb860b17` + follow-up `ctx_7a5b7c7a3912`): CHANGES_REQUESTED documental -> v2 `39b3e06`/`28f696e` (artefacto por afirmación, P2-3 rectificado, P0-1 con cita corregida) -> **APPROVED documentalmente**. Limitación: el revisor no tuvo navegador; coordenadas/zooms de 18/19 y DevTools no repetidos independientemente. P0-1 verificado de forma independiente por API (x2 revisores) y por captura 20 (coordinador).

### Ronda 2 de AUD-09 (2026-11-24)

- La revisión de AUD-09 (`ctx_e51f26382ff4`) detectó que los arneses aprobados de AUD-01 (`aud01_envelope_predeparture.py`, `aud01_snap.py`) y de AUD-04 (`aud04_dwell.py`, `aud04_dwell_window.py`), y la v1 de `aud09_stop_crossing.py`, usan un horizonte de 190 s desde el ancla, mientras que producción usa `valid_until = ancla + 180 s` para anclas observadas (`packages/movement/rendering.py:279,341-346`). **Ninguna de las cuatro rondas de revisión de AUD-04 ni las tres de AUD-01 lo detectó**: aprobaron la cifra «190 s efectivos» como correcta. Es una lección de proceso para el H4: los arneses de medición deben pasar por la función pública de producción (`render_from_movement`), no por funciones internas con parámetros reconstruidos a mano.
- Corrección: `scratch/aud09_production_recheck.py` (nuevo; equivalencia 44/44 con la envolvente publicada) y `scratch/aud09_stop_crossing.py` v2. Los arneses de AUD-01/AUD-04 **no se modifican** (evidencia aprobada); sus valores de producción constan en `FINDINGS_REGISTER.md` §0bis.
- La tabla de la «Consolidación verificada» de más arriba mantiene sus cifras de la ronda 1 para AUD-01 (salto p50 1 237,09 m, medido con 190 s) y AUD-09 (30/44): **valores de producción: p50 1 229,15 m y 29/44**, con 0/44 travesías de esperas declaradas.

## Cierre (2026-11-24)
- **AUD-09:** revisión independiente Codex `gpt-5.6-sol` · high (`ctx_e51f26382ff4` -> CHANGES_REQUESTED; ronda 2 `ctx_48db1ae73a45` -> **APPROVED**), commits `3014347` y `5b9a7ec`. AUD-00..AUD-09 con aprobación formal conforme a matriz. Pendiente: aceptación del propietario; ningún push/PR/merge; H4 sin autorizar.
