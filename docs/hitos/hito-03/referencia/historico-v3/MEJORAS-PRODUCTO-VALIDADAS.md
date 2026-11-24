# Mejoras de producto integradas — Hito 3, v3

Documento operativo que complementa PLAN-Y-ACEPTACION.md y concreta MP-016→MP-022. El informe UX extenso se conserva en referencia/04-ux-plan-original.md como análisis, sin autoridad para reasignar tareas ni imponer su estructura de carpetas.

## Decisión de arquitectura

Mantener React/MapLibre, API propia, Python y PostGIS. Refactorizar por necesidad, conservando los arreglos del worker y del arranque de MapLibre. No migrar el stack ni copiar código de Vía Península. Vía aporta patrones de movimiento, cámara y objetos; Valfiguer aporta referencias funcionales. No usar sus APIs como dependencia productiva.

## MP-016: fiabilidad antes del rediseño

Reproducir SKIPPED sin arrival, fuente congelada, JSON inválido y último éxito conservado. Corregir el parser con fixtures verificadas y mantener raw. Una parada SKIPPED se omite del servicio/ETA; no congela por sí sola el tren completo. Solo una cancelación de circulación, una espera acreditada, falta de trayectoria o caducidad justifican su comportamiento correspondiente.

La edad visible procede de la observación utilizada, incluso si el último mensaje se descarta y se usa un ancla anterior. Diferenciar adquisición reciente de fuente reciente.

## MP-017: identidad para todos los objetos

Definir circulación con red/operador, trip_id, fecha de servicio y desambiguación que necesite la fuente. No usar vehicle_id como identidad única de viaje. Conservar líneas aunque no tengan trenes en un corte. Estaciones y variantes deben tener claves estables.

Verificar calendar_dates, 24:xx, DST, SPECIAL, cambios de servicio y campos realmente conservados para destino/número comercial. No tratar el fallback scheduled del motor como enumeración de todos los servicios programados.

## MP-018: geometría y anclas

Recorrido/patrón, sentido y geometry_version acompañan al ancla. Mantener raw, punto proyectado y residuo. Tramos desconectados no se unen con una recta. La versión de un plan de movimiento y su geometría deben ser coherentes.

Validar C5, ramal y tramo compartido antes de generalizar. La cobertura inventariada de toda Madrid no implica observación de todos los trenes.

## MP-019: contrato que permite movimiento

El motor publicado en 990c95d mantiene fija la observación reciente hasta observed_max_age_s=60. Añadir un bucle visual sin cambiar el modelo no resuelve el avance.

Antes de implementar, registrar ADR propuesto que compare:
1. Trayectoria/progreso temporal compacto calculado por backend.
2. Horario y anclas normalizados con cálculo puro compartido o equivalente verificado mediante replay.
3. Interpolación con búfer entre anclas conocidas, declarando retraso de presentación.

Elegir la alternativa más simple que preserve reglas, consistencia y presupuesto medido. No imponer un array de puntos futuros, un endpoint por tren ni una segunda implementación divergente del motor. En directo sin ancla futura, el avance es estimación; no denominarlo interpolación observada.

El contrato elegido debe resolver circulación, patrón, versión, ancla usada, calculated_at, momento de presentación, horizonte permitido, espera/movimiento y causas de falta de posición. Mantener compatibilidad con los consumidores actuales o versionar la ruptura. La coordenada renderizada nunca se archiva como observación Renfe.

Separar catálogo cacheable de snapshot ligero. Mantener último resultado por recurso ante fallo parcial. Evitar N+1. Un snapshot_id es identidad: no ordenar hashes o UUID como si fueran secuencias. Elegir revisión monotónica en un ámbito explícito o generated_at con desempate y tratamiento del reinicio.

El tablero de estación se calcula con servicios, calendario y actualizaciones; no con trenes cercanos. ETA de operador, horario y cálculo propio se distinguen. No introducir un modelo predictivo nuevo como requisito. Evitar propagar un retraso a todas las paradas sin identificar esa aproximación.

## MP-020: App.tsx y experiencia completa

### Refactor funcional

App.tsx compone adquisición, navegación, mapa y ficha. Extraer cálculo temporal y objetos MapLibre fuera de su render. No crear todas las carpetas del informe como condición previa; empezar con componentes/hooks suficientes para reducir responsabilidad.

En api.ts separar catálogo, snapshot, salud y detalles. Evitar Promise.all como único bloque indivisible de éxito. Usar una lectura en vuelo por recurso, timeout, cancelación y descarte de respuestas antiguas. Pausar/reducir adquisición al ocultarse y revalidar al volver. Una respuesta exitosa no rejuvenece datos.

### Mapa y objetos

Conservar una instancia de mapa. Estaciones llevan station_id, no solo nombre. Tren, estación y línea admiten selección desde mapa/lista/búsqueda. Selección por identidad sobrevive al polling, no por índice u objeto de respuesta.

Reconciliar marcadores por clave estable. Migrar a capa symbol/GeoJSON si rendimiento lo requiere, sin imponer dos renderers definitivos. No recargar geometría con cada snapshot ni recrear todos los objetos.

Color identifica línea; método/calidad usa forma, contorno y texto. Ocultar porcentajes de confianza no calibrados de la vista principal; explicar el índice heurístico en detalle. Datos ausentes conservan NULL.

Mapa como primera pantalla, ficha con línea/destino/próxima parada, detalle técnico desplegable. Hover opcional; tap y teclado resuelven funciones esenciales. Solapamientos se desambiguan.

### Movimiento y cámara

Un scheduler visual con reloj coherente, fuera de setState global por frame. Avanzar sobre longitud de arco del patrón, nunca interpolar lat/lon en recta entre estaciones. Mantener esperas y horizonte; corregir desviaciones pequeñas y marcar discontinuidades grandes sin acelerar ficticiamente.

Seleccionar tren no equivale a seguir cámara. Seguir es explícito; arrastrar libera cámara pero conserva ficha. Volver al tren reanuda. Los movimientos programáticos no se confunden con gestos. El panel aporta padding para no tapar el tren; no llamar easeTo indiscriminadamente cada frame.

La cámara actual ya evita fitBounds por cada polling: preservar esa propiedad. Usar APIs públicas de MapLibre; no replicar los parches a internals de proyectos externos.

### Navegación y móvil

Fichas conectadas tren→parada→línea con retorno al contexto. Búsqueda por estación/línea; tren comercial solo si puede resolverse. Enlace restaura objeto y fecha de circulación. pushState para navegación y replaceState limitado para cámara; validar parámetros.

Móvil: panel inferior con estados y botones además de gesto, foco visible, safe areas y teclado. Alternativa de lista/tablero cuando falle WebGL. Reduced motion evita seguimiento continuo y efectos automáticos. No anunciar cada segundo con lector.

Favoritos locales: mejora opcional dentro de MP-020 si no retrasa el recorrido principal; formato versionado y fallo de almacenamiento tolerado. Sin cuentas.

Cinta de novedades: progresiva; estática/pausable, sin duplicados ni carrusel obligatorio. No bloquear la salida si el aviso útil se presenta mejor como lista.

## MP-021: continuidad analítica

Abrir histórico con identidad/fecha de Live y volver al contexto. Idempotencia, huecos y denominadores visibles. El histórico y Explore mínimo del kit se mantienen; no añadir SQL Lab, dbt obligatorio, cuentas ni infraestructura distribuida a este cierre.

## MP-022: aceptación

Demostrar selección desde mapa/lista, seguir→arrastrar→volver, dos polls sin pérdida de contexto, respuesta antigua descartada, fallo parcial, recuperación, parada/ramal, fuente obsoleta, móvil 390 px, teclado y reduced motion.

Los dos cortes 1532/1533 no prueban por sí solos todos esos casos ni precisión física. Conservarlos intactos; añadir secuencias derivadas/sintéticas etiquetadas o capturas reales adicionales con manifiesto, y reloj controlado. No atribuir a Renfe un escenario fabricado.

Medir rendimiento en equipo/navegador/dataset documentados. Los presupuestos del informe son objetivos propuestos, no resultados ni umbrales universales. Vídeo real del frontend integrado; no acreditar implementación con el prototipo HTML.

## Orden de entrega dentro de la cadena

A. Contratos/fiabilidad/catálogo/geometría: MP-016→018.
B. Snapshot coherente y contrato temporal: MP-019.
C. Incrementos pequeños en MP-020: selección+ficha → movimiento+seguimiento → estación/línea/búsqueda → enlaces/móvil.
D. Histórico y cierre completo: MP-021→022.

No abrir worktrees UX-01…UX-15. Preservar los IDs y el ejecutor/revisor del plan vigente. Si tareas ya avanzaron localmente, revisar delta y no repetir trabajo aprobado.

