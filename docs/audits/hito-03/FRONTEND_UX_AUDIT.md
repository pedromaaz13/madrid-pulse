# AUD-05 — Auditoría exhaustiva del frontend en navegador real

**Ejecuta:** Claude Sonnet (worker dispatchado, contexto aislado)
**Revisa:** Codex Terra · High (pendiente)
**Fecha:** 2026-11-23
**Rama:** `audit/hito-03-adversarial`
**Worktree:** `/Users/matu/orca/workspaces/madrid-pulse/audit-hito-03`
**Commit base auditado:** `d349465` (cadena MP-016→MP-022 + AUD-00/02/07 ya registrados)

No se ha modificado código de producto. Todos los hallazgos de este documento
se verificaron con **Chrome DevTools MCP real** (`new_page`, `navigate_page`,
`take_screenshot`, `take_snapshot`, `emulate`, `evaluate_script`,
`list_console_messages`, `list_network_requests`) contra una instancia local
de `apps/api` + `apps/web` propia, nunca contra código leído sin ejecutar.

## 1. Entorno levantado para esta auditoría

Instancia completamente propia y desechable, nunca comparte estado con otras
tareas:

| Componente | Detalle |
|---|---|
| PostgreSQL/PostGIS | Contenedor Docker propio `madrid-pulse-aud05-postgres` (`postgis/postgis:17-3.5`), puerto `127.0.0.1:5455`, migraciones `0001_init`/`0002_api_batch_indexes` aplicadas. Destruido al terminar (§8). |
| Datos | `data/hito-03/replay/` repuesto vía `instalar.py --worktree "$PWD" --solo-datos` (dos cortes reales Renfe `1532`/`1533`, 2026-11-20, GTFS estático completo del núcleo). |
| Ingesta | `apps.api.tools.replay_three_snapshots` (colector real, `run_cycle`), 122 vehículos únicos insertados con `payload_hash`/dedupe reales. |
| Histórico | `services.snapshotter 2026-11-20` con `MADRID_PULSE_SHORT_NAME=` (núcleo completo, no el valor por defecto `C5`) → 1304 viajes programados, 69 estaciones, 35 rutas con métrica diaria. |
| API | `uvicorn apps.api.main:app` en `127.0.0.1:8010`, `MADRID_PULSE_MODE=replay`, GTFS completo. |
| Web | `npm run dev -- --port 5180` en `apps/web`, `MADRID_PULSE_API_TARGET=http://127.0.0.1:8010` (proxy `/api` propio, puerto por defecto 8000 libre para otras instancias). |
| Navegador | Chrome DevTools MCP real, confirmado operativo con `new_page` antes de capturar nada (ver mensaje al coordinador). |

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

**Evidencia en navegador** (capturas `02-ficha-tren-c5-20842.png`,
`04-busqueda-atocha.png`): la cinta "NOVEDADES" muestra, de forma persistente
y reproducible,

> `vehicles: feed vehicle_positions en estado unknown: se conserva el último resultado válido con su edad real, no se vacía el recurso ni se rejuvenece el dato (hace 0 s)`

— un mensaje que **se contradice a sí mismo**: afirma que preserva "el último
resultado válido" mientras etiqueta el recurso como "unknown" (ausencia de
ingesta), y el "(hace 0 s)" nunca avanza porque la edad real subyacente es
negativa.

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

**Captura adicional de consistencia:** `03-live-zoom-atocha-centro.png` y
`05-ficha-estacion-atocha.png` fueron tomadas con `?at=2026-11-20T14:33:40Z`
(posterior a ambos cortes reales) precisamente para que el resto de hallazgos
de este documento no quedaran contaminados por este bug — todas las demás
observaciones de UX en este informe son independientes de P0-1.

---

## 3. Hallazgos P1

Ninguno más allá de P0-1. No se encontraron destinos, horarios, retrasos o
campos de ficha incompatibles con la circulación seleccionada: la ficha de
`20842` (captura `02`) lista un itinerario real Móstoles-El Soto→Fuenlabrada
coherente con su cabecera "Fuenlabrada"; el tablero de Atocha (capturas `05`,
`06`, `07`) distingue correctamente destinos de paso en ambos sentidos de C5,
marca explícitamente "esta llamada quedó atrás u omitida" en vez de inventar
una hora, y separa "Solo horario" de observado. History/Explore (capturas
`08`, `09`, `10`) muestran numerador/denominador reales (1304 programados /
122 observados / 1179 huecos / 3 anuladas) con el mensaje explícito de que la
cobertura depende de la ventana real del colector, no de la calidad del
servicio — exactamente el comportamiento que exige `AGENTS.md`.

---

## 4. Hallazgos P2

### P2-1 — Solapamiento de marcadores en el núcleo de Madrid al zoom de red completa

**Capturas:** `16-busqueda-sin-tilde.png`, `17-escape-cierra-busqueda.png`,
`18-solapamiento-nucleo-madrid.png`.

Con las 12 líneas activas y zoom de "ver toda la red" (el que ofrece
"Centrar Madrid" por defecto), el racimo de estaciones en el entorno de
Nuevos Ministerios–Sol–Atocha–Méndez Álvaro concentra 5-8 marcadores de
vehículo en un radio de ~25 px. Son distinguibles por color pero no por forma
a simple vista a ese zoom; hace falta acercar el zoom (captura `19`, donde a
zoom 13 ya se separan con claridad) para leerlos. No es un error de datos —
cada marcador representa una circulación real y el propio contrato nunca
fabrica una posición — es una cuestión de legibilidad en el nivel de zoom por
defecto, exactamente el "solapamiento de marcadores/etiquetas" que el
encargo pide revisar activamente. Dado que el diseño ya resuelve
correctamente el caso a mayor zoom, no recomiendo clustering adicional
(coste de legibilidad/rendimiento) sino, como mucho, que el zoom inicial de
"Centrar Madrid" en modo "Todas las líneas" seleccione un nivel ligeramente
mayor que el actual.

### P2-2 — El campo de búsqueda no tiene `id`/`name`

**Archivo:** `apps/web/src/ui/SearchBox.tsx:40-50`.

Chrome DevTools marca de forma consistente, en todas las vistas con el buscador
montado: *"A form field element should have an id or name attribute"*
(`list_console_messages`, tipo `issue`, confirmado en capturas `01` a `18`).
El `<input role="combobox" aria-label="Buscar estación o línea">` tiene buena
semántica ARIA (confirmada en los `take_snapshot` de este informe: lectores
de pantalla lo anuncian correctamente), pero sin `id`/`name` los gestores de
contraseñas y algunas heurísticas de autocompletado del navegador no pueden
asociarlo de forma estable. Corrección trivial: añadir `id="station-search"`
(o similar) al `<input>`.

### P2-3 — "Seguir tren" visible sin mapa en el fallback sin WebGL

**Captura:** `15-sin-webgl-ficha-tren.png`.

En el fallback sin WebGL (correctamente implementado, ver §6) la ficha de
circulación sigue mostrando el botón "Seguir tren". Pulsarlo no provoca error
(confirmado, consola limpia tras el click) pero tampoco tiene ningún efecto
observable porque no hay mapa que centrar. No es un fallo funcional — es una
affordance que promete una acción sin consecuencia visible en ese modo.
Sugerencia menor: ocultar o deshabilitar "Seguir tren" cuando el mapa no está
disponible.

---

## 5. DESCARTADO

### Divergencia visual entre la maqueta (`diseno/01-escritorio.png`) y la Live real

La maqueta de referencia usa un esquema oscuro, un plano esquemático
(solo C4/C5) y tipografía de palo seco de alto contraste. La Live real
(captura `01-live-overview-desktop.png`) usa fondo claro, basemap real de
OpenStreetMap y una serif editorial para titulares. **No lo cuento como
defecto**: el propio `docs/hitos/hito-03/diseno/INTERACCIONES.md` declara
explícitamente que la maqueta es "un esquema ilustrativo... la red de
producción se construye con los datos y trazados verificados de Madrid", y
un basemap real es la elección correcta para 12 líneas reales con geometría
OSM verificada (frente a un esquema de 2 líneas). La jerarquía tipográfica
(titular serif grande, metadatos en mayúsculas pequeñas, chips de línea con
color) sí se conserva fielmente respecto a la maqueta.

### "Mapa de la red" sin etiqueta de texto propia en las capas

Confirmado en código (`apps/web/README.md`, sección "Símbolos y
accesibilidad") y en pantalla: las etiquetas de estación son marcadores DOM,
no `symbol`/`text-field` de MapLibre, precisamente para no depender de un
servidor de glifos externo. Comportamiento deliberado y documentado, no un
hallazgo.

---

## 6. Verificado correcto (evidencia positiva, no solo ausencia de bug)

Para que este informe no sea solo una lista de problemas, se registra aquí lo
que se intentó activamente romper y resistió:

- **`prefers-reduced-motion`:** confirmado con `matchMedia` interceptado vía
  `initScript` (captura `13-reduced-motion-live.png`) + lectura de código:
  `useReducedMotion` (`apps/web/src/hooks/useReducedMotion.ts`) alimenta
  `NewsTicker` (`src/ui/NewsTicker.tsx:32`: `if (paused || reducedMotion ||
  items.length < 2) return;` — no rota) y `MapView`
  (`src/map/MapView.tsx:469-474`: `duration: reducedMotion ? 0 : 600` en el
  `easeTo` de recentrado, y `jumpTo` en vez de interpolación por fotograma
  en la línea 301 cuando `reducedMotion` está activo).
- **Arrastrar el mapa cancela el seguimiento:** `MapView.tsx:386`,
  `map.on("dragstart", release)`, con `followingRef` en `App.tsx:326-341`.
- **Fallback sin WebGL:** interceptando `HTMLCanvasElement.getContext` vía
  `initScript` (capturas `14-sin-webgl-fallback.png`,
  `15-sin-webgl-ficha-tren.png`) la aplicación nunca intenta renderizar un
  mapa roto: muestra "Este navegador no ofrece WebGL" y dirige explícitamente
  al panel de búsqueda/tablero, que permanece 100 % navegable (confirmado
  seleccionando una estación y una circulación reales sin mapa).
  Consola sin errores nuevos en ningún momento de esta prueba.
  (`src/map/webgl.ts` es el punto de detección).
- **Búsqueda sin tilde:** `mostoles` encuentra "Móstoles" y "Móstoles-El
  Soto" (captura `16-busqueda-sin-tilde.png`).
  `atocha` encuentra "Madrid-Atocha Cercanías" con sus 9 líneas reales
  (captura `04-busqueda-atocha.png`).
- **Escape cierra la búsqueda** sin dejar residuo de texto ni de resultados
  (captura `17-escape-cierra-busqueda.png`).
- **Parada omitida vs. dato ausente:** el tablero de Atocha distingue
  explícitamente "El operador ya declara una parada posterior: esta llamada
  quedó atrás u omitida" de "Solo horario, sin observación" — dos estados
  reales que el encargo pedía verificar activamente que no se confundieran
  (captura `06`).
- **Denominador/numerador reales en Explore:** 1304 programados vs. 122
  observados vs. 1179 huecos vs. 3 anuladas, con el aviso textual de que la
  cobertura depende de la ventana del colector, no de la calidad del
  servicio ferroviario (captura `10`).
- **Móvil (390×844, `touch`+`mobile` emulados):** mapa protagonista, chips de
  línea en grid legible, "Ampliar panel" presente para leer el itinerario
  completo sin perder el mapa (captura `11-live-mobile-390.png`).

---

## 7. NO VERIFICADO (limitaciones honestas de esta ronda)

- **"Ampliar panel" en móvil:** se confirmó que el enlace existe y es
  accesible (captura `11`), pero no se interactuó con el panel ampliado en
  detalle (contenido completo del itinerario a pantalla completa en 390 px).
- **Simulación de señal (GPS/interpolación/estimación/obsoleta/sin
  conexión)** del selector descrito en `INTERACCIONES.md` §3: ese control es
  específico del prototipo HTML de maqueta (`live.html`), no de la aplicación
  real auditada aquí — la app real no tiene ese selector de demo, usa datos
  de replay reales en su lugar. Se señala para que quien revise no espere
  encontrarlo.
- **Rendimiento con un volumen de vehículos mucho mayor (cientos
  simultáneos) y estabilidad de memoria de MapLibre en sesiones largas:** no
  se ejecutó un perfil de rendimiento/heap (`performance_start_trace`,
  `take_heapsnapshot`) en esta ronda por alcance de tiempo; esta auditoría se
  concentró en corrección de datos y UX. Recomiendo una ronda específica de
  rendimiento si no está ya cubierta por otra tarea AUD.
- **Codex Terra · High** no tiene navegador real disponible en su contexto
  (mismo límite ya documentado en MP-020/MP-021/MP-022): su revisión de este
  informe será sobre el documento y el código citado, no una repetición en
  vivo. El coordinador debería reproducir personalmente, como mínimo, P0-1
  (tres comandos `curl` reproducibles arriba) antes de aceptar este informe.

---

## 8. Limpieza del entorno

Al terminar esta auditoría:

```sh
docker stop madrid-pulse-aud05-postgres && docker rm madrid-pulse-aud05-postgres
```

Contenedor desechable propio, nunca compartido con otra tarea; no se tocó
`madrid-pulse-postgres-1` (el contenedor compartido existente) ni ninguna
base de datos de otra tarea MP-0XX/AUD-0X.
