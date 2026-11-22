# Anexo vinculante Hito 3 — Posición, movimiento y relojes

**Estado:** complemento de aceptación del kit existente `PLAN-Y-ACEPTACION.md`. No reemplaza MP-016→MP-022 ni su reparto Claude/Codex. Aplicar con los ADR vigentes del repositorio; incompatibilidades requieren ADR propuesto y revisión cruzada. En caso de conflicto, la seguridad de trazabilidad y no inventar observaciones prevalece sobre una demo visual bonita.

## A. Tres coordenadas distintas y cuatro tiempos distintos

Nunca confundir estos niveles:

1. **Punto publicado (`raw`)**: lat/lon tal como Renfe lo difundió, sin retoque. Guardar payload/hash, identificadores fuente, `gps_observed_at` (si existe), `feed_published_at` y `received_at`. Ausente es NULL, no `(0,0)`. El punto fuente puede estar fijado a estación o tener granularidad gruesa; no asegurar «GPS exacto» por el hecho de recibir una lat/lon.
2. **Ancla proyectada (`map_matched`)**: proyección del punto anterior a la geometría/patrón verificado, con `matched_lat/lon`, `distance_from_raw_m`, `pattern_id`, `direction_id`, `progress_m`, `geometry_version`, método, razones de selección y anomalías. Una corrección grande o ruta ambigua implica estado incierto, no certeza fingida.
3. **Posición de presentación (`rendered`)**: lat/lon, `calculated_at`, `display_at`, `rendering_method` (`anchor`, `interpolated_between_known_anchors`, `extrapolated_from_last_anchor`, `schedule_only`, `stale_frozen`, `unlocated`), `confidence`, `last_confirmed_at`, `valid_until` y distancia/antigüedad de la última observación. **Los frames del navegador nunca se escriben como observaciones de origen.**

Diferenciar explícitamente `feed_published_at`, `received_at`, `gps_observed_at`, `eta_observed_at`, `snapshot_generated_at` y `display_at` cuando existan. No usar la hora de un sondeo exitoso como nueva edad de un dato de origen antiguo. Un timestamp de fallback antiguo pertenece al ancla realmente dibujada, no al mensaje nuevo descartado. Timestamps internos UTC; fecha de servicio GTFS en Europe/Madrid (incluidos servicios 24:xx y DST).

Conservar en el contrato existente `position.mode` (`observed | estimated | stale | scheduled`) por compatibilidad, pero añadir campos **aditivos** de procedencia/rendering para quitar ambigüedad: `observed` = «posición derivada de una observación reciente», no necesariamente coordenada bruta. Publicar el raw y el matched en detalle del dato cuando sea lícito y útil; si no, registrar la evidencia y exponer un vínculo/metadata estable. Proponer ADR si la semántica existente no se puede expresar de forma compatible.

## B. Movimiento creíble, no teletransportación

Dos modos distintos:

- **Replay/búfer con dos anclas reales**: interpolación entre anclas sobre *longitud de arco de un corredor validado*. Etiqueta `interpolated_between_known_anchors` y muestra retraso de reproducción; nunca afirmar que un frame fue observado por Renfe.
- **Directo sin ancla futura**: extrapolación limitada desde la última ancla usando horario + último retraso válido + topología del patrón, con límites físicos configurables por tipo de servicio, parada en estación y transición a `stale_frozen` cuando expira la confianza. Etiqueta `extrapolated_from_last_anchor`, no `interpolated` si falta la ancla siguiente.

El motor/cliente deben manejar velocidades/aceleraciones razonables **sin convertir los saltos de Renfe entre polls en velocidad real**. Validar sentido y rama; si se pierde geometría o la ruta es ambigua, no unir con una recta falsa, no «saltar» a otra vía ni poner un tren en un corredor ajeno. Si no hay corredor fiable, mostrar solo punto bruto identificado como tal (cuando sea válido) o ficha/tablero con `unlocated`. Cambios entre viaje, vehículo y día de servicio no reutilizan una ancla vieja de otro viaje.

Frontend: conservar fuentes/capas/markers por identidad estable; actualizar posiciones sin destruir y recrear todos los elementos cada poll. Animación mediante reloj de presentación/frame independiente del polling y de las consultas a API. Pausar/atenuar si hay fuente obsoleta, conexión perdida, servicio finalizado, cancelado o parada SKIPPED. En `prefers-reduced-motion`, animación espacial no automática y alternativa accesible. La posición del cliente no sustituye la del servidor en un replay auditado.

## C. Actualización y continuidad temporal

El colector debe registrar en cada ejecución `attempt`, `ok/error`, versión/hora publicada del feed y última recepción exitosa **por fuente**. Un fallo parcial (avisos) no vacía vehículos ni ETAs. Una respuesta válida de 0 entidades no es un fallo de red. Deduplicación no debe resetear edad ni reinsertar observaciones idénticas. Excluir de Live servicios expirados conservándolos en histórico. No reutilizar `delay` de otro servicio/día; interpretar cancelaciones y SKIPPED según contrato GTFS.

Separar catálogos (GTFS+OSM, caché versionada) de snapshots operativos ligeros. Una respuesta del frontend que llegue fuera de orden no sustituye un `snapshot_id` más nuevo. La cámara, selección de estación/tren, modo seguimiento, filtros y scroll del tablero sobreviven a varios polls y a cortes recuperables. Si la ETA deja de estar disponible, mostrar horario planificado y causa explícita, no una ETA falsa. El instante mostrado y la etiqueta Live/Replay deben ser visibles.

## D. Pruebas mínimas obligatorias

- **Backend**: raw→matched→rendered con los tres valores y procedencia; distancia de corrección, ancla rechazada, ausencia de posición, salto implausible, estación sin ruta, bifurcación, tramo compartido, parada SKIPPED, cancelación, cambio de viaje del mismo vehículo, refuerzo SPECIAL, 24:xx, horario DST, retraso antiguo y feed detenido.
- **Secuencia**: capturas congeladas `1532` y `1533` del kit; replay determinista con reloj simulado; observaciones fuera de orden, retry, feed válido vacío, JSON inválido y tres snapshots sucesivos; última señal se envejece aunque no haya nuevos polls.
- **Frontend**: comparar coordenadas en frames intermedios (no solo capturas finales), sin «teleport» entre puntos, sentido correcto, detener en estación, caducar posición, conservar cámara/selección/seguimiento tras dos polls y caída/recuperación; móvil 390 px, escritorio, teclado y WebGL ausente; `prefers-reduced-motion`.
- **Evidencia visual**: grabación de al menos 60 s de la app real, no del prototipo, escritorio y móvil; mostrar etiqueta de estado y hora de fuente al perder señal. El prototipo de `diseno/` usa datos sintéticos y **no prueba** el producto integrado.

Medir latencias p50/p95 de la API, edad de los snapshots, intervalo real de actualización, duración de frames/jank y cobertura por línea con su denominador y máquina de prueba. No declarar cifras objetivo como medidas reales. Proponer presupuestos operativos razonables tras benchmark y registrar cualquier incumplimiento; si la experiencia salta de posición con datos válidos, MP-020/MP-022 no está `DONE`.
