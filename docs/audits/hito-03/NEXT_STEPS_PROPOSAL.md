# NEXT_STEPS_PROPOSAL — Hito 4 PROVISIONAL ajustado a la evidencia

**Elabora:** AUD-09, Claude Opus · High · **Revisa:** Codex `gpt-5.6-sol` · High (pendiente) · **Fecha:** 2026-11-23

> **Esto es planificación, no autorización.** Nada de este documento autoriza implementar, abrir worktrees de implementación, desplegar, contratar, aceptar ADR, hacer push, PR ni merge. Las numeraciones `H4-*` son temporales; solo el propietario autorizará una serie `MP-023+`. No se promete que ningún candidato se implemente.

Fuente de cada `FR-xx`: `FINDINGS_REGISTER.md`. Fuente del backlog de hipótesis `H4-00`…`H4-09`: encargo de la auditoría, §9 bis.

---

## 1. Qué cambia respecto al backlog de hipótesis del encargo

| Candidato del encargo | Decisión | Por qué (evidencia) |
|---|---|---|
| H4-00 Arquitectura/ADR | **Se mantiene, P0, acotado** a una enmienda de ADR-0014 (modelo de estado de parada, horizonte, §2, §3, §5) y a la decisión sobre el modelo de segmentos OSM. | S1 (FR-01/03/04/05/31) es un defecto de diseño del contrato temporal, no de implementación aislada; AUD-04 y AUD-01 coinciden en que se corrige en la traducción de MP-019, pero ADR-0014 §2 hoy describe una fórmula falsa (FR-31) y §5 promete una revisión que el código no garantiza (FR-07). |
| H4-01 Bugs P0 y regresiones | **Se mantiene, se divide.** La parte de movimiento pasa a H4-04; H4-01 queda para FR-02 (replay `unknown`), FR-07 (snapshot consistente) y FR-19 (vigencia GTFS). | Separar «especificación de Claude» y «código» sin mezclar ejecutor/revisor, como pide el encargo. |
| H4-02 GTFS y estaciones | **Se descarta como tarea independiente; el residuo pasa a P2 dentro de H4-03 y H4-05.** | **Hipótesis refutada:** AUD-02 reconstruye 12/42/103/95 con igualdad estructural completa con `Catalog` (0 discrepancias, 0 duplicados); AUD-03 encuentra las paradas a ≤ 48,3 m de los corredores validados. Queda: 121 huérfanos/feed truncado (FR-23), servicios > 48 h (FR-24), `route_color` (FR-35). La confusión estación/andén **no es decidible** con este GTFS (sin `parent_station`, NV-07). |
| H4-03 Corredores y ramales | **Se mantiene, P1, el mayor en esfuerzo.** | FR-08: 38,45 % de circulaciones con corredor; 67 patrones accionables; 4 C4b + 3 caveats a coste cero de descarga. |
| H4-04 Movimiento y contratos temporales | **Se eleva a P0** (contiene FR-01). | S1-a: 28/44 circulaciones `STOPPED_AT` puestas en marcha. |
| H4-05 Frontend y experiencia premium | **Se mantiene, P1, reorientado a veracidad de rótulos y símbolos**, no a estética. | AUD-05 no encontró defectos visuales graves (P2); los P1 de interfaz son de **procedencia**: FR-06, rótulos FR-29, `CANCELED` FR-32, aviso de FR-05. |
| H4-06 History/Explore y métricas | **Se reduce, P1, a métricas de cierre honestas.** | **Hipótesis parcialmente refutada:** AUD-05 verificó numerador/denominador reales en History/Explore (capturas 08–10). Lo que sí está mal son las métricas de la **matriz de cierre** (FR-09 tautológica, FR-10 constante) y el umbral de puntualidad invisible (FR-36). |
| H4-07 Operación supervisada local | **Se mantiene, P1**, y se le separa la tarea de defaults (H4-11, decisión del propietario). | FR-15, FR-22, NV-01. |
| H4-08 Rendimiento y coste | **Se mantiene, P1 para publicar.** | FR-13; H7a/H7b sin medir. |
| H4-09 Release-readiness | **Se mantiene como gate final.** | Sin él, no hay base para un GO público. |
| — | **Nuevo H4-10:** documentación de portada, legal y puertas falsables (S). | FR-11, FR-12, FR-14: bloquean publicar y cuestan horas. |
| — | **Nuevo H4-11:** eliminar defaults peligrosos de PostgreSQL (decisión del propietario 2026-11-24). | FR-17, PR-01. |
| — | **Nuevo H4-12:** campaña de captura en vivo (≥ 2 h y ≥ 3 días). | NV-02: sin ella no se pueden calibrar horizonte/tolerancias ni refutar H1–H4 de AUD-01. |

## 2. Hipótesis refutadas o confirmadas por la auditoría

| Hipótesis | Resultado | Fuente |
|---|---|---|
| Los recuentos del cierre (12/42/103/95/28) son falsos. | **Refutada** (son correctos como identidad de fuente; la usabilidad es 40/102/121 huérfanos). | AUD-02 |
| Los 75 patrones no validados fallan por ausencia de geometría en OSM. | **Refutada.** 72 nunca se probaron; 4+3 pasan con lo ya congelado. | AUD-03 |
| El GPS original se altera en la cadena. | **Refutada** (0/931). | AUD-04 |
| El cliente fabrica posiciones. | **Refutada** para la autoridad de avance. | AUD-01 DESC-002 |
| La arquitectura está sobre-ingenierizada. | **Refutada.** | AUD-01 DESC-001; EGM |
| History/Explore muestran denominadores falsos. | **Refutada** en la UI; confirmada en la matriz de cierre (FR-09/10). | AUD-05, AUD-01 |
| El movimiento es ferroviariamente fiel en el espacio. | **Confirmada** para los 28 corredores (p50 2,6 m del trazado; arco, no recta). | AUD-04 |
| El movimiento es fiel en el tiempo. | **Refutada:** 28/44 detenidos puestos en marcha; mediana real 0,0 km/h frente a 6,8–30 m/s publicados. | AUD-01, AUD-04, AUD-09 |
| ≥ 30 % de envolventes atraviesan una estación sin detenerse (H4 de AUD-01). | **Apoyada en un solo corte** (30/44 = 68 %), pendiente de vivo. | AUD-09 |
| La batería verde (283 + 89) demuestra ausencia de defectos. | **Refutada:** pasa con los dos P0 presentes. | AUD-08 |
| 823 s / 21 ciclos demuestran operación 24/7. | **Refutada.** | AUD-06, AUD-08 |

## 3. Modelos verificados para asignar

Solo se asignan modelos con evidencia real en este entorno:

| Modelo (Orca `--model` / `--effort`) | Evidencia | Uso propuesto |
|---|---|---|
| Claude `opus` · high | recibos Orca `requested = effective` (AUD-01, AUD-03 rev., AUD-04, AUD-09) | arquitectura, especificación, revisión de geometría |
| Claude `sonnet` · high / medium | recibos Orca (AUD-02 rev., AUD-05, AUD-06 rev., AUD-08 rev. / AUD-07) | frontend, revisión crítica / documentación |
| Codex `gpt-5.6-sol` · high | recibos Orca (AUD-01 rev., AUD-02, AUD-03, AUD-04 rev.) | algoritmos de movimiento, geoespacial, P0 |
| Codex `gpt-5.6-terra` · high / medium | recibos Orca (AUD-05 rev., AUD-06, AUD-08; AUD-00 rev., AUD-07 rev.) | DB, colector, API, operación, regresiones |
| Codex `gpt-5.6-luna` | presente en `~/.codex/models_cache.json` (`visibility: list`, «Legacy»); **sin recibo de Orca en esta ejecución** | no se asigna ningún gate |
| Codex `gpt-6.2-sol` · medium | presente en `~/.codex/models_cache.json` (`visibility: list`, «Fast, go-to model for coding and everyday work», niveles low…ultra) y default de `~/.codex/config.toml`; **sin recibo de Orca todavía**. Familia `gpt-6.*` excluida por el encargo original; **excepción explícita del propietario solo para H4-11** | solo H4-11; verificar `effective.model` en el recibo al despachar y, si no coincide, parar |

Los tres `gpt-5.6-*` están etiquetados «Legacy» por el proveedor (`BASELINE.md` §2); se usan porque son la selección expresa del propietario.

## 4. Candidatos H4 (provisionales)

Leyenda de esfuerzo relativo: **S** ≈ una tarea MP corta (≤ 1 día de agente); **M** ≈ 2–4 días; **L** > 1 semana o varios lotes.

### Bloque A — Correcciones imprescindibles antes de publicar o promocionar

#### H4-00 · Enmienda de ADR-0014: modelo de estado de parada — **P0 · M**
- **Problema real:** S1 (FR-01 P0, FR-03, FR-04, FR-05 P1, FR-31, FR-33 P2) + FR-07 contra ADR-0014 §5 + FR-06 contra §3/§4.
- **Trabajo:** ADR propuesto (enmienda de ADR-0014 o ADR-0016) que fije: (1) estado de parada derivado de `current_status`/`current_stop_id` del operador y de la ventana del viaje (pre-salida, salida retrasada, en ruta, post-llegada); (2) espera por `stop_id` en vez de por progreso ±1 m; (3) horizonte por tramo (hasta la próxima parada) o espera mínima por parada, con calibración por H4-12; (4) fórmula §2 corregida con `dwell_until`; (5) `anchor` separado por `coordinate_space`; (6) lectura consistente para `revision` (§5). Alternativas comparadas: (A) estado de parada del operador [recomendada], (B) acotar `temporal_offset_s` [insuficiente: no cubre salidas retrasadas ni paradas intermedias], (C) subir tolerancia [insuficiente, contrafactual B de AUD-04].
- **Fuentes:** `PRODUCT_AUDIT.md` P0-001/P1-005; `POSITION_MOVEMENT_AUDIT.md` P0-001/P1-001/P1-002/P2-006; `FINDINGS_REGISTER.md` §2.
- **Ejecutor:** Claude `opus` · high · **Revisor:** Codex `gpt-5.6-sol` · high.
- **Dependencias:** ninguna (primero del hito). Debe leer los arneses `scratch/aud01_*`, `aud04_*`, `aud09_*`.
- **Coste/riesgo:** bajo coste; riesgo de sobre-especificar sin datos en vivo → las constantes quedan como parámetros a calibrar en H4-12, no como valores.
- **Prueba de cierre:** ADR con las tres alternativas, criterios de aceptación numéricos (los de H4-04) y el revisor confirmando que cada `FR` S1 tiene una regla que lo cubre.
- **ADR/DEC afectados:** ADR-0014 (enmienda), DEC-010 (horizonte), ADR-0012 (frontera del paquete, sin cambio esperado).
- **Gate humano:** **aprobación del propietario del ADR antes de cualquier código de H4-04.**

#### H4-04 · Implementación del modelo de estado de parada — **P0 · L**
- **Problema real:** FR-01 (P0), FR-03, FR-04, FR-05 (P1), FR-26, FR-27, FR-28, FR-31 (P2).
- **Trabajo:** implementar H4-00 en `packages/movement/rendering.py`/`schedule.py` y su consumo en `apps/api/snapshot.py` y `apps/web/src/domain/movement.ts`; DST en `_envelope` (FR-26); coordenada única por instante (FR-27).
- **Ejecutor:** Codex `gpt-5.6-sol` · high · **Revisor:** Claude `opus` · high (autor de la especificación; proveedor contrario). *Cambio respecto al encargo* (que proponía Opus ejecutor): el encargo reserva Sol High para «algoritmos de movimiento» y pide separar especificación (Claude) de código; así nadie revisa su propio código.
- **Dependencias:** H4-00 aprobado. H4-12 para calibrar constantes (puede ir en paralelo; las pruebas de cierre de vivo esperan a H4-12).
- **Coste/riesgo:** alto riesgo de regresión en la sensación de movimiento (más trenes quietos); es el comportamiento correcto y debe comunicarse.
- **Pruebas de cierre (deben FALLAR contra `beb9434` y pasar después):**
  1. Corte `1533`: **0** de las circulaciones `STOPPED_AT` con GPS idéntico entre `1532` y `1533` publican `speed_mps > 0` (hoy 25/25).
  2. **0** circulaciones pre-salida con avance (hoy 17); las 4 salidas retrasadas en origen, sin avance mientras el operador las declare `STOPPED_AT`.
  3. Ninguna circulación `IN_TRANSIT_TO` que avanzó entre cortes pierde su avance (H2b de AUD-01).
  4. `19656` desde su GPS bruto real (`40.283237, -3.7991464`): espera retenida (0 m a los 30 s) mientras el operador lo sitúe en `35002` (prueba propuesta por AUD-04).
  5. Retroceso al expirar ≤ 1 m (hoy p50 2 357,9 m) y aviso de congelación visible después de `valid_until`.
  6. DST: 0 m fabricados en 2027-03-28 y sin congelación de una hora en 2027-10-31.
  7. En vivo (H4-12): salto al llegar el ancla siguiente p50 ≤ 200 m (H1 de AUD-01), ≥ 500 pares.
- **ADR/DEC:** ADR-0014 (tras enmienda), DEC-010.
- **Gate humano:** aceptación de la enmienda (H4-00); revisión del diff real en el nuevo HEAD.

#### H4-01 · Veracidad fuera del motor de movimiento — **P0 · M**
- **Problema real:** FR-02 (P0), FR-07 (P1), FR-19 (P2 que bloquea publicar).
- **Trabajo:** acotar ingestas por `started_at <= now` y separar edad negativa de «sin ingesta»; vista transaccional única o watermark en `build_snapshot`; comprobación de vigencia del GTFS periódica, no solo al arrancar, y refresco operativo.
- **Ejecutor:** Codex `gpt-5.6-sol` · high · **Revisor:** Claude `sonnet` · high.
- **Dependencias:** la parte `revision` de H4-00 (§5) para FR-07; FR-02 y FR-19 son independientes y pueden empezar ya.
- **Coste/riesgo:** bajo; FR-07 toca la lectura del snapshot (riesgo de latencia, medir con H4-08).
- **Pruebas de cierre:** regresión `?at=2026-11-20T14:32:10Z` tras ingerir ambos cortes → `status ≠ unknown`, edades ≥ 0 o `null` declarado; carrera reproducida por AUD-06 (commit en el hueco) → la respuesta contiene el vehículo de su `revision` o la `revision` anterior; reloj simulado en 2026-12-20 con proceso vivo → catálogo marcado caducado o refrescado.
- **ADR/DEC:** ADR-0014 §5.
- **Gate humano:** ninguno adicional al del hito.

#### H4-10 · Portada, legal y puertas falsables — **P1 · S** (nuevo)
- **Problema real:** FR-11 (README/ARCHITECTURE/DATA_MODEL), FR-12 (teselas OSMF sin registrar), FR-14 (puertas no falsables), FR-37 (deriva de gobernanza: ADR-0011, `PLAN.md` sin fase para H3/H4).
- **Trabajo:** actualizar portada; fila de servicio de teselas en `docs/legal/DATA_SOURCES.md` y `LICENSE_MATRIX.md` con su política; enmienda de ADR-0011; añadir a `PLAN.md` una fase H3/H4 con *exit gate* numérico; una tabla de aceptación con **un número y un comando por puerta** (`PRODUCT_AUDIT.md` §15).
- **Ejecutor:** Claude `sonnet` · medium · **Revisor:** Codex `gpt-5.6-terra` · medium.
- **Dependencias:** ninguna.
- **Coste/riesgo:** muy bajo coste; la elección de proveedor de teselas puede tener coste → gate.
- **Prueba de cierre:** `grep` de portada sin «no hay código de producto»; fila legal presente; cada puerta del H4 con umbral y comando.
- **ADR/DEC:** ADR-0011 (enmienda), DEC-002/DEC-003 (siguen del propietario).
- **Gate humano:** **proveedor/política de teselas; licencia de código (DEC-002) y visibilidad (DEC-003).**

#### H4-11 · Eliminar defaults peligrosos de PostgreSQL — **P1 · S** (decisión del propietario, 2026-11-24)
- **Problema real:** FR-17 y PR-01 (escritura real en 5433).
- **Trabajo:** `services/collector/config.py` y `apps/api/config.py` sin valor por defecto que apunte a `127.0.0.1:5433`; configuración explícita por entorno (`dev`/`test`/`replay`/`live`); **fallo seguro** (salida con error claro) si falta la configuración; **una sola variable** de conexión compartida por API, colector y snapshotter (hoy `MADRID_PULSE_DATABASE_DSN` frente a `MADRID_PULSE_DATABASE_URL`, causa probable de los skips divergentes); aislamiento de tests (las suites rechazan conectarse a una base que no sea la desechable declarada); guarda contra escrituras accidentales en la base de desarrollo compartida (p. ej. marca de entorno en la propia base comprobada antes de escribir).
- **Ejecutor:** Codex `gpt-6.2-sol` · medium (**excepción explícita del propietario a la exclusión de `gpt-6.*`, solo para esta tarea**; disponible en el catálogo local, **sin recibo de Orca todavía**: verificar `effective.model` al despachar) · **Revisor:** Claude `sonnet` · high (`claude-sonnet-5-5`).
- **Dependencias:** ninguna; conviene antes de H4-07 y H4-12.
- **Coste/riesgo:** bajo; riesgo de romper scripts de operación (`infra/operate/`) y la CI → la CI ya fija ambas variables (`AUD08_REPRODUCTION.md`).
- **Pruebas de cierre (reproducibles, contra PostgreSQL desechable, nunca 5433):** (1) arrancar colector y API **sin** variables → salen con error y **0** filas nuevas en cualquier base; (2) con una sola variable, API y colector escriben/leen la misma base; (3) un test de la suite apuntado a una base sin marca de «desechable» se niega a ejecutar; (4) la suite de CI sigue dando 283 casos con los mismos skips por entorno (5 con `data/`, 18 en checkout limpio); (5) búsqueda en el repositorio: ningún literal `5433` fuera de documentación e `infra/` de desarrollo.
- **ADR/DEC:** ninguno nuevo; documentar en `docs/` de operación.
- **Gate humano:** ninguno más allá de la autorización del hito; **no** toca los datos de 5433 (decisión CONSERVAR).

### Bloque B — Consolidación ferroviaria

#### H4-03 · Corredores, ramales y catálogo honesto — **P1 · L**
- **Problema real:** FR-08 (P1), FR-23, FR-24, FR-25, FR-34 (P2), NV-05, NV-06, NV-12.
- **Trabajo por lotes, en orden de circulaciones afectadas:**
  1. **Coste cero de descarga:** C4b opuesta (4 patrones, 1 740 circulaciones) aceptando arcos decrecientes sobre `9174511` **solo** si el contrato declara la incertidumbre lateral de vía; retirar las 3 caveats no sustentadas (31 viajes). Resultado esperado: 35/103 patrones, 15 649/36 097 circulaciones (43,35 %).
  2. Congelar `9174512` (C4b, sentido físico propio).
  3. Adquisición OSM por corredor físico: C1 (4 262), C10 (4 159), C2 (3 744), C3 (3 216), C7 (2 160), C8a (1 346), C8b (1 132), C9 (254), reutilizando tramos compartidos (`9174511`/`11332` ya cubren 17000↔18002 para 16/14 patrones).
  4. `reason` desagregado en el CSV canónico (sin fuente / intento fallido / feed truncado / caveat); evento de calidad `source_truncated`; publicar 40/102/121 junto a 42/103 (FR-23); retroceso de fechas de servicio por horizonte (FR-24); `route_id` fuera de `packages/geo/madrid.py` (FR-34).
- **Ejecutor:** Codex `gpt-5.6-sol` · high · **Revisor:** Claude `opus` · high.
- **Dependencias:** decisión de modelo de segmentos (en H4-00 o ADR propio) antes del lote 3; H4-04 se beneficia de cada lote, pero no lo bloquea.
- **Coste/riesgo:** llamadas a Overpass (cuota, 502 ya observados); obligación ODbL de atribución; riesgo de dibujar en la vía contigua (C4b invertida).
- **Pruebas de cierre:** por lote, fixture con manifiesto y SHA-256; 0 `ChainGap`; todas las paradas ≤ 150 m; orden monótono en el sentido del patrón; prueba de dirección; matriz regenerada con numerador por **circulaciones y llamadas**, no solo patrones; comparación antes/después.
- **ADR/DEC:** posible ADR de grafo de segmentos; ADR-0011 §3 (literales).
- **Gate humano:** autorización de descargas externas y de su atribución; aceptar o no la alternativa C4b invertida.

#### H4-12 · Campaña de captura en vivo — **P1 · M** (nuevo)
- **Problema real:** NV-02; calibración de horizonte y tolerancias de H4-00/H4-04; hipótesis H1, H2a, H3, H3b, H4 de AUD-01.
- **Trabajo:** captura ≥ 2 h continua y ≥ 10 sondeos por franja en ≥ 3 días (las seis franjas de H2a) contra PostgreSQL **desechable**, con la configuración de H4-11; ejecutar los guiones `aud01_*`, `aud04_*`, `aud09_*` sobre cada corte.
- **Ejecutor:** Codex `gpt-5.6-terra` · high · **Revisor:** Claude `sonnet` · high.
- **Dependencias:** H4-11 (para no repetir PR-01).
- **Coste/riesgo:** carga a los feeds públicos (cadencia ya medida), almacenamiento local pequeño.
- **Pruebas de cierre:** cada hipótesis de `PRODUCT_AUDIT.md` §10 con su umbral evaluado y el resultado (confirmada/refutada) registrado con comandos.
- **Gate humano:** autorizar captura continua en el host local.

### Bloque C — Madurez del producto

#### H4-05 · Interfaz: procedencia y rótulos veraces — **P1 · M**
- **Problema real:** FR-06 (P1), parte UI de FR-05, FR-28, FR-29, FR-32, FR-35, FR-39–42 (P2).
- **Trabajo:** símbolo y texto propios para `raw` frente a `map_matched`; forma distinta para `stale_frozen` frente a `interpolated`; rótulos sin «GPS observado» para un sello de lote; `CANCELED` visible; `route_color` oficial; correcciones menores de AUD-05 (buscador `id`/`name`, «Seguir tren» sin mapa, zoom inicial).
- **Ejecutor:** Claude `sonnet` · high · **Revisor:** Codex `gpt-5.6-terra` · high.
- **Dependencias:** contrato de H4-00 (§3/§4) para FR-06.
- **Coste/riesgo:** **el revisor de Codex no tiene navegador** (limitación repetida en MP-020/021/022 y en ambas revisiones de AUD-05): el ejecutor debe dejar capturas y transcripciones de DevTools como artefactos verificables, y toda afirmación de ejecución sin artefacto no cuenta (lección de la revisión formal de AUD-05).
- **Pruebas de cierre:** arnés vitest que extraiga `METHOD_STYLES` y exija forma única por método y por `coordinate_space`; capturas antes/después en escritorio y 390×844; escala de grises.
- **ADR/DEC:** ADR-0014 §3/§4.
- **Gate humano:** ninguno.

#### H4-06 · Métricas de cierre honestas — **P1 · S**
- **Problema real:** FR-09, FR-10 (P1), FR-36 (P2).
- **Trabajo:** cobertura de posicionamiento definida (observados en curso / programados en curso, por línea); edad de posición medida; umbral de puntualidad visible en contrato y pantalla.
- **Ejecutor:** Claude `sonnet` · medium · **Revisor:** Codex `gpt-5.6-terra` · high.
- **Dependencias:** H4-12 para la medida por línea.
- **Pruebas de cierre:** `route_coverage_pct` no puede valer 100 % por construcción (test con un programado no observado); `position_age` sale de datos, no de constante; el umbral aparece en `/api/v1/history/*` y en Explore.
- **ADR/DEC:** DEC-033 (b) (sigue abierto hasta tener histórico).
- **Gate humano:** ninguno.

### Bloque D — Operación y despliegue

#### H4-07 · Operación supervisada local medida — **P1 · M**
- **Problema real:** FR-15, FR-22 (P2), FR-30 (umbrales de calidad), NV-01.
- **Trabajo:** métricas de uptime, reinicios, lag de sondeo, edad de fuente, RSS/FD, disco y resultado del archivo; watermark común de exportación (FR-22); ensayo de backup/restore en volumen desechable; ventana ≥ 24 h (preferible 72 h) con pérdida de BD/red ensayada.
- **Ejecutor:** Codex `gpt-5.6-terra` · high · **Revisor:** Claude `sonnet` · high.
- **Dependencias:** H4-11.
- **Pruebas de cierre:** informe con la ventana completa sin huecos inexplicados; carrera de AUD-08 repetida → nunca «2 runs con 1 posición» en la primera exportación; restore verificado.
- **ADR/DEC:** ADR-0015 §6 (sigue «local supervisada»); DEC-004 (aporta la medida que falta).
- **Gate humano:** host persistente; cualquier coste.

#### H4-08 · Rendimiento y coste antes de decidir — **P1 · M**
- **Problema real:** FR-13 (P1), FR-38 (P2 que bloquea exposición pública), NV-03.
- **Trabajo:** carga real con `uvicorn` + red (1/10/50/100 clientes a 10 s) = H7a; snapshot pregenerado servido estático = H7b; decisión motivada de pool; propuesta de autenticación/limitación de tasa; política de retención con la medida de H4-07.
- **Ejecutor:** Codex `gpt-5.6-terra` · high · **Revisor:** Claude `sonnet` · high (el encargo proponía `sonnet` · medium; se eleva porque el resultado decide DEC-038 y un bloqueante de publicación).
- **Dependencias:** H4-01 (lectura consistente cambia la latencia); H4-07 para retención.
- **Pruebas de cierre:** p50/p95 por nivel de concurrencia; H7a y H7b confirmadas o refutadas con su umbral; benchmark antes/después del pool.
- **ADR/DEC:** DEC-038, DEC-004, `ARCHITECTURE.md:68-69` (CDN).
- **Gate humano:** **DEC-038 y DEC-004 son del propietario**; cualquier CDN o infraestructura con coste.

#### H4-09 · Release-readiness integral — **P0 como gate · M**
- **Trabajo:** E2E real de red, geometría, navegación, History/Explore, seguridad y coste operativo; reevaluar cada `FR` con su prueba de cierre en el **nuevo HEAD**; sesión con usuarios (H5 con n ≥ 30 si se quiere una conclusión; n = 5 solo como orientación).
- **Ejecutor:** Codex `gpt-5.6-sol` · high · **Revisor:** Claude `opus` · high.
- **Dependencias:** todos los anteriores cerrados o `BLOCKED` documentados.
- **Pruebas de cierre:** GO/CONDITIONAL/NO-GO con cada bloqueante de `AUDIT_EXECUTIVE_DECISION.md` §8 resuelto o aceptado expresamente por el propietario.
- **Gate humano:** decisión de publicar; push/PR/merge.

### Bloque E — Ampliaciones posteriores (fuera del H4)

AVE, Larga y Media Distancia y otros núcleos **no** entran en el H4: la cobertura de Madrid es del 38,45 % por circulaciones y el contrato temporal tiene un P0 abierto; ampliar multiplicaría ambos defectos. Requisito previo para reconsiderarlo: H4-03 por encima del umbral que fije H4-10 y H4-04 cerrado.

## 5. Orden y paralelismo propuestos

```text
Bloque 1 (veracidad):   H4-00 ──► H4-04            H4-01 (FR-02/FR-19 ya; FR-07 tras H4-00 §5)
                        H4-10 (en paralelo)        H4-11 (en paralelo, antes de H4-07/H4-12)
Bloque 2 (geometría):   H4-03 lote 1 (coste cero) ─► lote 2 ─► lote 3…   H4-12 (tras H4-11) ─► calibra H4-04
Bloque 3 (producto):    H4-05 (tras contrato H4-00)   H4-06 (tras H4-12)
Bloque 4 (operación):   H4-07 (tras H4-11) ─► H4-08
Gate final:             H4-09
```

Máximo dos tareas técnicas pesadas simultáneas (preferencia del encargo). Si H4-00 concluye que basta con corregir la traducción sin enmendar ADR-0014, se reduce a la corrección del texto de §2 y §5 (FR-31, FR-07) y H4-04 sigue igual.

## 6. Revisión explícita de ADR-0014, ADR-0015, DEC-033, DEC-038 y DEC-004

**No se acepta ni se rechaza ninguna en nombre del propietario.** Se documenta qué evidencia hay.

| Decisión | Estado actual | Evidencia a favor | Evidencia en contra | Recomendación al propietario |
|---|---|---|---|---|
| **ADR-0014** — contrato temporal y snapshot | `Propuesto` | Envolvente única y acotada; el cliente no decide avance (`AUD01-DESC-002`, error 6,6 cm); separación `raw`/`map_matched`/`rendered` correcta en el contrato; `revision` ordenable con `scope` (EGM DESCARTADO); catálogo cacheable (200/304, AUD-06). | §2 describe una fórmula sin `dwell_until` y `speed_mps = 0` con espera, contraria al código (FR-31); la regla de la envolvente produce FR-01 (P0) y FR-03/04/05; §5 promete una revisión que `build_snapshot` no garantiza (FR-07); §3/§4 separan `raw` de `map_matched` pero la presentación los colapsa (FR-06). | **Mantener `Propuesto`; no aceptar en su redacción actual.** Aceptar tras la enmienda de H4-00 y la verificación de H4-04. La arquitectura (alternativa 1, envolvente en backend) no está refutada: lo refutado es la regla de estado de parada. |
| **ADR-0015** — archivo frío e histórico | `Propuesto` | Idempotencia y recuperación por cuarentena probadas con PostgreSQL real (AUD-06: 103 tests; doble exportación byte-idéntica; ambas caídas del intercambio); 404 en día no archivado; §6 «nunca 24/7 verificado» se cumple y AUD-06/08 lo confirman. | La primera exportación concurrente no es un corte atómico multi-tabla (FR-22/`AUD08-P2-001`), algo que §1 no afirma pero tampoco advierte; retención sin decidir (DEC-004). | **Evidencia suficiente para aceptarlo con una nota** que declare la no atomicidad multi-tabla y la obligación de reprocesar tras ingesta tardía (o con el watermark de H4-07). Decisión del propietario. |
| **DEC-033** — métricas diarias | límite (a) cerrado en MP-021; (b) y (c) abiertos | (a) `calendar_dates` aplicado vía `scheduled_service_ids_for_date` (verificado sintéticamente; Renfe no publica el fichero, NV-11). | (b) el umbral de 300 s sin calibrar **se publica** como `on_time_pct_of_covered` y no aparece en contrato ni pantalla (FR-36); no hay histórico con el que calibrar. | **Mantener pendiente** (b) y (c). Condición mínima para seguir publicando la métrica: umbral visible (H4-06). |
| **DEC-038** — pool de conexiones | abierta | ~66 ms de 68,91 ms de p50 de `/health` son conexión; `/snapshot` baja de 98,70 a 8,47 ms con conexión reutilizada (MP-019). | Ninguna medida con ASGI + red + concurrencia; el pool es dependencia nueva y decisión de despliegue. | **Mantener pendiente; la evidencia favorece el pool**, pero la decisión debe tomarse con H7a (H4-08), porque el cuello de botella público puede ser el cálculo del snapshot por espectador, que el pool no resuelve. |
| **DEC-004** — retención del histórico | pendiente | ≈48,9 B/fila Parquet ZSTD; ≈19 MB/día; ≈7 GB/año (MP-021). | Proyección de 13 min (823,2 s), no de 24–72 h como exige la propia DEC y el *exit gate* F3 (FR-15). | **Mantener pendiente** hasta la ventana ≥ 24 h de H4-07; la cifra actual sirve como orden de magnitud, no como base de decisión. |

## 7. Propuestas anteriores que conviene descartar

1. Criterios de aceptación que **pre-autorizan** incompletitud («mayoría `pending` honesto», `TASKS.md:443`) o que dejan «condición fundamental» sin lista cerrada (`PROMPT-UNICO-ORCA.md:19`).
2. Conteos de fixture como criterio de cierre de producto («119/121/49 SKIPPED»): buena regresión de parser, mal criterio de producto.
3. Marcar el patrón C8b truncado como `non_traversable` (consagra un defecto del proveedor).
4. Subir la tolerancia de espera como corrección única (contrafactual B de AUD-04) o acotar solo `temporal_offset_s` (no cubre salidas retrasadas ni paradas intermedias, §2 del registro).
5. Trasladar la decisión de espera al cliente (alternativa D de AUD-04; viola ADR-0014 §1).
6. Clustering de marcadores (AUD-05: coste de legibilidad y rendimiento; basta el zoom inicial).
7. Llamar «24/7» a una ráfaga supervisada.
8. Tratar el snapshot en CDN como «futuro» indefinido mientras se construye una API cuyo coste crece con cada espectador: se mide en H4-08 y se decide.
9. La Opción B de `INCIDENT_5433.md` (limpieza): **descartada por el propietario** el 2026-11-24.
10. H4-02 del encargo como tarea independiente (hipótesis refutada, §1).

## 8. Gates humanos que nadie más puede cerrar

Autorizar el H4 y la serie `MP-023+`; aprobar la enmienda de ADR-0014 antes de H4-04; aceptar ADR-0015 (con nota) y, más tarde, ADR-0014; DEC-002 (licencia de código), DEC-003 (visibilidad), DEC-004, DEC-038; proveedor y política de teselas; descargas OSM y su atribución; host persistente y cualquier coste; push, PR y merge (ver `INTEGRATION_PROPOSAL.md`); decisión de publicar.
