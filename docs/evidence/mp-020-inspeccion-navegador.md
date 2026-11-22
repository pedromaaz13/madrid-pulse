# MP-020 — Inspección real en navegador (evidencia ejecutada)

Todo lo de este documento está **ejecutado y observado**, no descrito. Las
cifras son medidas reales; donde algo no se ha comprobado, se dice.

El prototipo `docs/hitos/hito-03/diseno/live.html` se usó como referencia de
interacción y jerarquía visual. **Ninguna evidencia de aquí procede del
prototipo**: todas las capturas y medidas son de `apps/web` contra la API
propia de este repositorio.

## Entorno real usado

| Dimensión | Valor |
|---|---|
| Node | `22.13.1` (vía `fnm`), npm `10.9.2` |
| Navegador | Chrome (Chrome DevTools MCP), viewport escritorio `1440×900` y móvil `390×844 @3x` con `mobile,touch` |
| Backend | `apps.api.main:app` con `uvicorn` real en `127.0.0.1:8010`, `MADRID_PULSE_MODE=replay` |
| GTFS | ZIP **completo** del núcleo (`data/hito-03/replay/fomento_transit.zip`, `sha256:c5b40823…`): 42 `route_id`, 12 líneas/variantes, 103 patrones, 95 estaciones |
| PostgreSQL | contenedor **desechable** `mp020-replay-db` (`postgis/postgis:17-3.5`, `127.0.0.1:5434`), migraciones `0001`+`0002` desde cero. **No se tocó la base de desarrollo** (`5433`) |
| Datos | capturas congeladas `1532`/`1533` del kit, ingeridas con el colector real (`apps/api/tools/replay_three_snapshots.py`). 122 circulaciones; 44 con coordenada `map_matched`, 78 con GPS bruto etiquetado |
| Frontend | `npm run dev` con `MADRID_PULSE_API_TARGET=http://127.0.0.1:8010` |

El puerto `8010` se usó porque `8000` estaba ocupado por una instancia ajena
a este worktree (el clon principal); no se detuvo ni se modificó. Por eso
`vite.config.ts` acepta ahora `MADRID_PULSE_API_TARGET`, conservando
`127.0.0.1:8000` como valor por defecto.

### Reloj de replay

El frontend admite `?at=<ISO>`: fija el instante base y avanza al ritmo del
reloj real, enviándolo al backend en cada sondeo. Dos ejecuciones desde el
mismo `?at=` recorren la misma secuencia, que es lo que hace repetible esta
evidencia. La etiqueta `REPLAY` y el instante mostrado están siempre
visibles en la barra superior: un replay nunca se presenta como directo.

## 1. Movimiento — secuencia continua de 60 s de la app real

Circulación `19656` (`1023V19656C5`, día de servicio `2026-11-20`, línea C5),
seguida con la cámara a zoom 13,2. Trece muestras de la posición realmente
dibujada, tomadas cada 5 s sobre fotogramas intermedios — no capturas
finales:

| t (s) | reloj mostrado | lon | lat | avance (m) | método |
|---|---|---|---|---|---|
| 0 | 14:34:00 | −3.806034 | 40.277627 | — | `extrapolated_from_last_anchor` |
| 5 | 14:34:05 | −3.807009 | 40.276973 | 110,2 | `extrapolated_from_last_anchor` |
| 10 | 14:34:10 | −3.807965 | 40.276302 | 110,2 | `extrapolated_from_last_anchor` |
| 15 | 14:34:15 | −3.808916 | 40.275627 | 110,2 | `extrapolated_from_last_anchor` |
| 20 | 14:34:20 | −3.809866 | 40.274952 | 110,2 | `extrapolated_from_last_anchor` |
| 25 | 14:34:25 | −3.810799 | 40.274262 | 110,2 | `extrapolated_from_last_anchor` |
| 30 | 14:34:30 | −3.811693 | 40.273539 | 110,5 | `extrapolated_from_last_anchor` |
| 35 | 14:34:35 | −3.812510 | 40.272769 | 110,2 | `extrapolated_from_last_anchor` |
| 40 | 14:34:40 | −3.813300 | 40.271982 | 110,2 | `extrapolated_from_last_anchor` |
| 45 | 14:34:45 | −3.814053 | 40.271175 | 110,2 | `extrapolated_from_last_anchor` |
| 50 | 14:34:50 | −3.814817 | 40.270374 | 110,1 | `extrapolated_from_last_anchor` |
| 55 | 14:34:55 | −3.815552 | 40.269558 | 110,1 | `extrapolated_from_last_anchor` |
| 60 | 14:35:00 | −3.816304 | 40.268749 | 110,2 | `extrapolated_from_last_anchor` |

Recorrido total **1 316,7 m en 60 s**. El avance por tramo se mantiene entre
110,1 y 110,5 m por cada 5 s = **22,0 m/s**, que es exactamente el
`speed_mps = 22,037` que publica la envolvente de esa circulación: el cliente
no acelera ni inventa nada, solo evalúa la regla del contrato. Ningún tramo
se desvía del resto, es decir **no hay teletransporte**. El rumbo cambia de
forma gradual porque la posición se proyecta sobre la polilínea del corredor
C5, no sobre una recta entre estaciones.

Capturas de la secuencia: `mp-020-capturas/seguimiento-t00s.png` y
`mp-020-capturas/seguimiento-t60s.png`. En la segunda se ve el tren sobre el
trazado C5 entre Humanes y Fuenlabrada **y, por detrás, el anillo de la
última lectura confirmada**, separado del símbolo porque la posición
mostrada es una proyección de hace 2 min — la ficha lo dice con esas
palabras: «Avance estimado desde la última observación; no es una lectura
GPS. Última lectura confirmada 15:33 · hace 2 min».

Muestreo adicional a 400 ms sobre cuatro circulaciones distintas: pasos de
8,79–8,84 m (22,0 m/s), 5,57–5,60, 5,23–5,26 y 5,61–5,64 m. Cada una avanza a
**su** velocidad declarada, no a una común.

### El cliente dibuja donde el backend dijo

`apps/web/src/domain/movement.test.ts` comprueba, sobre una grabación real de
la API (`src/__fixtures__/snapshot-map-matched.json`, instante
`2026-11-20T14:33:40Z`), que convertir `rendered.progress_m` a coordenada en
el cliente cae sobre `rendered.lat/lon` del backend: **error máximo < 1 m en
las 12 circulaciones map-matcheadas** de la grabación. La misma comprobación
hecha en Python contra las 44 del snapshot completo da **6,6 cm de error
máximo**; el resto es aritmética en coma flotante, no una aproximación de
modelo.

## 2. Selección, cámara y seguimiento

| Prueba | Resultado observado |
|---|---|
| Seguir tren | La cámara se engancha: el centro del mapa coincide con la posición dibujada (distancia 0) y se mueve de forma continua entre fotogramas |
| Arrastrar el fondo | `dragstart` suelta la cámara (`followKey → null`), que queda a 0,145° del tren y **no vuelve sola**. La ficha sigue siendo «Humanes» y la URL no cambia |
| «Volver al tren» | Reengancha la cámara (distancia 0) conservando la ficha |
| Dos sondeos | Sondeos 6 → 8: `followKey`, ficha, zoom (9,6) y centro intactos; 122 circulaciones |
| Caída del backend | Proceso suspendido 26 s: siguen las 122 circulaciones, la cámara, el seguimiento y la ficha. Aviso visible y **la edad avanza de «hace 1 min» a «hace 2 min» sin nuevos sondeos** |
| Recuperación | Al reanudar, el aviso desaparece y la edad pasa a «hace 3 min»: una respuesta con éxito **no rejuvenece** el dato |

Captura del estado degradado: `mp-020-capturas/04-fuente-caida.png`.

El seguimiento es siempre explícito: seleccionar no engancha la cámara, y si
la selección pasa a otra circulación el seguimiento no se arrastra, porque se
deriva de la selección vigente en lugar de guardarse por separado.

## 3. Navegación

| Prueba | Resultado observado |
|---|---|
| Búsqueda sin tilde | «alcorcon» encuentra **Alcorcón** (`35605`) |
| Teclado | Flechas recorren los resultados, Intro selecciona, Escape cierra sin perder contexto. Foco visible con contorno de 3 px `rgb(238,137,86)` |
| Enlace restaurable | `?at=…&train=19674&trip=1023V19674C5&sd=2026-11-20` reconstruye la circulación exacta al recargar (vehículo **y** viaje **y** día de servicio) |
| Atrás / Adelante | Tablero de Atocha → ficha de tren → Atrás vuelve al tablero → Adelante vuelve a la ficha |
| Estación compartida | Madrid-Atocha Cercanías aparece con sus líneas (C1 · C10 · C2 · …) en una ficha única |
| Tablero | Alcorcón devuelve 12 salidas reales con destino, hora, procedencia de la ETA y edad del retraso |

Capturas: `mp-020-capturas/02-tablero-alcorcon.png`,
`mp-020-capturas/03-ficha-tren.png`.

## 4. Accesibilidad, móvil y fallos

| Prueba | Resultado observado |
|---|---|
| Móvil 390 px | Sin desbordamiento horizontal (`scrollWidth` = `clientWidth` = 390). Panel inferior con botones además del gesto; «Ampliar panel» pasa el panel de 344 a 493 px |
| Tamaño táctil | Chips de línea y pastillas ≥ 38 px de alto en móvil; controles del mapa a 36 px |
| `prefers-reduced-motion` | **Deriva nula dentro de un intervalo** (0 m en 4 s) y un único repintado por snapshot aceptado, con paso discreto de 220,4 m. La cinta de novedades arranca pausada |
| Sin WebGL | Aviso explícito y el tablero sigue completo y navegable: `mp-020-capturas/06-sin-webgl.png` |
| Árbol de accesibilidad | Las 122 circulaciones son botones alcanzables con teclado, con línea, método de posición, edad y retraso en el texto |
| Líneas sin circulaciones | C4 aparece con contador `0` y sigue siendo seleccionable; no desaparece del catálogo |

Capturas móviles: `mp-020-capturas/05-movil-390.png`,
`mp-020-capturas/07-movil-seguimiento.png`.

## 5. Defectos reales encontrados **solo** mirando el navegador

Ninguno de estos lo detectó un test; todos están corregidos y verificados de
nuevo en navegador.

1. **Mapa invisible.** `maplibre-gl.css` llega en el chunk diferido de
   `MapView`, es decir después de la hoja propia, y su
   `.maplibregl-map { position: relative }` ganaba al `position: absolute`
   del contenedor por igual especificidad y orden. El contenedor quedaba con
   **altura 0** y no se veía ni un tile. Es el mismo género de fallo que
   MP-014 documentó con el worker.
2. **`snapshot_id` no sirve como señal de «hay dato nuevo».** Es identidad de
   contenido y se repite entre sondeos cuando los vehículos no cambian,
   aunque `display_at` avance. Usarlo para decidir el repintado dejaba el
   mapa congelado con movimiento reducido. La señal correcta es la
   `revision` del contrato.
3. **«Volver al tren» no aparecía nunca.** El estado se escribía dentro del
   actualizador de `setFollowKey`, que debe ser puro.
4. **Scroll horizontal en móvil 390 px** (449 px de ancho real) por la barra
   superior, cinta de 120 px de alto y leyenda pegada a la atribución.
5. **Código crudo del contrato en la interfaz**:
   `passed_or_skipped_per_operator_next_stop` se mostraba tal cual al usuario.
6. **Rótulos de estación solapados** al estar alejado el zoom.
7. **La ficha heredaba el desplazamiento** del tablero anterior y abría con
   la cabecera fuera de la vista.

## 6. Suites ejecutadas

```text
apps/web (Node 22.13.1)
  npm run lint       → limpio (--max-warnings 0)
  npm run typecheck  → limpio
  npm test           → 6 ficheros, 49/49 en verde
  npm run build      → OK, «Verified production MapLibre worker (550754 bytes)»

backend (.venv, Python 3.12.3, PostgreSQL de desarrollo 5433)
  python -m unittest (las 22 suites de .github/workflows/ci.yml)
                     → Ran 233 tests … OK
  recuentos antes y después: 668/484/3/120/0 (sin residuo)
```

## 7. Límites declarados de esta evidencia

- **No hay vídeo**: la evidencia de movimiento es la tabla de coordenadas de
  fotogramas intermedios de la sección 1 más las capturas inicial y final.
  Es más auditable que un vídeo para comprobar que no hay teletransporte,
  pero no lo sustituye si el propietario exige grabación.
- Las medidas de fluidez son de **una** máquina y un navegador (Apple
  Silicon, Chrome); no son un presupuesto ni un umbral universal.
- La secuencia usa el **replay** de dos cortes reales. No acredita cobertura
  GPS de toda la red en directo: 78 de las 122 circulaciones no tienen
  corredor validado y se dibujan con su GPS bruto etiquetado.
- El GTFS oficial publica `route_color` real de Renfe, pero el contrato
  `/api/v1/catalog` de MP-019 no lo expone y MP-020 no reescribe el
  contrato. La paleta de líneas del cliente es, por tanto, una elección de
  presentación propia y **no** el color corporativo del operador. Queda
  anotado por si MP-021/MP-022 quieren publicarlo.
- La base `mp020-replay-db` del puerto 5434 es desechable y queda levantada
  para que el revisor reproduzca lo mismo; no es la base de desarrollo.
