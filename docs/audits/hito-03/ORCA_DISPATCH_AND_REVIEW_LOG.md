# Registro de despachos y revisiones — Auditoría adversarial Hito 3

Mantenido en vivo por el coordinador (Claude Sonnet) a medida que cada `AUD-ID` reporta. AUD-09 puede partir de este registro en vez de reconstruirlo desde cero.

**Run:** `run_3b3bfaf88f3d` · **Worktree:** `/Users/matu/orca/workspaces/madrid-pulse/audit-hito-03` (rama `audit/hito-03-adversarial`, base `mp-022-validacion-integrada@beb9434`)

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
| AUD-03 | Revisor | Claude `opus` · high | `ctx_4db56fd6dd34` | `task_5f1319cdd3c0` | — | *(pausado — límite de sesión Claude, reset 21:10 CET)* |
| AUD-06 | Ejecutor | Codex `gpt-5.6-terra` · high | `ctx_cf7d40a866d7` | `task_7982bf79c176` | *(en curso)* | *(en curso)* |
| AUD-07 | Ejecutor | Claude `sonnet` · medium | `ctx_7f0fde0b7e4f` | `task_a9deb9865cbc` | `44c98cb`, `ea49e6a` | **completado** — revisión independiente real de Codex (`ctx_db3c9aa62ac8`, settled/succeeded) incorporada: 2 P1→P2, 2 P1 confirmados, 1 hallazgo descartado |
| AUD-01 | — | Claude `opus` · high (pendiente de despachar) | — | `task_8bf54c0799dd` | — | en cola |
| AUD-04 | — | Claude `opus` · high (pendiente de despachar) | — | `task_e6d1bf8a933e` | — | en cola |
| AUD-06 | — | Codex `gpt-5.6-terra` · high (pendiente de despachar) | — | `task_7982bf79c176` | — | en cola |
| AUD-08 | — | Codex `gpt-5.6-terra` · high (pendiente, depende de AUD-02/03/04/05/06) | — | `task_e0212d2fd3fe` | — | pendiente de dependencias |
| AUD-09 | — | Claude `opus` · high (pendiente, depende de todo) | — | `task_2e01f9d87b46` | — | pendiente de dependencias |

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

- **AUD-03** (75 patrones sin corredor validado, pendiente revisión): 67 sin fuente congelada; **4 patrones C4b que la relación OSM real `9174512` SÍ validaría** (refuerza directamente P0-002 de AUD-01: esa geometría existe y no se usó); 3 falsos negativos por caveats manuales incorrectos; 1 patrón degenerado de una sola parada. 19/19 tests focales.

*(Esta tabla se actualizará según reporten AUD-04, AUD-06 y el resto.)*
