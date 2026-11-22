> REFERENCIA HISTÓRICA DE ANÁLISIS. Sus quince tareas UX y reparto no son ejecutables como una segunda cadena. Aplicar REVISION-Y-DECISIONES.md y MEJORAS-PRODUCTO-VALIDADAS.md; el reparto vigente está en PLAN-Y-ACEPTACION.md.

# Madrid Pulse — Plan concreto de experiencia de producto para Orca

**Fecha:** 21/11/2026  
**Ámbito:** producto ferroviario, frontend, movimiento, objetos interactivos y navegación.  
**Destino sugerido dentro del repositorio:** docs/hitos/hito-03/MADRID_PULSE_PRODUCT_UX_PLAN.md  
**Estado:** propuesta de desarrollo; este documento no acredita cambios implementados ni pruebas ejecutadas.

## 0. Instrucción de uso para Orca

Leer este documento junto con AGENTS.md, docs/STATUS.md, docs/TASKS.md, docs/HITO_3_BACKLOG.md, docs/DATA_CONTRACTS.md y los ADR vigentes.

Antes de convertirlo en tareas, comprobar main, las ramas y los worktrees locales. Las observaciones siguientes corresponden al código publicado; puede haber trabajo local posterior que deba conservarse. Integrar las propuestas en el backlog existente, evitando duplicados y respetando decisiones más recientes del propietario.

El objetivo de Hito 3 de ampliar Cercanías Madrid se mantiene. Este plan incorpora la experiencia que debería acompañar a esa ampliación y los cambios técnicos que la hacen posible.

Los identificadores UX-01…UX-15 son referencias de planificación de este documento. No asignan números MP-XXX ni estados DONE a tareas reales.

**Encargo:** convertir el piloto actual en una aplicación de movilidad que permita explorar la red, seleccionar un tren, seguirlo, abrir estaciones y líneas, buscar y compartir una vista, con movimiento fluido sobre las vías y calidad del dato comprensible.

No incorpora tráfico urbano, rutas en coche, otros núcleos ni una migración de stack. Esos ámbitos se tratarán en sus entregas.

## 1. Baseline comprobado y procedencia de las propuestas

### Versiones revisadas

- Madrid Pulse: main en **990c95dfa58cabcf664b905318a4a84fe1cecf19**.
- Vía Península: main en **66d468a4f170a3245ea637956fefa1b216afaf32**.
- Valfiguer: documentación pública de API y página Acerca consultadas el 21/11/2026.

Se han inspeccionado archivos de implementación de Madrid Pulse y Vía Península. No se han ejecutado aquí las aplicaciones ni sus suites. La inspección visual completa de los mapas externos quedó limitada por errores de carga en la investigación previa. Las propuestas de diseño se basan en código, documentación y criterio de producto; no en un benchmark visual móvil realizado.

### Tres categorías que no deben confundirse

| Categoría | Qué significa |
|---|---|
| Hallazgo | Comportamiento deducido directamente del código actual revisado |
| Referencia | Patrón descrito o implementado en un proyecto externo |
| Propuesta | Comportamiento a implementar y validar en Madrid Pulse |

Este documento no propone consumir Valfiguer como API de producción. Madrid Pulse mantiene Renfe GTFS/GTFS-RT y almacenamiento propios.

Vía Península utiliza AGPL-3.0. AGENTS.md permite estudiar su arquitectura y patrones, pero establece que no se copie ni importe su código sin un ADR específico. Toda implementación propuesta aquí debe ser propia. Las interfaces y pseudocódigo de este documento son diseños propuestos, no código extraído de sus repositorios.

## 2. Resultado de producto esperado

Una persona abre Madrid Pulse y el mapa es utilizable desde el primer momento. Reconoce líneas y estaciones, pulsa un tren y entiende a dónde va. Puede seguirlo mientras se mueve sobre su recorrido, abrir una estación, consultar próximos servicios y volver al tren sin perderse.

No necesita interpretar un vehicle_id o trip_id para usar la aplicación. Puede consultar los detalles de calidad cuando los necesita.

### Recorrido principal de la demo

1. Abrir el mapa de Cercanías Madrid.
2. Buscar una estación, por ejemplo Alcorcón.
3. Abrir su ficha y los servicios disponibles según los datos.
4. Seleccionar un tren.
5. Consultar destino, próximas paradas y antigüedad de la observación.
6. Activar seguimiento.
7. Arrastrar el mapa: la cámara deja de seguir, pero la ficha permanece.
8. Pulsar “Volver al tren” y reanudar seguimiento.
9. Abrir la ficha de una parada del itinerario.
10. Compartir un enlace que reconstruya el objeto y el contexto.

Los nombres y servicios de los ejemplos se validarán contra el GTFS cargado. No deben convertirse en datos inventados de una demo.

### Qué hace que se perciba como producto

- El mapa ocupa el espacio principal.
- Los elementos tienen identidad, selección y acciones.
- La cámara responde a la intención de la persona.
- El movimiento conserva geometría, tiempo y significado.
- Mapa, ficha y listado expresan la misma situación.
- Una caída de fuente tiene un estado comprensible.
- El contenido útil aparece antes que el diagnóstico técnico.

## 3. Auditoría del frontend actual: cambios concretos

| Archivo | Hallazgo comprobado | Cambio propuesto |
|---|---|---|
| apps/web/src/App.tsx | Concentra adquisición, filtros, layout, estados y lista | Convertirlo en composición de funcionalidades |
| App.tsx | POLL_INTERVAL_MS = 20_000; fetchDashboard en cada ciclo | Separar catálogo, datos vivos y salud |
| App.tsx | Promise.all agrupa tres recursos | Conservar resultados parciales y el último dato válido |
| App.tsx | No tiene estado explícito de objeto seleccionado | Introducir selección única y navegación |
| App.tsx | Filtra trenes con vehicle.line === selectedLine.line_id | Migrar a claves canónicas con red/route/patrón |
| App.tsx | El contenido principal incluye un gran bloque introductorio | Mapa como primera pantalla; explicación en Ayuda |
| App.tsx | Las tarjetas muestran vehicle_id, trip_id y confianza porcentual | Priorizar línea, destino, próxima parada y dato disponible |
| apps/web/src/MapView.tsx | Elimina y recrea todos los marcadores al cambiar vehicles | Reconciliación estable y después capa WebGL según presupuesto |
| MapView.tsx | Los botones de tren tienen título y aria-label, sin acción de selección | Click/tap/teclado conectados a la misma selección |
| MapView.tsx | stationFeatures publica solo name como propiedad | Incluir station_id y clave canónica para abrir estación |
| MapView.tsx | No hay bucle de animación entre snapshots | Añadir controlador de presentación temporal |
| MapView.tsx | Mapa base raster tile.openstreetmap.org | Evaluar estilo vectorial para jerarquía y tema |
| apps/web/src/types.ts | Vehicle no incluye destino, patrón ni itinerario | Evolucionar el contrato desde información verificada |
| apps/web/src/api.ts | Cast de response.json; sin validación de contrato ni timeout propio | Validación acotada y errores por recurso |
| apps/web/src/styles.css | Mapa acotado y panel lateral que se apila debajo | Layout de aplicación con panel adaptable |
| apps/web/src/MapView.test.tsx | Prueba arranque, geometría y errores con mock | Añadir pruebas de interacción y navegador real para animación |

### Lo que ya funciona y debe preservarse

- Instancia de MapLibre conservada mediante referencias.
- Aplicación de geometría aunque llegue después del evento load.
- Ajuste de cámara protegido por identidad de línea: el código actual no hace fitBounds en cada polling.
- Segmentos geométricos separados; no se concatenan arbitrariamente.
- Atribución visible y controles del mapa.
- Configuración del worker de MapLibre en producción.
- Cuatro modos de posición y cobertura explícita del retraso.

El rediseño debe conservar estos comportamientos y sus pruebas. No corregir un síntoma de UX reintroduciendo fallos de carga del worker o puentes geométricos falsos.

## 4. Qué trasladamos de Vía Península y de Valfiguer

| Experiencia | Referencia concreta | Adaptación propuesta |
|---|---|---|
| Movimiento entre lecturas | Vía: src/web/main.ts y ADR-0002 | Un reloj de presentación y recorrido parametrizado |
| Tren reconocible al hacer zoom | Vía: src/web/pill.ts | Punto a baja escala; etiqueta de línea a escala útil |
| Seguir un tren | Vía: estado following y cámara en main.ts | Selección y seguimiento como estados distintos |
| Soltar seguimiento al arrastrar | Vía: letGo, dragstart y movestart | Ceder la cámara al gesto humano sin cerrar la ficha |
| Mapa como primera pantalla | Vía: ADR-0011 | App shell con paneles sobre el mapa |
| Vista persistida | Vía: src/web/view.ts | URL explícita prevalece sobre última vista guardada |
| Interacción en líneas compartidas | Vía: src/web/tap.ts | Desambiguar líneas superpuestas |
| Recuperación de carga | Vía: src/web/files.ts | Timeout, reintentos acotados y conservación de datos |
| Favoritos sin cuenta | Vía: src/web/favourites.ts | Persistencia local tolerante a fallos |
| Tren, estación y línea como producto | Valfiguer: documentación de API | Fichas propias sobre nuestra API |
| Antigüedad y correcciones visibles | Valfiguer: Acerca/API | Transparencia de fuente y método |

Valfiguer documenta detalle de tren, paneles de estación, horarios, líneas, avisos, cancelaciones y salud. Son referencia funcional. Su página Acerca declara que no extrapola posiciones entre actualizaciones. La animación propuesta para Madrid Pulse toma como referencia técnica Vía Península y debe identificar sus estimaciones.

No trasladar sin evaluación el gran archivo main.ts de Vía, ni sus ajustes sobre internals privados de MapLibre, ni todos sus detalles visuales. Estudiar el comportamiento y resolverlo con módulos propios y APIs públicas.

## 5. Nuevo papel de App.tsx y estructura de frontend

### Responsabilidad de App.tsx

Componer servicios y pantalla; conectar navegación con mapa y panel. No debería contener el cálculo de coordenadas por fotograma, el filtrado temporal GTFS, la reconciliación de objetos MapLibre ni todos los detalles de una estación.

Pseudocódigo de composición, no implementación lista para pegar:

~~~tsx
export default function App() {
  const catalog = useNetworkCatalog();
  const live = useLiveRailway();
  const navigation = useRailwayNavigation();
  const preferences = useLocalPreferences();

  return (
    <RailwayShell
      map={
        <RailwayMap
          catalog={catalog.data}
          snapshot={live.data}
          selection={navigation.selection}
          followMode={navigation.followMode}
          onSelect={navigation.select}
          onManualPan={navigation.releaseCamera}
        />
      }
      controls={<MapControls />}
      panel={<EntityPanel selection={navigation.selection} />}
      status={<DataStatus status={live.status} />}
    />
  );
}
~~~

Los nombres son propuestos. Durante implementación deberán recibir las props y acciones necesarias, sin duplicar la fuente de verdad entre controles.

### Distribución sugerida

| Carpeta/archivo propuesto | Responsabilidad |
|---|---|
| app/RailwayShell.tsx | Layout, overlays y adaptación a pantalla |
| features/network/ | Catálogo y filtros de líneas |
| features/live/ | Lecturas, snapshots y salud |
| features/navigation/ | Selección, URL, historial y seguimiento |
| features/map/RailwayMap.tsx | Ciclo de vida de MapLibre |
| features/map/layers/ | Red, estaciones, trenes y selección |
| features/map/animation/ | Reloj y muestreo de planes de movimiento |
| features/train/ | Ficha e itinerario |
| features/station/ | Ficha y panel de salidas |
| features/line/ | Resumen y trenes de línea |
| features/search/ | Índice y resultados |
| features/favourites/ | Persistencia local |
| shared/contracts/ | Modelos públicos y validación |
| shared/ui/ | Controles comunes y accesibilidad |

Se pueden agrupar archivos mientras el código sea pequeño. No crear una arquitectura de docenas de abstracciones para cada componente.

### Tres clases de estado

| Estado | Ejemplos | Dónde |
|---|---|---|
| Datos del servidor | Catálogo, observaciones, avisos | Hooks/cache de recursos |
| Intención del usuario | Selección, filtros, cámara y panel | Navegación/controlador de aplicación |
| Presentación por fotograma | Progreso y coordenada dibujada | Controlador fuera del render React |

React actualiza fichas, controles y listas a su frecuencia útil. MapLibre recibe las posiciones dibujadas. No ejecutar setState para toda la aplicación a 60 Hz.

No es obligatorio introducir Redux, Zustand, React Query ni otra dependencia. Evaluar una dependencia cuando simplifique un problema real; un reducer y hooks especializados pueden bastar.

## 6. Objetos interactivos e identidad

Una selección debe referenciar una entidad estable, no el índice de una lista ni un objeto de respuesta que desaparece al siguiente polling.

### Identidades propuestas

- networkKey: núcleo/red de la fuente.
- lineKey: red y línea del catálogo.
- patternKey: recorrido ordenado de paradas y sentido.
- runKey: identidad de circulación, con ámbito de operador/red, service_date y trip_id; aplicar política de desambiguación si la fuente exige más campos.
- vehicleKey: identidad de vehículo publicada, cuando exista y se haya verificado.
- stationKey: red/operador y station_id o identidad física normalizada, según el modelo.

No identificar una circulación solo por vehicle_id ni solo por “C5”. Un vehículo puede realizar varios viajes y un identificador de viaje puede reutilizarse otro día.

### Selección propuesta

~~~ts
type Selection =
  | { kind: "none" }
  | { kind: "train"; runKey: string }
  | { kind: "station"; stationKey: string }
  | { kind: "line"; lineKey: string }
  | { kind: "alert"; alertKey: string };

type FollowMode = "off" | "active" | "released";
~~~

La selección del tren se resuelve sobre el último snapshot. Si deja de aparecer, se conserva una ficha con estado “Sin actualización” o “Servicio finalizado” solo si esa conclusión está acreditada. Ausencia del feed no demuestra finalización o cancelación.

### Interacción por entidad

| Entidad | Acción primaria | Acción contextual |
|---|---|---|
| Tren | Seleccionar y abrir ficha | Seguir, abrir línea, próxima parada |
| Estación | Abrir ficha | Salidas, líneas y favorito |
| Línea | Resaltar y abrir resumen | Filtrar, ajustar vista y ver avisos |
| Aviso | Abrir contenido y ámbito | Navegar a entidades identificadas |
| Fondo del mapa | Desplazar/explorar | Cerrar selección según interacción documentada |

Click, tap y selección en listas convergen en la misma acción. Un hover ofrece información breve en escritorio; ninguna función esencial depende de hover.

### Solapamientos

Si hay varios trenes prácticamente coincidentes, mostrar una elección compacta en vez de seleccionar uno al azar. Para líneas sobre un tramo compartido, abrir las candidatas del punto. La prioridad de hit testing debe ser explícita: trenes, estaciones y trazados; ofrecer desambiguación cuando corresponda.

El área táctil puede ser mayor que el símbolo. Los símbolos de WebGL requieren una alternativa navegable por teclado; no convertir cada tren en un foco invisible sin nombre.

## 7. Navegación, paneles y cámara

### Estados de cámara

~~~mermaid
stateDiagram-v2
  [*] --> Exploracion
  Exploracion --> TrenSeleccionado: Seleccionar tren
  TrenSeleccionado --> Seguimiento: Pulsar Seguir
  Seguimiento --> CamaraLibre: Arrastrar mapa
  CamaraLibre --> Seguimiento: Volver al tren
  CamaraLibre --> Exploracion: Cerrar ficha
  Seguimiento --> Exploracion: Cerrar ficha
  TrenSeleccionado --> Exploracion: Cerrar ficha
~~~

- Seleccionar no debe secuestrar la cámara indefinidamente.
- “Seguir” es una intención explícita.
- Un gesto humano libera la cámara conservando el tren seleccionado.
- Abrir una estación del itinerario cambia el panel y conserva un origen de navegación.
- El botón Atrás del panel vuelve al contexto anterior.
- Escape cierra el nivel contextual; no borra preferencias.

### Evitar conflictos de cámara

El seguimiento no debe llamar easeTo cada fotograma. Emplear una zona de tolerancia en pantalla y un ritmo de recentrado limitado, medidos con pruebas. Respetar pointerdown, drag, pinch y transiciones ya activas.

Distinguir movimientos programáticos de gestos. Un movestart iniciado por la aplicación no debería liberar accidentalmente el seguimiento. Evitar wrappers de APIs internas o monkey patches.

Ajustar padding al panel realmente abierto: el tren debe quedar en la parte visible del mapa, no debajo de la ficha. Usar ResizeObserver/map.resize cuando cambie el contenedor y los mecanismos públicos disponibles en la versión instalada.

### URL y preferencias

Propuesta de parámetros propios, no contrato existente:

- view: centro y zoom, con validación.
- line: lineKey seleccionado/filtrado.
- train: runKey con codificación segura.
- station: stationKey.
- panel: contexto abierto cuando haga falta.

Prioridad: enlace explícito → preferencias válidas → vista inicial de Madrid.

Usar pushState para navegación semántica entre objetos y replaceState, con limitación de frecuencia, para movimientos de cámara. Soportar popstate. Así Atrás es útil sin recorrer centenares de desplazamientos.

No escribir tokens, credenciales ni geolocalización personal persistente en el enlace. Favoritos y preferencias locales no se comparten automáticamente.

## 8. Movimiento: la mejora técnica principal

### Problema actual

El motor tiene observed_max_age_s = 60 y stale_after_s = 180 como umbrales operativos. En la rama OBSERVED devuelve la última coordenada proyectada al corredor; después calcula una estimación con horario. El cliente solo recibe una posición por respuesta.

**Conservar esa misma posición y añadir requestAnimationFrame no producirá avance.** Tampoco lo produce una transición CSS arbitraria del marcador.

La mejora exige separar evidencia recibida de posición presentada y publicar información temporal suficiente.

### Principio propuesto

El backend conserva autoridad sobre recorrido, plausibilidad, estado ferroviario y horizonte permitido. El cliente representa un plan de movimiento y lo muestrea con un reloj; no crea su propia versión independiente del horario o de las reglas del motor.

La observación puede ser reciente y, al mismo tiempo, el tren dibujado entre actualizaciones ser una estimación. Son dos dimensiones distintas.

| Dimensión | Ejemplo |
|---|---|
| Evidencia | Posición publicada hace 12 s |
| Ajuste geométrico | Proyectada al recorrido a 18 m del punto |
| Presentación | Estimada ahora a partir de horario y evidencia |
| Calidad | Fuente reciente, ajuste válido, horizonte vigente |

No etiquetar como “GPS confirmado ahora” una coordenada animada calculada.

### Estrategia elegida para desarrollar

**Plan temporal preparado por backend, guiado por recorrido/horario y corregido por observaciones.** El contrato debe admitir tramos de espera y un horizonte corto calibrable.

Esta estrategia requiere un ADR propuesto y un cambio real del modelo de presentación; no basta con reutilizar sin cambios la rama que congela la posición durante 60 segundos.

Como comparación técnica se puede evaluar una interpolación retrasada entre dos observaciones conocidas. Esta introduce latencia de presentación. No mezclar ambos métodos sin identificar cuál se está mostrando.

### Contrato conceptual mínimo

~~~ts
interface TrainAnimationPlan {
  planId: string;
  runKey: string;
  patternKey: string;
  geometryVersion: string;
  generatedAt: string;         // ISO UTC
  validFrom: string;           // ISO UTC
  validUntil: string;          // ISO UTC
  method: "timetable_corrected" | "buffered_interpolation" | "hold";
  sourceObservationAt: string | null;
  sourceObservationKey: string | null;
  points: Array<{
    at: string;                // ISO UTC
    segmentKey: string;
    progressM: number;         // metros en ese segmento
    state: "moving" | "holding";
  }>;
}
~~~

Es un diseño inicial, no el schema definitivo. Puede optimizarse para no repetir claves. Las trayectorias, unidades, timestamps y versiones se validarán en ambos extremos.

Los campos actuales del API se mantienen compatibles mientras se migra el frontend. El backend debe exponer también la identidad y edad de la observación realmente usada tras un fallback.

### Reglas de cálculo

1. Resolver la circulación contra su fecha de servicio, patrón y sentido.
2. Seleccionar el recorrido correcto, con segmentos continuos.
3. Proyectar observaciones y registrar distancia/residuo.
4. Rechazar o marcar saltos según reglas justificadas; no convertir umbrales de detección en velocidad real de animación.
5. Corregir la fase temporal con evidencia disponible.
6. Mantener una parada cuando el estado/horario corregido la justifique; no avanzar por la estación mediante interpolación genérica.
7. Respetar cancelaciones, SKIPPED y modificaciones verificadas.
8. Producir puntos de movimiento/espera dentro de un horizonte permitido.
9. Al agotar el horizonte, no continuar extrapolando indefinidamente.
10. No cruzar un hueco de geometría ni una bifurcación sin ruta resuelta.

La política de obsolescencia de presentación debe ser tan estricta o más que la del dato. Si se ofrece posteriormente un modo “Solo horario”, debe estar identificado y separado de un seguimiento confirmado.

### Muestreo y reloj del cliente

- Tomar una referencia temporal del servidor y asociarla al reloj monotónico del cliente.
- Estimar desfase con cautela respecto al RTT; conservar timestamps absolutos para auditoría.
- Usar performance.now para avanzar dentro de una sesión; no acumular posiciones por deltas de frames.
- Un único scheduler de animación para todos los trenes.
- Interpolar progreso sobre un segmento y convertirlo a coordenadas con medidas geométricas coherentes.
- No interpolar latitud y longitud en línea recta entre estaciones.
- Evaluar el tiempo actual al volver de una pestaña oculta; no reproducir cientos de frames atrasados.
- Si falta un plan válido, mantener la última situación representable y mostrar su estado.

### Reconciliación cuando llega una observación nueva

| Caso | Respuesta |
|---|---|
| Corrección pequeña y mismo patrón | Corregir suavemente dentro del recorrido |
| Cambio grande o salto imposible | Marcar discontinuidad; evitar una carrera visual falsa |
| Cambio de trip/fecha/patrón | Reiniciar plan con identidad nueva |
| Tren detenido | Estado holding |
| Desaparece temporalmente | Conservar contexto y evaluar obsolescencia |
| Llega otra geometryVersion | Sustituir geometría/plan como conjunto consistente |
| Plan fuera de orden | Descartar según revisión temporal, sin rebobinar la vista |

La duración de corrección y los umbrales se calibran con replay. El suavizado nunca justifica atravesar una estación, un hueco o un ramal erróneo.

### Métricas de movimiento

- Saltos de presentación en metros y píxeles.
- Retrocesos no justificados.
- Tiempo dibujado fuera del segmento.
- Diferencia entre predicción y observación posterior utilizable.
- Casos de parada mal representada.
- Fracción de tren-tiempo con plan válido.
- Frames útiles, trabajo en main thread y consumo de CPU.

Una trayectoria suave no demuestra exactitud física. La evidencia de fuente y el error del modelo se evalúan aparte.

## 9. MapView: renderizado estable y jerarquía visual

### Implementación incremental recomendada

**Paso 1:** extraer gestión de marcadores a un registro por identidad. Crear cada marcador una vez, actualizar coordenadas y atributos y eliminarlo solo al salir del conjunto definido. Permite incorporar selección sin esperar una reescritura.

**Paso 2:** evaluar capas GeoJSON/symbol de MapLibre para el conjunto de la red. Priorizar esta vía si el benchmark muestra que los marcadores DOM no cumplen. Un elemento DOM de selección puede mantenerse si aporta accesibilidad sin duplicar símbolos.

No imponer WebGL nuevo, deck.gl o clustering como requisito antes de medir. No mantener las dos implementaciones indefinidamente si solo una es necesaria.

### Capas propuestas

| Capa | Contenido | Ritmo |
|---|---|---|
| network-casing | Borde/contraste de trazado | Cambios de catálogo o estilo |
| network-lines | Geometría de líneas | Cambios de catálogo o filtro |
| station-points | Estaciones con identidad | Catálogo |
| station-labels | Etiquetas según zoom | Motor cartográfico |
| trains | Posiciones presentadas | Scheduler |
| train-selection | Resaltado del tren | Selección y movimiento |
| route-selection | Trayecto relevante | Cambio de objeto |
| alerts-context | Ámbito verificable del aviso | Actualización de avisos |

Estilos y nombres son propuestos. Incluir ids estables en GeoJSON, gestionar recarga de estilo y no recrear el mapa al alternar tema.

No repetir setData de toda la geometría cuando solo cambian trenes. Para los trenes, limitar publicaciones al ritmo visual útil: requestAnimationFrame puede coordinar sin obligar a serializar todo GeoJSON a la frecuencia de pantalla.

### Escalas

| Escala | Tren | Red |
|---|---|---|
| Vista Madrid | Punto/forma compacta | Líneas principales y estaciones prioritarias |
| Distrito | Etiqueta corta de línea | Más estaciones, detalles relevantes |
| Seguimiento | Símbolo seleccionado claro y dirección si está respaldada | Recorrido y próxima parada |

El color de línea identifica servicio; el estado de calidad usa contorno, patrón, icono y texto. El retraso no debe anular el significado del color de línea sin una leyenda explícita.

Cuando varias líneas comparten vía, usar orden estable y desplazamientos visuales limitados a las escalas donde ayuden. Mantener geometría física y desplazamiento cartográfico separados para que las coordenadas analíticas no cambien al hacer zoom.

### Mapa base

Evaluar un estilo vectorial sobre la misma instancia MapLibre, con contraste suficiente, nombres de lugares, ferroviario visible y posibilidad de tema claro/oscuro. Mantener atribuciones y política del proveedor. No construir un motor propio para dibujar las calles.

La decisión del proveedor y de publicación de teselas debe respetar los ADR y costes del proyecto. Cambiar la apariencia no requiere migrar FastAPI, Python o PostGIS.

## 10. Fichas que convierten puntos en objetos útiles

### Ficha de tren

Orden de contenido propuesto:

1. Línea, destino y número comercial si realmente existe.
2. Estado entendible: en parada, hacia una parada o sin actualización.
3. Retraso publicado; si no existe, “Retraso no disponible”.
4. Próxima parada y hora programada/estimada, identificando cada una.
5. Itinerario con paradas pasadas, actuales y futuras.
6. Acciones: Seguir, abrir línea, abrir estación y compartir.
7. Detalle desplegable: timestamps, coordenadas, método, flags e identificadores.

No inferir “en hora” porque delay sea null. No inventar velocidad o rumbo; si se calculan, indicar el método y no presentarlos como campos publicados.

No propagar automáticamente el retraso actual a todas las paradas como si fueran predicciones del operador. Si se ofrece esa aproximación, etiquetarla y evitar que se confunda con una estimación por parada recibida.

El itinerario necesita identidad de circulación, calendario, orden de paradas y relaciones de servicio. Las paradas SKIPPED deben diferenciarse de cancelaciones de todo el viaje.

### Ficha de estación

- Nombre y líneas verificadas.
- Servicios próximos con destino.
- Hora programada y hora estimada cuando exista.
- Distinción entre circulación observada y servicio solo programado.
- Avisos asignados mediante evidencia de entidad.
- Favorito y acceso a línea/tren.

La API actual de estación devuelve datos de estación, no un panel de salidas. Esta funcionalidad requiere backend; no debe simularse a partir de los trenes que casualmente estén cerca.

Las estaciones de intercambio pueden reunir varias plataformas o station_id. Conservar relación entre estación física y paradas de servicio. No deduplicar exclusivamente por nombre ni por proximidad.

### Ficha de línea

- Denominación y color del catálogo verificado.
- Trenes observados/ubicables y cobertura.
- Variantes de recorrido y terminales relevantes.
- Avisos activos.
- Lista de estaciones navegable.
- Acciones para mostrar/filtrar y ajustar vista.

“Mostrar una línea”, “seleccionar su ficha” y “filtrar toda la red” son acciones relacionadas, pero distintas. Abrir una línea desde una estación no debería ocultar sin explicación todo el resto del mapa.

### Panel Ahora

Posterior a las fichas básicas: agrupar lo relevante por línea y evidencia —avisos, cancelaciones publicadas y retrasos conocidos—. Evitar declarar una red “sin incidencias” si faltan fuentes. Incluir ámbito y momento del resumen.

## 11. Búsqueda, favoritos y enlaces

### Búsqueda

Primera entrega: estaciones y líneas con índice local del catálogo cargado. Añadir tren por número comercial o identidad interna cuando el backend pueda resolverlo sin ambigüedad.

Normalizar acentos y mayúsculas conservando los nombres originales. Ordenar coincidencias exactas y prefijos antes que resultados débiles. No hace falta un buscador semántico ni IA.

Los resultados deben admitir teclado, lector de pantalla y tap. Cancelar o ignorar respuestas antiguas si la búsqueda depende del servidor.

### Favoritos

Guardar referencias de estación y línea, versión de formato y preferencias mínimas. Manejar almacenamiento deshabilitado, JSON corrupto, entidades desaparecidas y cambios de esquema. La app funciona aunque falle la persistencia.

No introducir cuenta/sincronización de dispositivos como condición de esta entrega. No guardar tokens de fuente en el navegador.

### Enlaces

Un enlace de estación funciona tras recargar. Un tren de otro día muestra contexto explícito o indisponibilidad; no abre una circulación distinta con el mismo trip_id. Un enlace inválido no deja el mapa en blanco ni dispara reintentos infinitos.

La preferencia guardada nunca anula un objeto especificado en la URL.

## 12. Lecturas, caché y tolerancia a errores

### Cambio concreto en api.ts y hooks

Hoy fetchDashboard solicita lines, vehicles y health en Promise.all cada vez. Separar responsabilidades:

| Recurso | Estrategia propuesta |
|---|---|
| Catálogo/geometría | Carga inicial, versionada; recarga al cambiar versión/ámbito |
| Snapshot vivo | Cadencia de fuente, con una sola lectura en vuelo |
| Salud | Independiente; no impide usar el último snapshot |
| Avisos | Ciclo propio y validación de vigencia |
| Detalle de objeto | Bajo demanda, cancelable |
| Panel de estación | Bajo demanda y actualización limitada |

Mantener 20 s como punto inicial de adquisición visible si sigue siendo adecuado; no es un requisito de animación. Medir carga y frescura antes de modificarlo.

### Reglas de red

- Planificar siguiente lectura tras completar la anterior, o usar single-flight equivalente.
- Aplicar timeout para que una solicitud bloqueada no congele el ciclo.
- Abort al desmontar o cambiar el ámbito.
- Evitar respuestas fuera de orden mediante revisión/generación y timestamps.
- Reintentos acotados con backoff y jitter; respetar la respuesta de la fuente propia.
- Si falla health, conservar trains y catálogo.
- Si falla el snapshot, conservar último resultado con su antigüedad real.
- Un HTTP 200 o 304 no implica una observación nueva.
- Pausar o reducir actividad con la pestaña oculta; actualizar al volver.
- No iniciar lecturas por tren ni por fotograma.

El valor updatedAt de interfaz debe distinguir “última consulta satisfactoria” de “momento de la evidencia”. El actual setUpdatedAt(new Date()) solo refleja la actualización del cliente.

### Envelope propuesto

Para un endpoint nuevo de snapshot, proponer generated_at, snapshot_id/revision, catalogue_version, feeds y vehicles. Si se mantiene el endpoint actual de lista, añadir uno nuevo o una migración compatible; no cambiar silenciosamente una lista por un objeto.

Verificar cómo feed_health calcula edad. El código revisado usa el inicio de ingestión para parte de su estado; el frontend no debe interpretarlo como edad de cada posición. Necesita timestamps de fuente y entidad.

### Uso real frente a demo

Toda la aplicación sigue funcionando contra la API propia. No llamar a Renfe desde cada navegador ni conectar el frontend a Valfiguer. Snapshots/CDN son una evolución de distribución, compatible con el backend actual.

Las fixtures deben indicar “Replay/demo”, fecha y condición. Nunca mezclar datos históricos de prueba con un rótulo de “En vivo”.

## 13. Cambios de API y datos que necesita el frontend

| Ruta/contrato actual | Qué existe | Evolución propuesta |
|---|---|---|
| GET /api/v1/lines | Catálogo con geometría disponible | Identidad canónica, versión y ámbito |
| GET /api/v1/lines/{line_id} | Detalle de línea | Resolver claves cuando haya varias redes |
| GET /api/v1/stations | Estaciones | Relaciones y agrupación física verificadas |
| GET /api/v1/stations/{station_id} | Datos de estación | Conservar; no confundir con salidas |
| GET /api/v1/live/vehicles | Lista de vehículos | Mantener compatible y enriquecer |
| GET /api/v1/live/vehicles/{vehicle_id} | VehicleOut individual | Conservar; no equivale aún a itinerario |
| GET /api/v1/health | Estado de feeds | Separar adquisición/fuente/evidencia |

### Capacidades nuevas, pendientes de diseñar

- Snapshot coherente para el mapa.
- Circulación/run con fecha de servicio e itinerario.
- Plan temporal de movimiento con versión de geometría.
- Salidas de estación por ventana temporal.
- Avisos y cancelaciones normalizados.
- Búsqueda/resolución por número comercial cuando exista.

Nombres de endpoints orientativos: /live/snapshot, /runs/{runKey}, /runs/{runKey}/animation, /stations/{station_id}/departures y /alerts. **No existen en el baseline y no son contratos acordados.** Evaluar si el plan se incluye en snapshot para evitar N peticiones.

Para ampliar modelos, modificar de forma coordinada apps/api/schemas.py, service.py, main.py, openapi.json, types.ts y contratos/pruebas. No inventar en el frontend campos que el parser nunca conserva.

### Precondiciones de datos

1. Corregir y probar el caso SKIPPED sin arrival con evidencia real.
2. Revisar calendar_dates y excepciones.
3. Interpretar horarios mayores de 24:00 con service_date y Europe/Madrid.
4. Probar cambio de día, horario de verano/invierno y servicios nocturnos.
5. Distinguir el tren físico de la circulación.
6. Resolver variantes/recorridos y sentido.
7. Confirmar qué campos GTFS se parsean realmente para destino y número.
8. Conservar dato bruto y no perder entidades por rechazos de otra entidad.

No generar todos los trenes programados a partir de “scheduled” del motor actual: esa rama es un fallback. La enumeración de servicios programados activos es una capacidad adicional, con calendario y ventana temporal explícitos.

## 14. Diseño responsive y accesibilidad

### Escritorio

Mapa en el espacio principal, búsqueda/selector compactos, controles persistentes y ficha contextual. El panel no debe obligar a desplazar la página para encontrar un tren. Una vista de lista accesible complementa al mapa.

### Móvil

Mapa visible desde la apertura. Panel inferior con estados cerrado, vista breve y expandido; botones para esas acciones además del gesto de arrastre. Aplicar safe areas y altura dinámica del viewport.

La ficha expandida puede requerir espacio para leer; debe existir una acción clara para volver al mapa. El teclado de búsqueda y el cambio de orientación no deben dejar controles fuera de pantalla.

### Calidad del dato sin saturar

En la ficha breve: línea, destino, próxima parada y rótulo compacto de edad/método. En el detalle: flags, timestamps e incertidumbre. La explicación introductoria completa se mueve a Ayuda.

### Reglas de accesibilidad

- Contraste y estados distinguibles sin depender solo de color.
- Foco visible y devolución del foco al cerrar un panel.
- Modalidad y aria-modal solo cuando el panel sea realmente modal.
- Escape y Atrás con comportamiento consistente.
- Controles táctiles de al menos 44 CSS px como objetivo de diseño.
- Evitar anuncios de lector de pantalla cada segundo o cada movimiento.
- Estados de error y cambios importantes con anuncios limitados.
- prefers-reduced-motion respetado tanto en paneles como en cámara y animación.
- Alternativa de consulta mediante listas y fichas.

Con movimiento reducido, evitar cámara continua y pulsaciones decorativas; usar cambios discretos o recentrado explícito. No convertir la preferencia en una pérdida de funciones.

## 15. Expansión a toda Cercanías Madrid

El backend actual carga un LoadedNetwork con un corredor y un motor. Esto no equivale a disponer de toda la red aunque el GTFS completo resuelva muchos vehículos.

Proponer un registro por patrón/recorrido y versión de geometría. Mantener entidades no resueltas fuera del mapa con un diagnóstico accesible, sin inventar coordenadas.

### Secuencia de validación

1. Mantener C5 como circuito de verificación.
2. Añadir un recorrido con bifurcación/sentidos que pruebe el modelo.
3. Añadir un tramo compartido para probar desambiguación y dibujo.
4. Incorporar líneas restantes contra datos reales.
5. Publicar cobertura por línea y método.

Las líneas elegidas se deciden con GTFS actual y fuentes verificadas; no con una lista histórica fija.

El mapa puede mostrar varias líneas simultáneamente. El filtro por una línea es una elección de UX, no una limitación estructural. Mostrar “red parcial” mientras siga habiendo cobertura pendiente.

No afirmar “todos los trenes de Madrid” porque se hayan incorporado todas las líneas: la fuente puede omitir circulaciones. Expresar ámbito y cobertura observada.

## 16. Rendimiento y verificación

Los siguientes valores son **presupuestos propuestos** para orientar implementación, no resultados medidos:

| Área | Objetivo inicial |
|---|---|
| Selección de tren/estación | Respuesta visual en menos de 200 ms con datos locales |
| Movimiento visible | Buscar 30 fps sostenidos en el dispositivo de referencia |
| Polling vivo | Máximo una lectura en vuelo por recurso/ámbito |
| Geometría | Sin descarga completa en cada polling |
| Actualizaciones React | Sin renders globales por fotograma |
| Estabilidad | Sin crecimiento sostenido de listeners, marcadores o timers |
| Degradación | Último dato válido y motivo visible |
| Vista oculta | Sin animación ni adquisición de alta frecuencia innecesarias |

Definir dispositivo, navegador, viewport, dataset y método de medida. No presentar throttling de escritorio como prueba de iPhone real. Mantener capturas y trazas internas de verificación según las reglas del proyecto.

### Pruebas necesarias

| Capa | Caso que debe cubrir |
|---|---|
| Motor | Parada, salida, sentido, corrección y horizonte agotado |
| Geometría | Segmentos desconectados, ramales y cambio de versión |
| Tiempo | Medianoche, service_date y horas GTFS >24 |
| API | Compatibilidad, datos ausentes y timestamps usados |
| Red | Recursos parciales, timeout y respuesta fuera de orden |
| UI | Seleccionar el mismo tren desde mapa y lista |
| Cámara | Arrastrar libera; volver al tren reanuda |
| Navegación | Deep link, recarga, Atrás y enlace inválido |
| Móvil | Panel, teclado, orientación y controles |
| Accesibilidad | Teclado, foco y movimiento reducido |
| Producción | Worker, assets, carga fría y ruta profunda |
| Sesión prolongada | Sin acumulación de objetos ni loops duplicados |

Las pruebas actuales con mock de MapLibre son útiles para ciclo de vida, pero no acreditan renderizado, movimiento, hit testing ni comportamiento de cámara. Combinar pruebas puras deterministas con comprobación de navegador real.

Usar reloj controlado en pruebas de movimiento; no sleeps largos. Medir una sesión larga con perfilado, sin declarar resultados antes de ejecutarla.

## 17. Backlog propuesto para incorporar a Orca

Asignación propuesta conforme a roles de herramientas: Claude coordina experiencia/arquitectura y Codex puede ejecutar o revisar datos, algoritmos y contratos. Usar los modelos disponibles configurados en Orca; no inventar nombres de versiones. Escalar el razonamiento en geometría, movimiento o decisiones difíciles cuando exista motivo.

| ID local | Entrega | Depende de | Ejecutor propuesto | Revisor propuesto |
|---|---|---|---|---|
| UX-01 | Auditoría local y fixtures de riesgos | — | Codex | Claude |
| UX-02 | Estados de producto y diseño de navegación | UX-01 | Claude | Codex |
| UX-03 | Contratos de identidad y tiempo; ADR | UX-01 | Codex | Claude |
| UX-04 | App shell y separación de responsabilidades | UX-02 | Claude | Codex |
| UX-05 | Adquisición por recurso y resiliencia | UX-03 | Codex | Claude |
| UX-06 | Selección y renderer estable | UX-03, UX-04 | Codex | Claude |
| UX-07 | Plan temporal backend y replay | UX-03 | Codex | Claude |
| UX-08 | Animación y cámara de seguimiento | UX-05, UX-06, UX-07 | Claude | Codex |
| UX-09 | Detalle de tren e itinerario | UX-03, UX-06 | Claude | Codex |
| UX-10 | Estación/salidas y línea | UX-03, UX-04, precondiciones de datos | Codex | Claude |
| UX-11 | Búsqueda, URL y favoritos | UX-06, UX-09, UX-10 | Claude | Codex |
| UX-12 | Capas por zoom y red de varios patrones | UX-06, UX-07 | Claude | Codex |
| UX-13 | Móvil, accesibilidad y rendimiento | UX-08…UX-12 | Claude | Codex |
| UX-14 | Validación incremental de Madrid | UX-10, UX-12 | Codex | Claude |
| UX-15 | Demo integrada y aceptación | UX-13, UX-14 | Codex | Claude |

Son asignaciones recomendadas, no ejecuciones/delegaciones realizadas. El orquestador reconcilia este reparto con tareas que ya tengan responsables.

### UX-01 — Auditoría local y fixtures

Inspeccionar ramas/worktrees, reproducir fragilidad de parser, revisar campos disponibles, calendario y estado actual de contratos. Crear fixtures representativas sin alterar la fuente bruta. Entregar hallazgos reproducibles y lista de cambios realmente necesarios.

### UX-02 — Diseño de navegación

Mockup funcional o prototipo local que pruebe mapa, tren, estación, línea, seguimiento y panel móvil. Revisar flujos y contenido antes de desarrollar todas las fichas. No dar por terminada la UX con una imagen estática.

### UX-03 — Contratos y decisiones

Resolver identidades, fuente temporal, fallback, método de presentación y geometría versionada. Proponer ADR del plan de movimiento y compatibilidad de API. Aceptación: ejemplos y casos límite inequívocos, con transición desde los cuatro modos actuales.

### UX-04/05 — Base de aplicación

Conservar funciones existentes al extraer responsabilidades. Probar que una caída de health no vacía el mapa, que no se solapan solicitudes y que cambiar de selección no reinicia el sistema de adquisición.

### UX-06 — Selección estable

Un click sobre tren/estación abre la ficha correcta. El siguiente polling no borra selección, hover ni foco. Las geometrías contienen claves. No hay reconstrucción masiva de marcadores por actualización.

### UX-07 — Movimiento backend

Replay congelado de un recorrido y observaciones genera un plan reproducible. Detención, ausencia, cambio de recorrido y saltos tienen comportamientos definidos. Medir error sin afirmar que cada observación es ground truth perfecto.

### UX-08 — Animación y seguimiento

El tren avanza sobre la vía entre respuestas, con rótulo de método. Arrastrar cede la cámara; recentrar la recupera. La ficha y el mapa usan el mismo reloj/modelo. Sin animaciones atravesando huecos.

### UX-09/10 — Fichas útiles

Priorizar contenido comprensible, acceso a paradas y acciones. Salidas de estación calculadas sobre calendario y actualizaciones correctas. Presentar ausencia de datos sin suplirla por ceros o textos concluyentes.

### UX-11/12 — Exploración

Búsqueda, favoritos y enlaces sobreviven recarga según su contrato. Más de una línea funciona simultáneamente. Zoom no cambia la identidad analítica de los trenes.

### UX-13/14/15 — Aceptación

Probar dispositivos y cobertura real, registrar presupuestos medidos, actualizar README y documentación. Cierre mediante revisión cruzada documentada; no basta compilar o tener un screenshot.

## 18. Entregas recomendadas y límites

### Entrega A — Un objeto que se puede usar

UX-01…UX-06 y la parte mínima de UX-09. Resultado: mapa primero, selección, ficha breve y cargas resilientes. Puede validarse sobre C5 mientras avanza el trabajo de red.

### Entrega B — Un tren que se puede seguir

UX-07…UX-09 con pruebas de cámara, tiempo y accesibilidad. Resultado: movimiento explicado y seguimiento utilizable.

### Entrega C — Una red que se puede explorar

UX-10…UX-15 y expansión de Hito 3. Resultado: estaciones, líneas, búsqueda, enlaces, móvil y cobertura incremental de Cercanías Madrid.

No esperar a cubrir España ni a tener todas las funciones avanzadas para validar la Entrega A. Tampoco confundir una demo C5 con el cumplimiento de toda Cercanías Madrid.

**Posponer:** pasaporte, insignias, seguimiento aleatorio, puentes 3D detallados, agentes de IA, push notifications, cuentas y planificación multimodal. Pueden evaluarse después de comprobar uso real de los recorridos principales.

## 19. Integración en el repositorio y protocolo de trabajo

Cambios de documentación a preparar durante implementación:

- docs/HITO_3_BACKLOG.md: incorporar UX y dependencias, preservando expansión Madrid.
- docs/TASKS.md: asignar MP-XXX reales y responsables.
- docs/STATUS.md: registrar autorización vigente, progreso y evidencia.
- docs/CHANGELOG.md: comportamientos entregados.
- docs/adr/: decisiones de movimiento, identidad y contratos cuando cambien.
- docs/DATA_CONTRACTS.md y OpenAPI: mantener coherencia con API.
- README.md: demo, estado real y límites.
- docs/legal/: atribución y nuevas fuentes/proveedores si los hubiera.

Respetar un worktree por tarea, ejecución/revisión secuenciales y la revisión por la herramienta contraria. No marcar DONE por la revisión del mismo ejecutor ni afirmar aprobación de Claude desde un subagente de otro proveedor.

El propietario mantiene las operaciones Git que AGENTS.md reserva. Este documento no realiza push, PR, merge ni promoción de ADR. No es necesario pedir permiso para redactar o revisar esta propuesta; la planificación se integra en el alcance autorizado conforme a las reglas ya vigentes.

### Riesgos y resolución

| Riesgo | Resolución |
|---|---|
| Animación bonita con dato mal interpretado | Contrato dual de evidencia/presentación y replay |
| Copiar complejidad de Vía | Implementación propia por capacidades pequeñas |
| Frontend pide campos inexistentes | Precondición de parser/API por cada ficha |
| Crecimiento de App.tsx | Separación por responsabilidad y límites claros |
| Cámara que pelea con el gesto | Estados explícitos y prueba real táctil |
| Toda la red rompe el modelo de corredor | Registro por patrones, validación incremental |
| Pruebas con mock ocultan errores reales | Navegador/producción y presupuesto medido |
| Diseño móvil relegado | Entregas y aceptación móvil desde A |
| Refactor bloquea el producto | Migración funcional por pasos, conservando comportamientos |

## 20. Mensaje listo para el orquestador

> Analiza este plan contra el estado real de Madrid Pulse y los worktrees vigentes. Integra las mejoras de producto ferroviario en Hito 3 sin duplicar tareas ni sustituir el objetivo de toda Cercanías Madrid.
>
> Prioriza App.tsx como composición, adquisición separada por recurso, selección estable de objetos, ficha de tren y estaciones identificables. Después desarrolla el contrato temporal y el plan de movimiento backend para que el cliente anime sobre recorridos verificados.
>
> No resuelvas el movimiento solo con requestAnimationFrame ni con una transición entre coordenadas: el motor actual mantiene fija la observación reciente y el contrato no incluye trayectoria. Separa evidencia, proyección y presentación; valida el cambio con replay y conserva compatibilidad.
>
> Incorpora seguimiento que cede ante el gesto, navegación tren–parada–línea, búsqueda, enlaces, favoritos locales y un panel móvil accesible. Mantén el dato ausente, la obsolescencia y las estimaciones explícitos.
>
> Usa Vía Península como referencia de comportamiento/arquitectura y Valfiguer como referencia funcional, sin copiar código ni depender de sus APIs. Evita internals privados de MapLibre y conserva el arreglo del worker y el arranque actual.
>
> Propón ADR, tareas MP reales, dependencias, ejecutor/revisor y criterios de aceptación. Trabaja dentro de las autorizaciones vigentes y las reglas de AGENTS.md. Entrega evidencia de ejecución para toda prueba declarada superada.

## 21. Fuentes concretas para la implementación

### Madrid Pulse: código publicado auditado

Todos los enlaces siguientes apuntan a 990c95d, no a una rama que pueda cambiar:

- [App.tsx](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/App.tsx).
- [MapView.tsx](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/MapView.tsx).
- [api.ts](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/api.ts).
- [types.ts](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/types.ts).
- [styles.css](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/styles.css).
- [MapView.test.tsx](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/web/src/MapView.test.tsx).
- [main.py de API](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/api/main.py).
- [schemas.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/api/schemas.py).
- [service.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/api/service.py).
- [gtfs_source.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/apps/api/gtfs_source.py).
- [movement/engine.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/packages/movement/engine.py).
- [movement/model.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/packages/movement/model.py).
- [contracts/raw.py](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/packages/contracts/raw.py).
- [HITO_3_BACKLOG.md](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/docs/HITO_3_BACKLOG.md).
- [AGENTS.md](https://github.com/pedromaaz13/madrid-pulse/blob/990c95dfa58cabcf664b905318a4a84fe1cecf19/AGENTS.md).

### Vía Península: qué abrir para cada problema

| Fuente en 66d468a | Qué estudiar |
|---|---|
| [src/web/main.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/main.ts) | L2013: scheduler; L3260: cámara y gesto; localizar por función si cambia |
| [src/web/pill.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/pill.ts) | Simbología por escala, selección y estado |
| [src/web/view.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/view.ts) | Vista inicial, enlaces y persistencia |
| [src/web/tap.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/tap.ts) | Líneas compartidas y espacio de popup |
| [src/web/files.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/files.ts) | Carga, fallos y recuperación |
| [src/web/favourites.ts](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/src/web/favourites.ts) | Favoritos locales |
| [ADR-0002](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/docs/adr/0002-timetable-drives-motion.md) | Movimiento guiado por horario |
| [ADR-0003](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/docs/adr/0003-live-data-snapshot-on-r2.md) | Separación entre adquisición y visitantes |
| [ADR-0004](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/docs/adr/0004-track-follows-openstreetmap.md) | Recorridos sobre red OSM |
| [ADR-0011](https://github.com/gariasf/viapeninsula/blob/66d468a4f170a3245ea637956fefa1b216afaf32/docs/adr/0011-more-than-a-map-the-map-first-and-viewer-data-in-the-browser.md) | Mapa, fichas y navegación |

### Valfiguer: referencia funcional pública

- [API y capacidades documentadas](https://trenes.valfiguer.com/desarrolladores).
- [Modelo de observación y límites](https://trenes.valfiguer.com/acerca).
- [Fuentes y datos](https://trenes.valfiguer.com/datos).

Se han utilizado para definir funciones deseables y transparencia. No se ha auditado su backend, ni se atribuye a Valfiguer el motor de animación de Vía Península.

---

**Criterio final de aceptación:** una persona puede abrir Madrid Pulse, comprender qué ve, seleccionar y seguir un tren, navegar a sus paradas y volver a su contexto, mientras el producto explica qué se observó y qué se estimó. La ampliación de red conserva ese comportamiento y publica su cobertura real.


