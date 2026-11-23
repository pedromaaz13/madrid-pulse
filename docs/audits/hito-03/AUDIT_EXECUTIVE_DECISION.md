# AUDIT_EXECUTIVE_DECISION — Decisión de la auditoría adversarial del Hito 3

**Elabora:** AUD-09, Claude Opus · High (`ctx_d10350eb24d0`) · **Revisa:** Codex `gpt-5.6-sol` · High, contexto nuevo (pendiente) · **Fecha:** 2026-11-23
**Código auditado:** `mp-022-validacion-integrada@beb9434` (cadena MP-016→MP-022, solo en local). **Fuentes:** los ocho documentos AUD-00…AUD-08, `INCIDENT_5433.md`, `INTEGRATION_PROPOSAL.md` y las medidas propias de AUD-09. Registro detallado: `FINDINGS_REGISTER.md` (`FR-xx`). Roadmap: `NEXT_STEPS_PROPOSAL.md`. Despachos: `ORCA_DISPATCH_AND_REVIEW_LOG.md`.

> **Decisión provisional, pendiente de aceptación del propietario:**
> **Despliegue público: NO-GO.**
> **Uso local, demostración supervisada e integración en `main` como «hito local cerrado, no apto para publicación»: CONDITIONAL GO** (condiciones en §7.3).
> Nada de este documento acepta ADR, autoriza el Hito 4, ni ejecuta push, PR o merge.

---

## 1. Hallazgos demostrados

Severidad según la escala del encargo (§8): P0 = veracidad, integridad ferroviaria, seguridad o funcionalidad esencial; P1 = limita significativamente experiencia, cobertura o fiabilidad; P2 = mejora. **«Pub.»** = bloquea un despliegue público (Sí / Cond. / No), eje independiente de la severidad.

### P0 (2)

| FR | Hallazgo | Evidencia decisiva | Pub. |
|---|---|---|---|
| **FR-01** | **El mapa pone en marcha trenes que el operador declara detenidos o que no han salido.** En el corte real `1533`, **28 de 44** circulaciones con corredor están `STOPPED_AT` y **las 28** reciben avance (31–108 km/h; 1,6–5,4 km en el horizonte), 25 con GPS idéntico en dos cortes separados 77 s: 17 antes de su salida (hasta 38,65 min y 5,7 km de avance falso), 4 en origen con la salida ya vencida, 7 en paradas intermedias. Al llegar el ancla siguiente el símbolo salta p50 1 237 m (máx. 3 274 m). | `aud01_envelope_predeparture.py`, `aud01_snap.py` (AUD-01, 3 rondas de Sol High); `aud09_stop_crossing.py` (AUD-09, **pendiente de validar por el revisor**) | **Sí** |
| **FR-02** | **En replay, `/api/v1/snapshot?at=` oculta datos reales:** un feed con 468 entidades se publica `unknown` con edades **−71 s** cuando el instante pedido es anterior a una ingesta ya guardada. | 3 `curl` reproducidos 4 veces por 3 agentes (AUD-05) | Cond. (sí si se publica replay o `?at=`) |

### P1 (16) — los que más pesan

- **Modelo de paradas (sistema S1, misma causa raíz que FR-01):** la espera programada solo se respeta en una ventana de ~1 m (**FR-03**, antes `AUD04-P0-001`, reclasificado P1 en §2 del registro); el horizonte de 190 s efectivos hace que **30/44** envolventes atraviesen al menos una estación sin detenerse (**FR-04**); al caducar, el símbolo retrocede p50 2 358 m y el aviso desaparece (**FR-05**).
- **Procedencia:** el mapa no distingue GPS de proyección y rotula la proyección como «coordenada publicada por la fuente» (**FR-06**); el snapshot puede publicar una `revision` sin el vehículo que la generó (**FR-07**).
- **Cobertura:** **38,45 %** de las circulaciones con corredor; 8 de 12 líneas sin trazado (**FR-08**, antes `AUD01-P0-002`, reclasificado P1: el fallback GPS es honesto, el defecto es de cobertura); métricas de cierre tautológicas o inyectadas (**FR-09**, **FR-10**).
- **Publicación:** README que niega el producto (**FR-11**); teselas OSMF sin registrar (**FR-12**); capacidad pública no medida (**FR-13**); puertas de aceptación no falsables (**FR-14**); 24/7 no demostrado (**FR-15**); dependencia de Renfe (**FR-16**, riesgo aceptado); **defaults de PostgreSQL a la base compartida** (**FR-17**); licencia y visibilidad sin decidir (**FR-18**).

### P2 (24)

Detallados en `FINDINGS_REGISTER.md` §5. Cuatro bloquean publicar aunque sean P2: **catálogo GTFS que vence el 2026-12-19 sin refresco** (FR-19), **sin autenticación ni límite de tasa** (FR-38), rótulos «GPS observado» sobre un sello de lote (FR-29, Cond.) y `CANCELED` dibujado como en marcha (FR-32, Cond.).

---

## 2. Recomendaciones de corrección y riesgos

| Orden | Qué arreglar | Por qué primero | Riesgo de la corrección |
|---|---|---|---|
| 1 | **Modelo de estado de parada** (FR-01, FR-03, FR-04, FR-05): estado del operador (`current_status`/`current_stop_id`) + ventana del viaje, espera por `stop_id`, horizonte por tramo. Enmienda de ADR-0014 aprobada **antes** del código. | Es el único P0 que afecta al directo y la promesa central del producto («se mueve por donde y cuando se movió el tren»). Una sola corrección de diseño cierra P0 y tres P1. | Más trenes quietos en el mapa (es lo correcto); calibración pendiente de datos en vivo. No sustituir por subir la tolerancia (no basta, contrafactual B de AUD-04) ni por las dos correcciones que proponía AUD-01 por sí solas (acotar `temporal_offset_s` o comprobar la ventana antes de la primera salida): dejan fuera las 4 salidas retrasadas y las 7 paradas intermedias, 11 de 28. |
| 2 | **Replay `?at=`** (FR-02), **snapshot consistente** (FR-07), **vigencia GTFS** (FR-19). | P0 y bloqueante con fecha. Cambios acotados en `apps/api`. | La lectura transaccional puede subir la latencia: medir. |
| 3 | **Defaults de PostgreSQL** (FR-17) — tarea propia por decisión del propietario. | Ya causó una escritura real; precondición para cualquier captura en vivo o soak. | Romper scripts de `infra/operate/`. |
| 4 | **Portada, legal y puertas con número** (FR-11, FR-12, FR-14). | Horas de trabajo; sin ellas no se puede publicar ni evitar que el H4 cierre como el H3. | Coste del proveedor de teselas (gate). |
| 5 | **Rótulos y símbolos veraces** (FR-06, FR-29, FR-32). | Lo que el usuario cree que ve. | Revisor sin navegador: exigir capturas como artefactos. |
| 6 | **Cobertura geométrica por lotes** (FR-08): primero coste cero (C4b + 3 caveats → 43,35 %), luego C1, C10, C2, C3, C7, C8a, C8b, C9. | Mayor esfuerzo; P1, no P0, porque hoy no fabrica nada. | Cuota/502 de Overpass, ODbL, vía contigua en C4b invertida. |
| 7 | **Medir antes de decidir:** captura en vivo ≥ 2 h y ≥ 3 días; carga real con ASGI; ≥ 24 h de operación. | Sin ellas, horizonte, pool (DEC-038), retención (DEC-004) y capacidad son conjeturas. | Coste de host (gate). |

**Riesgo transversal:** las 283 + 89 pruebas pasan con los dos P0 presentes (AUD-08). Toda prueba de cierre del H4 debe **fallar contra `beb9434`** antes de contar.

---

## 3. Cobertura ferroviaria real y problemas de estaciones y trazados

**Lo que está bien (verificado):** 12 líneas, 42 `route_id`, 103 patrones y 95 estaciones son correctos como identidad de fuente, con igualdad estructural completa entre reconstrucción independiente y `Catalog` (AUD-02). Las 7 fixtures OSM son reales (SHA-256 7/7, 0 huecos). En los 28 patrones validados el tren se proyecta sobre su vía (p50 2,6 m, p95 20,8 m) y las estaciones caen a ≤ 150 m del eje (≤ 48,3 m en los casos C4b medidos). Ningún patrón sin corredor se proyecta sobre un corredor ajeno.

**Cobertura real, con denominadores:**

| Medida | Con corredor validado | Denominador |
|---|---|---|
| Patrones | 28 (27,2 %) + 3 `partial` | 103 |
| Circulaciones de red | **13 878 (38,45 %)** | 36 097 |
| Llamadas a estación | 242 129 (45,0 %) | 537 899 |
| Estaciones tocadas | 39 (41,1 %) | 95 |
| Líneas con algún corredor | 4 de 12 | 12 |
| Trenes del corte que pueden moverse | 44 de 121 (36,4 %) | 121 |
| Cobertura de posicionamiento (observados/programados en curso) | 65/73 = 89,0 % (C1 50 %, C10 60 %; un solo sondeo) | — |
| Longitud ferroviaria única | **NO VERIFICADO** (no hay grafo deduplicado) | — |

**Problemas de trazado y estaciones:**
- 72 patrones `pending` **nunca se sometieron a prueba geométrica** (ninguna fuente admitida por su `route_id`): 67 por falta de fuente, 4 C4b con su vía ya congelada en sentido opuesto, 1 por feed truncado. El CSV canónico les da a los 72 el mismo motivo.
- Tres `PatternCaveat` rebajan patrones que pasan todas las pruebas (31 viajes): confunden «no para» con «no pasa por esa vía».
- El GTFS de Renfe viene truncado en C8b (121 trips huérfanos, `stop_sequence` 025/032) y **no publica andenes ni `parent_station`**: la distinción estación/andén/acceso no es decidible con esta fuente (NV-07). El hueco de 5,38 m de `19656` es entre la proyección de la estación y la del tren, no ruido GPS.
- Servicios > 48 h se asignarían mal (latente) y `route_color` oficial no se usa.

---

## 4. Defectos visuales y funcionales

**Funcionales (por superficie):**
- **Live / mapa:** FR-01 (trenes detenidos en marcha), FR-03/04 (atraviesa estaciones), FR-05 (retroceso y aviso que desaparece), FR-27 (dos coordenadas del mismo tren hasta 429,5 m aparte), FR-26 (DST latente, 2027-03-28 y 2027-10-31).
- **Replay / `?at=`:** FR-02.
- **API:** FR-07 (revisión inconsistente), FR-38 (sin autenticación ni tasa), FR-19 (catálogo caduca en silencio).
- **History / Explore:** sin defecto de denominador en la interfaz (AUD-05, capturas 08–10); el umbral de puntualidad de 300 s no se muestra (FR-36).
- **Operación:** FR-17 (defaults), FR-22 (exportación concurrente no atómica, el reproceso converge).

**Visuales y de procedencia:**
- `raw` y `map_matched` idénticos en forma, glifo y texto; texto falso para la proyección (FR-06). Los 75–78 puntos sin trazado validado llevan el símbolo más autoritativo.
- `stale_frozen` e `interpolated` comparten forma `ring` (FR-28); «GPS observado» y «última lectura confirmada» sobre datos que no lo son (FR-29); `CANCELED` sin distinción (FR-32); paleta por hash en lugar del color oficial (FR-35).
- AUD-05 v2 (navegador real, artefacto por afirmación): sin P1 visuales; cuatro P2: en la vista inicial **25 grupos de trenes comparten la misma coordenada** (el mayor, 6 C5 estacionados en el origen `35607`, son trenes `STOPPED_AT` que FR-01 pone en marcha juntos) (FR-39); buscador sin `id`/`name` (FR-40); «Seguir tren» sin WebGL activa un modo y un aviso imposibles de cumplir (FR-41, la v1 lo describía mal); la leyenda tapa la lista de novedades (FR-42). Verificado correcto con artefacto: movimiento reducido (1 repintado/4 s frente a 229), fallback sin WebGL navegable, búsqueda sin tildes, móvil 390×844, distinción «parada omitida» frente a «solo horario». No verificado: lector de pantalla real.

---

## 5. Estado de la base 5433 y resolución

- **Qué pasó:** AUD-06 (`ctx_cf7d40a866d7`) ejecutó el colector sin la variable que aísla la base y escribió en `madrid-pulse-postgres-1` (127.0.0.1:5433), la base de desarrollo **persistente y compartida**: 6 `source_ingestion_run` (3090–3095), 227 posiciones, 162 actualizaciones, 5 alertas y 8 `data_quality_event`, entre 17:04:46Z y 17:05:18Z. El propio worker lo detuvo y escaló.
- **Naturaleza:** **solo aditiva** (`n_tup_upd = 0`; las filas previas siguen en `668/484/3/120/0`); ninguna fila nueva es referenciada por otra; no hubo escrituras posteriores (`max(id) = 3095`). Dump completo previo fuera del repositorio (SHA-256 `e319e8e4…727d7`).
- **Causa raíz de diseño:** `services/collector/config.py:34` y `apps/api/config.py:34-35` apuntan por defecto a 5433, sin guarda; además API y colector usan variables distintas. Es un defecto de producto (FR-17), no solo un error del worker.
- **Incumplimiento:** sí, de la restricción «no modificar base de datos persistente»; accidental, no destructivo y divulgado. El primer informe de AUD-06 lo negaba; corregido (`2d02227`).
- **Resolución — decisión del propietario (2026-11-24): CONSERVAR.** No se autoriza `DELETE`, `TRUNCATE` ni restauración; la Opción B queda descartada. La nueva línea base de 5433 es `895/646/8/126/8`.
- **Efecto de reproducibilidad (permanente):** la verificación histórica «suite sin skips contra desarrollo» **ya no se reproduce** contra 5433 (`test_real_soak_postgres` exige 668). Toda prueba reproducible debe usar PostgreSQL desechable con migraciones desde cero. Skips esperados: **5** con `data/` y base aislada, **1** con DSN de API y URL de colector divergentes (no representativo), **18** en checkout limpio (lo que vería CI).
- **Prevención:** tarea H4-11 (sin defaults, fallo seguro, una sola variable, aislamiento de tests, guarda de escritura). Planificada, no implementada.

---

## 6. Roadmap H4 revisado (provisional)

Detalle, dependencias, pruebas de cierre, ADR/DEC y gates en `NEXT_STEPS_PROPOSAL.md`. Modelos solo de la lista verificada (Claude `opus`/`sonnet`; Codex `gpt-5.6-sol`/`terra`/`luna`) más la excepción del propietario para H4-11.

| ID | Bloque | Prioridad · esfuerzo | Ejecutor (modelo · esfuerzo) | Revisor independiente (modelo · esfuerzo) | Cierra |
|---|---|---|---|---|---|
| H4-00 | A | **P0 · M** | Claude `opus` · high | Codex `gpt-5.6-sol` · high | Enmienda ADR-0014 (estado de parada, horizonte, §2, §3/§4, §5) — **gate: aprobación del propietario antes de H4-04** |
| H4-04 | A | **P0 · L** | Codex `gpt-5.6-sol` · high | Claude `opus` · high | FR-01, FR-03, FR-04, FR-05, FR-26, FR-27, FR-31 |
| H4-01 | A | **P0 · M** | Codex `gpt-5.6-sol` · high | Claude `sonnet` · high | FR-02, FR-07, FR-19 |
| H4-10 | A | P1 · S | Claude `sonnet` · medium | Codex `gpt-5.6-terra` · medium | FR-11, FR-12, FR-14, FR-37 — gates: teselas, DEC-002/003 |
| H4-11 | A | P1 · S | Codex `gpt-6.2-sol` · medium (*excepción del propietario; sin recibo de Orca aún*) | Claude `sonnet` · high | FR-17 |
| H4-03 | B | P1 · L | Codex `gpt-5.6-sol` · high | Claude `opus` · high | FR-08, FR-23, FR-24, FR-25, FR-34 — gates: descargas OSM, C4b invertida |
| H4-12 | B | P1 · M | Codex `gpt-5.6-terra` · high | Claude `sonnet` · high | NV-02; hipótesis H1–H4 de AUD-01; calibración de H4-04 |
| H4-05 | C | P1 · M | Claude `sonnet` · high | Codex `gpt-5.6-terra` · high | FR-06, FR-28, FR-29, FR-32, FR-35, FR-39–42 |
| H4-06 | C | P1 · S | Claude `sonnet` · medium | Codex `gpt-5.6-terra` · high | FR-09, FR-10, FR-36 |
| H4-07 | D | P1 · M | Codex `gpt-5.6-terra` · high | Claude `sonnet` · high | FR-15, FR-22, FR-30 — gate: host persistente |
| H4-08 | D | P1 · M | Codex `gpt-5.6-terra` · high | Claude `sonnet` · high | FR-13, FR-38; insumo de DEC-038/DEC-004 — gates: DEC, coste |
| H4-09 | gate | P0 (gate) · M | Codex `gpt-5.6-sol` · high | Claude `opus` · high | Re-evaluación de cada `FR` en el nuevo HEAD; decisión de publicar |
| ~~H4-02~~ | — | **descartado** | — | — | Hipótesis refutada por AUD-02/AUD-03; residuo absorbido como P2 |
| E | — | fuera del H4 | — | — | AVE, Larga/Media Distancia y otros núcleos tras H4-03 y H4-04 |

---

## 7. Decisión de preparación para el lanzamiento

### 7.1 Despliegue público: **NO-GO**

Justificación con evidencia concreta, no con impresión general:

1. **Veracidad en directo (P0):** FR-01 — el mapa mueve el 64 % (28/44) de los trenes con trazado mientras el operador los declara detenidos. La promesa del producto (ver dónde está el tren) se incumple justo en los trenes que se pueden animar.
2. **Veracidad en replay (P0, condicional):** FR-02.
3. **Bloqueantes no técnicos con coste casi nulo, sin resolver:** README que niega el producto (FR-11), teselas OSMF sin registrar (FR-12), licencia y visibilidad sin decidir (FR-18), catálogo que caduca el 2026-12-19 (FR-19).
4. **Capacidad y operación no demostradas:** sin prueba de carga con red (FR-13), sin autenticación ni tasa (FR-38), sin 24 h de operación (FR-15).
5. **Cobertura inferior a la afirmación de misión** («mapa de toda Cercanías Madrid», `PROMPT-UNICO-ORCA.md:11`): 38,45 % de circulaciones con trazado, 8 de 12 líneas sin él (FR-08). Publicable **solo** si la afirmación cambia y la cobertura se muestra por línea.

**Condición para reconsiderarlo (H4-09):** FR-01, FR-02, FR-11, FR-12, FR-17, FR-18, FR-19 y FR-38 cerrados con prueba que fallaba antes; FR-13 medido; FR-15 con ≥ 24 h; FR-06 resuelto; afirmación pública alineada con la cobertura real.

### 7.2 Qué está demostrado que funciona (para uso local y demo)

- Ingesta GTFS-RT con dedupe por hash que no rejuvenece la edad del dato; recuperación del colector ante pérdida de PostgreSQL (código 75, backoff 5 s, ciclos posteriores completos).
- Catálogo GTFS correcto como identidad de fuente; geometría real y verificable de C4/C5; proyección fiel en el espacio para los 28 patrones validados; GPS bruto nunca alterado (0/931); ningún patrón proyectado sobre una vía ajena.
- Separación contractual `raw`/`map_matched`/`rendered` y seis métodos de presentación; el cliente no decide el avance.
- Archivo frío idempotente con cuarentena y recuperación (ADR-0015); histórico con huecos como filas y `404` en vez de ceros.
- Interfaz navegable: fichas coherentes con la circulación, History/Explore con numerador y denominador reales, movimiento reducido, fallback sin WebGL, móvil.
- CI: 283 casos Python (265 ejecutados en checkout limpio) y 89/89 frontend, lint, typecheck y build.

### 7.3 Uso local, demo e integración en `main`: **CONDITIONAL GO**

Condiciones: (a) etiquetar el hito como «local cerrado, no apto para publicación» (coincide con `INTEGRATION_PROPOSAL.md` §4.1); (b) en cualquier demo, no presentar el movimiento como fiel en el tiempo ni la cobertura como «toda la red», y evitar `?at=` anterior a la última ingesta; (c) ADR-0014 y ADR-0015 siguen `Propuesto`; (d) usar PostgreSQL desechable para cualquier ejecución reproducible; (e) push, PR y merge los hace el propietario.

**Sobre `INTEGRATION_PROPOSAL.md`** (revisado; documento del coordinador sin revisión independiente): sus HEAD coinciden con `BASELINE.md` (aprobado); la Opción 1 (un PR `mp-022` → `main`, *fast-forward* posible) es razonable. **Una objeción:** recomienda no fusionar `scratch/`, pero los informes de auditoría citan `scratch/aud0*_*.py` como sus comandos reproducibles; integrar los documentos sin los guiones deja la evidencia sin forma de reproducirse. Alternativas: integrar la rama de auditoría completa como tal, moverla junto con los guiones a `docs/audits/hito-03/scripts/` **actualizando las rutas citadas**, o conservarla como rama/etiqueta de archivo fuera de `main`.

### 7.4 Qué funciona con limitaciones

Movimiento (fiel en el espacio, no en el tiempo; solo 44/121 trenes); cobertura (honesta pero del 38 %); métricas (reales en la UI, tautológicas en la matriz de cierre); operación (supervisada local, no 24/7); replay (correcto salvo `?at=` anterior a la ingesta); interfaz (sólida, con procedencia ambigua para GPS frente a proyección).

### 7.5 Qué es incorrecto o puede inducir a error

FR-01 (trenes detenidos en marcha), FR-02 (datos presentes rotulados como ausentes, edades negativas), FR-05 (retroceso sin aviso), FR-06 (proyección rotulada como dato de la fuente), FR-09/FR-10 (cifras de cierre que no miden lo que dicen), FR-11 (README), FR-29 («GPS observado» sobre un sello de lote) y, como afirmación, «mapa de toda Cercanías Madrid».

### 7.6 Qué no se ha podido comprobar (limitaciones de reproducibilidad)

- **24/7:** no verificado (máximo medido: 823,2 s / 21 ciclos).
- **Feed en vivo ≥ 2 h:** no realizado; todo el movimiento se midió sobre **dos cortes de un día separados 77 s**, no sobre la cadencia real de ~20 s. Las frecuencias de FR-01/03/04/05 en el uso real están sin medir.
- **Usuarios:** n = 0 en tres hitos (H5, H6, H8 abiertas).
- **Geometría:** 28/103; longitud ferroviaria única sin verificar; relaciones OSM de 8 líneas sin consultar.
- **Capacidad:** solo `TestClient` en proceso.
- **Skips por entorno:** 5 / 1 / 18; la cifra de CI real es 18.
- **Base 5433 alterada** (conservada por decisión del propietario): la verificación «sin skips contra desarrollo» ya no se reproduce.
- **AUD-05 (APPROVED en v2):** la v1 contenía afirmaciones de ejecución en navegador sin artefacto (una de ellas, P2-3, incorrecta); la v2 (`39b3e06`, `28f696e`) las retira o las respalda. **Limitación de su revisión:** el revisor de Codex no tiene navegador; no repitió las sesiones de DevTools ni verificó de forma independiente coordenadas y zooms de las capturas 18/19 (revisó capturas, JSON y transcripciones). Lector de pantalla real, arrastre/seguimiento en vivo y «Ampliar panel» siguen sin verificar.
- **Medida nueva de AUD-09** (`aud09_stop_crossing.py`): un solo corte; GPS idéntico puede ser un fijo repetido (corroborado por `STOPPED_AT`, no probado físicamente). Pendiente de validación del revisor.

### 7.7 Qué propuestas anteriores conviene descartar

Criterios que pre-autorizan incompletitud y puertas sin número; conteos de fixture como criterio de producto; `non_traversable` para el C8b truncado; subir la tolerancia de espera o acotar solo el offset como corrección única; mover la decisión de espera al cliente; clustering de marcadores; llamar «24/7» a una ráfaga; el CDN como «futuro» sin medir; la limpieza de 5433 (descartada por el propietario); H4-02 como tarea independiente. Detalle en `NEXT_STEPS_PROPOSAL.md` §7.

### 7.8 ADR y DEC (sin aceptar nada en nombre del propietario)

| Decisión | Recomendación basada en evidencia | Detalle |
|---|---|---|
| ADR-0014 | **Mantener `Propuesto`**: la arquitectura (envolvente en backend) no está refutada; su regla de estado de parada (FR-01) y la redacción de §2 (FR-31) y §5 (FR-07) sí. Aceptar tras H4-00 + H4-04. | `NEXT_STEPS_PROPOSAL.md` §6 |
| ADR-0015 | **Evidencia suficiente para aceptarlo con una nota** sobre la no atomicidad multi-tabla de la primera exportación (FR-22). | ídem |
| DEC-033 | **Mantener pendiente** (b) y (c); mostrar el umbral si se publica la métrica. | ídem |
| DEC-038 | **Mantener pendiente; la evidencia favorece el pool**, pero decidir con la prueba de carga real. | ídem |
| DEC-004 | **Mantener pendiente** hasta ≥ 24 h medidas; ≈7 GB/año es una proyección de 13 min. | ídem |

---

*Aceptación pendiente del propietario. Ningún agente ha aceptado ADR, autorizado el Hito 4, modificado código de producto o datos, ni ejecutado push, PR o merge.*
