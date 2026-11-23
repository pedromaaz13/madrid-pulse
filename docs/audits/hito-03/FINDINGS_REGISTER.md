# FINDINGS_REGISTER — Registro consolidado de hallazgos de la auditoría del Hito 3

**Elabora:** AUD-09, Claude Opus · High (dispatch `ctx_d10350eb24d0`), contexto de síntesis.
**Revisa:** Codex `gpt-5.6-sol` · High, en contexto nuevo (pendiente). **La severidad de `AUD04-P0-001` y la reclasificación de `AUD01-P0-002` son propuestas de este documento y requieren validación expresa del revisor.**
**Fecha:** 2026-11-23 · **Rama:** `audit/hito-03-adversarial` · **Código auditado:** `mp-022-validacion-integrada@beb9434` (comprobado: `git diff --stat beb9434..HEAD -- . ':!docs/audits' ':!scratch'` vacío; la rama de auditoría no toca producto).

Este registro **no sustituye** a los informes de origen: cada fila remite al hallazgo completo (evidencia, alternativas, prueba de cierre) en su documento. Lo que añade es (1) deduplicación entre auditorías, (2) una severidad consolidada contra **una sola** escala, (3) la separación entre severidad y bloqueo de despliegue público, (4) dos mediciones propias de AUD-09 y (5) los hallazgos de proceso y las discrepancias documentales abiertas.

---

## 0. Estado de revisión de las fuentes (no hay aprobación tácita)

| Fuente | Documento | Estado formal verificado en Orca (inbox + `worker-show`) | Peso en este registro |
|---|---|---|---|
| AUD-00 | `BASELINE.md` | APPROVED (Codex `gpt-5.6-terra` · medium, `ctx_34a13efbb75a`) | pleno |
| AUD-01 | `PRODUCT_AUDIT.md` | APPROVED tras 3 rondas (Codex `gpt-5.6-sol` · high) | pleno |
| AUD-02 | `RAILWAY_GEOMETRY_AUDIT.md` §GTFS | APPROVED 5/5 (Claude `sonnet` · high) | pleno |
| AUD-03 | `RAILWAY_GEOMETRY_AUDIT.md` §OSM | APPROVED tras 2 rondas (Claude `opus` · high) | pleno |
| AUD-04 | `POSITION_MOVEMENT_AUDIT.md` | APPROVED tras 4 rondas (Codex `gpt-5.6-sol` · high); **severidad P0/P1 dejada abierta a AUD-09** | pleno; severidad resuelta aquí (§2) |
| AUD-05 | `FRONTEND_UX_AUDIT.md` | Revisión formal (Codex `gpt-5.6-terra` · high, `ctx_53f6eb860b17`): **CHANGES_REQUESTED documental**, P0-1 **confirmado** (reproducido dos veces). Corrección v2 con artefacto por afirmación en `39b3e06`, `28f696e` (P2-1 reescrito con medición, P2-3 de la v1 era incorrecto, P2-4 nuevo) → **APPROVED documental** (`ctx_7a5b7c7a3912`, follow-up de `ctx_53f6eb860b17`, `msg_5100134ffbf0`). **Limitación declarada:** el revisor no tiene navegador; no repitió DevTools ni verificó de forma independiente las coordenadas/zooms atribuidos a las capturas 18/19 (no sostienen la conclusión medida) | pleno, con esa limitación |
| AUD-06 | `BACKEND_OPERATIONS_AUDIT.md` | APPROVED (Claude `sonnet` · high); corrección de divulgación del incidente 5433 en `2d02227` | pleno |
| AUD-07 | `EGM_REVIEW.md` | APPROVED por revisión formal conforme a matriz (Codex `gpt-5.6-terra` · medium, `ctx_1626c278cd8f` → corrección `48dd53f` → APPROVED). La verificación original `ctx_db3c9aa62ac8` fue autodelegada y de modelo no verificable: **no cuenta** como revisión | pleno desde `48dd53f` |
| AUD-08 | `AUD08_REPRODUCTION.md` | APPROVED tras 2 rondas (Claude `sonnet` · high) | pleno |
| Coordinador | `INCIDENT_5433.md`, `INTEGRATION_PROPOSAL.md` | Documentos del coordinador, **sin revisión independiente**; decisión del propietario sobre 5433 registrada en `INCIDENT_5433.md` §7 | hechos de lectura (recuentos, claves) pleno; propuestas como propuestas |

---

## 1. Escala única y reglas de consolidación

**Escala (encargo §8, textual):**
- **P0 — Bloqueante:** afecta a la veracidad de los datos, la integridad ferroviaria, la seguridad o la funcionalidad esencial.
- **P1 — Importante:** limita significativamente la experiencia, cobertura o fiabilidad.
- **P2 — Mejora:** aporta calidad, mantenibilidad, accesibilidad o rendimiento sin bloquear el producto.
- **DESCARTADO / NO VERIFICADO** según el encargo.

**Problema de origen que este registro corrige:** AUD-01 usó su propia escala («P0 bloquea publicar o falsea un dato mostrado; P1 rompe un criterio declarado o impide publicar sin trabajo real», `PRODUCT_AUDIT.md:749-751`), distinta de la del encargo. Por eso el mismo hecho —28/103 patrones con corredor— es P0 en AUD-01 y P1 en AUD-03, ambos aprobados. Aquí se reclasifica **todo** contra la escala del encargo.

**Segundo eje, independiente de la severidad — «Bloquea despliegue público»:** `Sí` (no se puede publicar sin resolverlo), `Cond.` (bloquea solo si se publica esa superficie o esa afirmación), `No`. Una P2 puede bloquear el despliegue (p. ej. un catálogo que caduca en 26 días) y una P1 puede no hacerlo. Esto responde a la decisión del propietario de distinguir bloqueantes de publicación de mejoras opcionales.

**Deduplicación:** un mismo defecto citado por varias auditorías tiene una sola fila `FR-xx` con todas sus fuentes. Los defectos con causa raíz común se agrupan en un **sistema** (`S1`), sin fundir sus severidades.

---

## 2. Dictamen de severidad de `AUD04-P0-001` y defecto sistémico S1 (propuesta para validación de Codex)

### 2.1 Pregunta

El propietario pide decidir P0 o P1 «con evidencia reproducible», evaluando si ignorar una espera programada puede representar un tren en posición incorrecta o inducir a error: cuánto error de posición, cuánto tiempo, cuántas circulaciones, qué ve el usuario y si se señala; y si es un único defecto sistémico del modelo de paradas junto con `AUD01-P0-001`.

### 2.2 Evidencia reproducida por AUD-09 (sin red, sin PostgreSQL, código de producción)

```sh
.venv/bin/python scratch/aud04_dwell.py            # reproduce: 5,38 m, tol 1,0 m, 75,2 km/h, 1 252,7 m/60 s, dwell_until=None
.venv/bin/python scratch/aud04_dwell_window.py     # reproduce: ventana efectiva [-0,999, 0,000] m
.venv/bin/python scratch/aud04_cohorte_19656.py    # reproduce: post_llegada +141 s; IN_TRANSIT_TO → INCOMING_AT; 75,0 km/h observados
.venv/bin/python scratch/aud09_stop_crossing.py    # NUEVO (AUD-09): barrido de las 44 circulaciones del corte 1533
```

Salida relevante del guion nuevo `scratch/aud09_stop_crossing.py` (reloj de la evidencia MP-019: `calculated_at = ancla + 10 s`, horizonte `stale_after_s = 180 s`):

```text
== operador STOPPED_AT en el corte 1533 ==
   con envolvente: 28; con speed_mps > 0: 28; de ellas en la parada de ORIGEN: 21; con GPS identico en 1532 y 1533: 25
   en origen con avance, por cohorte AUD-04: {'pre_salida': 17, 'en_ventana': 4}
   [stopped] 1023V20280C4a cohorte=en_ventana stop=37011 origen=False gps_identico=True speed=18.76 m/s avance_publicado=3378 m
   [stopped] 1023V19677C5  cohorte=en_ventana stop=35012 origen=True  gps_identico=True speed=22.12 m/s avance_publicado=3981 m
   ... (28 filas; velocidades 8,68–30,00 m/s; avance publicado 1 563–5 401 m)
== TOTAL: n=44
   cruzan >=1 parada sin retenerse: 30/44  (paradas cruzadas: total=52)
   cruzan >=1 parada con espera DECLARADA: 5/44  (las 5 en el origen 35012, todas STOPPED_AT con GPS idéntico)
   dwell_until publicado: 0/44
== en_ventana: n=25 → cruzan >=1 parada sin retenerse: 16/25
```

### 2.3 Respuesta a cada pregunta del propietario

| Pregunta | Respuesta medida | Fuente |
|---|---|---|
| ¿Ignorar la espera **declarada** representa un tren en posición incorrecta? | En el único caso medido (`1023V19656C5`) **no hay observación que lo contradiga**: el operador lo declara `INCOMING_AT` (no `STOPPED_AT`) y la velocidad publicada (75,2 km/h) coincide con la observada entre cortes (75,0 km/h). Lo demostrado es que el contrato **no puede expresar** la espera que el horario declara, no que el tren estuviera parado. | `aud04_cohorte_19656.py` |
| ¿Cuánto error de posición? | Cota: `speed × espera` = **1 252,7 m** si el tren hubiera honrado los 60 s (`19656`); a los 30 s, 626,4 m frente a 0 m con la espera honrada. Para las 5 circulaciones que cruzan una parada con espera declarada dentro del horizonte, cota **221 m**. | `aud04_dwell.py`, `aud09_stop_crossing.py` |
| ¿Cuánto tiempo? | Hasta la siguiente ancla (cadencia real ~20–22 s según MP-003, **no verificada en vivo** en esta auditoría) y como máximo el horizonte de 190 s efectivos; a continuación, corrección hacia atrás. | `AUD04-NO-VERIFICADO-002` |
| ¿Cuántas circulaciones? | Espera **declarada** ignorada: 1/44 anclado en la parada + 5/44 que la cruzan dentro del horizonte; esas 5 están **además** detenidas en el origen (las cubre la fila S1-a). La espera declarada existe solo en el 9,9 % de las paradas (`aud01_stopgap.py`). | `aud09_stop_crossing.py` |
| ¿Qué ve el usuario y se señala? | Símbolo `dashed` («Proyectada — Avance estimado desde la última observación; no es una lectura GPS»): **se señala que es una estimación**, no se señala que contradice una espera programada; al llegar la siguiente ancla, salto atrás. | `POSITION_MOVEMENT_AUDIT.md` §1, `format.ts` |

### 2.4 Dictamen propuesto

1. **`AUD04-P0-001` (tolerancia de 1,0 m + guarda `anchor_at < candidate`) → P1.** Cita del encargo: P0 «afecta a la veracidad de los datos, la integridad ferroviaria…»; P1 «limita significativamente la … fiabilidad». Ningún dato observado contradice lo publicado en el caso medido, el error está acotado (≤ 1,25 km durante ≤ 60 s en el peor caso medido), el símbolo se rotula como estimación y la espera declarada afecta a una minoría de paradas. Es un defecto real y estructural de fiabilidad, no una publicación demostrablemente falsa. **Condición para elevarlo a P0:** una captura en vivo ≥ 2 h en la que, sobre observaciones `STOPPED_AT` en paradas con espera declarada, el símbolo publicado haya avanzado > 200 m en ≥ 10 % de los eventos.
2. **El defecto que sí es P0 es más amplio que `AUD01-P0-001` y lo absorbe: `S1-a`.** La medida nueva muestra que el operador declara **`STOPPED_AT` 28 de las 44** circulaciones con cadena completa y **las 28** reciben `speed_mps > 0` (1,6–5,4 km de avance publicado en el horizonte); 25 de ellas tienen GPS idéntico en dos cortes separados 77 s. Se reparten en: **17** en origen antes de su salida (exactamente el conjunto de `AUD01-P0-001`), **4** en origen **después** de su hora de salida (salida retrasada; no las cubre la corrección (B) de AUD-01, que solo actúa antes de la primera salida) y **7** detenidas en paradas intermedias. Aquí sí hay observación que contradice lo publicado: el operador dice «detenido», la posición no cambia en 77 s y el mapa lo mueve a 31–108 km/h. **P0 por veracidad.** *Salvedad declarada:* un GPS idéntico en dos cortes podría ser también un fijo repetido por el proveedor (`AUD04-P2-004`: `observed_at` es sello de lote); el `STOPPED_AT` del operador lo corrobora, pero no es una prueba física independiente.
3. **Es un único defecto sistémico del modelo de paradas (`S1`), con varias manifestaciones de distinta severidad.** Causa raíz común, confirmada en código: la envolvente (`packages/movement/rendering.py::_envelope`, consumiendo `TripSchedule`) **deduce el estado del tren respecto a las paradas solo a partir del progreso geométrico y la interpolación del horario**, e ignora (a) el estado por parada que el operador publica (`current_status`, `current_stop_id`, presentes en `VehiclePositionObservation` y hoy usados solo para `station_skip_anomaly`), (b) la ventana temporal del viaje (antes de salir / tras llegar) y (c) las esperas no declaradas en GTFS (90,1 % de las paradas con llegada = salida). Manifestaciones: S1-a (P0), `AUD04-P0-001` (P1), `AUD01-P1-005` horizonte/travesía de estaciones (P1; **30/44** envolventes cruzan al menos una estación sin retenerse, 16/25 en ventana), `AUD04-P1-001` retroceso al expirar (P1), `AUD04-P2-006` fórmula de ADR-0014 §2 (P2) y `AUD01-P2-010` `stop_time_update` descartado (P2). **Una sola corrección de diseño** (estado de parada anclado al operador + ventana de viaje) resuelve S1-a y `AUD04-P0-001` a la vez —es la alternativa (B) de AUD-04—; por eso el roadmap las trata en un único trabajo (H4-00 + H4-04 en `NEXT_STEPS_PROPOSAL.md`), aunque sus severidades se conserven separadas.

---

## 3. P0 — Bloqueantes

| FR | Fuentes | Componente | Hallazgo consolidado | Evidencia reproducible | Despliegue público | Recomendación | Prueba de cierre |
|---|---|---|---|---|---|---|---|
| **FR-01 (S1-a)** | `AUD01-P0-001`; AUD-09 §2; cohortes `AUD-04` §0.2 | `packages/movement/rendering.py::_envelope`, `schedule.py`; contrato ADR-0014 §2 | La envolvente pone en movimiento circulaciones que el operador declara detenidas o que no han salido: **28/44** `STOPPED_AT` con `speed_mps > 0` (17 pre-salida, 4 salida retrasada en origen, 7 en paradas intermedias); peor caso `1023V20478C4b` a 38,65 min de su salida con 5 700,6 m de avance falso; al llegar el ancla siguiente, salto p50 **1 237,09 m** / máx **3 274,23 m** (31/44 inmóviles reales). | `aud01_envelope_predeparture.py`, `aud01_snap.py`, `aud09_stop_crossing.py` | **Sí** | Estado de parada anclado al operador (`current_status`/`current_stop_id`) + ventana de viaje (antes de salir, salida retrasada, tras llegar) en la traducción de MP-019; ADR-0014 enmendado (H4-00 → H4-04). | Regresión sobre el corte `1533` real: **0** circulaciones `STOPPED_AT` con GPS idéntico entre cortes reciben `speed_mps > 0`; 0 pre-salida con avance; sin anular el avance de ninguna circulación `IN_TRANSIT_TO` que avanzó entre cortes; H1/H2a de AUD-01 medidas en vivo ≥ 2 h. |
| **FR-02** | `AUD05-P0-1` (reproducido por el coordinador, por el ejecutor en navegador, por `ctx_41022ed63263` y dos veces por `ctx_53f6eb860b17`) | `apps/api/db.py:178-223` (`recent_ingestion_runs` no acota por `now`) + `apps/api/service.py:381` | En replay, `/api/v1/snapshot?at=` anterior a una ingesta ya persistida marca un feed con datos reales (468 entidades, `source_timestamp` 14:33:21Z) como `status="unknown"` con `data_age_s = poll_age_s = -71,0`: el sistema **tiene** el dato y lo presenta como ausente, con edades negativas visibles en el banner. Acotado a snapshot/Live (el tablero no expone `degraded`). | 3 `curl` de `FRONTEND_UX_AUDIT.md` §2 contra PostgreSQL desechable + `replay_three_snapshots` | **Cond.** (sí si se publica replay o cualquier `?at=` histórico; no afecta al directo sin `?at=`) | Acotar las ejecuciones de ingesta por `started_at <= now` y separar «edad negativa» (error de reloj/consulta) de «nunca hubo ingesta». | Regresión con `?at=2026-11-20T14:32:10Z` tras ingerir ambos cortes: `status` ≠ `unknown`, edades ≥ 0 o `null` declarado; la suite de 283 debe ejercer esta combinación (hoy no la ejerce, `AUD08_REPRODUCTION.md` §Reconciliación). |

---

## 4. P1 — Importantes

| FR | Fuentes | Hallazgo consolidado | Evidencia clave | Despliegue público | Recomendación (detalle en la fuente) |
|---|---|---|---|---|---|
| **FR-03 (S1)** | `AUD04-P0-001` (**reclasificado P0→P1**, §2.4) | La espera programada solo se expresa si el ancla cae en una ventana de ~1 m (`[-0,999, 0,000]` m) de 45 165 m: tolerancia 1,0 m frente a error de proyección p95 20,8 m, y la guarda de `_envelope` recorta todo el lado positivo. `rendering.py:185-187` afirma lo contrario. El test de regresión coloca su ancla en el borde de la ventana (offset −0,000011 m). | `aud04_dwell*.py`, `aud04_test_anchor.py` | Sí (junto con FR-01: misma corrección) | Alternativa (B)+(C) de AUD-04: espera por `stop_id` + guarda simétrica. |
| **FR-04 (S1)** | `AUD01-P1-005`; AUD-09 §2.2; hipótesis H4 de AUD-01 | El horizonte (180 s configurados / **190 s efectivos**) se reutilizó de un umbral de frescura «calibrable» (DEC-010) sin recalibrar; intervalo mediano entre paradas = 180 s; espera declarada en el 9,9 % de las paradas. **Medido por AUD-09:** 30/44 envolventes cruzan ≥ 1 estación sin retenerse (16/25 en ventana; 52 estaciones cruzadas). Baseline de un solo corte para H4 (≥ 30 %), no refutación. | `aud01_stopgap.py`, `aud09_stop_crossing.py` | Sí (afirmación de «movimiento fluido y fiel») | Recalibrar con captura en vivo; horizonte por tramo hasta la próxima parada o espera mínima por parada; enmienda de ADR-0014 §2. |
| **FR-05 (S1)** | `AUD04-P1-001` | Al cruzar `stale_after_s` el símbolo retrocede p50 **2 357,9 m** (25/25 en ventana; máx 3 959,2 m) y el aviso de congelación desaparece en ese instante porque depende de `valid_until`, que `stale_frozen` pone a `null`. | `aud04_sweep.py` | Sí | Congelar en la última posición **dibujada** o publicar la regresión explícitamente; aviso independiente de `valid_until`. |
| **FR-06** | `AUD04-P1-002` (relacionado: `AUD04-P2-003`, `-P2-004`, `-P2-008`) | El mapa no distingue observación GPS (`raw`) de proyección sobre vía (`map_matched`): una sola entrada `anchor` en `METHOD_STYLES`, y la etiqueta afirma que la proyección es «la coordenada que publicó la fuente» (hasta 106,8 m del GPS). Los 75–78 `anchor` sin corredor validado reciben el símbolo más autoritativo. | arnés `scratch/aud04_web/` (vitest) | Sí (veracidad del rótulo) | Separar estilo y texto por `coordinate_space`; texto correcto para proyección. |
| **FR-07** | `AUD06-P1-001`; misma familia que `AUD08-P2-001` | `build_snapshot()` no fija una vista transaccional: puede publicar `revision.sequence` de una ingesta nueva sin su vehículo. Contradice ADR-0014 §5 («revisión ordenable»). | Reproducido por ejecutor y revisor (PostgreSQL desechable 5546/5799) | Sí (con tráfico concurrente real) | Lectura `REPEATABLE READ` única o watermark `source_ingestion_run.id` común a todas las lecturas. |
| **FR-08** | `AUD01-P0-002` (**reclasificado P0→P1** por escala, §1) + `AUD03-P1-001` + `AUD03-P1-002` + `AUD01-P1-009` (parte geométrica) | Cobertura geométrica: 28/103 patrones `validated` = **13 878 / 36 097 circulaciones de red (38,45 %)**, 242 129/537 899 llamadas (45,0 %); 8 de 12 líneas sin ningún corredor; 72 `pending` **sin ninguna prueba geométrica ejecutada** (67 accionables por adquisición, 4 C4b con vía ya congelada en sentido opuesto, 1 feed truncado); el CSV canónico da el mismo `reason` a los 72. El fallback `raw` es honesto (no fabrica proyección): por eso P1 (cobertura), no P0 (veracidad). | `aud03_geometry.py summary|offline-c4b`, `mp-018-corridor-coverage.csv` | **Sí para la afirmación «mapa de toda Cercanías Madrid con movimiento»**; No para un mapa que declare explícitamente la cobertura por línea | Lotes por circulaciones (C4b coste cero + caveats → 35/103, 43,35 %; luego C1, C10, C2, C3, C7, C8a, C8b, C9); `reason` desagregado; publicar numerador ponderado. |
| **FR-09** | `AUD01-P1-003`; `HITO_3_BACKLOG.md:36` | `route_coverage_pct` de la matriz vinculante es tautológico (121/121 = 100 %); la cobertura de posicionamiento real medida es **65/73 = 89,0 %**, C1 50 %, C10 60 % (un solo sondeo). | `aud01_coverage.py` | Cond. (si se publica una cifra de cobertura) | Definir numerador/denominador; medir por línea en ≥ 10 sondeos (H3). |
| **FR-10** | `AUD01-P1-004` | `position_age_p50_s/p95_s` de la matriz vinculante son una constante inyectada, no una medida. | `PRODUCT_AUDIT.md` §11 | Cond. | Medir desde observaciones reales. |
| **FR-11** | `AUD01-P1-006` | `README.md:23`, `ARCHITECTURE.md:3` y `DATA_MODEL.md:3` siguen declarando que no hay producto. | lectura directa | **Sí** (coste: minutos) | Actualizar portada; puerta de documentación automatizable. |
| **FR-12** | `AUD01-P1-007` | El mapa base consume `tile.openstreetmap.org` (`MapView.tsx:195`), servicio operativo de la OSMF con política de uso propia, **no registrado** en `docs/legal/`. | lectura directa | **Sí** | Registrar y cumplir la política o cambiar a un proveedor/teselas propias autorizadas (gate humano: coste/licencia). |
| **FR-13** | `AUD01-P1-008`; DEC-038; H7a/H7b; `EGM` §5 | Coste por espectador: 254,73 ms p50 de snapshot en proceso, ~66 ms de conexión por petición (sin pool), sin snapshot en CDN pese a ser principio de `ARCHITECTURE.md:68-69`; cota derivada ~30 espectadores/núcleo **no medida** con ASGI + red. | `mp-019-explain-y-bench.md`, `mp-022-benchmark.md` | **Sí** (capacidad pública no demostrada) | Prueba de carga real (H7a) antes de decidir pool (DEC-038) y snapshot pregenerado (H7b). |
| **FR-14** | `AUD01-P1-009`; `AUD01` §9.1-9.2, §15 | Ninguna puerta de aceptación del Hito 3 es falsable: documentar un hueco basta para que deje de bloquear (`AMPLIACION:40`, `MATRIZ-CIERRE:15`, `PROMPT-UNICO-ORCA.md:19`). Explica sin mala fe el cierre con 28/103. | citas textuales | No (proceso) | Un umbral numérico y un comando por puerta en el H4. |
| **FR-15** | `EGM` P1-2 (drift #3); `AUD06-NO-VERIFICADO-001`; `AUD08-NO-VERIFICADO-001`; DEC-004 | El *exit gate* F3 (`PLAN.md:26-29`) exige 24 h de ingesta; la evidencia son 13–20 min y 823,2 s/21 ciclos. Ninguna operación 24/7 verificada; el ≈7 GB/año y ≈19 MB/día son proyecciones de minutos. | `mp-021-coste-colector-continuo.md` | **Sí** para un servicio 24/7 | Host persistente autorizado y ventana ≥ 24 h (preferible 72 h) con métricas y fallos ensayados. |
| **FR-16** | `EGM` P1-4; ADR-0002 | Dependencia exclusiva de que Renfe siga publicando GTFS-RT sin cambios de contrato; riesgo ya declarado como hipótesis en ADR-0002. | `config.py:23-28`, `ADR-0002:13,25-27` | No (riesgo aceptado conscientemente) | Monitorizar cambios de esquema y salud de feed (ya existe); plan de degradación. |
| **FR-17** | Incidente 5433 (`INCIDENT_5433.md`); `AUD08` | **Defaults peligrosos de PostgreSQL:** `services/collector/config.py:34` y `apps/api/config.py:34-35` apuntan por defecto a `127.0.0.1:5433/madrid_pulse` (la base de desarrollo compartida). Sin variable, cualquier ejecución escribe ahí, sin guarda. Además la API lee `MADRID_PULSE_DATABASE_DSN` y el colector `MADRID_PULSE_DATABASE_URL`, lo que permite que convivan dos bases sin aviso (mecanismo que **probablemente** explica el «1 skip» histórico; inferencia, ver §9). Se materializó: AUD-06 añadió 6 runs/227/162/5/8 filas. | `INCIDENT_5433.md` §2-3; `AUD08_REPRODUCTION.md` §Entorno | **Sí** (integridad operativa de cualquier entorno compartido) | Tarea H4 específica decidida por el propietario (H4-11): sin default, fallo seguro, una sola variable, aislamiento de tests, guarda contra escritura accidental. |
| **FR-18** | `AUD01` §7.3; DEC-002, DEC-003 | Sin licencia de código decidida (DEC-002 `Pendiente`) ni visibilidad (DEC-003). Gate exclusivo del propietario. | `docs/DECISIONS.md` | **Sí** (literalmente bloquea publicar el repositorio) | Decisión del propietario. |

---

## 5. P2 — Mejoras (con las que bloquean despliegue marcadas)

| FR | Fuentes | Hallazgo (una línea) | Despliegue público |
|---|---|---|---|
| FR-19 | `AUD01-P2-014` | La vigencia del GTFS solo se comprueba al arrancar (`gtfs_source.py:158`); el ZIP del kit vence el **2026-12-19** y no hay refresco en `infra/operate/`: un proceso vivo servirá un catálogo caducado en silencio. | **Sí** (vence en menos de cuatro semanas) |
| FR-20 | `AUD06-P2-001` = `EGM` P2-2 (drift #2) | `affected_stop_ids` filtra alertas por relevancia geográfica pero no se persiste (`db.py:171-196`). | No |
| FR-21 | `AUD06-P2-002` = `EGM` P2-1 (drift #1) | FK `trip_id` nunca poblada por el colector; la API resuelve vía `Topology` en memoria (documentado). | No |
| FR-22 | `AUD08-P2-001`; ADR-0015 §1 | La primera exportación concurrente no es un corte atómico multi-tabla (1 posición / 2 runs); el reproceso converge. | No (Cond. si se archiva el día en curso) |
| FR-23 | `AUD02-P2-001`; `AUD03-P2-002` | 12/42/103/95 son identidad de fuente; usable: 40 rutas con patrón, 102 patrones ≥ 2 paradas, **121 trips huérfanos** (C8b truncado en origen, `stop_sequence` 025/032). No marcar `non_traversable`. | No |
| FR-24 | `AUD02-P2-002` | `service_dates_covering` retrocede un día fijo; un servicio > 48 h se asignaría mal (latente: máximo real 24:53). | No |
| FR-25 | `AUD03-P2-001` | Tres `PatternCaveat` confunden «no para» con «no pasa por esa vía» (31 viajes): pasan continuidad/distancia/orden. | No |
| FR-26 | `AUD04-P2-001` | `_envelope` mezcla reloj de pared y segundos reales: 8 444 m fabricados el día de adelanto de hora o congelación de una hora el de atraso (latente; próximo: 2027-03-28). | No (Cond. si se opera en esas fechas) |
| FR-27 | `AUD04-P2-002` | `position` y `rendered` publican dos coordenadas del mismo tren y mismo instante, hasta 429,5 m aparte. | No |
| FR-28 | `AUD04-P2-003` | `interpolated_between_known_anchors` inalcanzable con `display_lag_s = 0`; su forma `ring` coincide con `stale_frozen`. | No |
| FR-29 | `AUD04-P2-004`, `AUD04-P2-008` | `observed_at` es un sello de lote (no hora del fijo GPS) rotulado «GPS observado»; en `schedule_only` el ancla es la observación **rechazada** y se rotula «última lectura confirmada». | Cond. (rótulos) |
| FR-30 | `AUD04-P2-005`; `AUD01-P2-015` | Umbral `implausible_speed` del snapshot a 900 km/h (el evento de 200 km/h se guarda y no llega al directo); calidad mide sobre cuerda y movimiento sobre arco (caso ciego `20277`). Ilustrado en vivo por los 8 eventos del incidente 5433. | No |
| FR-31 | `AUD04-P2-006` (S1) | ADR-0014 §2 publica la fórmula sin `dwell_until` y declara `speed_mps = 0` con espera, al contrario que código, API y cliente. | No (se resuelve en la enmienda de ADR-0014) |
| FR-32 | `AUD04-P2-007` | Una circulación `CANCELED` se dibuja igual que una en marcha (latente en Madrid). | Cond. |
| FR-33 | `AUD01-P2-010` (S1) | El array `stop_time_update` por parada se descarta al normalizar; no se puede decir «esta parada se omite». | No |
| FR-34 | `AUD01-P2-011` | `packages/geo/madrid.py` codifica literales `route_id` contra ADR-0011 §3. | No |
| FR-35 | `AUD01-P2-012` | `route_color` oficial se parsea y no se expone; paleta hash (H5 sin medir). | No (visible al primer usuario) |
| FR-36 | `AUD01-P2-013`; DEC-033 (b) | La puntualidad publicada usa 300 s sin calibrar, umbral ausente del contrato y de la pantalla. | Cond. (si se publica la métrica) |
| FR-37 | `AUD01-P2-016`, `-017`, `-018`; `EGM` P2-3, P2-5..P2-8 | Deriva de gobernanza: ADR-0011 `Aceptado` contradicho sin enmienda; backlog propio de H3 (áreas 5, 6, 8) perdido; estándar de evidencia no uniforme (MP-016/017 sin `docs/evidence/`); `DATA_MODEL.md` partido sin referencia cruzada; modelo línea/`route_id` frágil; umbrales sin recalibrar; índices descubiertos reactivamente; carga de onboarding alta. | No |
| FR-38 | `EGM` P2-4; `AUD01-DESC-004` (residuo) | Sin autenticación ni limitación de tasa en la API, sin ADR que lo decida (CORS same-origin es *default-deny* y queda descartado como agujero). | **Sí** para exposición pública (abuso/coste) |
| FR-39 | `AUD05-P2-1` (v2, APPROVED) | En la vista inicial (z 9,6, 104 circulaciones en encuadre) **25 grupos** de circulaciones comparten exactamente la misma coordenada dibujada y 162 pares de símbolos se solapan: no se distingue cuántos trenes hay en cada punto. **Relación con FR-01 (AUD-09):** el mayor grupo (6 × C5: `19674, 19678, 19682, 20842, 20850, 20854`) son exactamente las 6 circulaciones `STOPPED_AT` en el origen `35607` con GPS idéntico de `aud09_stop_crossing.py` (unidades estacionadas), a las que la envolvente da la misma velocidad: se apilan y se mueven juntas. | No (P2 de legibilidad; su causa principal se corrige con FR-01) |
| FR-40 | `AUD05-P2-2` (v2, APPROVED) | El buscador carece de `id`/`name` (issue literal de DevTools, `msgid=23`; volcado del único campo de formulario). | No |
| FR-41 | `AUD05-P2-3` (v2, **corregido**, APPROVED) | En el fallback sin WebGL, «Seguir tren» activa «Dejar de seguir» y el aviso «Siguiendo · arrastra para soltar la cámara» sin mapa que seguir (capturas 25/26). La v1 («sin efecto observable») era incorrecta. | No |
| FR-42 | `AUD05-P2-4` (v2, nuevo, APPROVED) | La leyenda del mapa tapa la tercera fila de la lista de novedades desplegada (captura 20, escritorio 1440×900). | No |

---

## 6. DESCARTADO (hipótesis adversas refutadas con evidencia)

| Fuente | Hipótesis refutada | Evidencia |
|---|---|---|
| `AUD01-DESC-001` | La arquitectura está sobre-ingenierizada. | Cada proceso aísla un modo de fallo medido (DEC-040/041). |
| `AUD01-DESC-002` | El cliente decide cuánto avanzar / fabrica posiciones. | `movement.ts:74-96`: solo aplica la envolvente; error cliente-backend 6,6 cm. |
| `AUD01-DESC-003` | La salud de feed copió a Valfiguer solo en lo fácil. | Cinco campos completos; dedupe no resetea la edad (sin prueba de equivalencia semántica). |
| `AUD01-DESC-004` | La ausencia de CORS es un agujero. | *Default-deny* same-origin; autenticación y tasa siguen abiertas (FR-38). |
| `AUD02-DESCARTADO-001/002` | Los recuentos 12/42/103/95 o las secuencias compartidas son erróneos. | Igualdad estructural completa con `Catalog`; 0 IDs duplicados. |
| `AUD03-DESCARTADO-001` | «Los 75 fallan porque OSM no tiene geometría». | 3 `partial` pasan la prueba; 4 C4b encajan sobre `9174511`; 67 sin fuente local. |
| `AUD03-DESCARTADO-002` | Las fixtures OSM están inventadas o corruptas. | 7/7 SHA-256, 0 gaps, 19/19 tests focales. |
| `AUD04-DESCARTADO-001..004` | GPS alterado; partición por `vehicle_id` fusiona circulaciones; DEC-039 rompible por `service_seconds`; dos marcos de `progress_m` contradictorios. | 0/931 entidades alteradas; 0/3 079 fusiones en Madrid; ida y vuelta solo falla en la hora inexistente declarada; 28/28 `forward=True`. |
| `AUD05` §5 (2) | Divergencia con la maqueta; mapa sin etiquetas de capa. | Documentado como deliberado en `INTERACCIONES.md` y `apps/web/README.md`. |
| `AUD06-DESCARTADO-001/002` | `SKIPPED` fabrica omisiones; índices/OpenAPI/caché no coinciden. | Primer `next_stop_id` no `SKIPPED`; 15 endpoints iguales, 200/304, `no-store`, Index Scan. |
| `AUD08-DESCARTADO-001` | Caída de feed en DST fabrica una fecha de servicio. | Error persistido sin observación; primera ocurrencia de 02:30. |
| `EGM` DESCARTADO | El contrato de revisión (`scope`/`sequence`/`tiebreak`) es sobre-ingeniería. | Los hashes no son ordenables; complejidad justificada. |
| H4-02 del encargo como tarea independiente (ver `NEXT_STEPS_PROPOSAL.md`) | «Las secuencias, identidades y coordenadas de estación están mal». | AUD-02: 0 discrepancias; AUD-03: paradas a ≤ 48,3 m de los corredores validados. Lo residual pasa a P2 (FR-23/24/35). |

---

## 7. NO VERIFICADO (límites de toda la auditoría)

| ID consolidado | Qué no se pudo comprobar | Fuentes | Qué haría falta |
|---|---|---|---|
| NV-01 | Operación 24/7 y estabilidad durante días. | `AUD06-NV-001`, `AUD08-NV-001`, `EGM` P1-2 | Host persistente autorizado, ≥ 24–72 h. |
| NV-02 | Comportamiento con feed en vivo y cadencia real (~20 s): frecuencia real de FR-01/03/04/05; hipótesis H1, H2a, H3, H3b, H4. | `AUD01-NV-004`, `AUD04-NV-002` | Captura en vivo ≥ 2 h y ≥ 3 días (H4-12). |
| NV-03 | Capacidad con ASGI + red + concurrencia; ganancia de snapshot pregenerado (H7a/H7b). | `AUD01-NV-003` | `wrk`/`locust` contra `uvicorn` real. |
| NV-04 | Usuarios reales: n = 0 en tres hitos (H5, H6, H8). | `AUD01-NV-005` | Prueba A/B n ≥ 30 para H5; desagregación por canal para H6. |
| NV-05 | Relaciones OSM utilizables para C1, C2, C3, C7, C8a, C8b, C9, C10, y causa física de los 67. | `AUD01-NV-001`, `AUD03-NV-002` | Adquisición por lotes (requiere red, ODbL y gate). |
| NV-06 | Longitud ferroviaria OSM única de Madrid (denominador físico). | `AUD03-NV-001` | Grafo de *ways* deduplicado. |
| NV-07 | Andenes, accesos y estación física frente a punto de parada. **El GTFS de Renfe no publica `location_type` ni `parent_station`** (`stops.txt`: `stop_id,stop_name,stop_lat,stop_lon,wheelchair_boarding`), así que la confusión estación/andén/acceso no es decidible con esta fuente; el hueco de 5,38 m de `19656` es entre la proyección de la estación y la del tren. | AUD-09 (`unzip -p … stops.txt`), `AUD02` | Fuente adicional de andenes con licencia, o aceptar la estación como punto. |
| NV-08 | Render real en MapLibre de la indistinción `raw`/`map_matched` y de la colisión `ring`/`ring` (percepción, escala de grises, daltonismo); rendimiento y memoria con cientos de vehículos. | `AUD04-NV-003`, `AUD05` §7 | Sesión de navegador con perfilado; revisor con navegador. |
| NV-09 | Suites `pytest` en el `.venv` de AUD-04 (no instalado); camino PostgreSQL completo del snapshot en AUD-04. Cubiertos parcialmente por AUD-06/AUD-08 (283 casos `unittest`). | `AUD04-NV-001/004` | Declarar `pytest` o mantener `unittest`. |
| NV-10 | Estado actual de Via Península, Valfiguer y apps oficiales (comparación fechada 2026-11-18). | `AUD01-NV-002` | Consulta en vivo. |
| NV-11 | ADD/REMOVE de `calendar_dates.txt` contra un dato real (Renfe no lo publica). | `AUD02-NV-002` | Fixture real atribuida de otro productor. |
| NV-12 | Cifras vivas de la relación OSM `9174512` (versión, longitud, hash). | `AUD03` revisión §2 | Congelar la relación. |
| NV-13 | Interfaz con tecnología de apoyo y en interacción continua: lector de pantalla real (solo se probó el árbol de accesibilidad), arrastre y seguimiento en vivo, «Ampliar panel» en móvil, maquetas 02–04/`live.html`. Las afirmaciones de la v1 de AUD-05 sin artefacto (5–8 marcadores en ~25 px, zoom 13, «Centrar Madrid» por defecto, anuncio por lector) se **retiraron** en la v2. | `FRONTEND_UX_AUDIT.md` v2 §7; revisión `ctx_53f6eb860b17` | Sesión con lector de pantalla; prueba de interacción grabada. |

---

## 8. Hallazgos de proceso de la propia auditoría

| ID | Hallazgo | Evidencia | Consecuencia |
|---|---|---|---|
| PR-01 | **Escritura accidental en la base persistente 5433** durante AUD-06 (dispatch `ctx_cf7d40a866d7`, 17:04:46Z–17:05:18Z): 6 `source_ingestion_run` (ids 3090–3095), 227 posiciones, 162 actualizaciones, 5 alertas, 8 `data_quality_event`; **solo aditiva** (`n_tup_upd = 0`, filas previas intactas), sin dependencias entrantes, detenida y escalada por el propio worker. Causa raíz de diseño: FR-17. El primer informe de AUD-06 lo negaba (`:25`, `:281`); corregido en `2d02227`. **Decisión del propietario (2026-11-24): CONSERVAR**; la Opción B (limpieza) queda descartada. | `INCIDENT_5433.md` §3, §7; dump fuera del repo (SHA-256 `e319e8e4…727d7`) | La línea base de 5433 pasa a `895/646/8/126/8`; **la verificación histórica «suite sin skips contra desarrollo» (668/484/3/120/0) deja de ser reproducible**; los resultados reproducibles deben usar PostgreSQL desechable. |
| PR-02 | La revisión original de AUD-07 la creó el propio ejecutor (`ctx_db3c9aa62ac8`, profundidad 2, contra «profundidad 1»), sin modelo ni esfuerzo registrados (Orca: `null`; default local de Codex = `gpt-6.2-sol`, familia excluida por el encargo), veredicto «verificado con matices», correcciones `ea49e6a` sin re-verificar. | `worker-show ctx_db3c9aa62ac8` | Sustituida por revisión formal conforme (`ctx_1626c278cd8f`, `gpt-5.6-terra` · medium): CHANGES_REQUESTED → `48dd53f` → APPROVED. |
| PR-03 | AUD-05 constaba en el registro del coordinador como «CONFIRMADO» cuando su único veredicto era «CHANGES_REQUESTED por P0-1» sin re-revisión. | inbox `msg_dd824ccd8ec2` | Revisión formal `ctx_53f6eb860b17`: CHANGES_REQUESTED documental (P0-1 confirmado) → v2 `39b3e06`/`28f696e` (la v1 contenía una afirmación falsa en P2-3 y citas de captura erróneas en P0-1) → **APPROVED** (`ctx_7a5b7c7a3912`). Lección para el H4: toda afirmación de ejecución en navegador necesita artefacto, porque el revisor de Codex no tiene navegador. |
| PR-04 | Desviación de la matriz: AUD-04 la ejecutó Claude `opus` · high en lugar de `sonnet` · high. Mejora de capacidad, no degradación; registrada. | `worker-show ctx_079d97438512` | Ninguna sobre la validez; consta en el log. |
| PR-05 | Las suites verdes no ejercen los P0: los 283 casos pasan con FR-01 y FR-02 presentes. | `AUD08_REPRODUCTION.md` §Veredicto | Las pruebas de cierre del H4 deben fallar contra `beb9434`. |

---

## 9. Discrepancias documentales abiertas (registradas por AUD-08) y su resolución

| Discrepancia | Dónde | Resolución de AUD-09 |
|---|---|---|
| «68» frente a 67 | AUD-01 ronda 1 frente a AUD-03 | **Resuelta:** 68 = 67 patrones accionables sin fuente/intento + 1 patrón C8b truncado. Universos: 75 no `validated` = 72 `pending` + 3 `partial`; 72 = 67 + 4 C4b + 1 truncado. No hay cifras rivales. |
| «72 de 103 sin corredor validado» frente a 75 | `POSITION_MOVEMENT_AUDIT.md:141`, `:543` | **Resuelta (editorial):** sin corredor validado son **75** (72 `pending` + 3 `partial`); los 75–78 `anchor` son **circulaciones**, no patrones. No altera ninguna medida de AUD-04 (que solo usa los 28 `validated`). Se registra aquí y no se reescribe el informe aprobado. |
| «hasta 180 s después del ancla» frente a 190 s | `POSITION_MOVEMENT_AUDIT.md:455` | **Resuelta (editorial):** 180 s configurados (`stale_after_s`) desde `calculated_at`; **190 s efectivos** desde el ancla (`calculated_at = ancla + 10 s`). Las cifras medidas no cambian. |
| «17 tablas» | `BACKEND_OPERATIONS_AUDIT.md:27` | **Resuelta:** 15 tablas base + 2 vistas PostGIS (`geometry_columns`, `geography_columns`). |
| Fila de 5433 que dice que `BACKEND_OPERATIONS_AUDIT.md:25/:281` «requieren corrección» | `AUD08_REPRODUCTION.md` §Reconciliación | **Obsoleta:** `2d02227` ya las corrigió; el informe actual divulga el incidente (observación no bloqueante del revisor de AUD-08). |
| «1 skip histórico» atribuido al mecanismo DSN/URL | `AUD08_REPRODUCTION.md` §Entorno | **Inferencia, no hecho medido en 5433:** el revisor lo reprodujo con una base desechable de 24 vehículos, no con 5433. Se mantiene como explicación plausible. |
| Skips 5 / 1 / 18 | `AUD08_REPRODUCTION.md` | **Resuelta:** 5 con `data/` y base aislada; 1 con DSN de la API y URL del colector en bases distintas (no representativo de CI); **18 en checkout limpio = lo que vería CI** (265 ejecutados). «283/5» no es un resultado de CI. |
| «seis ciclos» frente a «dos ciclos» | `BACKEND_OPERATIONS_AUDIT.md:28-29` frente a `INCIDENT_5433.md` §2 | **Resuelta:** dos ciclos completos × tres feeds = seis `source_ingestion_run`. |
| Verificación (b) de la Opción B | `INCIDENT_5433.md` §6 («`max(id)` ≤ 195») | **Inconsistente** con ids de run en el rango 3090–3095 (la secuencia ya estaba por encima de 3089); **irrelevante** tras descartar la Opción B. Si alguna vez se reabre, debe corregirse antes de usarse. |
