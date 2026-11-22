# apps/web — Madrid Pulse Live (MP-020)

Cliente estático React + TypeScript + MapLibre GL JS para **toda la red de
Cercanías Madrid**. Consume exclusivamente la API propia `/api/v1/*`; Vite la
proxifica en desarrollo. No contiene fixtures ni respuestas simuladas en la
build: la única fixture del repositorio vive en `src/__fixtures__/` y la usan
los tests, declarando dentro del propio fichero que es una grabación real de
esta API.

```sh
npm ci
npm run dev
```

## Contrato que consume (MP-019, ADR-0014)

- **`GET /api/v1/catalog`** — cacheable. Se descarga una vez y se revalida con
  `ETag`; un `304` conserva el índice ya construido. De él salen líneas,
  patrones, estaciones y geometrías, y los índices de longitud de arco que se
  calculan **una sola vez por `catalog_version`**.
- **`GET /api/v1/snapshot`** — ligero, `no-store`. Las respuestas se ordenan
  por `revision` (`scope` + `sequence`, desempate por `generated_at`).
  `snapshot_id` **nunca** se ordena: es identidad de contenido y el propio
  payload lo declara con `snapshot_id_is_sortable: false`. Tampoco sirve como
  señal de «ha llegado dato nuevo», porque se repite entre sondeos cuando los
  vehículos no han cambiado aunque `display_at` avance.
- **`GET /api/v1/stations/{id}/board`** — tablero calculado con calendario,
  horario y actualizaciones en tiempo real; el cliente solo lo presenta, no
  ordena por cercanía geográfica.
- **`GET /api/v1/health`** — salud, adquirida por separado.

Cada recurso se adquiere con su propio hook: una lectura en vuelo por
recurso, timeout y cancelación propios, descarte de respuestas antiguas y
conservación del último valor bueno ante un fallo. No hay ningún
`Promise.all` como bloque indivisible de éxito, y una respuesta con éxito no
rejuvenece el dato: la edad se recalcula siempre contra los timestamps del
propio contrato.

## Movimiento

El backend publica una `ProgressEnvelope` por circulación y el cliente la
evalúa con la fórmula fijada por el contrato, sin reinventarla:

```text
t0 = dwell_until or reference_at
progress(t) = min(progress_m_at_reference + speed_mps · max(0, t − t0),
                  max_progress_m)
```

El progreso **dirigido** se convierte en longitud de arco **física**
(`forward ? progress_m : corridor_length_m − progress_m`, con el sentido
derivado del orden real de las paradas sobre el corredor) y de ahí a
coordenada sobre la polilínea del patrón. **Nunca** se interpola lat/lon en
línea recta entre estaciones. Agotada la vigencia (`rendered.valid_until`) el
símbolo se congela: el cliente no extrapola más allá de lo que el contrato
autoriza, y ningún fotograma se archiva como observación.

Un test comprueba contra una grabación real de la API que la coordenada que
calcula el cliente cae sobre la que publicó el backend (error < 1 m).

El reloj de presentación vive en un `requestAnimationFrame` que escribe
directamente en las fuentes de MapLibre: no hay `setState` por fotograma.

## Símbolos y accesibilidad

El **color identifica la línea** y nada más. La procedencia de la posición se
distingue por **contorno, forma interior y texto**, de modo que el símbolo
sigue siendo legible en escala de grises. Cuando la posición mostrada ya no es
una observación (`extrapolated_from_last_anchor` o `stale_frozen`) se dibuja
además el **anillo de la última lectura confirmada**.

El índice de confianza es heurístico y no calibrado: no aparece como
porcentaje en la vista principal, solo en el detalle técnico y nombrado como
índice.

Las capas del mapa no llevan texto propio: un `symbol` con `text-field`
exigiría un servidor de glifos externo y la aplicación no depende de ninguno
fuera de las teselas de OpenStreetMap. Los rótulos son marcadores DOM
acotados al contexto seleccionado y solo cuando el zoom permite leerlos.

Con `prefers-reduced-motion` no hay animación espacial automática: las
posiciones se evalúan en el instante de presentación del snapshot y el mapa
solo repinta cuando llega una respuesta nueva. La cinta de novedades arranca
pausada y nunca es un carrusel obligatorio.

Sin WebGL la aplicación no muestra un mapa roto: sirve la alternativa de
lista y tablero, que es navegable por completo.

### Paleta de líneas — limitación declarada

El GTFS oficial publica `route_color` real de Renfe, pero el contrato
`/api/v1/catalog` no expone ese campo y MP-020 no reescribe el contrato. La
paleta es por tanto una elección de presentación del cliente, asignada de
forma determinista por `line_id` y **sin identificadores de línea incrustados
en la lógica** (ADR-0011); no es el color corporativo del operador.

## Modo replay

`?at=<ISO>` fija un instante base y lo hace avanzar al ritmo del reloj real,
enviándolo al backend en cada sondeo. Dos ejecuciones desde el mismo `?at=`
recorren la misma secuencia, lo que hace reproducible la demostración sobre
cortes congelados. La etiqueta `REPLAY`/`LIVE` y el instante mostrado están
siempre visibles: un replay nunca se presenta como directo.

El resto del estado también vive en la URL y es restaurable:
`?station=<id>`, `?train=<vehículo>&trip=<viaje>&sd=<día de servicio>` —los
tres campos, porque `vehicle_id` no es identidad de circulación— y
`?lines=C4,C5`. La navegación entre objetos usa `pushState`, así que el botón
Atrás vuelve al contexto anterior; la cámara no entra en el historial.

## Verificación local

```sh
npm run lint
npm run typecheck
npm test
npm run build
npm run preview
```

Para levantarlo contra un backend en otro puerto (por ejemplo si `8000` ya
está ocupado por otra instancia local):

```sh
MADRID_PULSE_API_TARGET=http://127.0.0.1:8010 npm run dev
```

La calidad visual es un requisito real: `npm test` y `npm run build` **no**
acreditan esta aplicación. La evidencia de inspección en navegador está en
`docs/evidence/mp-020-inspeccion-navegador.md`.

## Notas heredadas de MP-014 que siguen vigentes

`vite.config.ts` excluye `maplibre-gl` del prebundle de dependencias en
desarrollo: Vite respondía `504` para su worker ESM prebundled y dejaba sin
procesar las fuentes GeoJSON. En producción un plugin local emite
`dist/assets/maplibre-gl-worker.mjs`, `MapView` fija esa URL con
`setWorkerUrl` y `npm run build` compara el asset byte a byte con el paquete
instalado para impedir que un fallback HTML pase por worker válido.
