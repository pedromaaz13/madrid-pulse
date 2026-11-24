# AUD-01 — Tesis de producto, arquitectura y diseño de pruebas refutables

**Ejecuta:** Claude Opus (worker despachado, contexto aislado)
**Revisa:** OpenAI Codex · Sol · High — **ronda 1: CHANGES_REQUESTED**, correcciones aplicadas en esta revisión (pendiente de re-evaluación)
**Fecha:** 2026-11-23 (revisión 2)
**Rama de auditoría:** `audit/hito-03-adversarial`, creada desde `mp-022-validacion-integrada` @ `beb9434`
**Worktree:** `<WORKTREES>/audit-hito-03`

No se ha modificado ni una línea de código de producto, migración, contrato o dato
persistente. Lo único que añade esta tarea al repositorio es este documento y los siete
guiones de medición de `scratch/aud01_*.py` que lo sustentan.

---

## Revisión 2 — qué cambió respecto a la ronda 1, y por qué

Codex Sol · High reprodujo de forma independiente ambos P0 ejecutando mis propios guiones
sin red ni PostgreSQL. **Ambos P0 quedan CONFIRMADOS como hallazgo de producto**, y varias
cifras y formulaciones de mi redacción no coincidían con lo reproducido. Esto es lo que he
corregido, todo contra medida nueva, no contra opinión:

| # | Qué decía la revisión 1 | Qué dice ahora | Por qué |
|---|---|---|---|
| 1 | «**26** de 44 no se movieron» (§5.2, P0-001) | «**31** no cambiaron ni coordenada ni progreso; solo **13** se movieron» | Mi 26 era un recuento **a ojo** de la tabla impresa y estaba mal. El recuento programático da 31/13. Definición ahora explícita: `v_real == 0,00 m/s` exacto, es decir progreso map-matcheado idéntico en los dos cortes. `aud01_snap.py` imprime ya ese par de recuentos para que no dependa de una lectura visual. |
| 2 | Horizonte rotulado «180 s» en guiones y texto | **180 s configurados** (`stale_after_s`) frente a **190 s efectivos** desde el ancla, distinguidos en cada sitio | `horizon_end = calculated_at + stale_after_s` y `calculated_at = ancla + 10 s` (el snapshot se construye 10 s **después** del corte), así que la ventana real desde el ancla son 190 s. Afecta a §3.4, P1-005, P0-001, H4 y a los rótulos de columna de dos guiones. El desajuste con el intervalo mediano entre paradas resulta algo **mayor**, no menor. |
| 3 | «el criterio **pre-autorizó** 28/103» (§1, P0-002) | «el criterio **admitía de antemano** una mayoría pendiente sin cuantificar, y 28/103 cumple ese mínimo bajo **sin haber sido el número bendecido**» | `docs/TASKS.md:443` autoriza «mayoría `pending` honesto» y `docs/STATUS.md:832` un mínimo de C5 + un ramal de C4 + un tramo compartido. Ninguno de los dos aprueba el número 28/103: mi formulación atribuía al criterio una precisión que no tiene. |
| 4 | «ocho líneas **nunca se intentaron**»; los 72 pendientes como una sola categoría | **67 sin fuente congelada ni intento registrado**, **1 patrón con feed truncado** y **4 con descarga fallida** de `9174512`, separados en tabla y en texto | «Nunca se intentó» es una prueba negativa que no tengo. El patrón de una parada no es trabajo geométrico pendiente, y los 4 de C4b ya encajan offline sobre `9174511` invertida aunque siga faltando decidir la vía direccional correcta. El CSV da a los 72 el mismo `reason`, así que esta distinción no es recuperable desde el artefacto canónico. |
| 5 | 8 hipótesis (H1–H8) | **10** (H1, H2, H3, **H3b**, H4, H5, H6, **H7a**, **H7b**, H8), cada una declarando qué parte del baseline es medida y qué parte no | H3 era una conjunción cuyo criterio de refutación no atacaba su primera mitad; H7 mezclaba capacidad con ganancia de CDN y dejaba sin cubrir la banda 5×–10×. Además: H1 define ahora pares ancla-a-ancla y no generaliza la fixture a Live; H2 separa refutación empírica de recomendación de corrección y abandona «cualquier instante»; H3 declara que omite líneas con denominador cero; H4 admite baseline solo indirecto; H5/H6/H8 se marcan **no concluyentes con n=5**; H8 añade métrica operacional y orden contrabalanceado. |
| 6 | 4 descartados con formulación ancha | Los mismos 4, **con alcance acotado** y lo que sigue sin cubrir | DESC-001 da ahora una razón sustantiva (cada frontera aísla un fallo observado) en vez de enumerar tecnologías ausentes; DESC-002 se limita a la **autoridad de avance** y reconoce que el cliente sí calcula coordenadas; DESC-003 no se presenta como prueba de equivalencia semántica con Valfiguer; DESC-004 separa CORS de **autenticación** y **limitación de tasa**, que siguen siendo riesgos abiertos. |

**Lo que el revisor confirmó y no se ha tocado:** 17/121 circulaciones pre-salida
(17/44 = 38,6 % de las map-matcheables), velocidades 15,52–30,00 m/s (55,9–108 km/h), el
peor caso `1023V20478C4b` a 2 319 s = 38,65 min de su salida con 5 700,6 m de avance falso;
el salto p50 **1 237,0938 m** / máximo **3 274,2258 m**; la matriz 28 `validated` / 3
`partial` / 72 `pending`; y 44/121 móviles frente a 77/121 = 63,636 % en punto estático.


### Ronda 2 del revisor — los dos puntos que quedaban

Codex Sol · High aprobó los puntos 1, 3, 4 y 6 tras reproducirlos de nuevo (17/121, 190 s
efectivos, 15,52–30,00 m/s, 31/44 quietas, 13/44 móviles, salto p50 1 237 m / máx 3 274 m:
todo coincide) y devolvió dos:

| # | Qué estaba mal | Qué dice ahora | Por qué |
|---|---|---|---|
| 7 | «`calculated_at` va **10 s por detrás** del ancla» (fila 2 de la tabla de la revisión 2, y §3.4) | «`calculated_at = ancla + 10 s`»; el snapshot se construye 10 s **después** del corte, así que **el ancla** queda 10 s por detrás de `calculated_at` | Tenía la dirección temporal **invertida** en esos dos sitios. El propio guion la daba bien (`aud01_envelope_predeparture.py:8`, `calculated_at = cut + 10 s`), así que era un error de redacción, no de medida: los 190 s efectivos no cambian. Las otras tres menciones del desfase (§3.4, P0-001, P1-005) ya estaban correctas y no se han tocado. |
| 8 | Varias hipótesis sin umbral de refutación cuantificado, o con el umbral contradiciendo la afirmación | **Ocho hipótesis** con umbral numérico explícito y estadístico alineado con su afirmación, más **dos preguntas exploratorias** (H6, H8) reclasificadas por no ser refutables hoy | Detalle por hipótesis en la introducción de §10: H1 pasa a afirmar medianas (afirmaba proporción y se refutaba con mediana); H2a declara que basta **1 de 6** instantes por debajo del 10 %; H3 define «persistente» como **≥ 8 de 10 sondeos** y se refuta con **≤ 1 línea**; H4 sube su umbral a **< 25 %** para cerrar la banda muerta del 10–30 %; H5 añade **margen de equivalencia** (< 20 puntos) y **n ≥ 30**; H6 y H8 pasan a exploratorias declarando qué haría falta para volverlas refutables. |

Nada de lo ya aprobado se ha modificado en esta ronda: los cambios se limitan a la
dirección temporal de dos frases y a la columna «Qué la refutaría» de §10.

---

## 0. Método y límites de esta auditoría

**Qué he hecho.** He leído la cadena documental completa de los tres hitos
(`docs/PLAN.md`, `TASKS.md`, `STATUS.md`, `DECISIONS.md`, los 15 ADR, los 12 documentos
del kit en `docs/hitos/hito-03/`, `docs/research/` y las 10 evidencias de
`docs/evidence/`), y después he **ejecutado medidas propias** contra las fixtures
congeladas del kit usando el código de producción del repositorio, sin PostgreSQL y sin
red. Cada cifra de este documento viene con el comando que la produce (§8) o con
`archivo:línea`.

**Qué NO he hecho, y por tanto no afirmo.**

- No he consultado en vivo Via Península, Valfiguer ni las apps oficiales de
  Renfe/CRTM. La comparación de §1 se apoya en la verificación documentada del propio
  proyecto (`docs/research/deep-research-report.md`, `docs/legal/DATA_SOURCES.md`,
  DEC-016, fechada `2026-11-18`) y queda marcada como **NO VERIFICADO en vivo**.
- No he llamado a Overpass para comprobar si existen relaciones OSM utilizables para las
  ocho líneas sin geometría. Lo que sí está verificado es que para esas ocho **no hay
  intento documentado** —distinto de los 4 patrones de C4b, donde sí hubo intento y
  falló con dos `HTTP 502`— (§3.5).
- No he montado la aplicación en navegador: eso es AUD-05, cuyo informe
  (`FRONTEND_UX_AUDIT.md`) cito en vez de repetir.
- Evito duplicar AUD-02 (`RAILWAY_GEOMETRY_AUDIT.md`) y AUD-07 (`EGM_REVIEW.md`); cuando
  un hallazgo mío toca el mismo terreno lo digo y añado solo lo que falta.

**Sesgo declarado.** El encargo pide buscar debilidades reales, no confirmar que el
proyecto está bien construido. He registrado también cuatro hipótesis adversas que
intenté sostener y **no** se sostienen (§6, `DESCARTADO`), porque una auditoría que solo
encuentra defectos no es verificable.

---

## 1. Veredicto en una página

El Hito 3 está **correctamente ejecutado contra sus criterios y mal especificado en su
criterio central**. Las siete tareas cumplen lo que se les pidió, con evidencia real y
revisión cruzada que encontró y corrigió defectos verdaderos. El problema no está en la
ejecución: está en que **el criterio de aceptación de la geometría admitía de antemano que
la mayoría de la red no tuviera trazado** (`docs/TASKS.md:443`: «mayoría `pending`
honesto»; `docs/STATUS.md:832`: un mínimo de C5 + un ramal de C4 + un tramo compartido)
mientras la misión de producto exigía «un mapa de toda Cercanías Madrid, inmersivo,
map-first» (`PROMPT-UNICO-ORCA.md:11`) y una puerta de aceptación exigía que «el tren no
salte cada 20 s» (`MATRIZ-CIERRE-MADRID.md:21`). Nadie reconcilió las tres cosas, y el
sistema de puertas no podía detectarlo porque **ninguna puerta es falsable**: basta
documentar la causa de un hueco para que deje de bloquear (§6, `AUD01-P1-009`).

El resultado medible, con el código del repositorio y los cortes del propio kit:

| Magnitud | Valor medido | Comando |
|---|---|---|
| Patrones con geometría validada | **28 de 103** (8 de 12 líneas con **0**) | `docs/evidence/mp-018-corridor-coverage.csv` |
| Trenes del corte que pueden moverse entre sondeos | **44 de 121 (36,36 %)**; los otros 77 (63,64 %) son puntos estáticos | `mp-019-tres-snapshots-replay.md:50` |
| Circulaciones a las que el contrato da movimiento **sin haber salido** | **17 de 121**, hasta **38,6 min** antes, a **56–108 km/h** | `aud01_envelope_predeparture.py` |
| Salto real al llegar el ancla siguiente | p50 **1 237 m**, máx **3 274 m** (44 circulaciones; 31 de ellas inmóviles) | `aud01_snap.py` |
| Cobertura real de posicionamiento (lo que el kit pedía medir) | **65/73 = 89,0 %**, con C1 al 50 % y C10 al 60 % | `aud01_coverage.py` |
| Cobertura publicada en la matriz vinculante | **121/121 = 100,0 %** (tautológica) | `mp-022-coverage.md:5` |

Y tres cosas impiden publicar hoy, ninguna de ellas de código: el README sigue diciendo
que no hay producto (`README.md:23`), el mapa base usa un servicio operativo de la OSMF
que no está registrado en `docs/legal/` (`MapView.tsx:195`), y el coste por espectador
(255 ms de p50 de snapshot cada 10 s, sin pool ni CDN) no soporta una audiencia pública.

Lo que **sí** es genuinamente bueno, y debe conservarse: la separación
`raw`/`map_matched`/`rendered` con seis métodos de presentación explícitos; que un patrón
sin corredor nunca se proyecte sobre un corredor ajeno (`gtfs_source.py:97-117`); que el
cliente no extrapole sin envolvente (`movement.ts:80-96`, error cliente-backend de 6,6 cm);
la taxonomía `coverage` del histórico que separa un hueco real de una anulación del
operador (DEC-042); y el archivo frío con cuarentena y recuperación de sustituciones
interrumpidas (DEC-040). Nada de eso es cosmético y nada de eso lo tiene la competencia
documentada.

---

## 2. ¿Resuelve una necesidad real o reproduce lo que ya existe?

**Respuesta corta: la diferenciación que el producto tiene no es la que su misión
declara.** La misión declarada es un mapa (`PROMPT-UNICO-ORCA.md:11`, «mapa de toda
Cercanías Madrid, inmersivo, map-first»); en el mapa es donde Madrid Pulse está peor
respecto a Via Península. La diferenciación real está en la capa de datos, que es
invisible para quien abre la aplicación.

Comparación con lo que el propio proyecto verificó y registró (fechas de verificación en
`docs/legal/DATA_SOURCES.md`, filas `reference.*`; análisis en
`docs/research/deep-research-report.md:23-61`):

| Capacidad | Via Península | Valfiguer | Apps oficiales Renfe/CRTM | Madrid Pulse hoy |
|---|---|---|---|---|
| Mapa en vivo con movimiento continuo sobre vía | **Sí**, toda España, geometría construida a diario (`deep-research-report.md:27,31`) | Orientado a posición observada (`:41`) | No publican mapa de posición de trenes | **Parcial: 36 % de los trenes** (44/121); 8 de 12 líneas sin trazado |
| API pública propia | Snapshots en R2/CDN | **Sí**, GeoJSON con salud por feed (`:41-43`) | No | Sí, `/api/v1`, no publicada |
| Histórico descargable | Bundles operativos | **Sí, 90 días**, CSV diario 11–21 MB (`:45`) | No | Sí, Parquet idempotente, retención **sin decidir** (DEC-004) |
| Puntualidad | Secundaria | **Sí**, con `flags` de calidad (`:21`) | Sí, agregada | Sí, **siempre con denominador** (`ExploreView.tsx:193-207`) |
| Salud de fuente expuesta al usuario | — | **Sí** (`ok/stale/data_age_s/unchanged_for_s/rejected`) | No | **Sí, los cinco campos** (`schemas.py:59-67`) |
| Separación observado / proyectado / renderizado | Implícita | Implícita | — | **Sí, explícita y contractual** (ADR-0014 §3) |
| Hueco de cobertura distinguido de anulación del operador | — | No documentado | No | **Sí** (DEC-042, `history.py`) |

Lectura honesta de esa tabla: en las cuatro primeras filas —las que un usuario percibe—
Madrid Pulse **reproduce** funcionalidad que ya existe, y en la primera lo hace peor que
Via Península. En las tres últimas —las que un analista percibe— aporta algo que no
consta en ninguna de las referencias. El producto que está construido es un **producto de
datos de transporte con interfaz de mapa**, no «otro mapa de trenes»; y su propio prompt
de autorización lo describe como lo segundo.

Esto no es un argumento para abandonar: es un argumento para dejar de medir el éxito con
la vara del mapa inmersivo. Si el criterio de valor fuera «puedo demostrar, con
denominador, qué se sabía de un tren a una hora dada, y distinguir un tren anulado de un
hueco de mi colector», Madrid Pulse ya gana a lo documentado de la competencia hoy — y lo
hace con 28/103 de geometría.

**Dependencia de fuente, ya registrada:** todo el producto depende de que Renfe siga
publicando GTFS-RT abierto sin cambio de contrato, sin SLA ni acuerdo. No es un hallazgo
nuevo (ADR-0002 lo declara y AUD-07 §1 lo confirmó); lo repito porque es el riesgo de
viabilidad dominante y no lo mitiga ninguna de las decisiones de los tres hitos: CRTM
sigue `PENDING` como fuente alternativa desde DEC-006.

---

## 3. ¿La arquitectura es proporcional?

**Sí en el eje que normalmente se sobre-ingenieriza, y no en el eje que el propio
proyecto identificó y luego no atendió.**

### 3.1 Lo proporcionado (confirmado, no es hallazgo)

No hay microservicios por dominio, ni broker de eventos, ni Kubernetes, ni Spark: el
monolito modular con cuatro procesos (colector, API, snapshotter, web) es correcto para
≈19 MB/día y ≈1 300 circulaciones/día medidos (`mp-021-coste-colector-continuo.md`). Las
fronteras se respetan de verdad: `engine_for` devuelve `None` para un patrón sin corredor
en vez de reutilizar el corredor cargado por defecto (`apps/api/gtfs_source.py:97-117`),
que era la vía fácil y habría producido trenes sobre vías ajenas. Coincido con AUD-07 §2
y §9.

### 3.2 El desajuste real: el coste por espectador

`docs/ARCHITECTURE.md:68-69` adoptó como **principio arquitectónico** el patrón de Via
Península «fetch periódico → publicar en CDN», con la razón correcta escrita: «desacoplar
el coste de servir el mapa en vivo del número de espectadores». Tres hitos después:

- `infra/cloudflare/` sigue vacío, con el aviso «vacío intencionadamente».
- Cada espectador sondea `/api/v1/snapshot` **cada 10 s** (`useSnapshot.ts:8`).
- Ese snapshot mide **p50 254,73 ms / p95 418,23 ms / máx 2 501 ms** con solo 121
  vehículos, y **en proceso con `TestClient`, sin red ni servidor ASGI**
  (`mp-022-benchmark.md:36`).
- No hay pool de conexiones: ~66 ms de cada petición son abrir la conexión (DEC-038,
  abierta desde MP-019).

Aritmética directa: 0,255 s de trabajo cada 10 s son **2,5 % de un núcleo por
espectador**, antes de red, TLS y ASGI; con el tablero de estación abierto (103 ms cada
20 s) y salud (75 ms cada 30 s) sube a ~3,3 %. Eso son **~30 espectadores concurrentes
por núcleo** y p95 degradándose antes. Para un piloto local es irrelevante; para publicar
es el techo.

Lo que convierte esto en hallazgo y no en «deuda normal» es que el **propio backlog del
proyecto lo pidió explícitamente para este hito**:

> «Evaluar si el patrón de snapshot/CDN ya previsto en `docs/ARCHITECTURE.md` se vuelve
> necesario en este punto, en vez de seguir sirviendo peticiones directas desde la API
> para cada espectador.» — `docs/HITO_3_BACKLOG.md:32`

MP-019 midió el coste y lo documentó bien; ninguna tarea de la cadena evaluó la pregunta.
Y el feed se actualiza cada ~30 s mientras el cliente sondea cada 10 s: dos de cada tres
peticiones no pueden traer dato nuevo por construcción.

### 3.3 Complejidad introducida sin necesidad: no la encuentro, con una excepción menor

Busqué activamente sobre-ingeniería y no la hay en el stack. La única pieza cuyo coste no
veo compensado es la **doble ruta de lectura de vehículos**:
`/api/v1/live/vehicles` (legado, p50 **1 621 ms**, `mp-022-benchmark.md:38`) sobrevive en
paralelo al snapshot batch, fuera del camino del frontend, con sus propios tests de
contrato. Mantener una ruta 6× más lenta que nadie usa es coste sin beneficio; o se
declara obsoleta en el contrato o se reimplementa sobre el mismo lote.

### 3.4 El umbral que cambió de trabajo sin recalibrarse

DEC-010 introdujo `60 s / 180 s` como «defaults configurables» para **clasificar
frescura** (`OBSERVED`/`ESTIMATED`/`STALE`), con la advertencia explícita de
`deep-research-report.md:181`: «Los umbrales exactos deben parametrizarse y calibrarse
con datos reales, no fijarse como verdad desde el diseño».

ADR-0014 §2 reutilizó `stale_after_s = 180` como **horizonte de extrapolación**: cuánto
tiempo es lícito que el cliente avance un tren. Es un trabajo distinto y mucho más
consecuente, y no se recalibró. Lo medí contra el GTFS oficial del kit
(`aud01_stopgap.py`, 501 923 intervalos reales del núcleo Madrid):

- intervalo mediano entre paradas: **180 s** — exactamente el horizonte;
- **53,1 %** de los intervalos son ≤ 180 s;
- el GTFS declara espera > 0 en solo **9,9 %** de las paradas (p50 de espera: **0 s**).

La consecuencia es que la mitigación escrita en el propio código es falsa:

> «tras la espera del propio ancla, la envolvente usa una sola tasa media hasta el fin del
> horizonte, así que no reproduce las esperas *intermedias* que caigan dentro de él […]
> El horizonte por defecto (`stale_after_s`, 180 s) acota ese efecto.»
> — `packages/movement/rendering.py:82-85`

180 s no acota el efecto: **lo abarca**. Y el horizonte que de verdad se aplica es aún
mayor: `horizon_end = calculated_at + stale_after_s`, y `calculated_at = ancla + 10 s` en
la propia evidencia de MP-019 —el snapshot se construye 10 s **después** del corte, así que
el ancla queda 10 s por detrás de `calculated_at`, no al revés—, de modo que la ventana
**efectiva** desde el ancla es de **190 s**, por encima del intervalo mediano entre paradas. Un horizonte completo
cruza por tanto un tramo entre estaciones entero, y como `dwell_end_seconds` solo devuelve
algo si el horario declara espera (9,9 % de las paradas), el tren se dibuja atravesando la
estación sin detenerse. Es el caso que `diseno/INTERACCIONES.md:20` pone como prueba de
aceptación («parada en estación») y que ninguna prueba del hito comprueba.

> **Precisión de la revisión (Codex Sol · High).** Conviene no mezclar los dos números:
> **180 s es el valor configurado** (`stale_after_s`, `packages/movement/model.py:40`) y
> **190 s es el horizonte efectivo medido** desde el ancla en esta evidencia. La
> comparación con el intervalo mediano de 180 s vale para el valor configurado; con el
> efectivo, el desajuste es algo mayor, no menor. Los dos guiones
> (`aud01_envelope_predeparture.py`, `aud01_snap.py`) imprimen ahora el horizonte efectivo
> y rotulan sus columnas con él.

### 3.5 Geometría: 67 pendientes son alcance accionable, 1 es feed truncado y 4 tuvieron intento fallido

Los 72 patrones `pending` **no son una sola categoría**, y conviene separarlos porque su
causa y su remedio son distintos (`docs/evidence/mp-018-corridor-coverage.csv`, recuento
reproducido por línea y estado):

| Grupo | Patrones | Líneas | Qué consta | Naturaleza |
|---|---:|---|---|---|
| **Sin fuente congelada ni intento registrado; accionables por geometría** | **67** | C1, C2, C3, C7, C8a, C8b, C9, C10 | ninguna entrada en `madrid_source_specs` y ningún intento registrado en `STATUS`/`TASKS` | alcance no encargado |
| **Feed de origen truncado** | **1** | C8b (`10T0098C8b`) | solo queda Cercedilla con `stop_sequence` 032/025; la ruta espejo `10T0097C8b` tiene 114 viajes sin `stop_times` | defecto upstream; no se resuelve descargando OSM |
| **Intento real fallido** | **4** | C4b (`10T0016C4b`, sentido opuesto) | `9174512` devolvió dos `502`; offline, las 15 paradas encajan a 48,3 m sobre `9174511` invertida | descarga propia bloqueada; alternativa local con incertidumbre de vía contigua |

La formulación precisa para los 67 es «**sin fuente congelada ni intento
registrado**», no «nunca se intentó»: lo que la evidencia sostiene es la ausencia
de fuente en `packages/geo/madrid.py:19-60` y de registro, no una prueba negativa.
El patrón 68º de ese grupo original es un feed truncado y requiere calidad de
dato/upstream, no adquisición geométrica. Para los 4 de C4b sí hay intento y causa
externa registrada.

Un detalle del artefacto canónico que esta separación deja a la vista: el CSV asigna a
**los 72** el mismo `reason` —«sin geometría OSM descargada para este patrón/sentido»—, así
que la distinción entre límite externo y alcance no encargado **no es recuperable desde la
matriz**, solo desde la prosa de `STATUS`. Es una pérdida de información en el único
artefacto que un consumidor leería.

Y el alcance que decidió los 67 accionables está escrito:

> «Mínimo real a descargar/verificar: revalidar C5 sin huecos, un ramal de C4 […] y un
> tramo compartido entre dos líneas» — `docs/STATUS.md:832`

El herramental para hacerlo existe y es reproducible (`packages/geo/tools/fetch_fixture.py`,
`find_route_relations(ref=..., network="Cercanías Madrid")`, documentado en
`tests/fixtures/osm_c4_real/MANIFEST.md`). Para los 67, no es un problema técnico abierto:
es trabajo no encargado. El patrón truncado no se arregla con ese herramental. Para los 4
de C4b, consta un intento contra un servicio externo que falló y quedó correctamente
registrado como pendiente en vez de interpretarse como relación inexistente.

---

## 4. Decisiones tomadas sin evidencia suficiente y luego tratadas como hecho

Recorrí `docs/DECISIONS.md` buscando todo lo marcado como estimación, supuesto o «punto de
partida calibrable», y comprobé en el código qué carga soporta hoy cada una.

| DEC | Cómo se declaró | Qué carga soporta hoy | Veredicto |
|---|---|---|---|
| **DEC-010** (60/180 s) | «defaults configurables mantenidos tras calibración», `Propuesta` | `stale_after_s` es el **horizonte de extrapolación** de ADR-0014 §2, no solo una etiqueta de frescura | **Ascendido de hecho sin recalibrar.** Medido incorrecto (§3.4). `AUD01-P1-005` |
| **DEC-033 (b)** (300 s de puntualidad) | «punto de partida calibrable sin histórico real propio todavía» | Calcula `on_time_pct_of_covered` que la UI publica (`ExploreView.tsx:201`) | **Se publica como métrica.** El umbral no está en el contrato (`schemas.py:557-565`) ni en pantalla. `AUD01-P2-013` |
| **DEC-004** (retención) | «La ventana medida son 13 min, no 24–72 h, así que es una proyección» | De ahí sale el «≈7 GB/año» que el dossier presenta al propietario | **Correctamente etiquetado**, pero el *exit gate* F3 de `docs/PLAN.md:26-29` exigía 24 h y nunca se cumplió. Confirmado por AUD-07 §drift-3; no lo re-cuento |
| **DEC-011** (almacenamiento híbrido) | «supuestos de tamaño extrapolados de Valfiguer» | Medido de verdad en MP-021 (48,9 B/fila) | **Resuelto.** No es hallazgo |
| **DEC-028** (un corredor sirve ambos sentidos) | «Verificado en MP-013 con los 4 vehículos C5 reales del soak» | MP-018 generalizó a `madrid_source_specs`, ya con una relación por sentido para C4a | **Generalización sana**: MP-018 no heredó la simplificación, descargó los dos sentidos. No es hallazgo |
| **Umbrales de calidad** (`implausible_speed_kmh=200`) | «puntos de partida calibrables, no verdades de diseño» (`quality/engine.py:4-5`) | Deciden qué entra como `data_quality_event` | **Sin calibrar y medidos sobre cuerda, no sobre arco** (§5.3). `AUD01-P2-015` |

El patrón es consistente y vale como lección de proceso: este proyecto **etiqueta muy bien
lo que no sabe, y no tiene ningún mecanismo que obligue a volver sobre una etiqueta cuando
el valor cambia de papel**. DEC-010 pasó de clasificar frescura a autorizar extrapolación
sin que nada lo señalara, porque el cambio no fue un cambio de valor sino de uso.

---

## 5. ¿Qué se dio por terminado sin probarse en condiciones realistas?

### 5.1 El inventario de evidencia

| Tarea | Base de la evidencia de cierre | Datos reales en vivo |
|---|---|---|
| MP-016 | cortes congelados `1532`/`1533` + tests contra PostGIS + escenario «colector detenido» provocado | parcial (el colector detenido sí) |
| MP-017 | ZIP GTFS oficial congelado + topología sintética; **sin documento en `docs/evidence/`** | no |
| MP-018 | descargas Overpass reales (7 relaciones, 3 líneas) | sí, para lo descargado |
| MP-019 | tres snapshots sobre `1532`/`1533`, reloj controlado | no |
| MP-020 | base de replay (`mp020-replay-db`) de los mismos cortes | no |
| MP-021 | replay + **13 min 43 s** de feeds en vivo (única ventana real del hito) | sí, 13 min |
| MP-022 | los mismos dos cortes + fixture sintética derivada | no |

Es decir: **toda la cadena se validó sobre dos capturas de 77 segundos de un único día
(2026-11-20) más 13 minutos de operación en vivo**. Eso no es un defecto de los
ejecutores: es exactamente lo que los criterios pedían. `MATRIZ-CIERRE-MADRID.md:9`
advierte correctamente que «los recuentos congelados **no** son expectativa del directo de
hoy», y `MEJORAS-PRODUCTO-VALIDADAS.md:88` que «los dos cortes 1532/1533 no prueban por sí
solos todos esos casos ni precisión física». Ambas advertencias se cumplieron al pie de la
letra —cada documento de evidencia repite el caveat— y ninguna se convirtió en una
exigencia de capturar más días. El resultado es un hito cerrado sobre una muestra de la
que su propia documentación dice que no basta.

### 5.2 La puerta de movimiento fluido, medida de verdad

La puerta 3 de `MATRIZ-CIERRE-MADRID.md:21` exige que «el tren no salte cada 20 s». La
evidencia que la cierra (`mp-020-inspeccion-navegador.md:36-68`) es **una circulación**
—`19656`, C5— seguida 60 s con 13 muestras intermedias, **todas con método
`extrapolated_from_last_anchor` y sin que llegara ni un ancla nueva**: es el cliente
evaluando la envolvente desde un ancla congelada de hace 2 minutos. Mide que el cliente
implementa la fórmula del contrato (lo hace, con 6,6 cm de error). **No mide el salto**,
porque el salto ocurre precisamente cuando llega el ancla siguiente y desmiente la
extrapolación.

Lo he medido yo, con el código de producción y los dos cortes del kit
(`scratch/aud01_snap.py`): para las **44 circulaciones map-matcheables presentes en ambos
cortes**, comparo la posición que el cliente habría dibujado evaluando la envolvente del
ancla de `1532` durante los 77 s reales de separación, contra el progreso del ancla de
`1533`:

```
|salto| p50 = 1 237 m · media = 1 295 m · máx = 3 274 m
a la cadencia real del feed (~30 s): ~482 m (p50), ~1 276 m (máx)
```

De esas 44, **31 no cambiaron ni coordenada bruta ni progreso proyectado** entre los dos
cortes (`v_real = 0,00 m/s` exacto) mientras la envolvente las conducía a 10–30 m/s; solo
**13 se movieron de verdad**, y una de esas trece (`20846`) retrocedió 510 m. La puerta no
se cumple, y no podía detectarse con la prueba que se usó para cerrarla.

> **Corrección de la revisión (Codex Sol · High).** Una versión anterior de este documento
> decía «26 no se movieron». Era un recuento mío a ojo de la tabla impresa, y estaba mal:
> el recuento programático da **31 quietas / 13 en movimiento**. La definición que uso es
> `v_real == 0,00 m/s` exacto, es decir progreso map-matcheado idéntico en los dos cortes
> (ni la coordenada de origen ni su proyección cambian); `scratch/aud01_snap.py` imprime
> ahora ese par de recuentos directamente para que no vuelva a depender de una lectura
> visual.

### 5.3 El defecto de corrección que ese salto revela

Investigando el origen del salto encontré algo peor que un error de calibración. De los
121 vehículos del corte `1533`, **49 están observados antes de la hora de salida de su
propio viaje** (`aud01_coverage.py` / `aud01_window.py`): unidades estacionadas en la
estación de origen, con mediana de 16–30 min de antelación y máximo 39 min. De esas 49,
**17 están en patrones con corredor validado**, y para esas 17 el contrato publica una
`ProgressEnvelope` que las pone en marcha (`aud01_envelope_predeparture.py`):

```
trip_id          antelación  progreso ancla   speed_mps  avance en 190 s  dwell_until
1023V20478C4b       38.6 min         32.5 m      30.00         5700.6 m  None
1023V19689C5        36.6 min         98.3 m      20.95         3981.3 m  None
1023V20285C4a       29.6 min         68.4 m      21.89         4159.4 m  None
...  (17 filas, todas con dwell_until = None)
peor caso: 1023V20478C4b — 38,6 min antes de salir, 30,00 m/s (108 km/h), 5 701 m
```

Causa raíz, confirmada en el código: `_envelope` calcula
`temporal_offset_s = anchor_s - schedule.seconds_at_progress(anchor_progress_m)`
(`packages/movement/rendering.py:171`). Con el progreso ≈ 0 de un tren en su origen,
`seconds_at_progress(0)` devuelve la hora de la primera parada
(`schedule.py:107-108`), de modo que un tren presente 38 min antes se modela como un tren
que va **38 min adelantado** sobre su horario, y la envolvente le concede la velocidad del
horario para los siguientes 190 s —el horizonte **efectivo** desde el ancla: los 180 s
configurados en `stale_after_s` más los 10 s de desfase con que el snapshot se construye
tras el corte, igual que en la evidencia de MP-019—. No hay espera que lo frene porque
`dwell_end_seconds(0)` solo devuelve algo si el horario declara espera en la primera
parada, y el GTFS la declara en el 9,9 % de las paradas. Y nada aguas arriba lo filtra:
`circulation_status` es de granularidad **día** —«el `service_id` del viaje está programado
para la fecha de servicio actual», `schemas.py:49-56`— y no distingue «todavía no ha
salido».

Esto es justo lo que el anexo vinculante prohíbe: «parada en estación y transición a
`stale_frozen` cuando expira la confianza», «sin convertir los saltos de Renfe entre polls
en velocidad real» (`ANEXO-CRITICO-POSICION-Y-RELOJ.md:22,24`). No es teletransporte —es
movimiento falso **continuo y suave**, que ninguna prueba busca porque todas las pruebas
verifican suavidad, no que el movimiento deba existir.

---

## 6. ¿Se confunde cobertura de catálogo, geográfica y de posicionamiento?

**Sí, en la matriz vinculante de cierre, y de una forma que el propio documento de origen
del kit ya había advertido diez días antes.**

El documento que originó MP-016 dice, sobre el reparto por línea de vehículos del corte:

> «El reparto anterior mide coincidencia con catálogo, **no cuántos trenes programados
> operaban** ni cuántos iban en hora.»
> — `docs/hitos/hito-03/referencia/01-auditoria-live.md:22`

Y `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:8` pide explícitamente la otra medida:
«Medir cobertura de **unión contra servicios programados** y resolución de `route_id`» —
dos cosas distintas, y por eso §3 del mismo documento exige
`scheduled_trip_instances`, `feed_vehicle_observations`, `resolved_trip_instances` **y,
por separado**, `route_coverage_numerator/denominator/pct`.

Lo entregado (`apps/api/tools/build_closure_matrix.py:213-215`):

```python
"route_coverage_numerator": numerator,      # resolved_by_line[line_id]
"route_coverage_denominator": denominator,  # len(feed_rows) == observaciones del corte
"route_coverage_pct": pct(numerator, denominator),
```

El numerador son los viajes observados que resuelven contra el GTFS; el denominador, las
observaciones que resuelven contra el GTFS. Es la misma pregunta dos veces, y por tanto
**100 % por construcción**: `mp-022-coverage.md:5` publica «Cobertura de resolución
ponderada: **121/121 (100.0 %)**» y las doce líneas con GPS marcan `100.0%` en la columna
titulada «Cobertura ruta». La medida que el kit pedía no se calculó nunca.

La he calculado (`scratch/aud01_coverage.py`), enumerando con
`packages.gtfs.scheduled_trip_instances_for_date` las instancias **en curso** en el
instante del corte (salida ≤ instante ≤ última llegada):

```
--- corte 1533 (2026-11-20T15:33:21+01:00) ---
  instancias programadas del día de servicio : 1299
  instancias programadas EN CURSO al instante: 73
  viajes observados distintos                : 121
  observados que están EN CURSO por horario  : 65
  COBERTURA REAL DE POSICIONAMIENTO          : 65/73 = 89.0%
    C1 1/2 = 50% · C10 6/10 = 60% · C2 9/10 = 90% · C3 8/9 = 89%
    C4a 6/6 = 100% · C4b 5/6 = 83% · C5 16/16 = 100% · C7 7/7 = 100%
    C8a 3/3 = 100% · C8b 4/4 = 100%
```

Tres conclusiones que la matriz entregada no permite sacar y esta sí:

1. La cobertura real es **89 %**, no 100 %. Es un buen número, y decirlo bien vale más que
   decir 100 %: 100 % invita a la pregunta «¿entonces por qué faltan trenes?».
2. **No es homogénea por línea** (C1 50 %, C10 60 % frente a C5 100 %), que es exactamente
   lo que `HITO_3_BACKLOG.md:36` pedía confirmar empíricamente —«podría no ser así, y si
   no lo es, debe documentarse como hallazgo»— y nadie midió.
3. Poner `scheduled_trip_instances` (144 para C1, **del día entero**) al lado de
   `feed_vehicle_observations` (7, **de un instante**) en la misma fila invita a leer
   «7 de 144 = 5 %», que es falso en la dirección opuesta. El denominador correcto —73 en
   curso— no aparece en ninguna columna.

**Un segundo defecto de la misma matriz:** las columnas obligatorias
`position_age_p50_s`/`position_age_p95_s` valen **10.0 en las doce líneas**, porque se
calculan como `captured_at + timedelta(seconds=10) - gps_observed_at`
(`build_closure_matrix.py:135,163`) sobre un corte en el que todas las observaciones
comparten timestamp. No son una distribución medida: son una constante elegida por el
desplazamiento de 10 s que la herramienta inyecta. Dos columnas exigidas por el criterio
de aceptación se satisfacen con un artefacto.

**Lo que sí está bien, y conviene no romper:** `drawable_positions` y `matched_positions`
se mantienen como columnas separadas y la sección de definiciones advierte que
«`drawable_positions` […] No equivale a map matching» y que
«`unknown_reason_count`: cero no significa cobertura geométrica plena»
(`mp-022-coverage.md:42,44`). La distinción conceptual está entendida; lo que falla es la
única columna que lleva la palabra «cobertura» en el nombre.

---

## 7. ¿Qué impide publicar Madrid Pulse hoy mismo?

Concreto, en orden de esfuerzo creciente. Ninguno es «falta madurez».

1. **El README dice que el producto no existe.** `README.md:23`: «El proyecto está en
   **MP-001 — Fundación del repositorio** […] Todavía **no hay código de producto**». Lo
   mismo en `docs/ARCHITECTURE.md:3` («Ningún componente aquí descrito está implementado
   todavía») y `docs/DATA_MODEL.md:3` («propuesta candidata, no implementada», con dos
   migraciones aplicadas). El insumo del propio kit lo señaló el 2026-11-20
   (`referencia/01-auditoria-live.md:2`) y pasó por siete tareas sin corregirse. Coste de
   arreglo: minutos. Impacto si se publica sin arreglarlo: la puerta de entrada
   del repositorio desmiente el producto.
2. **El mapa base es un servicio operativo ajeno, sin registrar.**
   `apps/web/src/map/MapView.tsx:195` consume `https://tile.openstreetmap.org/{z}/{x}/{y}.png`,
   la capa estándar de la OSMF, que se rige por su propia **política de uso del servicio**
   —distinta de la ODbL de los datos—. `docs/legal/DATA_SOURCES.md` registra
   `osm.rail_geometry` (Overpass, datos) pero **no existe ninguna fila para el servicio de
   teselas**, ni se menciona esa política en `LICENSE_MATRIX.md`. Es la única laguna legal
   que he encontrado, y está precisamente en el eje del que el proyecto hace bandera.
   Publicar con tráfico real sobre esa capa es el riesgo de terceros más concreto del
   repositorio.
3. **No hay licencia de código decidida.** DEC-002 sigue `Pendiente` («Antes de hacer
   público el repositorio»), igual que DEC-003 (visibilidad). Son gates del propietario,
   no de los agentes, pero bloquean literalmente la publicación.
4. **El coste por espectador no escala** (§3.2): ~30 espectadores concurrentes por núcleo,
   sin pool (DEC-038) y sin snapshot en CDN pese a ser principio arquitectónico declarado.
5. **El catálogo caduca en silencio.** La comprobación de vigencia del GTFS solo corre al
   arrancar el proceso (`apps/api/gtfs_source.py:158`, dentro de `load_network`, llamado
   una única vez desde `lifespan`). El ZIP del kit vence el **2026-12-19** (verificado con
   `aud01_validity.py`). Un proceso vivo el 20 de diciembre servirá un catálogo caducado
   sin que la guardia dispare, y no hay trabajo de refresco en `infra/operate/` (solo
   colector y archivo diario).
6. **Sin pruebas de carga con red real.** Todo el benchmark es `TestClient` en proceso
   (`mp-022-benchmark.md:18`, declarado). No hay ninguna medida con ASGI + red +
   concurrencia, que es la única que importa para publicar.
7. **El replay no es reproducible por un tercero.** `data/` está fuera de Git por diseño,
   así que un clon limpio puede arrancar `live` (vía `fetch_gtfs_static`) pero no puede
   reproducir ni un solo escenario de la evidencia del hito. Correcto respecto al tamaño y
   la licencia; incompatible con «aplicación local reproducible» como entregable
   (`PROMPT-UNICO-ORCA.md:21`) para alguien que no tenga el ZIP del kit.

No bloqueantes, pero visibles al primer usuario madrileño: las líneas no llevan su color
oficial (§6 de hallazgos, `AUD01-P2-012`) y 8 de 12 líneas no tienen trazado dibujado.

---

## 8. Via Península y Valfiguer: qué se entendió y qué se quedó a medias

### Via Península — se entendió el principio y no la mecánica que lo hace posible

**Bien entendido.** «Posición del tren y geometría visual son dos problemas distintos»
(`deep-research-report.md:31`) está implementado con más rigor que en la referencia: tres
coordenadas separadas y contractuales, y un patrón sin corredor que **nunca** se proyecta
sobre otro (`gtfs_source.py:97-117`). También se respetó el *clean-room*: no hay rastro de
código AGPL (DEC-008/NOGO-002), y la reimplementación es genuinamente independiente.

**A medias.** Via Península resuelve la geometría con **un proceso diario que construye
las geometrías y los viajes de toda la red** (`deep-research-report.md:29`). Madrid Pulse
tomó el principio («geometría es otro problema») y no la mecánica («y por eso necesita una
tubería que la produzca a escala de red»): 7 relaciones OSM congeladas como fixtures
versionadas, con el mapa `route_id → relación` y las salvedades por patrón escritos **en
código Python** (`packages/geo/madrid.py:19-60,62-82`). Es excelente para
reproducibilidad y auditoría —cada fixture tiene manifiesto, SHA-256 y comando— y es la
razón estructural de 28/103: añadir una línea exige editar un paquete compartido, no
ejecutar un proceso.

**Mal leído.** El patrón «publicar snapshots en CDN» se registró como principio
arquitectónico (`ARCHITECTURE.md:68-69`) citando su razón correcta, y después se trató como
«futuro» durante tres hitos mientras se construía exactamente lo que ese patrón evita:
una API que calcula el estado completo en cada petición de cada espectador. La lección de
Via Península no era «un CDN estaría bien algún día»: era que el coste de servir el mapa no
debe depender de cuánta gente lo mire.

### Valfiguer — se entendió casi todo, incluida la parte no obvia

**Bien entendido, y conviene decirlo:** los cinco campos de salud por feed se
implementaron completos, incluidos los dos que son fáciles de omitir —
`unchanged_for_s` (el feed responde pero el contenido no cambia) y `rejected`
(`apps/api/schemas.py:59-67`)—. Y la deduplicación por hash de payload completo
(ADR-0010) implementa la lección de volumen correcta: 47 actualizaciones idénticas del
corte `1533` no se reinsertan **y no resetean la edad del dato**
(`mp-019-tres-snapshots-replay.md:29-31`), que es el matiz que hace útil la deduplicación
en vez de peligrosa.

**A medias.** Valfiguer guarda «cada cambio de posición, estado o retraso» con **90 días
de retención declarada**; Madrid Pulse archiva con más rigor (idempotente, con
cuarentena) y **sin política de retención decidida** (DEC-004 `Pendiente`). Un histórico
sin retención declarada no es un histórico consultable: es un directorio que crece.

**Mal leído.** El informe de origen convirtió la regla de honestidad de Valfiguer/Niltra en
una norma excelente —`deep-research-report.md:116-124`: no publicar «87 % de puntualidad»
sino «87 % de los observados con delay disponible; cobertura del feed 78 %»— y el producto
la cumple en la UI (`ExploreView.tsx:193-207`, numerador y denominador siempre juntos).
Pero la misma disciplina **no se aplicó a la propia cobertura**: la única columna del
cierre que se llama «cobertura» es la tautológica (§6). La regla se aplicó al indicador
que venía con ella y no al indicador nuevo.

---

## 9. Requisitos contradictorios, innecesarios, incompletos o perjudiciales

Citados textualmente, con archivo y línea. Son los documentos que originaron el trabajo,
no el trabajo.

### 9.1 Contradicción central del Hito 3

| Documento | Cita textual | Conflicto |
|---|---|---|
| `PROMPT-UNICO-ORCA.md:11` | «cerrar el hito con un **mapa de toda Cercanías Madrid**, inmersivo, map-first, responsive y navegable, no solo C5» | — |
| `MATRIZ-CIERRE-MADRID.md:21` | «**Sensación de movimiento fluido**: el tren no «salta» cada 20 s» | Exige movimiento, que requiere corredor |
| `docs/TASKS.md:443` | «matriz de cobertura cubre los patrones de las 12 líneas, **mayoría `pending` honesto**, no fabricado» | **Pre-autoriza que la mayoría no tenga corredor** |
| `docs/STATUS.md:832` | «Mínimo real a descargar/verificar: revalidar C5 […] un ramal de C4 […] y un tramo compartido» | Fija el alcance en 3 de 12 líneas |

Las cuatro se cumplieron. Son incompatibles entre sí y nadie tenía la obligación de
notarlo, porque cada tarea responde solo de su propia fila.

### 9.2 Criterios que no pueden fallar (el defecto de diseño más dañino)

> «La inexistencia comprobada de GPS o de trazado fiable no autoriza inventar datos:
> **documentar el gap** y mantener acceso al horario/tablero; si impide el objetivo
> funcional, declararlo `PARTIAL`/`BLOCKED` en vez de DONE.»
> — `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:40`

> «Cualquier línea ausente del mapa **sin causa documentada**, pérdida de selección, falsa
> posición observada o backend no reproducible bloquea `DONE`.»
> — `MATRIZ-CIERRE-MADRID.md:15`

> «Si una **condición fundamental** falla, no declares DONE» — `PROMPT-UNICO-ORCA.md:19`

Ninguna define qué es «impedir el objetivo funcional» ni «condición fundamental», y las
dos primeras hacen de *documentar* la condición suficiente. Con esa redacción, un hueco
documentado nunca bloquea y «fundamental» lo decide quien cierra. Esto explica, sin
necesidad de suponer mala fe en nadie, cómo una cadena con 28/103 de geometría cierra con
«las nueve puertas tienen evidencia» (`mp-022-dossier-integracion.md:15`). La redacción
correcta habría sido un umbral: *«si menos del X % de los patrones de una línea tiene
corredor validado, esa línea es PARTIAL»*.

### 9.3 Requisito perjudicial por omisión: dos universos, un solo denominador

`AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:5-8` define correctamente «dos universos de
circulación, dos denominadores», y §3 lista las columnas obligatorias **sin definir
`route_coverage_numerator/denominator`**. La única columna llamada «cobertura» quedó sin
definición en un documento vinculante que define las otras veinte. El resultado es §6.

### 9.4 Requisito innecesario que consumió atención

`MATRIZ-CIERRE-MADRID.md:9` y `docs/TASKS.md:407` elevan a criterio de cierre reproducir
los conteos congelados: «119 vehículos Madrid, 119 matches, **49 `SKIPPED` sin `arrival`**».
Medí qué hay detrás de ese 49 (`python3 -c` sobre las fixtures): los 49 marcadores viven en
**3 de 474 entidades** (0,6 %), y Renfe publica **una sola** `stopTimeUpdate` para 462 de
las 474, con `trip.delay == arrival.delay` en **465 de 465** casos comprobables. Es decir:
el número que daba nombre a la tarea mide un detalle de 3 circulaciones, mientras el
contrato canónico descarta el array por parada entero (`packages/contracts/normalize.py:58-72`)
y ADR-0014 cierra reconociendo que «el `stop_time_update` por parada […] **no** está
persistido en el modelo canónico» y que por tanto «no hay evidencia directa de `SKIPPED`
por parada». La tarea cumplió su criterio (el parser ya no revienta, que era el P0 real) y
el producto sigue sin poder decir «esta parada se omite».

### 9.5 Deriva de gobernanza

> «Hito 2 entrega la arquitectura extensible y el piloto C5 poblado; **Hito 3 planifica (no
> implementa)** la cobertura de toda la red» — `docs/adr/0011-public-scope-vs-technical-pilot.md:24`
> (estado: **`Aceptado`**)

Hito 3 implementó la red completa. El cambio de alcance es legítimo —lo autorizó el
propietario— pero ADR-0011 nunca se enmendó, `docs/PLAN.md` nunca recibió una fase ni un
*exit gate* para MP-016→MP-022 (su última fase sigue siendo «F10 — Expansión (fuera de
alcance de MP-001 a MP-015)»), y el propio `PLAN.md:86` lista como gate transversal
«Ninguna decisión arquitectónica cambia sin ADR». La consecuencia práctica no es
formalismo: **el Hito 3 es el único de los tres que se ejecutó sin puerta de salida
escrita en el plan**, y por eso su cierre se evaluó solo contra el kit externo.

### 9.6 El backlog propio que se perdió

El proyecto escribió su propio Hito 3 durante MP-015, con el contexto completo del
repositorio (`docs/HITO_3_BACKLOG.md`, 9 áreas). El kit que lo sustituyó fue redactado
**sin acceso al repositorio**, y lo dice:

> «No se ha inspeccionado el clon local del propietario ni ejecutado su aplicación en esta
> revisión.» — `docs/hitos/hito-03/REVISION-Y-DECISIONES.md:3`

Tres áreas del backlog propio no reaparecen en ningún criterio de MP-016→MP-022:

- **Área 5** (`:29-32`): escalabilidad con muchos trenes y «evaluar si el patrón de
  snapshot/CDN se vuelve necesario en este punto» → §3.2.
- **Área 6** (`:36`): «Confirmar empíricamente (no asumir) que todas las líneas del núcleo
  Madrid tienen el mismo nivel de instrumentación en el feed» → §6, medido aquí por primera
  vez (C1 50 %, C10 60 %).
- **Área 8** (`:42-44`): «validarse contra datos reales […] con el mismo rigor empírico que
  MP-002/MP-003 aplicaron a C5 — no se asume que otra línea se comporta igual que C5» →
  §5.1, el hito se validó con dos cortes de un día.

Las tres son, exactamente, los tres huecos mayores de este informe.

---

## 10. Hipótesis refutables para AUD-08 / AUD-09, y dos preguntas exploratorias

**Ocho hipótesis refutables** (H1, H2 con sus dos mitades, H3, H3b, H4, H5, H7a, H7b) y
**dos preguntas exploratorias** (H6, H8) que **no** se presentan como hipótesis porque hoy
no tienen criterio de refutación posible.

Cada hipótesis trae un **umbral numérico explícito** que la refuta, y el estadístico del
umbral coincide con el tipo de afirmación que hace (proporción contra proporción, mediana
contra mediana). Cambios respecto a la ronda anterior, todos por objeciones del revisor:

- **H1** afirmaba una proporción y se refutaba con una mediana: ahora es una afirmación
  sobre medianas (`p50 ≤ 200 m` la refuta), con la variante por proporción separada como
  **H1b**.
- **H2a** es una afirmación **universal** sobre los seis instantes, así que su criterio es
  explícitamente «**≥ 1 de 6 por debajo del 10 %**», no «los seis».
- **H3** define ahora qué es «persistente» (**≥ 8 de 10 sondeos consecutivos** de la misma
  franja) y cuándo queda refutada (**≤ 1 línea** cumpliéndolo), además de declarar que
  omite las líneas con denominador cero.
- **H4** subió su umbral de refutación de `< 10 %` a **`< 25 %`** para eliminar la banda
  muerta del 10–30 % en la que no se confirmaba ni se refutaba.
- **H5** fija un **margen de equivalencia** (una diferencia `< 20 puntos porcentuales` la
  refuta) y un mínimo de potencia (**n ≥ 30**).
- **H6** y **H8** se **reclasifican como exploratorias**: una tasa de acierto agregada no
  puede refutar una afirmación sobre «la UI» en bloque sin desagregar por canal (H6), y
  «valor percibido» no tiene todavía métrica primaria acordada (H8). Ambas declaran qué
  haría falta para volverse refutables (desagregación por canal y métrica primaria
  declarada de antemano, más **n ≥ 30**).
- **H3b** y **H7a/H7b** vienen de partir H3 y H7 en la ronda anterior; H7b conserva su
  único umbral (`< 10×`) que cierra la banda 5×–10×.

Cada fila declara además **qué parte del baseline es medida y qué parte no**. Cuatro (H1,
H2a, H3, H4) tienen evidencia parcial a favor en §3-§6 sobre las capturas congeladas; H7a
está derivada aritméticamente, no medida; H5 no tiene ninguna evidencia todavía.

| ID | Hipótesis | Qué la refutaría | Experimento |
|---|---|---|---|
| **H1** | Sobre **pares ancla-a-ancla consecutivos de la misma circulación** (misma identidad vehículo+viaje+día de servicio, dos observaciones sucesivas del feed en vivo), la **mediana** de la corrección de posición al llegar la segunda supera los **200 m**. | **`p50 ≤ 200 m`** sobre ≥ 500 pares ancla-a-ancla consecutivos reales. *(Estadístico alineado con la afirmación: la versión anterior afirmaba una proporción —«en más del 50 % de los pares»— y la negaba con una mediana, dos cosas distintas. Queda como afirmación sobre medianas. La variante por proporción, si se quiere medir también, es **H1b**: «la corrección supera 200 m en > 50 % de los pares», refutada por **`≤ 50 %`**.)* | Colector en vivo ≥ 2 h; por cada par, registrar la posición que la envolvente del primer ancla predecía para el instante del segundo, y el progreso map-matcheado del segundo. **Límite del baseline, explícito:** mi p50 de 1 237 m sale de **un único par** de capturas congeladas separadas 77 s (`aud01_snap.py`), no de pares consecutivos en Live; el escalado a ~30 s es aritmético. No generalizo la fixture a Live: eso es precisamente lo que H1 pone a prueba. |
| **H2** | El contrato pone en movimiento circulaciones que no han salido. Dos partes separadas: **(H2a, empírica)** en **cada uno** de los seis instantes medidos, la proporción afectada sobre las circulaciones con corredor validado es **≥ 10 %**; **(H2b, de corrección)** acotar `temporal_offset_s` o añadir comprobación de ventana de viaje la lleva a **0 %** sin suprimir movimiento legítimo. | H2a: **≥ 1 de los 6 instantes con < 10 %** basta para refutarla —es una afirmación universal sobre los seis, no un promedio, así que un solo contraejemplo la tumba—. H2b: que la corrección deje **alguna** circulación pre-salida con `speed_mps > 0`, o que anule el avance de **≥ 1** circulación que sí estaba en marcha. | H2a: repetir `aud01_envelope_predeparture.py` sobre 6 capturas nuevas en franjas declaradas (07:30, 09:00, 13:00, 18:30, 21:00, 23:30 locales). H2b: aplicar la corrección y comparar el conjunto de circulaciones con `speed_mps > 0` antes y después. Baseline: **17/44 = 38,6 %** en el corte `1533` — un solo instante (15:33 local), no una media del día. El abandono de «cualquier instante diurno» es deliberado: la proporción depende de la franja y de cuántas unidades estén estacionadas esperando salida. |
| **H3** | **Al menos dos líneas** tienen cobertura de posicionamiento (observados en curso / programados en curso) **< 70 % de forma persistente**, donde **persistente = en ≥ 8 de 10 sondeos consecutivos** de la misma franja horaria con denominador > 0. | **≤ 1 línea** cumpliendo el criterio de persistencia (es decir: si solo una línea queda por debajo del 70 % en ≥ 8 de 10 sondeos, H3 queda refutada tal como está escrita, y la observación se reporta como hallazgo de una sola línea, no como patrón de red). | `aud01_coverage.py` sobre ≥ 10 capturas de la misma franja repartidas en ≥ 3 días. Baseline: C1 50 %, C10 60 % en **un** sondeo del corte `1533` — un solo punto no establece persistencia, que es la razón de fijar 8 de 10. **Limitación declarada:** el cálculo **omite las líneas con denominador cero** (C4 no tenía ninguna instancia en curso en ese corte), así que «línea» significa «línea con denominador > 0 en ese sondeo»; una línea sin servicio programado en el instante no cuenta ni a favor ni en contra. |
| **H3b** | El global de cobertura de posicionamiento es estable: no se desvía más de 10 puntos entre capturas de la misma franja horaria. | Una desviación **> 10 puntos** entre dos capturas cualesquiera de la misma franja. | Mismo conjunto de capturas que H3, agregando por franja. Baseline: **un solo punto**, 89,0 % a las 15:33 — insuficiente por sí mismo para afirmar ninguna estabilidad, que es la razón de separar esta hipótesis de H3. |
| **H4** | El horizonte de extrapolación hace que **≥ 30 %** de las circulaciones con envolvente activa se dibujen atravesando una estación sin detenerse. | **< 25 %** de travesías sin `dwell_until` que las cubra. *(Umbral de refutación subido para que sea coherente con la afirmación: el «< 10 %» anterior dejaba una banda muerta del 10–30 % en la que la hipótesis no se confirmaba ni se refutaba. Con 25 % la banda muerta queda en 5 puntos, y el criterio por proxy de `dwell_until` deja de ser una vía alternativa de refutación: es la propia medida.)* | Para cada circulación con envolvente, comprobar si `[progress_m_at_reference, max_progress_m]` contiene el progreso de alguna parada y si `dwell_until` la cubre; contar la proporción sobre el total de circulaciones con envolvente. **Baseline solo indirecto, declarado como tal:** no he medido ninguna travesía de estación; lo que he medido son los dos ingredientes (intervalo mediano entre paradas de **180 s** y espera declarada en el **9,9 %** de las paradas, `aud01_stopgap.py`) frente al horizonte, que es de **180 s configurados** y **190 s efectivos** desde el ancla. La hipótesis existe precisamente porque la consecuencia no está medida. |
| **H5** | El color no oficial degrada la identificación de línea en el mapa: la tasa de identificación correcta con la paleta hash es **≥ 20 puntos porcentuales inferior** a la obtenida con `route_color`. | Una diferencia **< 20 puntos porcentuales** entre ambas condiciones (margen de equivalencia explícito: por debajo de 20 puntos se considera que el color no es el factor dominante y H5 queda refutada). **Potencia mínima para que el resultado cuente: n ≥ 30 participantes.** Con n < 30 no se declara ni confirmada ni refutada: se reporta como exploratoria. | Tarea de identificación **A/B** sobre dos capturas idénticas salvo la paleta, con el nombre de línea oculto. Dato duro independiente de la prueba: `route_color` existe en `routes.txt`, se parsea (`Route.color`) y no se expone en `/api/v1/catalog`. |
| **H6** | *(Pregunta exploratoria, **no hipótesis refutable** en su estado actual.)* ¿Transmite la UI la diferencia entre GPS reciente, avance extrapolado y posición congelada? | **No procede: sin criterio de refutación.** Un fallo de clasificación no distingue entre causa de color, de símbolo, de texto o de vocabulario («extrapolado», «ancla»), así que ningún umbral sobre la tasa de acierto refutaría una afirmación sobre *la UI* en bloque. Para convertirla en refutable hace falta antes **desagregarla por canal** (una hipótesis por símbolo, texto y color) y fijar **n ≥ 30** por condición. Hasta entonces se reporta como exploratoria y **no** como hipótesis. | Tarea de clasificación sobre una captura con los tres estados presentes (`anchor`, `extrapolated_from_last_anchor`, `stale_frozen`), con n = 5 como sondeo previo para decidir si merece la pena el diseño desagregado. Cruzar con el hallazgo P0-1 de AUD-05 (edades negativas en replay), que es un defecto de dato y no de presentación. |
| **H7a** | **Capacidad:** un proceso no sostiene 100 espectadores concurrentes a 10 s de sondeo con p95 < 1 s. | 100 concurrentes con **p95 < 1 s** sin ningún cambio. | `wrk`/`locust` contra `uvicorn` real (no `TestClient`) con 1/10/50/100 clientes. Baseline: p50 254,73 ms en proceso, del que ~66 ms son abrir conexión (DEC-038). |
| **H7b** | **Ganancia:** servir un snapshot pre-generado reduce la carga de backend por espectador **al menos 10×**. | Una mejora medida **< 10×**. (La versión anterior dejaba sin cubrir la banda 5×–10×: pedía «más de un orden de magnitud» y la refutaba con «< 5×», de modo que un resultado de 7× no la confirmaba ni la refutaba. Queda un único umbral: ≥ 10× la confirma, < 10× la refuta.) | Repetir la medida de H7a sirviendo un snapshot pre-generado desde disco/CDN y comparar coste de CPU por petición servida. |
| **H8** | *(Pregunta exploratoria, **no hipótesis refutable** en su estado actual.)* ¿Está la diferenciación real del producto en la capa analítica (History/Explore con denominadores explícitos) más que en el mapa? | **No procede: sin criterio de refutación.** «Valor percibido» no tiene todavía una métrica acordada, y las tres señales operacionales que propongo abajo pueden apuntar en direcciones distintas sin que nada diga cuál manda. Para convertirla en refutable hacen falta dos cosas que hoy no existen: **una métrica primaria declarada de antemano** (propongo la señal 1, «qué vista reabren para una consulta propia») y **n ≥ 30** con orden contrabalanceado. Hasta entonces se reporta como exploratoria y **no** como hipótesis. | Entrevista estructurada con **orden contrabalanceado** (la mitad recorre Live→History, la mitad History→Live; la versión anterior tenía **sesgo de orden**: siempre Live primero, lo que favorece a lo visto en último lugar). Señales operacionales a registrar: (1) **primaria** — qué vista eligen reabrir cuando se les pide una segunda consulta propia; (2) si mencionan numerador/denominador sin que se les pregunte; (3) qué vista nombran al describir el producto a un tercero. Con n = 5 es orientación para decidir el rumbo de los hitos siguientes, nunca conclusión. |

---

## 11. Hallazgos

Formato de la sección 8 del encargo. Severidad: **P0** bloquea publicar o falsea un dato
mostrado; **P1** rompe un criterio declarado o impide publicar sin trabajo real; **P2**
riesgo real acotado o deuda de proceso.

---

### AUD01-P0-001 — El contrato temporal publica movimiento para trenes que no han salido, y el salto al refrescar el ancla mide 1,2 km de mediana

- **Identificador:** `AUD01-P0-001`
- **Componente:** `packages/movement/rendering.py` (`_envelope`) + contrato ADR-0014 §2;
  consumido por `apps/api/snapshot.py` y `apps/web/src/domain/movement.ts`.
- **Severidad:** **P0** — el mapa muestra como «en marcha, a 108 km/h» un tren
  físicamente detenido en su estación de origen, y la puerta 3 de aceptación
  («el tren no salta cada 20 s») no se cumple.
- **Evidencia reproducible:**
  ```sh
  .venv/bin/python scratch/aud01_envelope_predeparture.py   # 17/121 pre-salida con envolvente
  .venv/bin/python scratch/aud01_snap.py                    # salto p50 1 237 m, máx 3 274 m
  .venv/bin/python scratch/aud01_window.py                  # 49/121 observados antes de salir
  ```
  Alcance exacto: **17 de 121** circulaciones del corte `1533`, es decir **17 de las 44
  map-matcheables = 38,6 %**, con velocidades de envolvente entre **15,52 y 30,00 m/s**
  (55,9–108 km/h). Peor caso medido: `1023V20478C4b`, a **2 319 s = 38,65 min** de su salida
  programada, `speed_mps = 30,00` (108 km/h), **5 700,6 m** de avance autorizado en los
  190 s del horizonte efectivo (190 s = 180 s configurados en `stale_after_s` + 10 s de
  desfase del snapshot), `dwell_until = None` en los 17 casos. Sobre las 44 circulaciones map-matcheables presentes en
  ambos cortes, **31 no cambiaron ni coordenada ni progreso** en los 77 s reales (solo 13
  se movieron, una de ellas hacia atrás) mientras la envolvente las conducía a 10–30 m/s.
- **Archivo/símbolo/dato afectado:** `packages/movement/rendering.py:166-203` (`_envelope`,
  en particular `temporal_offset_s` en la línea 171);
  `packages/movement/schedule.py:106-118` (`seconds_at_progress`) y `:120-133`
  (`dwell_end_seconds`); `apps/api/schemas.py:49-56` (`circulation_status`, granularidad
  día); cortes `data/hito-03/replay/{1532,1533}`.
- **Riesgo de producto:** se muestra como hecho observado un movimiento que no ocurrió.
  Es el único tipo de error que el proyecto declara inaceptable en todos sus documentos
  («no inventar un tren», `MATRIZ-CIERRE-MADRID.md:42`). A la cadencia real del feed el
  usuario ve un tren arrancar, recorrer ~500–900 m y volver de golpe a la estación cada
  ~30 s.
- **Causa raíz (confirmada en código):** `_envelope` interpreta cualquier desajuste entre
  el instante del ancla y el horario como **adelanto o retraso de la circulación**. Con
  `anchor_progress_m ≈ 0`, `seconds_at_progress(0)` devuelve la hora de la primera parada,
  así que una unidad estacionada 38 min antes de salir se modela como un tren 38 min
  adelantado. No hay freno porque `dwell_end_seconds(0)` requiere espera declarada en el
  horario y el GTFS la declara en el 9,9 % de las paradas (`aud01_stopgap.py`). Y nada
  filtra aguas arriba: `circulation_status` solo comprueba que el `service_id` esté
  programado **hoy**, no que el instante caiga dentro de la ventana del viaje.
- **Alternativas:**
  (A) Acotar `temporal_offset_s` a un rango físicamente defendible (p. ej. ±`operator_delay_max_age_s`
  o el `delay` realmente publicado por el operador) y, fuera de él, emitir `anchor` sin
  envolvente. Mínimo cambio, resuelve el 100 % de los 17 casos.
  (B) Añadir una comprobación de ventana de viaje: si `anchor_at` es anterior a la primera
  salida programada, `speed_mps = 0` con `dwell_until = primera_salida` — semánticamente
  es exactamente lo que ocurre (el tren espera para salir) y reutiliza un campo que ya
  existe en el contrato.
  (C) Derivar `speed_mps` del movimiento observado entre las dos últimas anclas en vez del
  horario. Descartable: convierte los saltos del feed en velocidad real, prohibido en
  `ANEXO-CRITICO-POSICION-Y-RELOJ.md:24`.
  (D) No hacer nada y etiquetarlo. Insuficiente: la etiqueta ya es
  `extrapolated_from_last_anchor` y no impide dibujar 5,7 km de avance falso.
- **Recomendación razonada:** **(B) y (A), en ese orden.** (B) es correcta por significado
  y no inventa nada —un tren antes de su salida está esperando, y `dwell_until` es
  precisamente el campo para declarar una espera—; (A) cierra además el caso simétrico de
  un ancla muy posterior al horario. Ninguna de las dos toca el contrato publicado ni el
  motor de MP-012, solo la traducción de MP-019, así que caben dentro de ADR-0014 sin
  enmendarlo.
- **Prueba necesaria para cerrar el hallazgo:** regresión que, con el ZIP del kit y el
  corte `1533`, exija `speed_mps == 0` (o ausencia de envolvente) para **las 17
  circulaciones nombradas**, y que falle contra el código actual; más la medida de H1/H2
  con feed en vivo ≥ 2 h demostrando p50 de salto < 200 m.

---

### AUD01-P0-002 — El criterio de aceptación admitía de antemano una mayoría sin trazado, y el resultado (28/103) deja al 63,6 % de los trenes sin poder moverse

- **Identificador:** `AUD01-P0-002`
- **Componente:** criterios de aceptación de MP-018/MP-020/MP-022 y `packages/geo` (alcance
  de fixtures), no la implementación.
- **Severidad:** **P0** — la misión de producto no negociable del hito no se alcanzó, y el
  sistema de puertas admitía de antemano un mínimo muy por debajo de ella.
- **Evidencia reproducible:** `docs/evidence/mp-018-corridor-coverage.csv`, recontado por
  línea y estado: **28 `validated` / 3 `partial` / 72 `pending`** sobre 103 filas.
  Los 72 `pending` se reparten en **tres categorías que no deben confundirse**:
  - **67** en C1, C2, C3, C7, C8a, C8b, C9 y C10 — **sin fuente congelada ni
    intento registrado**, accionables adquiriendo geometría;
  - **1** en C8b (`10T0098C8b`) — feed truncado: una única parada residual con
    `stop_sequence` 032/025; no se arregla descargando OSM;
  - **4** en C4b (`10T0016C4b`, sentido opuesto) — **intento real fallido**: se pidió la
    relación OSM `9174512` y Overpass devolvió `HTTP 502` dos veces
    (`docs/STATUS.md:850-852`). Es un límite externo verificado, y la tarea hizo lo
    correcto registrándolo como `pending` en vez de como relación inexistente.

  Consecuencia en el snapshot, en palabras del propio proyecto: «**44 de 119**
  circulaciones tienen coordenada `map_matched` […] Las otras 75 publican su GPS bruto
  etiquetado […] **sin envolvente de progreso**»
  (`mp-019-tres-snapshots-replay.md:50-56`). En el corte `1533`: **44 de 121 se pueden
  mover (36,36 %) y 77 de 121 quedan en punto estático (63,64 %)**.
- **Archivo/símbolo/dato afectado:** `docs/TASKS.md:443` («mayoría `pending` honesto»);
  `docs/STATUS.md:832` («Mínimo real a descargar»); `packages/geo/madrid.py:19-60`
  (`madrid_source_specs`, 5 fuentes para 3 líneas); `apps/web/src/domain/movement.ts:91-96`
  (sin envolvente → `source: "published"`, punto estático).
- **Riesgo de producto:** en 9 de 12 líneas el usuario ve puntos que saltan cada sondeo
  sobre un mapa sin trazado — es decir, exactamente el producto que
  `PROMPT-UNICO-ORCA.md:11` declaraba no negociable evitar. Y como la cobertura geométrica
  no está en ninguna métrica de portada, nada avisa de que el 63,6 % de los trenes está en
  ese régimen. Añadido: el CSV da a los 72 `pending` el mismo `reason`, así que la
  distinción entre el límite externo de C4b, los 67 sin fuente/intento registrado
  y el feed truncado no es recuperable desde el artefacto canónico.
- **Causa raíz (confirmada, con el alcance de la afirmación acotado):** no es técnica para
  los 67 accionables. El alcance de MP-018 se fijó deliberadamente en «C5 + un ramal de C4 + un tramo
  compartido» (`docs/STATUS.md:832`) y su criterio de aceptación admitía «mayoría
  `pending` honesto» (`docs/TASKS.md:443`). **Ninguno de los dos bendijo el número
  28/103**: lo que autorizaron fue un mínimo bajo y una mayoría pendiente sin cuantificar,
  y 28/103 cumple ese mínimo sin haber sido el resultado específicamente aprobado de
  antemano. MP-020 y MP-022 heredaron ese estado y sus puertas de movimiento se cerraron
  con una circulación del 36,36 % que sí tiene corredor. El herramental para resolver los
  67 ya existe y es reproducible (`packages/geo/tools/fetch_fixture.py`,
  `find_route_relations`); el patrón truncado requiere calidad/upstream; los 4 de C4b
  tienen la vía ya congelada en `9174511` en sentido inverso, aunque usarla podría
  situar el tren en la vía contigua equivocada.
- **Alternativas:**
  (A) Descargar y versionar las relaciones OSM de las ocho líneas sin fuente ni intento
  registrado, una tarea por línea y manifiesto ODbL; tratar por separado el feed truncado;
  y congelar `9174512` para los 4 patrones C4b (o documentar la incertidumbre lateral de
  reutilizar `9174511` invertida).
  (B) Sustituir las fixtures por una tubería diaria que las construya (modelo Via
  Península). Resuelve también el mantenimiento, pero es alcance de hito propio y añade
  dependencia operativa de Overpass.
  (C) Usar `shapes.txt` del GTFS como corredor de respaldo donde no haya relación OSM.
  Descartable sin verificación: `deep-research-report.md:31` ya advierte que las
  geometrías GTFS no coinciden con la vía visible.
  (D) Dejarlo y declarar las 9 líneas `PARTIAL` en producto, no solo en una tabla de
  evidencia.
- **Recomendación razonada:** **(A) ahora, (D) mientras dure, (B) como hito posterior.**
  (A) es trabajo acotado y conocido —cada línea es una ejecución del herramental más un
  manifiesto— y es lo que convierte el entregable actual en el producto prometido. (D) es
  obligatorio en el intervalo: si una línea no puede mover sus trenes, el mapa debe decirlo
  en la propia línea, no solo en `mp-022-coverage.md`.
- **Prueba necesaria para cerrar:** matriz regenerada con `geometry_validated_patterns ==
  geometry_total_patterns` para ≥ 10 de las 12 líneas, o causa externa verificada y
  documentada **por patrón** —con un `reason` distinto en el CSV para «límite externo» y
  para «sin intento», que hoy comparten cadena—; y una prueba de producto que falle si una
  línea del catálogo con GPS no tiene corredor **y** la UI no lo declara explícitamente.

---

### AUD01-P1-003 — `route_coverage_pct` es tautológico (100 % por construcción) y la cobertura que el kit exigía medir nunca se calculó

- **Identificador:** `AUD01-P1-003`
- **Componente:** `apps/api/tools/build_closure_matrix.py` y la matriz vinculante de cierre.
- **Severidad:** **P1** — la métrica de portada del cierre del hito no mide cobertura.
- **Evidencia reproducible:** `build_closure_matrix.py:213-215` fija
  `numerator = resolved_by_line[line_id]` y `denominator = len(feed_rows)`; ambos cuentan
  observaciones que ya resolvieron contra el GTFS, por lo que el cociente es 1 salvo
  resoluciones fallidas. Resultado publicado: «Cobertura de resolución ponderada:
  **121/121 (100.0 %)**» y `100.0%` en las doce líneas con GPS
  (`docs/evidence/mp-022-coverage.md:5,9-20`). La medida real, calculada con
  `scratch/aud01_coverage.py`: **65/73 = 89,0 %** en el corte `1533` (C1 50 %, C10 60 %,
  C5 100 %).
- **Archivo/símbolo/dato afectado:** `build_closure_matrix.py:47-49,213-215`;
  `docs/evidence/mp-022-coverage.{csv,md}`; especificación sin definir en
  `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:24`.
- **Riesgo de producto:** un 100 % de «cobertura» en el documento de cierre es la clase de
  cifra que luego se cita fuera de contexto. Y oculta el hallazgo que el propio proyecto
  pedía buscar (`HITO_3_BACKLOG.md:36`): la instrumentación del feed **no** es homogénea
  por línea.
- **Causa raíz (confirmada):** el documento vinculante enumera veinte columnas y define
  diecinueve; `route_coverage_*` quedó sin definición, y se implementó como duplicado de
  `resolved/observations`. El documento de origen del kit ya había advertido la confusión
  («mide coincidencia con catálogo, no cuántos trenes programados operaban»,
  `referencia/01-auditoria-live.md:22`); la advertencia se trasladó al texto de `caveats` y
  no a la fórmula.
- **Alternativas:**
  (A) Redefinir `route_coverage` como `observados en curso / programados en curso`, con el
  nuevo denominador como columna propia (`scheduled_in_progress`).
  (B) Renombrar la columna actual a `feed_resolution_pct` (que es lo que mide) y **añadir**
  la de (A). Conserva la serie histórica.
  (C) Eliminar la columna. Pierde una señal útil (resolución del feed) que sí vale.
- **Recomendación razonada:** **(B).** La resolución del feed es una métrica legítima —mide
  si sabemos atribuir cada observación— y lo único roto es su nombre; la cobertura real
  necesita su propio par numerador/denominador. Las dos juntas son exactamente los «dos
  universos, dos denominadores» que pedía `AMPLIACION:5-8`.
- **Prueba necesaria para cerrar:** test de contrato de la matriz que exija las dos columnas
  y que falle si `route_coverage_denominator == feed_vehicle_observations`; más la medida
  de H3 sobre ≥ 10 capturas de ≥ 3 días.

---

### AUD01-P1-004 — `position_age_p50_s/p95_s` de la matriz vinculante son una constante inyectada, no una medida

- **Identificador:** `AUD01-P1-004`
- **Componente:** `apps/api/tools/build_closure_matrix.py`.
- **Severidad:** **P1** — dos columnas obligatorias del criterio de aceptación se satisfacen
  con un artefacto de la herramienta.
- **Evidencia reproducible:** `mp-022-coverage.md:9-20` da `10.0/10.0` en **las doce
  líneas**. En `build_closure_matrix.py:163` la edad es
  `captured_at + timedelta(seconds=10) - item.timestamps.gps_observed_at`, y en un corte
  congelado todas las observaciones comparten `gps_observed_at == captured_at`: el
  resultado es exactamente el desplazamiento de 10 s elegido en la línea 135.
- **Archivo/símbolo/dato afectado:** `build_closure_matrix.py:135,163`; columnas
  `position_age_p50_s`/`position_age_p95_s` de `mp-022-coverage.{csv,md}`; requisito en
  `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:24`.
- **Riesgo de producto:** la edad de la posición es el indicador con el que un usuario
  decide si creerse un tren. Publicar `10.0/10.0` en las doce líneas como si fuera una
  distribución medida enmascara que en operación real esa distribución es lo que separa
  una línea bien instrumentada de una mal instrumentada.
- **Causa raíz (confirmada):** la métrica es intrínsecamente no medible desde un corte
  congelado de un solo instante; se calculó igualmente en vez de declararse `null` con su
  motivo, que es la convención que la propia matriz aplica a C4 («`null (sin GPS)`»).
- **Alternativas:**
  (A) Emitir `null` con motivo `corte de un solo instante: la edad no es observable` —
  coherente con el tratamiento de C4.
  (B) Calcularla sobre una ventana real de operación (≥ 1 h de colector en vivo) y declarar
  la ventana.
  (C) Dejarlo con un caveat textual. Insuficiente: el CSV es la fuente canónica y un
  consumidor lo lee sin los caveats.
- **Recomendación razonada:** **(A) para cortes congelados y (B) cuando haya ventana real.**
  Declarar `null` cuando algo no es observable es la regla que este proyecto aplica en todo
  lo demás («dato ausente ≠ cero»); la excepción aquí no está justificada.
- **Prueba necesaria para cerrar:** test que, dado un corte de instante único, exija
  `position_age_p50_s is None`; y una corrida de la matriz sobre ≥ 1 h de ingesta real con
  p50/p95 distintos entre líneas.

---

### AUD01-P1-005 — El horizonte de extrapolación (180 s configurados, 190 s efectivos) nació como umbral de frescura «calibrable» y hoy autoriza avance, sin recalibrar y contra la medida real de la red

- **Identificador:** `AUD01-P1-005`
- **Componente:** DEC-010 / ADR-0004 / ADR-0014 §2 / `packages/movement/rendering.py`.
- **Severidad:** **P1** — una afirmación del código es falsa y produce un comportamiento
  visible incorrecto (trenes que no paran en las estaciones).
- **Evidencia reproducible:** `.venv/bin/python scratch/aud01_stopgap.py` sobre el ZIP
  oficial del kit, 501 923 intervalos reales del núcleo Madrid:
  ```
  intervalo salida->llegada siguiente: p50 180s  media 229s  p10 120s  p90 360s
  intervalos <= 180 s (horizonte por defecto): 266490/501923 = 53.1%
  parada (dwell) declarada: p50 0s · fracción de dwell>0: 9.9%
  ```
  Contra la afirmación de `packages/movement/rendering.py:84-85`: «El horizonte por defecto
  (`stale_after_s`, 180 s) acota ese efecto». El valor **configurado** son 180 s
  (`packages/movement/model.py:40`); el horizonte **efectivo** desde el ancla medido en esta
  evidencia son **190 s** (`horizon_end = calculated_at + stale_after_s`, con `calculated_at`
  10 s posterior al ancla), de modo que la ventana real supera el intervalo mediano entre
  paradas en vez de quedarse justo en él.
- **Archivo/símbolo/dato afectado:** `packages/movement/model.py:40`
  (`stale_after_s = 180.0`); `packages/movement/rendering.py:82-85` (afirmación) y
  `:188-194` (`dwell_end_seconds`); `docs/DECISIONS.md` DEC-010;
  `docs/adr/0014-snapshot-and-temporal-contract.md` §2.
- **Riesgo de producto:** el horizonte iguala el intervalo mediano entre paradas, así que
  una extrapolación completa abarca un tramo entre estaciones entero y cruza al menos una
  parada; y como el horario declara espera en el 9,9 % de las paradas, la envolvente casi
  nunca puede detener el tren. Cualquier usuario que conozca su línea ve el tren pasar de
  largo por su estación.
- **Causa raíz (confirmada):** el valor se eligió en DEC-010 para clasificar frescura, con
  la advertencia explícita de que los umbrales «no son verdad de diseño»
  (`deep-research-report.md:181`). ADR-0014 lo reutilizó para un trabajo distinto —cuánto
  tiempo es lícito avanzar— y ningún mecanismo del proceso obliga a recalibrar un umbral
  cuando cambia de papel.
- **Alternativas:**
  (A) Derivar el horizonte del horario de la propia circulación: hasta la siguiente parada
  programada, no un valor fijo. Resuelve el cruce de estaciones por construcción.
  (B) Bajar el horizonte a un valor por debajo del p10 medido (120 s) — p. ej. 60–90 s — y
  congelar antes. Más simple, deja huecos de presentación.
  (C) Poblar `dwell_until` también cuando el horario declara espera cero pero hay una parada
  en el tramo (espera mínima asumida). Fabrica un dato que la fuente no da.
  (D) Mantener el valor actual y corregir la afirmación del docstring (incluida la
  distinción configurado/efectivo). Honesto y no resuelve nada.
- **Recomendación razonada:** **(A), con (D) como mínimo inmediato.** (A) es la única que
  elimina la causa en vez de acotarla, usa solo datos que el horario ya da, y encaja en el
  contrato sin romperlo: `horizon_s` por circulación en vez de constante. Y mientras no se
  haga, la frase de `rendering.py:84-85` debe corregirse porque hoy afirma algo medidamente
  falso.
- **Prueba necesaria para cerrar:** medida de H4 —proporción de circulaciones cuya
  envolvente atraviesa el progreso de una parada sin `dwell_until` que la cubra— con umbral
  < 10 %, más una regresión con el ZIP real que lo fije.

---

### AUD01-P1-006 — El README y dos documentos de arquitectura siguen declarando que no hay producto

- **Identificador:** `AUD01-P1-006`
- **Componente:** documentación de portada del repositorio.
- **Severidad:** **P1** — impide publicar; señalado en el insumo del propio kit y no
  corregido en siete tareas.
- **Evidencia reproducible:**
  - `README.md:23`: «El proyecto está en **MP-001 — Fundación del repositorio** […]
    Todavía **no hay código de producto**. […] el backlog completo MP-001 a MP-015.»
  - `docs/ARCHITECTURE.md:3`: «Estado de este documento: **propuesta validada por
    investigación, pendiente de validación empírica en MP-002 a MP-007**. Ningún componente
    aquí descrito está implementado todavía».
  - `docs/DATA_MODEL.md:3`: «Estado: **propuesta candidata, no implementada**», con
    `infra/migrations/0001_init.up.sql` y `0002_api_batch_indexes.up.sql` aplicadas.
  - `docs/PLAN.md:61`: la última fase sigue siendo «F10 — Expansión (fuera de alcance de
    MP-001 a MP-015)»; no existe fase ni *exit gate* para MP-016→MP-022.
  - Ya señalado el 2026-11-20 en `docs/hitos/hito-03/referencia/01-auditoria-live.md:2`:
    «El párrafo «Estado actual» del README raíz todavía describe MP-001».
  - `.venv/bin/python -c` / `find`: 90 módulos Python y 48 ficheros TS/TSX de producto.
- **Archivo/símbolo/dato afectado:** `README.md:21-23`, `docs/ARCHITECTURE.md:3`,
  `docs/DATA_MODEL.md:3`, `docs/PLAN.md:61-67`, `docs/MVP_READINESS.md` (solo Hito 2).
- **Riesgo de producto:** la puerta de entrada del repositorio desmiente el producto. Para
  cualquiera que llegue —colaborador, revisor externo, empleador— el repositorio dice que
  no hay nada construido. Es además el contraejemplo más caro del principio que el proyecto
  defiende: «la documentación refleja la realidad implementada».
- **Causa raíz (confirmada):** el *exit gate* F9 de `docs/PLAN.md:57-59` («sin deuda de
  documentación pendiente») se declaró cumplido en MP-015 sin que nadie revisara los
  encabezados de estado; y ninguna tarea del Hito 3 tuvo la documentación de portada en su
  lista de ficheros afectados.
- **Alternativas:**
  (A) Actualizar los cuatro documentos y añadir una fase F11 a `PLAN.md` con el *exit gate*
  real de MP-016→MP-022, retrospectivamente declarado.
  (B) Actualizar solo el README. Deja la contradicción en los documentos de arquitectura.
  (C) Añadir una comprobación de CI que falle si `README.md` menciona una tarea `MP-0XX`
  anterior a la última `DONE` de `TASKS.md`.
- **Recomendación razonada:** **(A) + (C).** (A) es trabajo de minutos y desbloquea la
  publicación; (C) es la única forma de que no vuelva a ocurrir, y este proyecto ya
  demostró que la disciplina humana no basta: la advertencia estaba escrita y sobrevivió a
  siete tareas y dos revisiones cruzadas.
- **Prueba necesaria para cerrar:** comprobación automática en `.github/workflows/ci.yml`
  que cruce el estado declarado en `README.md`/`ARCHITECTURE.md` con la última tarea `DONE`
  de `docs/TASKS.md`.

---

### AUD01-P1-007 — El mapa base consume un servicio operativo de la OSMF que no está registrado en `docs/legal/`

- **Identificador:** `AUD01-P1-007`
- **Componente:** `apps/web/src/map/MapView.tsx` y el registro legal de fuentes.
- **Severidad:** **P1** — riesgo de terceros al publicar, en el eje del que el proyecto hace
  bandera.
- **Evidencia reproducible:** `apps/web/src/map/MapView.tsx:190-201` define el único
  `source` del estilo como
  `tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"]`. En
  `docs/legal/DATA_SOURCES.md` la enumeración de fuentes
  (`grep -n '^| \`' docs/legal/DATA_SOURCES.md`) contiene `osm.rail_geometry` —los datos
  vía Overpass— y **ninguna fila** para el servicio de teselas; `LICENSE_MATRIX.md:13,23-26`
  trata la ODbL de los datos y la frontera base derivada/colectiva, no la política de uso
  del servicio.
- **Archivo/símbolo/dato afectado:** `apps/web/src/map/MapView.tsx:195`;
  `docs/legal/DATA_SOURCES.md` (fila ausente); `docs/legal/LICENSE_MATRIX.md`.
- **Riesgo de producto:** la capa estándar de la OSMF se rige por una política de uso del
  servicio distinta de la licencia de los datos, con límites de volumen y requisitos de
  identificación del cliente. La atribución ODbL está correctamente puesta
  (`attribution: "© OpenStreetMap contributors · ODbL"`), lo que cubre la licencia de los
  datos y **no** la política del servicio. Un producto publicado con tráfico real sobre esa
  capa es la clase de incumplimiento que este proyecto creó `docs/legal/` para evitar.
- **Causa raíz (probable):** la frontera «licencia de datos» vs «términos del servicio que
  los sirve» no está contemplada en el modelo de `docs/legal/`: todas las filas de
  `DATA_SOURCES.md` describen conjuntos de datos que se descargan, y el mapa base es el
  único recurso que se consume como servicio en caliente desde el navegador del usuario.
- **Alternativas:**
  (A) Registrar `osm.basemap_tiles` en `DATA_SOURCES.md` con su política de uso, y declarar
  explícitamente que solo es válido para uso local/demo.
  (B) Antes de publicar, sustituir por un proveedor de teselas con términos compatibles con
  el volumen previsto (decisión de coste → gate del propietario, ADR-0007).
  (C) Autoalojar teselas. Coste de infraestructura desproporcionado para el volumen actual.
- **Recomendación razonada:** **(A) ya, (B) como gate de publicación.** (A) cierra la
  laguna documental hoy sin decidir nada; (B) es una decisión de coste y licencia que
  corresponde al propietario y que debe estar resuelta **antes** de que haya un usuario
  externo, no después.
- **Prueba necesaria para cerrar:** fila nueva en `DATA_SOURCES.md` con enlace a la política
  y estado de verificación, y un apartado de «gates de publicación» que la liste junto a
  DEC-002/DEC-003.

---

### AUD01-P1-008 — El coste por espectador no escala y el patrón de CDN que el propio proyecto adoptó como principio sigue sin evaluarse

- **Identificador:** `AUD01-P1-008`
- **Componente:** `apps/api` (snapshot por petición), `apps/web/src/hooks/useSnapshot.ts`,
  `infra/cloudflare/`.
- **Severidad:** **P1** — impide publicar con audiencia; la tarea de evaluarlo estaba
  escrita y no se hizo.
- **Evidencia reproducible:** `docs/evidence/mp-022-benchmark.md:33-40`:
  `/api/v1/snapshot` p50 **254,73 ms**, p95 **418,23 ms**, máx **2 501,02 ms**, con 121
  vehículos y «en proceso con `TestClient`: incluye el código de aplicación y PostgreSQL,
  pero excluye red y servidor ASGI» (`:18`).
  `apps/web/src/hooks/useSnapshot.ts:8`: `SNAPSHOT_POLL_MS = 10_000`.
  DEC-038: «~66 ms de los 68,91 ms de p50 de `/api/v1/health` son establecer la conexión».
  `infra/cloudflare/README.md`: «**Vacío intencionadamente.**»
  Derivado: 0,255 s cada 10 s = **2,5 % de un núcleo por espectador** (≈3,3 % con tablero y
  salud) → **~30 espectadores concurrentes por núcleo**.
- **Archivo/símbolo/dato afectado:** `apps/api/snapshot.py` (`build_snapshot`);
  `apps/web/src/hooks/useSnapshot.ts:8`; `docs/ARCHITECTURE.md:68-69` (principio declarado);
  `docs/HITO_3_BACKLOG.md:32` (tarea no realizada); DEC-038 (abierta).
- **Riesgo de producto:** el producto no puede publicarse para una audiencia sin
  rediseñar su capa de servicio, y el rediseño está descrito en el propio documento de
  arquitectura desde MP-001. Además se desperdician dos tercios de las peticiones: el feed
  cambia cada ~30 s y el cliente sondea cada 10 s.
- **Causa raíz (confirmada):** la pregunta se formuló explícitamente para este hito
  (`HITO_3_BACKLOG.md:32`) y desapareció al sustituir ese backlog por el kit externo; el
  kit mide rendimiento (bien) pero no pregunta por la arquitectura de servicio.
- **Alternativas:**
  (A) Pool de conexiones (DEC-038, resuelve ~66 ms de los 255) + alinear el sondeo con la
  cadencia real del feed (30 s). Barato, mejora ~3×, no cambia la arquitectura.
  (B) Publicar el snapshot como artefacto estático: un proceso lo genera cada ~30 s y la
  API/CDN lo sirve; el coste pasa a ser independiente del número de espectadores. Es el
  principio de `ARCHITECTURE.md:68-69`.
  (C) Caché de snapshot en memoria con TTL de 10–30 s dentro del proceso. Mucho de (B) sin
  infraestructura nueva, pero sigue acoplando coste y escala en un único proceso.
  (D) Nada, y declarar el producto como demo local. Coherente con el estado actual pero
  cierra la puerta a publicar.
- **Recomendación razonada:** **(A) + (C) ahora, (B) como decisión del propietario.** (A) y
  (C) son cambios acotados y medibles que suben el techo uno o dos órdenes de magnitud sin
  contratar nada —y (C) no puede servir dato viejo rotulado como nuevo si el TTL va por
  `revision`, que ya existe—. (B) implica coste y proveedor, así que es gate del
  propietario, no de los agentes.
- **Prueba necesaria para cerrar:** medida de H7 con `uvicorn` real y 1/10/50/100 clientes
  concurrentes, antes y después, con p95 declarado.

---

### AUD01-P1-009 — Ninguna puerta de aceptación del Hito 3 es falsable: documentar un hueco basta para que deje de bloquear

- **Identificador:** `AUD01-P1-009`
- **Componente:** criterios de aceptación del kit (`AMPLIACION`, `MATRIZ-CIERRE`,
  `PROMPT-UNICO-ORCA`).
- **Severidad:** **P1** — es la causa estructural de `AUD01-P0-002` y de §5.1, y volverá a
  producir el mismo resultado en el Hito 4 si no se cambia.
- **Evidencia reproducible:** las tres citas de §9.2:
  `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md:40` («documentar el gap […] si impide el
  objetivo funcional, declararlo `PARTIAL`/`BLOCKED`»),
  `MATRIZ-CIERRE-MADRID.md:15` («Cualquier línea ausente del mapa **sin causa
  documentada** […] bloquea `DONE`»),
  `PROMPT-UNICO-ORCA.md:19` («Si una **condición fundamental** falla, no declares DONE»).
  Resultado: `mp-022-dossier-integracion.md:15-18`, «Las nueve puertas tienen evidencia
  […] **El Hito 3 está completo**», con 28/103 patrones de geometría.
- **Archivo/símbolo/dato afectado:** los tres documentos citados; `docs/TASKS.md:443`
  (criterio que admite «mayoría `pending` honesto» sin cuantificarla).
- **Riesgo de producto:** un sistema de aceptación que no puede rechazar no es un sistema de
  aceptación. Lo grave aquí no es que alguien hiciera trampa —no la hizo: cada evidencia es
  real y cada caveat está escrito— sino que **la honestidad documental se convirtió en el
  sustituto del umbral**. Los agentes hicieron exactamente lo correcto dentro de un marco
  que no exigía nada medible.
- **Causa raíz (confirmada):** los criterios están redactados como prohibiciones de
  deshonestidad («no inventar un tren», «no proclamar cobertura plena»), que el equipo
  cumplió escrupulosamente, y no como umbrales de suficiencia («≥ X % de patrones con
  corredor», «≥ N días de captura real», «salto < Y m»). No hay un solo número de
  suficiencia en todo el kit.
- **Alternativas:**
  (A) Añadir a cada puerta un umbral cuantitativo con su medida y su comando.
  (B) Separar «puertas de honestidad» (no falsear) de «puertas de suficiencia» (alcanzar un
  nivel), y exigir ambas.
  (C) Dejarlo y confiar en la revisión cruzada. Ya se intentó: dos agentes y cuatro rondas
  de auditoría no lo detectaron, porque cada uno revisaba el cumplimiento de su fila.
- **Recomendación razonada:** **(B), implementada con (A).** La distinción importa: las
  puertas de honestidad de este kit son excelentes y deben conservarse tal cual —son la
  razón por la que esta auditoría puede medir cosas, porque todo está declarado—. Lo que
  falta es la segunda familia, y basta un número por puerta.
- **Prueba necesaria para cerrar:** reescritura de las nueve puertas de
  `MATRIZ-CIERRE-MADRID.md:19-26` con un umbral medible y su comando por puerta, revisada
  por el agente contrario **antes** de autorizar el hito siguiente.

---

### AUD01-P2-010 — El array `stop_time_update` por parada se descarta al normalizar, y con él la única evidencia de qué parada se omite

- **Identificador:** `AUD01-P2-010`
- **Componente:** `packages/contracts/normalize.py`, modelo canónico, tablero de estación.
- **Severidad:** **P2** — pérdida de información acotada y ya declarada en ADR-0014, pero
  es justo la información que daba nombre al criterio de cierre de MP-016.
- **Evidencia reproducible:** `packages/contracts/normalize.py:54-74` conserva de cada
  `TripUpdate` solo `delay` de nivel viaje y `next_stop_id` (el primer no-`SKIPPED`); el
  array completo se descarta. ADR-0014 lo reconoce: «el `stop_time_update` por parada […]
  **no** está persistido en el modelo canónico — solo `next_stop_id`». Medido sobre las
  fixtures del kit:
  ```
  1533: 474 entidades · distribución de stopTimeUpdate {0: 9, 1: 462, 8: 1, 22: 2}
        trip.delay == arrival.delay: 465/465 (0 discrepancias)
        trips con alguna parada SKIPPED: 3 · CANCELED: 9
  ```
  Es decir: los **49 `SKIPPED`** del criterio de aceptación viven en **3 de 474** viajes
  (0,6 %), y son exactamente los viajes cuyo array se descarta.
- **Archivo/símbolo/dato afectado:** `packages/contracts/normalize.py:58-72`;
  `packages/contracts/canonical.py:96-102` (`TripUpdateObservation`);
  `apps/api/schemas.py:466`; `apps/api/snapshot.py:85-86`.
- **Riesgo de producto:** el tablero no puede decir «esta parada se omite», que es
  información operativamente relevante para un viajero esperando en ella; y la ETA por
  parada es necesariamente una aproximación declarada
  (`trip_level_delay_applied_to_all_stops`). El impacto sobre la ETA es menor de lo que
  parece —`trip.delay == arrival.delay` en 465/465, así que no se pierde precisión—; lo
  que se pierde es exclusivamente la identidad de la parada omitida.
- **Causa raíz (confirmada):** decisión de alcance tomada en MP-005/MP-006 (modelo canónico
  sin tabla de paradas por actualización) y conscientemente no revisada en el Hito 3,
  declarada en ADR-0014 y en `limitations` del tablero. No es un descuido: es deuda
  documentada cuyo coste quedó mal estimado por el criterio de aceptación de MP-016.
- **Alternativas:**
  (A) Tabla `trip_update_stop_time` (viaje, parada, `arrival_time`, `delay`,
  `schedule_relationship`), poblada por el colector. Habilita «parada omitida» y ETA por
  parada con procedencia real.
  (B) Guardar el array como `jsonb` en `trip_update_observation`. Barato, sin modelo, difícil
  de consultar.
  (C) Conservar solo los `SKIPPED` como lista de `stop_id`. Cubre el 100 % del caso de
  producto con coste mínimo (3 de 474 viajes lo usan).
  (D) Nada, y dejar de presentar «49 SKIPPED» como criterio de cierre, ya que el producto no
  puede expresarlo.
- **Recomendación razonada:** **(C), y (A) solo si el histórico lo justifica.** (C) entrega
  la capacidad de producto que falta —decir qué parada se omite— con un campo y sin tabla
  nueva, y es proporcional a un fenómeno que afecta al 0,6 % de los viajes. (A) es correcto
  pero su coste solo se justifica si se quiere ETA por parada con procedencia de operador.
- **Prueba necesaria para cerrar:** test que, ingiriendo el corte `1533`, recupere de la base
  los `stop_id` omitidos de los tres viajes afectados, y un elemento de UI que los muestre
  en el tablero de esas estaciones.

---

### AUD01-P2-011 — `packages/geo/madrid.py` codifica literales `route_id` y lógica condicionada por ellos, contra ADR-0011 §3

- **Identificador:** `AUD01-P2-011`
- **Componente:** `packages/geo/madrid.py`.
- **Severidad:** **P2** — deuda de extensibilidad en el eje exacto que ADR-0011 existe para
  proteger.
- **Evidencia reproducible:** `packages/geo/madrid.py:19-60` fija el mapa relación→`route_id`
  con literales (`"10T0017C5"`, `"10T0047C5"`, `"10T0018C5"`, `"10T0012C4"`,
  `"10T0014C4a"`, `"10T0011C4"`, `"10T0013C4a"`, `"10T0015C4b"`), y `:62-82`
  (`_known_caveats`) condiciona lógica sobre ellos más un recuento mágico de paradas:
  ```python
  if pattern.route_id in {"10T0047C5", "10T0048C5"} and len(pattern.stop_ids) == 7:
  if pattern.route_id == "10T0015C4b" and len(pattern.stop_ids) == 14:
  ```
  Contra ADR-0011 §3 (`Aceptado`): «La configuración/geometría específica de C5 (qué
  estaciones, qué `route_id`, qué shapes) vive en **datos o configuración cargable**, no en
  lógica de código condicionada por el literal».
- **Archivo/símbolo/dato afectado:** `packages/geo/madrid.py:19-60,62-82`;
  `docs/adr/0011-public-scope-vs-technical-pilot.md:19-22`.
- **Riesgo de producto:** añadir una línea, un sentido o un núcleo exige editar un paquete
  compartido y volver a pasar revisión cruzada, cuando el plan declarado es expandir a todos
  los núcleos de Cercanías y después a AV/LD/MD (`SIGUIENTES-HITOS.md`). Es la fricción que
  explica, en parte, por qué ocho líneas siguen sin geometría.
- **Causa raíz (probable):** el mapa de fuentes nació en MP-011 con una sola relación y
  creció por acumulación en MP-018 sin que nadie lo promoviera a datos; las salvedades por
  patrón se añadieron donde era más rápido escribirlas.
- **Alternativas:**
  (A) Mover especificaciones y salvedades a un manifiesto declarativo (JSON/TOML) junto a
  las fixtures, con el mismo esquema que ya tiene `MANIFEST.md`, y que `madrid.py` solo lo
  cargue.
  (B) Derivar la asociación `route_id`→relación de los propios metadatos OSM
  (`ref`/`official_ref`), que `find_route_relations` ya consulta. Elimina el mapa manual
  pero depende de la calidad de las etiquetas OSM.
  (C) Dejarlo y anotar la excepción en ADR-0011. Honesto, perpetúa la fricción.
- **Recomendación razonada:** **(A), con (B) como objetivo.** (A) es mecánico, no cambia
  comportamiento y restaura el cumplimiento de un ADR `Aceptado`; (B) es lo que hace falta
  si se quiere escalar a otros núcleos sin una tarea de código por línea.
- **Prueba necesaria para cerrar:** añadir una línea nueva al catálogo de geometría **sin
  tocar ningún `.py`**, y una prueba que falle si aparece un literal `10T...` en
  `packages/`.

---

### AUD01-P2-012 — El `route_color` oficial de Renfe se parsea y nunca se expone; las líneas se pintan con una paleta generada por hash

- **Identificador:** `AUD01-P2-012`
- **Componente:** `apps/api` (contrato de catálogo) y `apps/web/src/domain/palette.ts`.
- **Severidad:** **P2** — defecto de reconocimiento de producto con arreglo barato.
- **Evidencia reproducible:** `packages/gtfs/parser.py` construye `Route(... color=row["route_color"],
  text_color=row["route_text_color"] ...)`; `grep -n color apps/api/schemas.py` no devuelve
  ningún campo de color en `LineOut`/`CatalogOut`. El frontend lo documenta y lo asume:
  «el GTFS oficial publica `route_color` real de Renfe (p. ej. `75B6E0` para C1), pero el
  contrato `/api/v1/catalog` de MP-019 no expone ese campo y MP-020 no reescribe el
  contrato» (`apps/web/src/domain/palette.ts:13-17`), con asignación por hash FNV en
  `:36-68`.
- **Archivo/símbolo/dato afectado:** `packages/gtfs/parser.py` (`Route.color`);
  `apps/api/schemas.py` (`LineOut:102-106`, sin color); `apps/web/src/domain/palette.ts:19-32`.
- **Riesgo de producto:** en Madrid la línea **es** su color. Un mapa que pinta C5 de
  turquesa y C1 de rosa obliga a leer la etiqueta en cada tren y rompe el reconocimiento
  inmediato, que es justo lo que un mapa «inmersivo, map-first» vende. Y la limitación está
  redactada como ausencia de la fuente («el contrato no expone ese campo») cuando el dato
  está parseado una capa más abajo.
- **Causa raíz (confirmada):** el contrato de catálogo de MP-019 se diseñó antes del
  frontend de MP-020 y nadie añadió el campo; MP-020 respetó correctamente la regla de no
  reescribir el contrato de otra tarea.
- **Alternativas:**
  (A) Añadir `color`/`text_color` nullable a `LineOut` (extensión aditiva, no rompe `/v1`,
  mismo patrón que `LineOut.geometry` en DEC-031) y usarlos con la paleta actual como
  respaldo.
  (B) Codificar los colores en el frontend. Viola ADR-0011 y se desincroniza del GTFS.
  (C) Dejarlo. El mapa sigue siendo irreconocible para un madrileño.
- **Recomendación razonada:** **(A).** Es una extensión aditiva de las que el contrato ya
  admite por precedente explícito (DEC-031), usa un dato real de la fuente con su
  atribución ya resuelta, y conserva el principio correcto que la paleta documenta: el color
  identifica la línea y la procedencia de la posición se expresa con forma y texto.
- **Prueba necesaria para cerrar:** `GET /api/v1/catalog` devolviendo `75B6E0` para C1 y el
  frontend usándolo, con la paleta hash solo como respaldo cuando el GTFS no lo publique; y
  la medida de H5.

---

### AUD01-P2-013 — La puntualidad publicada se calcula con un umbral sin calibrar que no aparece en el contrato ni en la pantalla

- **Identificador:** `AUD01-P2-013`
- **Componente:** `services/snapshotter/gold.py`, `apps/api/schemas.py`,
  `apps/web/src/ui/ExploreView.tsx`.
- **Severidad:** **P2** — la métrica es honesta en su denominador y opaca en su definición.
- **Evidencia reproducible:** `services/snapshotter/gold.py:139`
  (`on_time_threshold_seconds: float = 300.0`), declarado en DEC-033 (b) como «un punto de
  partida calibrable sin histórico real propio todavía con el que calibrarlo» y confirmado
  abierto en `mp-022-dossier-integracion.md:52`. El mart lo lleva en sus metadatos
  (`gold.py:253`, `history.py:292`) pero `grep -n threshold apps/api/schemas.py` no lo
  encuentra en ningún contrato (`HistoryLineMetricOut:557-565`), y `ExploreView.tsx:199-207`
  muestra «Puntualidad de lo cubierto» con numerador y denominador, sin umbral.
- **Archivo/símbolo/dato afectado:** `services/snapshotter/gold.py:139,253`;
  `apps/api/schemas.py:557-565`; `apps/web/src/ui/ExploreView.tsx:170,199-207`.
- **Riesgo de producto:** «83 % de puntualidad de lo cubierto (10/12)» no es interpretable
  sin saber qué cuenta como puntual, y 300 s (5 min) es un umbral generoso para Cercanías
  que nadie ha validado contra el servicio real. El proyecto cumple su propia regla
  —puntualidad siempre con cobertura (DEC-009)— y le falta la gemela: puntualidad siempre
  con su umbral.
- **Causa raíz (confirmada):** DEC-033 (b) registra correctamente que el umbral no se puede
  calibrar con dos días archivados, y la decisión de no calibrarlo es acertada; lo que no se
  hizo fue propagar la incertidumbre al consumidor.
- **Alternativas:**
  (A) Añadir `on_time_threshold_seconds` a `HistoryLineMetricOut` y mostrarlo junto al
  porcentaje («puntual = ≤ 5 min»), marcado como sin calibrar.
  (B) Publicar la distribución de retrasos en vez de un porcentaje binario. Más informativo,
  más alcance.
  (C) Retirar la métrica hasta calibrar. Desproporcionado: la métrica con denominador ya es
  mejor que la de cualquier referencia.
- **Recomendación razonada:** **(A).** Exponer el umbral cuesta un campo y convierte una
  cifra opaca en una cifra auditable, que es la tesis del producto. (B) es la evolución
  natural cuando haya histórico.
- **Prueba necesaria para cerrar:** el umbral presente en la respuesta de
  `/api/v1/history/lines` y visible en Explore, con test de contrato.

---

### AUD01-P2-014 — La vigencia del GTFS solo se comprueba al arrancar, y no hay refresco; un servicio publicado servirá un catálogo caducado en silencio

- **Identificador:** `AUD01-P2-014`
- **Componente:** `apps/api/gtfs_source.py`, `infra/operate/`.
- **Severidad:** **P2** — la guardia existe y no puede dispararse en el único escenario que
  importa.
- **Evidencia reproducible:** `apps/api/gtfs_source.py:155-161` calcula `madrid_today` y
  rechaza el arranque si el GTFS está fuera de vigencia, **dentro de `load_network`**, que
  `apps/api/main.py:39-50` invoca una sola vez en el `lifespan`. No hay recarga ni
  revalidación periódica. Vigencia del ZIP del kit, verificada con
  `scratch/aud01_validity.py`: **2026-11-20 .. 2026-12-19**. `infra/operate/` supervisa el
  colector y el archivo diario; no hay ninguna pieza que descargue GTFS nuevo ni que
  reinicie la API.
- **Archivo/símbolo/dato afectado:** `apps/api/gtfs_source.py:133-161`;
  `apps/api/main.py:39-50`; `infra/operate/README.md:24-26`.
- **Riesgo de producto:** un proceso arrancado hoy y vivo el 20 de diciembre servirá
  horarios caducados sin avisar: tableros con salidas que ya no existen y
  `scheduled_trip_instances` de un calendario vencido. La guardia que debería impedirlo
  pasó hace semanas.
- **Causa raíz (probable):** el catálogo es inmutable por proceso **por diseño** (es la
  mitad de ADR-0014: catálogo cacheable vs snapshot ligero), decisión correcta; lo que falta
  es el ciclo de vida que la acompaña, que no pertenece a ninguna tarea de la cadena.
- **Alternativas:**
  (A) Revalidar la vigencia en cada petición barata (`/health`) y publicar
  `gtfs_expired: true` con degradación visible, sin recargar nada.
  (B) Trabajo diario en `infra/operate/` que descargue el GTFS, compare `gtfs_version` y
  reinicie la API si cambió. Es lo que hace falta para operación real.
  (C) Recarga en caliente del catálogo. Rompe la inmutabilidad por proceso de ADR-0014.
- **Recomendación razonada:** **(A) + (B).** (A) es barato y convierte un fallo silencioso
  en un fallo visible, que es la disciplina de todo el resto del producto; (B) es la pieza
  que falta en `infra/operate/` para que «operación local supervisada» incluya el catálogo y
  no solo la ingesta.
- **Prueba necesaria para cerrar:** test que, con el reloj desplazado más allá de
  `gtfs_valid_until`, exija que `/api/v1/health` declare el catálogo caducado; y una
  plantilla de refresco diario en `infra/operate/`.

---

### AUD01-P2-015 — `implausible_speed` se mide sobre la cuerda mientras el movimiento se mide sobre el arco; hay un caso ciego real, y es el tren usado en la demostración de cierre

- **Identificador:** `AUD01-P2-015`
- **Componente:** `packages/quality/engine.py` frente a `packages/geo`/`packages/movement`.
- **Severidad:** **P2** — sesgo sistemático del detector hacia el falso negativo, acotado.
- **Evidencia reproducible:** `.venv/bin/python scratch/aud01_chord_vs_arc.py`, sobre los
  dos cortes del kit:
  ```
  pares de Madrid (route_id resuelto): 118; sobre el umbral de cuerda (200 km/h): 2
    20058  10T0007C3   cuerda 245.6 km/h
    20481  10T0016C4b  cuerda 581.7 km/h
  ciegos (cuerda bajo umbral, arco por encima): 1
    20277  10T0014C4a  cuerda 184.2 km/h   arco 200.5 km/h
  razón arco/cuerda para pares con movimiento real: p50 1.00  máx 1.57
  ```
  Los dos marcados coinciden con los 2 `data_quality_event` que registra la base de replay
  (`240/199/4/7/2`, `docs/TASKS.md:534`): el motor funciona como está diseñado. El caso
  ciego, `20277`, es exactamente el tren que la revisión de MP-022 usó para su recorrido de
  la puerta 8 («tren 20277 → Seguir → arrastre […]», `docs/TASKS.md:571`).
- **Archivo/símbolo/dato afectado:** `packages/quality/engine.py:27`
  (`implausible_speed_kmh = 200.0`) y `:166-182` (`check_implausible_speed`, haversine);
  `packages/geo/geometry.py` (`arc_length_to`), `packages/movement/rendering.py`.
- **Riesgo de producto:** el detector de velocidades imposibles —uno de los cinco flags de
  calidad, y la lección explícita que el proyecto tomó del artículo de Valfiguer
  (`deep-research-report.md:49`)— subestima la velocidad real en corredores curvos hasta un
  36 % (razón arco/cuerda máxima 1,57), así que deja pasar anomalías justo donde la vía
  gira. Además, 200 km/h es un umbral sin calibrar para una red cuya velocidad comercial
  máxima está muy por debajo.
- **Causa raíz (confirmada):** la regla se escribió en MP-008, antes de que existiera
  geometría (MP-011/MP-018), así que la cuerda era la única distancia disponible. Al llegar
  la geometría nadie revisó la regla, y el umbral siguió siendo el original.
- **Alternativas:**
  (A) Cuando el patrón tenga corredor validado, evaluar el flag sobre el progreso de arco y
  conservar la cuerda como respaldo. Usa lo que ya existe.
  (B) Bajar el umbral a la velocidad comercial máxima real de Cercanías más un margen, con
  evidencia. Requiere histórico (bloqueado por lo mismo que DEC-033 b).
  (C) Dejarlo y documentar el sesgo. No cuesta nada y no detecta nada nuevo.
- **Recomendación razonada:** **(A) ahora, (B) cuando haya histórico.** (A) elimina el sesgo
  con datos que el sistema ya calcula para otra cosa y no toca el umbral; (B) necesita
  exactamente el histórico real que (§5.1) todavía no existe, así que no debe forzarse.
- **Prueba necesaria para cerrar:** regresión que, sobre el par `20277` de los dos cortes,
  exija un `data_quality_event` de `implausible_speed`, y que falle con la regla actual.

---

### AUD01-P2-016 — El Hito 3 implementó lo que un ADR `Aceptado` reservaba a planificación, sin enmendar el ADR ni añadir puerta de salida al plan

- **Identificador:** `AUD01-P2-016`
- **Componente:** gobernanza (`docs/adr/0011`, `docs/PLAN.md`).
- **Severidad:** **P2** — deuda de gobernanza con consecuencia práctica real.
- **Evidencia reproducible:** `docs/adr/0011-public-scope-vs-technical-pilot.md:24`
  (`Estado: Aceptado`): «Hito 2 entrega la arquitectura extensible y el piloto C5 poblado;
  **Hito 3 planifica (no implementa)** la cobertura de toda la red». `docs/STATUS.md` (Hito
  2) lo repite: «no se implementa la red completa de Cercanías Madrid en este hito — eso es
  Hito 3, **solo backlog de planificación**». El Hito 3 la implementó
  (`PROMPT-UNICO-ORCA.md:11`), el ADR sigue sin enmendar, y `docs/PLAN.md:61-67` termina en
  «F10 — Expansión (fuera de alcance de MP-001 a MP-015)», sin fase ni *exit gate* para
  MP-016→MP-022 — contra su propio gate transversal de `:86`: «Ninguna decisión
  arquitectónica cambia sin ADR».
- **Archivo/símbolo/dato afectado:** `docs/adr/0011-public-scope-vs-technical-pilot.md:24`;
  `docs/PLAN.md:61-67,86`.
- **Riesgo de producto:** el Hito 3 es el único de los tres sin puerta de salida escrita en
  el plan del repositorio, así que su cierre se evaluó **solo** contra el kit externo — y
  las debilidades de ese kit (§9.2) no tenían contrapeso interno. Es la vía por la que las
  áreas 5, 6 y 8 del backlog propio desaparecieron sin que nada lo señalara.
- **Causa raíz (confirmada):** el cambio de alcance llegó como prompt de autorización, no
  como propuesta de ADR, y el protocolo no exige convertir una autorización del propietario
  en enmienda de los ADR que contradice.
- **Alternativas:**
  (A) ADR-0016 que supersede el punto 4 de ADR-0011 y registre lo realmente ejecutado, más
  una fase F11 en `PLAN.md` con el *exit gate* real.
  (B) Enmendar ADR-0011 en caliente. Prohibido por `docs/adr/README.md` y ya corregido una
  vez por esta misma razón (DEC-034).
  (C) Nada. Deja dos documentos `Aceptado` contradiciendo el estado del repositorio.
- **Recomendación razonada:** **(A).** Es el mecanismo que el propio proyecto se dio y ya
  aplicó correctamente una vez (ADR-0013 en lugar de reescribir ADR-0003). Y añadir la fase
  a `PLAN.md` es lo que devuelve al repositorio su propia vara de medir para el Hito 4.
- **Prueba necesaria para cerrar:** ADR nuevo en `Propuesto` y fase F11 en `PLAN.md` con
  *exit gate* verificable; ninguna de las dos cosas la promueve un agente.

---

### AUD01-P2-017 — El backlog de Hito 3 escrito con el repositorio delante se sustituyó por un kit redactado sin acceso a él, y se perdieron sus tres áreas de mayor valor

- **Identificador:** `AUD01-P2-017`
- **Componente:** proceso de autorización de hitos.
- **Severidad:** **P2** — hallazgo de proceso; es la causa común de P0-002, P1-003 y P1-008.
- **Evidencia reproducible:** `docs/HITO_3_BACKLOG.md` (9 áreas, redactado en MP-015 con el
  repositorio delante) frente a `docs/hitos/hito-03/REVISION-Y-DECISIONES.md:3`: «**No se ha
  inspeccionado el clon local del propietario ni ejecutado su aplicación** en esta
  revisión». Áreas sin equivalente en ningún criterio de MP-016→MP-022:
  - `:29-32` área 5 — escalabilidad y «evaluar si el patrón de snapshot/CDN se vuelve
    necesario» → `AUD01-P1-008`;
  - `:36` área 6 — «Confirmar empíricamente (no asumir) que todas las líneas […] tienen el
    mismo nivel de instrumentación en el feed» → `AUD01-P1-003`;
  - `:42-44` área 8 — validar cada línea nueva «con el mismo rigor empírico que
    MP-002/MP-003 aplicaron a C5» → §5.1.
- **Archivo/símbolo/dato afectado:** `docs/HITO_3_BACKLOG.md:29-44`;
  `docs/hitos/hito-03/PLAN-Y-ACEPTACION.md` (siete tareas, ninguna cubre esas tres áreas).
- **Riesgo de producto:** el kit aportó mucho que el backlog propio no tenía —el contrato
  temporal, la separación raw/matched/rendered, el diseño de interacción, la disciplina de
  procedencia— y a cambio perdió las tres preguntas que solo se pueden formular habiendo
  medido el sistema. El resultado es un hito que mejora mucho el rigor de presentación del
  dato y no responde a si el producto escala, si la fuente es homogénea, ni si funciona
  fuera de dos capturas.
- **Causa raíz (confirmada):** el kit se incorporó como fuente de verdad del reparto y la
  aceptación (`docs/TASKS.md:394`) sin un paso de reconciliación explícito contra
  `HITO_3_BACKLOG.md`; ni el kit ni el backlog mencionan al otro.
- **Alternativas:**
  (A) Paso obligatorio de reconciliación al autorizar un hito: tabla área-del-backlog →
  tarea-del-kit, con las ausencias justificadas por escrito.
  (B) Que el kit lo redacte alguien con acceso al repositorio. No siempre es posible y
  pierde la ventaja de una mirada externa.
  (C) Nada. Se repetirá en el Hito 4, donde el riesgo es mayor (AV/LD/MD con umbrales y
  fuentes distintos).
- **Recomendación razonada:** **(A).** Conserva el valor de la mirada externa —que aquí fue
  grande y real— y hace visible lo que se abandona. Una tabla de diez filas al autorizar
  habría salvado las tres áreas.
- **Prueba necesaria para cerrar:** tabla de reconciliación en el documento de autorización
  del Hito 4, revisada por el agente contrario antes de abrir el primer worktree.

---

### AUD01-P2-018 — El estándar de evidencia no es uniforme: MP-016 y MP-017 cerraron sin documento en `docs/evidence/`

- **Identificador:** `AUD01-P2-018`
- **Componente:** `docs/evidence/`.
- **Severidad:** **P2** — deuda de auditabilidad.
- **Evidencia reproducible:** `ls docs/evidence/` contiene documentos para MP-019 (3),
  MP-020, MP-021 (3) y MP-022 (4), más el CSV de MP-018. **No hay ningún
  `mp-016-*` ni `mp-017-*`**: su evidencia vive solo en línea dentro de `docs/TASKS.md` y
  `docs/STATUS.md`.
- **Archivo/símbolo/dato afectado:** `docs/evidence/`; `docs/TASKS.md:396-430`.
- **Riesgo de producto:** MP-016 (fiabilidad de ingesta) y MP-017 (catálogo e identidad) son
  la base sobre la que se apoyan las cinco tareas siguientes, y son precisamente las dos
  cuya evidencia no es citable por fichero. Auditar sus cifras —los 119/121/49, el
  `stopId 60104`, la ventana de recencia de 20 h— obliga a reconstruirlas desde un tablero
  de 1 882 líneas.
- **Causa raíz (probable):** la convención de `docs/evidence/` se consolidó a partir de
  MP-019, cuando el volumen de medidas lo hizo necesario; las dos primeras tareas cerraron
  antes de que existiera.
- **Alternativas:**
  (A) Extraer retrospectivamente la evidencia de MP-016/MP-017 de `STATUS.md` a dos
  documentos, sin reejecutar nada y declarándolo así.
  (B) Reejecutar y documentar. Más valioso y es alcance de otra tarea.
  (C) Nada. La asimetría se queda.
- **Recomendación razonada:** **(A).** Es reorganización documental sin afirmación nueva, y
  deja las siete tareas con el mismo nivel de citabilidad.
- **Prueba necesaria para cerrar:** `docs/evidence/mp-016-*.md` y `mp-017-*.md` existentes,
  con los comandos y cifras ya registrados y marcados como extracción retrospectiva.

---

## 12. DESCARTADO — hipótesis adversas que intenté sostener y no se sostienen

Las cuatro siguen descartadas tras la revisión de Codex Sol · High, pero **con su alcance
acotado**: tres de ellas se descartaban antes con una formulación más ancha de lo que la
evidencia sostiene. Cada fila dice ahora qué queda descartado y qué sigue sin cubrir.

| ID | Hipótesis | Por qué se descarta, y con qué alcance |
|---|---|---|
| `AUD01-DESC-001` | La arquitectura está sobre-ingenierizada para el problema. | **Razón sustantiva, no un inventario de tecnologías ausentes** (objeción del revisor a la versión anterior, que se limitaba a enumerar lo que no hay): cada uno de los cuatro procesos existe porque **aísla un modo de fallo que de otro modo se propagaría**, y eso es comprobable. El colector puede morir y reiniciarse sin tocar a quien sirve peticiones —medido: `kill -9` con reanudación en 5 s, y `EX_TEMPFAIL` 75 ante pérdida de PostgreSQL (DEC-041)—; el snapshotter escribe el archivo frío mediante una sustitución con cuarentena cuya caída intermedia no destruye el día ya archivado (DEC-040, fijado con inyección de fallo en la costura exacta); la API no toca la red externa jamás y el frontend no toca Renfe jamás, frontera que impide que un cambio de contrato de la fuente alcance al navegador. Suprimir cualquiera de esas cuatro fronteras reintroduce un fallo concreto ya observado en el proyecto: la separación compra algo medible en vez de ser estructura por gusto. El desajuste real es el inverso — **falta** la pieza de escala que el propio documento de arquitectura ya había adoptado (`AUD01-P1-008`). Coincide con AUD-07 §2 y §9. |
| `AUD01-DESC-002` | El frontend extrapola por su cuenta y puede fabricar posiciones. | **Descartado, y acotado a la autoridad de avance** (precisión del revisor): el cliente **sí calcula coordenadas** —convierte progreso en lat/lon sobre la polilínea del corredor, `coordinateAtProgress` en `movement.ts:47-49`—, así que no es cierto que no calcule nada. Lo que no hace es **decidir cuánto avanzar**: `frameFor` (`movement.ts:74-96`) solo progresa si el backend publicó `progress_envelope` **y** hay eje de patrón, aplica la expresión fijada por el contrato sin reinventarla, se congela en `valid_until` (`source: "frozen_horizon"`) y en cualquier otro caso dibuja la coordenada publicada tal cual. La comprobación de fidelidad (error < 1 m en test y 6,6 cm en Python sobre 44 circulaciones) verifica exactamente eso: que su cálculo de coordenada reproduce el del backend. Conclusión acotada: **la autoridad sobre el avance es del backend**, y el movimiento falso de `AUD01-P0-001` se origina ahí; el cliente evalúa con fidelidad una envolvente equivocada. |
| `AUD01-DESC-003` | La salud de feed copió a Valfiguer solo en lo fácil. | Descartado **como afirmación de omisión deliberada de lo difícil**, no como prueba de equivalencia semántica: `apps/api/schemas.py:59-67` publica los cinco campos, incluidos los dos no obvios (`unchanged_for_s`, `rejected`), y la deduplicación no resetea la edad del dato (`mp-019-tres-snapshots-replay.md:29-31`), que es el matiz que la hace segura en vez de peligrosa. **Lo que esto NO prueba** (objeción del revisor): que la semántica de cada campo coincida con la de Valfiguer. No he comparado definiciones —qué cuenta como `rejected`, desde qué instante se mide `unchanged_for_s`, qué umbral separa `ok` de `stale`— porque exigiría consultar su servicio en vivo, que esta auditoría no hizo (`AUD01-NV-002`). La afirmación sostenible es: **los campos difíciles están presentes y bien usados dentro de su propio modelo**; la equivalencia con la referencia queda sin verificar. |
| `AUD01-DESC-004` | La ausencia de CORS es un agujero de seguridad. | Descartado **solo para el caso que cubre**: lectura desde navegador, mismo origen y solo lectura. Sin cabeceras `Access-Control-Allow-Origin` el navegador deniega por defecto cualquier lectura cross-origin, y `apps/web/vite.config.ts:42-52` documenta el modelo *same-origin* (proxy en desarrollo, reverse proxy en producción) sobre el que se apoya esa ausencia; ya evaluado y rebajado en AUD-07 §6 tras verificación independiente. **Dos riesgos distintos quedan fuera de ese descarte y siguen sin cubrir** (separación que pide el revisor, y que la versión anterior de esta fila fundía en uno): (1) **autenticación** — ningún endpoint la tiene, de modo que la política del navegador no protege frente a un cliente que no sea un navegador (`curl`, un script, otro servidor); (2) **limitación de tasa** — no existe ninguna, así que el coste por espectador de `AUD01-P1-008` no tiene techo impuesto por el servicio. Ninguno de los dos está registrado como decisión deliberada en ningún ADR. Son riesgos de publicación reales que el descarte del CORS no desmiente. |

## 13. NO VERIFICADO — límites explícitos de esta auditoría

| ID | Afirmación no verificada | Qué haría falta |
|---|---|---|
| `AUD01-NV-001` | Que Overpass publique relaciones utilizables para C1, C2, C3, C7, C8a, C8b, C9 y C10. | Ejecutar `find_route_relations(ref=..., network="Cercanías Madrid")` para las ocho líneas. No lo hice: requiere llamadas externas que esta auditoría no tiene autorizadas. **Lo que sí está verificado** es que para esas ocho no hay intento documentado: ninguna entrada en `madrid_source_specs` (`packages/geo/madrid.py:19-60`) ni registro de intento en `STATUS`/`TASKS`. No afirmo que nadie lo probara —eso es una prueba negativa que no tengo—, ni extiendo la afirmación a los 4 patrones de C4b, donde el intento consta y falló con dos `HTTP 502` (`docs/STATUS.md:850-852`). |
| `AUD01-NV-002` | El estado funcional actual de Via Península, Valfiguer y las apps oficiales. | Consulta en vivo de los cuatro productos. La comparación de §2 y §8 se apoya en la verificación documentada del proyecto, fechada `2026-11-18`, y puede estar desactualizada en cualquier fila. |
| `AUD01-NV-003` | Latencia y escalado reales con red, ASGI y concurrencia. | Prueba de carga de H7. Todo el benchmark existente es `TestClient` en proceso, declarado como tal (`mp-022-benchmark.md:18`). Mi cálculo de ~30 espectadores/núcleo es una cota superior derivada, no una medida. |
| `AUD01-NV-004` | Que los saltos medidos en `AUD01-P0-001` se reproduzcan con la cadencia real del feed. | Colector en vivo ≥ 2 h (H1). Mi medida usa los 77 s que separan los dos cortes congelados; el escalado a ~30 s es aritmético, no observado. |
| `AUD01-NV-005` | Que un usuario real no distinga los estados de posición ni reconozca las líneas. | H5 y H6 con 5 usuarios. No hay ninguna prueba con usuarios en los tres hitos. |

---

## 14. Comandos reproducibles

Todos desde la raíz del worktree, con el `.venv` del repositorio y los datos del kit
repuestos (`data/hito-03/replay/`). Ninguno toca PostgreSQL, la red ni el estado del
repositorio.

```sh
# Cobertura real de posicionamiento (programados en curso vs observados), por línea
.venv/bin/python scratch/aud01_coverage.py

# Desviación de los observados respecto a su propia ventana de horario
.venv/bin/python scratch/aud01_window.py

# Envolvente publicada para trenes que no han salido (17/121, hasta 108 km/h)
.venv/bin/python scratch/aud01_envelope_predeparture.py

# Salto real al llegar el ancla siguiente, 44 circulaciones (p50 1 237 m, máx 3 274 m)
.venv/bin/python scratch/aud01_snap.py

# Intervalo entre paradas del núcleo Madrid vs horizonte (180 s configurados / 190 s efectivos)
.venv/bin/python scratch/aud01_stopgap.py

# Velocidad de cuerda (quality) vs de arco (movimiento), y el caso ciego 20277
.venv/bin/python scratch/aud01_chord_vs_arc.py

# Vigencia del GTFS del kit
.venv/bin/python scratch/aud01_validity.py

# Riqueza real del array stop_time_update y los 49 SKIPPED
python3 -c "
import json, collections
for cut in ('1532','1533'):
    d = json.load(open(f'data/hito-03/replay/{cut}/trip_updates.json'))
    ents = d['entity']
    print(cut, 'entidades', len(ents),
          collections.Counter(len(e.get('tripUpdate',{}).get('stopTimeUpdate') or []) for e in ents))
"
```

Los guiones viven en `scratch/` (fuera del producto) y están escritos contra el código del
repositorio: cualquier cambio en `packages/movement`, `packages/geo` o `packages/gtfs`
cambia sus resultados, que es lo que se quiere de una prueba de cierre.

---

## 15. Lo que cambiaría de los prompts de los Hitos 1, 2 y 3

El encargo pide esto explícitamente, y es la parte más reutilizable del informe.

**Descartar.**

- *«mayoría `pending` honesto, no fabricado»* (`docs/TASKS.md:443`) y toda formulación que
  pre-autorice un nivel de incompletitud. Si la mayoría puede quedar pendiente, el criterio
  no es un criterio.
- *«Si una condición fundamental falla, no declares DONE»* (`PROMPT-UNICO-ORCA.md:19`) sin
  una lista cerrada de condiciones fundamentales. Delega en quien cierra la definición de lo
  que le bloquea.
- Reproducir conteos de fixture como criterio de cierre («119/121/49 SKIPPED»,
  `MATRIZ-CIERRE-MADRID.md:9`). Son una buena prueba de regresión del parser y un mal
  criterio de producto: el 49 resultó medir 3 circulaciones de 474, y el producto sigue sin
  poder expresarlo.

**Simplificar.**

- El kit del Hito 3 son 12 documentos con jerarquía de precedencia declarada en tres sitios
  distintos (`PLAN-Y-ACEPTACION.md:7`, `REVISION-Y-DECISIONES.md:41-48`,
  `MATRIZ-CIERRE-MADRID.md:5`). Nueve puertas, cuatro documentos vinculantes de aceptación y
  un anexo «vinculante» que complementa a otro vinculante. Cuesta más reconciliarlos que
  cumplirlos, y la contradicción de §9.1 sobrevivió precisamente porque estaba repartida
  entre cuatro ficheros. Un documento de aceptación, con un umbral por puerta.
- Las prioridades técnicas de `PROMPT-UNICO-ORCA.md:13` son siete, con sub-cláusulas, en un
  párrafo. Las que llevaban número y medida (p50/p95, EXPLAIN) se cumplieron; las que
  llevaban adjetivo («animación fluida», «inmersivo», «honestas») se cumplieron en el
  sentido más favorable posible.

**Añadir.**

1. **Un número por puerta.** «≥ 90 % de los patrones de cada línea con corredor validado o
   causa externa verificada por patrón»; «salto de posición al refrescar el ancla < 200 m en
   p50»; «≥ 3 días de captura en vivo, no dos cortes»; «≥ 100 espectadores concurrentes con
   p95 < 1 s». Cada una con el comando que la mide.
2. **Reconciliación obligatoria entre el backlog propio y el kit externo** al autorizar un
   hito: tabla área → tarea, con las ausencias justificadas. Habría salvado las áreas 5, 6 y
   8 (`AUD01-P2-017`).
3. **Regla de reutilización de umbrales:** cuando un valor marcado «calibrable» cambia de
   papel —de clasificar a autorizar— hace falta una medida nueva, no solo una cita. Es el
   mecanismo que falta y el que produjo `AUD01-P1-005`.
4. **Una puerta de documentación de portada**, automatizable: ningún hito cierra si
   `README.md` o `ARCHITECTURE.md` describen un estado anterior a la última tarea `DONE`.
   Siete tareas y cuatro rondas de revisión cruzada no lo detectaron
   (`AUD01-P1-006`).
5. **Una pregunta de producto, y no de implementación, en cada hito:** «¿qué puede hacer hoy
   un usuario que no podía antes, y cómo lo comprobamos con un usuario?». Los tres hitos no
   tienen ni una sola observación de una persona usando el producto; H5, H6 y H8 existen
   porque esa pregunta nunca se hizo.

**Conservar tal cual.** Las prohibiciones de deshonestidad del kit —«no inventar un tren»,
«no proclamar cobertura plena de GPS», «dato ausente ≠ cero», «puntualidad siempre con
cobertura», «la coordenada renderizada nunca se archiva como observación Renfe», «ninguna
prueba sintética se presenta como captura oficial»— son el mejor activo del proyecto y la
razón por la que esta auditoría ha podido medir con precisión en vez de especular: todo
estaba declarado. No hay que relajarlas; hay que añadirles la familia que falta, la de
suficiencia.
