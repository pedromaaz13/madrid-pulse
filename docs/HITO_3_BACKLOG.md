# HITO_3_BACKLOG.md — Propuesta de planificación (no implementación)

Estado: **propuesta de planificación**, redactada durante Hito 2 por instrucción explícita del propietario (Sección 7 de la autorización de Hito 2, `2026-11-19`). Ningún punto de este documento se implementa durante Hito 2 (`MP-010`→`MP-015`); es exclusivamente backlog para que el propietario lo revise, recorte o reordene antes de autorizar Hito 3. Corresponde a la Fase **F10** de `docs/PLAN.md` ("Expansión — fuera de alcance de MP-001 a MP-015") y aplica la distinción de [ADR-0011](adr/0011-public-scope-vs-technical-pilot.md) (`Propuesto`): Hito 2 es el piloto técnico C5; Hito 3 es el primer paso real hacia el objetivo de producto (toda la red de Cercanías Madrid).

## Objetivo de Hito 3 (propuesto)

Extender Madrid Pulse de "C5 en vivo" a "toda la red de Cercanías Madrid en vivo", reutilizando la arquitectura genérica que Hito 2 debe dejar preparada (ADR-0011) sin rediseñar motores, API ni frontend. No incluye la expansión a otras provincias/núcleos fuera de Madrid — eso queda para una fase posterior, ni siquiera numerada todavía.

## Áreas de trabajo propuestas (no numeradas como MP-XXX todavía — a decidir por el propietario)

### 1. Cobertura de todas las líneas del núcleo Madrid
- Identificar en el GTFS estático las líneas reales del núcleo "10" más allá de C5 (candidatas: C1, C2, C3, C4, C7, C8, C9, C10 — a confirmar contra el GTFS real, no asumir la lista).
- Repetir para cada línea el mismo proceso de validación que MP-010/MP-011 aplicaron a C5: topología, geometría, variantes de sentido/tramo.
- Medir si alguna línea tiene peculiaridades que la arquitectura genérica de Hito 2 no haya anticipado (p. ej. tramos compartidos con otro núcleo, servicios directos entre líneas).

### 2. Rutas y variantes compartidas entre líneas
- Dos o más líneas de Cercanías Madrid comparten tramos de vía física (no solo estaciones) en varios puntos de la red real — validar empíricamente cuáles, y confirmar que el modelo de geometría (MP-011) no duplica ni contradice el trazado cuando dos líneas comparten el mismo tramo.
- Confirmar que el modelo `route`/`trip`/`trip_stop` (ya diseñado para múltiples `source_route_id` por línea desde ADR-0008) no necesita cambios estructurales al añadir las variantes de las líneas nuevas — si los necesita, documentarlo como hallazgo, no como "sorpresa" de última hora.

### 3. Estaciones de intercambio (interchange)
- Identificar las estaciones donde confluyen varias líneas de Cercanías (p. ej. Atocha, Chamartín, Sol, Nuevos Ministerios) y confirmar que el modelo `station` (una fila por estación física, no por línea) sigue siendo correcto cuando varias líneas la comparten.
- Diseñar cómo el frontend debe representar un tren que llega a una estación de intercambio sin que el usuario confunda "la estación" con "la línea" — esto es una decisión de UX, no solo de datos.

### 4. Filtros de línea y búsqueda en API/frontend
- La API (MP-013) ya debe dejar espacio para filtrar por línea/`route_id` (ADR-0011); Hito 3 es donde ese filtro se ejercita con datos reales de más de una línea.
- Diseñar un selector de línea en el frontend (MP-014) que no asuma "una sola línea visible a la vez" como límite técnico, sino como preferencia de UX — un usuario podría querer ver dos líneas simultáneamente en un tramo compartido.
- Búsqueda por estación/línea: evaluar si el volumen de estaciones de toda la red justifica un buscador (autocompletar) frente a una lista navegable, igual que ya se evaluó para C5 en MP-014.

### 5. Escalabilidad con muchos trenes simultáneos
- C5 tiene un volumen de trenes simultáneos relativamente pequeño (confirmado en el soak test de MP-007: ~24 vehículos). Toda la red de Cercanías Madrid multiplica ese número significativamente.
- Medir si el motor de movimiento (MP-012) y la API (MP-013) escalan linealmente o si aparecen cuellos de botella reales (no teóricos) al servir el estado de todos los trenes de la red — con datos reales, no con una proyección sin medir.
- Evaluar si el patrón de snapshot/CDN ya previsto en `docs/ARCHITECTURE.md` ("Snapshot CDN (futuro)") se vuelve necesario en este punto, en vez de seguir sirviendo peticiones directas desde la API para cada espectador.

### 6. Cobertura y calidad de datos por línea
- El quality engine (MP-008) y las métricas (MP-009/análisis futuro) deben reportar cobertura y calidad **por línea**, no solo agregadas — una línea con mala cobertura de datos no debe quedar oculta detrás del promedio de toda la red (mismo principio que ya rige para `delay_coverage_pct`, ver `docs/DECISIONS.md` DEC-009).
- Confirmar empíricamente (no asumir) que todas las líneas del núcleo Madrid tienen el mismo nivel de instrumentación en el feed de Renfe — podría no ser así, y si no lo es, debe documentarse como hallazgo, no asumirse igual que C5.

### 7. Métricas de puntualidad fiables por línea
- **Actualizado en MP-015 (DEC-033):** `daily_line_metrics`/`station_daily_metrics` ya se calculan de verdad para C5 (`services/snapshotter/gold.py`), con tres límites documentados: `trips_scheduled` sin `calendar_dates.txt`, umbral de puntualidad calibrable sin histórico real propio, y `station_daily_metrics` sin `data_quality_events_count` (sin atribución verificada a una parada). Hito 3 extiende esto a todas las líneas y revisa si esos tres límites siguen siendo aceptables a esa escala, siempre con `coverage` explícita junto a cualquier porcentaje de puntualidad — regla no negociable ya fijada en `docs/DATA_CONTRACTS.md`.
- Evaluar si la comparación de puntualidad entre líneas necesita normalizarse de alguna forma (p. ej. longitud de trayecto, número de paradas) antes de presentarse al usuario, para no inducir una comparación injusta entre una línea corta y una larga.

### 8. Validación con datos reales (no proyección)
- Cada punto anterior debe validarse contra datos reales de Renfe para las líneas nuevas, con el mismo rigor empírico que MP-002/MP-003 aplicaron a C5 — no se asume que otra línea se comporta igual que C5 solo porque comparte núcleo.
- Repetir el tipo de hallazgos que Hito 1/2 ya encontraron específicos de C5 (trip_id de refuerzo, campos no observados, velocidades implausibles) para las líneas nuevas, documentando cualquier diferencia real encontrada.

### 9. Preparación para expansión futura a toda España
- Sin implementar nada de esto en Hito 3: dejar registrado qué del diseño de "toda Cercanías Madrid" es reutilizable directamente para otros núcleos (Barcelona, Valencia, Sevilla, etc.) y qué parte es específica de Madrid (p. ej. intercambiadores concretos, convenios con CRTM) — esto es una nota de arquitectura para Hito 4+ (ni siquiera nombrado todavía), no un entregable de Hito 3.

## Qué NO se decide en este documento

- Numeración `MP-XXX` de las tareas de Hito 3 — eso se decide junto con el propietario al autorizar el hito, igual que se hizo con Hito 1/Hito 2.
- Orden de ejecución ni dependencias exactas entre estas áreas — se derivarán del mismo tipo de grafo que ya usa `docs/TASKS.md`, una vez que el propietario confirme qué áreas entran en el alcance de Hito 3.
- Si Hito 3 cubre todas las líneas de golpe o se hace línea por línea de forma incremental — ambas son opciones razonables y el propietario debe decidir cuál prefiere antes de que se abra ningún worktree de Hito 3.
