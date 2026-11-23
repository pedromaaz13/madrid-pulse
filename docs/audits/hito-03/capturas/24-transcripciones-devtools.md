# Transcripciones de Chrome DevTools MCP (AUD-05, ronda de corrección)

Salidas de las llamadas del MCP (literales; solo se abrevia con «…» donde un texto se repite), tomadas el 2026-11-23 contra la instancia local propia
(`apps/web` en `127.0.0.1:5191` → `apps/api` en `127.0.0.1:8037` → PostgreSQL desechable en `127.0.0.1:5456`).
Las capturas `.png`/`.json` asociadas están en este mismo directorio.

## A. P2-2 — issue de DevTools y campo de formulario (`list_console_messages` + `get_console_message` + `evaluate_script`)

`list_console_messages` (carga limpia de `/?at=2026-11-20T14:33:40Z`):

```
msgid=20 [debug] [vite] connecting... (1 args)
msgid=21 [info] %cDownload the React DevTools for a better development experience: https://react.dev/link/react-devtools font-weight:bold (2 args)
msgid=22 [debug] [vite] connected. (1 args)
msgid=23 [issue] A form field element should have an id or name attribute (count: 1)
msgid=24 [debug] [vite] connecting... (1 args)
msgid=25 [debug] [vite] connected. (1 args)
```

`get_console_message msgid=23`:

```
ID: 23
Message: issue> A form field element should have an id or name attribute

A form field element has neither an `id` nor a `name` attribute. This might stop the browser from correctly autofilling the form.

To fix this issue, add a unique `id` or `name` attribute to a form field. This isn’t strictly needed, but still recommended even if you have an autocomplete attribute on the same element.
### Affected resources
data={"violatingNodeId":2903,"violatingNodeAttribute":""}
```

`evaluate_script` — todos los campos de formulario del documento
(`[...document.querySelectorAll('input, select, textarea')]`):

```json
[{"tag":"input","type":"search","id":null,"name":null,"role":"combobox","ariaLabel":"Buscar estación o línea","className":""}]
```

Es el único campo de formulario de la página y no tiene `id` ni `name`. Nótese que el propio texto del issue dice que
"isn’t strictly needed": es una recomendación de autocompletado, no un fallo funcional.

## B. Nombre accesible del buscador (`take_snapshot`, árbol de accesibilidad)

```
uid=1_11 combobox "Buscar estación o línea" autocomplete="list" expandable haspopup="listbox"
```

Es lo que expone el árbol de accesibilidad de Chrome. **No** se probó con un lector de pantalla real (VoiceOver/NVDA).

## C. P2-3 — clic en «Seguir tren» sin WebGL (`initScript` que hace `getContext('webgl'|'webgl2') → null`)

URL: `/?at=2026-11-20T14:33:40Z&train=19874&trip=1023V19874C1&sd=2026-11-20`.

Antes del clic (`take_snapshot`, fragmento):

```
uid=2_16 button "Seguir tren"
uid=1_36 region "Mapa de la red"
  uid=1_37 StaticText "MAPA NO DISPONIBLE"
  uid=1_38 heading "Este navegador no ofrece WebGL" level="2"
```

Después de `click uid=2_16` (`take_snapshot`, fragmento):

```
uid=2_16 button "Dejar de seguir" focusable focused pressed
uid=1_36 region "Mapa de la red"
  uid=1_37 StaticText "MAPA NO DISPONIBLE"
  uid=1_38 heading "Este navegador no ofrece WebGL" level="2"
  uid=3_0 StaticText "Siguiendo · arrastra para soltar la cámara"
uid=1_47 paragraph live="polite" relevant="additions text"
  uid=1_48 StaticText "Circulación seleccionada: 19874"
```

`list_console_messages` tras el clic:

```
msgid=26 [debug] [vite] connecting... (1 args)
msgid=27 [info] %cDownload the React DevTools for a better development experience: https://react.dev/link/react-devtools font-weight:bold (2 args)
msgid=28 [debug] [vite] connected. (1 args)
msgid=29 [issue] A form field element should have an id or name attribute (count: 1)
```

Sin mensajes `error` ni `warn`. Capturas: `25-p2-3-antes-seguir-sin-webgl.png`, `26-p2-3-despues-seguir-sin-webgl.png`.
En ninguna de las dos hay un anuncio de lector de pantalla verificable: lo único observado es el árbol de accesibilidad de arriba.

## D. Ficha de la circulación 20842 — itinerario completo (`take_snapshot`)

`/?at=2026-11-20T14:33:40Z&train=20842&trip=1023V20842C5&sd=2026-11-20`:

```
heading "Fuenlabrada" level="1"
button "C5"   StaticText "Proyectada"
StaticText "Retraso +35 min"   StaticText "1023V20842C5"
heading "Itinerario" level="2"   StaticText "Patrón " "259c91" " · " "corredor validado"
Móstoles-El Soto · Móstoles · Las Retamas · Alcorcón · San José de Valderas · Cuatro Vientos · Las Águilas ·
Maestra Justa Freire-Polidep. Aluche · Aluche · Laguna · Embajadores · Madrid-Atocha Cercanías · Méndez Álvaro P.V. ·
Doce de Octubre · Orcasitas · Puente Alcocer · Madrid-Villaverde Alto · Zarzaquemada · Leganés · Parque Polvoranca ·
La Serna-Fuenlabrada · Fuenlabrada
```

Captura del tramo inicial del itinerario: `29-ficha-20842-itinerario.png`.

## E. P0-1 en la UI — cinta NOVEDADES con la lista abierta (`evaluate_script` sobre el DOM)

`/?at=2026-11-20T14:33:05Z`, tras pulsar «Ver lista»; texto de `footer`:

```
NOVEDADES
alerts: feed alerts en estado unknown: se conserva el último resultado válido con su edad real, no se vacía el recurso ni se rejuvenece el dato (hace 0 s)
1/3 …
alerts: feed alerts en estado unknown: … (hace 0 s)
delays_and_eta: feed trip_updates en estado error: …
vehicles: feed vehicle_positions en estado unknown: se conserva el último resultado válido con su edad real, no se vacía el recurso ni se rejuvenece el dato (hace 0 s)
```

Banner lateral en el mismo instante: `3 recurso(s) degradado(s): se conserva el último dato válido con su hora.`
Captura: `20-p0-novedades-unknown-lista.png`.

## F. Reduced-motion: medición contrastada (`27-…json` frente a `28-…json`)

| | `prefers-reduced-motion: reduce` (override de `matchMedia` vía `initScript`) | sin override |
|---|---|---|
| `window.matchMedia(...).matches` | `true` | `false` |
| sonda del cliente `__mpFrame().reducedMotion` | `true` | `false` |
| repintados del mapa en 4 s (`paintCount`) | **1** | **229** |
| cinta de novedades | botón «Reanudar», `aria-pressed="true"` (arranca pausada) | botón «Pausar», `aria-pressed="false"` |

(`__mpFrame` es una sonda que `MapView.tsx:248-250` solo publica en el build de desarrollo.)
