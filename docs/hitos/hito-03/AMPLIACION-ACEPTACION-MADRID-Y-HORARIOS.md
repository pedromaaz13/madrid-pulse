# Hito 3 — Cierre ferroviario: catálogo, horarios, posiciones y cobertura

Complemento **vinculante de aceptación** para MP-017, MP-019, MP-020 y MP-022. No crea nuevas tareas y no afirma que Renfe publique GPS de cada tren. El criterio es «toda Cercanías Madrid explorable» con evidencias y estados transparentes, no «todos los servicios localizados en directo».

## 1. Dos universos de circulación, dos denominadores

- **Servicios programados elegibles**: instancias activas del GTFS estático para el día de servicio local y ventana temporal, aplicando `calendar.txt` + `calendar_dates.txt`, patrones, `stop_times.txt`, horas `24:xx` y reglas de dirección. Debe existir un proceso **explícito** de enumeración de servicios programados: el fallback `SCHEDULED` que devuelve el motor para un `trip_id` conocido **no** enumera por sí solo todos los servicios del día.
- **Observaciones de vehículo recibidas**: registros provenientes del feed en vivo, identificados por núcleo, vehículo, viaje y timestamp. Medir cobertura de unión contra servicios programados y resolución de `route_id`, nunca suponer que una posición existe para cada trip.
- **Servicios añadidos, cancelados, omitidos o excepcionales**: tratarlos por reglas de servicio y evidencia de GTFS-RT, sin forzar un enlace o ETA. `SKIPPED` afecta a una parada, salvo evidencia independiente de cancelación completa.

Toda línea inventariada podrá mostrar sus recorridos y horario si están respaldados por GTFS, incluso con cero GPS en el corte, pero esas circulaciones se etiquetan como **solo programadas**. Una posición sin geometría validada no se fuerza a una vía cualquiera: se muestra GPS original identificado como tal si es defendible o se conserva el tren en tablero/lista con motivo `unlocated`.

## 2. Qué exige «mapa completo de Madrid»

- Inventario dinámico del **GTFS versionado del núcleo Madrid**. Las 12 denominaciones/variantes del replay son evidencia de ese dataset y fecha, no una lista contractual eterna. Comparar catálogo real, altas, bajas y alias comerciales con fecha de corte.
- Todas las líneas del inventario deben ser seleccionables en mapa y listas con sus patrones y estaciones, aunque no haya posiciones activas. Una línea sin geometría validada mantiene ficha/horarios, y el mapa informa expresamente de la limitación.
- Un recorrido compartido puede dibujar varias líneas sin duplicar geometrías físicas; la identidad de tramo y geometría OSM está separada de los offsets de visualización y del color comercial.
- Mostrar dos modos explícitos: `Live` con fuente y edades, y `Replay` con reloj y fecha propios. No simular hoy el comportamiento de dos capturas históricas como si fueran el feed actual.

## 3. Matriz de evidencias por línea/variante

En MP-022 publicar CSV y Markdown reproducibles con columnas mínimas:

`gtfs_version, captured_at_utc, line_id, route_ids, pattern_count, scheduled_trip_instances, feed_vehicle_observations, resolved_trip_instances, matched_positions, drawable_positions, position_age_p50_s, position_age_p95_s, route_coverage_numerator, route_coverage_denominator, route_coverage_pct, geometry_validated_patterns, geometry_total_patterns, eta_covered_stops, eta_eligible_stops, unknown_reason_count, caveats`.

No promediar porcentajes entre líneas sin ponderar denominadores. Denominador cero → `null`, motivo visible. Si la fuente deja líneas sin GPS, medirlo y no inventar trenes; si faltan geometrías de patrones relevantes para operar Live, el revisor debe registrar la causa, demostrar un fallback honesto y **no declarar cobertura plena de geometría**.

## 4. Pruebas que bloquean DONE

1. Viaje programado válido sin observación GPS: aparece en itinerario/tablero con la hora, fuente y modo `scheduled`, no como GPS real.
2. Calendario excluido por excepción y servicio `24:xx` junto al cambio de día: no aparece indebidamente el viaje del día erróneo.
3. Se recupera GPS tras estimación: diferencia entre raw, matched y rendered; el cliente corrige sin teletransportar a través de tramos/ramales.
4. Feed detenido, feed válido con cero entidades, feed parcial con alertas caídas: estado, edad y lista de servicios siguen coherentes; no se rejuvenece la observación.
5. Cambio de identidad vehículo→trip/día: no reutiliza anclas ni delays de otro servicio.
6. Respuestas fuera de orden: snapshot de menor revisión no rebobina posición, cámara ni selección. No ordenar GUID/hash como número.
7. Tres capturas con reloj controlado: posiciones intermedias cambian cuando el servicio realmente avanza, respeta parada/sentido/límite físico y se congela al agotarse horizonte; `prefers-reduced-motion` mantiene información accesible sin animación continua.
8. UX completa: abrir mapa Madrid → elegir dos líneas → estación compartida → salida válida → tren → Seguir → arrastrar → Volver al tren → History y Atrás. Pruebas desktop, móvil de 390 px, teclado y ausencia WebGL.
9. Benchmark reproducible: p50/p95 API, edad dato, cobertura, duración de frames y memoria, con equipo y dataset descritos; registrar problemas antes de afirmar fluidez.

**Bloqueante de producto:** cualquier línea oficial vigente ausente del catálogo o de los selectores sin explicación; errores de atribución de viaje/ramal; falsas posiciones GPS observadas; UX incapaz de realizar el escenario central. La inexistencia comprobada de GPS o de trazado fiable no autoriza inventar datos: documentar el gap y mantener acceso al horario/tablero; si impide el objetivo funcional, declararlo `PARTIAL`/`BLOCKED` en vez de DONE.

## 5. No adelantar trabajo de Hito 4

AVE/LD/MD y nuevos operadores exigen otro estudio de fuentes, identidades de circulación, ancho/infraestructura y umbrales propios. No contaminar el MVP Cercanías ni bloquear su aceptación por servicios fuera del núcleo Madrid.
