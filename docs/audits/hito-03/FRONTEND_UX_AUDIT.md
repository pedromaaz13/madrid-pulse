# AUD-05 — Auditoría exhaustiva del frontend en navegador real

**Ejecuta:** Claude Sonnet (worker dispatchado, contexto aislado)
**Revisa:** Codex `gpt-5.6-terra` · high, sin navegador (`ctx_53f6eb860b17`). Resultado de esa revisión formal: **P0-1 CONFIRMADO** (reproducido dos veces en su propio PostgreSQL: `unknown`, edades −71,0 s, `source_timestamp` 14:33:21Z, 468 entidades, determinista), el `board` no expone `degraded`, y los P2-2/P2-3 respaldados por JSX/código; veredicto sobre el **documento**: `CHANGES_REQUESTED` por afirmaciones de ejecución sin artefacto. Esta versión (v2) responde a ese veredicto punto por punto (ver §0) y queda **pendiente de re-verificación**; no está APPROVED.
**Fecha:** 2026-11-23 (v1) · 2026-11-23 (v2, corrección tras revisión formal)
**Rama:** `audit/hito-03-adversarial`
**Worktree:** `/Users/matu/orca/workspaces/madrid-pulse/audit-hito-03`
**Commit base auditado:** `d349465` (cadena MP-016→MP-022 + AUD-00/02/07 ya registrados)

No se ha modificado código de producto. Los hallazgos de este documento
se verificaron con **Chrome DevTools MCP real** (`new_page`, `navigate_page`,
`take_screenshot`, `take_snapshot`, `emulate`, `evaluate_script`,
`list_console_messages`, `get_console_message`, `wait_for`) contra una instancia
local de `apps/api` + `apps/web` propia. Lo que se apoya solo en lectura de
código está marcado como "solo código" (§6, §7).

## 0. Cambios de la v2 (respuesta al veredicto `CHANGES_REQUESTED`)

Regla aplicada: cada afirmación de ejecución lleva ahora un artefacto en `capturas/` (captura, JSON de medición o
transcripción literal en `capturas/24-transcripciones-devtools.md`) o se ha reducido a lo que sí está probado.
P0-1 (confirmado por el revisor) no cambia en sustancia; solo se corrige **a qué captura se remite** (ver nota en P0-1).

| Punto del revisor | Qué se hizo |
|---|---|
| 1. P2-1 | Reescrito. Retirados "5-8 marcadores", "radio ~25 px", "zoom 13" como zoom de trabajo y "«Centrar Madrid» es el estado por defecto" tal como estaban redactados; sustituidos por una medición reproducible (`21-…json`) con captura pareada (`21-…png`). Ver P2-1. |
| 2. Capturas 16/17 | Eran las que apoyan la búsqueda y la tecla Escape (§6), no el solapamiento; ya no se citan en P2-1. P2-1 cita 18, 19 y 21. |
| 3. P2-2 | Artefacto de DevTools adjunto: texto literal del *issue*, `msgid`, y volcado del único campo de formulario sin `id`/`name` (`24-…md` §A). Corregida la redacción "lectores de pantalla lo anuncian correctamente": solo se probó el árbol de accesibilidad, no un lector real. |
| 4. P2-3 | **La afirmación de la v1 era incorrecta** ("no tiene ningún efecto observable"). Con clic real y captura antes/después se observa que sí cambia el estado (ver P2-3). Adjuntos: árbol de accesibilidad antes/después, consola tras el clic y dos capturas. Retirada toda mención a anuncio por lector de pantalla (no hay evidencia). |
| 5. Resto | Auditadas todas las afirmaciones de ejecución. Corregidas: citas de captura en P0-1 (la v1 remitía a 02/04, que no muestran ese mensaje), "capturas 01 a 18" para el *issue*, "69 estaciones" del histórico, "tres comandos curl", y la verificación de reduced-motion (ahora medida, no solo leída). Añadido P2-4 (visible en la captura 20). Se marcó como "solo código" lo no probado en vivo (§6, §7). |

---

## 1. Entorno levantado para esta auditoría

Instancia completamente propia y desechable, nunca comparte estado con otras
tareas:

| Componente | Detalle |
|---|---|
| PostgreSQL/PostGIS | Ronda v1: contenedor propio `madrid-pulse-aud05-postgres`, `127.0.0.1:5455`. Ronda v2 (esta corrección): contenedor propio `aud05r-postgres` (`postgis/postgis:17-3.5`), `127.0.0.1:5456`. Nunca 5433. Migraciones `0001_init`/`0002_api_batch_indexes` aplicadas. Ambos destruidos al terminar (§8). |
| Datos | `data/hito-03/replay/` repuesto vía `instalar.py --worktree "$PWD" --solo-datos` (dos cortes reales Renfe `1532`/`1533`, 2026-11-20, GTFS estático completo del núcleo). |
| Ingesta | `apps.api.tools.replay_three_snapshots` (colector real, `run_cycle`); salida íntegra de la ronda v2 en `capturas/30-ingesta-replay.txt` (snapshots con 119/122 vehículos; recuentos finales `(240, 199, 4, 7, 2)`). |
| Histórico | `services.snapshotter 2026-11-20` con `MADRID_PULSE_SHORT_NAME=` (núcleo completo, no el valor por defecto `C5`), solo en la ronda v1. Lo que muestran las capturas 09/10: 1304 programados, 122 observados, 1179 huecos, 3 anuladas y 35 rutas con viajes programados. |
| API | `uvicorn apps.api.main:app`, `MADRID_PULSE_MODE=replay`, GTFS completo: `127.0.0.1:8010` (v1) y `127.0.0.1:8037` (v2). |
| Web | `npm run dev` en `apps/web` con `MADRID_PULSE_API_TARGET` apuntando a la API propia: puerto 5180 (v1) y 5191 (v2). |
| Navegador | Chrome DevTools MCP real, confirmado operativo con `new_page` antes de capturar nada; transcripciones de las llamadas relevantes en `capturas/24-transcripciones-devtools.md`. |

Todas las capturas están en `docs/audits/hito-03/capturas/`, referenciadas por
nombre de archivo en cada hallazgo.

---

## 2. Hallazgos P0

### P0-1 — `/api/v1/snapshot?at=` en replay reclasifica datos válidos como "unknown" y expone edades negativas al usuario

**Resumen:** cuando el reloj de reproducción (`?at=`) es anterior al
`started_at` real de una ejecución de ingesta ya persistida en PostgreSQL —
algo que ocurre con el uso **normal y documentado** de la función de replay
(`apps/web/README.md`: "`?at=<ISO>` fija un instante base..."), no con ningún
caso extremo forzado—, `data_age_s`/`poll_age_s` se vuelven **negativos** y el
feed se reclasifica como `"unknown"` aunque tenga datos reales y vigentes. El
texto del propio contrato define `"unknown"` como *"sin ninguna ejecución de
ingesta registrada: ausencia de dato, no cero"* (`apps/api/snapshot.py:571-575`),
pero el caso real es justo lo contrario: el feed **sí tiene** una observación
válida, con cientos de entidades y marca de tiempo conocida.

**Evidencia en navegador** (captura `20-p0-novedades-unknown-lista.png`, con
la lista de la cinta abierta, `?at=2026-11-20T14:33:05Z`; transcripción del
texto en `24-transcripciones-devtools.md` §E; reproducido en dos sesiones
distintas sobre dos bases de datos distintas). *Corrección de la v2: la v1
remitía a las capturas 02 y 04, que no muestran este mensaje (la cinta rota y
en ellas aparece otra entrada); la medición no cambia.* La cinta "NOVEDADES"
muestra

> `vehicles: feed vehicle_positions en estado unknown: se conserva el último resultado válido con su edad real, no se vacía el recurso ni se rejuvenece el dato (hace 0 s)`

— un mensaje que **se contradice a sí mismo**: afirma que preserva "el último
resultado válido" mientras etiqueta el recurso como "unknown" (ausencia de
ingesta), y muestra "(hace 0 s)" aunque la edad real subyacente es negativa
(−15,74 s en la respuesta de la API).

**Reproducción directa contra la API** (sin ninguna extensión sintética mía,
solo los dos cortes reales `1532`/`1533` del kit):

```
curl "http://127.0.0.1:8010/api/v1/snapshot?at=2026-11-20T14:32:10Z"
```

```json
{
  "feed_name": "vehicle_positions",
  "status": "unknown",
  "source_timestamp": "2026-11-20T14:33:21Z",
  "data_age_s": -71.0,
  "poll_age_s": -71.0,
  "entities": 468,
  "rejected": 0
}
```

`entities: 468` y `source_timestamp` presentes — el feed tiene datos
perfectamente válidos — pero `status` es `"unknown"` y las edades son
negativas. Repetido dos veces de forma idéntica (determinista, no una
condición de carrera).

**Causa raíz, con archivo y línea exactos:**

1. `apps/api/db.py:178-223` (`recent_ingestion_runs`) selecciona la ejecución
   más reciente de cada feed por `started_at DESC` **global**, sin acotar por
   el `now`/`at` que va a usar el llamante.
2. `apps/api/service.py:359-399`, línea **381**:
   ```python
   elif data_age_s is None or data_age_s < 0 or poll_age_s < 0 or latest.status != "ok":
       status = "unknown"
   ```
   Una edad negativa (reloj de reproducción situado antes que una ingesta ya
   ocurrida en el tiempo real) se colapsa en el mismo estado que "nunca hubo
   ingesta", perdiendo la distinción que el propio contrato declara como
   importante.

**Por qué es P0, no un matiz de demo:** viola directamente el principio más
repetido en la documentación de este hito — "nunca rejuvenece el dato, nunca
vacía el recurso, nunca fabrica datos" — pero en sentido inverso: aquí el
sistema sí tiene el dato, y en su lugar **lo oculta y lo etiqueta como
ausente** frente al usuario, en la función de demo/replay que es justamente la
que se usará para mostrar el producto. Cualquier integración futura de
`MADRID_PULSE_MODE=live` con un historial persistente y una UI que permita
"volver a un instante anterior" heredaría el mismo problema.

**Alcance verificado:** confirmado en `/api/v1/snapshot` (y por tanto en el
banner "recursos degradados" y en la cinta de NOVEDADES del cliente). El
endpoint `/api/v1/stations/{id}/board?at=` **no** expone el campo `degraded`
en absoluto (verificado con `curl`), así que esta regresión concreta no
afecta al tablero de estación — solo a Live.

**Consistencia del resto del informe:** las capturas 03–19 se tomaron con
`?at=2026-11-20T14:33:40Z` (posterior a ambos cortes reales) para no
contaminar los demás hallazgos con este bug; en las de Live con banner
visible (p. ej. 04, 05, 11, 16) el banner lateral muestra "1 recurso(s)
degradado(s)" (solo `trip_updates`), frente a los "3 recurso(s)" de las
capturas 01 y 20, tomadas con `at=14:33:05Z`. Las
observaciones de UX de este informe son independientes de P0-1.

---

## 3. Hallazgos P1

Ninguno más allá de P0-1. No se encontraron destinos, horarios, retrasos o
campos de ficha incompatibles con la circulación seleccionada: la ficha de
`20842` (capturas `02` y `29`; árbol completo en `24-…md` §D) lista un
itinerario de 22 paradas de Móstoles-El Soto a Fuenlabrada, coherente con su
cabecera "Fuenlabrada"; el tablero de Atocha (capturas `05`, `06`, `07`)
muestra salidas C5 con destinos Humanes y Móstoles-El Soto,
marca explícitamente "esta llamada quedó atrás u omitida" en vez de inventar
una hora, y separa "Solo horario" de observado. History/Explore (capturas
`08`, `09`, `10`) muestran numerador/denominador reales (1304 programados /
122 observados / 1179 huecos / 3 anuladas) con el mensaje explícito de que la
cobertura depende de la ventana real del colector, no de la calidad del
servicio — exactamente el comportamiento que exige `AGENTS.md`.

---

## 4. Hallazgos P2

### P2-1 — Marcadores de circulaciones que se solapan o se apilan en la misma coordenada en la vista inicial

**Evidencia:** captura `21-zoom-defecto-carga-inicial.png` + medición
`21-medicion-solapamiento-zoom-defecto.json` (tomadas en la misma carga limpia,
`?at=2026-11-20T14:33:40Z`, con una separación de pocos segundos entre ambas);
contraste visual en `18-solapamiento-nucleo-madrid.png` y
`19-solapamiento-centro-detalle.png`.

**Qué está probado**

- El encuadre de carga es `MADRID_CENTER` `[-3.7038, 40.4168]` y `MADRID_ZOOM = 9.6`
  (`apps/web/src/map/MapView.tsx:28-29`, usado en la creación del mapa, líneas 187-188, y en el
  recentrado del botón «Centrar Madrid», líneas 469-473). En el navegador, tras una recarga limpia,
  `map.getZoom()` = 9,6 y `getCenter()` = `[-3.7038, 40.4168]` de forma estable durante 7 s, sin eventos
  de movimiento. (Registrado en la medición del JSON: `zoom: 9.6`, `center: [-3.7038, 40.4168]`.)
- En esa vista (canvas de 1080×604 px CSS, 104 de las 122 circulaciones dentro del encuadre), proyectando
  con `map.project` las posiciones que el propio cliente publica en cada fotograma (`window.__mpFrame`,
  solo build de desarrollo), con el diámetro del símbolo de línea 11,92 px (radio de `BODY_RADIUS` a
  z 9,6, `apps/web/src/map/layers.ts:58-66`): **162 pares** de centros más cercanos que el diámetro, **73
  circulaciones** implicadas, **102 pares** a menos de 0,5 px (mismo píxel), y como máximo **17**
  circulaciones en un entorno de 25 px de una de ellas. Además, **25 grupos** de circulaciones comparten
  *exactamente* la misma coordenada dibujada; los mayores: 6 × C5 (`19674, 19678, 19682, 20842, 20850,
  20854`), 5 × C5, y, entre los cinco mayores, tres grupos de 4 (C1, C3, C10).
- Contraste visual: en los encuadres de las capturas 18 (centro [-3,70, 40,41], z 11,3) y 19 (centro
  [-3,693, 40,415], z 13) los símbolos se distinguen individualmente, salvo algún par contiguo en la 18.
  No se repitió la medición numérica en esos encuadres (una primera tanda quedó contaminada por una
  navegación a la misma URL y se descartó), así que no se da ninguna cifra para ellos.

**Qué NO está probado (retirado respecto a la v1)**: "5-8 marcadores en un radio de ~25 px" (la medición
da otro orden de magnitud y depende del encuadre), que el zoom por defecto sea "el de ver toda la red",
y cualquier cifra sobre la zona Nuevos Ministerios–Atocha en concreto. Tampoco se ha medido que cada
fotograma publicado corresponda a un símbolo efectivamente dibujado (no se contrastó con
`queryRenderedFeatures`); lo medido son los fotogramas del cliente, no píxeles de la captura.

**Alcance honesto:** es una medición sobre un instante del replay (`displayAt` 14:34:00Z) con datos de
dos cortes de Renfe. No se ha investigado por qué coinciden tantas
circulaciones en el mismo punto (p. ej. paradas compartidas o extrapolación acotada) y no se afirma que
sea un defecto del movimiento. Con coordenadas idénticas sus símbolos se superponen exactamente (0 px),
de modo que, por inferencia —no verificada en píxeles—, la vista inicial no permite distinguir cuántas
circulaciones hay en cada punto. No recomiendo clustering ni efectos nuevos (coste de legibilidad y
rendimiento); como mucho, un indicador de recuento donde coincidan varias.

### P2-2 — El campo de búsqueda no tiene `id`/`name` (issue de DevTools)

**Archivo:** `apps/web/src/ui/SearchBox.tsx:40-50`. **Artefacto:** `24-transcripciones-devtools.md` §A y §B.

Chrome DevTools registra, en la carga de `/`, el issue `A form field element should have an id or name
attribute` (`msgid=23`, `count: 1`). El volcado de todos los campos de formulario del documento
(`input, select, textarea`) devuelve un único elemento, el buscador: `id: null`, `name: null`,
`role: "combobox"`, `aria-label: "Buscar estación o línea"`. El propio texto del issue aclara que esto
"isn’t strictly needed" y que solo puede afectar al autocompletado del navegador: es una
recomendación, no un fallo funcional. El árbol de accesibilidad sí expone el nombre del control
(`combobox "Buscar estación o línea"`); **no** se probó con un lector de pantalla real.
Corrección trivial: añadir `id`/`name` al `<input>`.

### P2-3 — En el fallback sin WebGL, «Seguir tren» activa un modo de cámara y un aviso que no se pueden cumplir

**Artefacto:** capturas `25-p2-3-antes-seguir-sin-webgl.png` y `26-p2-3-despues-seguir-sin-webgl.png`;
árbol de accesibilidad y consola en `24-transcripciones-devtools.md` §C.

*Corrección de la v2: la v1 decía que pulsarlo "no tiene ningún efecto observable". Era incorrecto: se
pulsó con un clic real y el efecto sí es observable.* Con WebGL desactivado (`initScript` sobre
`getContext`) y la ficha de la circulación 19874 abierta, tras pulsar «Seguir tren» el botón pasa a
«Dejar de seguir» (`pressed`) y dentro del panel del mapa, que sigue diciendo "Este navegador no ofrece
WebGL", aparece el texto **«Siguiendo · arrastra para soltar la cámara»** (captura 26). En ese modo no hay
mapa que arrastrar ni cámara que seguir, de modo que la acción ofrece un estado y una instrucción que
el usuario no puede cumplir. No hubo mensajes `error` ni `warn` en consola tras el clic (solo el issue de
P2-2). Sugerencia menor: ocultar/deshabilitar la acción, o cambiar el texto, cuando el mapa no está
disponible. No hay evidencia sobre cómo lo anunciaría un lector de pantalla.

### P2-4 — La leyenda del mapa tapa texto de la lista de novedades cuando esta se despliega

**Evidencia:** captura `20-p0-novedades-unknown-lista.png`. Con «Ver lista» abierta en escritorio
(1440×900), el recuadro flotante "Observada" de la leyenda queda encima de la tercera fila de la lista
("vehicles: feed vehicle_positions en estado unknown: se co[…]resultado válido…"), ocultando parte del
texto. Es un solapamiento puramente visual, visible en esa captura; no se ha comprobado en otros tamaños
de ventana ni en móvil.

---

## 5. DESCARTADO

### Divergencia visual entre la maqueta (`diseno/01-escritorio.png`) y la Live real

La maqueta de referencia (`diseno/01-escritorio.png`) muestra un plano
esquemático oscuro con solo C4/C5. La Live real
(captura `01-live-overview-desktop.png`) usa fondo claro y basemap real de
OpenStreetMap. **No lo cuento como defecto**: el propio
`docs/hitos/hito-03/diseno/INTERACCIONES.md` declara que los mapas de la
maqueta son "esquemas ilustrativos de C4 y C5" y que "la red de producción se
construye con los datos y trazados verificados de Madrid", y un basemap real
es una elección razonable para 12 líneas reales. Ambas pantallas comparten
titular serif grande ("Atocha" en la maqueta, "Cercanías Madrid" en la Live),
metadatos en mayúsculas pequeñas y chips de línea con color (comparación solo
visual entre las dos imágenes; ver §7 para lo que no se contrastó).

### "Mapa de la red" sin etiqueta de texto propia en las capas

`apps/web/README.md` (sección "Símbolos y accesibilidad") documenta que los
rótulos son marcadores DOM acotados al contexto seleccionado y no una capa
`symbol` con `text-field`, para no depender de un servidor de glifos
externo. En pantalla es coherente: la captura `05` muestra la etiqueta "Madrid-Atocha
Cercanías" junto a la estación seleccionada. Comportamiento deliberado y documentado, no un
hallazgo (no se inspeccionó la lista de capas del estilo en esta ronda).

---

## 6. Verificado correcto (evidencia positiva, no solo ausencia de bug)

Para que este informe no sea solo una lista de problemas, se registra aquí lo
que se intentó activamente romper y resistió. Cada punto indica su artefacto y
distingue lo probado en el navegador de lo leído en código.

- **`prefers-reduced-motion` (probado en navegador + código):** con `matchMedia`
  interceptado vía `initScript` (`27-reduced-motion-medicion.json`) frente a la
  misma carga sin override (`28-sin-reduced-motion-medicion.json`): el mapa se
  repinta **1 vez en 4 s** (cuando llega un snapshot nuevo) frente a **229
  veces** sin reduced-motion, y la cinta de novedades arranca en estado
  «Reanudar» (`aria-pressed="true"`, es decir, pausada) frente a «Pausar»
  (`aria-pressed="false"`). La captura `13-reduced-motion-live.png` solo muestra la app cargada con el
  override. Código que lo explica (solo lectura): `useReducedMotion`
  (`apps/web/src/hooks/useReducedMotion.ts`) alimenta `NewsTicker`
  (`src/ui/NewsTicker.tsx:32`: `if (paused || reducedMotion || items.length < 2) return;`)
  y `MapView` (`src/map/MapView.tsx:469-474`: `duration: reducedMotion ? 0 : 600`
  en el recentrado; `jumpTo` en la línea 301 en el seguimiento). **No** se probó
  en vivo el seguimiento de cámara con reduced-motion.
- **Arrastrar el mapa cancela el seguimiento (solo código, no probado en
  vivo):** `MapView.tsx:386`, `map.on("dragstart", release)`, con `followingRef`
  en `App.tsx:326-341`.
- **Fallback sin WebGL (probado en navegador):** interceptando
  `HTMLCanvasElement.getContext` vía `initScript` (capturas
  `14-sin-webgl-fallback.png`, `15-sin-webgl-ficha-tren.png`, `25`, `26`) la
  aplicación no intenta renderizar un mapa roto: muestra "Este navegador no
  ofrece WebGL" y dirige al panel de búsqueda/tablero. Se comprobó que la
  ficha de una circulación (19874) y su itinerario se abren sin mapa; **no**
  se probó en ese modo la ficha de estación. En la prueba de `Seguir tren` la
  consola solo contiene el issue de P2-2 (`24-…md` §C).
- **Búsqueda sin tilde (probado):** `mostoles` encuentra "Móstoles" y "Móstoles-El
  Soto" (captura `16-busqueda-sin-tilde.png`); `atocha` encuentra
  "Madrid-Atocha Cercanías" con sus 9 líneas (captura `04-busqueda-atocha.png`).
- **Escape cierra la búsqueda (probado):** el campo queda vacío y sin lista de
  resultados (captura `17-escape-cierra-busqueda.png`).
- **Parada omitida vs. dato ausente (probado):** el tablero de Atocha
  distingue "El operador ya declara una parada posterior: esta llamada quedó
  atrás u omitida" de "Solo horario, sin observación" (captura `06`).
- **Denominador/numerador reales en History/Explore (probado):** 1304
  programados, 122 observados, 1179 huecos, 3 anuladas (capturas `09`, `10`),
  con el aviso textual de que la cobertura depende de la ventana del colector
  ("lo archivado va de 15:32 a 15:33") y mide lo observado, no la calidad del
  servicio ferroviario (captura `10`).
- **Móvil (probado, 390×844 `touch`+`mobile` emulados):** el mapa ocupa la parte
  superior, los chips de línea se reparten en una cuadrícula legible y hay un
  enlace «Ampliar panel» (captura `11-live-mobile-390.png`).

---

## 7. NO VERIFICADO (limitaciones honestas de esta ronda)

- **«Ampliar panel» en móvil:** se ve el enlace (captura `11`), pero no se abrió
  el panel ampliado.
- **Lector de pantalla real:** no se probó con VoiceOver/NVDA; solo se inspeccionó
  el árbol de accesibilidad de Chrome. No hay evidencia de cómo se anuncia nada.
- **Seguimiento de cámara y gesto de arrastre en vivo** (con y sin reduced-motion):
  solo lectura de código.
- **Ficha de estación sin WebGL:** no se probó.
- **Contraste con el resto del diseño:** solo se comparó `diseno/01-escritorio.png`
  con la Live real (§5). No se contrastaron `02-movil.png`, `03-tren-sin-senal.png`,
  `04-explore.png` ni `live.html`, ni las referencias conceptuales de Via
  Península/Valfiguer; tampoco se evaluó contraste de color (ratios) ni
  tipografía de forma medida.
- **Simulación de señal** del selector de `INTERACCIONES.md` §3: ese control es del
  prototipo HTML de maqueta (`live.html`), no de la aplicación real auditada;
  no se buscó en `live.html` en esta ronda, así que esta frase es una lectura de
  `INTERACCIONES.md`, no una comprobación.
- **Rendimiento con muchos vehículos y estabilidad de memoria de MapLibre:** no se
  ejecutó ningún perfil (`performance_start_trace`, `take_heapsnapshot`). El único
  dato de rendimiento incidental es el recuento de repintados de §6.
- **P2-1:** medición de un solo instante del replay y de los fotogramas del cliente,
  no de píxeles (ver sus límites en P2-1).
- **Codex `gpt-5.6-terra` · high no tiene navegador real** (mismo límite de
  MP-020/MP-021/MP-022): su revisión confirmó P0-1 por la API (`curl`), no la UI.
  Para P0-1 basta repetir el `curl` de su sección variando `at` (cualquier
  instante anterior a `2026-11-20T14:33:21Z`).

---

## 8. Limpieza del entorno

Ronda v1: `docker stop madrid-pulse-aud05-postgres && docker rm madrid-pulse-aud05-postgres` (ejecutado).
Ronda v2: `docker stop aud05r-postgres && docker rm aud05r-postgres`, y procesos `uvicorn` (8037) y `vite` (5191)
detenidos al terminar. Contenedores desechables propios, nunca compartidos con otra tarea;
no se usó 5433, no se tocó `madrid-pulse-postgres-1` ni ninguna base de datos de otra tarea.
