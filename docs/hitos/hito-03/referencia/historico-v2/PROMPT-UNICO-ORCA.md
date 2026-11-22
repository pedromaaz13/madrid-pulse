# MADRID PULSE — AUTORIZACIÓN Y EJECUCIÓN AUTÓNOMA DEL HITO 3

Soy el propietario de `pedromaaz13/madrid-pulse`. Autorizo **el trabajo local completo de MP-016 a MP-022**, con Claude Code como **único coordinador en Orca** y revisión independiente obligatoria entre Claude y Codex. No quiero distribuir tareas manualmente a otros chats: utiliza `orca orchestration` y los workers disponibles desde esta sesión.

**Material adjunto:** carpeta descomprimida de **Madrid-Pulse-Orca-Hito3-v2.zip**. Identifica su ruta en el equipo; no supongas una ruta ficticia. El ZIP preserva el kit de Hito 3 previo: `instalar.py`, replay real `1532/1533`, parche de live, mockups, prototipo `live.html`, `PROMPTS.md`, `PLAN-Y-ACEPTACION.md` y documentos de referencia. Incluye además `ANEXO-CRITICO-POSICION-Y-RELOJ.md`, `MATRIZ-CIERRE-MADRID.md` y `SIGUIENTES-HITOS.md`. **Todos son parte del encargo; los anexos amplían los criterios de aceptación existentes, no cambian el reparto de tareas.**

## Fase 0 — Recuperación y preparación sin perder trabajo

1. Comprueba `origin/main` y el merge real del Hito 2, incluyendo el SHA actual; `990c95d` es solo la base con la que se creó el kit, no una suposición sobre el HEAD de hoy. Lee íntegramente `AGENTS.md`, `CLAUDE.md`, `docs/PLAN.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/DECISIONS.md`, `docs/HITO_3_BACKLOG.md`, `docs/MVP_READINESS.md` y ADR relevantes.
2. Inspecciona todos los worktrees y despachos activos: **recupera trabajo ya iniciado** y no repitas una tarea ni borres ramas. Si MP-016→MP-022 ya existen en TASKS con otro alcance, conserva IDs y registra equivalencias documentadas. No desplaces cambios locales.
3. Lee `EMPIEZA-AQUI.md`, `docs/hitos/hito-03/PROMPTS.md`, `PLAN-Y-ACEPTACION.md`, `diseno/INTERACCIONES.md`, los cuatro PNG, `diseno/live.html`, `referencia/01-auditoria-live.md`, `02-hito-3-orca.md`, `03-arquitectura-analitica.md`, **ANEXO-CRITICO-POSICION-Y-RELOJ.md, MATRIZ-CIERRE-MADRID.md** y `SIGUIENTES-HITOS.md`. Valida los hashes de replay.
4. En el worktree de MP-016 ejecuta el instalador del kit primero con `--comprobar` y luego normalmente, si procede; usa su opción `--solo-datos` en worktrees posteriores. Si existen documentos editados manualmente, integra sus diferencias sin sobrescribirlos ni sortear protecciones. Conserva fixtures y parche original; `git apply --check` antes de cualquier parche y adáptalo al HEAD real.
5. Registra en STATUS/TASKS la autorización de Hito 3 y los criterios adicionales. Si hay decisiones técnicas sin resolver, documéntalas en ADR `Propuesto` y ejecuta las partes independientes conforme a la política vigente.

## Meta de producto innegociable

Al cerrar MP-022 debo poder **abrir un mapa interactivo potente de toda Cercanías Madrid**, no solo C5: ver y filtrar todas las líneas/variantes identificadas en GTFS del núcleo Madrid; trenes con movimiento fluido y correctamente asignados a sus vías y recorridos; estaciones, próximas salidas, horarios planificados, retrasos/ETA reales cuando existan y representación transparente de GPS, map matching y estimación. Debo poder buscar Alcorcón/Atocha, seguir un tren, perder señal y recuperar el directo sin saltos ni perder selección. History/Explore debe permitir justificar datos históricos y cobertura.

Delimita **Cercanías Madrid/núcleo Renfe** por catálogo ferroviario oficial, no por un polígono administrativo que corte recorridos fuera de la Comunidad. AVE/LD/MD y otros operadores NO están autorizados en este hito: solo planifica ese futuro bloque.

El mapa debe dominar la experiencia, con panel lateral en escritorio y bottom sheet en móvil, siguiendo los mockups del kit como referencia visual (los datos de los mockups son sintéticos). Estudia Via Península y Valfiguer a nivel conceptual; **no copies código AGPL ni activos no autorizados**.

## Ejecución y asignaciones: respetar el plan existente

- **MP-016 — Fiabilidad realtime:** ejecuta Codex (preferencia GPT-6.2 Sol); revisa Claude Sonnet High. Reproduce y arregla las incidencias reales de parsing `SKIPPED`, reloj UTC, feeds caducados, catálogo live/replay y colector detenido. Los contadores congelados solo aplican a ese replay.
- **MP-017 — Catálogo Madrid:** ejecuta Claude Sonnet High; revisa Codex Sol. Resolver todo el núcleo (líneas, variantes, trip/route, patrón, sentido, estaciones, avisos), identidades de viaje, cambios de servicio y fecha GTFS.
- **MP-018 — Corredores Madrid:** ejecuta Codex (preferencia Astra, razonamiento alto); revisa Claude Opus High. Geometrías OSM/GTFS por patrón y sentido, ramales, tramos compartidos y cobertura por línea, sin conectar huecos ficticios.
- **MP-019 — Snapshot/API:** ejecuta Claude Opus High; revisa Codex Astra. Snapshot consistente y versionado, consultas batch sin N+1, TTL/estado activo, tablero por estación, ETA con fuente y edad; contrato compatible y trazable.
- **MP-020 — Mapa/frontend:** ejecuta Claude Opus High; revisa Codex Sol. Implementación propia React/MapLibre centrada en el mapa; múltiples líneas, búsqueda, seguimiento, tablero, cinta de novedades, diseño responsive y **animación real entre polls**.
- **MP-021 — Histórico/analítica:** ejecuta Claude Opus High; revisa Codex Astra. Archivo/replay reproducible, histórico por circulación, Explore con coberturas y ejecución local supervisada; despliegue 24/7 de pago solo tras aprobación de coste.
- **MP-022 — Validación integral:** ejecuta Codex Sol; revisa Claude Sonnet High. Reproduce E2E real desde Renfe y catálogo hasta API, animación, histórico y mart. Entrega auditoría independiente completa y checklist de cobertura Madrid.

**Modelos:** Sonnet High para coordinar y trabajo ordinario; Opus High para geometría difícil, arquitectura/API/frontend y analítica según el plan. Verifica en Orca alias/versiones reales (`sonnet`/`opus`) y el catálogo de Codex antes de lanzar; `gpt-6.2-sol/astra` son preferencias, no identificadores garantizados. Conserva el proveedor asignado si un modelo no existe, usa uno soportado y registra solicitado/efectivo/razón.

## Requisitos críticos adicionales — obligatorios en MP-018 a MP-022

**No confundir tres posiciones**: raw publicada por Renfe, map-matched sobre vía y posición renderizada/interpolada/extrapolada. Mantener coordenadas, edad de GPS, distancia de corrección, patrón, timestamp de ancla, método de cálculo y nivel de confianza. `observed` heredado no puede significar GPS exacto si es una proyección. Crear evolución aditiva de contrato o ADR, con pruebas de procedencia.

**No confundir tiempos**: publicación del feed, poll/recepción, observación del vehículo, cálculo de ETA y hora del snapshot. Un poll reciente no rejuvenece un GPS antiguo ni un retraso de otro día.

**Movimiento fluido verificable**: distinguir interpolación entre dos anclas (replay/búfer) y extrapolación en directo desde una sola ancla (estimada). Animación de posición sobre longitud de arco y patrón validado, independiente del polling HTTP; conservar marcadores, cámara y selección. Frenar en estaciones, detener ante dato stale/cancelado, limitar velocidad/aceleración, no cruzar ramales incorrectos, no fabricar frames GPS. Probar la pérdida/recuperación de señal y `prefers-reduced-motion`.

**Backend que funcione como un reloj**: respuestas y catálogos versionados, frescura por feed/GPS/ETA, fallo parcial y datos vacíos diferenciados, estado activo con TTL, snapshots monotónicos y rechazo de respuestas fuera de orden. Medir intervalos reales de ingesta, coste computacional, p50/p95 API, tamaño de snapshots y cobertura por línea; no inventar rendimientos medidos.

**Cobertura de todo Madrid**: las 12 denominaciones/variantes de los cortes del kit (`C1,C2,C3,C4,C4a,C4b,C5,C7,C8a,C8b,C9,C10`) son referencia congelada, NO lista universal inmutable. Inventariar las líneas reales del GTFS vigente y mostrar por cada una: patrones, corredor validado/parcial/no disponible, trenes observados/resueltos/dibujables, ETA, estado de calidad y causa de ausencias. No declarar que el mapa representa todos los GPS si Renfe no publica todas las posiciones.

**UX validada en pantalla**: visual principal full-map, escritorio y móvil 390 px, multiselección, tablero, búsqueda, seguimiento, aviso, teclado, pantalla sin WebGL y alternativa para movimiento reducido. El prototipo es guía visual: las pruebas finales deben ejecutarse sobre **nuestra aplicación consumiendo nuestra API**. Grabar al menos 60 segundos de escritorio y móvil para demostrar movimiento entre dos actualizaciones, no solo pantallazos.

## Protocolo autónomo

Para cada MP: un solo worktree por tarea, un ejecutor y un revisor del proveedor contrario trabajando por turnos. Claude coordinador despacha workers mediante Orca, pasa ruta, base, criterios, prueba y contexto; ejecutor implementa y aporta tests ejecutados; revisor inspecciona diff completo y reproduce casos esenciales; si hay defectos devuelve hallazgos hasta aprobar último HEAD. Solo `DONE` con aprobación independiente. Actualiza `TASKS`, `STATUS`, `CHANGELOG` y ADR; preserva registro de dispatch para poder reanudar. Continúa automáticamente MP-016→MP-022 respetando dependencias.

**Límites:** autorizo trabajo local y commits de iteración con `Pedro Matute <pedromaaz13@gmail.com>`, sin trailers de agentes ni cambiar git config; no autorizo push, apertura de PR, merge, limpieza destructiva ni contratación cloud. Si se necesita decisión de licencia/coste, pausa solo la parte afectada y documenta el gate; sigue con tareas independientes. No marques 24/7 como verificado por una demo local ni ocultes skips o ausencia de datos.

## Condición de cierre

NO declares Hito 3 completado solamente por pasar tests unitarios. Debes entregar:

1. Demo local integrada **de toda la red de Cercanías Madrid** con catálogo y trazados por variante y cobertura visible; fuente en vivo o replay identificado.
2. Mapa fluido basado en trazados verificados y estados/procedencia visibles; evidencia vídeo real desktop/móvil.
3. Pruebas de fallo de feed, envejecimiento, cancelaciones, SKIPPED, identidad/día de servicio y movimiento entre polls.
4. Matriz por línea/variante con cobertura de GTFS, geometría, GPS, ETA, frescura y pendientes.
5. Resultados reales de benchmark: polling, API p50/p95, snapshots, rendimiento del render y límites de coste.
6. Recorrido Live→History/Explore reproducible con métricas de cobertura y replay idempotente.
7. Dossier de auditoría Codex↔Claude sobre el último HEAD, pruebas, capturas, README actualizado e instrucciones reproducibles.
8. Ramas y commits limpios, propuestas ADR y PR listo para que **yo** decida su publicación/integración.
9. Roadmap futuro diferenciado: AV/LD/MD Renfe como Hito 4 propuesto, analítica y despliegue público sujetos a decisiones específicas.

Lee los documentos del kit y ejecuta el Hito 3 autorizado autónomamente. No te detengas para pedir aprobación por tarea o por revisión; detente solo en gates reales según el protocolo y deja evidencia reproducible.
